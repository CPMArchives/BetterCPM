"""Production phase layout: resident data/I/O, reloadable CLI and codec window."""
import hashlib
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path
from qualify_codec_native import native_text
from build_dasm import validate_native_identifiers

ROOT=Path(__file__).resolve().parents[1]
class Image(bytes):
    pass

def symbols(listing):
    table=re.search(r'Title:\s+Symbol table',listing)
    if not table: raise ValueError('missing assembler symbol table')
    listing=listing[table.end():]
    return {n:int(v,16) for n,v in re.findall(r'\b([A-Z_][A-Z_0-9]*)[ \t]+([0-9a-f]{4})\b',listing,re.I)}

def native_export(text):
    # Native ZSM4 stores 15 significant internal characters. Deterministic local
    # aliases remove collisions without altering the maintained source names.
    names=set(re.findall(r'(?m)^\s*([A-Z_][A-Z_0-9]*)\s*(?::|\s+EQU\b|\s+MACRO\b)',text,re.I))
    aliases={n.upper():'N'+hashlib.sha256(n.upper().encode()).hexdigest()[:11].upper() for n in names if len(n)>15}
    def line(s):
        parts=re.split(r"('[^']*'|\"[^\"]*\"|;.*$)",s)
        return ''.join(p if p.startswith(("'",'"',';')) else re.sub(r'\b[A-Z_][A-Z_0-9]*\b',lambda m:aliases.get(m[0].upper(),m[0]),p,flags=re.I) for p in parts)
    text='\n'.join(map(line,text.splitlines()))+'\n'
    validate_native_identifiers(text)
    text=re.sub(r'(?mi)^\s*ORG\s+(\S+)',lambda m:' CSEG\n .PHASE '+m[1],text,count=1)
    text=re.sub(r'(?mi)^\s*END\s*$', ' .DEPHASE\n END',text)
    return native_text(text)

def assemble(assembler,out,name,text):
    (out/(name+'.mac')).write_text(text)
    result=subprocess.run([str(assembler),'-e32','-sn','-fb','-o'+name+'.bin','-l'+name+'.lst',name+'.mac'],cwd=out,capture_output=True)
    if result.returncode:
        raise ValueError(result.stdout.decode(errors='replace')+'\n'+ '\n'.join(x for x in (out/(name+'.lst')).read_text(errors='replace').splitlines() if x.startswith('=>')))
    return (out/(name+'.bin')).read_bytes(),symbols((out/(name+'.lst')).read_text(errors='replace'))

def partition(flat):
    code=[];data=[];constants=[];pending=[]
    for line in flat.splitlines():
        clean=re.sub(r"'[^']*'|;.*$",lambda m:m[0] if m[0].startswith("'") else '',line).strip()
        if not clean:continue
        if re.match(r'(ORG|END)\b',clean,re.I):continue
        if re.match(r'[A-Z_][A-Z_0-9]*\s+EQU\b',clean,re.I):constants.append(line);continue
        if re.match(r'[A-Z_][A-Z_0-9]*:$',clean,re.I):pending.append(line);continue
        target=data if re.match(r'(?:(?:[A-Z_][A-Z_0-9]*):\s*)?(?:DB|DW|DS)\b',clean,re.I) else code
        target.extend(pending);pending=[];target.append(line)
    data.extend(pending)
    data=[x for x in data if not x.startswith(('NH_OLDSP:','NW_PLANS:'))]
    # Original entry JP is replaced by the module jump table.
    assert code[0].strip()=='JP NH_START';code.pop(0)
    return '\n'.join(constants)+'\n','\n'.join(code)+'\n','NH_OLDSP: DW 0\n'+'\n'.join(data)+'\n'

def production_build(assembler,out,flat_builder):
    out.mkdir(parents=True,exist_ok=True)
    flat_builder(assembler,out/'flat',source_only=True)
    constants,controller,data=partition((out/'flat/noah-flat.mac').read_text())
    lines=constants.splitlines()
    aliases='\n'.join(x for x in lines if re.search(r'EQU\s+[A-Z_]',x,re.I))+'\n'
    constants='\n'.join(x for x in lines if not re.search(r'EQU\s+[A-Z_]',x,re.I))+'\n'
    constant_names=set(re.findall(r'^([A-Z_][A-Z_0-9]*)\s+EQU',constants+aliases,re.M|re.I))
    resident=(ROOT/'src/utilities/common/noahresident.inc').read_text()+'\n'+(ROOT/'src/utilities/common/noahcodec-resident.inc').read_text()
    resident_data=(ROOT/'src/utilities/common/noahresident-data.inc').read_text()
    def boot(window,header):
        h='NR_EXPECT:\n'+''.join(' DB '+','.join(map(str,header[i:i+16]))+'\n' for i in range(0,128,16))
        return ' ORG 100H\n JP NR_START\n'+constants+f'NR_WINDOW EQU {window}\nNR_CONTEXT EQU {window+2048}\n'+resident+data+resident_data+h+'NR_END:\n'+ '\n'.join(x for x in aliases.splitlines() if 'NI_' not in x)+'\n END\n'
    first,rs=assemble(assembler,out,'resident-sizing',boot(0x6000,bytes(128)))
    window=(256+len(first)+127)//128*128
    base,rs=assemble(assembler,out,'resident-sizing',boot(window,bytes(128)))
    rs['NW_PLANS']=0x9000
    rs['NC_ADD_IDS']=0xa800
    imports=''.join(f'{n} EQU {v}\n' for n,v in rs.items() if n not in constant_names and n!='NR_WINDOW')
    cli,cs=assemble(assembler,out,'NHCLI',f' ORG {window}\n'+constants+imports+' JP NH_START\n'+controller+aliases+' END\n')
    prior_cli_size=len(cli)
    plan_address=window+(len(cli)+127)//128*128
    imports=re.sub(r'(?m)^NW_PLANS EQU .*$',f'NW_PLANS EQU {plan_address}',imports)
    imports=re.sub(r'(?m)^NC_ADD_IDS EQU .*$',f'NC_ADD_IDS EQU {plan_address+6144}',imports)
    cli,cs=assemble(assembler,out,'NHCLI',f' ORG {window}\n'+constants+imports+' JP NH_START\n'+controller+aliases+' END\n')
    assert len(cli)==prior_cli_size, "phase address changed code size"
    payloads=[cli];requirements=[plan_address-window+6144+6656];entries=[(window,0,0)]
    for codec,size in [('sq',3524),('usq',1440),('cr',25207),('uncr',26582)]:
        name=codec.upper();head={'SQ':'SQ_SCAN','USQ':'USQ_HEAD','CR':'MC_NOHEAD','UNCR':'UNCR_HEAD'}[name]
        text=f' ORG {window}\n JP {name}_INIT\n JP {head}\n JP {name}_RUN\n'
        text+=''.join((ROOT/'src/codec'/p).read_text()+'\n' for p in ('codec.inc','codec.mac',codec+'.inc',codec+'.mac'))
        text+=' CODEC_CODE\n '+name+'_CODE\nMC_NOHEAD: OR A\n RET\n END\n'
        raw,_=assemble(assembler,out,'NC'+name,text)
        assert len(raw)<=2048,(codec,len(raw))
        payloads.append(raw);requirements.append(2048+size);entries.append((window,window+3,window+6))
        (out/('NC'+name+'.MAC')).write_bytes(native_export(text))
    # ARK supplements the CLI in the inactive writer arena, rather than
    # replacing it for every 128-byte extraction read.
    ark_prefix=''.join((ROOT/'src/archive'/p).read_text()+'\n' for p in ('ark.inc','ark.mac'))
    ark_body=ark_prefix+(ROOT/'src/utilities/common/noahark-phase.inc').read_text()+(ROOT/'src/utilities/common/noahark-decode.inc').read_text()+(ROOT/'src/utilities/common/noahark-huffman.inc').read_text()
    needed=set(re.findall(r'\b[A-Z_][A-Z_0-9]*\b',ark_body,re.I))
    ark_imports=''.join(f'{n} EQU {v}\n' for n,v in (rs|cs).items() if n in needed and n not in constant_names)
    ark_text=f' ORG {plan_address}\n'+constants+ark_imports+ark_body+'\n END\n'
    raw,_=assemble(assembler,out,'NHARK',ark_text)
    assert plan_address+(len(raw)+127)//128*128 <= plan_address+12800
    payloads.append(raw);requirements.append(plan_address-window+(len(raw)+127)//128*128);entries.append((plan_address,0,0))
    (out/'NHARK.MAC').write_bytes(native_export(ark_text))
    build_id=hashlib.sha256(b''.join(payloads)+constants.encode()+resident.encode()+data.encode()+resident_data.encode()).digest()[:8]
    header=bytearray(128);header[:4]=b'NHOV';struct.pack_into('<HH8s',header,4,2,1,build_id)
    header[18]=len(payloads);record=1;companion=bytearray(128)
    for i,(raw,need,entry) in enumerate(zip(payloads,requirements,entries)):
        count=(len(raw)+127)//128
        struct.pack_into('<BBHHHHHHH',header,24+i*16,i+1,1,record,count,len(raw),need,*entry)
        companion.extend(raw+bytes(count*128-len(raw)));record+=count
    struct.pack_into('<H',header,16,record);companion[:128]=header
    struct.pack_into('<I',header,124,zlib.crc32(companion));companion[:128]=header
    image,finalrs=assemble(assembler,out,'NOAH',boot(window,header))
    assert len(image)==len(first)
    assert window+max(requirements)<=0xd501,hex(window+max(requirements))
    (out/'NOAH.COM').write_bytes(image);(out/'NOAH.OVL').write_bytes(companion)
    (out/'NOAH.MAC').write_bytes(native_export(boot(window,header)))
    (out/'NHCLI.MAC').write_bytes(native_export(f' ORG {window}\n'+constants+imports+' JP NH_START\n'+controller+aliases+' END\n'))
    combined=(out/'NOAH.lst').read_text(errors='replace')+'\n'+(out/'NHCLI.lst').read_text(errors='replace')
    (out/'noah.lst').write_text(combined)
    report={'resident_bytes':len(image),'window':window,'codec_context':window+2048,
      'ark_bytes':len(raw),'ark_address':plan_address,'cli_bytes':len(cli),'writer_plans':[plan_address,plan_address+6144],
      'transformed_ids':[plan_address+6144,plan_address+12800],
      'stack':[rs['NH_STACK'],rs['NH_STACK_TOP']],'required_ceilings':[window+n for n in requirements],
      'build_id':build_id.hex(),'companion_sha256':hashlib.sha256(companion).hexdigest()}
    (out/'layout.json').write_text(json.dumps(report,indent=2)+'\n')
    result=Image(image);result.overlay=bytes(companion);result.controller=cli;result.window=window;result.layout=report;return result
