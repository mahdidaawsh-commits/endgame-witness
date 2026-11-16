# StudioNet proofs

Contract address 0xC73bf0F91aFc5D4f07936BD386D5722BFB5CA5BB

The challenge started at nine plies to mate. After c4b5, the defending king chose a8b7 with seven plies remaining. Its two alternatives had five plies left. The accepted line ended with c1a1 checkmate.

[Workflow](https://github.com/mahdidaawsh-commits/endgame-witness/actions/runs/43941517326) · [Verified reads and tablebase witnesses](verified.json)

| Outcome | Explorer | Receipt | Agree / disagree / idle |
| --- | --- | --- | --- |
| Deployed fixed king-and-rook challenge | [Transaction](https://explorer-studio.genlayer.com/tx/0x6154a8064aacff7580a1a19740b627af2485a96a02056c10d8481c3ac90e2807) | [JSON](deploy-receipt.json) | 3 / 0 / 2 |
| Second wallet started an isolated session | [Transaction](https://explorer-studio.genlayer.com/tx/0x38849e4fb393f24cea1fefd36a9d8a413727ee3e5f9374246946a10173bee941) | [JSON](start-receipt.json) | 4 / 0 / 1 |
| Legal h1a1 rejected because it lengthens mate | [Transaction](https://explorer-studio.genlayer.com/tx/0xcf03699fd7c5637923dd44186a20c4e042d34078f70f724f8d6a5b76ff7e59f1) | [JSON](suboptimal-receipt.json) | 3 / 0 / 2 |
| c4b5 / a8b7 · 7 plies remaining | [Transaction](https://explorer-studio.genlayer.com/tx/0x7cfd61f12d3e999e41bb749df0431e663f63147c56db62bbe40211681f644181) | [JSON](turn-0-receipt.json) | 3 / 0 / 2 |
| h1c1 / b7a7 · 5 plies remaining | [Transaction](https://explorer-studio.genlayer.com/tx/0xc61aed868599121a2bde2ffe693d7466fc85b1384eaaa6fbfbd91a9dedd935d3) | [JSON](turn-1-receipt.json) | 3 / 0 / 2 |
| b5c6 / a7a8 · 3 plies remaining | [Transaction](https://explorer-studio.genlayer.com/tx/0x81301cd1639183f2a356adc357d1b87d063d99bdc1b90955ffbd02f7f4954720) | [JSON](turn-2-receipt.json) | 3 / 0 / 2 |
| c6c7 / a8a7 · 1 plies remaining | [Transaction](https://explorer-studio.genlayer.com/tx/0xdd59d795c2b25e693092353416429d0dc6adadc3ece45570df1d5a09c1b4415a) | [JSON](turn-3-receipt.json) | 3 / 0 / 2 |
| c1a1 checkmate · 0 plies remaining | [Transaction](https://explorer-studio.genlayer.com/tx/0x888ba9138d251f64f7b386b458825bdb096652d7280eaa129eafc033e37ea5e3) | [JSON](turn-4-receipt.json) | 3 / 0 / 2 |
| Play after mate rejected | [Transaction](https://explorer-studio.genlayer.com/tx/0xeef8751a02c3242ca4298fcd2d64a6c5c128979d16ac071ecc8aa16849c2bd67) | [JSON](terminal-receipt.json) | 3 / 0 / 2 |

All nine receipts finalized with MAJORITY_AGREE. A separate python-chess run generated legal moves and matched the live Lichess tables. The proof checked signed calldata, deployed bytes, session isolation and fresh onchain history.

Deployed revision 373fdf482b8776029a0bff41ecbee6aa30166059

Contract SHA-256 b3c101af68f66dec424988f35ce59c456a90706d472274c299abf37df99f87d9
