"""Generate compact metadata-owned utility quick references (CP/M ASCII)."""
from utility_versions import banner

SCREENS={
 'DUMP':('Hexadecimal File Display','DUMP [options] file [options]',[
 ('/P','Use the paged viewer.'),('/40','Show eight bytes per row.'),
 ('/FROM=hex[H]','Start at this file byte offset.'),('/LEN=hex[H]','Limit displayed bytes.'),
 ('/BARE','Use the original CP/M display.')]),
 'DASM':('Disassembler','DASM [file]',[]),
 'DSYM':('Verified LINK Symbol Conversion','DSYM [DU:]file.LOG [destination-DU:]',[]),
 'TED':('Full-screen Text Editor','TED [DU:]file',[]),
}

def text(name,identity=None):
 purpose,usage,options=SCREENS[name]
 lines=[identity or banner(name),'  - - -',' | '+purpose,' |',' |   Usage: '+usage,'']
 lines+=['   Options:']
 for opt,desc in options:lines.append('     '+opt.ljust(15)+desc)
 if options:lines.append('')
 lines+=['     '+ '/HELP'.ljust(15)+'Display this help.','     '+ '/VER'.ljust(15)+'Display utility identification.']
 assert len(lines)<=23 and max(map(len,lines))<=79
 return '\r\n'.join(lines)+'\r\n'

def source(name,label,identity=None):
 return label+':\n'+''.join("        DB '"+line.replace("'","''")+"',13,10\n" if line else '        DB 13,10\n' for line in text(name,identity).splitlines())+"        DB '$'\n"

def query_source(root):
 q=(root/'src/utilities/common/version.inc').read_text()
 q=q[q.index('\nUV_QUERY:')+1:]
 return q.replace('UV_','UH_').replace('LD C,4','LD C,5').replace("'/ver'","'/help'")
