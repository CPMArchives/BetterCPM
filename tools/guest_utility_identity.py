"""Prepare project-owned guest command identities from the component registry.

The pinned upstream patches remain intact. Only their two identification text
occurrences are generated here; the assembler and selected-input fingerprints
are recorded rather than forcing a released display state.
"""
import re
from pathlib import Path

from component_inputs import ROOT, capture, digest
from component_development import select
from component_identity import title
from component_registry import identity

GUESTS = {'R': 'r', 'W': 'w', 'MOUNT': 'mount'}


def prepare(source, assembler):
    records = {}
    for name, stem in GUESTS.items():
        owner = 'utility:'+name
        inputs = capture(owner, assembler, root=ROOT, target='z80pack')
        display = select(owner, assembler, root=ROOT, target='z80pack')
        version, revision = identity(owner)
        text = title(name, version, revision, development=display['development'])
        path = Path(source)/'cpmtools'/(stem+'.asm')
        original = path.read_text()
        pattern = re.escape(name)+r' 1\.0 \([0-9]+-dev\)'
        prepared, count = re.subn(pattern, text, original)
        if count != 2:
            raise ValueError('unexpected pinned guest identification layout: '+name)
        path.write_text(prepared)
        records[owner] = {'schema':1, 'component':owner,
            'identity':inputs['assigned_identity'], 'input_record':inputs,
            'display_selection':display,
            'status':'prepared guest identity; execution qualification not asserted'}
    return records


def finish(records, source, assembler):
    for owner, record in records.items():
        name = owner.split(':')[1]
        if (capture(owner, assembler, root=ROOT, target='z80pack') != record['input_record']
                or select(owner, assembler, root=ROOT, target='z80pack') != record['display_selection']):
            raise ValueError('guest identity inputs changed during build: '+name)
        data = (Path(source)/'cpmtools'/(GUESTS[name]+'.com')).read_bytes()
        record['artifact'] = {'name':name+'.COM','bytes':len(data),'sha256':digest(data)}
        record['status'] = 'guarded guest build record; execution qualification not asserted'
    return records
