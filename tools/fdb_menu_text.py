"""Lossless encoding of fixed FDB messages to retain the existing RAM layout.

Only selected zero-terminated resident UI literals are eligible.
Dynamic catalogue strings and file-format text keep their existing format.
"""
import collections
import re

BLOCK=re.compile(r'^(\w+):[ \t]*(?:\n[ \t]*)?DB[^\n]*(?:\n[ \t]+DB[^\n]*)*',re.M)
FIELD=re.compile(r"'([^']*)'|([0-9]+)")

def messages(source):
    result=[]
    for m in BLOCK.finditer(source):
        name=m[1]
        if not (name.endswith('MSG') or name.startswith('EDRULE') or name in {'MENUTITLE','UNTITLED','MODSTATE','CLEANSTATE','NEWHINT','AMBIGBAD','NONEFOUND','KEEPBACK','EDNUMBAD','EDIDMISSING','STACKUNIT'}):continue
        data=bytearray();valid=True
        for line in m[0].splitlines():
            if "DB" not in line:continue
            raw=line.split('DB',1)[1]
            if FIELD.sub('',raw).strip(' ,\t'):valid=False;break
            for f in FIELD.finditer(raw):data.extend(f[1].encode('ascii') if f[1] is not None else bytes([int(f[2])]))
        if valid and data and data[-1]==0 and 0 not in data[:-1] and all(b<128 for b in data):result.append((m,bytes(data[:-1])))
    return result

def encode(source):
    boundary=source.index('STACK: DS 128')
    originals=messages(source[:boundary])
    streams=[b for _,b in originals];words=[]
    for i in range(64):
        counts=collections.Counter()
        for stream in streams:
            for span in re.findall(rb'[ -~]+',stream):
                for n in range(3,min(48,len(span))+1):
                    counts.update(span[j:j+n] for j in range(len(span)-n+1))
        scores=[(sum(b.count(w) for b in streams)*(len(w)-1)-len(w)-3,w) for w,k in counts.items() if k>1]
        if not scores:break
        saving,word=max(scores)
        if saving<=0:break
        words.append(word);streams=[b.replace(word,bytes([128+i])) for b in streams]
    # Verify a complete round trip before altering assembly source.
    replacements=[]
    for (m,original),stream in zip(originals,streams):
        decoded=b''.join(words[b-128] if b>=128 else bytes([b]) for b in stream)
        assert decoded==original
        if len(stream)+1>=len(original):continue
        data=bytes([255])+stream+b'\0'
        body=m[1]+':\n'+''.join('        DB '+','.join(map(str,data[i:i+24]))+'\n' for i in range(0,len(data),24))
        replacements.append((m.start(),m.end(),body.rstrip()))
    for a,b,text in reversed(replacements):source=source[:a]+text+source[b:]
    table='MDICT:\n'+''.join(f'        DW MD{i:02d}\n' for i in range(len(words)))
    for i,word in enumerate(words):table+=f'MD{i:02d}: DB '+','.join(map(str,word+b'\0'))+'\n'
    return source.replace('; @fdb-message-dictionary@',table)
