#!/usr/bin/env python3
"""Export a compiled BetterCP/M catalogue as editable FDF v1 text."""
import argparse
from dataclasses import fields
from pathlib import Path
from tempfile import NamedTemporaryFile

from fdf_v1 import parse, read_fdb, serialize


def decompile(data):
    lines = ["FDF_VERSION 1"]
    for descriptor in read_fdb(data).descriptors:
        item = descriptor.format
        if item is None:
            raise ValueError(f"{descriptor.ident}: unsupported required extension")
        lines.extend(("", "FORMAT", "ID " + item.ident, f'DESCRIPTION "{item.description}"'))
        for field in fields(item):
            if field.name in ("ident", "description"):
                continue
            value = getattr(item, field.name)
            if value is None:
                continue
            if isinstance(value, tuple):
                value = ",".join(map(str, value))
            elif isinstance(value, bool):
                value = "YES" if value else "NO"
            lines.append(f"{field.name.upper()} {value}")
        lines.append("END")
    text = "\n".join(lines) + "\n"
    if serialize(parse(text)) != data:
        raise ValueError("cannot reproduce this binary exactly with FDF v1 text")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        text = decompile(args.source.read_bytes())
        with NamedTemporaryFile(dir=args.output.parent, delete=False) as temp:
            path = Path(temp.name)
        try:
            path.write_text(text, encoding="ascii")
            path.replace(args.output)
        finally:
            path.unlink(missing_ok=True)
    except (OSError, ValueError) as error:
        parser.exit(1, f"FDFDECOMP: {error}\n")


if __name__ == "__main__":
    main()
