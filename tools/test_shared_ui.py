#!/usr/bin/env python3
"""Qualify compiled shared UI engines/controllers with hostile caller callbacks."""
from pathlib import Path
import hashlib,json,re
from build_shared_ui_fixtures import ROOT,BUILD,PROFILES,build
from test_bios import Z80
from test_utility_versions import address


class Fixture:
    def __init__(self,profile,keys=b'',validator=None):
        self.profile=profile;self.c=Z80(b'');self.image=(BUILD/(profile+'.bin')).read_bytes()
        self.c.mem[256:256+len(self.image)]=self.image
        self.listing=(BUILD/(profile+'.lst')).read_text();self.keys=list(keys)
        self.trace=[];self.validated=[];self.validator=validator or (lambda value,event:True)
        self.c.port_read=self.io
        if profile!='choice':
            self.c.mem[self.at('EDITLEN')]=0;self.c.mem[self.at('EDITCUR')]=0
            self.c.mem[self.at('EDITSTART')]=0;self.c.mem[self.at('EDITMAX')]=32
        if profile in ('basic','text','combined'):
            self.c.mem[self.at('UP_MODE')]=self.at('UP_CAN')
            self.c.setword(self.at('UP_DPTR'),self.at('DEFAULTBUF'))
            self.c.mem[self.at('UP_DLEN')]=7
        if profile in ('choice','combined'):
            self.c.setword(self.at('UC_LIST'),self.at('CHOICES'))
            self.c.mem[self.at('UC_COUNT')]=2;self.c.mem[self.at('UC_DEF')]=ord('N')

    def at(self,name):
        constant=re.search(r'\b'+re.escape(name)+r'\s+EQU\s+(\d+)\s*$',self.listing,re.M)
        return int(constant[1]) if constant else address(self.listing,name)
    def state(self):
        if self.profile=='choice':return None
        c=self.c;length=c.mem[self.at('EDITLEN')]
        return (bytes(c.mem[self.at('EDITBUF'):self.at('EDITBUF')+length]),
                c.mem[self.at('EDITCUR')],c.mem[self.at('EDITSTART')])
    def io(self,port):
        c=self.c;kind=port&255
        if kind==113:
            assert self.keys,('input exhausted',self.trace[-10:])
            value=self.keys.pop(0);self.trace.append(('key',value))
        elif kind==116:
            event=c.a;value=bytes(c.mem[c.hl:c.hl+c.b]);self.validated.append((event,value))
            good=self.validator(value,event)
            c.carry=not good;self.trace.append(('validate',event,value,good))
            value=91
            c.hl=0xeeee if good else self.at('ERRORMSG')
        else:
            assert kind in (114,115,117,118,119),kind
            msg=None
            if kind in (115,119):msg=bytes(c.mem[c.hl:c.mem.index(0,c.hl)])
            self.trace.append(({114:'draw',115:'message',117:'finish',118:'choice',119:'choice-error'}[kind],self.state(),msg))
            value=77;c.hl=0xeeee
        c.bc=0xbcbc;c.de=0xdede
        if kind!=116:c.hl=0xeeee
        return value
    def call(self,name):
        sp=self.c.sp;self.c.run(self.at(name),limit=300000)
        assert self.c.sp==sp,(name,'stack imbalance')
        assert bytes(self.c.mem[self.at('APP_VALUE'):self.at('APP_VALUE')+8])==b'ORIGINAL'
        if self.profile!='choice':
            assert self.c.mem[self.at('GUARD0')]==90 and self.c.mem[self.at('GUARD1')]==165
        return self.c.a
    def init(self,value=b'',capacity=32):
        if value:self.c.mem[self.at('EDITBUF'):self.at('EDITBUF')+len(value)]=value
        self.c.a=capacity;self.c.b=len(value);self.c.hl=self.at('LABEL')
        return self.call('UE_INIT')
    def feed(self,key):self.c.a=key;return self.call('UE_KEY')
    def prompt(self,policy='UP_CAN'):
        self.c.mem[self.at('UP_MODE')]=self.at(policy)
        result=self.call('UP_RUN')
        value=bytes(self.c.mem[self.c.hl:self.c.hl+self.c.b]) if self.c.hl else None
        return result,value
    def choice(self):
        result=self.call('UC_RUN')
        value=bytes(self.c.mem[self.c.hl:self.c.hl+self.c.b]) if self.c.hl else None
        return result,value


def main():
    for profile in PROFILES:build(profile)
    count=0
    def new(profile='text',keys=b'',validator=None):
        nonlocal count
        count+=1;return Fixture(profile,keys,validator)
    f=new('engine');assert f.init()==f.at('UI_MORE')
    for key in b'Ab c':assert f.feed(key)==f.at('UI_MORE')
    assert f.state()==(b'Ab c',4,0)
    assert f.feed(19)==0 and f.feed(7)==0 and f.state()[0]==b'Ab '
    f.feed(8);f.feed(ord('Z'));assert f.state()==(b'AbZ',3,0)
    assert not f.trace,'event engine performed I/O'
    for key in (13,27,3):
        f=new('engine');f.init()
        assert f.feed(key)==f.at('UI_SEND' if key==13 else 'UI_ABORT')
    for key in (0,9,10,17,21,24,1,6,25):
        f=new('engine');f.init(b'Q')
        assert f.feed(key)==f.at('UI_SKIP') and f.state()==(b'Q',1,0)
    f=new('engine');f.init(b'A');f.feed(127);assert f.state()==(b'',0,0)
    for key in (19,8,7):
        f=new('engine');f.init();assert f.feed(key)==0 and f.state()==(b'',0,0)
    f=new('engine');f.init(b'A');assert f.feed(4)==0 and f.state()==(b'A',1,0)
    for capacity,value in [(0,b''),(1,b'AB'),(5,b'A\tB'),(5,b'A\x7fB'),(5,b'A\xffB')]:
        f=new('engine');old=f.state();assert f.init(value,capacity)==f.at('UI_BAD')
        assert f.c.carry and f.state()[1:]==old[1:]
    f=new('engine');assert f.init(b'A'*255,255)==0
    assert f.feed(ord('B'))==f.at('UI_LIMIT') and f.state()==(b'A'*255,255,0)
    f.feed(8);f.feed(ord('B'));assert f.state()==(b'A'*254+b'B',255,0)
    # Word boundaries use literal spaces; punctuation is part of a word.
    for text,start,key,want in [(b'one  two',8,1,5),(b'one  two',5,1,0),
          (b'one  two',4,1,0),(b'one  two',2,1,0),(b'   ',3,1,0),
          (b'',0,1,0),(b'one  two',0,6,5),(b'one  two',3,6,5),
          (b'one  two',5,6,8),(b'   ',0,6,3),(b'A0:FILE.COM /P',0,6,12)]:
        f=new('words');f.init(text);f.c.mem[f.at('EDITCUR')]=start
        assert f.feed(key)==0 and f.state()==(text,want,0),(text,start,key,f.state())
    f=new('words');f.init(b'old');f.c.mem[f.at('EDITSTART')]=1
    f.feed(25);assert f.state()==(b'',0,0)
    # Full controller outcomes, including an accepted empty string versus cancel.
    for policy,result,value in [('UP_CAN','UI_ABORT',None),('UP_EMPTY','UI_SEND',b''),('UP_DEF','UI_DEF',b'DEFAULT')]:
        f=new(keys=b'\r');f.init();assert f.prompt(policy)==(f.at(result),value)
        assert len([x for x in f.trace if x[0]=='finish'])==1
    f=new(keys=b'\rQ\r');f.init();assert f.prompt('UP_NEED')==(f.at('UI_SEND'),b'Q')
    assert any(x[0]=='message' and x[2]==b'A value is required.' for x in f.trace)
    for key in (b'\x1b',b'\x03'):
        f=new(keys=b'changed'+key);f.init(b'old');assert f.prompt()==(f.at('UI_ABORT'),None)
        assert not f.validated
    # Invalid values retain text/cursor; the correction key is handled once.
    f=new(keys=b'12X\r\x13\x07\r',validator=lambda v,e:v==b'12')
    f.init();assert f.prompt()==(f.at('UI_SEND'),b'12')
    assert [v for e,v in f.validated]==[b'12X',b'12']
    assert [x[1] for x in f.trace if x[0]=='draw'][-1]==(b'12',2,0)
    f=new(keys=b'\rnew\r',validator=lambda v,e:e!=3);f.init()
    assert f.prompt('UP_DEF')==(f.at('UI_SEND'),b'new')
    assert f.validated==[(f.at('UI_DEF'),b'DEFAULT'),(f.at('UI_SEND'),b'new')]
    assert bytes(f.c.mem[f.at('DEFAULTBUF'):f.at('DEFAULTBUF')+7])==b'DEFAULT'
    # Replacing a field clears only the editable value; the default survives.
    f=new(keys=b'xx\x19\r');f.init();assert f.prompt('UP_DEF')==(f.at('UI_DEF'),b'DEFAULT')
    f=new(keys=b'ABA\x01X\x06Y\r');f.init()
    assert f.prompt()==(f.at('UI_SEND'),b'XABAY')
    f=new('basic',keys=b'A\x01\r');f.init()
    assert f.prompt()==(f.at('UI_SEND'),b'A')
    # Limit messages survive unknown keys; a recognized no-op dismisses normally.
    f=new(keys=b'ABCDE\x15\x04\x08Z\r');f.init(capacity=4)
    assert f.prompt()==(f.at('UI_SEND'),b'ABCZ')
    i=next(i for i,x in enumerate(f.trace) if x[0]=='message')
    assert [x[0] for x in f.trace[i:i+5]]==['message','key','key','draw','key']
    for default_len,pointer in [(0,None),(33,None),(7,0)]:
        f=new();f.init();f.c.mem[f.at('UP_DLEN')]=default_len
        if pointer is not None:f.c.setword(f.at('UP_DPTR'),pointer)
        assert f.prompt('UP_DEF')[0]==f.at('UI_BAD') and not f.trace
    f=new();f.init(b'prefilled');assert f.prompt('UP_DEF')[0]==f.at('UI_BAD') and not f.trace
    f=new();f.init();f.c.mem[f.at('DEFAULTBUF')]=1
    assert f.prompt('UP_DEF')[0]==f.at('UI_BAD') and not f.trace
    f=new();f.init();f.c.mem[f.at('UP_MODE')]=255
    assert f.call('UP_RUN')==f.at('UI_BAD') and not f.trace
    f=new(keys=b'\r');f.init(b'prefilled')
    assert f.prompt()==(f.at('UI_SEND'),b'prefilled')
    # Choice-only immediate acceptance, canonical case, defaults and typeahead.
    for keys,result,value in [(b'yZ','UI_SEND',b'Y'),(b'N','UI_SEND',b'N'),
                              (b'\r','UI_DEF',b'N'),(b'\x1b','UI_ABORT',None),
                              (b'\x03','UI_ABORT',None),(b'xy','UI_SEND',b'Y')]:
        f=new('choice',keys=keys);assert f.choice()==(f.at(result),value)
        assert f.keys==([ord('Z')] if keys==b'yZ' else [])
    f=new('choice',keys=b'\r');f.c.mem[f.at('UC_DEF')]=0
    assert f.choice()==(f.at('UI_ABORT'),None)
    f=new('choice',keys=b'yn',validator=lambda v,e:v==b'N')
    assert f.choice()==(f.at('UI_SEND'),b'N') and any(x[0]=='choice-error' for x in f.trace)
    for setting,value in [('UC_COUNT',0),('UC_DEF',ord('X'))]:
        f=new('choice');f.c.mem[f.at(setting)]=value
        assert f.choice()[0]==f.at('UI_BAD') and not f.trace
    f=new('choice');f.c.mem[f.at('CHOICES')]=27
    assert f.choice()[0]==f.at('UI_BAD') and not f.trace
    f=new('choice');f.c.setword(f.at('UC_LIST'),0)
    assert f.choice()[0]==f.at('UI_BAD') and not f.trace
    # Both controllers coexist and share validation/completion without state leakage.
    f=new('combined',keys=b'Q\ry');f.init();assert f.prompt()==(f.at('UI_SEND'),b'Q')
    assert f.choice()==(f.at('UI_SEND'),b'Y')
    metrics={}
    for profile in PROFILES:
        f=Fixture(profile);code=f.at('LIB_END')-f.at('LIB_BEGIN')
        metrics[profile]={'library_bytes':code,'fixture_sha256':hashlib.sha256(f.image).hexdigest()}
        if profile in ('engine','basic','choice'):
            assert 'UW_LEFT:' not in f.listing,profile
        if profile=='choice':
            assert 'EDITBUF:' not in f.listing and 'UE_KEY:' not in f.listing and 'UP_RUN:' not in f.listing
    assert metrics['choice']['library_bytes']<metrics['basic']['library_bytes']
    (BUILD/'results.json').write_text(json.dumps({'status':'PASS','cases':count,'profiles':metrics,
       'scope':'Compiled Z80 with hostile callbacks and caller storage guards; no native display claim.'},indent=2)+'\n')
    print(f'PASS: {count} compiled shared UI engine/prompt/choice/modularity cases')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
