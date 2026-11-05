#!/usr/bin/env python3
"""Build only a new documentation candidate or explicit authoring review snapshot."""
# SPDX-License-Identifier: GPL-2.0-or-later
import argparse
import json
from pathlib import Path
from release_documentation import assemble


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--revision')
    choice.add_argument('--preview', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.repository, args.output, revision=args.revision, preview=args.preview), indent=2))


if __name__ == '__main__':
    main()
