"""Bind the shared CONFIG menus/PDS overlay to the RomWBW block backend."""
import re
from pathlib import Path
from build_config import expanded_source, build_image, validate_layout
from checked_build_contract import assembly_constants
from checked_carriers import selected_contract
ROOT=Path(__file__).resolve().parents[1]

def build(assembler):
    out=ROOT/'build/utilities';out.mkdir(exist_ok=True)
    (out/'config-validation.inc').write_text('SGVALID: DS 20\nSGVEND EQU $\n')
    (out/'config-iobyte.inc').write_text('IO_VALID: DW 0\n')
    text=expanded_source()
    text=text.replace("DB 'BDCF',5,4,4,64", "DB 'BDCF',6,2,0,64")
    text=text.replace('        CALL CF_PARSE                  ; valid quoted command text is not options',
                      '        CALL WB_ROUTE\n        CALL CF_PARSE                  ; valid quoted command text is not options')
    text=text.replace('        CALL INIT\n','        CALL INIT\n        CALL U_CHECK\n',1)
    # Inapplicable floppy editors have no entry on the block target. Retain
    # their label names as explicit unsupported stubs for legacy CLI paths.
    a=text.index('PHYSMENU:');b=text.index('RESETLOG:',a)
    labels=re.findall(r'^([A-Z][A-Z0-9_]*):',text[a:b],re.M)
    text=text[:a]+''.join(name+': JP WB_UNSUP\n' for name in labels)+text[b:]
    text=text.replace("        CP 'C'\n        JR Z,PHYSMENU", "        CP 'C'\n        JP Z,WB_BMENU")
    text=text.replace("        CP 'D'\n        JP Z,LOGMENU",'')
    text=text.replace("        CP 'E'\n        JP Z,EDITDRIVE",'')
    text=text.replace('FDBLOAD:', 'FDBLOAD: RET\nWB_FDB_UNUSED:',1)
    text=text.replace('SYSGEN: LD A,(CF_MODE)', 'SYSGEN: JP WB_ALL\nWB_SG_UNUSED: LD A,(CF_MODE)',1)
    a=text.index('CF_SHOW:');b=text.index('CF_SDRIVES:',a)
    # Keep referenced labels as unreachable stubs; /SHOW uses block discovery.
    labels=re.findall(r'^([A-Z][A-Z0-9_]*):',text[a:b],re.M)
    text=text[:a]+'CF_SHOW: JP WB_SHOW\n'+''.join(name+': JP WB_UNSUP\n' for name in labels if name!='CF_SHOW')+text[b:]
    a=text.index('IO_READ:');b=text.index('IO_MENU:',a)
    # Replace I/O editing implementation, retain its parser and menu below.
    labels=re.findall(r'^([A-Z][A-Z0-9_]*):',text[a:b],re.M)
    text=text[:a]+'IO_READ: JP WB_IOREAD\nIO_APPLY: JP WB_IOSET\n'+''.join(name+(': JP MAIN\n' if name=='IO_BACK' else ': JP WB_IODONE\n') for name in labels if name not in ('IO_READ','IO_APPLY'))+text[b:]
    # IO_SHOW is inside/after the menu and has its own target implementation.
    a=text.index('IO_SHOW:');b=text.index('IO_LIVE:',a)
    labels=re.findall(r'^([A-Z][A-Z0-9_]*):',text[a:b],re.M)
    text=text[:a]+'IO_SHOW: JP WB_IOSHOW\n'+''.join(name+': JP WB_UNSUP\n' for name in labels if name!='IO_SHOW')+text[b:]
    # Mirror each BCST record write into the checked package's saved record.
    text=text.replace('SGIO:   LD (SGWRITE),A','SGIO: JP WB_SGIO\nWB_SGRAW: LD (SGWRITE),A')
    text=text.replace('; @package-record-map@','')
    text=text.replace('        LD DE,(SGSPT)\n        LD BC,0\nSGDIV:', '        LD DE,(WB_EXTRA)\n        ADD HL,DE\n        LD DE,(SGSPT)\n        LD BC,0\nSGDIV:')
    # Main-menu strings must describe the selected hardware, not fake floppies.
    a=text.index('MAINMSG:');b=text.index('PHYHEAD:',a)
    menu=['[ A ] Startup command','[ B ] Cold-boot IOBYTE','[ C ] Block device bindings',
          '[ F ] Command environment / PDS','[ S ] Save configuration','Select A/B/C/F/S, or Ctrl-C to exit.']
    text=text[:a]+'MAINMSG:\n'+''.join("        DB '"+line+"',13,10\n" for line in menu)+'        DB 0\n'+text[b:]

    a=text.index('CQ_TEXT:')
    help_lines=['CONFIG: /SHOW /STARTUP="text" /DEFAULT /IOBYTE=n',
        'RomWBW: /LOGICAL=B /UNIT=n | /UNBIND, optionally /SAVE',
        'No arguments: shared startup, PDS and IOBYTE menus; block bindings.']
    text=text[:a]+'CQ_TEXT:\n'+''.join("        DB '"+line+"',13,10\n" for line in help_lines)+"        DB '$'\n        END\n"

    backend=(ROOT/'src/platform/romwbw/config-backend.inc').read_text()
    utility=(ROOT/'src/platform/romwbw/utility.inc').read_text()
    text=text.replace('CF_MAIN_END:',backend+'\n'+utility+'\nCF_MAIN_END:')
    image=build_image(assembler,assembly_constants(selected_contract(assembler))+text,out)
    validate_layout(image,(out/'config.lst').read_text(encoding='latin1'))
    return [('CONFIG.COM',image),('PDSCONF.OVL',(out/'PDSCONF.OVL').read_bytes())]
