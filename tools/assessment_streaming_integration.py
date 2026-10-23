"""Select the Part 11 command/package contract in an isolated checked build."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def bind_command(data):
    from assessment_part10_stream import carrier
    profile=json.loads((ROOT/'assessment-profile.json').read_text())
    assert profile['contract']['carrier_epoch']==2
    return carrier(data,profile['compatibility_id'])

def apply(root):
    from assessment_checked_profiles import replace
    def edit(path,old,new):
        p=root/path;p.write_text(replace(p.read_text(),old,new))
    edit('tools/build_ccp.py','    module.write_bytes(header + data)',
         '    from assessment_streaming_integration import bind_command\n    module.write_bytes(bind_command(header + data))')
    for name in ('rcp','hello'):
        edit(f'tools/build_{name}_cpx.py','    module.write_bytes(module_data)',
             '    from assessment_streaming_integration import bind_command\n    module.write_bytes(bind_command(module_data))')
    p=root/'tools/build_z80pack_image.py';s=p.read_text()
    s=replace(s," loader=asm('reloader',reload,L['RELOADER'],L['RELOADER_CAPACITY'])", " subprocess.run([sys.executable,str(ROOT/'tools/build_streaming_loader.py'),str(ROOT),'--output',str(out/'command-loader')],check=True,stdout=subprocess.DEVNULL)\n loader=(out/'command-loader/stage1.bin').read_bytes()\n (out/'reloader.bin').write_bytes(loader)")
    s=replace(s," padded_loader=bound(loader.ljust(L['RELOADER_CAPACITY'],b'\\0')+selector.ljust(1024-L['RELOADER_CAPACITY'],b'\\0'), ROOT)"," padded_loader=(out/'command-loader/stage1.carrier').read_bytes()")
    s=replace(s," put(84,bytes(1021)+gateway_tail,1024)\n put(92,bytes(1021)+gateway_tail,1024)"," put(84,(out/'command-loader/stage2.carrier').read_bytes(),2048)")
    s=replace(s," (out/'resident.bin').write_bytes(resident)"," (out/'resident.bin').write_bytes(resident)\n from checked_system_package import prepare\n prepare(ROOT,out,bytes(logical[:160*128]),bs)")
    p.write_text(s)
    # Package version 2 is deliberately understood only by the selected checked
    # cpmsim utility. Legacy Model 4/ROM builders are not changed.
    p=root/'src/utilities/sysgen.mac';s=p.read_text()
    s=replace(s,"PKGMAGIC:DB 'BCSY',1,1,160,0", "PKGMAGIC:DB 'BCSY',2,2,160,0")
    s=replace(s,'        LD HL,PKGHEADER+16\n        LD DE,SOURCE', '        CALL P11HCHK\n        JP NZ,LFERR\n        LD HL,PKGHEADER+16\n        LD DE,SOURCE')
    s=replace(s,'        LD C,16\n        CALL BDOS\n        XOR A\n        RET\n\nLFERR:', '        LD C,16\n        CALL BDOS\n        INC A\n        JP Z,LFERR\n        CALL P11FCRC\n        JP NZ,LFERR\n        CALL P11CHECK\n        JP NZ,LFERR\n        XOR A\n        RET\n\nLFERR:')
    s=replace(s,'IMAGEOK:                                ; imageok\n        CALL PATCHTARGET','IMAGEOK:                                ; imageok\n        CALL P11CHECK\n        JP NZ,PKGBAD\n        CALL P11FILES\n        JP NZ,P11FBAD\n        CALL PATCHTARGET')
    s=replace(s,'        INCLUDE sysgen-export.inc','        INCLUDE sysgen-export.inc\n; @part11-package@')
    # The longer admission path exceeds the old relative LFERR branch span.
    s=s.replace('JR Z,LFERR','JP Z,LFERR').replace('JR NZ,LFERR','JP NZ,LFERR')
    p.write_text(s)
    p=root/'src/utilities/sysgen-export.inc';s=p.read_text()
    s=replace(s,'XREADOK:CALL XHEADER\n        JP NZ,PKGBAD','XREADOK:CALL P11CHECK\n        JP NZ,PKGBAD\n        CALL XHEADER\n        JP NZ,PKGBAD\n        CALL P11HEAD')
    p.write_text(s)
    edit('tools/build_disk_utilities.py',"        if stem=='sysgen':", "        if stem=='sysgen':\n            from checked_system_package import guard_source\n            text=text.replace('; @part11-package@',guard_source(ROOT))\n        if stem=='sysgen':")
    # Expose the private assessment identity in /VER, never reuse a released
    # utility build number for the changed installer.
    p=root/'tools/utility_versions.py';s=p.read_text()
    s=replace(s,"    return f'BetterCP/M {name} {version} ({detail})'", "    if name=='SYSGEN':\n        import json\n        ident=json.loads((ROOT/'assessment-profile.json').read_text())['compatibility_id']\n        detail='Assessment P11 '+ident[:8]\n    return f'BetterCP/M {name} {version} ({detail})'")
    p.write_text(s)
    from assessment_utility_guards import apply as guard_utilities
    guard_utilities(root)
