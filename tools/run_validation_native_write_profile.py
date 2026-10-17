#!/usr/bin/env python3
"""Measure native write paths with boundary-only output and instruction tracing.

Uses private copies only; timings are emulated CPU t-states, not a claim about
real hardware throughput. Caller supplies independently prepared raw data media.
"""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw,add_file
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from run_validation_model4 import sha,audit_files
from test_sysgen_install import screen
from trs80gp_launch import run
from system_layout import LAYOUT


def source():
    lines=['        ORG 0100H','        LD SP,09000H',
           '        LD DE,DMA','        LD C,26','        CALL 5']
    for name,fn in [('SEQ',21),('RND',34)]:
        lines += ['        LD HL,INITIAL','        LD DE,FCB','        LD BC,36','        LDIR',
                  '        LD DE,FCB','        LD C,22','        CALL 5','        CP 0FFH','        JP Z,FAIL',
                  f'        LD DE,{name}BEG','        LD C,9','        CALL 5',
                  '        XOR A','        LD (COUNT),A',f'{name}START: NOP',f'{name}LOOP:',
                  '        LD A,(COUNT)','        LD (FCB+33),A',
                  '        LD DE,FCB',f'        LD C,{fn}','        CALL 5',
                  '        LD (RESULT),A','        OR A','        JP NZ,FAIL',
                  '        LD A,(COUNT)','        INC A','        LD (COUNT),A','        CP 8',f'        JP C,{name}LOOP',
                  f'{name}STOP: NOP',f'        LD DE,{name}END','        LD C,9','        CALL 5',
                  '        LD DE,FCB','        LD C,16','        CALL 5','        CP 0FFH','        JP Z,FAIL',
                  '        LD HL,INITIAL','        LD DE,FCB','        LD BC,36','        LDIR',
                  '        LD DE,FCB','        LD C,19','        CALL 5','        CP 0FFH','        JP Z,FAIL']
    lines += ['        LD DE,DONE','        LD C,9','        CALL 5','        JP 0',
              'FAIL: LD DE,BAD','        LD C,9','        CALL 5','        JP 0',
              "SEQBEG: DB 13,10,'PERF SEQ BEGIN',13,10,'$'", "SEQEND: DB 13,10,'PERF SEQ END',13,10,'$'",
              "RNDBEG: DB 13,10,'PERF RND BEGIN',13,10,'$'", "RNDEND: DB 13,10,'PERF RND END',13,10,'$'",
              "DONE: DB 13,10,'PERF COMPLETE',13,10,'$'", "BAD: DB 13,10,'PERF FAILED',13,10,'$'",
              "INITIAL: DB 0,'PERFTMP ','DAT'", '        DEFS 24,0',
              'FCB: DEFS 36,0','COUNT: DB 0','RESULT: DB 0','DMA: DEFS 128,0A5H','        END']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline','data-raw','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    w=Path(tempfile.mkdtemp(prefix='native-write-',dir=a.output.resolve()))
    report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image']
    assert sha(original)==report['sha256'] and report['target']=='trs80gp'
    text=source();(w/'PERF8.ASM').write_text(text)
    com=w/'PERF8.COM';data=assemble(Path.home()/'bin/z80asm',text,com,w/'perf8.lst',0x100)
    syms={}
    for line in (w/'perf8.lst').read_text().splitlines():
        m=re.match(r'^([0-9a-f]{4})\s+.*\b(SEQSTART|SEQSTOP|RNDSTART|RNDSTOP):',line,re.I)
        if m:syms[m[2].upper()]=int(m[1],16)
    assert len(syms)==4
    raw=extract_raw(original.read_bytes());add_file(raw,'PERF8.COM',data);(w/'a.dmk').write_bytes(build(bytes(raw)))
    shutil.copy2(a.data_raw,w/'b-before.raw');(w/'b.dmk').write_bytes(build(a.data_raw.read_bytes()))
    # Match the native 800K data format; never trust host geometry auto-probing.
    (w/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    # Public BIOS entries count logical disk requests, not physical FDC transfers.
    syms.update(BIOS_READ=LAYOUT['BIOS']+39,BIOS_WRITE=LAYOUT['BIOS']+42,
                DISK_READ=LAYOUT['DISK']+9,DISK_WRITE=LAYOUT['DISK']+12)
    trace=','.join(f'{v:x}' for v in syms.values())
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-tr',trace,
         '-d0',str(w/'a.dmk'),'-d1',str(w/'b.dmk'),'-itime','15000',
         '-iw','Type TYPE README.TXT for more','-id','6000']+key_args('B:\r')+['-id','6000','-it']+key_args('A0:PERF8\r')
    for marker in ('PERF SEQ BEGIN','PERF SEQ END','PERF RND BEGIN','PERF RND END','PERF COMPLETE'):
        cmd+=['-iw',marker,'-it']
    cmd+=['-id','1200','-it','-ix']
    (w/'command.json').write_text(json.dumps(cmd,indent=2))
    shutil.copy2(__file__,w/'executed-runner.py')
    run(cmd,cwd=w,timeout=600)
    captures=[screen(f) for f in sorted(w.glob('trs80-text-*.bin'))]
    (w/'screen.txt').write_text('\n--- capture ---\n'.join(captures))
    assert 'PERF COMPLETE' in captures[-1] and not any('PERF FAILED' in s for s in captures)
    events=[]
    for line in (w/'bus-trace-0.txt').read_text().splitlines():
        m=re.match(r'^\s*(\d+) @([0-9a-f]+) z ex\s+(.*)',line,re.I)
        if m:events.append((int(m[1]),int(m[2],16),m[3].strip()))
    measured={}
    for name in ('SEQ','RND'):
        # TPA addresses are reused by boot/command loaders before this program.
        # Accept only our NOP boundary instructions, not earlier code there.
        starts=[i for i,e in enumerate(events) if e[1]==syms[name+'START'] and e[2]=='nop']
        stops=[i for i,e in enumerate(events) if e[1]==syms[name+'STOP'] and e[2]=='nop']
        assert len(starts)==len(stops)==1,(name,starts,stops)
        begin,end=starts[0],stops[0];assert begin<end
        measured[name]={'successful_records':8,'t_states':events[end][0]-events[begin][0],
                        'logical_bios_reads':sum(e[1]==syms['BIOS_READ'] for e in events[begin:end]),
                        'logical_bios_writes':sum(e[1]==syms['BIOS_WRITE'] for e in events[begin:end])}
        for key in ('DISK_READ','DISK_WRITE'):
            if syms[key] in [int(v,16) for v in trace.split(',')]:
                measured[name][key.lower()+'_calls']=sum(e[1]==syms[key] for e in events[begin:end])
    after=extract_raw((w/'b.dmk').read_bytes());(w/'b-after.raw').write_bytes(after)
    before=a.data_raw.read_bytes()
    def live(raw):return [raw[n:n+32] for n in range(0,4096,32) if raw[n]<32]
    assert live(before)==live(after),'live input entries changed or temporary file remains'
    # Independently compare every allocated source block; deleted scratch slots
    # and now-free data may legitimately retain test bytes.
    for e in live(before):
        for pos in range(16,32,2):
            block=int.from_bytes(e[pos:pos+2],'little')
            if block:assert before[block*2048:(block+1)*2048]==after[block*2048:(block+1)*2048]
    used={0,1}
    for e in live(before):
        used.update(int.from_bytes(e[pos:pos+2],'little') for pos in range(16,32,2))
    target=min(set(range(400))-used)
    assert after[target*2048:target*2048+8*128]==bytes([0xA5])*1024, 'written payload missing'
    check=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','native-data','-n',str(w/'b-after.raw')],cwd=w,text=True,capture_output=True)
    (w/'filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
    audit=audit_files(original,w/'a.dmk',report,w)
    result={'status':'PASS','measurements':measured,'trace_symbols':syms,
            'baseline_sha256':sha(original),'data_before_sha256':sha(a.data_raw),
            'system_file_audit':audit,'input_files_preserved':True,
            'final_payload_verified':{'block':target,'records':8,'byte':165},
            'scope':'eight writes; boundary output excluded; logical BIOS counts; t-states include emulated disk waits, not host wall time'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'evidence':str(w),**measured},indent=2))


if __name__=='__main__':main()
