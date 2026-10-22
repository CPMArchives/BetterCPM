"""Expand the same selected shared UI modules for native and cross CONFIG builds."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

UI=ROOT/'src/utilities/common/ui'


def input_source(*,standard=False,words=False):
    if words and not standard:raise ValueError('word commands require standard profile')
    source=f'UISTD EQU {int(standard)}\nUI_WORDS EQU {int(words)}\n'
    if standard:source+=(UI/'events.inc').read_text()+'\n'
    source+=(UI/'input.inc').read_text()
    if words:source+='\n'+(UI/'wordstar.inc').read_text()
    return source


def controller_source(*,text=True,choice=False):
    if not text and not choice:raise ValueError('select a prompt controller')
    parts=['checks']
    if text:parts.append('prompt')
    if choice:parts.append('choice')
    return '\n'.join((UI/(p+'.inc')).read_text() for p in parts)


def confirmation_source():
    binding=(UI/'confirm.inc').read_text()
    modules=(UI/'events.inc').read_text()+'\n'+controller_source(text=False,choice=True)
    return binding.replace('; @choice-modules@',modules)


def expand_sysgen_ui(source):
    binding=(UI.parent/'sysgeninput.inc').read_text()
    return source.replace('; @sysgen-choice@',binding.replace('; @confirmation@',confirmation_source().replace('UIREAD EQU UY_READ','UIREAD EQU SG_READ')))


def expand_dup_ui(source):
    # Change only DUP's CHOICE reader, retaining its existing echo/layout.
    start=source.index('CHOICE:');end=source.index('DECOUT:',start)
    choice=source[start:end];assert choice.count('CALL KEY')==1
    source=source[:start]+choice.replace('CALL KEY','CALL DU_PICK')+source[end:]
    binding='DP_ASK:\n        XOR A\n        LD (DU_MODE),A\n'+confirmation_source()
    binding=binding.replace('UIREAD EQU UY_READ','UIREAD EQU DU_READ')
    binding=(UI.parent/'dupmenu.inc').read_text()+'\n'+binding
    return source.replace('; @dup-choice@',binding)


def expand_era_ui(source):
    binding=(UI.parent/'erainput.inc').read_text()
    modules=(UI/'events.inc').read_text()+'\n'+controller_source(text=False,choice=True)
    return source.replace('; @era-choice@',binding.replace('; @choice-modules@',modules))


def expand_config_ui(source):
    common=ROOT/'src/utilities/common'
    source=source.replace('; @config-ui@',(common/'configinput.inc').read_text())
    source=source.replace('; @ui-input@',input_source())
    source=source.replace('; @ui-inline@',(common/'ui/inline.inc').read_text())
    before,marker,rest=source.partition('; @legacy-number-begin@')
    if not marker:raise ValueError('CONFIG common input marker missing')
    unused,marker,after=rest.partition('; @legacy-number-end@')
    if not marker:raise ValueError('CONFIG common input end marker missing')
    source=before+after
    # CONFIG retains its existing CHOICE rendering, menu dispatch and one-key
    # approval policy. The editor keeps CI_READ; only choice input uses CC_INPUT.
    start=source.index('CHOICE:');end=source.index('DECOUT:',start)
    choice=source[start:end];assert choice.count('CALL KEY')==1
    source=source[:start]+choice.replace('CALL KEY','CALL CC_PICK')+source[end:]
    binding=(common/'configchoice.inc').read_text()
    modules=(UI/'events.inc').read_text()+'\n'+controller_source(text=False,choice=True).replace('UIREAD','CC_INPUT')
    return source.replace('; @config-choices@',binding.replace('; @choice-modules@',modules))


def expand_ren_ui(source):
    binding=(UI.parent/'reninput.inc').read_text()
    modules=(UI/'events.inc').read_text()+'\n'+controller_source(text=False,choice=True)
    binding=binding.replace('; @choice-modules@',modules).replace('; @append-module@',(UI/'append.inc').read_text())
    return source.replace('; @ren-choice@',binding)


def copy_ui_source():
    binding=(UI.parent/'copyinput.inc').read_text()
    modules=(UI/'events.inc').read_text()+'\n'+controller_source(text=False,choice=True)
    return binding.replace('; @choice-modules@',modules).replace('; @append-module@',(UI/'append.inc').read_text())


def expand_pip_ui(source):
    binding=(UI.parent/'pipinput.inc').read_text()
    confirm=confirmation_source().replace('CALL KEY','CALL PU_KEY')
    return source.replace('; @pip-confirm@',binding.replace('; @confirmation@',confirm))
