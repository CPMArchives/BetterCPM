#!/usr/bin/env python3
"""Compare text S/Q extraction with pinned DRI PIP on real cpmsim media."""
import argparse,shutil,subprocess,tempfile,struct
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--formatting',action='store_true');p.add_argument('--numbering',action='store_true');p.add_argument('--echo',action='store_true');p.add_argument('--hex',action='store_true');p.add_argument('--block',action='store_true');p.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack');p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');args=p.parse_args()
 report=ROOT/('build/test-results/pip-block' if args.block else 'build/test-results/pip-hex-transfer' if args.hex else 'build/test-results/pip-echo' if args.echo else 'build/test-results/pip-number' if args.numbering else 'build/test-results/pip-format' if args.formatting else 'build/test-results/pip-extract');report.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='pip-extract-',dir='/private/tmp') as temporary:
  work=Path(temporary);shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs');disk=work/'disks/drivea.dsk'
  def install(path,target):subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),target],cwd=work,check=True)
  source=work/'TEXT.TXT';source.write_bytes(b'x'*126+b'STARTbodyQUITafter\x1a')
  cases=[b'SSTART\x1aQQUIT\x1a',b'QQUIT\x1a',b'USSTART\x1a',b'S\x1a',b'Q\x1a']
  if args.formatting:
   source.write_bytes(b'A\tB\x0cC\r\nLONGTEXT\tZ\nD\r\tEND\x1a')
   cases=[b'T8F',b'T4D3',b'T255']
  if args.numbering:
   source.write_bytes(b'\x0cA\r\nB\r\nC\r\nD\x1a')
   cases=[b'N',b'N2T8',b'NP2F']
  if args.echo:
   source.write_bytes(b'Ab\tCd\r\nEF\x1a')
   cases=[b'EU',b'EN',b'ET8']
  if args.hex:
   from test_pip_hex import record
   source.write_bytes(b'noise\r\n'+record(b'ABC')+b'\n'+record(bytes(range(33)))+b'\r\n:00000001FF\r\n\x1a')
   cases=[b'H',b'I',b'HV']
   source.write_bytes(b'\x13'.join(bytes([v]) for v in source.read_bytes()))
  if args.block:
   source.write_bytes(b'A'*127+b'\x13'+b'B'*132+b'\x13C\x1a')
   cases=[b'B',b'BV',b'BE']
  install(source,'3:TEXT.TXT')
  commands=[(b'A4:\r',b'A4>_ ',30)]
  for i,options in enumerate(cases):
   for prefix,binary in [('OUR',ROOT/'build/pip-development/PIP.COM'),('REF',ROOT/'third_party/dri-pip/PIP-1.5-reference.COM')]:
    data=binary.read_bytes();assert data[0]==0xc3
    command=(prefix+str(i)+'.TXT=TEXT.TXT[G3').encode()+options+b']'
    tail=bytes([len(command)])+command+b'\r'
    # Tiny appended launcher supplies literal 1Ah delimiters in the command
    # tail. The current CCP editor filters typed Ctrl-Z; no keyboard assumption.
    entry=int.from_bytes(data[1:3],'little');stub=256+len(data)
    code=b'\x21'+struct.pack('<H',stub+14)+b'\x11\x80\x00\x01'+struct.pack('<H',len(tail))+b'\xed\xb0\xc3'+struct.pack('<H',entry)
    patched=b'\xc3'+struct.pack('<H',stub)+data[3:]+code+tail
    launcher=work/(prefix+str(i)+'.COM');launcher.write_bytes(patched);install(launcher,'0:'+launcher.name)
    commands.append((b':'+launcher.stem.encode()+b'\r',b'A4>_ ',30))
  session(args.simulator,work/'disks',commands,report/'transcript.txt')
  for i in range(len(cases)):
   def extract(prefix):
    name=prefix+str(i)+'.TXT';out=work/name
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),'4:'+name,str(out)],cwd=work,check=True)
    return out.read_bytes()
   assert extract('OUR')==extract('REF'),i
 print('PASS: cpmsim '+('B block transfer' if args.block else 'H/I HEX transfer' if args.hex else 'E echo' if args.echo else 'N/P numbering' if args.numbering else 'T/F/D formatting' if args.formatting else 'S/Q text extraction')+' matches pinned DRI PIP')
if __name__=='__main__':main()
