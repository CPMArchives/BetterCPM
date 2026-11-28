#!/usr/bin/env python3
"""Build an isolated Altair engineering image from the common checked RAM core."""
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def compile_image(assembler, release=False):
    from altair_media import DISKDEFS, geometry, image
    from build_ccp import assemble
    from build_checked_command_loader import build_stages
    from build_checked_resident_rsx import build_rsx_components
    from build_z80pack_image import normalized, symbols
    from checked_build_contract import assembly_constants
    from checked_carriers import selected_contract
    from checked_rsx_pack import bind_slot
    from checked_system_package import make, prepare, validate
    from startup_record import build as startup_record
    from system_layout import CONTEXT, LAYOUT as L
    if not CONTEXT or CONTEXT[0]['target'] != 'altair':
        raise ValueError('Altair compile requires its prepared profile')
    out = ROOT/'build/altair'
    out.mkdir(parents=True, exist_ok=False)
    platform = ROOT/'src/platform/altair'
    contract = selected_contract(assembler)
    identity = bytes.fromhex(contract['compatibility_id'])
    const = assembly_constants(contract)
    read = lambda name: (ROOT/name).read_text(encoding='ascii')
    equ = lambda values, names: ''.join(f'{n} EQU 0{values[n]:04X}H\n' for n in sorted(names))

    def component(name, text, base, capacity, includes=None):
        def include(match):
            leaf = match[1]
            if leaf in (includes or {}):
                return expand(includes[leaf])
            if (platform/leaf).is_file():
                return expand((platform/leaf).read_text(encoding='ascii'))
            return match[0]
        def expand(source):
            return re.sub(r'^[ \t]*INCLUDE[ \t]+([\w.-]+)[ \t]*$', include, source, flags=re.M|re.I)
        data = assemble(assembler, const+expand(normalized(text)), out/(name+'.bin'), out/(name+'.lst'), base)
        if not 0 < len(data) <= capacity:
            raise ValueError(f'{name}: {len(data)} bytes, {capacity} available')
        return data

    for name in ('bdos', 'fileloader', 'rsxresolver', 'ccp', 'rcp_cpx'):
        subprocess.run([sys.executable, '-B', str(ROOT/'tools'/f'build_{name}.py'),
                        '--assembler', str(assembler)], check=True, cwd=ROOT)
    system = ROOT/'build/system'
    build_rsx_components(contract, assembler, system)
    loader = out/'command-loader'
    build_stages(loader, identity, assembler)
    # Retain the public BIOS/monitor/router and replace only the sector adapter.
    text = read('src/bios/bios.mac')
    start, end = text.index('BIOREAD:'), text.index('; LISTST') if '; LISTST' in text else text.index('BIOLSTST:')
    text = text[:start]+read('src/platform/altair/recordio.inc')+'\n'+text[end:]
    bios = bytearray(component('bios', text, L['BIOS'], L['FILE']-L['BIOS']))
    bs = symbols(out/'bios.lst')
    bc = symbols(ROOT/'build/bdos/bdos.lst')
    bioslinks = equ(bs, ('BIO_DRIVE','BIO_TRACK','BIO_SECTOR','BIO_DMA','BIO_QUART','BIO_PCYL','BIO_PSEC'))
    disk = component('disk', read('src/platform/altair/disk.mac'), L['DISK'], L['BIOS']-L['DISK'],
                     {'bioslinks.inc': bioslinks})
    ds = symbols(out/'disk.lst')
    core = equ(bc, ('UB_DMA','UB_DRIVE','UB_USERNO','UB_COLUMN','UB_LISTE'))
    ext = component('extensions', read('src/system/extens.mac'), L['EXTENSIONS'], L['DISK']-L['EXTENSIONS'],
                    {'core.inc':core, 'versions.inc':read('src/bdos/versions.inc')})
    es = symbols(out/'extensions.lst')
    gateway = component('gateway', read('src/system/gateway.mac'), L['SYSTEM'], L['BDOS']-L['SYSTEM'],
                        {'core.inc':core})
    # CPX controls are common. Unsupported geometry setters have no executable
    # overlay here; the resident API rejects them before attempting a load.
    tail = read('src/bios/config.mac').split('CPTCOUNT EQU',1)[1].split('CF_GETPH:',1)[0]
    config = ('        INCLUDE layout.inc\n'+equ(es,('EX_RETURN','BCX_MVAL'))+
              '        ASEG\n        ORG LY_CFG\n'+
              '        JP AC_UNSUP\n'*3+'        JP BF_CPXCTL\n'+
              '        JP AC_UNSUP\n'*3+'AC_UNSUP: LD HL,2\n        RET\nCPTCOUNT EQU'+tail+'\n        END\n')
    ctl = component('config',config,L['CONFIG'],1000)
    control = bind_slot(ctl.ljust(1024,b'\0'),identity)
    stage1 = (loader/'stage1.carrier').read_bytes()
    entry = (system/'R3ENTRY.RSX').read_bytes()
    for label,data in [('Z_EREL',stage1),('Z_ECTL',control),('Z_EENT',entry)]:
        at = bs[label]-L['BIOS']
        if bios[at] != 0x21 or len(data) != 1024:
            raise ValueError('checked loader fixup moved: '+label)
        struct.pack_into('<H',bios,at+1,binascii.crc_hqx(data,0xffff))
    fmt = geometry()
    tables = bytearray()
    alv = L['TABLES']+320
    for drive in range(4):
        tables += struct.pack('<8H',0,0,0,0,L['DIRBUF'],L['TABLES']+80*drive+17,
                              alv+32+drive*16,alv)+fmt.binding(drive)
    tables += bytes(32+64)
    if len(tables)!=416 or len(tables)+128 > L['RSX_STATE']-L['TABLES']:
        raise ValueError('disk tables/read staging overlap resident state')
    resident = bytearray(52*128)
    parts = [(L['SYSTEM'],gateway,L['BDOS']),
             (L['BDOS'],(ROOT/'build/bdos/bdos.bin').read_bytes(),L['EXTENSIONS']),
             (L['EXTENSIONS'],ext,L['DISK']), (L['DISK'],disk,L['BIOS']),
             (L['BIOS'],bios,L['FILE']),
             (L['FILE'],(system/'fileloader.bin').read_bytes(),L['TABLES']),
             (L['TABLES'],tables,L['RSX_STATE'])]
    for address,data,limit in parts:
        at = address-L['SYSTEM']
        if at < 0 or not data or address+len(data)>min(limit,L['SYSTEM']+len(resident)):
            raise ValueError(f'resident overlap at {address:04X}')
        resident[at:at+len(data)] = data
    boot_source = read('src/platform/altair/boot.mac').replace('AL_FIRST EQU 2','AL_FIRST EQU 5').replace('AL_AFTER EQU 10','AL_AFTER EQU 9')
    boot = component('boot',boot_source,0,128)
    stage2 = component('systemboot',read('src/platform/altair/systemboot.mac'),0x1000,512)
    payload = bytearray(160*128)
    def put(record,data,capacity):
        if len(data)>capacity:
            raise ValueError(f'package slot overflow at {record}')
        payload[record*128:record*128+len(data)] = data
    put(0,boot,128)
    startup = json.loads((ROOT/'metadata/distribution.json').read_text())['cold_start_command'] if release else ''
    put(1,startup_record(startup,system_base=L['SYSTEM']),256)
    put(4,stage2,512)
    put(8,resident,52*128)
    put(60,stage1,1024)
    put(68,control,1024)
    put(76,entry,1024)
    put(84,(loader/'stage2.carrier').read_bytes(),2048)
    put(100,(system/'R3RESOL.RSX').read_bytes(),1024)
    put(108,(ROOT/'build/ccp/ccp.rlm').read_bytes(),52*128)
    payload = bytes(payload)
    (out/'bios.bin').write_bytes(bios)
    (out/'resident.bin').write_bytes(resident)
    (out/'system-tracks.bin').write_bytes(payload)
    prepare(ROOT,out,payload,bs)
    pkgdef = json.loads((out/'checked-package.json').read_text())
    package = make(payload,pkgdef)
    validate(package,pkgdef)
    (out/'SYSTEM.SYS').write_bytes(package)
    files = [('RCP.CPX',(ROOT/'build/cpx/RCP.CPX').read_bytes()),
             ('R3PACK.RSX',(system/'R3PACK.RSX').read_bytes()),
             ('R3CACHE.RSX',(system/'R3CACHE.RSX').read_bytes()),
             ('SYSTEM.SYS',package)]
    util = ROOT/'build/utilities'
    util.mkdir(exist_ok=True)
    from build_stat import build as build_stat
    files.append(('STAT.COM',build_stat(assembler,util,target='altair',identity_state='assigned' if release else 'development')))
    for name in ('disk_utilities','path','ndr','batch','rsx_utilities','echo_rsx'):
        subprocess.run([sys.executable,'-B',str(ROOT/'tools'/f'build_{name}.py'),
                        '--assembler',str(assembler)],cwd=ROOT,check=True)
    files += [('RSX.COM',(util/'RSX.COM').read_bytes()),
              ('ECHO.RSX',(ROOT/'build/rsx/ECHO.RSX').read_bytes())]
    files += [(name,(util/name).read_bytes()) for name in
              ('CONFIG.COM','PDSCONF.OVL','SYSGEN.COM','DUP.COM','PATH.COM','NDR.COM','SUBMIT.COM','XSUB.COM')]
    files += [('NDR.RSX',(ROOT/'build/rsx/NDR.RSX').read_bytes()),
              ('BATCHIO.RSX',(ROOT/'build/rsx/BATCHIO.RSX').read_bytes())]
    from fdf_v1 import compile_file
    files.append(('DISK.FDB',compile_file(platform/'ALTRB77.FDF')))
    for filename,source in [('AFILE.COM','filetest.mac'),('ATPA.COM','tpatest.mac'),('AAPI.COM','apitest.mac')]:
        files.append((filename,component(filename[:-4].lower(),(platform/source).read_text(),0x100,4096)))
    files.append(('AECHO.COM',component('aecho',
        "        ASEG\n        ORG 0100H\n        LD C,199\n        CALL 5\n        JP 0\n        END\n",0x100,128)))
    files.append(('BYE.COM',component('bye',
        "        ASEG\n        ORG 0100H\n        LD A,0AAH\n        OUT (0A0H),A\n        LD A,080H\n        OUT (0A0H),A\n        HALT\n        END\n",0x100,128)))
    (out/'diskdefs').write_text(DISKDEFS)
    disks = out/'disks'
    disks.mkdir()
    for drive in 'abcd':
        raw = image(payload,files if drive=='a' else [])
        (disks/f'drive{drive}.dsk').write_bytes(raw)
    (out/'system.conf').write_text('sio1_baud_rate 0\nsio1_upper_case 0\nsio1_strip_parity 0\nsio1_drop_nulls 0\n[MEMORY 1]\nram 0,256\nboot 0\n')
    if release:
        from altair_release import build_collection
        build_collection(ROOT,out,payload,assembler)
    if selected_contract(assembler) != contract:
        raise ValueError('Altair inputs changed during compilation')
    (out/'candidate.json').write_text(json.dumps({'target':'altair','status':'engineering image; guest checks pending',
        'contract':contract,'layout':L,'profile':CONTEXT[0],
        'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                      'cpm_sha256':hashlib.sha256(data.ljust((len(data)+127)//128*128,b'\x1a')).hexdigest()}
                 for name,data in files},
        'resident_parts':[{ 'address':a,'bytes':len(d),'limit':limit} for a,d,limit in parts],
        'boot_bytes':len(boot),'stage2_bytes':len(stage2)},indent=2)+'\n')
    print(out/'disks/drivea.dsk')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--release',action='store_true',help='also prepare the complete release media collection')
    p.add_argument('--compile',action='store_true',help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.compile:
        compile_image(a.assembler.resolve(),a.release)
        return
    if not a.work:
        p.error('--work is required; use a fresh directory')
    from build_distribution import prepare_profile, source_identity
    from build_profiles import CONTEXT_ENV, PROFILES
    profile = PROFILES['altair-fullram']
    identity = source_identity(profile)
    if identity['assembler_sha256'] != __import__('hashlib').sha256(a.assembler.read_bytes()).hexdigest():
        p.error('use the source identity assembler at ~/bin/z80asm')
    root = prepare_profile(a.work.resolve(),'altair',identity,profile)
    environment = dict(os.environ)
    environment['BETTERCPM_IDENTITY_TARGET']='altair'
    environment['BETTERCPM_IDENTITY_STATE']='assigned' if a.release else 'development'
    environment[CONTEXT_ENV] = str(root/'build/profile/context.json')
    with (root/'build.log').open('w') as log:
        subprocess.run([sys.executable,'-B',str(root/'tools/build_altair.py'),'--compile',
                        '--assembler',str(a.assembler.resolve())]+(['--release'] if a.release else []),cwd=root,env=environment,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    print(root/'build/altair')


if __name__ == '__main__':
    main()
