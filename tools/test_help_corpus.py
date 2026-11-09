#!/usr/bin/env python3
"""Check the distributed HELP topics against their disk inventories and index."""
from collections import Counter
import json
from pathlib import Path
import re

from build_help import ROOT, SUBJECTS
from build_utilities_disk import COMPONENTS as UTILITIES
from noah_distribution import COMPONENTS as COMPANION


def check_corpus():
    sources = {p.stem: p.read_text(encoding="ascii") for p in SUBJECTS.glob("*.HLP")}
    system = json.loads((ROOT / "metadata/distribution.json").read_text())
    files = {item["name"] for item in system["system_disk"] if item["status"] == "implemented"}
    programs = {Path(name).stem for name in files | UTILITIES.keys() | COMPANION.keys()
                if name.endswith(".COM")}
    programs.add("HELP")
    subjects = sources.keys() - {"_INDEX"}
    assert programs <= subjects, f"Missing packaged programs: {sorted(programs - subjects)}"

    # The reader interprets links on a single physical line outside literal examples.
    links = []
    sections = {}
    for name, source in sources.items():
        fenced = False
        sections[name] = []
        for number, line in enumerate(source.splitlines(), 1):
            if line.startswith("```"):
                fenced = not fenced
            elif not fenced:
                if line.startswith("## "):
                    sections[name].append("-".join(line[3:].lower().split()))
                targets = re.findall(r"\[[^]\n]+\]\(([^)]*)\)", line)
                assert len(targets) == line.count("]("), (name, number, line)
                for target in targets:
                    file, _, section = target.partition("#")
                    assert file.endswith(".HLP"), (name, number, target)
                    links.append((name, number, file[:-4], section))
        assert not fenced, f"{name}: unterminated example"

    for name, number, target, section in links:
        assert target in sources, (name, number, target)
        if section:
            assert sections[target].count(section) == 1, (name, number, target, section)

    indexed = Counter(target for owner, _, target, _ in links if owner == "_INDEX")
    assert indexed == Counter(subjects), "Each subject must appear exactly once in the index"
    print(f"PASS: {len(programs)} packaged programs, {len(subjects)} indexed subjects, "
          f"{len(links)} topic and section links.")


if __name__ == "__main__":
    check_corpus()
