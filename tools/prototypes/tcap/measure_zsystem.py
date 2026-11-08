"""Measure original Microsoft REL modules, dependency closures and linked VLIB.

Input: unmodified LIBS45A.LBR (historical VLIB 4.5 distribution). No historical
source is vendored. CrLZH decoding checks the original member checksum. REL
container bytes and CP/M record padding are not counted as executable memory.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from test_unlzh import decode
from test_usq import SHIM


class Bits:
    def __init__(self,data):self.data=data;self.pos=0
    def get(self,n):
        if self.pos+n>len(self.data)*8:raise ValueError('truncated REL stream')
        value=0
        for _ in range(n):
            value=(value<<1)|((self.data[self.pos//8]>>(7-self.pos%8))&1);self.pos+=1
        return value
    def address(self):return self.get(2),self.get(8)+(self.get(8)<<8)
    def name(self):
        name=''.join(chr(self.get(8)) for _ in range(self.get(3)))
        if not name or any(not 32<=ord(c)<=126 for c in name):raise ValueError('invalid REL symbol')
        return name
    def align(self):self.pos=(self.pos+7)//8*8


def parse_rel(data,library):
    """Read the Microsoft subset actually present; fail on unhandled records."""
    bits=Bits(data);modules=[];module=None
    def emit(payload,kind=None):
        if module is None:raise ValueError('payload outside module')
        if kind is not None:module['relocations'][len(module['image'])]=kind
        module['image'].extend(payload)
    while True:
        if bits.get(1)==0:emit(bytes((bits.get(8),)));continue
        kind=bits.get(2)
        if kind:
            if kind==3:raise ValueError('common relocation not supported')
            emit(bytes((bits.get(8),bits.get(8))),kind);continue
        op=bits.get(4)
        if op==2:
            if module is not None:raise ValueError('nested module')
            name=bits.name();module={'library':library,'ordinal':len(modules),'name':name,
                'code_bytes':None,'data_bytes':None,'exports':{},'chains':[],
                'image':bytearray(),'relocations':{},'entry_declarations':[]}
        elif op==0:module['entry_declarations'].append(bits.name())
        elif op==6:
            address=bits.address();module['chains'].append((bits.name(),address))
        elif op==7:
            address=bits.address();name=bits.name()
            if name in module['exports']:raise ValueError('duplicate entry')
            module['exports'][name]=address
        elif op in (10,13):
            kind,value=bits.address()
            module['data_bytes' if op==10 else 'code_bytes']=value
        elif op==14:
            bits.address();bits.align()
            if module['code_bytes'] is None or len(module['image'])>module['code_bytes']:
                raise ValueError(('emitted code exceeds segment',module['name']))
            # Microsoft permits an uninitialized reservation at the end of a
            # program segment (e.g. SYSLIB $MEMRY). It still consumes memory.
            module['emitted_code_bytes']=len(module['image'])
            module['image'].extend(bytes(module['code_bytes']-len(module['image'])))
            if module['data_bytes'] is None:raise ValueError('missing data size')
            if set(module['exports'])!=set(module['entry_declarations']):raise ValueError('entry directory mismatch')
            for kind,address in module['exports'].values():
                if kind not in (0,1,2):raise ValueError('unsupported export segment')
                if kind and address>module['code_bytes' if kind==1 else 'data_bytes']:raise ValueError('export outside segment')
            modules.append(module);module=None
        elif op==15:
            if module is not None:raise ValueError('unterminated module')
            return modules
        else:raise ValueError(f'unhandled REL record {op} at bit {bits.pos}')


def read_archive(path,out):
    raw=path.read_bytes();directory=struct.unpack_from('<H',raw,14)[0]
    result={};manifest=[]
    for offset in range(32,directory*128,32):
        entry=raw[offset:offset+32]
        if entry[0]!=0 or entry[9:12]!=b'RYL':continue
        name=entry[1:9].decode('ascii').strip()
        if name not in ('VLIB','Z3LIB','SYSLIB'):continue
        start,count=struct.unpack_from('<HH',entry,12)
        compressed=raw[start*128:(start+count)*128]
        expanded,used,rebuilds=decode(compressed)
        (out/(name+'.REL')).write_bytes(expanded)
        result[name]=parse_rel(expanded,name)
        manifest.append({'library':name,'rel_file_bytes':len(expanded),
            'sha256':hashlib.sha256(expanded).hexdigest(),'compressed_member_records':count,
            'compressed_bytes_consumed':used})
    if set(result)!=set(('VLIB','Z3LIB','SYSLIB')):raise ValueError('missing original library')
    return result,manifest


def closure(libraries,roots):
    providers={}
    for modules in libraries.values():
        for module in modules:
            for symbol in module['exports']:providers.setdefault(symbol,[]).append(module)
    selected={};pending=[s.upper()[:6] for s in roots]
    while pending:
        name=pending.pop();matches=providers.get(name,[])
        if len(matches)!=1:raise ValueError(('ambiguous/unresolved symbol',name,len(matches)))
        module=matches[0];key=(module['library'],module['ordinal'])
        if key in selected:continue
        selected[key]=module;pending.extend(s for s,_ in module['chains'])
    return [m for modules in libraries.values() for m in modules if (m['library'],m['ordinal']) in selected]


def link(modules,base=0x8000):
    code_size=sum(m['code_bytes'] for m in modules);data_size=sum(m['data_bytes'] for m in modules)
    code_pos=0;data_pos=code_size;locations={};exports={}
    for m in modules:
        key=m['library'],m['ordinal'];locations[key]=(0,base+code_pos,base+data_pos)
        for name,(kind,offset) in m['exports'].items():exports[name]=locations[key][kind]+offset
        code_pos+=m['code_bytes'];data_pos+=m['data_bytes']
    image=bytearray(code_size+data_size)
    for m in modules:
        bases=locations[m['library'],m['ordinal']];original=m['image'];code=bytearray(original)
        for offset,kind in m['relocations'].items():
            value=struct.unpack_from('<H',original,offset)[0]
            struct.pack_into('<H',code,offset,value+bases[kind])
        external_sites=set()
        for name,(kind,offset) in m['chains']:
            while kind or offset:
                if kind!=1 or offset+1>=len(original):raise ValueError('external chain outside code')
                if offset in external_sites:raise ValueError('cyclic/shared external chain')
                external_sites.add(offset)
                next_offset=struct.unpack_from('<H',original,offset)[0]
                next_kind=m['relocations'].get(offset,0)
                struct.pack_into('<H',code,offset,exports[name])
                kind,offset=next_kind,next_offset
        at=bases[1]-base;image[at:at+len(code)]=code
    return bytes(image),exports


def cpu_checks(image,exports,out):
    core=Path.home()/'projects/git/z80pack/z80core'
    (out/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):shutil.copy2(core.parent/'z80sim/srcsim'/name,out/name)
    shim=SHIM.replace('static WORD readpc, writepc;','static WORD readpc, writepc;\nunsigned low_sp;')
    shim=shim.replace('cpu_error=0; tmax=100000000;','cpu_error=0; tmax=100000000; low_sp=SP;')
    shim=shim.replace('if(PC==65535) return i;','if(SP<low_sp) low_sp=SP;\n  if(PC==65535) return i;')
    (out/'shim.c').write_text(shim)
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{out}',f'-I{core}',str(out/'shim.c'),str(core/'simglb.c'),
        *map(str,sorted(core.glob('simz80*.c'))),'-o',str(out/'core.so')],check=True)
    lib=C.CDLL(str(out/'core.so'));memory=(C.c_ubyte*65536).in_dll(lib,'memory')
    registers={n:C.c_ubyte.in_dll(lib,n) for n in 'AFBCDEHL'}
    sp=C.c_ushort.in_dll(lib,'SP');low_sp=C.c_uint.in_dll(lib,'low_sp')
    memory[:]=bytes(65536);memory[0x8000:0x8000+len(image)]=image
    memory[1:3]=(0xf003).to_bytes(2,'little');memory[0xf00c]=0xc9
    captured=bytearray()
    def callback(kind):
        if kind!=0:raise AssertionError('unexpected console input')
        captured.append(registers['C'].value)
    hook=C.CFUNCTYPE(None,C.c_int)(callback);lib.set_hooks(0xf00c,0xf009,hook)
    env=0x5000;memory[env+0x2b]=4
    strings=[b'\x1b[2J',b'\x1b[%i%d;%dH',b'\x1b[K',b'\x1b[7m',b'\x1b[0m',b'\x1b[0m',b'\x1b[0m',b'',b'',b'\x1b[J',b'',b'',b'',b'']
    tcap=bytearray(b'TCAP BENCH'.ljust(13,b' ')+bytes(3)+bytes((11,22,12,8))+bytes(3))
    tcap+=b''.join(s+b'\0' for s in strings);tcap[13]=len(tcap)
    tcap+=bytes(1+4+13);assert len(tcap)<=128
    memory[env+128:env+256]=tcap.ljust(128,b'\0')
    checks=[]
    def invoke(name,hl,expected):
        captured.clear();registers['H'].value,registers['L'].value=hl>>8,hl&255;sp.value=0x7000
        steps=lib.test_run(exports[name[:6]],1000000)
        if steps<0 or captured!=expected:raise AssertionError((name,steps,bytes(captured),expected))
        if sp.value!=0x7000:raise AssertionError('stack imbalance')
        checks.append({'routine':name,'HL':hl,'output_hex':captured.hex(),'steps':steps,
            'observed_stack_bytes_including_entry_return':0x7000-low_sp.value})
    invoke('Z3VINIT',env,b'')
    for name,expected in [('TINIT',b'\x1b[0m'),('CLS',b'\x1b[2J'),('EREOL',b'\x1b[K'),('STNDOUT',b'\x1b[7m'),('STNDEND',b'\x1b[0m'),('DINIT',b'\x1b[0m')]:invoke(name,0,expected)
    for row,col in ((1,1),(24,80),(100,101),(255,255)):
        invoke('GOTOXY',(row<<8)|col,f'\x1b[{row};{col}H'.encode())
    invoke('Z3VINIT',0,b'');invoke('CLS',0,b'');invoke('GOTOXY',0x0101,b'')
    return {'scope':'original linked library on full Z80 CPU; console BIOS leaf captured, not hardware qualification',
        'checks':checks,'maximum_observed_stack_bytes':max(c['observed_stack_bytes_including_entry_return'] for c in checks),
        'fixture_tcap_allocated_bytes':128,'fixture_tcap_populated_bytes':len(tcap)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    libraries,manifest=read_archive(args.archive,out)
    scenarios={'dimensions':['Z3INIT','GETCRT'],'initialization':['Z3VINIT'],
        'help_emphasis':['Z3VINIT','STNDOUT','STNDEND'],
        'core_screen':['Z3VINIT','TINIT','DINIT','CLS','EREOL','GOTOXY','STNDOUT','STNDEND'],
        'editor_with_dimensions':['Z3VINIT','TINIT','DINIT','CLS','EREOL','GOTOXY','STNDOUT','STNDEND','GETCRT'],
        'entire_vlib':[s for m in libraries['VLIB'] for s in m['exports']]}
    report={'status':'MEASURED original REL module-level closures','distribution':'LIBS45A.LBR, VLIB 4.5',
        'source_url':'https://www.df.lth.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/zcpr33/libs45a.lbr',
        'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'libraries':manifest,'scenarios':{},'resident_tcap_bytes':128,'resident_environment_including_tcap_bytes':256,
        'accounting':'No CP/M record padding, REL encoding, application call sites/header, or preexisting platform BIOS included. DSEG and transitive library dependencies included. No function-level stripping inside modules.'}
    for name,roots in scenarios.items():
        modules=closure(libraries,roots);image,exports=link(modules)
        (out/(name+'.bin')).write_bytes(image)
        code=sum(m['code_bytes'] for m in modules);data=sum(m['data_bytes'] for m in modules)
        report['scenarios'][name]={'roots':roots,'code_bytes':code,'private_data_bytes':data,'linked_bytes':len(image),
            'with_tcap_bytes':len(image)+128,'with_full_environment_bytes':len(image)+256,
            'modules':[{k:m[k] for k in ('library','ordinal','name','code_bytes','data_bytes')} for m in modules],
            'linked_sha256':hashlib.sha256(image).hexdigest()}
        print(name,code,data,len(image),flush=True)
        if args.execute and name=='core_screen':report['cpu']=cpu_checks(image,exports,out)
    (out/'measurement.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],out)


if __name__=='__main__':main()
