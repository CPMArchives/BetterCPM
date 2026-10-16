"""Build-owned cold IOBYTE patch descriptors; never search code for a value."""
import re,struct,zlib

def symbol(listing,name):
    matches=re.findall(r'^([0-9a-f]{4})\s+.*?\b'+re.escape(name)+r':',listing,re.I|re.M)
    if len(matches)!=1:raise ValueError('missing/ambiguous cold IOBYTE symbol')
    return int(matches[0],16)

def descriptor(code,origin,listing,spt,first):
    at=symbol(listing,'IO_COLD')+1-origin
    if at<1 or code[at-1:at+4]!=bytes.fromhex('3e95320300'):
        raise ValueError('cold IOBYTE instruction contract changed')
    record,within=divmod(first*128+at,128)
    if record>=60 or not 1<=within<=124:raise ValueError('cold patch outside protected records')
    payload=code[(at//128)*128:(at//128+1)*128].ljust(128,b'\0')
    resident=at if first==8 else 0xffff
    return struct.pack('<HBBHI',spt,record,within,resident,zlib.crc32(payload))

def assembly(records):
    if len({r[:2] for r in records})!=len(records):raise ValueError('ambiguous cold patch geometry')
    return 'IO_VALID:\n'+''.join('        DB '+','.join(map(str,r))+'\n' for r in records)+'        DW 0\n'
