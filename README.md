# EndgameWitness

EndgameWitness is a standalone GenLayer king-and-rook versus king challenge. Each wallet has its own position and turn counter. A player must keep a forced mate on its shortest line while the contract plays the defending king to delay mate as long as possible.

Deploy with `krk1:<white king>,<white rook>,<black king>`, such as `krk1:c4,h1,a8`. White moves first. The constructor validates the position and freezes it for every player. There is no game operator and no funds. The limited piece set eliminates castling, promotion, and en passant. This challenge uses depth to mate (DTM) with fresh FEN counters and never accepts a move that adds plies to the forced line.

Start with `start()`. Then call `play(turn, move)` using a zero-based turn number and UCI move. Before writing, the contract generates all legal moves locally. The leader and each validator independently fetch the Lichess standard tablebase for White's position and, when needed, Black's reply. The contract checks coverage of the full legal move set, local checkmate classification, DTM signs and parity, and the min/max depth identities. It accepts a White move only when the new depth is exactly one less. Black selects the greatest remaining depth, with lexical UCI order resolving ties. Validators compare complete normalized tables, replies and board results. Source failure, disagreement, and rejected moves leave the turn available.

`get_challenge()` shows the opening squares and query. `get_session("wallet:0x…")` returns the board, next turn, remaining plies and status. `get_turn("wallet:0x…", turn)` returns the accepted move, both normalized tablebase records, defense and resulting board. Squares use zero-based row-major order starting at a1. The contract relies on Lichess for exact DTM values and independently checks legality and internal consistency.

[Lichess tablebase API](https://github.com/lichess-org/lila-tablebase#http-api) · [GenLayer equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)

## Verification

```sh
pip install -r requirements-dev.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/endgame_witness.py
python -m pytest tests/direct -q
npm ci
node --test tests/rpc-preflight.test.cjs
```

The StudioNet proof re-fetches the live tablebase using a separate python-chess verifier. It checks the complete nine-ply line from the example position, including a legal move that is too slow and a defense with three legal choices of two different depths. The verifier checks accepted history, signed calldata, per-wallet isolation and terminal replay rejection. Generic CLI receipt transport is reused under MIT.
