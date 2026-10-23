#!/usr/bin/env python3
"""Qualify frozen compression COM files from Utilities B: on BetterCP/M.

Private System A:, unchanged Utilities B:, and disposable output C: are used.
Requires two-platform build_distribution output and build_utilities_disk media.
No production media or caller emulator disks are mounted. No COM is patched.
"""
import argparse
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as system_dmk
from build_utilities_disk import build as utilities
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from codec_version import DESCRIPTIONS, help_text, version_text
from convert_fdf_image import raw_to_dmk, dmk_to_raw
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_codec_historical_cpm import compressed_name, decode_sq
from test_cr_com import checked as check_cr
from test_lzh_com import checked as check_lzh
from test_uncr_com import crunch
from test_unlzh_com import compress
from test_usq import squeeze
from test_usq_com import padded
from test_z80pack_sysgen_install import session
from trs80gp_launch import run as launch

ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
sha = lambda b: hashlib.sha256(b).hexdigest()
FORMATS = {'z80pack':'bettercpm-default','trs80gp':'bettercpm-mm-80t-ds-data'}
SYSTEM_DEF = '''diskdef codec-system
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
'''


def command(work, *args):
    result = subprocess.run(list(map(str,args)),cwd=work,capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{args}: {result.stdout!r} {result.stderr!r}')
    return result.stdout


def put(work, image, definition, user, name, data):
    host=work/'import.bin';host.write_bytes(data)
    command(work,'cpmcp','-T','raw','-f',definition,image,host,f'{user}:{name}')


def get(work, image, definition, user, name):
    host=work/'export.bin';host.unlink(missing_ok=True)
    command(work,'cpmcp','-T','raw','-f',definition,image,f'{user}:{name}',host)
    return host.read_bytes()


def fixtures():
    rng=random.Random(1003)
    return [('EMPTY',b''),('BINARY.BIN',bytes(range(256))*4),
            ('R127.BIN',bytes(range(127))),('R128.BIN',bytes(range(128))),
            ('R129.BIN',bytes(range(129))),
            ('EXTENT.BIN',bytes(rng.randrange(256) for _ in range(17001))),
            ('BIG.BIN',(bytes(range(256))*274)[:70001])]


def prepare(work, platform, family, system, utility, fmt):
    work.mkdir(parents=True)
    definitions=disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT))+SYSTEM_DEF
    (work/'diskdefs').write_text(definitions)
    a=work/'a.raw';b=work/'b.raw';c=work/'c.raw'
    a.write_bytes(system.read_bytes() if platform=='z80pack' else extract_raw(system.read_bytes()))
    b.write_bytes(utility.read_bytes() if platform=='z80pack' else dmk_to_raw(utility.read_bytes(),fmt))
    c.write_bytes(bytes([0xe5])*fmt.image_bytes)
    definition=FORMATS[platform];adef=definition if platform=='z80pack' else 'codec-system'
    command(work,'mkfs.cpm','-f',definition,c)
    originals={}
    for name,data in fixtures():
        put(work,a,adef,0,name,padded(data));originals[(0,name)]=get(work,a,adef,0,name)
    if platform=='trs80gp' and family=='SQ':
        # Avoid hundreds of floppy-drive switches in the large SQ case.
        put(work,c,definition,0,'BIG.BIN',padded(dict(fixtures())['BIG.BIN']))
    put(work,a,adef,7,'USER.TXT',padded(b'user seven binary\x00\x90\x1a'))
    originals[(7,'USER.TXT')]=get(work,a,adef,7,'USER.TXT')
    put(work,c,definition,0,'DEFAULT.TXT',padded(b'logged drive defaults'))
    creator={'SQ':squeeze,'CR':crunch,'LZH':compress}[family]
    good=creator(b'bad checksum controlled payload',name=b'BADOUT.BIN')
    bad=bytearray(good);bad[2 if family=='SQ' else -1]^=1
    put(work,a,adef,0,'BAD.DAT',bytes(bad))
    put(work,a,adef,0,'BROKEN.DAT',b'not compressed')
    originals[(0,'BAD.DAT')]=get(work,a,adef,0,'BAD.DAT')
    originals[(0,'BROKEN.DAT')]=get(work,a,adef,0,'BROKEN.DAT')
    tempnames={'SQ':('SQU00000.$$$','USQ00000.$$$'),
               'CR':('CRU00000.$$$','UCR00000.$$$'),
               'LZH':('LZU00000.$$$','ULZ00000.$$$')}[family]
    for name in tempnames:put(work,c,definition,0,name,padded(b'preexisting temporary sentinel'))
    sentinel={name:get(work,c,definition,0,name) for name in tempnames}
    return a,b,c,adef,definition,originals,sentinel


def steps(family,platform=None):
    decoder={'SQ':'USQ','CR':'UNCR','LZH':'UNLZH'}[family]
    rows=[]
    def add(cmd,expected,prompt='A0>'):
        rows.append({'command':cmd,'expected':expected,'prompt':prompt})
    # All six identities/screens in the first family, each invoked from B:.
    if family=='SQ':
        add('RSX LIST','ADM3A')  # Model 4 only; cpmsim filters this provider check.
        for name in DESCRIPTIONS:
            add(f'B:{name} X /VER',version_text(name))
            add(f'B:{name} /HELP X',help_text(name))
        add('B:LZH /VER /HELP X',help_text('LZH'))
    for name,_ in fixtures():
        encoded=compressed_name(family,name)
        if platform=='trs80gp' and family=='SQ' and name=='BIG.BIN':
            add('B:SQ C:BIG.BIN C:','SQ: complete.')
            add(':REN /Y C:BIG.BIN SAVED.BIN','FILES RENAMED')
        else:
            add(f'B:{family} {name} C:',family+': complete.')
        add(f'B:{decoder} C:{encoded} C:',decoder+': complete.')
    add(f'B:{family} BINARY.BIN C:',family+': output exists; nothing replaced.')
    add(f'B:{decoder} C:{compressed_name(family,"BINARY.BIN")} C:',decoder+': output exists; nothing replaced.')
    add(f'B:{family} C:DEFAULT.TXT',family+': complete.')
    add(f'B:{decoder} {compressed_name(family,"DEFAULT.TXT")}',decoder+': complete.')
    add(f'B:{decoder} BAD.DAT C:',decoder+': checksum mismatch.')
    add(f'B:{decoder} BROKEN.DAT C:',decoder+': invalid or truncated')
    add('USER 7','A7>', 'A7>')
    add(f'B0:{family} USER.TXT C:',family+': complete.', 'A7>')
    add(f'B0:{decoder} C:{compressed_name(family,"USER.TXT")} C:',decoder+': complete.', 'A7>')
    add('USER 0','A0>')
    return rows


def execute_cpmsim(work,a,b,c,rows):
    disks=work/'disks';disks.mkdir()
    for letter,path in zip('abc',(a,b,c)):shutil.copy2(path,disks/f'drive{letter}.dsk')
    # Unused D: still has a valid disposable image.
    shutil.copy2(c,disks/'drived.dsk')
    rows=[row for row in rows if row['command']!='RSX LIST']
    interactions=[]
    for row in rows:
        interactions.append((row['command'].encode()+b'\r',row['expected'].encode(),120))
        if row['expected'] != row['prompt']:
            interactions.append((b'',row['prompt'].encode()+b'_ ',120))
    text=session(SIMULATOR,disks,interactions,work/'transcript.bin')
    for letter,path in zip('abc',(a,b,c)):shutil.copy2(disks/f'drive{letter}.dsk',path)
    return rows,{'transcript_sha256':sha(text)}


def execute_model4(work,a,b,c,rows,fmt):
    ad=work/'a.dmk';bd=work/'b.dmk';cd=work/'c.dmk'
    ad.write_bytes(system_dmk(a.read_bytes()));bd.write_bytes(raw_to_dmk(b.read_bytes(),fmt));cd.write_bytes(raw_to_dmk(c.read_bytes(),fmt))
    invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(ad),'-d1',str(bd),'-d2',str(cd),
                '-itime','120000','-iw','Type TYPE README.TXT for more','-id','6000','-it']
    for row in rows:
        # Clear prior results so a repeated completion message cannot satisfy
        # the next wait before that command has actually finished.
        invocation+=key_args('CLS\r',delay=25)+['-id','1000']
        invocation+=key_args(row['command']+'\r',delay=25)
        # Last line can match VRAM even when the earlier identity has scrolled.
        expected=row['expected'].splitlines()[-1].strip()
        invocation+=['-iw',expected,'-iw',row['prompt']+' ','-id','500','-it']
    invocation+=['-ix']
    (work/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
    launch(invocation,cwd=work,timeout=1800)
    captures=sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    assert len(captures)==len(rows)+1,(len(captures),len(rows))
    evidence=[]
    for number,(row,path) in enumerate(zip(rows,captures[1:])):
        raw=bytes(c&127 for c in path.read_bytes()[:1920])
        text='\n'.join(raw[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))
        (work/f'{number:03d}.screen.txt').write_text(text+'\n')
        expected=row['expected'].splitlines()
        if '\r\n' in row['expected']:
            assert '\n'.join(expected) in text,(row,text)
        else:assert row['expected'] in text,(row,text)
        assert row['prompt'] in text and text.rstrip().endswith((row['prompt'],row['prompt']+'_')),(row,text)
        if row['command']=='RSX LIST':assert 'M4SCRN' in text and 'ADM3A' in text,text
        evidence.append({'command':row['command'],'capture':path.name,'sha256':sha(path.read_bytes())})
    assert bd.read_bytes()==raw_to_dmk(b.read_bytes(),fmt),'private Utilities DMK changed'
    a.write_bytes(extract_raw(ad.read_bytes()));b.write_bytes(dmk_to_raw(bd.read_bytes(),fmt));c.write_bytes(dmk_to_raw(cd.read_bytes(),fmt))
    return rows,{'screens':evidence,'invocation_sha256':sha((work/'invocation.json').read_bytes())}


def verify(work,family,a,b,c,adef,definition,originals,sentinels,commands):
    for (user,name),data in originals.items():assert get(work,a,adef,user,name)==data,(user,name,'source changed')
    for name,data in fixtures():
        encoded=get(work,c,definition,0,compressed_name(family,name))
        assert get(work,c,definition,0,name)==padded(data),(family,name,'round trip')
        if family=='SQ':assert decode_sq(encoded)[1]==padded(data)
        elif family=='CR':check_cr(encoded,name,data)
        else:check_lzh(encoded,name,data)
    for name,data in sentinels.items():assert get(work,c,definition,0,name)==data,name
    default=padded(b'logged drive defaults')
    assert get(work,c,definition,0,'DEFAULT.TXT')==default
    assert get(work,a,adef,0,'DEFAULT.TXT')==default
    assert get(work,c,definition,7,'USER.TXT')==originals[(7,'USER.TXT')]
    encoded7=get(work,c,definition,7,compressed_name(family,'USER.TXT'))
    assert encoded7
    listing=command(work,'cpmls','-f',definition,c).decode().upper()
    assert 'BADOUT.BIN' not in listing and 'BROKEN' not in listing,listing
    assert listing.count('.$$$')==2,listing
    for name in sentinels:assert name in listing,listing
    for image,fmt in [(a,adef),(b,definition),(c,definition)]:command(work,'fsck.cpm','-n','-f',fmt,image)
    return {'round_trips':len(fixtures())+2,'original_files_preserved':True,
            'logged_drive_default':'PASS','current_user_7':'PASS','collision_refusals':'PASS',
            'checksum_and_malformed_refusals':'PASS','owned_temporary_cleanup':'PASS',
            'preexisting_temporaries_preserved':True,'filesystem':'PASS',
            'commands':commands,'data_files':{name:{'records':len(padded(data))//128,'sha256':sha(padded(data))} for name,data in fixtures()}}


def verify_system_payloads(work, private, definition, system, platform):
    manifest=json.loads((system.parent/'report.json').read_text())
    original=system.read_bytes()
    assert sha(original)==manifest['sha256'], 'System image differs from its build receipt'
    raw=original if platform=='z80pack' else extract_raw(original)
    reserved=(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT).reserved_records*128
              if platform=='z80pack' else 4*10*512)
    assert private.read_bytes()[:reserved]==raw[:reserved], 'private System reserved area changed'
    files={}
    for member in manifest['included']:
        content=get(work,private,definition,member['user'],member['name'])
        assert sha(content[:member['bytes']])==member['sha256'],member['name']
        files[member['name']]=sha(content)
    return {'reserved_area_unchanged':True,'payloads_unchanged':True,'files':files}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--only',choices=['z80pack','trs80gp'])
    parser.add_argument('--resume',action='store_true',help='reuse completed cases only after checking commands, images and captures')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=args.resume)
    previous=json.loads((out/'report.json').read_text()) if args.resume else {}
    source_digest=sha(Path(__file__).read_bytes())
    snapshots=out/'source-snapshots';snapshots.mkdir(exist_ok=True)
    (snapshots/(source_digest+'.py')).write_bytes(Path(__file__).read_bytes())
    if args.resume:
        assert previous['commands'], 'missing previous artifact identities'
        prior_snapshot=snapshots/(previous['test_source_sha256']+'.py')
        if not prior_snapshot.exists():
            old_source=out/'test-source-original.py'
            assert sha(old_source.read_bytes())==previous['test_source_sha256']
            shutil.copy2(old_source,prior_snapshot)
        assert sha(prior_snapshot.read_bytes())==previous['test_source_sha256']
    frozen=json.loads((ROOT/'docs/engineering/Compression-1.0-Qualification.json').read_text())['our_commands']
    for c,identity in frozen.items():assert sha((args.artifacts/'build/utilities'/(c+'.COM')).read_bytes())==identity['sha256'],c
    packages=utilities(out/'packaged',args.artifacts)
    result={'compression_utilities_acceptance':'IN_PROGRESS','whole_utilities_disk':'PROVISIONAL',
            'test_source_sha256':source_digest,'commands':frozen,'platforms':{},
            'resumed_from_test_source_sha256':previous.get('test_source_sha256')}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    for filename,image,package in packages:
        platform=package['target']
        if args.only and args.only!=platform:continue
        candidates=[p for p in (args.system/platform).glob('*') if p.suffix in ('.dsk','.dmk') and 'boot-test' not in p.name]
        assert len(candidates)==1,candidates
        system=candidates[0];before_system=system.read_bytes();utility=out/'packaged'/filename
        fmt=select_fdf(ROOT/'third_party/montezuma'/('DISK.FDF' if platform=='z80pack' else 'DISK-INT.FDF'),
                       DEFAULT_FORMAT if platform=='z80pack' else 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
        trials={}
        def run_family(family):
            work=out/platform/family
            rows=steps(family,platform)
            actual_rows=[x for x in rows if platform!='z80pack' or x['command']!='RSX LIST']
            if args.resume and (work/'result.json').exists():
                trial=json.loads((work/'result.json').read_text())
                prior_trial=previous.get('platforms',{}).get(platform,{}).get('families',{}).get(family,{})
                old_system=trial.get('source_system_sha256',prior_trial.get('source_system_sha256'))
                if old_system is not None:
                    assert old_system==sha(system.read_bytes()), 'retained System generation changed'
                assert previous['commands']==frozen
                # Recreate the exact pre-run private images from the selected
                # System/Utilities generation. A different OS, profile, fixture
                # or packaged component must invalidate a retained result.
                probe=out/'resume-validation'/platform/(family+'-'+str(time.time_ns()))
                pa,pb,pc,*_=prepare(probe,platform,family,system,utility,fmt)
                assert {letter:sha(path.read_bytes()) for letter,path in zip('abc',(pa,pb,pc))}==trial['private_input_sha256'], 'retained inputs differ from selected System/Utilities generation'
                assert trial['status']=='PASS' and trial['commands']==actual_rows
                assert sha((work/'a.raw').read_bytes())==trial['output_a_sha256'], 'retained A: image changed'
                assert sha((work/'c.raw').read_bytes())==trial['output_c_sha256'], 'retained C: image changed'
                assert sha((work/'b.raw').read_bytes())==trial['private_input_sha256']['b']
                if platform=='z80pack':
                    assert sha((work/'transcript.bin').read_bytes())==trial['evidence']['transcript_sha256']
                else:
                    for capture in trial['evidence']['screens']:
                        assert sha((work/capture['capture']).read_bytes())==capture['sha256']
                prior_trial=previous.get('platforms',{}).get(platform,{}).get('families',{}).get(family,{})
                trial['test_source_sha256']=trial.get('test_source_sha256',prior_trial.get('test_source_sha256',previous['test_source_sha256']))
                trial['system_payload_readback']=verify_system_payloads(work,work/'a.raw',FORMATS[platform] if platform=='z80pack' else 'codec-system',system,platform)
                trial['source_system_sha256']=sha(system.read_bytes())
                trial['receipt_verifier_sha256']=source_digest
                print(platform,family,'PASS (verified retained case)',flush=True)
                return family,trial
            if work.exists():
                failed=out/'incomplete-pilots';failed.mkdir(exist_ok=True)
                work.rename(failed/(platform+'-'+family+'-'+str(time.time_ns())))
            a,b,c,adef,definition,originals,sentinels=prepare(work,platform,family,system,utility,fmt)
            before_b=b.read_bytes()
            private_input_hashes={letter:sha(path.read_bytes()) for letter,path in zip('abc',(a,b,c))}
            for name,identity in frozen.items():
                actual=get(work,b,definition,0,name+'.COM')
                assert actual[:identity['bytes']]==(args.artifacts/'build/utilities'/(name+'.COM')).read_bytes()
                assert identity['bytes'] <= len(actual) <= (identity['bytes']+127)//128*128
            (work/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
            actual_rows,evidence=(execute_cpmsim(work,a,b,c,rows) if platform=='z80pack' else execute_model4(work,a,b,c,rows,fmt))
            assert b.read_bytes()==before_b,'Utilities filesystem changed'
            assert system.read_bytes()==before_system and utility.read_bytes()==image,'source image changed'
            trial=verify(work,family,a,b,c,adef,definition,originals,sentinels,actual_rows)
            if platform=='trs80gp' and family=='SQ':
                assert get(work,c,definition,0,'SAVED.BIN')==padded(dict(fixtures())['BIG.BIN'])
            trial['system_payload_readback']=verify_system_payloads(work,a,adef,system,platform)
            trial.update({'status':'PASS','source_system_sha256':sha(before_system),'test_source_sha256':source_digest,'utilities_unchanged':True,'evidence':evidence,
                          'private_input_sha256':private_input_hashes,'output_a_sha256':sha(a.read_bytes()),
                          'output_c_sha256':sha(c.read_bytes())})
            (work/'result.json').write_text(json.dumps(trial,indent=2)+'\n')
            print(platform,family,'PASS',flush=True)
            return family,trial
        if platform=='trs80gp':
            # Separate emulator instances and media; no shared mutable disks.
            with ThreadPoolExecutor(max_workers=3) as pool:
                trials.update(pool.map(run_family,('SQ','CR','LZH')))
        else:
            trials.update(map(run_family,('SQ','CR','LZH')))
        result['platforms'][platform]={'status':'PASS','families':trials,'system_image':system.name,
            'system_sha256':sha(before_system),'utilities_image':filename,'utilities_sha256':sha(image),
            'emulator_sha256':sha((SIMULATOR if platform=='z80pack' else DEFAULT_EMULATOR).read_bytes()),
            'source_images_unchanged':True,'utilities_unchanged':True,
            'system_build_report_sha256':sha((args.system/platform/'report.json').read_bytes())}
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    result['compression_utilities_acceptance']='PASS'
    result['qualification_environment_note']='Exact local emulator hashes recorded; clean cpmsim reconstruction and future final-image reacceptance remain separate release gates.'
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: compression Utilities disk component qualification; whole disk remains PROVISIONAL.')


if __name__=='__main__':main()
