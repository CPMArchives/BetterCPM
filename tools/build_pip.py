#!/usr/bin/env python3
"""Build production PIP and the matching compatibility-test artifact."""
import argparse,hashlib
from pathlib import Path
from build_ccp import assemble
from utility_versions import expand_versions
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/pip-development'
def expanded_source():
 text=(ROOT/'src/utilities/pip.mac').read_text()
 from utility_help import query_source, source
 scan=text[text.index('P_VCHECK:'):text.index('P_PROMPT:')]
 helpers=''
 for prefix,word,length in [('QH','/help',5),('QS','/h',2)]:
  part=scan.replace('P_VCHECK:',prefix+'_CHECK:').replace('PV_',prefix+'_')
  part=part.replace('UV_WORD',prefix+'_WORD').replace('LD C,4','LD C,'+str(length))
  part=part.replace('LD DE,UV_TEXT','LD DE,PH_TEXT').replace('JP UV_QUERY','JP UH_QUERY')
  helpers+=part+prefix+"_WORD: DB '"+word+"'\n"
 helpers+=query_source(ROOT)+source('PIP','PH_TEXT')
 text=text.replace('        CALL P_VCHECK','        CALL QH_CHECK\n        JP C,00000H\n        CALL QS_CHECK\n        JP C,00000H\n        CALL P_VCHECK',1)
 text=text.replace('; @utility-version PIP@',helpers+'\n; @utility-version PIP@')

 text=text.replace('; @pip-parser@','\n'.join((ROOT/'src/utilities/common'/n).read_text() for n in ['pipparse.inc','pipoperand.inc','pipselect.inc','duselect.inc','piptransfer.inc','pipconcat.inc','pipwild.inc','pipdevice.inc','pipphysical.inc','pipextract.inc','pipformat.inc','piphex.inc','piphex-transfer.inc','pipbreak.inc']))
 from shared_ui import expand_pip_ui
 return expand_versions(expand_pip_ui(text))
def main():
 p=argparse.ArgumentParser();p.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'));args=p.parse_args()
 BUILD.mkdir(parents=True,exist_ok=True)
 text=expanded_source().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
 data=assemble(args.assembler,text,BUILD/'PIP.COM',BUILD/'pip.lst',0x100)
 assert data[3:10]==bytes((0xC9,0,0,0xC9,0,0,0x1A))
 (ROOT/'build/utilities').mkdir(parents=True,exist_ok=True)
 (ROOT/'build/utilities/PIP.COM').write_bytes(data)
 print(f'{hashlib.sha256(data).hexdigest()}  PIP: {len(data)} bytes')
if __name__=='__main__':main()
