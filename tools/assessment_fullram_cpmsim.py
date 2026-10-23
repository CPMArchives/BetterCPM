"""Experimental RAM-only cpmsim build; see the Part 5 prototype note."""
from pathlib import Path
import subprocess,sys,json,hashlib
base=Path(__file__).resolve().parents[1]
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else base
sys.path.insert(0,str(root/'tools'))
from build_complete_system import COMPONENTS
from build_trs80_boot import assemble,SOURCE,BUILD,BOOT_ADDRESS,STAGE1_ADDRESS
logs=root/'assessment-build-logs';logs.mkdir(exist_ok=True)
a=Path.home()/'bin/z80asm'
assemble(a,SOURCE/'boot.mac',BUILD/'boot.bin',BOOT_ADDRESS)
assemble(a,SOURCE/'stage1.mac',BUILD/'stage1.bin',STAGE1_ADDRESS)
for name in ('rsxselect',)+COMPONENTS+('z80pack_bye',):
    with (logs/(name+'.log')).open('wb') as f:
        p=subprocess.run([sys.executable,str(root/'tools'/f'build_{name}.py')],cwd=root,stdout=f,stderr=subprocess.STDOUT)
    if p.returncode:raise SystemExit(f'{name} failed: '+(logs/(name+'.log')).read_text()[-4000:])
    print('built',name,flush=True)
with (logs/'cpmsim.log').open('wb') as f:
    p=subprocess.run([sys.executable,str(root/'tools/build_z80pack_image.py'),'--system-tracks-only','--ram-only'],cwd=root,stdout=f,stderr=subprocess.STDOUT)
if p.returncode:raise SystemExit((logs/'cpmsim.log').read_text()[-5000:])
from build_distribution import geometry,selected_files,construct,capacity,validate_config_fingerprint,validate_config_cold_patch,validate_files
manifest=json.loads((root/'metadata/distribution.json').read_text())
files,omitted=selected_files(manifest,'z80pack',root)
g=geometry('z80pack',root)
out=root/'assessment-media';out.mkdir(exist_ok=True)
raw=construct('z80pack',root,out,files,g,manifest['cold_start_command'])
validate_config_fingerprint('z80pack',raw,files,root)
validate_config_cold_patch('z80pack',raw,files,root)
validate_files(raw,out,files,g)
(out/'manifest.json').write_text(json.dumps({'capacity':capacity(files,g),'source':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ('src','tools','metadata') for p in sorted((root/d).rglob('*')) if p.is_file() and '__pycache__' not in p.parts},'artifacts':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'build').rglob('*')) if p.is_file()}},indent=2)+'\n')
print('PASS: manifest media, filesystem, files and CONFIG metadata',flush=True)
