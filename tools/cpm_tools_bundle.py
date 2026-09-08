"""Read and verify the pinned general CP/M utility bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def files(root: Path) -> list[tuple[str, bytes]]:
    bundle = root / "third_party/cpm-tools"
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="ascii"))
    result: list[tuple[str, bytes]] = []
    names: set[str] = set()
    local_names = {path.name.upper()
                   for path in (root / "build/utilities").glob("*.COM")}
    for item in manifest["files"]:
        name = item["name"].upper()
        if name in names:
            raise SystemExit(f"duplicate cpm-tools disk filename: {name}")
        if name in local_names:
            raise SystemExit(
                f"cpm-tools filename conflicts with BetterCP/M utility: {name}")
        names.add(name)
        data = (bundle / item["path"]).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != item["sha256"]:
            raise SystemExit(f"cpm-tools snapshot checksum mismatch: {name}")
        result.append((name, data))
    return result
