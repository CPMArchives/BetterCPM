"""Capture selected input records without assigning revisions or changing builds.

An explicit baseline is a comparison reference, not a qualification receipt.
Unsupported components/profiles fail closed; input maps do not certify builds.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os

from component_registry import load, identity, ROOT


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_path(root, relative):
    path = PurePosixPath(relative)
    if (path.is_absolute() or '..' in path.parts or str(path) != relative
            or not path.parts or path.parts[0] not in ('src', 'tools', 'third_party', 'metadata')):
        raise ValueError('invalid selected source path: ' + relative)
    result = root / relative
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('selected source escapes workspace: ' + relative)
    return result


def capture(component, assembler, *, root=ROOT, target='z80pack',
            profile='default', build_mode='cross', toolchain=None, configuration=None, checked_context=None):
    root = Path(root)
    context = None
    context_path = checked_context or os.environ.get('BETTERCPM_BUILD_CONTEXT')
    if context_path:
        from build_profiles import read_context
        try:
            context = read_context(Path(context_path), root/'src/system/layout.inc')[0]
        except (OSError, ValueError) as error:
            raise ValueError('invalid checked context: '+str(error)) from error
        if context['target'] != target:
            raise ValueError('checked context target differs from component target')
        profile = context['profile']
    specification = json.loads((root/'metadata/component-inputs.json').read_text())
    if specification['schema'] != 1:
        raise ValueError('unsupported input-map schema')
    try:
        plan = specification['components'][component]
    except KeyError:
        raise ValueError('selected input map pending: ' + component) from None
    if (target not in plan.get('targets', [plan['target']])
            or (not context and profile != plan['profile'])
            or build_mode not in plan.get('modes', [plan['build_mode']])):
        raise ValueError('unsupported component variant')
    registry = load(root/'metadata/component-registry.json')
    version, revision = identity(component, registry)
    if build_mode == 'native' and not (toolchain or {}).get('linker'):
        raise ValueError('native capture requires an explicit linker binary')
    if not plan['files'] or len(plan['files']) != len(set(plan['files'])):
        raise ValueError('empty or duplicate selected input paths')
    selected_files = plan['files'] + (plan.get('native_files', []) if build_mode == 'native' else [])
    files = {name: digest(source_path(root, name).read_bytes())
             for name in sorted(set(selected_files))}
    # Never hash the whole registry: other component rows are unrelated inputs.
    # The assigned revision is envelope context, outside its own input hash.
    selected = registry['components'][component]
    inputs = {
        'schema': 1, 'component': component,
        'variant': {'target': target, 'profile': profile, 'build_mode': build_mode},
        'identity_fields': {'version': version, 'api_version': selected['api_version']},
        'configuration': plan['configuration'], 'files': files,
        'toolchain': {'assembler_sha256': digest(Path(assembler).read_bytes())},
    }
    if plan.get('registry_fields'):
        inputs['selected_metadata'] = {name: selected[name] for name in plan['registry_fields']}
    if plan.get('identity_dependencies'):
        inputs['identity_dependencies'] = {}
        for key in plan['identity_dependencies']:
            row = registry['components'][key]
            fields = ('version','api_version','display_format','description') if key == component else ('version','revision','api_version','display_format','description')
            inputs['identity_dependencies'][key] = {field:row.get(field) for field in fields}
    if context:
        inputs['configuration'] = dict(inputs['configuration'], checked_profile=context)
    if configuration:
        inputs['configuration'] = dict(inputs['configuration'], invocation=configuration)
    for name, path in sorted((toolchain or {}).items()):
        inputs['toolchain'][name+'_sha256'] = digest(Path(path).read_bytes())
    return {'schema': 1, 'status': 'selected-input-capture',
            'assigned_identity': {'version': version, 'revision': revision},
            'inputs': inputs, 'fingerprint': digest(canonical(inputs))}


def valid(record):
    try:
        return (record['schema'] == 1 and record['inputs']['schema'] == 1
                and isinstance(record['inputs']['component'], str)
                and set(record['inputs']['variant']) == {'target', 'profile', 'build_mode'}
                and all(isinstance(value, str) for value in record['inputs']['variant'].values())
                and record['fingerprint'] == digest(canonical(record['inputs']))
                and type(record['assigned_identity']['revision']) is int
                and record['assigned_identity']['revision'] > 0
                and record['assigned_identity']['version'] == record['inputs']['identity_fields']['version'])
    except (KeyError, TypeError, ValueError):
        return False


def classify(current, baseline=None):
    """Return unknown rather than clean for absent, invalid or mismatched records."""
    if not valid(current) or baseline is None or not valid(baseline):
        return {'state': 'unknown', 'reason': 'missing or invalid input record'}
    for field in ('component', 'variant'):
        if current['inputs'][field] != baseline['inputs'][field]:
            return {'state': 'unknown', 'reason': 'baseline component/variant mismatch'}
    if current['assigned_identity'] != baseline['assigned_identity']:
        return {'state': 'unknown', 'reason': 'baseline assigned identity mismatch'}
    return {'state': 'unchanged' if current['fingerprint'] == baseline['fingerprint'] else 'development',
            'reason': 'selected inputs compared; executable equivalence not evaluated'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component')
    parser.add_argument('--assembler', required=True, type=Path)
    parser.add_argument('--target', default='z80pack')
    parser.add_argument('--profile', default='default')
    parser.add_argument('--build-mode', default='cross')
    parser.add_argument('--toolchain', action='append', default=[], metavar='NAME=PATH')
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    try:
        record = capture(args.component, args.assembler, target=args.target,
                         profile=args.profile, build_mode=args.build_mode,
                         toolchain=dict(item.split('=',1) for item in args.toolchain))
        baseline = json.loads(args.baseline.read_text()) if args.baseline else None
        result = {'record': record, 'comparison': classify(record, baseline)}
    except (ValueError, OSError, KeyError) as error:
        result = {'comparison': {'state': 'unknown', 'reason': str(error)}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result['comparison']['state'] == 'unknown' else 0


if __name__ == '__main__':
    raise SystemExit(main())
