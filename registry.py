#!/usr/bin/env python3
"""Registry = the Anchoring layer. Ground truth of every marker you seeded, its
freshness, and when. JSONL + anchors/<hash>.json, per the family convention.
"""
from __future__ import annotations
import json
from pathlib import Path
from canary import Canary


class Registry:
    def __init__(self, path="registry/anchors.jsonl"):
        self.path = Path(path)
        self.entries: list[dict] = []

    def add(self, c: Canary):
        self.entries.append(c.anchor())

    def save(self, also_split=True):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            for e in self.entries:
                f.write(json.dumps(e) + "\n")
        if also_split:
            adir = self.path.parent / "anchors"
            adir.mkdir(exist_ok=True)
            for e in self.entries:
                h = e["hash"].split(":")[1][:16]
                (adir / f"{h}.json").write_text(json.dumps(e, indent=2))

    def load(self):
        self.entries = []
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                line = line.strip()
                if line:
                    self.entries.append(json.loads(line))
        return self.entries

    def seeded(self):
        return [e for e in self.entries if e["exposure"] == "seeded"]

    def held_out(self):
        return [e for e in self.entries if e["held_out"]]

    def by_value(self):
        return {e["value"]: e for e in self.entries}
