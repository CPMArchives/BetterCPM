from part7_probe_support import *
w=case('direct-no-workspace')
for name,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:put(w,name,(root/path).read_bytes())
requests=[(0,b'STATEFUL',0,0,1),(3,b'STATEFUL',0,0,1),(1,b'STATEFUL',0,0,0),(2,b'MISSING ',0,0,0),(1,b'ECHO    ',0,0x7000,-1),(1,b'ECHO    ',0x6000,0x7000,-1),(1,b'ECHO    ',0x5000,0xffff,-1)]
s=''
for i,(_,_,_,_,expected) in enumerate(requests):
 s+=f' LD DE,REQ{i}\n LD C,177\n CALL 5\n'
 s+=(' OR A\n JP Z,BAD\n' if expected==-1 else f' CP {expected}\n JP NZ,BAD\n')
s+=' LD DE,OK\n JR SHOW\nBAD: LD DE,ERR\nSHOW: LD C,9\n CALL 5\n RET\n'
s+="OK: DB 'DIRECT AND BOUNDS PASS',13,10,'$'\nERR: DB 'DIRECT AND BOUNDS FAILED',13,10,'$'\n"
for i,(op,name,low,high,_) in enumerate(requests):
 s+=f"REQ{i}: DB 2,{op},0,0\n DB '{name.decode()}'\n DW 0,{low},{high}\n"
put(w,'DIRECT.COM',asm(w,'direct',s))
t=run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','ERA R3PACK.RSX','DIRECT','STATTST CHECK','STAT MEM'])
assert 'DIRECT AND BOUNDS PASS' in t and 'FAILED' not in t and 'STATEFUL CHECK PASS' in t
results['direct']={'pack_absent':True,'zero_workspace_operations':4,'bad_workspace_rejections':3,'stateful_check':True};save()
print('PASS direct/no-op calls with zero workspace and absent pack; malformed workspace',flush=True)
for off,label in [(0,'payload'),(1000,'identity')]:
 w=case('bad-reloader-'+label)
 p=w/'disks/drivea.dsk';b=bytearray(p.read_bytes());record=60+off//128;track,within=divmod(record,fmt.spt)
 at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128+off%128;b[at]^=1;p.write_bytes(b)
 raw=session(sim,w/'disks',[],w/'halt.bin',initial_prompt=b'!')
 assert b'A0>' not in raw
 results['bad-reloader-'+label]={'halt_marker_seen':True,'no_command_prompt':True};save()
 print('PASS cold reloader rejection: '+label,flush=True)
