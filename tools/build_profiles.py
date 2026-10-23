"""Validated RAM build profiles and generated, source-preserving layout inputs.

Select a prepared context before importing layout-dependent builders. The
environment variable is inherited by subprocesses; each process verifies the
context against the canonical source in its own workspace before using it.
These inputs do not yet implement the checked loader/carrier migration.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

CONTEXT_ENV = 'BETTERCPM_BUILD_CONTEXT'
CONTEXT_RELATIVE = Path('build/profile/context.json')
EQUATE = re.compile(r'^(LY_\w+)(\s+EQU\s+)0([0-9A-F]+)H', re.MULTILINE)
RELOCATED = frozenset('LY_SYS LY_BDOS LY_EXT LY_DISK LY_BIOS LY_FILE LY_TAB '
    'LY_RSTA LY_DIR LY_BUF LY_RSX LY_CFG LY_CPX LY_RSSEL LY_LIMIT LY_RAMEND '
    'LY_HIST LY_TPA'.split())
FIXED = frozenset('LY_LOAD LY_RLCAP LY_STKL LY_STKT LY_SECTS LY_TOPRSV'.split())


@dataclass(frozen=True)
class BuildProfile:
    name: str
    target: str
    delta: int
    ram_end: int
    top_reserved: int
    checked: bool = True
    private_epoch: int = 2
    carrier_epoch: int = 2
    package_epoch: int = 2
    rsx_scratch_bytes: int = 4096
    command_loader: str = 'header-stream-v1'


PROFILES = {
    'cpmsim-legacy-checked': BuildProfile('cpmsim-legacy-checked', 'z80pack',
                                       0, 0xF400, 0xC00),
    'cpmsim-fullram': BuildProfile('cpmsim-fullram', 'z80pack',
                                 0xC00, 0x10000, 0),
}


def select_profile(name: str, target: str) -> BuildProfile:
    try:
        profile = PROFILES[name]
    except KeyError:
        raise ValueError(f'unknown build profile: {name}') from None
    if target != profile.target:
        raise ValueError(f'{name} requires --target {profile.target}; got {target}')
    return profile


def symbols(text: str) -> dict:
    pairs = [(m[1], int(m[3], 16)) for m in EQUATE.finditer(text)]
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError('duplicate numeric layout symbol')
    return result


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def profile_inputs(profile: BuildProfile, source: Path) -> tuple:
    """Return a manifest and generated includes without modifying source."""
    if select_profile(profile.name, profile.target) != profile:
        raise ValueError('profile differs from its supported definition')
    original = source.read_text(encoding='ascii')
    base = symbols(original)
    if set(base) != RELOCATED | FIXED:
        raise ValueError('numeric layout symbols changed; classify their profile behavior')
    if (base['LY_RAMEND'], base['LY_LIMIT'], base['LY_TOPRSV']) != (0xF400, 0xF400, 0xC00):
        raise ValueError('canonical RAM ceiling changed; reassess supported profiles')
    selected = {name: value + (profile.delta if name in RELOCATED else 0)
                for name, value in base.items()}
    selected['LY_TOPRSV'] = profile.top_reserved
    if (selected['LY_LIMIT'] != profile.ram_end or
            selected['LY_RAMEND'] != profile.ram_end or
            profile.ram_end + profile.top_reserved != 0x10000 or
            selected['LY_BUF'] + 1024 != profile.ram_end or
            selected['LY_CFG'] != selected['LY_BUF'] or
            selected['LY_TPA'] + 3 != selected['LY_HIST']):
        raise ValueError('inconsistent profile memory boundaries')
    ordered = ['LY_TPA', 'LY_HIST', 'LY_SYS', 'LY_BDOS', 'LY_EXT', 'LY_DISK',
               'LY_BIOS', 'LY_FILE', 'LY_TAB', 'LY_RSTA', 'LY_DIR', 'LY_BUF', 'LY_LIMIT']
    if any(selected[a] >= selected[b] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('profile resident regions overlap or are reversed')
    for name, value in selected.items():
        maximum = 0x10000 if name in ('LY_LIMIT', 'LY_RAMEND') else 0xFFFF
        if not 0 <= value <= maximum:
            raise ValueError(f'{name} is outside its address/count range')
    layout = EQUATE.sub(lambda m: f'{m[1]}{m[2]}0{selected[m[1]]:04X}H', original)
    layout = f'; Generated build profile: {profile.name}\n' + layout
    flags = (f'; Generated build profile: {profile.name}\n'
             f'BP_CHECKED EQU {int(profile.checked)}\n'
             f'BP_PRIVATE_EPOCH EQU {profile.private_epoch}\n'
             f'BP_CARRIER_EPOCH EQU {profile.carrier_epoch}\n'
             f'BP_PACKAGE_EPOCH EQU {profile.package_epoch}\n'
             f'BP_RSX_SCRATCH EQU 0{profile.rsx_scratch_bytes:04X}H\n'
             '; Checked resident service addresses; implementations must be integrated separately.\n'
             'LY_CCRC EQU LY_FILE-32\n'
             'LY_CBACK EQU LY_FILE-2\n'
             'LY_CCMP EQU LY_BIOS-26\n'
             'LY_CID EQU LY_BIOS-16\n')
    manifest = {
        'schema': 1, 'profile': profile.name, 'target': profile.target,
        'memory_mode': 'ram', 'checked': profile.checked,
        'status': 'layout-preparation; checked distribution migration pending',
        'delta': profile.delta, 'ram_end': profile.ram_end,
        'top_reserved': profile.top_reserved,
        'format_epochs': {'private': profile.private_epoch,
                          'carrier': profile.carrier_epoch, 'package': profile.package_epoch},
        'command_loader': profile.command_loader,
        'capacities': {'rsx_scratch_bytes': profile.rsx_scratch_bytes,
                       'maximum_com_bytes': (selected['LY_TPA'] - 0x100) // 128 * 128,
                       'bdos_bytes': selected['LY_EXT'] - selected['LY_BDOS'],
                       'module_buffer_bytes': profile.ram_end - selected['LY_BUF']},
        'canonical_layout_sha256': digest(source.read_bytes()),
        'layout_sha256': digest(layout.encode('ascii')),
        'flags_sha256': digest(flags.encode('ascii')),
        'symbols': selected,
    }
    return manifest, layout, flags


def write_context(profile: BuildProfile, source: Path) -> Path:
    root = source.resolve().parents[2]
    context = root / CONTEXT_RELATIVE
    manifest, layout, flags = profile_inputs(profile, source)
    context.parent.mkdir(parents=True, exist_ok=False)
    (context.parent / 'layout.inc').write_text(layout, encoding='ascii')
    (context.parent / 'profile.inc').write_text(flags, encoding='ascii')
    context.write_text(json.dumps(manifest, indent=2) + '\n', encoding='ascii')
    return context


def read_context(context: Path, source: Path) -> tuple:
    context = context.resolve()
    if context != source.resolve().parents[2] / CONTEXT_RELATIVE:
        raise ValueError('build context belongs to a different source workspace')
    manifest = json.loads(context.read_text(encoding='ascii'))
    profile = select_profile(manifest['profile'], manifest['target'])
    expected, layout, flags = profile_inputs(profile, source)
    if manifest != expected:
        raise ValueError('build context differs from current source/profile inputs; prepare again')
    if ((context.parent / 'layout.inc').read_text(encoding='ascii') != layout or
            (context.parent / 'profile.inc').read_text(encoding='ascii') != flags):
        raise ValueError('generated profile inputs changed; prepare again')
    return manifest, layout, flags


def selected_context(source: Path) -> tuple | None:
    context = os.environ.get(CONTEXT_ENV)
    return read_context(Path(context), source) if context else None


def context_environment(context: Path, source: Path) -> dict:
    read_context(context, source)
    environment = dict(os.environ)
    environment[CONTEXT_ENV] = str(context.resolve())
    return environment


def workspace(work: Path, target: str, profile: BuildProfile | None = None) -> Path:
    if profile is None:
        return work / target
    select_profile(profile.name, target)
    return work / 'profiles' / profile.name / target
