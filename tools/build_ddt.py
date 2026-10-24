#!/usr/bin/env python3
"""Build the BetterCP/M DDT adaptation without altering historical reproduction."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
from ddt_source import translate,zero_storage
from shared_ui import input_source
from utility_versions import identities
from component_inputs import capture, classify
from component_identity import identification
from component_development import select as select_display
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/ddt-development'
ASSEMBLER=Path.home()/'bin/z80asm'


def assemble(text,path,origin=0,intel=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    source=path.with_suffix('.mac');source.write_text(text,encoding='ascii')
    command=[str(ASSEMBLER)]
    if intel:command+=['-8']
    command+=['-fb','-o'+str(path),'-l'+str(path.with_suffix('.lst')),str(source)]
    r=subprocess.run(command,capture_output=True,text=True)
    path.with_suffix('.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    assert '0 error(s)' in r.stdout+r.stderr
    return path.read_bytes()


def original(name):
    return (ROOT/'third_party/dri-ddt'/name).read_bytes().split(b'\0',1)[0].split(b'\x1a',1)[0].decode('ascii').replace('\r','')


def version_text(development=None):
    version,build=identities()['DDT']
    if development is None: development = select_display('utility:DDT', ASSEMBLER, root=ROOT)['development']
    return identification('DDT', version, build, 'Dynamic Debugging Tool', style='numeric', development=development)


def payload_source(base=0,adapt=True):
    a=original('DDT1ASM.ASM');m=original('DDT2MON.ASM')
    a=a[a.index('JLOC1'):];a=re.sub(r'(?m)^\s*END\s*$','',a)
    a=translate(a,private=True)
    m=m[m.index('MODBAS'):];m=m.replace('MODBAS\tEQU\t$',f'MODBAS\tEQU\t{base:05X}H',1)
    m=m.replace('\tDS\t680H','\tDS\tMODBAS+680H-$',1)
    m=re.sub(r'\tIF\tDEBUG\nRSTNUM.*?\tENDIF', 'RSTNUM EQU 7',m,count=1,flags=re.S)
    m=re.sub(r'\tIF\tDEBUG\n\tMVI\tA,\':\'.*?\tENDIF',"\tMVI\tA,'-'",m,count=1,flags=re.S)
    m=re.sub(r'(?m)^\s*END\s*$','',m)
    if adapt:
        first=m.index('GETBUFF:\t;FILL COMMAND BUFFER');last=m.index('\n;\nBLANK:',first)
        m=m[:first]+'GETBUFF:\n\tJMP\tDU_GET\n\tDS\t12\n'+m[last:]
    m=translate(m)
    if adapt:
        template=(ROOT/'src/utilities/ddt.mac').read_text()
        source=template.replace('@origin@',f'{base:05X}H').replace('; @ddt-core@',a+m)
        source=source.replace('; @ddt-input@',(ROOT/'src/utilities/common/ddtinput.inc').read_text())
        source=source.replace('; @ddt-shared@',input_source(standard=True,words=True))
        return zero_storage(source)
    return zero_storage(f'        ASEG\n        ORG {base:05X}H\n'+a+m)+'\n        END\n'


def startup_source(length, development=None):
    text=original('DDT0MOV.ASM')
    text=text.replace('STACK\tEQU\t200H','STACK\tEQU\t400H').replace('MODULE\tEQU\t200H','MODULE\tEQU\t400H')
    text=text.replace('\tdb\t01h\t;lxi instruction\n\tds\t2\t;space for address',f'\tLXI\tB,{length:05X}H')
    text=text.replace('\tJMP\tSTART','\tJMP\tUV_INIT',1)
    start=text.index('SIGNON:');end=text.index('START:',start)
    banner='SIGNON:\n'+''.join('        DB '+str(x)+'\n' for x in version_text(development).encode())+"        DB '$'\n"
    text=text[:start]+banner+text[end:]
    text=re.sub(r'(?m)^\s*END\s*$','',text)
    query=(ROOT/'src/utilities/common/version.inc').read_text();query=query[query.index('\nUV_QUERY:')+1:]
    text=translate(text)+'''\nUV_INIT:
        LD SP,0400H
        PUSH BC
        LD HL,0081H
        LD A,(0080H)
        LD B,A
        LD DE,SIGNON
        CALL UV_QUERY
        POP BC
        JP C,0000H
        JP START
'''+query+'\nST_END:\n        END\n'
    return text


def main():
    global ASSEMBLER
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=BUILD)
    p.add_argument('--assembler',type=Path,default=ASSEMBLER);p.add_argument('--no-install',action='store_true')
    p.add_argument('--target',choices=('z80pack','trs80gp'),default='z80pack')
    p.add_argument('--baseline',type=Path,help='explicit raw input-record reference')
    p.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    a=p.parse_args();ASSEMBLER=a.assembler.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report_path=out/'build-report.json';report_path.unlink(missing_ok=True)
    reference=json.loads(a.baseline.read_text()) if a.baseline else None
    before=capture('utility:DDT',ASSEMBLER,root=ROOT,target=a.target)
    display=select_display('utility:DDT',ASSEMBLER,root=ROOT,target=a.target,mode=a.identity_state)
    parity={}
    for name in ['DDT0MOV.ASM','DDT1ASM.ASM','DDT2MON.ASM']:
        original_text=original(name)
        raw=assemble(original_text,out/('intel-'+name+'.bin'),intel=True)
        trans=assemble(translate(original_text),out/('z80-'+name+'.bin'))
        assert raw==trans,('translation changed bytes',name)
        parity[name]=len(raw)
    images={}
    for base in [0,0x100,0x3100]:images[base]=assemble(payload_source(base),out/f'payload-{base:04x}.bin')
    length=len(images[0]);assert all(len(x)==length for x in images.values())
    marks=[i for i,(x,y) in enumerate(zip(images[0],images[0x100])) if x!=y]
    for base in [0x100,0x3100]:
        r=bytearray(images[0])
        for i in marks:r[i]=(r[i]+(base>>8))&255
        assert bytes(r)==images[base],('relocation mismatch',base)
    bitmap=bytearray((length+7)//8)
    for i in marks:bitmap[i//8]|=0x80>>(i%8)
    (out/'relocation.bitmap').write_bytes(bitmap)
    stub=assemble(startup_source(length,display['development']),out/'startup.bin',0x100)
    assert len(stub)<=0x200,('bootstrap stack headroom',len(stub))
    result=stub+bytes(0x300-len(stub))+images[0]+bitmap
    result+=bytes((-len(result))%128)
    (out/'DDT.COM').write_bytes(result)
    report={'status':'PASS','version':version_text(display['development']),'file_size':len(result),'payload_size':length,'resident_pages':(length>>8)+1,'bitmap_bytes':len(bitmap),'relocation_marks':len(marks),'startup_bytes':len(stub),'sha256':hashlib.sha256(result).hexdigest(),'translated_core_parity':parity,'historical_reference_sha256':hashlib.sha256((ROOT/'third_party/dri-ddt/DDT.COM').read_bytes()).hexdigest()}
    files=['src/utilities/ddt.mac','src/utilities/common/ddtinput.inc','src/utilities/common/version.inc','src/utilities/common/ui/input.inc','src/utilities/common/ui/wordstar.inc','src/utilities/common/ui/events.inc','metadata/utility-versions.tsv','tools/ddt_source.py','tools/build_ddt.py']
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}
    report['assembler_sha256']=hashlib.sha256(ASSEMBLER.read_bytes()).hexdigest()
    after=capture('utility:DDT',ASSEMBLER,root=ROOT,target=a.target)
    if before!=after or display!=select_display('utility:DDT',ASSEMBLER,root=ROOT,target=a.target,mode=a.identity_state):raise RuntimeError('DDT inputs changed during assembly; no build report emitted')
    if (out/'DDT.COM').read_bytes()!=result:raise RuntimeError('DDT output changed before build report')
    provenance=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,text=True)
    report.update(schema=1,component='utility:DDT',identity=dict(zip(('version','revision'),identities()['DDT'])),
                  artifact={'name':'DDT.COM','bytes':len(result),'sha256':hashlib.sha256(result).hexdigest()},
                  input_record=before,display_selection=display,comparison=classify(before,reference),
                  qualification='not asserted; PASS covers existing build parity guards only',
                  provenance={'repository_commit':provenance.stdout.strip() if provenance.returncode==0 else None,
                              'source_state':'selected input hashes; global cleanliness not asserted'})
    if not a.no_install:
        release=ROOT/'build/utilities/DDT.COM';release.parent.mkdir(parents=True,exist_ok=True);release.write_bytes(result)
    report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
