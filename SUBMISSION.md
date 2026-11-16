# EndgameWitness — Consensus shortest-mate challenge

**Category** Builder → Intelligent Contracts

EndgameWitness is a king-and-rook versus king challenge with isolated wallet sessions. Every accepted turn locally checks the full legal move set, and GenLayer validators independently fetch the exact Lichess tablebase positions. White must preserve the shortest forced mate. The contract plays the defense with greatest depth to mate and records both normalized tables and the resulting position. StudioNet verified a nine-ply line, including a defender with three legal replies at two depths. It rejected a legal move that lengthens mate, accepted checkmate, and rejected play after completion. The repo includes a separate python-chess verifier, 11 direct tests, and nine finalized MAJORITY_AGREE receipts. Exact depth values rely on the external tablebase.

- [GenLayer contract](contracts/endgame_witness.py)
- [StudioNet deployment](https://explorer-studio.genlayer.com/tx/0x6154a8064aacff7580a1a19740b627af2485a96a02056c10d8481c3ac90e2807)
- [Longest defense](https://explorer-studio.genlayer.com/tx/0x7cfd61f12d3e999e41bb749df0431e663f63147c56db62bbe40211681f644181)
- [Checkmate](https://explorer-studio.genlayer.com/tx/0x888ba9138d251f64f7b386b458825bdb096652d7280eaa129eafc033e37ea5e3)
- [Receipts and verified state](proofs/README.md)
