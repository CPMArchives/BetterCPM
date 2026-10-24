"""Plan and record explicit component revisions from verified build artifacts.

This command never edits the registry or compiles. Supply builds made with the
same old revision for planning, then rebuild at the proposed revision to record
acceptance. Records express identity assignment, never execution qualification.
"""
import argparse
import copy
import json
from pathlib import Path

from component_inputs import canonical, digest, valid


def verify(report, artifact):
    """Refuse unsupported captures and bind a report to actual artifact bytes."""
    inputs = report.get('input_record')
    if not valid(inputs):
        raise ValueError('missing or invalid selected input record')
    if report.get('component') != inputs['inputs']['component']:
        raise ValueError('report component differs from input record')
    if report.get('identity') != inputs['assigned_identity']:
        raise ValueError('report identity differs from input record')
    if inputs['inputs']['variant']['build_mode'] not in ('cross','native'):
        raise ValueError('unsupported build mode')
    if report.get('artifact', {}).get('sha256') != digest(artifact):
        raise ValueError('artifact checksum differs from build report')
    if report['artifact'].get('bytes') != len(artifact):
        raise ValueError('artifact size differs from build report')
    if not artifact:
        raise ValueError('empty artifact')
    return inputs


def plan(reference, reference_bytes, candidate, candidate_bytes):
    old = verify(reference, reference_bytes)
    new = verify(candidate, candidate_bytes)
    for field in ('component', 'variant'):
        if old['inputs'][field] != new['inputs'][field]:
            raise ValueError('reference/candidate component or variant differs')
    revision = old['assigned_identity']['revision']
    if new['assigned_identity']['revision'] != revision:
        raise ValueError('candidate must be built using the reference revision')
    if reference.get('display_selection', {}).get('development', False) != candidate.get('display_selection', {}).get('development', False):
        raise ValueError('reference/candidate display state differs; compare at the same display state')
    changed = reference_bytes != candidate_bytes
    return {
        'schema': 1, 'status': 'revision-proposal; not acceptance',
        'component': old['inputs']['component'], 'variant': old['inputs']['variant'],
        'reference_identity': old['assigned_identity'],
        'candidate_identity': new['assigned_identity'],
        'proposed_identity': {'version': new['assigned_identity']['version'],
                              'revision': revision + int(changed)},
        'executable_changed': changed,
        'selected_inputs_changed': old['fingerprint'] != new['fingerprint'],
        'reference_report_sha256': digest(canonical(reference)),
        'candidate_report_sha256': digest(canonical(candidate)),
        'reference_artifact_sha256': digest(reference_bytes),
        'candidate_artifact_sha256': digest(candidate_bytes),
        'candidate_input_fingerprint': new['fingerprint'],
    }


def accept(proposal, reference, reference_bytes, candidate, candidate_bytes,
           final, final_bytes):
    expected = plan(reference, reference_bytes, candidate, candidate_bytes)
    if proposal != expected:
        raise ValueError('proposal differs from verified reference/candidate evidence')
    record = verify(final, final_bytes)
    if record['assigned_identity'] != proposal['proposed_identity']:
        raise ValueError('final identity does not match proposed assignment')
    if (record['inputs']['component'] != proposal['component']
            or record['inputs']['variant'] != proposal['variant']
            or record['fingerprint'] != proposal['candidate_input_fingerprint']):
        raise ValueError('final inputs differ from the reviewed candidate')
    if final.get('display_selection', {}).get('development', False) != candidate.get('display_selection', {}).get('development', False):
        raise ValueError('final display state differs from reviewed candidate')
    if not proposal['executable_changed'] and final_bytes != candidate_bytes:
        raise ValueError('retained revision requires identical final executable')
    return {
        'schema': 1, 'status': 'explicit revision assignment; not qualification',
        'component': proposal['component'], 'variant': proposal['variant'],
        'identity': proposal['proposed_identity'],
        'proposal': copy.deepcopy(proposal),
        'final_report_sha256': digest(canonical(final)),
        'artifact': copy.deepcopy(final['artifact']),
        'input_record': copy.deepcopy(record),
        'provenance': copy.deepcopy(final.get('provenance')),
    }


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('plan', 'accept'))
    for name in ('reference-report', 'reference-artifact', 'candidate-report',
                 'candidate-artifact', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('proposal', 'final-report', 'final-artifact'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--install-baseline', type=Path,
                        help='explicitly update this baseline catalog after verified acceptance')
    args = parser.parse_args()
    if args.operation == 'accept' and any(getattr(args, name) is None for name in
                                         ('proposal', 'final_report', 'final_artifact')):
        parser.error('accept requires --proposal, --final-report and --final-artifact')
    if args.install_baseline and args.operation != 'accept':
        parser.error('--install-baseline is only valid for accept')
    try:
        evidence = (read(args.reference_report), args.reference_artifact.read_bytes(),
                    read(args.candidate_report), args.candidate_artifact.read_bytes())
        if args.operation == 'plan':
            result = plan(*evidence)
        else:
            result = accept(read(args.proposal), *evidence,
                            read(args.final_report), args.final_artifact.read_bytes())
        # Preserve old proposals/acceptance records: no implicit overwrite.
        with args.output.open('x', encoding='utf-8') as output:
            output.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
        if args.install_baseline:
            catalog = read(args.install_baseline) if args.install_baseline.exists() else {'schema':1,'records':{}}
            if catalog['schema'] != 1:raise ValueError('unsupported baseline catalog')
            record=result['input_record'];variant=record['inputs']['variant']
            key='|'.join((result['component'],variant['target'],variant['profile'],variant['build_mode']))
            catalog['records'][key]=record
            temporary=args.install_baseline.with_suffix('.tmp')
            temporary.write_text(json.dumps(catalog,indent=2,sort_keys=True)+'\n')
            temporary.replace(args.install_baseline)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
