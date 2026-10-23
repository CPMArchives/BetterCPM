from part7_probe_support import *
pack=(root/'build/system/R3PACK.RSX').read_bytes()
foreign=Path(os.environ['P7_FOREIGN_PACK']).read_bytes()
cases={'foreign':foreign,'truncated':pack[:-128],'header':bytes([pack[0]^1])+pack[1:],'missing':b''}
for slot in (5,10,12,13,14):
 b=bytearray(pack);b[512+slot*1024+511]^=1;cases['slot'+str(slot)]=bytes(b)
for label,bad in cases.items():
 w=case('fault-'+label)
 for name,path in [('ECHO.RSX','build/rsx/ECHO.RSX'),('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:put(w,name,(root/path).read_bytes())
 put(w,'BAD.RSX',bad,'b');put(w,'GOOD.RSX',pack,'b')
 t=run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','STATTST CHECK','STAT MEM',('ERA R3PACK.RSX' if label=='missing' else 'PIP R3PACK.RSX=B:BAD.RSX'),'RSX LOAD ECHO','STATTST CHECK','RSX','STAT MEM','PIP R3PACK.RSX=B:GOOD.RSX','RSX LOAD ECHO','STATTST CHECK','RSX UNLOAD ECHO','RSX UNLOAD STATEFUL','STAT MEM'])
 assert t.count('STATEFUL CHECK PASS')==3 and 'FAILED' not in t,label
 assert t.count('RSX module or profile error')==1,(label,t)
 m=maps(t);assert m[0]['maximum']==m[1]['maximum'] and m[-1]['maximum']==57344,label
 results[label]={'stateful_checks':3,'failed_load_preserved_tpa':m[0]['maximum'],'final_maximum':m[-1]['maximum'],'recovery_and_later_load':True};save();print('PASS active-profile '+label,flush=True)
