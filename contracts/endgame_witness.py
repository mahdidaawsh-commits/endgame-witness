# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json
import re


SOURCE = 'https://tablebase.lichess.ovh/standard?fen='
FILES = 'abcdefgh'
RANKS = '12345678'
MAX_DEPTH = 63
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fail(message):
    raise gl.vm.UserError(message)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def checked_json(body):
    def fields(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate JSON key')
            value[key] = item
        return value

    try:
        return json.loads(body.decode('utf-8'), object_pairs_hook=fields)
    except ValueError:
        fail('Invalid tablebase JSON')


def named(square):
    return FILES[square % 8] + RANKS[square // 8]


def square(name):
    return FILES.index(name[0]) + 8 * RANKS.index(name[1])


def neighbors(first, second):
    return max(abs(first % 8 - second % 8), abs(first // 8 - second // 8)) <= 1


def rook_rays(rook, white, black):
    if rook < 0:
        return
    for dx, dy in DIRECTIONS:
        x, y = rook % 8 + dx, rook // 8 + dy
        while 0 <= x < 8 and 0 <= y < 8:
            point = y * 8 + x
            if point == white:
                break
            yield point
            if point == black:
                break
            x, y = x + dx, y + dy


def king_steps(king):
    x, y = king % 8, king // 8
    return [row * 8 + column for row in range(max(0, y - 1), min(8, y + 2))
            for column in range(max(0, x - 1), min(8, x + 2)) if (column, row) != (x, y)]


def legal(board, side):
    white, rook, black = board
    if side == 'w':
        moves = {named(white) + named(dest): [dest, rook, black] for dest in king_steps(white)
                 if dest != rook and not neighbors(dest, black)}
        for dest in rook_rays(rook, white, black):
            if dest != black:
                moves[named(rook) + named(dest)] = [white, dest, black]
        return moves
    moves = {}
    for dest in king_steps(black):
        next_rook = -1 if dest == rook else rook
        if not neighbors(dest, white) and dest not in rook_rays(next_rook, white, dest):
            moves[named(black) + named(dest)] = [white, next_rook, dest]
    return moves


def table_url(board, side):
    pieces = {board[0]: 'K', board[1]: 'R', board[2]: 'k'}
    ranks = []
    for row in range(7, -1, -1):
        rank, empty = '', 0
        for col in range(8):
            piece = pieces.get(row * 8 + col)
            if piece:
                rank += (str(empty) if empty else '') + piece
                empty = 0
            else:
                empty += 1
        ranks.append(rank + (str(empty) if empty else ''))
    return SOURCE + '/'.join(ranks) + '_' + side + '_-_-_0_1'


def initial_board(spec):
    if not re.fullmatch(r'krk1:[a-h][1-8],[a-h][1-8],[a-h][1-8]', spec):
        fail('Invalid challenge squares')
    board = [square(part) for part in spec[5:].split(',')]
    white, rook, black = board
    if len(set(board)) != 3 or neighbors(white, black) or black in rook_rays(rook, white, black):
        fail('Illegal starting board')
    return board


def table_for(board, side, moves):
    url = table_url(board, side)
    response = gl.nondet.web.get(url)
    if response.status != 200 or not 1 <= len(response.body) <= 32768:
        fail('Lichess tablebase unavailable')
    raw = checked_json(response.body)
    category = 'win' if side == 'w' else 'loss'
    if not isinstance(raw, dict) or raw.get('category') != category:
        fail('Position is not a supported forced mate')
    distance = raw.get('dtm')
    if (type(distance) is not int or not 1 <= abs(distance) <= MAX_DEPTH
            or (distance > 0) != (side == 'w') or distance % 2 != (side == 'w')):
        fail('Invalid tablebase mate depth')
    entries = raw.get('moves')
    if not isinstance(entries, list) or len(entries) != len(moves):
        fail('Tablebase does not cover every legal move')
    depths = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail('Invalid tablebase move')
        move, result, depth = entry.get('uci'), entry.get('category'), entry.get('dtm')
        if not isinstance(move, str) or move not in moves or move in depths:
            fail('Unexpected tablebase move')
        successor = moves[move]
        if side == 'w' and not legal(successor, 'b'):
            white, rook, black = successor
            mate = black in rook_rays(rook, white, black)
            if entry.get('checkmate') is not mate or result != ('loss' if mate else 'draw'):
                fail('Tablebase terminal classification mismatch')
            depths[move] = 0 if mate else None
        elif side == 'w' and result == 'draw' and depth is None:
            depths[move] = None
        elif (type(depth) is int and 1 <= abs(depth) <= MAX_DEPTH
              and result == ('loss' if side == 'w' else 'win')
              and (depth < 0) == (side == 'w') and depth % 2 == (side == 'b')):
            depths[move] = abs(depth)
        else:
            fail('Invalid successor mate depth')
    forced = [depth for depth in depths.values() if depth is not None]
    if not forced or abs(distance) != 1 + (min(forced) if side == 'w' else max(forced)):
        fail('Tablebase minimax depth mismatch')
    return {'source': url, 'depth': abs(distance), 'successors': depths}


def observe_turn(board, move, expected_depth, white_moves):
    def fetch():
        white = table_for(board, 'w', white_moves)
        if expected_depth is not None and white['depth'] != expected_depth:
            fail('Mate depth changed since previous turn')
        depth = white['successors'][move]
        if depth != white['depth'] - 1:
            fail('Move does not preserve shortest mate')
        after = white_moves[move]
        if depth == 0:
            return {'white': white, 'black': None, 'defense': None, 'board': after, 'remaining': 0}
        black_moves = legal(after, 'b')
        if not black_moves:
            fail('Nonterminal tablebase move ended the game')
        black = table_for(after, 'b', black_moves)
        if black['depth'] != depth:
            fail('White and black tables disagree')
        defense = min(black_moves, key=lambda uci: (-black['successors'][uci], uci))
        return {'white': white, 'black': black, 'defense': defense, 'board': black_moves[defense],
                'remaining': black['successors'][defense]}

    def verify(proposal):
        try:
            observed = fetch()
        except gl.vm.UserError as error:
            return not isinstance(proposal, gl.vm.Return) and getattr(proposal, 'message', None) == error.message
        except Exception:
            return False
        return isinstance(proposal, gl.vm.Return) and encode(proposal.calldata) == encode(observed)

    return gl.vm.run_nondet_unsafe(fetch, verify)


def owner_address(wallet):
    if not re.fullmatch(r'wallet:0x[0-9a-fA-F]{40}', wallet):
        fail('Invalid wallet')
    return Address(wallet[7:])


def history_key(owner, turn):
    return str(owner).lower() + ':' + str(turn)


class EndgameWitness(gl.Contract):
    opening: str
    sessions: TreeMap[Address, str]
    history: TreeMap[str, str]

    def __init__(self, challenge: str):
        self.opening = encode(initial_board(challenge))

    @gl.public.write
    def start(self) -> None:
        owner = gl.message.sender_address
        if owner in self.sessions:
            fail('Session already started')
        self.sessions[owner] = encode({'board': json.loads(self.opening), 'turn': 0, 'remaining': None, 'status': 'ACTIVE'})

    @gl.public.write
    def play(self, turn: int, move: str) -> None:
        owner = gl.message.sender_address
        if owner not in self.sessions:
            fail('Start a session first')
        session = json.loads(self.sessions[owner])
        if session['status'] != 'ACTIVE':
            fail('Session already completed')
        if type(turn) is not int or turn != session['turn']:
            fail('Unexpected turn number')
        moves = legal(session['board'], 'w')
        if move not in moves:
            fail('Illegal white move')
        record = observe_turn(session['board'], move, session['remaining'], moves)
        self.history[history_key(owner, turn)] = encode({'move': move, 'before': session['board'], **record})
        self.sessions[owner] = encode({'board': record['board'], 'turn': turn + 1, 'remaining': record['remaining'],
                                       'status': 'MATE' if record['remaining'] == 0 else 'ACTIVE'})

    @gl.public.view
    def get_challenge(self) -> dict:
        board = json.loads(self.opening)
        return {'board': board, 'source': table_url(board, 'w')}

    @gl.public.view
    def get_session(self, wallet: str) -> dict:
        owner = owner_address(wallet)
        return json.loads(self.sessions[owner]) if owner in self.sessions else {}

    @gl.public.view
    def get_turn(self, wallet: str, turn: int) -> dict:
        owner = owner_address(wallet)
        if type(turn) is not int or not 0 <= turn <= MAX_DEPTH // 2:
            fail('Invalid turn number')
        key = history_key(owner, turn)
        return json.loads(self.history[key]) if key in self.history else {}
