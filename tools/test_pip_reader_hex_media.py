#!/usr/bin/env python3
"""Compare automatic reader HEX selection with the pinned DRI binary."""
import argparse
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from test_pip_hex import record
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def launcher(binary, command, payload):
    """Supply deterministic INP/BDOS-reader input within this test process."""
    data = bytearray(binary.read_bytes())
    entry = int.from_bytes(data[1:3], 'little')
    page = bytearray()
    labels = {}
    fixups = []
    def emit(*values):
        page.extend(values)
    def word(label, offset=0):
        fixups.append((len(page), label, offset)); page.extend(b'\0\0')
    def label(name):
        labels[name] = 0x10a + len(page)
    label('reader')
    emit(0x79, 0xfe, 3, 0xc2); word('fallback')
    emit(0xcd); word('input')
    emit(0x6f, 0x26, 0, 0xc9)
    label('fallback'); emit(0xc3, 0, 0)
    label('input')
    emit(0xc5, 0xd5, 0xe5)
    label('pointer'); emit(0x21); word('payload')
    emit(0x7e, 0x23, 0x22); word('pointer', 1)
    emit(0x32, 9, 1, 0xe1, 0xd1, 0xc1, 0xc9)
    label('payload'); page.extend(payload)
    for pos, name, offset in fixups:
        page[pos:pos+2] = struct.pack('<H', labels[name] + offset)
    assert len(page) <= 246
    data[10:10+len(page)] = page
    base = 256 + len(data)
    tail = bytes([len(command)]) + command + b'\r'
    code = (b'\x2a\x06\x00\x22' + struct.pack('<H', labels['fallback']+1)
            + b'\x21' + struct.pack('<H', labels['reader']) + b'\x22\x06\x00'
            + b'\x21' + struct.pack('<H', base+26)
            + b'\x11\x80\x00\x01' + struct.pack('<H', len(tail))
            + b'\xed\xb0\xc3' + struct.pack('<H', entry))
    assert len(code) == 26
    data[0:3] = b'\xc3' + struct.pack('<H', base)
    data[3:6] = b'\xc3' + struct.pack('<H', labels['input'])
    return data + code + tail



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT/'build/z80pack')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = ROOT/'build/test-results/pip-reader-hex'
    report.mkdir(parents=True, exist_ok=True)
    payload = b'noise\r\n' + record(b'ABC') + b'\n:00000001FF\r\n\x1a'
    cases = [('INP', 'HEX', ''), ('RDR', 'HEX', ''),
             ('INP', 'TXT', ''), ('RDR', 'HEX', 'H'), ('INP', 'HEX', 'I')]
    with tempfile.TemporaryDirectory(prefix='pip-reader-', dir='/private/tmp') as tmp:
        work = Path(tmp)
        shutil.copytree(args.image_dir/'disks', work/'disks')
        shutil.copy2(args.image_dir/'diskdefs', work/'diskdefs')
        disk = work/'disks/drivea.dsk'
        commands = [(b'A4:\r', b'A4>_ ', 30)]
        for i, (device, ext, options) in enumerate(cases):
            for prefix, binary in [('OUR', ROOT/'build/pip-development/PIP.COM'),
                                   ('REF', ROOT/'third_party/dri-pip/PIP-1.5-reference.COM')]:
                name = prefix + str(i)
                command = (name+'.'+ext+'='+device+':'+('['+options+']' if options else '')).encode()
                program = work/(name+'.COM')
                program.write_bytes(launcher(binary, command, payload))
                subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(program),'0:'+program.name],cwd=work,check=True)
                commands.append((b':'+name.encode()+b'\r', b'A4>_ ', 30))
        session(args.simulator, work/'disks', commands, report/'transcript.txt')
        for i, (_, ext, _) in enumerate(cases):
            outputs = []
            for prefix in ('OUR', 'REF'):
                name = prefix+str(i)+'.'+ext
                output = work/name
                subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),'4:'+name,str(output)],cwd=work,check=True)
                outputs.append(output.read_bytes())
            assert outputs[0] == outputs[1], (cases[i], outputs)
    print('PASS: automatic INP HEX, ordinary RDR/TXT, explicit H and I match pinned DRI PIP')


if __name__ == '__main__':
    main()
