#!/usr/bin/env python3
"""Reconcile the pinned CP/M catalogue to retained Model II qualification records."""
import argparse
import csv
import io
import json
import subprocess
from collections import Counter
from pathlib import Path

from run_model2_conformance import CHECKS, GROUPS, SUITE, SUITE_REV

EVIDENCE = Path(__file__).resolve().parents[1]/'docs/engineering/evidence/2026-11-07-model2-acceptance'
# These are reviewed external oracles. Suite-owned pass counts include only
# the owning executable's P row; overlapping prerequisite rows are not added.
EXTERNAL = (
    ('0013 0014 0015 0475 0477 0479 0480 0481 0483 0484 0485 0486 0487 0488 0489 0495 0567 0578',
     'external.json', 'Edited MARK tail and FCB, exact dispatch, collision traps, caller DU and USER 0–15'),
    ('0482 0569 0570 0572 0574 0575 0577 0579 0612','external.json',
     'Resident commands, directory and user attributes, wildcard decisions, saved page readback and STAT assignment'),
    ('0420 0123 0519','external.json','BDOPROBE counted DE buffer and guarded DMA; BIOS/BDOS pointers on A/B/A'),
    ('0424 0425 0426 0427 0431 0432 0433 0435 0523 0449 0450 0453 0454 0456 0458',
     'external.json','Public calls: DPB/ALV, select and translation, physical offsets, WRITE types and reset masks'),
    ('0059 0060 0061 0062 0063 0064 0075 0076 0077 0078 0081 0082 0442 0448 0473 0600 0606',
     'external.json','Public calls: formatted output, direct literal I/O, queued status, flow control and DMA guards'),
    ('0065 0066 0079 0102 0436 0438 0440','external.json','MORECHAR intercepted logical input, reader and list vectors'),
    ('0439','external.json','BDOS Function 4 delivered graphic and control bytes at BIOS PUNCH'),
    ('0444 0445 0446 0468 0469 0470 0471 0472 0607','character-routes.json',
     'All 256 IOBYTE combinations, keyboard status/input, CRT/LIST routing, reader EOF and punch sink'),
    ('0091','constest-input.json','Function 1 input and echo, including 0092–0101'),
    ('0370 0371','external.json','Read-only erase and rename with whole-disk equality'),
    ('0464 0465 0466 0590 0593 0595','external.json','Damaged gateways, private stack, painted live CCP and warm/cold reconstruction'),
    ('0025 0026 0027 0028 0501 0503 0504 0509 0540','lifecycle.json',
     'Entire 448-record COM, RET/JP 0/Function 0, 449-record rejection, CPX reconstruction and subsequent STATE'),
    ('0390 0391 0392 0393 0457','controller.json','Physical failures and recoverable errors at FD1791/DMA ports, plus native media readback'),
    ('0394 0395 0396 0397 0581 0586 0587','guest.json','fault-suspended, fault-ignore and fault-abort with healthy read and restored B0 state'),
    ('0379 0380 0381 0382 0383 0384','guest.json','Protected-disk terminal cases with Disk R/O, WBOOT and unchanged disk'),
    ('0143 0389','guest.json','Replacement of logged-in removable B, blocked write, Function 37 reset and create'),
    ('0368 0369 0405 0516','guest.json','Read-only files, last writable record, full directory with free blocks, allocation exhaustion and injected failure'),
    ('0620 0621','guest.json','Shipped SUBMIT/XSUB/BATCHIO and submitted Function 10 input'),
)
DIFFERENCES = {'0020':'CCP retains original case in the command tail and uppercases the default FCB.',
               '0493':'The default numeric PATH searches current DU then A0; explicit drive lookup stays exact.',
               '0494':'Numeric PATH can select a different user; explicit DU remains exact.'}


def reconcile(suite, folder):
    def load(filename):
        return json.loads((folder/filename).read_text())
    external = load('external.json')
    guest = load('guest.json')
    assert guest['status']=='PASS' and external['suite_revision']==SUITE_REV
    assert guest['system_sha256']==external['system_sha256']==load('lifecycle.json')['system_sha256']
    cases = guest['conformance_cases']
    assert set(cases)==({name.lower() for name,_,_ in GROUPS}|set(CHECKS))
    assert all(row['status']=='PASS' for row in cases.values())
    assert guest['numeric_path']['result']=='PASS' and all(v=='PASS' for v in guest['release_phases'].values())
    assert load('controller.json')['status']=='PASS' and load('character-routes.json')['iobyte_values']==256
    assert set(external['terminal_cases'])=={k for k in cases if k.startswith(('disk-ro-','fault-','media-change-'))}
    assert [r['disk_restored'] for r in external['config_rollback']]==[True,True,False]
    evidence = {}
    for ids, filename, scope in EXTERNAL:
        assert (folder/filename).is_file()
        for card in ids.split():
            assert card not in evidence
            evidence[card]=('EXTERNAL',filename,scope)
    for filename in ('constest-output.json','constest-input.json'):
        report=load(filename)
        assert report['status']=='PASS' and report['suite_revision']==SUITE_REV
        for case in report['cards']:
            card=case['card']
            assert card not in evidence and case.get('result',case.get('status')) in ('PASS','WBOOT')
            evidence[card]=('CONTROLLED_CONSTEST',filename,'Whole CONSTEST card; 0117 stops at the WBOOT vector')
    raw=subprocess.check_output(['git','-C',str(suite),'show',SUITE_REV+':suite/design/case-to-executable-catalog.tsv'])
    catalogue=list(csv.DictReader(io.StringIO(raw.decode()),delimiter='\t'))
    assert len(catalogue)==len({row['ledger_entry'] for row in catalogue})==627
    ledger=[]
    for row in catalogue:
        card,name,category=row['ledger_entry'],row['executable'].split('.')[0],row['classification']
        observed=external['suite_rows'].get(name,{}).get(card)
        if card in DIFFERENCES:
            result=('PROFILE_DIFFERENCE','external.json' if card=='0020' else 'guest.json',DIFFERENCES[card])
        elif observed and observed[0]=='P':
            result=('SUITE_PASS','external.json',observed[1])
        elif card in evidence:
            result=evidence[card]
        elif observed and observed[0]=='O':
            result=('OBSERVED','external.json',observed[1])
        elif category=='OUTSIDE SCOPE':
            result=('OUTSIDE_BASELINE','suite catalogue',row['applicability'])
        elif category=='NOT GUARANTEED':
            result=('NOT_REQUIRED','suite catalogue',row['applicability'])
        elif category in ('PROFILE REQUIRED','OPTIONAL'):
            result=('UNCLAIMED_PROFILE','suite catalogue',row['applicability'])
        else:
            raise ValueError('missing required Model II oracle: '+card+' '+row['requirement'])
        ledger.append((card,name,category,row['requirement'],*result))
    with (folder/'cards.tsv').open('w') as f:
        writer=csv.writer(f,delimiter='\t',lineterminator='\n')
        writer.writerow(('card','executable','suite_class','requirement','disposition','evidence','scope'))
        writer.writerows(ledger)
    print(dict(Counter(x[4] for x in ledger)))
    return ledger


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',type=Path,default=SUITE)
    p.add_argument('--evidence',type=Path,default=EVIDENCE)
    args=p.parse_args()
    reconcile(args.suite,args.evidence)
