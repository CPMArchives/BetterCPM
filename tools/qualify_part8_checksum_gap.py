"""Reproduce the still-open CPX checksum gap with a harmless message change."""
from part7_probe_support import *
w=case('p8-command-checksum-gap')
p=bytearray((root/'build/cpx/HELLO.CPX').read_bytes())
offset=p.index(b'Hello from HELLO.CPX');checksum=int.from_bytes(p[44:46],'little')
p[offset]=ord('J');assert int.from_bytes(p[44:46],'little')==checksum
put(w,'HELLO.CPX',p)
t=run(w,['CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','STAT MEM'])
assert 'Jello from HELLO.CPX' in t
results['p8-command-checksum-gap']={'checksum_field_unchanged':True,'mutated_payload_executed':True,'status':'confirmed open issue'};save()
print('CONFIRMED OPEN ISSUE: CPX payload executes despite stale checksum')
