from part7_probe_support import *
import struct
foreign=Path(os.environ['P8_FOREIGN_RSX']);old=Path(os.environ['P8_OLD_RSX'])
pack=(root/'build/system/R3PACK.RSX').read_bytes()
echo=(root/'build/rsx/ECHO.RSX').read_bytes();m=int.from_bytes(echo[30:32],'little');rec=m+12
badpub=bytearray(echo);badpub[rec+4]=1
badclass=bytearray(echo);badclass[rec+3]=2
dup=bytearray(echo);dup[rec:rec]=dup[rec:rec+20];dup[m+7]+=1;struct.pack_into('<H',dup,m+8,int.from_bytes(dup[m+8:m+10],'little')+20)
cases={'foreign-private':('FDF',(foreign/'FDF.RSX').read_bytes()),'old-v2':('ECHO',(old/'ECHO.RSX').read_bytes()),'public-nonzero':('ECHO',badpub),'unknown-class':('ECHO',badclass),'duplicate-binding':('ECHO',dup)}
for label,(module,bad) in cases.items():
 w=case('p8-'+label)
 for name in ('STATEFUL.RSX','ECHO.RSX','FDF.RSX'):put(w,name,(root/'build/rsx'/name).read_bytes())
 put(w,'STATTST.COM',(root/'build/utilities/STATTST.COM').read_bytes());put(w,'BAD.RSX',bad,'b');put(w,'GOOD.RSX',(root/'build/rsx'/f'{module}.RSX').read_bytes(),'b')
 t=run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','STATTST CHECK','STAT MEM',f'PIP {module}.RSX=B:BAD.RSX',f'RSX LOAD {module}','STATTST CHECK','STAT MEM',f'PIP {module}.RSX=B:GOOD.RSX',f'RSX LOAD {module}','STATTST CHECK',f'RSX UNLOAD {module}','RSX UNLOAD STATEFUL','STAT MEM'])
 assert t.count('RSX module or profile error')==1,label
 assert t.count('STATEFUL CHECK PASS')==3 and 'FAILED' not in t,label
 maps_=maps(t);assert maps_[0]['maximum']==maps_[1]['maximum'] and maps_[-1]['maximum']==57344
 results['p8-'+label]={'rejection':True,'stateful_checks':3,'final_tpa':57344};save();print('PASS '+label,flush=True)
for action in ('load','remove'):
 w=case('p8-retained-'+action)
 for name in ('STATEFUL.RSX','ECHO.RSX','HELLO.RSX'):put(w,name,(root/'build/rsx'/name).read_bytes())
 put(w,'STATTST.COM',(root/'build/utilities/STATTST.COM').read_bytes());put(w,'BAD.RSX',(foreign/'STATEFUL.RSX').read_bytes(),'b');put(w,'GOOD.RSX',(root/'build/rsx/STATEFUL.RSX').read_bytes(),'b')
 before=['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE']+(['RSX LOAD HELLO'] if action=='remove' else [])
 operation='RSX LOAD ECHO' if action=='load' else 'RSX UNLOAD HELLO'
 after=['RSX UNLOAD ECHO'] if action=='load' else []
 t=run(w,before+['PIP STATEFUL.RSX=B:BAD.RSX',operation,'STATTST CHECK','PIP STATEFUL.RSX=B:GOOD.RSX',operation,'STATTST CHECK']+after+['RSX UNLOAD STATEFUL','STAT MEM'])
 assert t.count('RSX module or profile error')==1 and t.count('STATEFUL CHECK PASS')==2 and 'FAILED' not in t
 assert maps(t)[-1]['maximum']==57344
 results['p8-retained-'+action]={'foreign_retained_carrier_rejected':True,'stateful_checks':2,'recovery':True};save();print('PASS retained '+action,flush=True)
w=case('p8-public-cross-profile');put(w,'HELLO.RSX',(foreign/'HELLO.RSX').read_bytes())
put(w,'CALL198.COM',asm(w,'call198',' LD C,198\n CALL 5\n RET'))
t=run(w,['RSX LOAD HELLO','CALL198','RSX UNLOAD HELLO','STAT MEM'])
assert 'Hello from HELLO.RSX' in t and 'RSX module or profile error' not in t and maps(t)[-1]['maximum']==57344
results['p8-public-cross-profile']={'service_executed':True,'unloaded_tpa':57344};save();print('PASS public cross-profile service execution',flush=True)
