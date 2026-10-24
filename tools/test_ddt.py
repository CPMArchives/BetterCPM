#!/usr/bin/env python3
"""Require adaptation-only core hook, pure /VER, relocation and baseline isolation."""
from pathlib import Path
import json,hashlib
from build_ddt import ROOT,BUILD,assemble,original,payload_source
from ddt_source import zero_storage
from test_utility_versions import runner,output
from build_ddt import version_text


def main():
    image=(BUILD/'DDT.COM').read_bytes()
    for tail in ['/VER',' /ver  ','/VeR','/VER x','x /VER','/VER /VER','/VER /B']:
        c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        before=bytes(c.mem[:128]);c.run(256,limit=100000)
        expected=version_text()
        assert output(c)==expected,(tail,output(c))
        assert bytes(c.mem[:128])==before,'version query altered page zero'
    # The combined transcription preserves all core bytes before adaptation.
    asm=assemble(zero_storage(original('DDT1ASM.ASM')),BUILD/'baseline-asm.bin',intel=True)
    mon=assemble(zero_storage(original('DDT2MON.ASM')),BUILD/'baseline-mon.bin',intel=True)
    baseline=asm+bytes(0x680-len(asm))+mon[0x680:]
    joined=assemble(payload_source(adapt=False),BUILD/'baseline-combined.bin')
    assert joined==baseline
    adapted=(BUILD/'payload-0000.bin').read_bytes()
    listing=(BUILD/'payload-0000.lst').read_text()
    from test_utility_versions import address
    hook=address(listing,'GETBUFF')
    changes=[i for i,(a,b) in enumerate(zip(adapted,baseline)) if a!=b]
    assert changes and all(hook<=i<hook+15 for i in changes),changes
    assert len(adapted)>len(baseline) and adapted[hook]==0xc3
    reference=ROOT/'third_party/dri-ddt/DDT.COM'
    assert hashlib.sha256(reference.read_bytes()).hexdigest()=='d79890f0a637aee317a255bdac6b27215b1ad4452a1b6da822828bcba5a49ecf'
    result={'status':'PASS','version_purity_cases':7,'core_patch_file_offsets':changes,
            'core_getbuff_offset':hook,'baseline_core_bytes':len(baseline),'adaptation_payload_bytes':len(adapted),
            'historical_reference_unchanged':True,'scope':'Original-source translation/combined parity, only GETBUFF changes inside core, /VER identity and page-zero purity.'}
    (BUILD/'compatibility-report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
