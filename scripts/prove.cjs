const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const {assert, equal, sourceHash, invoke, read, rpc, receipt, receiptSummary, save} = require('./transport.cjs');
const {decodeReceipt} = require('./receipt-calldata.cjs');

const challenge = 'krk1:c4,h1,a8';

async function main() {
  const wallets = JSON.parse(process.env.ENDGAME_ACCOUNTS || '[]');
  assert(wallets.length === 2 && wallets[0].address !== wallets[1].address, 'Two distinct wallets required');
  const expectedRounds = JSON.parse(execFileSync('python', ['scripts/reference.py'], {timeout: 240000}));
  const suboptimal = 'h1a1';
  assert(expectedRounds[0].white.successors[suboptimal] > expectedRounds[0].white.depth - 1,
    'Expected a legal move that loses tempo');
  assert(await rpc('eth_chainId', []) === '0xf22f', 'StudioNet only');
  const code = fs.readFileSync('contracts/endgame_witness.py');
  process.env.ENDGAME_ACCOUNT = wallets[0].name;
  const deployment = await invoke('deploy', ['deploy', '--contract', 'contracts/endgame_witness.py', '--args', challenge]);
  const deployed = await receipt('deploy', deployment, true);
  const contract = deployed.to_address || deployed.recipient;
  assert(/^0x[0-9a-f]{40}$/i.test(contract) && code.equals(Buffer.from(deployed.data.contract_code, 'base64')), 'Deployed code mismatch');
  let state = {};
  const player = 'wallet:' + wallets[1].address;
  const report = {contract, deployment, revision: process.env.GITHUB_SHA, source_sha256: sourceHash, trace: [], rounds: []};

  async function verify(label, raw, actor, args, error) {
    assert((raw.from_address || raw.sender).toLowerCase() === wallets[actor].address
      && (raw.to_address || raw.recipient).toLowerCase() === contract.toLowerCase(), 'Wrong receipt addresses');
    assert(equal(await decodeReceipt(raw), args), 'Unexpected signed calldata');
    if (error) {
      const data = Buffer.from(raw.consensus_data.leader_receipt[0].result, 'base64');
      assert(data[0] === 1 && data.subarray(1).toString() === error, 'Wrong rejection at ' + label);
    }
    const current = await read(label + '-session', ['call', contract, 'get_session', '--args', player]);
    assert(equal(current, state), 'Session state differs at ' + label);
    report.trace.push({label, ...receiptSummary(raw), signer: wallets[actor].address, args, error: error || null, state: current});
    save('progress', report);
  }

  async function write(label, method, args, next, error) {
    process.env.ENDGAME_ACCOUNT = wallets[1].name;
    const call = ['write', contract, method];
    if (args.length) call.push('--args', ...args.map(String));
    const hash = await invoke(label, call);
    const raw = await receipt(label, hash, !error);
    state = next;
    await verify(label, raw, 1, {method, args}, error);
  }

  await verify('deploy', deployed, 0, {args: [challenge]});
  const challengeView = await read('challenge', ['call', contract, 'get_challenge']);
  assert(equal(challengeView, {board: expectedRounds[0].before, source: expectedRounds[0].white.source}), 'Wrong fixed challenge');
  await write('start', 'start', [], {board: expectedRounds[0].before, turn: 0, remaining: null, status: 'ACTIVE'});
  await write('suboptimal', 'play', [0, suboptimal], state, 'Move does not preserve shortest mate');
  assert(equal(await read('no-rejected-turn', ['call', contract, 'get_turn', '--args', player, '0']), {}),
    'Rejected move wrote a witness');
  for (const [turn, expected] of expectedRounds.entries()) {
    const label = 'turn-' + turn;
    await write(label, 'play', [turn, expected.move],
      {board: expected.board, turn: turn + 1, remaining: expected.remaining, status: expected.remaining === 0 ? 'MATE' : 'ACTIVE'});
    const record = await read(label + '-witness', ['call', contract, 'get_turn', '--args', player, String(turn)]);
    assert(equal(record, expected), 'Tablebase or board differs at ' + label);
    report.rounds.push(record);
  }
  await write('terminal', 'play', [state.turn, expectedRounds.at(-1).move], state, 'Session already completed');
  assert(equal(await read('deployer-isolated', ['call', contract, 'get_session', '--args', 'wallet:' + wallets[0].address]), {}),
    'Session leaked across wallets');
  assert(code.equals(Buffer.from(await rpc('gen_getContractCode', [contract]), 'base64')), 'Fresh code differs');
  save('verified', report);
  console.log(JSON.stringify({contract, deployment, receipts: report.trace.length, status: state.status, turns: state.turn}));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
