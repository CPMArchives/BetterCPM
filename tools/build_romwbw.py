#!/usr/bin/env python3
"""Build an isolated RomWBW engineering image from the common checked RAM core."""
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


def compile_image(assembler):
    from romwbw_media import DISKDEFS, image, tables
    from build_ccp import assemble
    from build_checked_command_loader import build_stages
    from build_checked_resident_rsx import build_rsx_components
    from build_z80pack_image import normalized, symbols
    from checked_build_contract import assembly_constants
    from checked_carriers import selected_contract
    from checked_rsx_pack import bind_slot
    # Installer publication is outside this initial engineering bring-up.
    from startup_record import build as startup_record
    from system_layout import CONTEXT, LAYOUT as L
    if not CONTEXT or CONTEXT[0]['target'] != 'romwbw':
        raise ValueError('RomWBW compile requires its prepared profile')
    out = ROOT/'build/romwbw'
    out.mkdir(parents=True, exist_ok=False)
    platform = ROOT/'src/platform/romwbw'
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
            if leaf == 'checked-load.inc':
                return read('src/platform/z80pack/checked-load.inc').replace(
                    'IF PL_M2+PL_ALTAIR+PL_CROM EQ 1', 'IF 1')
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
    text = text[:start]+read('src/platform/romwbw/recordio.inc')+'\n'+text[end:]
    bios = bytearray(component('bios', text, L['BIOS'], L['FILE']-L['BIOS']))
    bs = symbols(out/'bios.lst')
    bc = symbols(ROOT/'build/bdos/bdos.lst')
    bioslinks = equ(bs, ('BIO_DRIVE','BIO_TRACK','BIO_SECTOR','BIO_DMA'))
    disk = component('disk', read('src/platform/romwbw/disk.mac'), L['DISK'], L['BIOS']-L['DISK'],
                     {'bioslinks.inc': bioslinks})
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
              '        JP WB_CONTROL\n'+'        JP AC_UNSUP\n'*2+
              'AC_UNSUP: LD HL,2\n        RET\n'+read('src/platform/romwbw/control.inc')+
              '\nCPTCOUNT EQU'+tail+'\n        END\n')
    ctl = component('config',config,L['CONFIG'],1000)
    control = bind_slot(ctl.ljust(1024,b'\0'),identity)
    stage1 = (loader/'stage1.carrier').read_bytes()
    entry = (system/'R3ENTRY.RSX').read_bytes()
    for label,data in [('Z_EREL',stage1),('Z_ECTL',control),('Z_EENT',entry)]:
        at = bs[label]-L['BIOS']
        if bios[at] != 0x21 or len(data) != 1024:
            raise ValueError('checked loader fixup moved: '+label)
        struct.pack_into('<H',bios,at+1,binascii.crc_hqx(data,0xffff))
    table_data = tables(L)
    if len(table_data)+16 > L['RSX_STATE']-L['TABLES']:
        raise ValueError('disk tables/platform state overlap RSX state')
    resident = bytearray(52*128)
    parts = [(L['SYSTEM'],gateway,L['BDOS']),
             (L['BDOS'],(ROOT/'build/bdos/bdos.bin').read_bytes(),L['EXTENSIONS']),
             (L['EXTENSIONS'],ext,L['DISK']), (L['DISK'],disk,L['BIOS']),
             (L['BIOS'],bios,L['FILE']),
             (L['FILE'],(system/'fileloader.bin').read_bytes(),L['TABLES']),
             (L['TABLES'],table_data,L['RSX_STATE'])]
    for address,data,limit in parts:
        at = address-L['SYSTEM']
        if at < 0 or not data or address+len(data)>min(limit,L['SYSTEM']+len(resident)):
            raise ValueError(f'resident overlap at {address:04X}')
        resident[at:at+len(data)] = data
    boot = component('boot',read('src/platform/romwbw/boot.mac'),0x1000,512)
    payload = bytearray(160*128)
    def put(record,data,capacity):
        if len(data)>capacity:
            raise ValueError(f'package slot overflow at {record}')
        payload[record*128:record*128+len(data)] = data
    # Records 0 and 4 are retained as unused common-package slots.
    startup = ''
    put(1,startup_record(startup,system_base=L['SYSTEM']),256)

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
    files = [('RCP.CPX',(ROOT/'build/cpx/RCP.CPX').read_bytes()),
             ('R3PACK.RSX',(system/'R3PACK.RSX').read_bytes()),
             ('R3CACHE.RSX',(system/'R3CACHE.RSX').read_bytes()),

             ('README.TXT',b'BetterCP/M RomWBW engineering image.\r\n'
              b'Initial HBIOS engineering bring-up.\r\n'
              b'Use CONFIG /SHOW for block mappings; SYSGEN B: installs on an empty hd512 B:.\r\n\x1a')]
    # Small executable probes use the public CP/M interface only.
    for filename,source in [('AFILE.COM','filetest.mac'),('ATPA.COM','tpatest.mac'),('AIOTEST.COM','iotest.mac'),('AFAILIO.COM','failio.mac')]:
        files.append((filename,component(filename[:-4].lower(),
            read('src/platform/romwbw/'+source),0x100,4096)))
    block = read('src/platform/romwbw/config.mac').replace('ORG 0100H','ORG 08000H')
    block = block.replace('        LD SP,01F00H', '        LD (WB_RETSP),SP\n        LD SP,08F00H')
    block = block.replace('        JP 0\n', '        JP WB_BRET\n')
    block = block.replace('        END\n', 'WB_BRET: LD SP,(WB_RETSP)\n        RET\nWB_RETSP: DW 0\n        END\n')
    utility = read('src/platform/romwbw/utility.inc').replace('        JP 0\n','        JP WB_BRET\n')
    files.append(('BLOCKCFG.OVL',component('blockcfg',block,0x8000,0xE00,{'utility.inc':utility})))
    from build_romwbw_config import build as build_config
    files += build_config(assembler)

    files.append(('HELLO.COM',component('hello',
        "        ASEG\n        ORG 0100H\n        LD DE,MSG\n        LD C,9\n        CALL 5\n        JP 0\nMSG: DB 'ROMWBW TRANSIENT PASS',13,10,'$'\n        END\n",0x100,256)))
    util = ROOT/'build/utilities'
    for builder in ('rsx_utilities', 'echo_rsx'):
        subprocess.run([sys.executable, '-B', str(ROOT/'tools'/f'build_{builder}.py'),
                        '--assembler', str(assembler)], check=True, cwd=ROOT)
    files += [('RSX.COM', (util/'RSX.COM').read_bytes()),
              ('ECHO.RSX', (ROOT/'build/rsx/ECHO.RSX').read_bytes())]
    files.append(('AECHO.COM', component('aecho',
        "        ASEG\n        ORG 0100H\n        LD C,199\n        CALL 5\n        JP 0\n        END\n",0x100,128)))
    # Portable COM builders share the selected core/context. Disk-specific
    # CONFIG/SYSGEN above are retained; floppy-only DUP/SYSBUILD are excluded.
    from build_utilities import BUILDERS
    for builder in BUILDERS:
        if builder in ('fdb','disk_utilities','rsx_utilities'):continue
        subprocess.run([sys.executable,'-B',str(ROOT/'tools'/f'build_{builder}.py'),
                        '--assembler',str(assembler)],cwd=ROOT,check=True)
    files += [(name,(ROOT/'build/help'/name).read_bytes()) for name in ('HELP.COM','HELP.LBR')]
    present={name for name,data in files}
    from component_registry import utility_identities
    for name in sorted(utility_identities()):
        filename=name+'.COM'
        path=util/filename
        if filename not in present and path.is_file():
            files.append((filename,path.read_bytes()));present.add(filename)
    for path in sorted(util.iterdir()):
        if path.suffix.upper() in ('.OVL','.HLB','.HLP','.HIX') and path.name not in present:
            files.append((path.name,path.read_bytes()));present.add(path.name)
    for filename in ('NDR.RSX','BATCHIO.RSX'):
        path=ROOT/'build/rsx'/filename
        if path.is_file():files.append((filename,path.read_bytes()))
    from build_release_tcap import release_modules
    display_reports=release_modules('romwbw',assembler)
    files += [(name+'.RSX',(ROOT/'build/rsx'/(name+'.RSX')).read_bytes())
              for name in display_reports]
    prefix = bytearray(image(payload,boot,files)[:131072])
    prefix[2048:2560]=bytes(512)
    prefix[128:384]=bytes(256)
    prefix[32896:33152]=bytes(256)
    install=f'SG_SYSCRC EQU 0{binascii.crc_hqx(prefix,0xffff):04X}H\n'
    install_files=[(name,data) for name,data in files
                   if name not in ('AFILE.COM','ATPA.COM','AIOTEST.COM','AFAILIO.COM')]
    install_files.append(('SYSGEN.COM',None))
    install+=f'SG_COUNT EQU {len(install_files)}\nSG_LIST:\n'
    for name,data in install_files:
        stem,ext=name.split('.')
        record=bytearray((stem.ljust(8)+ext.ljust(3)).encode('ascii'))
        if data is not None:
            padded=data.ljust((len(data)+127)//128*128,b'\x1a')
            record+=struct.pack('<HHB',binascii.crc_hqx(padded,0xffff),len(padded)//128,1)
        else:record+=bytes(5)
        install+='        DB '+','.join(str(n) for n in record)+'\n'
    files.append(('SYSGEN.COM',component('sysgen-com',read('src/platform/romwbw/sysgen.mac'),
                 0x100,0x1C00,{'installer.inc':install})))
    raw = image(payload, boot, files)
    (out/'system.img').write_bytes(raw)
    (out/'diskdefs').write_text(DISKDEFS)
    if selected_contract(assembler) != contract:
        raise ValueError('RomWBW inputs changed during compilation')
    (out/'candidate.json').write_text(json.dumps({'target':'romwbw','status':'engineering image; guest checks pending',
        'contract':contract,'layout':L,'profile':CONTEXT[0],
        'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                      'cpm_sha256':hashlib.sha256(data.ljust((len(data)+127)//128*128,b'\x1a')).hexdigest()}
                 for name,data in files},
        'display_profiles':display_reports,
        'resident_parts':[{ 'address':a,'bytes':len(d),'limit':limit} for a,d,limit in parts],
        'boot_bytes':len(boot),'proxy_start':0xFE00},indent=2)+'\n')
    print(out/'system.img')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--compile',action='store_true',help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.compile:
        compile_image(a.assembler.resolve())
        return
    if not a.work:
        p.error('--work is required; use a fresh directory')
    from build_distribution import prepare_profile, source_identity
    from build_profiles import CONTEXT_ENV, PROFILES
    profile = PROFILES['romwbw-hbios']
    identity = source_identity(profile)
    if identity['assembler_sha256'] != __import__('hashlib').sha256(a.assembler.read_bytes()).hexdigest():
        p.error('use the source identity assembler at ~/bin/z80asm')
    root = prepare_profile(a.work.resolve(),'romwbw',identity,profile)
    environment = dict(os.environ)
    environment['BETTERCPM_IDENTITY_TARGET']='romwbw'
    environment['BETTERCPM_IDENTITY_STATE']='development'
    environment[CONTEXT_ENV] = str(root/'build/profile/context.json')
    with (root/'build.log').open('w') as log:
        subprocess.run([sys.executable,'-B',str(root/'tools/build_romwbw.py'),'--compile',
                        '--assembler',str(a.assembler.resolve())],cwd=root,env=environment,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    print(root/'build/romwbw')


if __name__ == '__main__':
    main()
