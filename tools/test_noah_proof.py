#!/usr/bin/env python3
"""Focused full-Z80 checks of the isolated overlay profile; no CLI regression sweep."""
import argparse
import ctypes as C
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib

from build_noah_proof import build, ROOT, sha
from qualify_noah_proof import verify_system
from test_usq import SHIM
from test_usq_com import Command, diskkey


class Proof(Command):
    instruction_budget = 20000000

    def __init__(self, core, image, listing):
        super().__init__(core, image, listing, ('OLDSP','STACK_LOW','STACK_TOP','FCB'))
        self.symbols.update(UC_OLDSP=self.symbols['OLDSP'], UC_STACK=0,
                            UC_STACK_TOP=65535, UC_INPUT=self.symbols['FCB'])

    def bdos(self, fn, de):
        assert fn in (2,9,15,16,20,25,26,32), ('unexpected mutation/service', fn)
        if fn == 2:
            self.console += chr(de & 255)
            return de & 255
        if fn == 32:
            previous = self.user
            if de & 255 != 255:
                self.user = de & 255
            return previous
        return super().bdos(fn, de)


def system_preflight():
    """Reject a stale core or changed disk before any assembly/emulator work."""
    with tempfile.TemporaryDirectory(prefix='noah-system-gate-') as tmp:
        root = Path(tmp)
        folder = root/'trs80gp'; folder.mkdir()
        image = folder/'system.dmk'; image.write_bytes(b'fixture disk')
        report = {'image':image.name,'sha256':sha(image.read_bytes()),
                  'source':{'revision':'fixture','inputs':{
                      'src/bdos/unified.mac':sha((ROOT/'src/bdos/unified.mac').read_bytes())}}}
        receipt = folder/'report.json'
        receipt.write_text(json.dumps(report))
        assert verify_system(root, ['trs80gp'])['trs80gp']['source_revision']=='fixture'
        report['source']['inputs']['src/bdos/unified.mac']='obsolete'
        receipt.write_text(json.dumps(report))
        try:
            verify_system(root, ['trs80gp'])
        except ValueError as error:
            assert 'stale or unverified' in str(error)
        else:
            raise AssertionError('stale resident core accepted')
        report['source']['inputs']['src/bdos/unified.mac']=sha((ROOT/'src/bdos/unified.mac').read_bytes())
        receipt.write_text(json.dumps(report)); image.write_bytes(b'changed disk')
        try:
            verify_system(root, ['trs80gp'])
        except ValueError as error:
            assert 'differs from its build report' in str(error)
        else:
            raise AssertionError('changed system image accepted')
    return {'current_identity':'PASS','stale_core_refusal':'PASS','changed_image_refusal':'PASS'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'build/noah-proof/host')
    p.add_argument('--z80pack', type=Path, default=Path.home()/'projects/git/z80pack')
    a = p.parse_args()
    preflight = system_preflight()
    a.output.mkdir(parents=True, exist_ok=True)
    report = build(Path.home()/'bin/z80asm', a.output/'cross')
    with tempfile.TemporaryDirectory(prefix='noah-proof-core-') as tmp:
        w = Path(tmp)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for n in ('simmem.h','simport.h'):
            shutil.copy2(a.z80pack/'z80sim/srcsim'/n, w/n)
        (w/'shim.c').write_text(SHIM)
        core = a.z80pack/'z80core'
        subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),
                        str(w/'shim.c'),str(core/'simglb.c'),
                        *map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        cross = a.output/'cross'
        m = Proof(C.CDLL(str(w/'core.so')), (cross/'PROOF.COM').read_bytes(),
                  (cross/'PROOF.lst').read_text())
        ovl = (cross/'NOAH.OVL').read_bytes()
        need = report['required_ceiling']
        outcomes = {}
        def check(name, files, result, tpa=0xd501, drive=2, user=7, failures=None):
            text = m.run('', files, tpa=tpa, drive=drive, user=user, failures=failures)
            assert result in text, (name, text)
            assert m.user == user and m.drive == drive and m.dma == 128
            if not failures or 'close_input' not in failures:
                assert not m.opened
            assert not m.created and not m.renamed and not m.deleted
            m.intact()
            assert not any(m.mem[tpa:0xd800]), (name, 'protected memory changed')
            outcomes[name] = {'status':'PASS', 'console':text.strip()}
        local = diskkey(2,'NOAH.OVL',7)
        fallback = diskkey(1,'NOAH.OVL',0)
        check('simultaneous LBR/UNCR and exact decoded bytes', {local:ovl}, 'PROOF PASS')
        check('A0 fallback and caller DU restoration', {fallback:ovl}, 'PROOF PASS')
        check('exact minimum', {local:ovl}, 'PROOF PASS', tpa=need)
        check('one below minimum', {local:ovl}, 'LOW TPA', tpa=need-1)
        check('terminal RSX reduced TPA', {local:ovl}, 'LOW TPA', tpa=0xc501)
        check('no arbitrary DU scan', {diskkey(3,'NOAH.OVL',7):ovl}, 'PROOF INVALID')
        check('missing companion', {}, 'PROOF INVALID')
        for name, at, recalc in (('signature',0,True),('ABI',4,True),('count',6,True),
               ('build mismatch',8,True),('length',16,True),('offset',28,True),
               ('entry',36,True),('workspace',38,True),('body CRC',128,False),
               ('CRC field',124,False)):
            bad = bytearray(ovl); bad[at] ^= 1
            if recalc:
                bad[124:128] = bytes(4)
                struct.pack_into('<I',bad,124,zlib.crc32(bad))
            check(name, {local:bytes(bad),fallback:ovl}, 'PROOF INVALID')
        check('truncated companion', {local:ovl[:-128]}, 'PROOF INVALID')
        check('trailing record', {local:ovl+bytes(128)}, 'PROOF INVALID')
        check('read error', {local:ovl}, 'PROOF INVALID', failures={'read':2})
        check('close error', {local:ovl}, 'PROOF INVALID', failures={'close_input':1})
        (a.output/'report.json').write_text(json.dumps({'scope':__doc__,
             'layout':report,'system_preflight':preflight,'checks':outcomes},indent=2)+'\n')
        print('PASS: overlay validation, read/decode callbacks, bounds, refusal and original-file preservation')


if __name__ == '__main__':
    main()
