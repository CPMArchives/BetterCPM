#!/usr/bin/env python3
"""Native ZSM4/LINK parity and bounded NOAH memory experiment on both targets."""
import argparse
import json
from pathlib import Path
import re

from build_noah_proof import build, ROOT, sha
from dasm_native import campaign


def verify_system(system, platforms):
    """Do not qualify current source against an unrelated cached resident core.

    The original default image predated 8864aa5's sequential write rollover fix.
    LINK's XXPROG.$$$ reopen then failed on Model 4 EXM=0 media. Checking only
    the prototype/REL hashes cannot detect that stale operating-system input.
    """
    core = 'src/bdos/unified.mac'
    expected = sha((ROOT/core).read_bytes())
    identities = {}
    for platform in platforms:
        report = json.loads((system/platform/'report.json').read_text())
        source = report.get('source', {})
        actual = source.get('inputs', {}).get(core)
        if actual != expected:
            raise ValueError(f'{platform}: stale or unverified system core; '
                             f'{core} expected {expected}, recorded {actual}. '
                             'Use --system with media built from the current core.')
        image = system/platform/report['image']
        if sha(image.read_bytes()) != report['sha256']:
            raise ValueError(f'{platform}: system image differs from its build report')
        identities[platform] = {'source_revision':source['revision'],
                               'core_sha256':actual,'image_sha256':report['sha256']}
    return identities


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True,
                   help='System-media directory with current-core source/hash reports')
    p.add_argument('--utilities', type=Path, default=ROOT/'build/ted-qualified-utilities')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reuse-native', type=Path,
                   help='Reuse already verified native outputs for unchanged sources')
    p.add_argument('--resume-model4-rel', type=Path,
                   help='Retain completed Model 4 ZSM4 assembly; link its three REL outputs')
    p.add_argument('--runtime-only', action='store_true',
                   help='Run cross-built proof only; explicitly makes no native-build claim')
    p.add_argument('--existing-run', type=Path,
                   help='Evaluate retained complete campaign outputs without rerunning emulators')
    p.add_argument('--platforms', nargs='+', choices=['z80pack','trs80gp'],
                   default=['z80pack','trs80gp'])
    a = p.parse_args()
    a.output = a.output.resolve()
    a.system = a.system.resolve()
    a.utilities = a.utilities.resolve()
    systems = verify_system(a.system, a.platforms)
    a.output.mkdir(parents=True, exist_ok=False)
    cross = a.output/'cross'
    layout = build(Path.home()/'bin/z80asm', cross)
    ovl = (cross/'NOAH.OVL').read_bytes()
    bad = bytearray(ovl); bad[-128] ^= 1
    # Same executable, fixture filename only changed, to exercise a bad body.
    proof = (cross/'PROOF.COM').read_bytes()
    assert proof.count(b'NOAH    OVL') == 1
    badproof = proof.replace(b'NOAH    OVL',b'BAD     OVL')
    files = {n+'.MAC':(cross/(n+'.MAC')).read_bytes()
             for n in ('PROOF','LBRMOD','UNCRMOD')}
    files.update({'NOAH.OVL':ovl,'BAD.OVL':bytes(bad),'BADPRF.COM':badproof})
    builds = [f'B:ZSM4 {n}={n}' for n in ('PROOF','LBRMOD','UNCRMOD')]
    builds += [f'B:LINK {n}[A]' for n in ('PROOF','LBRMOD','UNCRMOD')]
    report = {'scope':'prototype only; no CLI/writer/ARK acceptance',
              'verified_systems':systems,
              'layout':layout, 'platforms':{}}
    for platform in a.platforms:
        reuse = a.reuse_native and (a.reuse_native/platform/'after-PROOF.COM').is_file()
        resume_rel = platform == 'trs80gp' and a.resume_model4_rel
        inputs = dict(files)
        if reuse:
            for n in ('PROOF','LBRMOD','UNCRMOD'):
                inputs[n+'.COM'] = (a.reuse_native/platform/('after-'+n+'.COM')).read_bytes()
        if resume_rel:
            for n in ('PROOF','LBRMOD','UNCRMOD'):
                inputs[n+'.REL'] = (a.resume_model4_rel/(n+'.REL')).read_bytes()
        if a.runtime_only:
            inputs['PROOF.COM'] = proof
            for n in ('LBRMOD','UNCRMOD'):
                inputs[n+'.COM'] = (cross/(n+'.bin')).read_bytes()
        prefix = ['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform == 'z80pack' else []
        monitor, provider = ('ANSI','ANSISCRN') if platform == 'z80pack' else ('ADM3A','M4SCRN')
        native_build = [] if reuse else builds
        if platform == 'trs80gp' and not reuse:
            native_build = builds[:3]+['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN']+builds[3:]+[
                'RSX LOAD M4SCRN','RSX LOAD ADM3A']
        if resume_rel:
            native_build = ['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN']+builds[3:]+[
                'RSX LOAD M4SCRN','RSX LOAD ADM3A']
        if a.runtime_only:
            native_build = []
        todo = native_build+prefix+[
            'PROOF','RSX UNLOAD '+monitor,'RSX UNLOAD '+provider,'PROOF','BADPRF','RSX LIST']
        if a.existing_run:
            prior = a.existing_run/platform
            log = (prior/'console.bin').read_bytes()
            outputs = {n+'.COM':(prior/('after-'+n+'.COM')).read_bytes()
                       for n in ('PROOF','LBRMOD','UNCRMOD')}
            execution = json.loads((prior/'execution.json').read_text())
            assert execution['system_sha256'] == systems[platform]['image_sha256'], \
                'retained campaign ran on a different system image'
            assert sha(log) == execution['console_sha256']
            assert execution['commands'] == todo
            assert execution['input_hashes'] == {n:sha(v) for n,v in inputs.items()} | {
                n:h for n,h in execution['input_hashes'].items() if n not in inputs}
        else:
            log, outputs = campaign(platform, inputs, todo, a.output/platform,
                 system=a.system, utilities=a.utilities,
                 extract=['PROOF.COM','LBRMOD.COM','UNCRMOD.COM'], timeout=600)
        errors = re.findall(rb'Errors: +([0-9]+)',log)
        assert (not errors if reuse or resume_rel or a.runtime_only else len(errors) == 3 and set(errors) == {b'0'}), errors
        for name, expected in (('PROOF',proof),('LBRMOD',(cross/'LBRMOD.bin').read_bytes()),
                               ('UNCRMOD',(cross/'UNCRMOD.bin').read_bytes())):
            actual = outputs[name+'.COM']
            assert actual[:len(expected)] == expected, (platform,name,'native mismatch')
            if a.runtime_only:
                assert len(expected) <= len(actual) <= (len(expected)+127)//128*128
            else:
                assert len(actual) == (len(expected)+127)//128*128
            assert set(actual[len(expected):]) <= ({0,26} if a.runtime_only else {26})
        assert b'NOAH PROOF PASS' in log, log[-3000:]
        assert b'NOAH PROOF LOW TPA' in log, log[-3000:]
        assert b'NOAH PROOF INVALID' in log, log[-3000:]
        measured = re.findall(rb'NOAH PROOF TPA ([0-9A-F]{4}) NEED ([0-9A-F]{4})',log)
        assert measured and all(int(n,16)==layout['required_ceiling'] for _,n in measured)
        report['platforms'][platform] = {'status':'PASS','native_cross_parity':not a.runtime_only,
            'native_build_status':'NOT_RUN' if a.runtime_only else 'PASS',
            'native_build_reused_from': str(a.reuse_native/platform) if reuse else None,
            'native_assembly_reused_from': str(a.resume_model4_rel) if resume_rel else None,
            'observed_tpa_ceiling_hex':sorted({c.decode() for c,_ in measured}),
            'bare_read_decode':True,'loaded_rsx_refusal':True,'corrupt_overlay_refusal':True,
            'execution_report':str(prior/'execution.json') if a.existing_run else platform+'/execution.json',
            'console_sha256':sha(log)}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,('cross runtime' if a.runtime_only else 'native parity'),
              'bare decode, loaded-RSX and corruption refusal',flush=True)


if __name__ == '__main__':
    main()
