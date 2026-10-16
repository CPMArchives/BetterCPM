#!/usr/bin/env python3
"""Read-only audit: demonstrate BDOS-only list-filter coverage and measure MM leaves.

No extension is installed and no production source/image is modified. Optional MM
input is Jeff Post's reconstructed archive, not original vendor source.
"""
import argparse,json,re,zipfile
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address
from system_layout import LAYOUT
from build_rsx_module import make_module
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--mm-archive',type=Path);a=p.parse_args()
 out=ROOT/'build/audit/peripheral-rsx';out.mkdir(parents=True,exist_ok=True)
 listing=(ROOT/'build/bdos/bdos.lst').read_text();addr=lambda n:address(listing,n)
 source=f''' ORG 8000H
 DW {LAYOUT['BDOS']}
 DW FILTER
 DB 0,0
 DW 0
FILTER: LD A,C
 CP 5
 JR NZ,CHAIN
 LD HL,HITS
 INC (HL)
CHAIN: JP {LAYOUT['BDOS']}
HITS: DB 0
 END
'''
 wrapper=assemble(Path.home()/'bin/z80asm',source,out/'list-filter.bin',out/'list-filter.lst',0x8000)
 hits=address((out/'list-filter.lst').read_text(),'HITS')
 results=[]
 for name,service,echo,direct in [('bdos5',5,False,False),('bdos2-echo',2,True,False),('bdos9-echo',9,True,False),('direct-bios-list',None,False,True)]:
  c=Z80(b'');image=(ROOT/'build/bdos/bdos.bin').read_bytes()
  c.mem[LAYOUT['BDOS']:LAYOUT['BDOS']+len(image)]=image;c.mem[0x8000:0x8000+len(wrapper)]=wrapper
  c.mem[LAYOUT['BIOS']+6:LAYOUT['BIOS']+8]=bytes((0xaf,0xc9))
  c.mem[LAYOUT['BIOS']+12:LAYOUT['BIOS']+15]=bytes((0xdb,240,0xc9))
  c.mem[LAYOUT['BIOS']+15:LAYOUT['BIOS']+18]=bytes((0xdb,241,0xc9))
  c.mem[addr('UB_LISTE')]=int(echo);c.mem[0x9000:0x9002]=b'A$'
  c.c=ord('A') if direct else service;c.de=0x9000 if service==9 else ord('A')
  emitted=[]
  def io(port):
   if port&255==241:emitted.append(c.c)
   return 0
  c.port_read=io;c.run(LAYOUT['BIOS']+15 if direct else 0x8008,limit=500000)
  assert emitted==[ord('A')],(name,emitted)
  assert c.mem[hits]==int(name=='bdos5'),(name,c.mem[hits])
  results.append({'path':name,'list_bytes':len(emitted),'filter_hits':c.mem[hits]})
 carrier=make_module(name='AUDIT',version=(0,1),services=[5],linked_base=0x8000,code=wrapper,relocations=[])
 report={'coverage':results,'dispatch_probe_bytes':len(wrapper),'dispatch_probe_allocation':int.from_bytes(carrier[14:16],'little'),
         'note':'probe only: no transformations, configuration, relocation qualification or production extension'}
 if a.mm_archive:
  with zipfile.ZipFile(a.mm_archive) as z:data=z.read('mmcpm232/bios.asm').decode().replace('\r','')
  regions=[('mm-printer','prtstat:','constsio:',"prtport EQU 0F8H\nprtstatmask EQU 0F0H\nlf EQU 10\ncr EQU 13\nformfeed EQU 12\n"),
           ('mm-serial','constsio:','; Disk routines',"modemstatus EQU 0E8H\nbrgen EQU 0E9H\nrstenable EQU 0E8H\nsioc EQU 0EAH\nsiod EQU 0EBH\n")]
  report['reconstructed_mm']={}
  for name,start,end,defs in regions:
   body=data[data.index(start):data.index(end,data.index(start))]
   text=' ORG 8000H\n'+defs+body+'\n END\n'
   labels=re.findall(r'^([A-Za-z_][A-Za-z0-9_]*)(?::|[ \t]+EQU\b)',text,re.M|re.I)
   for i,label in enumerate(sorted(set(labels))):
    if len(label)>8:text=re.sub(r'\b'+re.escape(label)+r'\b',f'Z{i:03}',text,flags=re.I)
   blob=assemble(Path.home()/'bin/z80asm',text,out/(name+'.bin'),out/(name+'.lst'),0x8000)
   report['reconstructed_mm'][name]={'bytes':len(blob),'scope':'selected leaf routines plus local state, not full BIOS or CONFIG'}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
