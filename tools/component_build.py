"""Reusable artifact-record wrapper for standalone component builders."""
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
import json
import subprocess
from component_inputs import ROOT, capture, digest
from component_development import select

DISPLAY = ContextVar('component_build_display', default=None)


def selected_display(component):
    context = DISPLAY.get()
    if context and context[0] == component:
        return context[1]
    return select(component, Path.home()/'bin/z80asm', root=ROOT)


def recorded_build(component):
    def decorate(build):
        @wraps(build)
        def wrapped(assembler, destination, *, target='z80pack', identity_state='auto'):
            assembler=Path(assembler).resolve();destination=Path(destination)
            destination.mkdir(parents=True,exist_ok=True)
            name=component.split(':')[1]
            report_path=destination/(name+'-build-report.json')
            report_path.unlink(missing_ok=True)
            # Preserve existing checked build paths without pretending a complete map.
            def inputs():
                try:return capture(component,assembler,root=ROOT,target=target),None
                except (OSError,ValueError,KeyError) as error:return None,str(error)
            before,error=inputs();display=select(component,assembler,root=ROOT,target=target,mode=identity_state)
            token=DISPLAY.set((component,display))
            try:
                image=build(assembler,destination)
                after,after_error=inputs()
                if before!=after or error!=after_error or display!=select(component,assembler,root=ROOT,target=target,mode=identity_state):
                    raise RuntimeError(name+' inputs/display changed during assembly')
                if (destination/(name+'.COM')).read_bytes()!=image:
                    raise RuntimeError(name+' output differs from assembler result')
                from component_registry import identity
                version,revision=identity(component)
                provenance=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,text=True)
                report={'schema':1,'component':component,'identity':{'version':version,'revision':revision},
                    'artifact':{'name':name+'.COM','bytes':len(image),'sha256':digest(image)},
                    'input_record':before,'input_error':error,'display_selection':display,
                    'provenance':{'repository_commit':provenance.stdout.strip() if provenance.returncode==0 else None},
                    'status':'build record; execution qualification not asserted'}
                report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
                return image
            finally:DISPLAY.reset(token)
        return wrapped
    return decorate
