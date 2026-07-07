#!/usr/bin/env python3
"""Scoring + controls. The held-out arm and -- uniquely -- the FRESHNESS GATE do
the epistemic work.

A DETECTION is one (canary, sighting) pair where the canary stands alone in the
completion. Each is tiered:

  HARD      : a canary seeded AFTER the model's cutoff, appearing in a THIRD-PARTY
              completion, observed after seeding -> it could not be in the weights
              (too new) and did not come back to you -> live inference leakage.
              A strong LEAD.
  WEIGHTS   : the canary was seeded on/before the model's cutoff -> it could be in
              the training set, so a surface is surfacing's membrane, not this one.
              Gated out (don't double-count what weights could explain).
  SELF      : the completion came back to YOU -> not cross-session leakage.
  IMPOSSIBLE: observed before the canary was seeded -> provenance/harness error.
  CONTROL   : a HELD-OUT canary in any completion -> fabrication -> run INVALID.

Certification: HARD leads certify only if a held-out control arm ran and its
false-positive rate is 0. A HARD lead is a LEAD -- it says the marker leaked
through live inference, not which mechanism (cache / retrieval / cross-session),
and never blames a vendor. Corroboration = distinct third-party sightings.
"""
from __future__ import annotations
from canary import HEX_LEN


def _before(a, b):
    if not a or not b:
        return False
    return a[:19] < b[:19]


def _fresh(seeded_utc, cutoff):
    """Seeded strictly after the model's training cutoff -> cannot be in weights."""
    if not seeded_utc or not cutoff:
        return False           # can't confirm freshness -> not fresh (conservative)
    return seeded_utc[:10] > cutoff[:10]


def tier(d):
    if d["held_out"]:
        return "CONTROL"
    if d["recipient"] == "self":
        return "SELF"
    if _before(d["observed_utc"], d["seeded_utc"]):
        return "IMPOSSIBLE"
    if not _fresh(d["seeded_utc"], d["model_cutoff"]):
        return "WEIGHTS"       # explainable by training membership -> surfacing's job
    return "HARD"


def score(detections, registry_entries):
    held_total = [e for e in registry_entries if e["held_out"]]
    n_held = len(held_total)

    for d in detections:
        d["tier"] = tier(d)

    control_hits = {d["value"] for d in detections if d["tier"] == "CONTROL"}
    fpr = (len(control_hits) / n_held) if n_held else None

    hard = {}
    for d in detections:
        if d["tier"] == "HARD":
            hard.setdefault(d["value"], set()).add(d.get("sighting_id", id(d)))
    weights_gated = {d["value"] for d in detections if d["tier"] == "WEIGHTS"}
    impossible = {d["value"] for d in detections if d["tier"] == "IMPOSSIBLE"}

    checks = max(1, len(detections))
    base_rate = checks * (2 ** -(HEX_LEN * 4))

    if n_held == 0:
        verdict = "INVALID: no held-out control arm was run (performative)"
        certified = {}
    elif fpr and fpr > 0:
        verdict = (f"INVALID: control FPR={fpr:.2f} -- the harness is manufacturing "
                   f"sightings; no lead is trustworthy")
        certified = {}
    else:
        certified = hard
        verdict = (f"CLEAN: control FPR=0 over {n_held} held-out; "
                   f"{len(certified)} inference-leak lead(s) -- corroboration, not proof")

    return {
        "verdict": verdict,
        "certified_leads": {v: len(s) for v, s in certified.items()},
        "hard": {v: len(s) for v, s in hard.items()},
        "weights_gated": sorted(weights_gated),
        "impossible": sorted(impossible),
        "control_hits": sorted(control_hits),
        "control_fpr": fpr,
        "held_out_n": n_held,
        "base_rate": base_rate,
    }
