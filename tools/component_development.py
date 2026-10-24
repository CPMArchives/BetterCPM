"""Select visible development state from explicit per-variant input baselines."""
import json
from pathlib import Path
from component_inputs import ROOT, capture, classify, canonical, digest


def select(component, assembler, *, root=ROOT, target='z80pack', mode='auto', build_mode='cross', toolchain=None, configuration=None, checked_context=None):
    import os
    target=os.environ.get('BETTERCPM_IDENTITY_TARGET',target)
    mode=os.environ.get('BETTERCPM_IDENTITY_STATE',mode)
    assembler=Path(os.environ.get('BETTERCPM_BUILD_ASSEMBLER',str(assembler)))
    if os.environ.get('BETTERCPM_BUILD_CONFIGURATION'):
        configuration=json.loads(os.environ['BETTERCPM_BUILD_CONFIGURATION'])
    if os.environ.get('BETTERCPM_NATIVE_LINKER'):
        build_mode='native';toolchain={'linker':Path(os.environ['BETTERCPM_NATIVE_LINKER'])}
    if mode not in ('auto', 'assigned', 'development'):
        raise ValueError('unsupported identity-state mode')
    if mode != 'auto':
        return {'mode': mode, 'development': mode == 'development',
                'reason': 'explicit build display selection; not qualification',
                'baseline_sha256': None}
    try:
        current = capture(component, assembler, root=root, target=target,build_mode=build_mode,toolchain=toolchain,configuration=configuration,checked_context=checked_context)
        catalog = json.loads((Path(root)/'metadata/component-baselines.json').read_text())
        if catalog['schema'] != 1:
            raise ValueError('unsupported component baseline schema')
        variant = current['inputs']['variant']
        key = '|'.join((component, variant['target'], variant['profile'], variant['build_mode']))
        baseline = catalog['records'].get(key)
        comparison = classify(current, baseline)
        return {'mode': mode, 'development': comparison['state'] != 'unchanged',
                'reason': comparison['reason'], 'input_state': comparison['state'],
                'baseline_sha256': digest(canonical(baseline)) if baseline else None}
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {'mode': mode, 'development': True, 'input_state': 'unknown',
                'reason': str(error), 'baseline_sha256': None}
