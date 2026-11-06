#!/usr/bin/env python3
"""Execute interactive working-catalogue operations with BDOS faults."""
from dataclasses import replace
import re
from test_fdb_roundtrip import FDBCommand, ROOT, machine, diskkey
from build_fdf_catalog import catalogue_payload
from fdfdecomp import decompile
from fdf_v1 import parse, serialize


class Session(FDBCommand):
    corrupt_readback = False
    fail_restoration = False
    arrival = None

    def bdos(self, fn, de):
        if fn == 32 and (de & 255) == 255:
            return self.user
        if fn == 6 and self.word(self.reg["SP"].value) == self.read_return:
            char = next(self.keys, None)
            if char is None:
                # Exit immediately and fail the assertion in run(), preserving
                # the transcript when a new/unexpected prompt exhausted input.
                self.unexpected_prompt = True
                self.keys = iter("Q\rD\r")
                char = next(self.keys)
            return ord(char)
        if fn == 17 and self.arrival and self.fcbkey(de)[2] == 'NEW.$$$':
            self.files[self.arrival] = b'appeared after confirmation'
            self.arrival = None
        if fn == 23 and self.fail_restoration and len(self.renamed) == 1:
            return 255
        result = super().bdos(fn, de)
        if fn == 20 and result == 0 and self.corrupt_readback and self.fcbkey(de)[2].endswith(".$$$"):
            self.mem[self.dma] ^= 1
        if fn == 23 and result != 255:
            self.checkpoints.append(dict(self.files))
        return result


def main():
    work = ROOT / 'build/fdb-session-test'
    work.mkdir(parents=True, exist_ok=True)
    m = machine(work, Session)
    m.read_return = int(re.search(r'^([0-9a-f]{4}).*\bASKREAD:', (work/'fdb.lst').read_text(), re.M | re.I)[1], 16)
    stock = catalogue_payload()
    entries = parse(decompile(stock))
    extra = replace(entries[0], ident='TEST109', description='New test definition')
    imported = serialize((extra,))
    expected = serialize((*entries, extra))
    key = lambda name: diskkey(1, name)
    dest, src, temp, backup = map(key, ('DISK.FDB', 'ADD.FDB', 'DISK.$$$', 'DISK.BAK'))
    original = {dest:stock, src:imported}

    def run(keys, files=original, failures=None):
        m.keys = iter(keys)
        m.checkpoints = []
        m.unexpected_prompt = False
        console = m.run('', files, failures=failures)
        assert not m.unexpected_prompt, console
        return console

    console = run('D\rMMI012\r4\rQ\rQ\r', {**original,key('FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes()})
    assert 'Canonical directory byte: 10240' in console
    console = run('P\rMMI012\rMMI012\r4\rA\rQ\rQ\r', {**original,key('FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes()})
    assert 'Canonical directory byte: 10240 | 10240' in console
    damaged = bytearray((work/'FDBVIEW.OVL').read_bytes())
    damaged[-1] ^= 1
    run('D\rQ\r', {**original,key('FDBVIEW.OVL'):bytes(damaged)})
    assert 'FDBVIEW.OVL mismatched/damaged' in m.console
    comparison = replace(next(e for e in entries if e.ident=='MMI012'), ident='CYLTEST', logical_track='CYLINDER',
                         spt=next(e for e in entries if e.ident=='MMI012').spt*2, dsm=389)
    viewfiles={**original, key('FDBVIEW.OVL'):(work/'FDBVIEW.OVL').read_bytes(),
               key('OTHER.FDB'):serialize((comparison,))}
    console = run('P\rMMI012\r/\rOTHER.FDB\rCYLTEST\r4\rQ\rQ\r', viewfiles)
    assert 'Canonical directory byte: 10240 | 20480*' in console, console
    assert m.files == viewfiles
    edit = 'I\rADD.FDB\rTEST109\r'
    save = 'S\r\rY\r'
    result = run(edit + save + 'Q\r')
    assert m.files == {dest:expected, src:imported}, result
    assert '1 added, 0 replaced' in result
    parked, promoted = m.checkpoints
    assert dest not in parked and parked[backup] == stock and parked[temp] == expected
    assert promoted[backup] == stock and promoted[dest] == expected
    # A power loss between either rename leaves complete recovery files.
    for interrupted in m.checkpoints:
        before = dict(interrupted)
        run('Q\r', interrupted)
        assert m.files == before
    m.fail_restoration = True
    run(edit + save + 'Q\rD\r')
    assert dest not in m.files and m.files[backup] == stock and m.files[temp] == expected
    m.fail_restoration = False
    m.corrupt_readback = True
    for filename in ('DISK.FDB', 'DISK.FDF'):
        run(edit + 'S\r'+filename+'\rY\rQ\rD\r')
        assert m.files[dest] == stock and not m.renamed
        assert 'failed readback' in m.console
    m.corrupt_readback = False
    # Resolve an ID and then a description on the imported working copy.
    duplicate = serialize((entries[0],))
    run('I\rADD.FDB\r\rU\rTEST109\rNew test definition\r'+save+'Q\r',
        {dest:stock, src:duplicate})
    assert m.files[dest] == expected and m.files[src] == duplicate, m.console
    # The same safe-save path handles text, including complete record readback.
    textfile = key('WORK.FDF')
    run('F\rWORK.FDF\r'+edit+save+'Q\r',
        {**original, textfile:decompile(stock).encode()+b'\x1a'})
    assert serialize(parse(m.files[textfile].split(b'\x1a')[0].decode())) == expected
    assert m.files[dest] == stock and m.files[src] == imported
    # One import is atomic even if an open or a conflict is cancelled later.
    result = run(edit + 'F\rD\rMISSING.FDB\rQ\rC\r' + save + 'Q\r')
    assert m.files[dest] == expected, result
    run('N\rI\rADD.FDB\r\rS\rNEW.FDB\rY\rQ\r')
    assert m.files[key('NEW.FDB')] == imported and m.files[dest] == stock
    for op, nth in [('make',1), ('write',2), ('close_output',1), ('rename',1), ('rename',2)]:
        result = run(edit + save + 'Q\rD\r', failures={op:nth})
        assert m.files[dest] == stock and m.files[src] == imported, (op, result)
        assert 'Catalogue saved' not in result
    run(edit + save + 'Q\r', failures={'delete':1})
    assert m.files[backup] == stock and m.files[dest] == expected and 'retained' in m.console
    multi = serialize((extra, entries[0]))
    result = run('I\rADD.FDB\r\rC\r'+save+'Q\r', {dest:stock, src:multi})
    assert m.files == {dest:stock, src:multi} and 'Modified' not in result
    revised = replace(entries[0], description='Replacement')
    run('I\rADD.FDB\r\rR\r'+save+'Q\r', {dest:stock, src:serialize((revised,))})
    assert m.files[dest] == serialize((revised, *entries[1:]))
    exchange = serialize((entries[0], extra))
    result = run(edit + 'L\rtest109\r' + save + 'Q\r', {dest:stock, src:exchange})
    assert re.search(r'TEST109 +New test definition +[0-9]+', result)
    assert m.files == {dest:expected, src:exchange}
    # Only Return requests a whole-file import. A leading space never does.
    run('I\rADD.FDB\r TEST109\rQ\r')
    assert m.files == original and 'Invalid filename or ID' in m.console
    # A stray suffix cannot confirm replacement, discard pending work or
    # leak out of an overlong field into a menu command.
    run(edit + 'S\r\rYNO\rQ\rDISAGREE\r' + save + 'Q\r')
    assert m.files[dest] == expected and len(m.renamed) == 2
    run(edit + 'S\r' + 'X'*33 + 'Q\r\x03' + save + 'Q\r')
    assert m.files[dest] == expected
    # The next save can be retried in the same session after a write failure.
    run(edit + save + save + 'Q\r', failures={'write':2})
    assert m.files == {dest:expected, src:imported}
    # Opening an ambiguous catalogue cannot silently commit it as the new default.
    ambiguous = serialize((extra, replace(entries[0], description=extra.description.lower())))
    run(edit + 'F\rD\rBAD.FDB\r' + save + 'Q\r',
        {**original, key('BAD.FDB'):ambiguous})
    assert m.files[dest] == expected and m.files[key('BAD.FDB')] == ambiguous
    assert 'Duplicate display names' in m.console
    run('F\rEMPTY.FDB\rQ\r', {**original, key('EMPTY.FDB'):serialize(())})
    assert 'EMPTY.FDB   Entries: 0' in m.console
    m.arrival = key('NEW.FDB')
    run(edit + 'S\rNEW.FDB\rY\rQ\rD\r')
    assert m.files[key('NEW.FDB')] == b'appeared after confirmation'
    assert m.files[key('NEW.$$$')] == expected and not m.renamed
    # BREAK from a naming prompt and a dirty exit preserves pending edits.
    run(edit + 'S\r\x03\x03C\r' + save + 'Q\r')
    assert m.files == {dest:expected, src:imported}
    # Export to an existing text catalogue while the session has pending work.
    textdest = key('OTHER.FDF')
    oldtext = decompile(serialize((entries[0],))).encode() + b'\x1a'
    result = run(edit + 'O\rTEST109\rOTHER.FDF\rY\rQ\rD\r', {**original,textdest:oldtext})
    assert serialize(parse(m.files[textdest].split(b'\x1a')[0].decode())) == serialize((entries[0],extra))
    assert m.files[dest]==stock and m.files[src]==imported and 'Unsaved catalogue' in result
    run(edit + 'O\r\rALL.FDB\rY\rQ\rD\r')
    assert m.files[key('ALL.FDB')] == expected
    run(edit + 'O\rTEST109\rONE.FDB\rY\rQ\rD\r')
    assert m.files[key('ONE.FDB')] == imported
    # Check every listed capacity (including cylinder and mixed-sector entries).
    result = run('L\r\r' + '\r'*8 + 'Q\r')
    assert result.count('Return for more') == 8
    for entry in entries:
        surface = sum(entry.sector_sizes or (entry.secsize,)*entry.psectors)
        raw_bytes = entry.cylinders * entry.sides * surface
        assert re.search(r' '+re.escape(entry.ident)+r' +'+re.escape(entry.description)+r' +'+str(raw_bytes)+r'\r',result)
    # Export conflict resolution changes only the proposed output descriptor.
    run(edit + 'O\rTEST109\rADD.FDB\rU\rOTHERID\rOther name\rY\r' + save + 'Q\r')
    assert m.files[dest] == expected and m.files[src] == serialize((extra,replace(extra,ident='OTHERID',description='Other name')))
    run(edit + 'O\rTEST109\rADD.FDB\rC\rQ\rD\r')
    assert m.files == original
    run(edit + 'O\r\rDISK.FDB\rN\rQ\rD\r')
    assert m.files == original
    run(edit + 'O\r\rDISK.FDB\rY\rQ\rD\r', failures={'rename':2})
    assert m.files[dest]==stock and m.files[src]==imported
    # Substrings cannot continue from an ID into its description.
    run('L\r'+entries[0].ident+' '+entries[0].description[:1]+'\rQ\r')
    assert 'No matching formats.' in m.console
    run('L\rnot a format\rQ\r')
    assert 'No matching formats.' in m.console
    run('L\r\r\x03Q\r')
    assert m.files == original
    # Export uses the recovery protocol for both encodings and leaves dirty
    # work available for a normal save after an output failure.
    for ext in ('FDB', 'FDF'):
        for op in ('make', 'write', 'close_output'):
            run(edit + 'O\rTEST109\rNEW.'+ext+'\rY\r' + save + 'Q\r',
                failures={op:1})
            assert m.files[dest] == expected and m.files[src] == imported
            assert key('NEW.'+ext) not in m.files
    for reserved in (temp, backup):
        run(edit + save + 'Q\rD\r', {**original, reserved:b'KEEP'})
        assert m.files == {**original, reserved:b'KEEP'}
    print('PASS working catalogue, 109 entries, save-as, cancellation and replacement fault recovery')


if __name__ == '__main__':
    main()
