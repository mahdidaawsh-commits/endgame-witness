"""Independent legal move generation and live tablebase replay."""
import json
from pathlib import Path
import sys
from urllib.request import urlopen

import chess


SOURCE = 'https://tablebase.lichess.ovh/standard?fen='
OPENING = 'k7/8/8/8/2K5/8/8/7R w - - 0 1'


def squares(board):
    return [board.king(chess.WHITE), next(iter(board.pieces(chess.ROOK, chess.WHITE))),
            board.king(chess.BLACK)]


def url_for(board):
    fields = board.fen().split()
    return SOURCE + '_'.join(fields[:4] + ['0', '1'])


def from_web(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=20) as response:
                return json.loads(response.read(32769))
        except (OSError, ValueError):
            if attempt == 2:
                raise
    raise RuntimeError('Unreachable fetch state')


def run(fetch):
    board = chess.Board(OPENING)
    documents = {}
    rounds = []

    def probe():
        url = url_for(board)
        data = fetch(url)
        documents[url] = data
        moves = sorted(move.uci() for move in board.legal_moves)
        assert sorted(entry['uci'] for entry in data['moves']) == moves
        depths = {}
        for entry in data['moves']:
            result = board.copy()
            result.push_uci(entry['uci'])
            assert bool(entry['checkmate']) == result.is_checkmate()
            depths[entry['uci']] = 0 if result.is_checkmate() else (
                None if entry['dtm'] is None else abs(entry['dtm']))
        return {'source': url, 'depth': abs(data['dtm']), 'successors': depths}

    while not board.is_checkmate():
        assert board.turn == chess.WHITE
        before = squares(board)
        white = probe()
        move = min(uci for uci, depth in white['successors'].items() if depth == white['depth'] - 1)
        board.push_uci(move)
        black, defense = None, None
        remaining = 0
        if not board.is_checkmate():
            black = probe()
            max_depth = max(black['successors'].values())
            defense = min(uci for uci, depth in black['successors'].items() if depth == max_depth)
            assert black['depth'] == max_depth + 1 == white['depth'] - 1
            board.push_uci(defense)
            remaining = max_depth
        rounds.append({'before': before, 'move': move, 'white': white, 'black': black, 'defense': defense,
                       'remaining': remaining, 'board': squares(board)})
        assert len(rounds) <= 32
    assert rounds[0]['white']['depth'] == 9
    assert rounds[0]['black']['successors'] == {'a8a7': 5, 'a8b7': 7, 'a8b8': 5}
    assert len(rounds) == 5
    return {'rounds': rounds, 'documents': documents}


if __name__ == '__main__':
    bundle = run(from_web)
    if len(sys.argv) == 2:
        Path(sys.argv[1]).write_text(json.dumps(bundle, indent=2) + '\n', encoding='utf-8')
    else:
        print(json.dumps(bundle['rounds']))
