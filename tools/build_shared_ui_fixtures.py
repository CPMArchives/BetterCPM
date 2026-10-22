#!/usr/bin/env python3
"""Build non-distributed CPU fixtures for selected shared UI profiles."""
from pathlib import Path
from build_ccp import assemble
from shared_ui import UI,input_source,controller_source
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/shared-ui'
PROFILES={'engine':(False,False,False),'basic':(False,True,False),
          'words':(True,False,False),'text':(True,True,False),
          'choice':(False,False,True),'combined':(True,True,True)}


def fixture_source(profile):
    words,text,choice=PROFILES[profile]
    editor=profile!='choice'
    source='        ASEG\n        ORG 0100H\n        JP 0\nLIB_BEGIN:\n'
    source+=input_source(standard=True,words=words) if editor else (UI/'events.inc').read_text()
    if text or choice:source+='\n'+controller_source(text=text,choice=choice)
    source+='''
LIB_END:
; Controlled CPU callbacks. Never invoked by the JP 0 entry stub.
UIREAD: IN A,(113)
        RET
UIDRAW: IN A,(114)
        RET
UIMESSAGE: IN A,(115)
        RET
UI_VALID: IN A,(116)
        RET
UI_CLOSE: IN A,(117)
        RET
UC_PAINT: IN A,(118)
        RET
UC_ERROR: IN A,(119)
        RET
UILIMITMSG: DB 'Input limit reached.',0
UI_NEED: DB 'A value is required.',0
ERRORMSG: DB 'Invalid value.',0
LABEL: DB 'Value:',0
DEFAULTBUF: DB 'DEFAULT',0
CHOICES: DB 'yn',0
APP_VALUE: DB 'ORIGINAL'
'''
    if editor:
        source+='''EDITLEN: DB 0
EDITCUR: DB 0
EDITSTART: DB 0
EDITMAX: DB 0
EDITPROMPT: DW 0
GUARD0: DB 90
EDITBUF:
        REPT 255
        DB 0FFH
        ENDM
GUARD1: DB 165
'''
    if text:source+='UP_MODE: DB 0\nUP_DPTR: DW 0\nUP_DLEN: DB 0\n'
    if choice:source+='UC_LIST: DW 0\nUC_COUNT: DB 0\nUC_DEF: DB 0\nUC_VALUE: DB 0\n'
    return source+'        END\n'


def build(profile,assembler=None):
    BUILD.mkdir(parents=True,exist_ok=True);source=fixture_source(profile)
    (BUILD/(profile+'.mac')).write_text(source,encoding='ascii')
    return assemble(assembler or Path.home()/'bin/z80asm',source,
                    BUILD/(profile+'.bin'),BUILD/(profile+'.lst'),0x100)


if __name__=='__main__':
    for profile in PROFILES:print(profile,len(build(profile)))
