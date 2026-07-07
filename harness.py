#!/usr/bin/env python3
"""Orchestrator: registry + sightings -> detections -> score -> report.

Lineage-claim language is temporal/structural, not causal: a certified HARD lead
says 'a marker only you seeded, and only AFTER this model's cutoff, appeared in a
completion to someone else' -- so it leaked through live inference, not training.
It is a corroborated LEAD, not proof of the mechanism and not a vendor finding.
"""
from __future__ import annotations
from registry import Registry
from sighting import Sighting
from score import score


def collect_detections(registry: Registry, sightings):
    values = [e["value"] for e in registry.entries]
    by_value = registry.by_value()
    detections = []
    for sidx, s in enumerate(sightings):
        for v in s.canaries_in(values):
            e = by_value[v]
            detections.append({
                "value": v,
                "hash": e["hash"],
                "held_out": e["held_out"],
                "seeded_utc": e["seeded_utc"],
                "recipient": s.recipient,
                "model_cutoff": s.model_cutoff,
                "observed_utc": s.observed_utc,
                "sighting_id": sidx,
            })
    return detections


def run_panel(registry: Registry, sightings):
    detections = collect_detections(registry, sightings)
    return score(detections, registry.entries)


def report(v: dict) -> str:
    lines = [
        "# Crosstalk report", "", v["verdict"], "",
        f"held-out controls run   : {v['held_out_n']}",
        f"control FPR             : {v['control_fpr']}",
        f"weights-gated (pre-cutoff): {len(v['weights_gated'])}",
        f"impossible (pre-seed)   : {len(v['impossible'])}",
        f"base-rate (chance)      : {v['base_rate']:.2e}",
        f"certified leads         : {len(v['certified_leads'])}",
    ]
    for val, corr in sorted(v["certified_leads"].items()):
        lines.append(f"  - {val[:16]}... in {corr} third-party sighting(s)")
    return "\n".join(lines)
