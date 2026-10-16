#!/usr/bin/env python3
"""Run pinned directory/BDOS/file groups on private native Model 4 data disks."""
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from run_validation_model4 import sha, audit_files
from test_sysgen_install import screen
from trs80gp_launch import run


def audit_data(work):
    results={}
    for letter in ('bcd' if (work/'d.dmk').is_file() else 'bc'):
        raw=work/f'{letter}-after.raw'
        raw.write_bytes(extract_raw((work/f'{letter}.dmk').read_bytes()))
        checked=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','native-data','-n',str(raw)],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (work/f'{letter}-filesystem.txt').write_text(checked.stdout)
        results[letter]={'sha256':sha(raw),'filesystem_status':checked.returncode}
        if letter=='d':
            assert raw.read_bytes()==(work/'d.raw').read_bytes(), 'directory-full attempt changed D data'
            results[letter]['unchanged_full_fixture']=True
        assert checked.returncode==0, 'data filesystem check failed: '+letter
    (work/'data-audit.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def preflight_data(work, fixtures):
    """Decode raw blocks independently of cpmtools/libdsk before booting.

    These native data disks use 2K blocks, 16-bit allocation entries and EXM=0.
    A host-tool round trip alone can hide a consistently wrong track mapping.
    """
    results={}
    for letter in ('bcd' if (work/'d.raw').is_file() else 'bc'):
        raw=(work/f'{letter}.raw').read_bytes()
        entries=[raw[offset:offset+32] for offset in range(0,4096,32)
                 if raw[offset]<32]
        used={0,1}
        for entry in entries:
            for offset in range(16,32,2):
                block=int.from_bytes(entry[offset:offset+2],'little')
                if not block:continue
                assert 2<=block<400, 'invalid allocation block'
                assert block not in used, 'duplicate allocation block'
                used.add(block)
        files=[]
        for fixture in fixtures:
            if fixture['drive'].lower()!=letter or 'source' not in fixture:continue
            name=fixture['name'].upper().split('.')
            identity=(name[0].ljust(8)+(name[1] if len(name)>1 else '').ljust(3)).encode('ascii')
            matched=[entry for entry in entries if entry[0]==fixture['user'] and
                     bytes(value&127 for value in entry[1:12])==identity]
            assert matched, 'missing fixture '+fixture['name']
            matched.sort(key=lambda entry:entry[14]*32+(entry[12]&31))
            decoded=bytearray()
            for index,entry in enumerate(matched):
                if index<len(matched)-1:assert entry[15]==128, 'hole in dense fixture extents'
                assert entry[14]*32+(entry[12]&31)==index, 'noncontiguous fixture extents'
                assert entry[15]<=128, 'invalid fixture record count'
                for record in range(entry[15]):
                    slot=16+2*(record//16)
                    block=int.from_bytes(entry[slot:slot+2],'little')
                    assert block in used and block>=2, 'missing fixture record block'
                    offset=block*2048+(record%16)*128
                    decoded.extend(raw[offset:offset+128])
            source=Path(fixture['source'])
            assert sha(source)==fixture['sha256'], 'fixture source changed'
            expected=source.read_bytes()
            assert len(decoded)==math.ceil(len(expected)/128)*128, 'fixture length mismatch'
            assert decoded[:len(expected)]==expected, 'misplaced fixture data: '+fixture['name']
            if fixture['name']=='BTRO.DAT':assert matched[0][9]&128, 'RO fixture attribute missing'
            files.append({'user':fixture['user'],'name':fixture['name'],'source_sha256':fixture['sha256'],'bytes':len(expected)})
        for fixture in fixtures:
            if fixture['drive'].lower()==letter and 'free_blocks' in fixture:
                assert 400-len(used)==fixture['free_blocks'], 'incorrect free-space fixture'
        if letter=='d':
            assert len(entries)==128 and used==set(range(400)), 'D must be directory- and allocation-full'
        results[letter]={'raw_sha256':sha(work/f'{letter}.raw'),'live_entries':len(entries),'allocated_blocks_including_directory':len(used),'free_allocation_blocks':400-len(used),'verified_files':files}
    (work/'fixture-preflight.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','suite','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--program',choices=('DIRTEST','BDOSTEST','FILETEST','RANDTEST'),required=True)
    args=parser.parse_args()
    report=json.loads((args.baseline/'report.json').read_text())
    original=args.baseline/report['image']
    assert report['target']=='trs80gp' and sha(original)==report['sha256']
    program=args.suite/f'suite/build/{args.program}.COM'
    hashes={line.split()[1]:line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program)==hashes[program.name]
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix=args.program.lower()+'-',dir=args.output.resolve()))
    shutil.copy2(__file__,work/'executed-runner.py')
    shutil.copy2(Path(__file__).with_name('run_validation_model4.py'),work/'executed-audit.py')
    image=work/'a.dmk';shutil.copy2(original,image)
    # Default Model 4 B/C data profiles have no reserved system-track prefix.
    # Pin LibDsk's geometry too: cpmtools 2.23 can retain a bad auto-probed
    # sidedness even after applying diskdefs, placing later fixtures on the
    # wrong physical tracks. A cpmcp round trip can hide the same mapping bug.
    (work/'diskdefs').write_text('diskdef native-data\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n')
    blank=b'\xe5'*len(extract_raw(original.read_bytes()))
    full_drive=args.program in ('FILETEST','RANDTEST')
    data={letter:work/f'{letter}.raw' for letter in ('bcd' if full_drive else 'bc')}
    for path in data.values():path.write_bytes(blank)
    fixtures=[]
    def install(path,name,user=0,drive='b'):
        subprocess.run(['cpmcp','-T','raw,pcw800','-f','native-data',str(data[drive]),str(path),f'{user}:{name}'],cwd=work,check=True)
        fixtures.append({'drive':drive.upper(),'user':user,'name':name,'bytes':path.stat().st_size,'sha256':sha(path),'source':str(path.resolve())})
    install(program,program.name)
    payload=args.suite/'suite/runtime-payload'
    for path in sorted(payload.iterdir()):
        if path.suffix.upper() in ('.DAT','.CFG'):install(path,path.name)
    install(payload/'BTUSR.DAT','BTUSR.DAT',user=1)
    subprocess.run(['cpmchmod','-T','raw,pcw800','-f','native-data',str(data['b']),'0444','0:BTRO.DAT'],cwd=work,check=True)
    cross=work/'BTBFILE.DAT';cross.write_bytes((b'BFILE-000 '*15)[:128])
    install(cross,cross.name,drive='c')
    if args.program=='BDOSTEST':
        for name in ('BDSA.TMP','BDSB.TMP'):install(payload/'BTEMPTY.DAT',name)
    if args.program=='RANDTEST':
        # Case 0346 writes until allocation exhaustion. Native random writes
        # take seconds apiece: leave one 2K block free, not 128K. The other
        # required writers each create one single-block temporary file, then
        # delete it; extent-crossing reads use the preinstalled BIG fixture.
        # This bounds exhaustion without changing the suite or its oracle.
        used=2+sum(math.ceil(fixture['bytes']/2048) for fixture in fixtures
                   if fixture['drive']=='B' and 'source' in fixture)
        filler=work/'RANDFILL.DAT';filler.write_bytes(bytes((400-1-used)*2048))
        install(filler,filler.name)
        fixtures.append({'drive':'B','free_blocks':1,'purpose':'bounded allocation exhaustion for 0346'})
    if full_drive:
        control=bytearray(128*128);control[-128:-120]=b'FULL-127'
        control_file=work/'BTFULL.DAT';control_file.write_bytes(control)
        release=work/'BTREL.DAT';release.write_bytes(bytes(128))
        # Native data geometry: 400 x 2K blocks, two directory blocks, EXM=0.
        filler=work/'BTFILL.DAT';filler.write_bytes(bytes((400-2-8-1)*2048))
        for file in (control_file,release,filler):install(file,file.name,drive='d')
        entries=sum(max(1,math.ceil(file.stat().st_size/16384)) for file in (control_file,release,filler))
        for slot in range(128-entries):install(payload/'BTEMPTY.DAT',f'F{slot:07d}.DAT',drive='d')
        fixtures.append({'drive':'D','full_directory':128,'allocated_blocks':400,'directory_blocks':2})
    preflight=preflight_data(work,fixtures)
    for letter,path in data.items():(work/f'{letter}.dmk').write_bytes(build(path.read_bytes()))
    selector='/SAFE' if args.program in ('DIRTEST','RANDTEST') else '/GROUP:REQUIRED'
    last='0566  ' if args.program=='DIRTEST' else '0531  '
    passes={'DIRTEST':49,'BDOSTEST':56,'FILETEST':68,'RANDTEST':39}[args.program]
    if full_drive:last='Summary: '
    expected=f'Summary: {passes} pass, 0 fail, 0 error'
    command=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-d1',str(work/'b.dmk'),'-d2',str(work/'c.dmk'),'-itime','15000','-iw','Type TYPE README.TXT for more','-id','6000']
    if full_drive:command += ['-d3',str(work/'d.dmk')]
    command+=key_args('B:\r')+['-id','6000','-it']
    command+=key_args(args.program+' '+selector+'\r')+['-iw',last,'-id','120','-it','-ix']
    initial={letter:sha(work/f'{letter}.dmk') for letter in ('abcd' if full_drive else 'abc')}
    try:
        run(command,cwd=work,timeout=900)
    except Exception as error:
        (work/'run-error.json').write_text(json.dumps({'status':'ERROR','error_type':type(error).__name__,'message':str(error),'initial_disks':initial,'fixtures':fixtures},indent=2)+'\n')
        raise
    ready=screen(work/'trs80-text-0.bin')
    (work/'drive-ready.txt').write_text(ready+'\n')
    assert any(line.startswith('B0>') for line in ready.splitlines()), 'drive-change readiness capture was not the B prompt'
    text=screen(work/'trs80-text-1.bin')
    (work/'screen.txt').write_text(text+'\n')
    result={'baseline_sha256':report['sha256'],'program_sha256':sha(program),'emulator_sha256':sha(DEFAULT_EMULATOR),'fixtures':fixtures,'fixture_preflight':preflight,'read_only_fixture':'B0:BTRO.DAT','command':args.program+' '+selector,'expected_summary':expected,'suite_status':'PASS' if expected in text else 'FAIL','status':'PENDING_AUDIT','initial_disks':initial,'final_disks':{letter:sha(work/f'{letter}.dmk') for letter in ('abcd' if full_drive else 'abc')},'scope':'native final aggregate summary and trailing rows; manual/excluded cards are not passes; no complete scrolling transcript'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert sha(original)==report['sha256']
    try:
        result['data_filesystem_audit']=audit_data(work)
        result['system_file_audit']=audit_files(original,image,report,work)
    except Exception as error:
        result['status']='ERROR'
        result['audit_error']=str(error)
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    result['status']=result['suite_status']
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'evidence':str(work),'expected_summary':expected},indent=2),flush=True)
    assert result['status']=='PASS','native group failed; see retained screens'


if __name__=='__main__':main()
