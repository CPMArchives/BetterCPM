"""Expand the same selected shared UI modules for native and cross CONFIG builds."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def expand_config_ui(source):
    common=ROOT/'src/utilities/common'
    source=source.replace('; @config-ui@',(common/'configinput.inc').read_text())
    source=source.replace('; @ui-input@',(common/'ui/input.inc').read_text())
    source=source.replace('; @ui-inline@',(common/'ui/inline.inc').read_text())
    before,marker,rest=source.partition('; @legacy-number-begin@')
    if not marker:raise ValueError('CONFIG common input marker missing')
    unused,marker,after=rest.partition('; @legacy-number-end@')
    if not marker:raise ValueError('CONFIG common input end marker missing')
    return before+after
