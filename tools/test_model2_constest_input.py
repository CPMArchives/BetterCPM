#!/usr/bin/env python3
"""Exercise the pinned interactive CONSTEST input recipes on the assembled Model II."""
import argparse
import json
import tempfile
from collections import deque
from pathlib import Path

from constest_input_cases import BUFFERED, CONTROLS, DIRECT, ECHO
from run_model2_conformance import SUITE, SUITE_REV
from run_validation_console_input import display
from test_model2_constest import CONFIRM, console_fixture


def recipes():
    # (prompt, keys, observed prefix after input, optional visible echo).
    for card,prompt,keys,prefix,_ in DIRECT:
        yield card, [(prompt,keys,prefix,None)]
    for card,prompt,keys,prefix in ECHO:
        yield card, [(prompt,keys,prefix,None)]
    for card,prompt,keys,data,visible in [(*row,row[-1]) for row in BUFFERED]+CONTROLS:
        steps = []
        if card == 116:
            steps.append((b'Can this keyboard send ASCII DEL (7Fh)? (Y/U; U=untested) ',b'Y',None,None))
        steps.append((prompt,keys,counted(data),visible))
        yield card, steps
    yield 85, [(b'Press any key to start with an empty input queue: ', b'K',
                b'\r\n\r\nOBSERVED: return A=00\r\n',None)]
    yield 92, [(b'Wait briefly, then press B: ',b'B',b'B\r\nOBSERVED: return A=42\r\n',None)]
    yield 101, [(b'The input call must pause until resumed and finally return X: ',
                 b'\x13\x11X',b'X\r\nOBSERVED: final return A=58\r\n',None)]
    yield 104, [(b'Press K once. Function 11 must detect it; Function 1 must consume it: ',
                 b'K',b'K\r\nOBSERVED: Function 1 returned A=4B\r\n',None)]
    yield 107, [(b'Maximum is 1. Type Z only; call must return without Enter: ',b'Z',counted(b'Z'),b'Z'),
                (b'Expect count 01 and data [Q]: ',b'Q\r',counted(b'Q'),b'Q')]
    yield 117, [(b'Press any key to start the test: ',b'K\x03',None,None)]


def counted(data):
    return f'\r\nOBSERVED: count={len(data):02X}; data=['.encode()+data+b']\r\n'


def observe_case(run, card, steps):
    output = bytearray()
    keys = deque()
    offsets = []
    pending = iter(steps)
    next_step = next(pending)
    polls = 0
    confirmed = False

    def verify():
        for (prompt, _, prefix, visible), start in zip(steps,offsets):
            if prefix is None:
                continue
            delta = bytes(output[start:])
            if visible is None:
                assert delta.startswith(prefix), (card,prompt,delta[:150])
            else:
                echo,sep,_ = delta.partition(b'\r\nOBSERVED:')
                assert sep and delta[len(echo):].startswith(prefix), (card,delta[:150])
                before = bytes(output[:start])
                assert display(before+echo)==display(before+visible), (card,echo,visible)

    def character(byte):
        nonlocal next_step,confirmed
        output.append(byte)
        if next_step and output.endswith(next_step[0]):
            assert not keys
            offsets.append(len(output))
            keys.extend(next_step[1])
            next_step = next(pending,None)
        if output.endswith(CONFIRM):
            assert card!=117 and not keys and not next_step
            verify()
            keys.append(ord('Y'))
            confirmed = True

    def poll():
        nonlocal polls
        if not keys:
            return None
        # Leave a measurable interval of empty status polls in blocking and
        # XOFF/XON cases. The fixture observes guest polls, not wall time.
        if card in (92,101) and not confirmed:
            polls += 1
            if polls % 64:
                return None
        return keys.popleft()

    try:
        run(card,character,poll)
    except AssertionError as exc:
        raise AssertionError(card,bytes(output[-450:]),exc) from exc
    assert not next_step and not keys and len(offsets)==len(steps), (card,output[-300:])
    if card==117:
        assert not confirmed and b'OBSERVED: Function 10 returned' not in output
    else:
        label = 'X' if card==104 else 'R'
        assert confirmed and f'{card:04d}  P  {label}'.encode() in output
    return {'card':f'{card:04d}', 'result':'WBOOT' if card==117 else 'PASS',
            'input_hex':[step[1].hex() for step in steps], 'transcript':output.decode('ascii')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts',type=Path)
    parser.add_argument('--suite',type=Path,default=SUITE)
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        run,program,resident=console_fixture(args.artifacts,args.suite,args.z80pack,Path(tmp))
        cards=[observe_case(run,card,steps) for card,steps in sorted(recipes())]
    print(json.dumps({'status':'PASS','suite_revision':SUITE_REV,'constest_sha256':program,
                      'resident_sha256':resident,'scope':'Controlled Model II keyboard and CRT. Card 0117 stops at WBOOT; native command recovery is witnessed separately.','cards':cards},indent=2))
