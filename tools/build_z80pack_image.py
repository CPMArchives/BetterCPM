#!/usr/bin/env python3
"""Build an independent cpmsim target; preserve the TRS-80 boot artifacts."""
from pathlib import Path
import argparse,re,struct,subprocess,sys,json,hashlib
from build_ccp import assemble
from fdf_format import select_fdf
from system_layout import LAYOUT as L
from cpm_tools_bundle import files as cpm_tools_files
ROOT=Path(__file__).resolve().parents[1]
PLATFORM=ROOT/'src/platform/z80pack'
DEFAULT_FORMAT='California Computer Systems (40T, DS, DD, 332K)'

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
 p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
 p.add_argument('--format',default=DEFAULT_FORMAT,
                help='exact DISK.FDF format name')
 p.add_argument('--fdf',type=Path,default=ROOT/'third_party/montezuma/DISK.FDF')
 args=p.parse_args();out=args.output.resolve()
 fmt=select_fdf(args.fdf,args.format)
 record_map=fmt.raw_record_map()
 if fmt.reserved_records < 160:raise SystemExit(f'{fmt.name}: reserved area has {fmt.reserved_records} records; 160 required')
 if fmt.raw_tracks>255 or fmt.raw_track_bytes//128>255:raise SystemExit(f'{fmt.name}: bootstrap geometry exceeds 8-bit cpmsim ports')
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
 for name in ('bdos','ccp','rcp_cpx','hello_cpx','rsxloader','rsxresolver','rsx_runtime_overlays','test_service_rsx','svctest','stateful_test_rsx','stattst','hello_rsx','echo_rsx','fdf_rsx','zprtc_rsx','fileloader','utilities'):
  subprocess.run([sys.executable,str(ROOT/'tools'/f'build_{name}.py')],check=True,stdout=subprocess.DEVNULL)
 bios_source=read('src/bios/bios.mac')
 # cpmsim port 5 is its CP/M 2 RDR: input.  Keep the common unassigned-reader
 # leaf for machines without a provider and substitute the z80pack binding
 # without enlarging the tightly packed resident BIOS.
 reader_pattern=r'(BIOREADR:[^\n]*\n)\s*LD\s+A,01AH\n\s*RET'
 bios_source,replacements=re.subn(reader_pattern,
                                  r'\1        IN      A,(5)\n        RET',
                                  bios_source,count=1)
 if replacements != 1:raise ValueError('common READER leaf changed')
 a=bios_source.index('BIOREAD:');b=bios_source.index('; LISTST',a)
 bios_source=bios_source[:a]+read('src/platform/z80pack/recordio.inc')+bios_source[b:]
 bios=asm('bios',bios_source.replace('        INCLUDE biosplat.inc',read('src/platform/z80pack/biosplat.inc')),L['BIOS'],L['FILE']-L['BIOS'])
 bs=symbols(out/'bios.lst');bc=symbols(ROOT/'build/bdos/bdos.lst')
 equ=lambda mapping,names:''.join(f'{k} EQU 0{mapping[k]:04X}H\n' for k in names)
 bioslinks=equ(bs,('BIO_DRIVE','BIO_TRACK','BIO_SECTOR','BIO_DMA','BIO_QUART'))
 disk_source=read('src/platform/z80pack/disk.mac').replace('        INCLUDE bioslinks.inc',bioslinks)
 disk_source=disk_source.replace('        INCLUDE bootfmt.inc',
                                 f'ZB_SLOTS EQU {fmt.raw_track_bytes//128}\n')
 disk_source=disk_source.replace('        DB ZB_MAP_BYTES',
                                 '        DB '+','.join(map(str,record_map)))
 disk_source=disk_source.replace('        REPT 4\n        DB 8,80,2,0,0,0\n        ENDM',
                                 '        REPT 4\n        DB 5,%d,%d,0,0,0\n        ENDM' % (fmt.cylinders,fmt.sides))
 disk=asm('disk',disk_source,L['DISK'],L['BIOS']-L['DISK'])
 core=equ(bc,('UB_DMA','UB_DRIVE','UB_USERNO','UB_COLUMN','UB_LISTE'))
 ext=asm('extensions',read('src/system/extens.mac').replace('        INCLUDE core.inc',core).replace('        INCLUDE versions.inc',read('src/bdos/versions.inc')),L['EXTENSIONS'],L['DISK']-L['EXTENSIONS'])
 es=symbols(out/'extensions.lst')
 ds=symbols(out/'disk.lst')
 config=read('src/platform/z80pack/config.mac')
 config=config.replace('        INCLUDE bioslinks.inc',bioslinks)
 config=config.replace('        INCLUDE cpxlinks.inc',
                       equ(es,('EX_RETURN','BCX_MVAL')))
 config=config.replace('ZP_PHYSICAL EQU 0FFFFH',
                       f"ZP_PHYSICAL EQU 0{ds['Z_PHYSICAL']:04X}H")
 tail=read('src/bios/config.mac').split('CPTCOUNT EQU',1)[1].split('CF_GETPH:',1)[0]
 config+='CPTCOUNT EQU'+tail+'\n        END\n'
 ctl=asm('config',config,L['CONFIG'],1024)
 tables='        INCLUDE layout.inc\n        ASEG\n        ORG LY_TAB\n'
 for i in range(4):
  binding=fmt.binding(i)
  tables+=f'ZDPH{i}: DW 0,0,0,0,LY_DIR,ZDPH{i}+17,ZCSV+{i * 32},ZALV\n'
  # z80asm accepts a long DB line but silently drops operands beyond its
  # internal line capacity.  Keep each directive short and verify stride.
  for offset in range(0,len(binding),16):
   tables+='        DB '+','.join(str(value) for value in binding[offset:offset+16])+'\n'
 # CONFIG may replace the boot binding with any supported catalogue format.
 # Keep one maximum-size allocation vector for the active BDOS context and a
 # persistent 32-byte checksum vector for each logical drive.  Sizing these
 # workspaces from the boot format corrupts the following drive's checksum
 # state as soon as a larger disk is selected.
 tables+='ZALV: DS 128\nZCSV: DS 128\n'
 tables+='        END\n'
 tab=asm('tables',tables,L['TABLES'],L['RSX_STATE']-L['TABLES'])
 gateway=asm('gateway',read('src/system/gateway.mac'),L['SYSTEM'],L['BDOS']-L['SYSTEM'])
 reload=read('src/platform/trs80m4/ccprelod.mac')
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
 selector=asm('rsxselect',read('src/platform/z80pack/rsxsel.mac'),L['CONFIG']+0x380,128)
 bootfmt=(f'ZB_TRACKS EQU {fmt.raw_tracks}\n'
          f'ZB_SLOTS EQU {fmt.raw_track_bytes//128}\n')
 boot_source=read('src/platform/z80pack/boot.mac').replace('        INCLUDE bootfmt.inc',bootfmt)
 boot_source=boot_source.replace('        DB ZB_MAP_BYTES',
                                 '        DB '+','.join(map(str,record_map)))
 boot=asm('boot',boot_source,0,128)
 resident=bytearray(L['DIRBUF']-L['SYSTEM'])
 parts=[(L['SYSTEM'],gateway),(L['BDOS'],(ROOT/'build/bdos/bdos.bin').read_bytes()),(L['EXTENSIONS'],ext),(L['DISK'],disk),(L['BIOS'],bios),(L['FILE'],(ROOT/'build/system/fileloader.bin').read_bytes()),(L['TABLES'],tab)]
 for address,data in parts:resident[address-L['SYSTEM']:address-L['SYSTEM']+len(data)]=data
 if len(resident)>52*128:raise ValueError('resident carrier too small')
 logical=bytearray(b'\xe5'*fmt.image_bytes)
 def put(record,data,capacity):
  if len(data)>capacity:raise ValueError('carrier overflow')
  logical[record*128:record*128+capacity]=data.ljust(capacity,b'\0')
 loader_carrier=loader.ljust(896,b'\0')+selector.ljust(128,b'\0')
 put(0,boot,128);put(8,resident,52*128);put(60,loader_carrier,1024);put(68,ctl,1024)
 gateway_tail=bytes((0xc3,L['BDOS']&255,L['BDOS']>>8))
 def rsx_overlay(path):return path.read_bytes().ljust(1021,b'\0')+gateway_tail
 put(76,rsx_overlay(ROOT/'build/system/rsxloader.bin'),1024)
 put(84,bytes(1021)+gateway_tail,1024)
 put(92,bytes(1021)+gateway_tail,1024)
 put(100,rsx_overlay(ROOT/'build/system/rsxresolver.bin'),1024)
 put(108,(ROOT/'build/ccp/ccp.rlm').read_bytes(),13*512)
 # CP/M 2.2, 1K allocation blocks, byte block numbers, 64 directory entries.
 from sysgen_image import sysgen_image
 files=[('SYSGEN.DAT',sysgen_image(bytes(resident),L['SYSTEM'],52,8,fmt.spt))]
 for name in ('RCP.CPX','HELLO.CPX'):files.append((name,(ROOT/'build/cpx'/name).read_bytes()))
 for f in sorted((ROOT/'build/utilities').glob('*.COM')):files.append((f.name,f.read_bytes()))
 for name,data in cpm_tools_files(ROOT):files.append((name,data))
 for name in ('HELLO.RSX','ECHO.RSX','BATCHIO.RSX','FDF.RSX','P2DOS.RSX','ZPRTC.RSX','STATEFUL.RSX'):files.append((name,(ROOT/'build/rsx'/name).read_bytes()))
 for name in ('R3PLAN.RSX','R3SLOTS.RSX','R3SNAP.RSX','R3CARR.RSX','R3META.RSX','R3COORD.RSX','R3PROF.RSX','R3KCTX.RSX','R3KEEP.RSX','R3KPRE.RSX','R3FINAL.RSX','R3DROP.RSX','R3MOVE.RSX','R3COMIT.RSX','R3RESOL.RSX'):files.append((name,(ROOT/'build/system'/name).read_bytes()))
 files.append(('DISK.FDF',(ROOT/'third_party/montezuma/DISK.FDF').read_bytes()))
 # A small transient proves that load and warm return use this target BIOS.
 hello=bytes([0x11,0x0b,1,0x0e,9,0xcd,5,0,0xc3,0,0])+b'BetterCP/M on z80pack\r\n$'
 files.append(('HELLO.COM',hello))
 # cpmsim hardware control: unlock, then halt the emulator cleanly.
 files.append(('BYE.COM',bytes((0x3e,0xaa,0xd3,160,0x3e,0x80,0xd3,160,0x76))))
 start=fmt.reserved_records*128;block=fmt.directory_blocks;entry=0
 for name,data in files:
  stem,suffix=name.split('.');payload=data.ljust((len(data)+127)//128*128,b'\x1a')
  for chunkstart in range(0,max(len(payload),1),16384):
   chunk=payload[chunkstart:chunkstart+16384];count=(len(chunk)+fmt.block_bytes-1)//fmt.block_bytes
   if entry>fmt.drm or block+count>fmt.dsm+1:raise ValueError('filesystem full')
   e=bytearray(32);e[1:9]=stem.ljust(8).encode();e[9:12]=suffix.ljust(3).encode()
   extent=chunkstart//16384;e[12]=extent&31;e[14]=extent>>5;e[15]=len(chunk)//128
   if fmt.dsm<256:e[16:16+count]=bytes(range(block,block+count))
   else:
    for slot,value in enumerate(range(block,block+count)):
     struct.pack_into('<H',e,16+slot*2,value)
   logical[start+entry*32:start+(entry+1)*32]=e
   logical[start+block*fmt.block_bytes:start+block*fmt.block_bytes+len(chunk)]=chunk
   entry+=1;block+=count

 def raw_image(flat):
  raw=bytearray(b'\xe5'*fmt.image_bytes)
  for track in range(fmt.raw_tracks):
   logical_base=track*fmt.spt*128
   raw_base=track*fmt.raw_track_bytes
   for record,slot in enumerate(record_map):
    source=logical_base+record*128;destination=raw_base+slot*128
    raw[destination:destination+128]=flat[source:source+128]
  return bytes(raw)

 raw=raw_image(logical)
 blank=raw_image(bytearray(b'\xe5'*fmt.image_bytes))
 disks.mkdir();library=disks/'library';library.mkdir()
 media={
  'a':('BetterCPM-System-CCS-40T-DS-DD-332K.dsk',raw),
  'b':('Blank-B-CCS-40T-DS-DD-332K.dsk',blank),
  'c':('Blank-C-CCS-40T-DS-DD-332K.dsk',blank),
  'd':('Blank-D-CCS-40T-DS-DD-332K.dsk',blank),
 }
 for letter,(name,data) in media.items():
  (library/name).write_bytes(data)
  (disks/f'drive{letter}.dsk').symlink_to(Path('library')/name)
 # cpmtools skewtab entries are zero-based raw-sector ordinals.
 ordered_ids=sorted(fmt.sector_ids)
 logical_to_raw=[ordered_ids.index(sector_id) for sector_id in fmt.sector_ids]
 # cpmtools maps each logical physical sector through this zero-based table.
 skew=','.join(map(str,logical_to_raw))
 diskdefs=f'''diskdef bettercpm-default
 seclen {fmt.sector_bytes}
 tracks {fmt.raw_tracks}
 sectrk {fmt.physical_sectors}
 blocksize {fmt.block_bytes}
 maxdir {fmt.drm+1}
 skewtab {skew}
 boottrk {fmt.off}
 os 2.2
end
diskdef bettercpm-ccs-40ds
 seclen {fmt.sector_bytes}
 tracks {fmt.raw_tracks}
 sectrk {fmt.physical_sectors}
 blocksize {fmt.block_bytes}
 maxdir {fmt.drm+1}
 skewtab {skew}
 boottrk {fmt.off}
 os 2.2
end
'''
 diskdefs+='''diskdef bettercpm-mm-standard-system
 seclen 256
 tracks 40
 sectrk 18
 blocksize 2048
 maxdir 128
 skew 2
 boottrk 2
 os 2.2
end
diskdef bettercpm-mm-80t-ds-data
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 2
 boottrk 0
 os 2.2
end
diskdef bettercpm-ampro-little-board
 seclen 512
 tracks 40
 sectrk 10
 blocksize 2048
 maxdir 64
 skew 0
 boottrk 2
 os 2.2
end
diskdef bettercpm-ampro-little-board-ds
 seclen 512
 tracks 80
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 0
 boottrk 2
 os 2.2
end
'''
 (out/'diskdefs').write_text(diskdefs)
 simulator=args.simulator.expanduser().resolve()
 if not simulator.is_file():raise SystemExit(f'missing cpmsim simulator: {simulator}')
 (out/'launch-z80pack.command').write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nPATH="'+str(simulator.parent/'srctools')+':$PATH"\nexport PATH\nexec "'+str(simulator)+'" -z -d "$PWD/disks" "$@"\n')
 (out/'launch-z80pack.command').chmod(0o755)
 (out/'manifest.json').write_text(json.dumps({'target':'z80pack/cpmsim','format':fmt.name,'cylinders':fmt.cylinders,'sides':fmt.sides,'physical_sectors_per_track':fmt.physical_sectors,'physical_sector_bytes':fmt.sector_bytes,'image_bytes':fmt.image_bytes,'records_per_logical_track':fmt.spt,'reserved_tracks':fmt.off,'reserved_records':fmt.reserved_records,'allocation_kib':(fmt.dsm+1)*fmt.block_bytes//1024,'cpmtools_format':'bettercpm-default','sha256':hashlib.sha256(raw).hexdigest(),'shared_bdos_sha256':hashlib.sha256((ROOT/'build/bdos/bdos.bin').read_bytes()).hexdigest()},indent=2)+'\n')
 print(f'Created linked media in {library}; {fmt.name}; {(fmt.dsm+1)*fmt.block_bytes//1024} KiB allocation area')
if __name__=='__main__':main()
