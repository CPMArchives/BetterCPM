"""Build the Model II engineering System Disk from the selected shared source."""
import binascii
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

from build_ccp import assemble
from build_checked_command_loader import build_stages
from build_checked_resident_rsx import build_rsx_components
from build_z80pack_image import normalized, symbols
from checked_build_contract import assembly_constants
from checked_carriers import selected_contract
from checked_rsx_pack import bind_slot
from checked_system_package import make, prepare, validate
from fdf_v1 import compile_file
from model2_media import DIAG, SOURCE, geometry, image
from startup_record import build as startup_record
from system_layout import CONTEXT, LAYOUT as L

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT/'src/platform/trs80m2'
OUT = ROOT/'build/trs80m2'
ASM = Path.home()/'bin/z80asm'


def build():
    if not CONTEXT or CONTEXT[0]['target'] != 'trs80m2':
        raise ValueError('select --target trs80m2 --profile model2-fullram using build_distribution.py')
    contract = selected_contract(ASM)
    identity = bytes.fromhex(contract['compatibility_id'])
    const = assembly_constants(contract)
    OUT.mkdir(parents=True, exist_ok=True)

    def tool(name):
        command=[sys.executable,'-B',str(ROOT/'tools'/f'build_{name}.py')]
        if name!='fdb':command+=['--assembler',str(ASM)]
        subprocess.run(command,cwd=ROOT,check=True)

    def read(name):
        return (ROOT/name).read_text(encoding='ascii')

    def equate(values, names):
        return ''.join(f'{n} EQU 0{values[n]:04X}H\n' for n in sorted(names))

    def component(name, text, base, capacity, includes=None):
        def include(match):
            leaf = match[1]
            if leaf in (includes or {}):
                return includes[leaf]
            if (PLATFORM/leaf).is_file():
                return expand((PLATFORM/leaf).read_text(encoding='ascii'))
            return match[0]
        def expand(source):
            return re.sub(r'^[ \t]*INCLUDE[ \t]+([\w.-]+)[ \t]*$', include, source, flags=re.M|re.I)
        data = assemble(ASM, const + expand(normalized(text)), OUT/(name+'.bin'), OUT/(name+'.lst'), base)
        if not 0 < len(data) <= capacity:
            raise ValueError(f'{name}: {len(data)} bytes, {capacity} available')
        return data

    for builder in ('bdos','fileloader','rsxresolver','ccp','rcp_cpx'):
        tool(builder)
    system = ROOT/'build/system'
    build_rsx_components(contract, ASM, system)
    loader = OUT/'command-loader'
    build_stages(loader, identity, ASM)
    fmt = geometry()
    # The common BIOS masks a record index inside the staging area. BCM2SS has
    # four records per data sector; keep the first 512 bytes available to FL_NEXT.
    binding = read('src/platform/trs80m2/console.inc') + '\n        INCLUDE checked-load.inc\nPL_CURSOR: JP M2_CURSOR\n'
    bios = bytearray(component('bios', read('src/bios/bios.mac'), L['BIOS'],
                               L['FILE']-L['BIOS'], {'biosplat.inc':binding}))
    bs = symbols(OUT/'bios.lst')
    bc = symbols(ROOT/'build/bdos/bdos.lst')
    bioslinks = equate(bs, ('BIO_DRIVE','BIO_TRACK','BIO_SECTOR','BIO_DMA','BIO_QUART',
                            'BIO_PCYL','B_PSide','B_PDrive','BIO_PSEC'))
    core = equate(bc, ('UB_DMA','UB_DRIVE','UB_USERNO','UB_COLUMN','UB_LISTE'))
    disk = component('disk', read('src/bios/disk.mac').replace('INCLUDE layout.inc','INCLUDE layout.inc\n        INCLUDE profile.inc'), L['DISK'], L['BIOS']-L['DISK'],
                     {'hardware.inc':'', 'bioslinks.inc':bioslinks})
    ds = symbols(OUT/'disk.lst')
    ext = component('extensions', read('src/system/extens.mac'), L['EXTENSIONS'], L['DISK']-L['EXTENSIONS'],
                    {'core.inc':core, 'versions.inc':read('src/bdos/versions.inc')})
    es = symbols(OUT/'extensions.lst')
    cfg = component('config', read('src/bios/config.mac'), L['CONFIG'], 1000,
                    {'disklinks.inc':equate(ds,[k for k in ds if k.startswith('DC_')]),
                     'hardware.inc':'', 'bioslinks.inc':bioslinks,
                     'cpxlinks.inc':equate(es, ('EX_RETURN','BCX_MVAL'))})
    gateway = component('gateway',read('src/system/gateway.mac'),L['SYSTEM'],L['BDOS']-L['SYSTEM'],
                        {'core.inc':core})
    boot = component('boot',read('src/platform/trs80m2/boot.mac'),0x1000,512)
    tables = bytearray()
    alv = L['TABLES']+4*80
    for i in range(4):
        tables += struct.pack('<8H',0,0,0,0,L['DIRBUF'],L['TABLES']+80*i+17,alv+64+i*32,alv)+fmt.binding(i)
    if (fmt.dsm + 8)//8 > 64 or fmt.cks > 32:
        raise ValueError('disk format exceeds allocated ALV or per-drive CSV')
    tables += bytes(64+4*32)
    control = bind_slot(cfg.ljust(1024,b'\0'), identity)
    stage1 = (loader/'stage1.carrier').read_bytes()
    entry = (system/'R3ENTRY.RSX').read_bytes()
    for label,data in [('Z_EREL',stage1),('Z_ECTL',control),('Z_EENT',entry)]:
        at = bs[label]-L['BIOS']
        if bios[at] != 0x21 or len(data)!=1024:
            raise ValueError('checked loader checksum operand moved')
        struct.pack_into('<H',bios,at+1,binascii.crc_hqx(data,0xffff))
    if disk[-16:]!=identity or ds['Z_CMP']!=L['BIOS']-26 or bs['Z_CRC']!=L['FILE']-32:
        raise ValueError('checked resident service identity or layout mismatch')
    resident = bytearray(52*128)
    def install(address,data,limit):
        if address < L['SYSTEM'] or not data or address+len(data)>limit or address+len(data)>L['SYSTEM']+len(resident):
            raise ValueError(f'resident overlap at {address:04X}')
        offset = address-L['SYSTEM']
        resident[offset:offset+len(data)] = data
    parts = [(L['SYSTEM'],gateway,L['BDOS']),(L['BDOS'],(ROOT/'build/bdos/bdos.bin').read_bytes(),L['EXTENSIONS']),
             (L['EXTENSIONS'],ext,L['DISK']),(L['DISK'],disk,L['BIOS']),(L['BIOS'],bios,L['FILE']),
             (L['FILE'],(system/'fileloader.bin').read_bytes(),L['TABLES']),(L['TABLES'],tables,L['RSX_STATE'])]
    for addr,data,limit in parts:
        install(addr,data,limit)
    payload = bytearray(160*128)
    def put(record, data, cap):
        if len(data)>cap: raise ValueError(f'package slot overflow at record {record}')
        payload[record*128:record*128+len(data)] = data
    put(1,startup_record('',system_base=L['SYSTEM']),256)
    put(3,DIAG,128)
    put(4,boot,512)
    put(8,resident,52*128)
    put(60,stage1,1024)
    put(68,control,1024)
    put(76,entry,1024)
    put(84,(loader/'stage2.carrier').read_bytes(),2048)
    put(100,(system/'R3RESOL.RSX').read_bytes(),1024)
    put(108,(ROOT/'build/ccp/ccp.rlm').read_bytes(),13*512)
    payload=bytes(payload)
    (OUT/'resident.bin').write_bytes(resident)
    (OUT/'bios.bin').write_bytes(bios)
    prepare(ROOT,OUT,payload,bs)
    pkgdef=json.loads((OUT/'checked-package.json').read_text())
    package=make(payload,pkgdef)
    validate(package,pkgdef)
    (OUT/'SYSTEM.SYS').write_bytes(package)
    (OUT/'system-tracks.bin').write_bytes(payload)
    files=[('RCP.CPX',(ROOT/'build/cpx/RCP.CPX').read_bytes()),('R3PACK.RSX',(system/'R3PACK.RSX').read_bytes()),
           ('R3CACHE.RSX',(system/'R3CACHE.RSX').read_bytes()),('DISK.FDB',compile_file(SOURCE)),('SYSTEM.SYS',package)]
    for builder in ('rsx_utilities','cpx_utility','disk_utilities','hello_rsx',
                    'screen_backends','adm3a','vt52','ansi','fdb','rcp_transients',
                    'era','ren','type','pip','batch'):
        tool(builder)
    # Assemble the same existing command collection selected by the other
    # release targets. This completes distribution membership, not OS scope.
    tool('ed')
    tool('p2dos_rsx')
    (OUT/'DISK.FDB').write_bytes(compile_file(SOURCE))
    util = ROOT/'build/utilities'
    # Use the selected target for component provenance and development identity.
    from build_path import build as path_command
    from build_stat import build as stat
    from build_time import build as time_command
    for build_utility in (stat, time_command):
        build_utility(ASM, util, target='trs80m2', identity_state='development')
    files.append(('PATH.COM', path_command(ASM, util, target='trs80m2', identity_state='development')))
    names = ('STAT.COM','TIME.COM','RSX.COM','CPX.COM','CONFIG.COM','DUP.COM','SYSGEN.COM')
    programs = [(name,(util/name).read_bytes()) for name in names]
    from build_release_tcap import release_modules
    release_modules('model2', ASM)
    for name in ('M2SCRN','ADM3A','VT52','ANSI'):
        filename=name+'.RSX'
        files.append((filename,(ROOT/'build/rsx'/filename).read_bytes()))
    from build_distribution import selected_files
    manifest=json.loads((ROOT/'metadata/distribution.json').read_text())
    selection,_=selected_files(manifest,'trs80m2',ROOT)
    files=[(row['name'],data) for row,data in selection]
    media = image(payload,files)
    utilities = image(bytes(160*128),programs + [('DISK.FDB',compile_file(SOURCE))],bootable=False)
    (OUT/'Model-II-Utilities-candidate.imd').write_bytes(utilities)
    if selected_contract(ASM) != contract:
        raise ValueError('source changed during Model II build')
    (OUT/'Model-II-System-candidate.imd').write_bytes(media)
    fixtures = OUT/'qualification'
    fixtures.mkdir()
    for name, path in [('HELLO.RSX', ROOT/'build/rsx/HELLO.RSX'), ('RSXTEST.COM',util/'RSXTEST.COM')]:
        (fixtures/name).write_bytes(path.read_bytes())
    manifest = {
        'target':'trs80m2', 'status':'engineering candidate; guest qualification outstanding',
        'profile':CONTEXT[0]['profile'], 'source_revision':contract['source_revision'],
        'compatibility_id':identity.hex(),
        'assembler_sha256':hashlib.sha256(ASM.read_bytes()).hexdigest(),
        'planned_tpa':CONTEXT[0]['capacities']['maximum_com_bytes'],
        'rom_loader_bytes':len(boot), 'console_code_end':bs['M2_VIDEO_END'],
        'qualification_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fixtures.iterdir())},
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.imd'))}
    }
    (OUT/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    build()
