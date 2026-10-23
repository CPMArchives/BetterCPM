from part7_probe_support import *
w=case('boundary')
records=(L['TPA']-256)//128
s=f'''        LD HL,(6)
        LD DE,0{L['TPA']:04X}H
        OR A
        SBC HL,DE
        JR NZ,BAD
        LD HL,(0{L['SYSTEM']+0x90:04X}H)
        OR A
        SBC HL,DE
        JR NZ,BAD
        LD HL,0180H
        LD DE,{(records-1)*128}
LOOP:   LD A,H
        DEC A
        ADD A,A
        LD B,A
        LD A,L
        RLCA
        AND 1
        OR B
        CP (HL)
        JR NZ,BAD
        INC HL
        DEC DE
        LD A,D
        OR E
        JR NZ,LOOP
        LD DE,OK
        JR SHOW
BAD:    LD DE,ERR
SHOW:   LD C,9
        CALL 5
        RET
OK: DB 'FULLRAM FIT PASS',13,10,'$'
ERR: DB 'FULLRAM FIT FAILED',13,10,'$'
'''
code=asm(w,'FIT',s);assert len(code)<=128
payload=code.ljust(128,b'\0')+b''.join(bytes([i&255])*128 for i in range(1,records))
put(w,'FIT.COM',payload);put(w,'OVER.COM',payload+bytes([records&255])*128)
for name,code in [('JPZERO',b'\xc3\0\0'),('FNZERO',b'\x0e\0\xcd\x05\0\x76'),('BIOSWB',b'\x2a\x01\0\xe9')]:put(w,name+'.COM',code)
t=run(w,['STAT MEM','FIT','STAT MEM','OVER','STAT MEM','FIT','JPZERO','FNZERO','BIOSWB','CPX /V','STAT MEM'])
assert t.count('FULLRAM FIT PASS')==2 and 'FULLRAM FIT FAILED' not in t
assert 'FULLRAM FIT' not in t.split('A0>OVER \n',1)[1].split('BetterCP/M Memory Map',1)[0]
m=maps(t);assert len(m)==4 and all(x['maximum']==57344 for x in m)
results['boundary']={'fit_bytes':len(payload),'rejected_bytes':len(payload)+128,'fit_pattern_and_two_boundaries_checked':True,'returns':['RET','JP 0','BDOS Function 0','BIOS WBOOT'],'maps':m};save();print('PASS boundary and warm returns',flush=True)

w=case('stateful')
for name,path in [('HELLO.RSX','build/rsx/HELLO.RSX'),('ECHO.RSX','build/rsx/ECHO.RSX'),('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:put(w,name,(root/path).read_bytes())
t=run(w,['RSX LOAD HELLO','RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','STATTST CHECK','RSX UNLOAD HELLO','STATTST CHECK','RSX LOAD ECHO','STATTST CHECK','RSX LOAD MISSING','STATTST CHECK','RSX LOAD ZPRTC','TIME','RSX UNLOAD ZPRTC','STATTST CHECK','RSX UNLOAD ECHO','RSX UNLOAD STATEFUL','STAT MEM'])
assert t.count('STATEFUL CHECK PASS')==5 and 'FAILED' not in t
assert 'RSX module or profile error' in t
assert maps(t)[-1]['maximum']==57344
results['stateful']={'checks':5,'missing_module_rejected':True,'unloaded_maximum':57344};save();print('PASS stateful services, relocation and failed load',flush=True)

w=case('monitor')
t=run(w,['RSX LOAD ANSISCRN','STAT MEM',(b'RSX LOAD ADM3A\r',b'\x1b[7m \x1b[0m ',25),(b'STAT MEM\r',b'\x1b[7m \x1b[0m ',25),(b'RSX UNLOAD ADM3A\r',b'A0>_ ',25),'RSX UNLOAD ANSISCRN','STAT MEM'])
m=maps(t);assert [x['maximum'] for x in m]==[54784,54272,57344]
assert 'RSX module or profile error' not in t
results['monitor']={'maps':m,'shared_manager_bytes':1024};save();print('PASS screen backend/personality memory and unload',flush=True)
