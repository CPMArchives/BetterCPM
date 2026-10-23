#!/usr/bin/env python3
"""Qualify real historical and BetterCP/M codec commands on stock CP/M 2.2.

Only disposable IBM-3740 media are used. Historical artifacts are unmodified,
SHA-256 pinned external fixtures; --fetch obtains the eight executables and
SQ archives into an ignored cache. CRUNCH and CrLZH archived corpora are
supplied separately (see --help). No historical code/binaries are vendored.
Reports include exact command/image/input/output hashes and console transcripts.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import tempfile
import urllib.request

from utility_versions import identities
from test_usq_com import padded
from test_usq_com_cpm import run
from test_uncr import decode as decode_cr
from test_unlzh import decode as decode_lzh, ARCHIVE_HASHES

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/squsq/'
# Observed original downloads, cross-checked with archive member listings and
# published compatibility-suite hashes for CRUNCH/UNCR 2.4. Never patched.
ARTIFACTS = {
    'SQ17.COM': ('sq-17.com', 16128, 'e30364aae9a5557d1d11b1320f0a42066b45d16f36bbfe0ad5a0fc558c4dda8b'),
    'USQ20.COM': ('usq-20.com', 12800, '0a43d21823206c247b9eaefa4d8fc730e8b377128aa3f2da74b0be8c3e87791d'),
    'USQ120.COM': ('usq120.com', 1920, 'dd9f96a426ae47d3fe7d3184e95dad6b910ba4c41dedd6e1b1b55235340114cf'),
    'CRUNCH.COM': ('crunch24/crunch.com', 5888, 'f29121a2b38b7f49d1b1c00efc8e35cae8793d1acdf9be9e63c64e5f1e48f0b0'),
    'UNCR.COM': ('crunch24/uncr.com', 6400, 'c834ad4a89b45200e8220ce84a5837dcc876ce4a6326267b342d8c0055fd810c'),
    'CRLZH11.COM': ('crlzh11/crlzh11.com', 7680, '153c73f20ed995fe08c0086423dd028848d8b64507bbcf87d156528853b1d70e'),
    'CRLZH20.COM': ('crlzh20/crlzh20.com', 7808, '365efa8f400c4809d69f5e81d35f7f8a57f81543fd6c48654775a7691d93287d'),
    'UCRLZH20.COM': ('crlzh20/ucrlzh20.com', 8704, '9ac052b2c5f4ecbab0fe9516f741afa88353ccd1d58ffebbf6ba2b72519b16d2'),
    'sq111.lbr': ('sq111.lbr', 12160, 'e3e0be5f5f2f334a89e5cf9848bb6d6884550edd295eb723f4cdef3c0727f090'),
    'usqfst20.lbr': ('usqfst20.lbr', 27520, 'c321f884e9cf1a15c5927f0751f4993eaad37af957ee1429c53f7a9c0748e1b5'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def lbr(raw):
    directory = struct.unpack_from('<H', raw, 14)[0] * 128
    assert 32 <= directory <= len(raw)
    for offset in range(32, directory, 32):
        entry = raw[offset:offset+32]
        if entry[0] != 0:
            continue
        sector, records = struct.unpack_from('<HH', entry, 12)
        assert (sector+records)*128 <= len(raw)
        name = entry[1:9].decode().rstrip()+'.'+entry[9:12].decode().rstrip()
        yield name, raw[sector*128:(sector+records)*128]


def decode_sq(raw):
    """Independent host tree/RLE model; historical disk padding is opaque."""
    assert raw[:2] == b'\x76\xff'
    expected = struct.unpack_from('<H', raw, 2)[0]
    end = raw.index(0, 4)
    name = raw[4:end]
    count = struct.unpack_from('<H', raw, end+1)[0]
    assert count <= 256
    nodes = [struct.unpack_from('<hh', raw, end+3+i*4) for i in range(count)]
    start, bit = end+3+count*4, 0
    def symbol():
        nonlocal bit
        if not nodes:
            return 256
        node = 0
        for _ in range(257):
            edge = raw[start+bit//8] >> (bit%8) & 1
            bit += 1
            node = nodes[node][edge]
            if node < 0:
                value = -node-1
                assert value <= 256
                return value
        raise AssertionError('cyclic historical SQ tree')
    out = bytearray()
    while True:
        value = symbol()
        if value == 256:
            break
        if value == 144:
            n = symbol()
            if n == 0:
                out.append(144)
            else:
                assert 2 <= n <= 255 and out
                out.extend([out[-1]]*(n-1))
        else:
            out.append(value)
    assert sum(out)&65535 == expected
    return name, bytes(out), start+(bit+7)//8


def parse(family, raw):
    if family == 'SQ':
        return decode_sq(raw)
    name = raw[2:raw.index(0, 2)]
    data, used, _ = (decode_cr if family == 'CR' else decode_lzh)(raw)
    return name, data, used


def output_name(family, name):
    if family != 'SQ':
        stem, dot, ext = name.partition(b'.')
        ext = ext[:3].rstrip(b' ')
        name = stem+(b'.'+ext if dot and ext else b'')
    try:
        text = name.decode('ascii').upper()
    except UnicodeDecodeError:
        return None
    legal = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()-@^_{}~")
    parts = text.split('.')
    if len(parts)>2 or not 1 <= len(parts[0]) <= 8:
        return None
    if len(parts)==2 and len(parts[1])>3:
        return None
    if any(c not in legal for part in parts for c in part):
        return None
    return text.rstrip('.')


def compressed_name(family, name):
    stem, _, ext = name.partition('.')
    letter = {'SQ':'Q','CR':'Z','LZH':'Y'}[family]
    ext = ext.ljust(3)
    if ext == '   ':
        ext = letter*3
    elif family == 'CR' and ext[1] == letter:
        ext = letter*3
    elif family == 'LZH' and ext[1] == letter:
        ext = ext[:2]+letter if ext[2] != letter else letter*3
    else:
        ext = ext[0]+letter+ext[2]
    return stem+'.'+ext.rstrip()


class Campaign:
    def __init__(self, args, commands):
        self.args, self.commands = args, commands
        self.sim = args.z80pack/'cpmsim/cpmsim'
        self.template = self.sim.parent/'disks/library/cpm22-62khd.dsk'
        self.rows = []
        self.args.output.mkdir(parents=True, exist_ok=True)

    def execute(self, label, programs, files, commands, verify, historical_fault=False):
        if self.args.match and self.args.match not in label:
            return
        row = {'case':label, 'commands':commands, 'status':'FAIL',
               'program_sha256':{n:sha(b) for n,b in programs.items()},
               'input_sha256':{n:sha(b) for n,b in files.items()}}
        with tempfile.TemporaryDirectory(prefix='bettercpm-historical-cpm-') as temporary:
            work = Path(temporary)
            disks = work/'disks'; disks.mkdir()
            for letter in 'abc':
                shutil.copy2(self.template, disks/f'drive{letter}.dsk')
                if letter != 'a':
                    run('mkfs.cpm','-f','ibm-3740',disks/f'drive{letter}.dsk')
            def put(name, data):
                host = work/'import.bin'; host.write_bytes(data)
                run('cpmcp','-f','ibm-3740',disks/'drivea.dsk',host,'0:'+name)
            def get(letter, name):
                host = work/'export.bin';host.unlink(missing_ok=True)
                run('cpmcp','-f','ibm-3740',disks/f'drive{letter}.dsk','0:'+name,host)
                return host.read_bytes()
            get.disks = disks
            get.listing = lambda letter: run('cpmls','-f','ibm-3740',disks/f'drive{letter}.dsk').stdout.upper()
            try:
                for name, data in {**programs, **files}.items():
                    put(name,data)
                originals = {n:get('a',n) for n in {**programs,**files}}
                # Save-anyway is the historical encoder's own prompt on the
                # same DU. No historical configuration or binary is patched.
                script = '''set timeout 30
proc await {} {
 expect {
  -exact "A>" {return}
  -re {Save anyway[^:?]*[:?]} {send -- "Y"; exp_continue}
  timeout {puts "TIMEOUT waiting for CP/M prompt"; exit 1}
  eof {puts "unexpected emulator EOF"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
await
'''
                for command in commands:
                    assert re.fullmatch(r'[A-Z0-9 .:/_-]+',command), command
                    script += f'send -- "{command}\\r"\nawait\n'
                script += 'send -- "\\034"\nexpect eof\n'
                (work/'test.exp').write_text(script)
                env = dict(os.environ)
                env['PATH'] = str(self.sim.parent/'srctools')+os.pathsep+env['PATH']
                result = subprocess.run(['expect',str(work/'test.exp'),str(self.sim),str(disks)],
                                        cwd=work,env=env,capture_output=True,text=True,timeout=180)
                console = result.stdout+result.stderr
                transcript = self.args.output/(label+'.console.txt')
                transcript.write_text(console)
                row['console'] = transcript.name
                row['console_sha256'] = sha(console.encode())
                assert result.returncode == 0, console[-2000:]
                if not historical_fault:
                    assert not re.search(r'checksum error|checksum mismatch|CPU error|sentinel',console,re.I),console[-2000:]
                row.update(verify(get,console))
                for name, data in originals.items():
                    assert get('a',name) == data, (label,name,'original changed')
                row['status'] = 'PASS'
                row['result'] = ('EXPECTED_REFUSAL' if 'expected_refusal' in row else
                                 'HISTORICAL_SKIP' if 'historical_limitation' in row else
                                 'HISTORICAL_ENCODER_DEFECT' if 'historical_encoder_defect' in row else
                                 'DECODED')
            except Exception as error:
                row['error'] = str(error)
                shutil.copytree(disks,self.args.output/(label+'.failed-disks'),dirs_exist_ok=True)
            self.rows.append(row)
            print(label+': '+row['status']+((': '+row['error'][:200]) if 'error' in row else ''),flush=True)


def fixtures():
    rng = random.Random(458)
    result = [('EMPTY',b''),('ONE.A',b'A'),('TWO.AB',b'\0\x90\xff'),
              ('NOEXT',b'no extension'),('R127.BIN',bytes(range(127))),
              ('R128.BIN',bytes(range(128))),('R129.BIN',bytes(range(129))),
              ('BINARY.BIN',bytes(range(256))*4),
              ('RUNS.DAT',b'R'+b'\x90'*2048+b'A'*18000),
              ('LEADDLE.BIN',b'\x90'*2048+b'A'*18000),
              ('TEXT.TXT',b'CP/M historical interoperability\r\n'*1000),
              ('EXTENT.BIN',bytes(rng.randrange(256) for _ in range(17001))),
              ('BIG.BIN',bytes(rng.randrange(256) for _ in range(70001)))]
    ring = bytes(rng.randrange(256) for _ in range(2048))
    result += [('RING.BIN',ring+ring+ring[:60])]
    return [(n,padded(b)) for n,b in result]


def matrix(campaign, historical):
    groups = [('SQ','SQ17.COM','USQ'),('CR','CRUNCH.COM','UNCR'),
              ('LZH','CRLZH11.COM','UNLZH'),('LZH','CRLZH20.COM','UNLZH')]
    for family, encoder, decoder in groups:
        if campaign.args.only and family != campaign.args.only:
            continue
        for name, data in fixtures():
            label = f'{encoder[:-4]}-to-{decoder}-{name.replace(".","-")}'
            compressed = compressed_name(family,name)
            command = f'HENC B: {name}' if family=='SQ' else f'HENC {name} /Q'
            drive = 'B' if family=='SQ' else 'A'
            control = 'USQ120.COM' if family=='SQ' else ('UNCR.COM' if family=='CR' else 'UCRLZH20.COM')
            control_command = f'CTRL B: {drive}:{compressed}' if family=='SQ' else f'CTRL {drive}:{compressed} B: /Q'
            programs = {'HENC.COM':historical[encoder], 'DEC.COM':campaign.commands[decoder],
                        'CTRL.COM':historical[control]}
            if not data and family != 'SQ':
                def verify(get,console,compressed=compressed):
                    assert re.search(r'file (?:is )?empty',console,re.I),console
                    assert compressed not in get.listing('a')
                    assert not get.listing('b').strip() and not get.listing('c').strip()
                    return {'historical_limitation':'encoder skips empty input; no compressed file to exchange'}
                campaign.execute(label,programs,{name:data},[command],verify)
                continue
            if family=='CR' and name=='LEADDLE.BIN':
                def verify(get,console,compressed=compressed,name=name,data=data):
                    raw=get('a',compressed)
                    try:
                        parse('CR',raw)
                    except ValueError as error:
                        assert str(error)=='invalid repeat'
                    else:
                        raise AssertionError('historical leading-DLE defect unexpectedly absent')
                    assert 'Checksum error detected.' in console,console
                    assert get('b',name) != data, 'historical control unexpectedly restored the original'
                    assert 'UNCR: invalid or truncated crunched file.' in console
                    assert not get.listing('c').strip()
                    return {'historical_encoder_defect':'CRUNCH 2.4 begins repeat stream with unescaped DLE; historical UNCR also fails checksum',
                            'encoded_sha256':sha(raw),'our_result':'malformed repeat rejected; no output published'}
                campaign.execute(label,programs,{name:data},
                                 [command,control_command,f'DEC {drive}:{compressed} C:'],verify,historical_fault=True)
                continue
            def verify(get,console,family=family,data=data,compressed=compressed,drive=drive,name=name,encoder=encoder):
                raw = get(drive,compressed)
                embedded, expected, used = parse(family,raw)
                assert expected == data, 'historical encoder changed physical-record input'
                assert output_name(family,embedded) == name
                control = get('b',name)
                assert control==padded(expected),'historical encoder/decoder control did not round trip'
                result = get('c',name)
                assert result == padded(expected), 'our decoder changed historical output'
                if family=='LZH':
                    significant = raw[raw.index(0,2)+2]
                    assert significant == (0x10 if encoder=='CRLZH11.COM' else 0x20)
                return {'encoded_sha256':sha(raw),'decoded_sha256':sha(result),'decoded_bytes':len(result),
                        'historical_control_sha256':sha(control)}
            campaign.execute(label,programs,{name:data},[command,control_command,f'DEC {drive}:{compressed} C:'],verify)
    for family, decoder in [('SQ','USQ20.COM'),('SQ','USQ120.COM'),
                            ('CR','UNCR.COM'),('LZH','UCRLZH20.COM')]:
        if campaign.args.only and family != campaign.args.only:
            continue
        for name, data in fixtures():
            label = f'{family}-to-{decoder[:-4]}-{name.replace(".","-")}'
            compressed = compressed_name(family,name)
            command = f'HDEC C: B:{compressed}' if family=='SQ' else f'HDEC B:{compressed} C: /Q'
            def verify(get,console,family=family,data=data,name=name,compressed=compressed):
                raw = get('b',compressed)
                embedded, expected, used = parse(family,raw)
                assert expected == data and output_name(family,embedded)==name
                result = get('c',name)
                assert result == padded(data),'historical decoder changed our output'
                assert raw[used:] == b'\x1a'*(-used%128),'our record padding changed'
                return {'encoded_sha256':sha(raw),'decoded_sha256':sha(result),'decoded_bytes':len(result)}
            campaign.execute(label,{'ENC.COM':campaign.commands[family],'HDEC.COM':historical[decoder]},
                             {name:data},[f'ENC {name} B:',command],verify)


def archived(campaign, historical):
    if not campaign.args.only or campaign.args.only=='SQ':
        for archive in ('sq111.lbr','usqfst20.lbr'):
            for member, raw in lbr(historical[archive]):
                if raw[:2] != b'\x76\xff':
                    continue
                embedded, data, used = parse('SQ',raw)
                name = output_name('SQ',embedded)
                assert name is not None
                for decoder in ('USQ','USQ20.COM','USQ120.COM'):
                    command = 'DEC INPUT.SQ B:' if decoder=='USQ' else 'DEC B: INPUT.SQ'
                    program = campaign.commands['USQ'] if decoder=='USQ' else historical[decoder]
                    def verify(get,console,name=name,data=data,raw=raw):
                        result = get('b',name)
                        assert result==padded(data)
                        return {'historical_sha256':sha(raw),'decoded_sha256':sha(result),'decoded_bytes':len(result)}
                    campaign.execute(f'archive-{archive}-{member}-{decoder}',{'DEC.COM':program},
                                     {'INPUT.SQ':raw},[command],verify)
    if not campaign.args.only or campaign.args.only=='CR':
        manifest = campaign.args.corpus/'MANIFEST.tsv'
        with manifest.open() as stream:
            rows = list(csv.DictReader(stream,delimiter='\t'))
        for entry in rows:
            raw=(campaign.args.corpus/(entry['utility']+'.MZC')).read_bytes()
            assert sha(raw)==entry['mzc_sha256']
            embedded,data,_=parse('CR',raw)
            size=int(entry['mac_size'])
            assert sha(data[:size])==entry['mac_sha256']
            name=output_name('CR',embedded)
            def verify(get,console,name=name,data=data,raw=raw):
                result=get('b',name)
                assert result==padded(data)
                return {'historical_sha256':sha(raw),'decoded_sha256':sha(result),'decoded_bytes':len(result)}
            campaign.execute('archive-CR24-'+entry['utility'],{'DEC.COM':campaign.commands['UNCR']},
                             {'INPUT.MZC':raw},['DEC INPUT.MZC B:'],verify)
    if not campaign.args.only or campaign.args.only=='LZH':
        for archive in campaign.args.archives:
            raw_archive=archive.read_bytes()
            sig,count=ARCHIVE_HASHES[sha(raw_archive)]
            members=[(n,r) for n,r in lbr(raw_archive) if r[:2]==b'\x76\xfd']
            assert len(members)==count
            for member,raw in members:
                embedded,data,_=parse('LZH',raw)
                name=output_name('LZH',embedded)
                def verify(get,console,name=name,data=data,raw=raw):
                    if name is None:
                        assert 'unsafe embedded filename' in console
                        listing=run('cpmls','-f','ibm-3740',get.disks/'driveb.dsk').stdout
                        assert not listing.strip()
                        return {'historical_sha256':sha(raw),'expected_refusal':'unsafe embedded filename'}
                    result=get('b',name)
                    assert result==padded(data)
                    return {'historical_sha256':sha(raw),'decoded_sha256':sha(result),'decoded_bytes':len(result)}
                campaign.execute(f'archive-LZH{sig:02x}-{member}',{'DEC.COM':campaign.commands['UNLZH']},
                                 {'INPUT.LZH':raw},['DEC INPUT.LZH B:'],verify)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    parser.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    parser.add_argument('--fixtures',type=Path,default=ROOT/'build/test-fixtures/historical-interop')
    parser.add_argument('--archives',type=Path,nargs=2,default=[ROOT/'build/test-fixtures/crlzh'/n for n in ('crlzh11.lbr','crlzh20.lbr')])
    parser.add_argument('--corpus',type=Path,default=ROOT.parent/'cpm-2.2-compatibility-suite/suite/crunched-source')
    parser.add_argument('--output',type=Path,default=ROOT/'build/historical-interop')
    parser.add_argument('--commands-dir',type=Path,
                        help='test final COM files here; require byte identity with fresh source builds')
    parser.add_argument('--fetch',action='store_true',help='fetch missing hash-pinned executables/SQ archives into ignored fixture cache')
    parser.add_argument('--only',choices=['SQ','CR','LZH'])
    parser.add_argument('--match',help='run only cases containing this string')
    parser.add_argument('--skip-archived',action='store_true',help='run generated cross-executable matrix only')
    args=parser.parse_args()
    args.fixtures.mkdir(parents=True,exist_ok=True)
    historical={}
    for name,(url,size,digest) in ARTIFACTS.items():
        path=args.fixtures/name
        if not path.exists() and args.fetch:
            raw=urllib.request.urlopen(BASE+url,timeout=30).read()
            assert len(raw)==size and sha(raw)==digest,name
            path.write_bytes(raw)
        if not path.exists():
            parser.error(f'missing {path}; use --fetch or provide the original file')
        raw=path.read_bytes()
        assert len(raw)==size and sha(raw)==digest,name
        historical[name]=raw
    with tempfile.TemporaryDirectory(prefix='bettercpm-historical-build-') as temporary:
        work=Path(temporary)
        commands={c:importlib.import_module('build_'+c.lower()).build(args.assembler,work)
                  for c in ('SQ','USQ','CR','UNCR','LZH','UNLZH')}
        if args.commands_dir:
            for command, built in commands.items():
                final = (args.commands_dir/(command+'.COM')).read_bytes()
                assert final == built, f'{command}: final artifact differs from fresh build'
                commands[command] = final
        source_paths = set((ROOT/'src/codec').glob('*.inc'))
        source_paths.update((ROOT/'src/codec').glob('*.mac'))
        source_paths.update((ROOT/'src/utilities/common').glob('codec*'))
        for command in commands:
            source_paths.add(ROOT/'src/utilities'/(command.lower()+'.mac'))
            source_paths.add(ROOT/'tools'/('build_'+command.lower()+'.py'))
        source_paths.update(ROOT/name for name in (
            'tools/codec_version.py', 'tools/utility_versions.py',
            'src/utilities/common/version.inc', 'metadata/utility-versions.tsv'))
        campaign=Campaign(args,commands)
        matrix(campaign,historical)
        if not args.skip_archived:
            archived(campaign,historical)
        assert campaign.rows, 'no cases selected'
        result_counts = {k:sum(r.get('result')==k for r in campaign.rows) for k in
                         ('DECODED','EXPECTED_REFUSAL','HISTORICAL_SKIP','HISTORICAL_ENCODER_DEFECT')}
        report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),
                'test_source_sha256':sha(Path(__file__).read_bytes()),
                'result_counts':result_counts,
                'source_revision':subprocess.check_output(
                    ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'utility_identities':{c:{'version':identities()[c][0],
                                         'build':identities()[c][1]} for c in commands},
                'final_artifacts_verified':bool(args.commands_dir),
                'assembler_sha256':sha(args.assembler.read_bytes()),
                'implementation_sources':{str(p.relative_to(ROOT)):sha(p.read_bytes())
                                          for p in sorted(source_paths)},
                'status':'PASS' if all(r['status']=='PASS' for r in campaign.rows) else 'FAIL',
                'environment':'stock z80pack 62K CP/M 2.2, Z80, disposable IBM-3740 disks, user 0',
                'simulator_sha256':sha(campaign.sim.read_bytes()),
                'boot_template_sha256':sha(campaign.template.read_bytes()),
                'historical_artifacts':{n:{'url':BASE+u,'bytes':s,'sha256':h} for n,(u,s,h) in ARTIFACTS.items()},
                'our_commands':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in commands.items()},
                'cases':campaign.rows}
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        passed=sum(r['status']=='PASS' for r in campaign.rows)
        print(f'{report["status"]}: {passed}/{len(campaign.rows)} historical interoperability cases; {args.output}/report.json')
        raise SystemExit(0 if report['status']=='PASS' else 1)


if __name__=='__main__':
    main()
