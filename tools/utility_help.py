"""Generate compact metadata-owned utility quick references (CP/M ASCII)."""
from utility_versions import banner

SCREENS={
 'NDR':('Named Directory Management','NDR [name DU: | operation]',[
 ('name DU:', 'Assign a name (1..8 letters/digits).'),
 ('/DEL name', 'Delete a name before reassignment.'),
 ('/CLEAR', 'Discard all live names.'),
 ('/LOAD [DU:]file', 'Replace names from a saved .NDR set.'),
 ('/SAVE [DU:]file', 'Save names to a new .NDR file.'),
 ('', 'List names: up to four columns, eight per column.')]),
 'STAT':('System and File Statistics','STAT [drive: | filespec | request]',[
 ('', 'No operand: report logged-in drives only.'),
 ('d:', 'Query free space on that drive directly.'),
 ('', 'Warm boot resets the logged-in drive set.'),
 ('VAL:', 'Show syntax and valid device assignments.'),
 ('DSK:', 'Show disk parameters for logged drives.'),
 ('USR:', 'Show user areas on the selected drive.'),
 ('DEV:', 'Show logical device assignments.'),
 ('d:=R/O', 'Make a drive temporarily read-only.'),
 ('file attribute', 'Prefix attributes with a dollar sign.'),
 ('R/O | R/W', 'Set file write protection.'),
 ('SYS | DIR', 'Set directory visibility.'),
 ('S', 'Show logical record count.'),
 ('CON:=CRT:', 'Assign a logical device (example).')]),
 'CPX':('Command Processor Extension Management','CPX LIST | LOAD name[.CPX] | UNLOAD name[.CPX]',[]),
 'RSX':('Resident Extension Management','RSX LIST | LOAD [DU:]name[.RSX] | UNLOAD name[.RSX]',[]),
 'DUP':('Disk Utilities','DUP [operation]',[
 ('/FORMAT d:', 'Format a physical drive.'),('/COPY s: d:', 'Copy a physical disk.'),
 ('/CHECK d:', 'Read-check a physical disk.'),('', 'No operation opens the interactive menu.')]),
 'SYSGEN':('System Installation','SYSGEN [source destination]',[
 ('A: B:', 'Install system tracks onto prepared media.'),
 ('package B:', 'Install a checked system package.'),('A: package', 'Export system tracks to a package.'),
 ('', 'No operands opens the interactive menu.')]),
 'TIME':('Date and Time','TIME [options]',[
 ('/PROVIDER', 'Identify the active clock provider.'),
 ('/SET LL HH HR MN SC', 'Set day bytes and BCD time (hex).')]),
 'ERA':('File Erasure','ERA filespec [options]',[('/Y','Approve ordinary confirmations.'),('/Q','Suppress routine output.'),('/C','Confirm each file.'),('/R','Allow selected read-only files.'),('/D','Destructively erase selected files.')]),
 'REN':('File Renaming','REN newname=oldname [options]',[('/C','Confirm each rename.'),('/Y','Approve ordinary confirmations.'),('/N /DRY','Preview without renaming.'),('/P','Allow selected protected files.'),('/Q /QQ','Suppress routine / most normal output.')]),
 'TYPE':('Text File Display','TYPE filespec [options]',[('/P','Page output and navigate files.'),('/7','Strip high bits.'),('/T','Expand tabs to eight-column stops.'),('/CTL','Show controls in caret notation.')]),
 'ED':('Text Editor','ED [drive:]filename.typ',[]),
 'SUBMIT':('Batch Command Processing','SUBMIT filename [arguments]',[]),
 'XSUB':('Batch Console Input','XSUB [DU:]',[]),
 'DIR':('Directory Listing','DIR [filespec] [options]',[('/WHEREIS','Locate names across drives/users.'),('/A','Display attributes.'),('/P','Page output.'),('/Z /Z=K','Show allocated KiB.'),('/Z=S /Z=E','Show records / directory entries.'),('/C=1|2|4','Select display columns.'),('/S=N|T|Z|U','Sort by name/type/size/directory order.')]),
 'USER':('User Area Selection','USER number',[]),
 'CLS':('Clear Screen','CLS',[]),
 'VER':('Version Information','VER [/BANNER]',[]),
 'COPY':('File Copying','COPY source destination [options]',[]),
 'MOVE':('File Moving','MOVE source destination [options]',[]),
 'DLINK':('Checked LINK Launcher','DLINK [LINK command tail]',[]),
 'ADMTST':('ADM-3A Console Test','ADMTST',[]),
 'VT52TST':('VT52 Console Test','VT52TST',[]),
 'ANSITST':('ANSI Console Test','ANSITST',[]),
 'SYSBUILD':('Native System Build','SYSBUILD',[]),
 'RESPACK':('Resident Image Packaging','RESPACK',[]),
 'RLMBUILD':('Relocation Map Build','RLMBUILD',[]),
 'PATH':('Numeric Command Search Path','PATH [location ... | /A location | /D location | /DEFAULT]',[
 ('location', 'Numeric DU or NAME:; current DU is always first.'),
 ('NAME:', 'Resolve once through the loaded NDR provider.'),
 ('/A /ADD DU', 'Append one entry to the list.'),
 ('/D /DEL DU', 'Delete one entry; at least one must remain.'),
 ('/DEFAULT','Restore current DU followed by A0:.')]),
 'WARM':('Warm Boot','WARM',[]),
 'DDT':('Debugger','DDT [file]',[]),
 'PIP':('File and Device Transfer','PIP [destination=source[,source...]]',[
 ('', 'No operands opens the interactive prompt.'),
 ('', 'Transfer parameters follow files in brackets.'),
 ('', 'Sources: B[-]:*.COM or [B0,C[1-3]]:*.COM.'),
 ('', 'Selectors: one destination DU; at most 64 files.'),
 ('', 'Duplicate names reject selection before copying.')]),
 'DUMP':('Hexadecimal File Display','DUMP [options] file [options]',[
 ('/P','Use the paged viewer.'),('/40','Show eight bytes per row.'),
 ('/FROM=hex[H]','Start at this file byte offset.'),('/LEN=hex[H]','Limit displayed bytes.'),
 ('/BARE','Use the original CP/M display.')]),
 'DASM':('Disassembler','DASM [file]',[]),
 'DSYM':('Verified LINK Symbol Conversion','DSYM [DU:]file.LOG [destination-DU:]',[]),
 'TED':('Full-screen Text Editor','TED [DU:]file',[]),
}

# Resident operations intentionally expose a smaller contract than the COMs.
# Share formatting and query semantics, not unsupported transient options.
RESIDENT_SCREENS={
 'DIR':('Directory Listing','DIR [filespec]',[]),
 'ERA':('File Erasure','ERA filespec',[]),
 'TYPE':('Text File Display','TYPE filespec [/P]',[('/P','Page output.')]),
 'REN':('File Renaming','REN newname=filespec',[]),
 'CLS':('Clear Screen','CLS',[]),
 'USER':('User Area Selection (0..31)','USER number',[]),
 'VER':('Version Information','VER [/V]',[('/V','Show subsystem versions.')]),
 'COPY':('File Copying','COPY source destination | destination=source [/O]',[('/O','Replace existing destination files.')]),
 'MOVE':('File Moving','MOVE source destination | destination=source [/O]',[('/O','Replace existing destination files.')]),
}

def text(name,identity=None,resident=False):
 purpose,usage,options=(RESIDENT_SCREENS if resident else SCREENS)[name]
 lines=[identity or banner(name),'  - - -',' | '+purpose,' |',' |   Usage: '+usage,'']
 lines+=['   Options:']
 # PATH's short operands fit the same label field as its query switches.
 query_width=15
 option_width=query_width if name=='PATH' else 21
 for opt,desc in options:lines.append('     '+opt.ljust(option_width)+desc)
 if options:lines.append('')
 lines+=['     '+ '/H /HELP'.ljust(query_width)+'Display this help.','     '+ '/VER'.ljust(query_width)+'Display utility identification.']
 assert len(lines)<=23 and max(map(len,lines))<=79
 return '\r\n'.join(lines)+'\r\n'

def source(name,label,identity=None):
 return label+':\n'+''.join("        DB '"+line.replace("'","''")+"',13,10\n" if line else '        DB 13,10\n' for line in text(name,identity).splitlines())+"        DB '$'\n"

def resident_identification(name):
 """Standard identification using the resident command's own title and purpose."""
 purpose=RESIDENT_SCREENS[name][0]
 return (banner(name,True)+'\r\n  - - -\r\n | BetterCP/M Utilities\r\n | '+purpose+'\r\n')

def resident_parts():
 """Inline variable parts; share framing without relocated pointer tables."""
 def literal(value):
  tokens=[]
  for part in value.splitlines(keepends=True):
   body=part.rstrip('\r\n')
   if body:tokens.append("'"+body.replace("'","''")+"'")
   if part.endswith('\r\n'):tokens.extend(('13','10'))
  return '        DB '+','.join(tokens+["'$'"])+ '\n'
 records={}
 for name,(purpose,usage,options) in RESIDENT_SCREENS.items():
  option_text=''.join('     '+o.ljust(21)+d+'\r\n' for o,d in options)
  if options:option_text+='\r\n'
  records[name]=''.join(literal(v) for v in (purpose,usage,option_text))
 return records

def query_source(root):
 """One bounded matcher accepts exact /HELP and /H; no extra query stack."""
 q=(root/'src/utilities/common/version.inc').read_text()
 q=q[q.index('\nUV_QUERY:')+1:]
 q=q.replace('UV_','UH_').replace('LD C,4','LD C,5').replace("'/ver'","'/help'")
 old='        DEC C\n        JR NZ,UH_MATCH'
 new=('        DEC C\n        LD A,C\n        CP 3\n        JR NZ,UH_LONG\n'
      '        LD A,B\n        OR A\n        JR Z,UH_FOUND\n'
      '        LD A,(HL)\n        CP \' \'\n        JR Z,UH_FOUND\n'
      '        CP 9\n        JR Z,UH_FOUND\nUH_LONG:\n'
      '        LD A,C\n        OR A\n        JR NZ,UH_MATCH')
 assert old in q
 return q.replace(old,new)
