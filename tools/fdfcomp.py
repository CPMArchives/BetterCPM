#!/usr/bin/env python3
"""Compile a BetterCP/M FDF v1 source catalogue into DISK.FDB."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from fdf_v1 import FDFError, compile_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        payload = compile_file(args.source)
        # Verify the host write before the atomic replacement. Semantic output
        # verification is already performed against the deterministic serializer.
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_bytes(payload)
        if temporary.read_bytes() != payload:
            raise FDFError("temporary FDB verification failed")
        temporary.replace(args.output)
    except (FDFError, OSError) as error:
        print(f"FDFCOMP: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"FDFCOMP: {len(payload)} bytes written to {args.output}")


if __name__ == "__main__":
    main()
