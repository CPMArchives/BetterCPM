#!/usr/bin/env python3
"""Copy local z80pack sources and add an instruction-boundary stack observer.

The source repository and the ordinary cpmsim binary remain untouched. This
host instrument is not a replacement for independent uninstrumented runs.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();source=a.source.resolve();out=a.output.resolve()
assert not out.exists(),out
inputs={}
for name in ('z80core','iodevices','cpmsim/srcsim','cpmsim/srctools'):
    src=source/name
    shutil.copytree(src,out/name,ignore=shutil.ignore_patterns('*.o','*.d','*.log','*.DS_Store'))
    for f in (out/name).rglob('*'):
        if f.is_file():inputs[str(f.relative_to(out))]=hashlib.sha256(f.read_bytes()).hexdigest()
header=Path(__file__).with_name('cpmsim_stack_trace.h')
shutil.copyfile(header,out/'z80core/cpmsim_stack_trace.h')
cpu=out/'z80core/simz80.c';text=cpu.read_text()
marker='void cpu_z80(void)'
assert text.count(marker)==1
text=text.replace(marker,'#include "cpmsim_stack_trace.h"\n\n'+marker)
marker='\t\tint_protection = false;\n'
assert text.count(marker)==1
text=text.replace(marker,'\t\tbc_before();\n'+marker)
marker='#include "altz80.h"\n#endif'
assert text.count(marker)==1
text=text.replace(marker,marker+'\n\t\tbc_after();')
cpu.write_text(text)
with (out/'build.log').open('wb') as log:
    # Avoid GNU make resolving ../cpmsim through VPATH to the cpmsim directory.
    subprocess.run(['make','-j4','all','SIM='+str(out/'cpmsim/cpmsim')],cwd=out/'cpmsim/srcsim',stdout=log,stderr=subprocess.STDOUT,check=True)
binary=out/'cpmsim/cpmsim'
subprocess.run(['codesign','--force','--sign','-',str(binary)],check=True,capture_output=True)
result={'source':str(source),'input_sha256':inputs,'observer_sha256':hashlib.sha256(header.read_bytes()).hexdigest(),'instrumented_cpu_sha256':hashlib.sha256(cpu.read_bytes()).hexdigest(),'binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'scope':'Host instruction-boundary PC/SP observer; no guest patch and no instruction-semantics change. No interrupts injected.'}
(out/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'binary':str(binary),'sha256':result['binary_sha256'],'source_files':len(inputs)},indent=2))
