#!/usr/bin/env python3
"""Build an independent cpmsim target; preserve the TRS-80 boot artifacts."""
from pathlib import Path
import argparse,re,struct,subprocess,sys,json,hashlib
from build_ccp import assemble
from system_layout import LAYOUT as L
from cpm_tools_bundle import files as cpm_tools_files
ROOT=Path(__file__).resolve().parents[1]
PLATFORM=ROOT/'src/platform/z80pack'
TRACKS=77;SPT=26;RESERVED=7;SIZE=TRACKS*SPT*128

def symbols(path):
 result={}
 for address,name in re.findall(r'^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):',path.read_text(),re.M|re.I):
  result[name]=int(address,16)
 return result

def normalized(text):
 return text.replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--output',type=Path,default=ROOT/'build/z80pack')
 p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
 args=p.parse_args();out=args.output.resolve()
 out.mkdir(parents=True,exist_ok=True)
 disks=out/'disks'
 if disks.exists():raise SystemExit(f'{disks} exists; use a new --output to preserve test media')
 def asm(name,text,base,limit):
  data=assemble(args.assembler,normalized(text),out/(name+'.bin'),out/(name+'.lst'),base)
  if not data or len(data)>limit:raise ValueError(f'{name}: {len(data)} bytes exceeds {limit}')
  return data
 def read(path):return (ROOT/path).read_text()
 # Rebuild common software from current source. These are portable artifacts;
 # target BIOS, disk code, tables and overlays are kept only in our output.
 for name in ('bdos','ccp','rcp_cpx','hello_cpx','rsxloader','rsxvalidator','rsxpublish','rsxresolver','test_service_rsx','svctest','hello_rsx','echo_rsx','zprtc_rsx','fileloader','utilities'):
  subprocess.run([sys.executable,str(ROOT/'tools'/f'build_{name}.py')],check=True,stdout=subprocess.DEVNULL)
 bios_source=read('src/bios/bios.mac')
 # cpmsim port 5 is its CP/M 2 RDR: input.  Keep the common unassigned-reader
 # leaf for machines without a provider and substitute the z80pack binding
 # without enlarging the tightly packed resident BIOS.
 old_reader='BIOREADR:\n        LD      A,01AH\n        RET'
 new_reader='BIOREADR:\n        IN      A,(5)\n        RET'
 if old_reader not in bios_source:raise ValueError('common READER leaf changed')
 bios_source=bios_source.replace(old_reader,new_reader)
 a=bios_source.index('BIOREAD:');b=bios_source.index('; LISTST',a)
 bios_source=bios_source[:a]+read('src/platform/z80pack/recordio.inc')+bios_source[b:]
 bios=asm('bios',bios_source.replace('        INCLUDE biosplat.inc',read('src/platform/z80pack/biosplat.inc')),L['BIOS'],L['FILE']-L['BIOS'])
 bs=symbols(out/'bios.lst');bc=symbols(ROOT/'build/bdos/bdos.lst')
 equ=lambda mapping,names:''.join(f'{k} EQU 0{mapping[k]:04X}H\n' for k in names)
 bioslinks=equ(bs,('BIO_DRIVE','BIO_TRACK','BIO_SECTOR','BIO_DMA','BIO_QUART'))
 disk=asm('disk',read('src/platform/z80pack/disk.mac').replace('        INCLUDE bioslinks.inc',bioslinks),L['DISK'],L['BIOS']-L['DISK'])
 core=equ(bc,('UB_DMA','UB_DRIVE','UB_USERNO','UB_COLUMN','UB_LISTE'))
 ext=asm('extensions',read('src/system/extensions.mac').replace('        INCLUDE core.inc',core).replace('        INCLUDE versions.inc',read('src/bdos/versions.inc')),L['EXTENSIONS'],L['DISK']-L['EXTENSIONS'])
 es=symbols(out/'extensions.lst')
 config='        INCLUDE layout.inc\n        ASEG\n        ORG LY_CFG\n        JP Z_UNSUP\n        JP Z_UNSUP\n        JP Z_UNSUP\n        JP BF_CPXCTL\nZ_UNSUP: LD A,0FFH\n        JP EX_RETURN\n'+equ(es,('EX_RETURN','BCX_MVAL'))
 tail=read('src/bios/config.mac').split('CPTCOUNT EQU',1)[1].split('CF_GETPH:',1)[0]
 config+='CPTCOUNT EQU'+tail+'\n        END\n'
 ctl=asm('config',config,L['CONFIG'],1024)
 tables='        INCLUDE layout.inc\n        ASEG\n        ORG LY_TAB\n'
 for i in range(4):
  tables+=f'''ZDPH{i}: DW 0,0,0,0,LY_DIR,ZDPH{i}+17,ZCSV,ZALV
        DB {i}
        DW 26
        DB 3,7,0
        DW {226 if i==0 else 249},63
        DB 0C0H,0
        DW 16,{RESERVED if i==0 else 0}
        DB 77,26,0,0
        DB '''+','.join(map(str,range(1,27)))+'''
        REPT 18
        DB 0
        ENDM
'''
 tables+='ZALV: DS 128\nZCSV: DS 32\n        END\n'
 tab=asm('tables',tables,L['TABLES'],L['RSX_STATE']-L['TABLES'])
 gateway=asm('gateway',read('src/system/gateway.mac'),L['SYSTEM'],L['BDOS']-L['SYSTEM'])
 reload=read('src/platform/trs80m4/commandreload.mac')
 a=reload.index('        PUSH    HL\n',reload.index('CRNEXT:'));b=reload.index('\nCRFAIL:',a)
 reload=reload[:a]+'''        INC     A
        LD      (CRSLOT),A
        DEC     A
        ADD     A,A
        ADD     A,A
        ADD     A,108
        LD      E,A
        LD      D,0
        LD      B,4
        JP      LY_DISK+15
'''+reload[b:]
 loader=asm('reloader',reload,L['RELOADER'],896)
 boot=asm('boot',read('src/platform/z80pack/boot.mac'),0,128)
 resident=bytearray(L['DIRBUF']-L['SYSTEM'])
 parts=[(L['SYSTEM'],gateway),(L['BDOS'],(ROOT/'build/bdos/bdos.bin').read_bytes()),(L['EXTENSIONS'],ext),(L['DISK'],disk),(L['BIOS'],bios),(L['FILE'],(ROOT/'build/system/fileloader.bin').read_bytes()),(L['TABLES'],tab)]
 for address,data in parts:resident[address-L['SYSTEM']:address-L['SYSTEM']+len(data)]=data
 if len(resident)>52*128:raise ValueError('resident carrier too small')
 raw=bytearray(b'\xe5'*SIZE)
 def put(record,data,capacity):
  if len(data)>capacity:raise ValueError('carrier overflow')
  raw[record*128:record*128+capacity]=data.ljust(capacity,b'\0')
 put(0,boot,128);put(8,resident,52*128);put(60,loader,1024);put(68,ctl,1024)
 gateway_tail=bytes((0xc3,L['BDOS']&255,L['BDOS']>>8))
 def rsx_overlay(path):return path.read_bytes().ljust(1021,b'\0')+gateway_tail
 put(76,rsx_overlay(ROOT/'build/system/rsxloader.bin'),1024)
 put(84,rsx_overlay(ROOT/'build/system/rsxvalidator.bin'),1024)
 put(92,rsx_overlay(ROOT/'build/system/rsxpublish.bin'),1024)
 put(100,rsx_overlay(ROOT/'build/system/rsxresolver.bin'),1024)
 put(108,(ROOT/'build/ccp/ccp.rlm').read_bytes(),13*512)
 # CP/M 2.2, 1K allocation blocks, byte block numbers, 64 directory entries.
 from sysgen_image import sysgen_image
 files=[('SYSGEN.DAT',sysgen_image(bytes(resident),L['SYSTEM'],52,8,26))]
 for name in ('RCP.CPX','HELLO.CPX'):files.append((name,(ROOT/'build/cpx'/name).read_bytes()))
 for f in sorted((ROOT/'build/utilities').glob('*.COM')):files.append((f.name,f.read_bytes()))
 for name,data in cpm_tools_files(ROOT):files.append((name,data))
 for name in ('HELLO.RSX','ECHO.RSX','BATCHIO.RSX','ZPRTC.RSX','TEST.RSX'):files.append((name,(ROOT/'build/rsx'/name).read_bytes()))
 files.append(('DISK.FDF',(ROOT/'third_party/montezuma/DISK.FDF').read_bytes()))
 # A small transient proves that load and warm return use this target BIOS.
 hello=bytes([0x11,0x0b,1,0x0e,9,0xcd,5,0,0xc3,0,0])+b'BetterCP/M on z80pack\r\n$'
 files.append(('HELLO.COM',hello))
 # cpmsim hardware control: unlock, then halt the emulator cleanly.
 files.append(('BYE.COM',bytes((0x3e,0xaa,0xd3,160,0x3e,0x80,0xd3,160,0x76))))
 start=RESERVED*SPT*128;block=2;entry=0
 for name,data in files:
  stem,suffix=name.split('.');payload=data.ljust((len(data)+127)//128*128,b'\x1a')
  for chunkstart in range(0,max(len(payload),1),16384):
   chunk=payload[chunkstart:chunkstart+16384];count=(len(chunk)+1023)//1024
   if entry>=64 or block+count>227:raise ValueError('filesystem full')
   e=bytearray(32);e[1:9]=stem.ljust(8).encode();e[9:12]=suffix.ljust(3).encode()
   extent=chunkstart//16384;e[12]=extent&31;e[14]=extent>>5;e[15]=len(chunk)//128
   e[16:16+count]=bytes(range(block,block+count))
   raw[start+entry*32:start+(entry+1)*32]=e
   raw[start+block*1024:start+block*1024+len(chunk)]=chunk
   entry+=1;block+=count
 disks.mkdir();(disks/'drivea.dsk').write_bytes(raw)
 for letter in 'bcd':(disks/f'drive{letter}.dsk').write_bytes(b'\xe5'*SIZE)
 (out/'diskdefs').write_text(''.join(f'diskdef bettercpm-z80pack-{name}\n seclen 128\n tracks 77\n sectrk 26\n blocksize 1024\n maxdir 64\n skew 1\n boottrk {off}\n os 2.2\nend\n' for name,off in [('system',RESERVED),('data',0)]))
 simulator=Path.home()/'CPM/z80pack/cpmsim/cpmsim'
 (out/'launch-z80pack.command').write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nPATH="'+str(simulator.parent/'srctools')+':$PATH"\nexport PATH\nexec "'+str(simulator)+'" -z -d "$PWD/disks" "$@"\n')
 (out/'launch-z80pack.command').chmod(0o755)
 (out/'manifest.json').write_text(json.dumps({'target':'z80pack/cpmsim','tracks':77,'records_per_track':26,'record_bytes':128,'reserved_tracks':RESERVED,'allocation_kib':227,'sha256':hashlib.sha256(raw).hexdigest(),'shared_bdos_sha256':hashlib.sha256((ROOT/'build/bdos/bdos.bin').read_bytes()).hexdigest()},indent=2)+'\n')
 print(f'Created {disks}/drivea.dsk; 227 KiB allocation area; three 250 KiB data disks')
if __name__=='__main__':main()
