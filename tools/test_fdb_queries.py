"""Execute FDB's early query ABI and exact ASCII screens on the full Z80 core."""
from pathlib import Path
import ctypes as C
import json
import shutil
import tempfile
from component_development import select
from test_fdb_roundtrip import machine, ROOT
from test_usq_com import Command, diskkey


class QueryCommand(Command):
    query = True

    def bdos(self, fn, de):
        if self.query:
            assert fn == 9, ('query performed non-console service', fn)
            self.reg['IX'].value = 0xDEAD
            self.reg['IY'].value = 0xCAFE
        if fn == 2:
            self.console += chr(de & 255)
            return 0
        return super().bdos(fn, de)


def main():
    work = ROOT/'build/fdb-query-test'
    work.mkdir(exist_ok=True, parents=True)
    m = machine(work, QueryCommand)
    report = json.loads((work/'FDB-build-report.json').read_text())
    dev = '-dev' if report['display_selection']['development'] else ''
    heading = 'FDB 1.0 (001'+dev+')\r\n'
    version = heading+'  - - -\r\n | BetterCP/M Utilities\r\n | Disk Format Catalogue Workbench\r\n'
    help_text = (heading+'  - - -\r\n | Disk Format Catalogue Workbench\r\n |\r\n'
        ' |   Usage: FDB [source [destination]]\r\n\r\n'
        '   Forms:\r\n'
        '     FDB                   Open DISK.FDB in the workbench.\r\n'
        '     FDB file.FDB          Open a named catalogue in the workbench.\r\n'
        '     FDB in.FDB out.FDF    Export a catalogue as FDF text.\r\n'
        '     FDB in.FDF out.FDB    Compile FDF text to a catalogue.\r\n\r\n'
        '   Options:\r\n'
        '     /H /HELP    Display this help.\r\n'
        '     /VER        Display utility identification.\r\n')
    files = {diskkey(2,'KEEP.BIN',7):b'PRESERVE ALL BYTES'}
    query_stack = 0
    for word, expected in [('/VER',version),('/H',help_text),('/HELP',help_text)]:
        for tail in [word,word.lower(),'\t'+word.swapcase()+'\t',
                'FILE.FDB '+word,word+' BAD:NAME /BOGUS',
                word+' '+word,' '*(127-len(word))+word,
                word+' '*(127-len(word)),word+'\tX',
                '/VER '+word+' /H','/HELP '+word+' /VER']:
            m.query = True
            m.reg['IX'].value = 0xABCD
            registers = dict(zip(('A','B','C','D','E','H','L','F'),range(31,39)))
            for name,value in registers.items():m.reg[name].value=value
            want = help_text if '/H' in tail.upper().split() or '/HELP' in tail.upper().split() else expected
            actual = m.run(tail,files,drive=2,user=7,tpa=0x7000)
            assert actual == want,(tail,actual,want)
            assert [fn for fn,_ in m.events] == [9]
            assert m.reg['IX'].value == 0xABCD
            assert all(m.reg[name].value==value for name,value in registers.items())
            query_stack=max(query_stack,m.symbols['UC_STACK_TOP']-C.c_uint.in_dll(m.lib,'minimum_sp').value)
            assert m.files == files and (m.drive,m.user,m.dma)==(2,7,0x80)
            assert not m.created and not m.deleted and not m.renamed and not m.opened
            assert bytes(m.mem[0x81:0x81+len(tail)]) == tail.encode()
            assert bytes(m.mem[0x5c:0x80]) == bytes(36)
            first,last=m.symbols['UC_INPUT'],m.symbols['UC_STACK']
            assert bytes(m.mem[first:last]) == m.image[first-0x100:last-0x100]
    # Wrong token boundaries and slash controls fall through to normal startup.
    for tail in ['/VERIFY','/VER.X','X/VER','/VER/','/HELPER','/HELP.X',
                 'X/HELP','/HEL','/H.X','/H/','/VER\x0f','\x0fVER','',
                 'FILE.FDB ROUND.FDF']:
        m.query=False
        assert m.run(tail,files,tpa=0x7000)=='FDB: insufficient TPA or workspace.\r\n',tail
    for screen in (version,help_text):
        assert screen.isascii() and '\x1b' not in screen
        assert screen.replace('\r\n','').find('\n') == -1
        assert len(screen.splitlines()) <= 23
        assert max(map(len,screen.splitlines())) <= 79
    assert query_stack <= 512
    syntax=work/'syntax';syntax.mkdir(exist_ok=True)
    normal=machine(syntax)
    for tail in ['BAD.TXT OUT.FDB','DISK.FDB BAD.TXT']:
        assert normal.run(tail,files)==('Usage: FDB [source [destination]]\r\n'
                                        'Use FDB /HELP for help.\r\n')
        assert not normal.created and not normal.opened
    # Prove the new component uses granular automatic input baselines, not a
    # forced clean display or a fingerprint of the entire registry/repository.
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        plan=json.loads((ROOT/'metadata/component-inputs.json').read_text())['components']['utility:FDB']
        for name in plan['files']+['metadata/component-registry.json','metadata/component-inputs.json','metadata/component-baselines.json']:
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
        def state(target='z80pack'):
            return select('utility:FDB',Path.home()/'bin/z80asm',root=root,target=target)
        assert not state()['development'] and not state('trs80gp')['development']
        registry=root/'metadata/component-registry.json';data=json.loads(registry.read_text())
        data['components']['utility:TYPE']['revision']+=1;registry.write_text(json.dumps(data))
        assert not state()['development']
        with (root/'src/utilities/fdb.mac').open('a') as changed:changed.write('\n; changed selected input\n')
        assert state()['development'] and state('trs80gp')['development']
    print('PASS FDB query exact screens, precedence, token bounds, 127-byte tails, console-only ABI and normal fall-through;',m.cases,'query/fall-through cases +',normal.cases,'short-syntax cases; query stack',query_stack,'/512; automatic identity baselines PASS')


if __name__=='__main__':
    main()
