#!/usr/bin/env python3
"""Build CONFIG, DUP and SYSGEN as ordinary transient programs."""
from pathlib import Path
import argparse
import json
import math
from build_ccp import assemble
from system_layout import expand_layout
from build_system_package import COMPONENTS
ROOT = Path(__file__).resolve().parents[1]

def builtin_source():
    rows=json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats']
    catalogue=''.join('*'+v['name']+'\r\n'+','.join(map(str,v['parameters']))+'\r\n'+','.join(map(str,v['sector_ids']))+'\r\n' for v in rows).encode('ascii')
    builtin='BUILTINS:\n'+'\n'.join('        DB '+','.join(map(str,catalogue[i:i+16])) for i in range(0,len(catalogue),16))+'\nBUILTINEND:\n'
    return builtin

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--config-extra-resident',type=Path)
    p.add_argument('--config-extra-spt',type=int)
    args=p.parse_args()
    out=ROOT/'build/utilities'
    out.mkdir(parents=True,exist_ok=True)
    builtin=builtin_source()
    from config_validation import validation_record,assembly
    from system_layout import LAYOUT
    from checked_carriers import selected_contract
    from checked_build_contract import assembly_constants
    checked = selected_contract(args.assembler)
    if checked:
        if args.config_extra_resident:
            p.error('checked utilities use only their selected resident; no extra platform descriptors')
        resident = ROOT/'build/z80pack/resident.bin'
        from build_z80pack_image import DEFAULT_FORMAT
        from fdf_format import select_fdf
        fmt = select_fdf(ROOT/'third_party/montezuma/DISK.FDF', DEFAULT_FORMAT)
        records=[validation_record(resident.read_bytes(),LAYOUT['SYSTEM'],52,8,fmt.spt)]
    else:
        records=[validation_record((ROOT/'build/system/resident.bin').read_bytes(),
                 LAYOUT['SYSTEM'],52,8,80)]
        if args.config_extra_resident:
            if not args.config_extra_spt:p.error('--config-extra-spt required')
            records.append(validation_record(args.config_extra_resident.read_bytes(),
                           LAYOUT['SYSTEM'],52,8,args.config_extra_spt))
    validation=assembly(records)
    (out/'config-validation.inc').write_text(validation)

    from iobyte_config import descriptor,assembly as io_assembly
    if checked:
        io_records=[descriptor(resident.read_bytes(),LAYOUT['SYSTEM'],
                     (resident.parent/'bios.lst').read_text(),fmt.spt,8)]
    else:
        from build_trs80_boot import assemble as boot_assemble,SOURCE,BUILD,STAGE1_ADDRESS
        stage=boot_assemble(args.assembler,SOURCE/'stage1.mac',BUILD/'stage1.bin',STAGE1_ADDRESS)
        io_records=[descriptor(stage,STAGE1_ADDRESS,(BUILD/'stage1.lst').read_text(),80,4)]
        if args.config_extra_resident:
            io_records.append(descriptor(args.config_extra_resident.read_bytes(),LAYOUT['SYSTEM'],
                              (args.config_extra_resident.parent/'bios.lst').read_text(),args.config_extra_spt,8))
    io_meta=io_assembly(io_records)
    (out/'config-iobyte.inc').write_text(io_meta)
    ccp = (ROOT/'build/ccp/ccp.bin').read_bytes()
    rlm = (ROOT/'build/ccp/ccp.rlm').read_bytes()
    relocations = int.from_bytes(rlm[14:16], 'little')
    ccpmeta = (f"CCP_SIZE EQU {len(ccp)}\n"
               f"CCP_ALLOC EQU {(len(ccp)+255)&~255}\n"
               f"CCP_RECORDS EQU {math.ceil(len(ccp)/128)}\n"
               f"CCP_RELOCS EQU {relocations}\n")
    partmeta = "".join(
        f"{symbol}_SIZE EQU {0 if checked else (ROOT/path).stat().st_size}\n"
        for symbol, path in (
            ('GATEWAY', 'build/system/gateway.bin'),
            ('BDOS', 'build/bdos/bdos.bin'),
            ('EXTENS', 'build/system/extensions.bin'),
            ('DISK', 'build/system/disk.bin'),
            ('BIOS', 'build/bios/bios.bin'),
            ('FILELOAD', 'build/system/fileloader.bin'),
            ('TABLES', 'build/system/tables.bin'),
        ))
    sysmeta = "".join(f"{name.split('.')[0]}_SIZE EQU {0 if checked else (ROOT/path).stat().st_size}\n"
                      for name, path, _offset, _capacity in COMPONENTS)
    for stem in ('config','dup','sysgen','sysbuild','respack','rlmbuild'):
        source=ROOT/f'src/utilities/{stem}.mac'
        text=expand_layout(source.read_text()).replace('        INCLUDE dup-cli.inc', (ROOT/'src/utilities/dup-cli.inc').read_text()).replace('        INCLUDE ccpmeta.inc', ccpmeta).replace('        INCLUDE partmeta.inc', partmeta).replace('        INCLUDE sysmeta.inc', sysmeta).replace('        INCLUDE disk/sysgen.inc',
            (ROOT/'src/utilities/disk/sysgen.inc').read_text()).replace('        INCLUDE disk/common.inc',
            (ROOT/'src/utilities/disk/common.inc').read_text()).replace('        INCLUDE disk/fdbread.inc',
            (ROOT/'src/utilities/disk/fdbread.inc').read_text()).replace('        INCLUDE disk/builtins.inc', builtin)
        text=text.replace('        INCLUDE sysgen-parse.inc', (ROOT/'src/utilities/sysgen-parse.inc').read_text())
        text=text.replace('        INCLUDE sysgen-export.inc', (ROOT/'src/utilities/sysgen-export.inc').read_text())
        text=text.replace('; @config-validation@',validation).replace('; @config-iobyte@',io_meta)
        text=text.replace('; @monitor-console@', (ROOT/'src/utilities/common/monitorconsole.inc').read_text())
        if stem=='config':
            from build_config import expanded_source
            text=expanded_source()
        if stem=='sysgen':
            from checked_system_package import guard_source
            text=text.replace('; @checked-package-guard@',guard_source(ROOT) if checked else '')
            from shared_ui import expand_sysgen_ui
            text=expand_sysgen_ui(text)
        if stem=='dup':
            from build_dup import expanded_source
            text=expanded_source()
        if checked:text=assembly_constants(checked)+text
        data=assemble(args.assembler,text,out/(stem.upper()+'.COM'),out/(stem+'.lst'),0x100)
        if len(data)>0x3D00:
            raise SystemExit(f'{stem}: program overlaps private stack')
        print(f'{stem.upper()}.COM: {len(data)} bytes')
if __name__=='__main__': main()
