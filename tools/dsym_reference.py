#!/usr/bin/env python3
"""Reference conversion of DRI LINK 1.3 final-address SYM pairs to DASM DSY.

This deliberately accepts one identified grammar, not REL objects or assembler
listings. Native DSYM has the same 255-name/12-character bounds. Output is
created exclusively; an existing destination is never replaced.
"""
import argparse
from pathlib import Path
import re


def convert(data):
    meaningful, marker, padding = data.partition(b'\x1a')
    if marker and padding.strip(b'\x1a \t\r\n'):
        raise ValueError('meaningful input after text terminator')
    tokens=meaningful.split()
    if len(tokens)%2:
        raise ValueError('incomplete address/name pair')
    symbols={}
    for address,name in zip(tokens[::2],tokens[1::2]):
        name=name.upper()
        if not re.fullmatch(rb'[0-9A-Fa-f]{4}',address):
            raise ValueError('address must contain four hexadecimal digits')
        if not re.fullmatch(rb'[A-Z_][A-Z0-9_]{0,11}',name):
            raise ValueError('illegal or overlength symbol')
        value=int(address,16)
        if name in symbols and symbols[name]!=value:
            raise ValueError('conflicting symbol '+name.decode('ascii'))
        symbols[name]=value
        if len(symbols)>255:
            raise ValueError('symbol capacity exceeded')
    return b''.join(f'{value:04X} '.encode()+name+b'\r\n'
                    for name,value in sorted(symbols.items()))+b'\x1a'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    output=convert(args.input.read_bytes())
    with args.output.open('xb') as stream:
        stream.write(output)
