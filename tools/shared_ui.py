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
    return source.replace('; @sysgen-choice@',binding.replace('; @confirmation@',confirmation_source()))


def expand_dup_ui(source):
    return source.replace('; @dup-choice@','DP_ASK:\n'+confirmation_source())


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
    return before+after
