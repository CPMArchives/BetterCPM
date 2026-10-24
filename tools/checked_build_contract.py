"""Private artifact identity from verified prepared-profile build inputs."""
from pathlib import Path
import hashlib
import json

from build_profiles import CONTEXT_RELATIVE, read_context


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compatibility_inputs(inputs):
    """Bind runtime admission to resident ABI/loader producers, not every utility/test."""
    source_prefixes = ('src/bdos/', 'src/bios/', 'src/ccp/', 'src/system/', 'src/platform/')
    tool_prefixes = ('tools/build_bdos', 'tools/build_bios', 'tools/build_ccp',
                     'tools/build_rsx', 'tools/build_system', 'tools/checked_',
                     'tools/system_layout', 'tools/build_profiles', 'tools/rsx_container')
    return {name:value for name,value in inputs.items()
            if (name.startswith(source_prefixes) and not name.endswith(('bye.mac','.md')))
            or (name.startswith(tool_prefixes) and name.endswith('.py'))}


def assembly_constants(contract: dict, pack_crc: int = 0) -> str:
    identity = bytes.fromhex(contract['compatibility_id'])
    if len(identity) != 16 or not 0 <= pack_crc <= 65535:
        raise ValueError('invalid checked build constants')
    return (''.join(f'BP_ID{i} EQU {value}\n' for i, value in enumerate(identity))+
            f'BP_PACK_CRC EQU 0{pack_crc:04X}H\n')


def load_contract(root: Path, assembler: Path) -> dict:
    root = root.resolve()
    context, _, _ = read_context(root/CONTEXT_RELATIVE, root/'src/system/layout.inc')
    state = json.loads((root/'profile-state.json').read_text())
    source = state['source']
    if source.get('profile') != context:
        raise ValueError('prepared source identity does not match the selected profile')
    current = {str(p.relative_to(root)): sha(p)
               for folder in ('src', 'tools', 'metadata', 'third_party')
               for p in sorted((root/folder).rglob('*'))
               if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    current = compatibility_inputs(current)
    if current != compatibility_inputs(source['inputs']):
        raise ValueError('prepared source closure changed; prepare a fresh profile')
    assembler_sha = sha(assembler)
    if assembler_sha != source['assembler_sha256']:
        raise ValueError('assembler differs from prepared build identity')
    contract = {
        'schema': 1, 'profile': context['profile'], 'checked': True,
        'private_epoch': context['format_epochs']['private'],
        'carrier_epoch': context['format_epochs']['carrier'],
        'package_epoch': context['format_epochs']['package'],
        'layout_sha256': context['layout_sha256'],
        'profile_flags_sha256': context['flags_sha256'],
        'scratch_bytes': context['capacities']['rsx_scratch_bytes'],
        'command_loader': context['command_loader'],
        'private_inputs': current, 'assembler_sha256': assembler_sha,
    }
    identity = hashlib.sha256(json.dumps(contract, sort_keys=True,
                                        separators=(',', ':')).encode()).hexdigest()[:32]
    return {'contract': contract, 'compatibility_id': identity,
            'source_revision': source['revision'],
            'status': 'checked components; full distribution integration pending'}
