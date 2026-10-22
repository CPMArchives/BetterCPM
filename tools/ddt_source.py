"""Syntax-aware 8080-to-Z80 transcription for the separate DDT adaptation."""
import re


def comment_split(line):
    quoted=False;i=0
    while i<len(line):
        c=line[i]
        if c=="'":
            if quoted and i+1<len(line) and line[i+1]=="'":i+=2;continue
            quoted=not quoted
        if c==';' and not quoted:return line[:i],line[i:]
        i+=1
    return line,''


def fields(code):
    code=code.rstrip()
    if not code.strip():return '', '', ''
    label=''
    m=re.match(r'^([^\s:]+):\s*(.*)$',code)
    if m:label,code=m.groups()
    elif not code[0].isspace():
        parts=code.split(None,1)
        label=parts[0];code=parts[1] if len(parts)>1 else ''
    parts=code.split(None,1)
    return label,parts[0].upper() if parts else '',parts[1] if len(parts)>1 else ''


def rename(code,mapping):
    # Replace identifiers only outside literals, including strings containing ';'.
    parts=re.split(r"('(?:[^']|'')*')",code)
    for i in range(0,len(parts),2):
        parts[i]=re.sub(r'\b[01][01$]*B\b',lambda m:m[0].replace('$',''),parts[i])
        parts[i]=re.sub(r'[A-Za-z_][A-Za-z_0-9$]*',lambda m:mapping.get(m[0].upper(),m[0]),parts[i])
    return ''.join(parts)


def translate(text, private=False):
    mapping={}
    if private:
        for line in text.splitlines():
            label,op,arg=fields(comment_split(line)[0])
            if label and label.upper() not in mapping:mapping[label.upper()]=f'A{len(mapping):04d}'
    out=[]
    reg=lambda s: '(HL)' if s.strip().upper()=='M' else s.strip().upper()
    pair=lambda s: {'B':'BC','D':'DE','H':'HL','SP':'SP','PSW':'AF'}[s.strip().upper()]
    simple={'XCHG':('EX','DE,HL'),'XTHL':('EX','(SP),HL'),'PCHL':('JP','(HL)'),
            'SPHL':('LD','SP,HL'),'RAL':('RLA',''),'RAR':('RRA',''),
            'RLC':('RLCA',''),'RRC':('RRCA',''),'CMA':('CPL',''),
            'CMC':('CCF',''),'STC':('SCF',''),'HLT':('HALT','')}
    alu={'ADD':'ADD','ADC':'ADC','SUB':'SUB','SBB':'SBC','ANA':'AND','XRA':'XOR','ORA':'OR','CMP':'CP',
         'ADI':'ADD','ACI':'ADC','SUI':'SUB','SBI':'SBC','ANI':'AND','XRI':'XOR','ORI':'OR','CPI':'CP'}
    conditions={'NZ':'NZ','Z':'Z','NC':'NC','C':'C','PO':'PO','PE':'PE','P':'P','M':'M'}
    for line in text.splitlines():
        code,comment=comment_split(line)
        code=rename(code,mapping);label,op,arg=fields(code)
        if op in simple:op,arg=simple[op]
        elif op=='MOV':a,b=arg.split(',');op,arg='LD',f'{reg(a)},{reg(b)}'
        elif op=='MVI':
            a,b=arg.split(',',1);b='0+'+b if b.lstrip().startswith('(') else b
            op,arg='LD',f'{reg(a)},{b}'
        elif op=='LXI':
            a,b=arg.split(',',1);b='0+'+b if b.lstrip().startswith('(') else b
            op,arg='LD',f'{pair(a)},{b}'
        elif op in ('INR','DCR'):op,arg=('INC' if op=='INR' else 'DEC'),reg(arg)
        elif op in ('INX','DCX'):op,arg=('INC' if op=='INX' else 'DEC'),pair(arg)
        elif op=='DAD':op,arg='ADD','HL,'+pair(arg)
        elif op in ('LDAX','STAX'):
            op,arg='LD',f'A,({pair(arg)})' if op=='LDAX' else f'({pair(arg)}),A'
        elif op in ('PUSH','POP'):arg=pair(arg)
        elif op in ('LDA','STA','LHLD','SHLD'):
            value='A' if op in ('LDA','STA') else 'HL'
            arg=f'{value},({arg})' if op in ('LDA','LHLD') else f'({arg}),{value}'
            op='LD'
        elif op in alu:
            old=op;op=alu[op];arg=reg(arg) if old in ('ADD','ADC','SUB','SBB','ANA','XRA','ORA','CMP') else arg
            if old not in ('ADD','ADC','SUB','SBB','ANA','XRA','ORA','CMP') and arg.lstrip().startswith('('):arg='0+'+arg
            if op in ('ADD','ADC','SBC'):arg='A,'+arg
        elif op=='JMP':op='JP'
        elif op.startswith('J') and op[1:] in conditions:arg=conditions[op[1:]]+','+arg;op='JP'
        elif op.startswith('C') and op[1:] in conditions:arg=conditions[op[1:]]+','+arg;op='CALL'
        elif op.startswith('R') and op[1:] in conditions:arg=conditions[op[1:]];op='RET'
        elif op=='RST':arg=f'({arg})*8'
        elif op in ('IN','OUT'):arg=f'A,({arg})' if op=='IN' else f'({arg}),A'
        if label:
            prefix=label+(' ' if op=='EQU' else ': ')
        else:prefix='        '
        out.append(prefix+(op+(' '+arg if arg else '') if op else '')+(' '+comment if comment else ''))
    return '\n'.join(out)+'\n'


def zero_storage(source):
    # Both assemblers emit explicit zero bytes, including alignment gaps.
    out=[]
    for line in source.splitlines():
        code,comment=comment_split(line);label,op,arg=fields(code)
        if op=='DS':
            if label:out.append(label+':')
            out+=['        REPT '+arg,'        DB 0','        ENDM']
        else:out.append(line)
    return '\n'.join(out)+'\n'
