"""One formatter for numeric revision identities and transitional legacy text.

Numeric formatting is ready for explicit migration; existing callers request
legacy forms until their changed executable revisions are assigned.
"""
import re


def revision_text(revision, *, development=False):
    if type(revision) is not int or revision < 1:
        raise ValueError('revision must be a positive integer')
    if type(development) is not bool:
        raise ValueError('development must be explicitly true or false')
    return f'{revision:03d}' + ('-dev' if development else '')


def title(name, version, revision, *, style='numeric', development=False,
          resident=False, checked_id=None):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Z][A-Z0-9]*', name):
        raise ValueError('invalid component display name')
    if not isinstance(version, str) or not re.fullmatch(r'[0-9]+\.[0-9]+', version):
        raise ValueError('invalid implementation version')
    number = revision_text(revision, development=development)
    if style == 'numeric':
        return f'{name} {version} ({number})'
    if style not in ('legacy', 'legacy-common'):
        raise ValueError('unknown identity display style')
    if development:
        raise ValueError('legacy display cannot represent development state')
    if style == 'legacy':
        if resident or checked_id is not None:
            raise ValueError('legacy standalone title has no resident/checked decoration')
        return f'{name} {version} (Build {number})'
    detail = f'Resident, RCP Build {number}' if resident else f'Build {number}'
    if checked_id is not None and not resident:
        if not isinstance(checked_id, str) or not re.fullmatch(r'[0-9a-f]{32}', checked_id):
            raise ValueError('invalid checked compatibility identifier')
        detail = 'Checked ' + checked_id[:8]
    return f'BetterCP/M {name} {version} ({detail})'


def identification(name, version, revision, description, *, style='numeric',
                   development=False):
    if (not isinstance(description, str) or not description.isascii()
            or any(c in description for c in '\r\n\x00$')):
        raise ValueError('description must be a safe single ASCII line')
    return (title(name, version, revision, style=style, development=development)
            + '\r\n  - - -\r\n | BetterCP/M Utilities\r\n | '
            + description + '\r\n')
