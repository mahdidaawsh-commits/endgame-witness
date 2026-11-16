from copy import deepcopy
import json
from pathlib import Path
import re

import pytest

from scripts.reference import run


CHALLENGE = 'krk1:c4,h1,a8'
BUNDLE = json.loads(Path('fixtures/live-line.json').read_bytes())
OPENING = BUNDLE['rounds'][0]['white']['source']


def deploy(direct_deploy, challenge=CHALLENGE):
    return direct_deploy('contracts/endgame_witness.py', challenge, sdk_version='v0.2.16')


def bind(vm, docs=None):
    vm.clear_mocks()
    for url, document in (BUNDLE['documents'] if docs is None else docs).items():
        vm.mock_web(re.escape(url), {'status': 200, 'body': json.dumps(document).encode()})


def wallet(address):
    return 'wallet:0x' + address.hex()


def test_complete_live_fixture_matches_independent_engine(direct_vm, direct_deploy, direct_alice, direct_bob):
    assert run(BUNDLE['documents'].__getitem__)['rounds'] == BUNDLE['rounds']
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    player = wallet(direct_alice)
    contract.start()
    bind(direct_vm)
    for turn, record in enumerate(BUNDLE['rounds']):
        contract.play(turn, record['move'])
        assert direct_vm.run_validator() is True
        assert contract.get_turn(player, turn) == record
        state = contract.get_session(player)
        assert state['remaining'] == record['remaining']
        assert state['board'] == record['board']
    assert state['status'] == 'MATE' and state['turn'] == 5
    assert contract.get_turn(player, 0)['defense'] == 'a8b7'
    assert contract.get_session(wallet(direct_bob)) == {}
    with direct_vm.expect_revert('Session already completed'):
        contract.play(5, 'h1a1')
    assert contract.get_session(player) == state


def test_rejected_turn_leaves_board_and_history_untouched(direct_vm, direct_deploy, direct_alice):
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert('Start a session first'):
        contract.play(0, 'c4b5')
    contract.start()
    player = wallet(direct_alice)
    initial = contract.get_session(player)
    with direct_vm.expect_revert('Session already started'):
        contract.start()
    with direct_vm.expect_revert('Unexpected turn number'):
        contract.play(1, 'c4b5')
    with direct_vm.expect_revert('Illegal white move'):
        contract.play(0, 'c4a4')
    bind(direct_vm)
    with direct_vm.expect_revert('Move does not preserve shortest mate'):
        contract.play(0, 'h1a1')
    assert contract.get_session(player) == initial and contract.get_turn(player, 0) == {}


def test_validator_checks_material_alternatives_even_when_selected_moves_match(direct_vm, direct_deploy):
    contract = deploy(direct_deploy)
    contract.start()
    bind(direct_vm)
    contract.play(0, 'c4b5')
    altered = deepcopy(BUNDLE['documents'])
    for document in altered.values():
        document['moves'].reverse()
    bind(direct_vm, altered)
    assert direct_vm.run_validator() is True
    # The worse Black reply still loses and the same defense stays optimal.
    black = BUNDLE['rounds'][0]['black']['source']
    for entry in altered[black]['moves']:
        if entry['uci'] == 'a8a7':
            entry['dtm'] = 3
    bind(direct_vm, altered)
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize(('fault', 'reason'), [
    ('omit', 'Tablebase does not cover every legal move'),
    ('insert', 'Unexpected tablebase move'),
    ('distance', 'Tablebase minimax depth mismatch'),
    ('sign', 'Invalid tablebase mate depth'),
    ('side', 'Position is not a supported forced mate'),
])
def test_invalid_table_cannot_advance(direct_vm, direct_deploy, direct_alice, fault, reason):
    contract = deploy(direct_deploy)
    direct_vm.sender = direct_alice
    contract.start()
    altered = deepcopy(BUNDLE['documents'])
    root = altered[OPENING]
    if fault == 'omit':
        root['moves'].pop()
    elif fault == 'insert':
        root['moves'][0]['uci'] = 'a1a8'
    elif fault == 'distance':
        root['dtm'] += 2
    elif fault == 'sign':
        root['dtm'] = -root['dtm']
    else:
        root['category'] = 'draw'
    bind(direct_vm, altered)
    with direct_vm.expect_revert(reason):
        contract.play(0, 'c4b5')
    assert contract.get_session(wallet(direct_alice))['turn'] == 0
    bind(direct_vm)
    contract.play(0, 'c4b5')
    assert contract.get_session(wallet(direct_alice))['remaining'] == 7


@pytest.mark.parametrize('challenge', ['krk1:c4,c4,a8', 'krk1:b7,h1,a8', 'krk1:c4,a1,a8'])
def test_illegal_opening(direct_vm, direct_deploy, challenge):
    with direct_vm.expect_revert('Illegal starting board'):
        deploy(direct_deploy, challenge)
