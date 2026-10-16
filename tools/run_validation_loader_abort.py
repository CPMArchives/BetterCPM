#!/usr/bin/env python3
"""Inject a one-shot cross-user full-COM READ failure, then exercise Ctrl-C."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','diskdefs','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image'];assert sha(original)==report['sha256'] and report['target']=='z80pack'
    a.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='loader-abort-',dir=a.output.resolve()))
    disks=work/'disks';disks.mkdir()
    for letter in 'ab':shutil.copy2(original,disks/f'drive{letter}.dsk')
    shutil.copy2(a.diskdefs,work/'diskdefs')
    def install(path,drive,user):
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),str(path),f'{user}:'+path.name],cwd=work,check=True)
    assembler=Path.home()/'bin/z80asm';fixtures=ROOT/'tests/fixtures/conformance'
    hook=L['RSX_STATE']+1;readptr=L['BIOS']+40
    template=fixtures/'loadfault.mac'
    source=template.read_text().replace('@HOOK@',str(hook)).replace('@CPXHEAD@',str(L['SYSTEM']+0x86)).replace('@READPTR@',str(readptr)).replace('@DEST@',str(L['SYSTEM']+0x70))
    code=assemble(assembler,source,work/'hook.bin',work/'hook.lst',hook)
    assert len(code)<=40, 'fault provider exceeds unused empty reconstruction slots'
    # Last three bytes are JP saved_read. No runtime source is patched.
    old_operand=hook+len(code)-2
    installer=f"""        ORG 100H
        LD A,({L['RSX_STATE']})
        OR A
        RET NZ
        LD HL,DATA
        LD DE,{hook}
        LD BC,{len(code)}
        LDIR
        LD HL,({readptr})
        LD ({old_operand}),HL
        LD HL,{hook}
        LD ({readptr}),HL
        RET
DATA: DB {','.join(map(str,code))}
        END
"""
    setup=work/'LFAULT.COM';assemble(assembler,installer,setup,work/'setup.lst',0x100);install(setup,'a',0)
    state=work/'STATE.COM';assemble(assembler,(fixtures/'returnstate.mac').read_text(),state,work/'state.lst',0x100);install(state,'a',0)
    capacity=(L['TPA']-0x100)//128*128
    source=(fixtures/'fullreturn.mac').read_text().replace('@COUNT@',str(capacity-256)).replace('@ROUTE@','RET').replace('@EXIT@','        RET')
    program=work/'ERET.COM';code=assemble(assembler,source,program,work/'eret.lst',0x100)
    assert len(code)<=256;program.write_bytes(code.ljust(capacity,b'\xa5'))
    install(program,'b',7)
    trace=work/'transcript.bin';prompt=b'B31>_ '
    commands=[(b'B31:\r',prompt,30),(b'A0:LFAULT\r',prompt,30),
              (b'B7:ERET\r',b'Bad Sector',30),(b'\x03',prompt,30),
              (b'A0:STATE\r',f'STATE D=01 U=1F TOP={L["TPA"]:04X}'.encode(),30),
              (b'',prompt,30),(b'CPX LIST\r',b'RCP',30),(b'',prompt,30),
              (b'RSX LIST\r',b'No RSXs loaded',30),(b'',prompt,30),
              (b'BYE\r',b'System halted',10)]
    transcript=session(a.simulator.resolve(),disks,commands,trace)
    assert b'FULL-TPA RET ENTERED' not in transcript and b'PATTERN OR RETURN FAILED' not in transcript
    assert transcript.count(b'Bad Sector')==1 and sha(original)==report['sha256']
    result={'status':'PASS','caller':'B31','lookup':'B7','read_failure_at_destination_at_least':'C000h',
            'program_not_executed':True,'caller_du_restored':True,'rcp_reconstructed':True,'baseline_sha256':sha(original),
            'provider_source_sha256':sha(template),'provider_binary_sha256':sha(work/'hook.bin'),
            'installed_setup_sha256':sha(setup),'transcript_sha256':sha(trace),
            'scope':'one-shot final BIOS READ fault; Ctrl-C after the load reached and overwrote the CCP prefix; no controller retry claim'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','evidence':str(work)},indent=2))


if __name__=='__main__':main()
