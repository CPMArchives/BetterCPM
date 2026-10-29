#!/usr/bin/env python3
"""Build MD5SUM with the CRCKSUM file engine and its own digest/list modules."""
from pathlib import Path
import argparse
import hashlib
import math
import re
from build_ccp import assemble
from component_build import recorded_build
from component_identity import identification, title
from utility_versions import identities, display_development
from search_source import selector_source

ROOT = Path(__file__).resolve().parents[1]


def shared(name, start=None, end=None):
    """Compose whole labelled routines, failing if their shared boundary moves."""
    text = (ROOT/f'src/utilities/crc/{name}.inc').read_text()
    # CRC-only reference failure guard and report strings must not alter MD5's
    # independently qualified discovery and single-digest report paths.
    if name == 'lists':
        text = text.replace('        LD (REFFAIL),A\n', '')
        text = text.replace('        LD A,(REFFAIL)\n        OR A\n        JP NZ,DUNEXT\n', '')
        text = text.replace('        JP Z,REFOPENERR', '        JP Z,LISTIOER')
        begin = text.index('REFOPENERR:\n')
        finish = text.index('LISTIOER:\n', begin)
        text = text[:begin] + text[finish:]
        text = text.replace("MSGMATCH: DB ': MATCH (all ',0\nMCHEND: DB ' checksums)',0",
                            "MSGMATCH: DB ' MATCH',0")
    if start:
        text = text[text.index(start+':\n'):]
    if end:
        text = text[:text.index(end+':\n')]
    return text


def module(name):
    return (ROOT/f'src/utilities/md5sum/{name}.inc').read_text()


def expanded_source():
    command = (shared('command', end='COMMAND')+module('command')+
               shared('command', 'DESTINAT', 'OPTIONS')+
               shared('command', 'COLLIDE', 'APPENDAL'))
    # MD5 has no expected size in its reference format, but the common check
    # loop still uses its prepass to avoid reading unlisted files.
    lists = (shared('lists', end='CHECKFOU')+module('reference')+
             shared('lists','CHECKDIA','DISCOVER')+
             shared('lists', 'EXREFERE', 'CANDIDAT')+module('candidates')+
             shared('lists', 'MISSCAND'))
    # No size, discovery-tier or algorithm-mask data is interpreted by MD5.
    begin = lists.index('DISCOV01:\n')
    end = lists.index('MSGREFER:',begin)
    lists = lists[:begin]+lists[end:]
    lists = '\n'.join(line for line in lists.split('\n') if not line.startswith(
        ('MSGAMBIG:', 'MSGSKIPP:', 'MSGSIZEM:')))
    lists = lists.replace("No CRC list found", "No MD5 list found").replace(
        'CHECKSUM MISMATCH', 'MD5 MISMATCH')
    lists = lists.replace('        LD (CATCRC),A\n', '').replace('        LD (CATORDER),A\n', '')
    lists = lists.replace("        CP ';'\n        JR Z,LISTNEXT\n", '')
    lists = lists.replace('        CALL PARSELIN\n', '        LD HL,LISTLINE\n        CALL PARSELIN\n')
    # Do not strip high bits from modern md5sum text; reject embedded NULs.
    lists = lists.replace('        AND 127\n        CP 26', '        CP 26')
    lists = lists.replace('        CP 13\n        JR Z,RLCHAR',
                          '        OR A\n        JR Z,RLOVER\n        CP 13\n        JR Z,RLCHAR')
    # Count each physical line before diagnosing it (including overlong/NUL).
    lists = lists.replace('        JR NZ,LISTNEXT\n        LD HL,LISTLI01',
                          '        JR NZ,MDLONG\n        LD HL,LISTLI01',1)
    lists = lists.replace('LISTBADL:\n', 'MDLONG:\n        LD HL,LISTLI01\n        CALL INC32\nLISTBADL:\n')
    lists = lists.replace('        CALL NZ,LISTBAD\n        OR A\n        RET\nLISTGET:',
                          '        OR A\n        RET\nLISTGET:')
    # The historical/native parser bookkeeping has no MD5 counterpart.
    for variable in ('LISTFORM','LISTPEND'):
        lists = lists.replace('        LD ('+variable+'),A\n','')
    lists = lists.replace('        LD A,(LISTPEND)\n        OR A\n        CALL NZ,LISTBAD\n','')
    lists = '\n'.join(line for line in lists.split('\n') if not line.startswith(
        ('LISTFORM:', 'LISTPEND:', 'DISCCOUN:', 'DISCCAND:', 'MATCHMAS:',
         'SAVEDALG:', 'OLDALG:', 'EMASK:', 'ESIZE:', 'ESIZETYP:',
         'EMATCHMA:', 'CMBIT:', 'KSIZE:')))
    # A carriage return must introduce LF; do not erase an embedded CR.
    lists = lists.replace('        CP 13\n        JR Z,RLCHAR',
        '        CP 13\n        JR NZ,MDNOTCR\n'
        '        CALL LISTGET\n        JR C,MDCRBAD\n        CP 10\n'
        '        JR Z,RLDONE\nMDCRBAD:\n        LD A,1\n'
        '        LD (LLTOOLON),A\n        JR RLCHAR\nMDNOTCR:')
    # No saved section boundaries; the entry streams concatenate directly.
    output = shared('output', end='WSECTION')+shared('output', 'WLINE')
    traverse = shared('traverse')
    start = traverse.index('        ; Preflight determines')
    end = traverse.index('        CALL WLOCAL\n', start)
    traverse = traverse[:start]+traverse[end:]
    source = (ROOT/'src/utilities/md5sum.mac').read_text()
    for name, text in {'command':command, 'traverse':traverse,
                       'render':module('render'), 'lists':lists,
                       'output':output, 'algorithms':module('algorithms'),
                       'support':shared('support')}.items():
        source = source.replace('; @'+name+'@', text)
    source = source.replace('; @list-parser@', module('list-parser'))
    rows = ['MDSCHEDULE:']
    shifts = ((7,12,17,22),(5,9,14,20),(4,11,16,23),(6,10,15,21))
    for i in range(64):
        k = i if i<16 else ((5*i+1)%16 if i<32 else ((3*i+5)%16 if i<48 else (7*i)%16))
        constant = int(abs(math.sin(i+1))*(1<<32))
        values = [4*k,shifts[i//16][i%4],*constant.to_bytes(4,'little')]
        rows.append('        DB '+','.join(f'0{x:02X}H' for x in values))
    source = source.replace('; @md5-schedule@', '\n'.join(rows))
    version, revision = identities()['MD5SUM']
    dev = display_development('utility:MD5SUM')
    identity = identification('MD5SUM',version,revision,'MD5 File Digests',development=dev)
    help_text = (title('MD5SUM',version,revision,development=dev)+
        '\n  - - -\n | MD5 File Digests\n |\n'
        ' |   Usage: MD5SUM [options] [filespec ...] [options]\n\n'
        '   Options:\n'
        '     /FILE=name  Write a master list.\n'
        '     /LOCAL=name Write a list in each target DU.\n'
        '     /CHECK[=name] Verify a list in each target DU.\n'
        '     /40         Narrow screen display.\n\n'
        '     /HELP       Display this help.\n'
        '     /VER        Display utility identification.\n')
    def string(label,value):
        return label+':\n'+''.join("        DB '"+line.replace("'","''")+"',13,10\n" if line else '        DB 13,10\n'
                                  for line in value.splitlines())+'        DB 0\n'
    source = source.replace('; @identity@',string('VERSIONT',identity)+string('HELPTEXT',help_text))
    return source.replace('; @selectors@',selector_source()).replace('CRCKSUM:', 'MD5SUM:')


@recorded_build('utility:MD5SUM')
def build(assembler, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    text = expanded_source()
    cross = text.replace('        CSEG\n','        ASEG\n').replace(
        '        .PHASE 0103H\n','        ORG 0103H\n').replace('        .DEPHASE\n','')
    data = b'\xc3\x03\x01'+assemble(assembler,cross,destination/'md5sum.bin',destination/'md5sum.lst',0x103)
    (destination/'MD5SUM.COM').write_bytes(data)
    native = re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                    r'\1\n        REPT \2\n        DB 0FFH\n        ENDM',text)
    prepared = native.replace('\n','\r\n').encode('ascii')+b'\x1a'
    (destination/'MD5SUM-NATIVE.MAC').write_bytes(prepared)
    import json
    (destination/'MD5SUM-native.json').write_text(json.dumps({
        'binary_sha256':hashlib.sha256(data).hexdigest(),
        'native_source_sha256':hashlib.sha256(prepared).hexdigest()},indent=2)+'\n')
    return data


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    a=p.parse_args()
    image=build(a.assembler,ROOT/'build/utilities')
    print(f'MD5SUM.COM: {len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}')
