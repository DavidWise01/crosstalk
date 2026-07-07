#!/usr/bin/env python3
"""Sightings = Detection + Comparison.

A SIGHTING is a completion produced by a hosted model that you have gotten hold
of -- ideally one addressed to someone who is NOT you. Each sighting records the
model, the model's REAL training cutoff, when it was observed, and the recipient:

  recipient of a sighting:
    "third_party" : the completion went to someone else (the strong case --
                    your seeded marker crossed sessions/users).
    "self"        : the completion came back to you (weak -- you may have put
                    the marker in your own context).

Detection is the family's stands-alone rule: a canary counts only when it is not
flanked by [A-Za-z0-9_-] (a substring is not a marker).
"""
from __future__ import annotations
import re
from dataclasses import dataclass


def scan_text(text: str, values):
    """Return the canary values that stand ALONE in text (word-boundary)."""
    found = []
    for v in values:
        if not v:
            continue
        pat = r"(?<![A-Za-z0-9_-])" + re.escape(v) + r"(?![A-Za-z0-9_-])"
        if re.search(pat, text):
            found.append(v)
    return found


@dataclass
class Sighting:
    text: str                       # the model's completion
    model: str = "some-model"       # which model produced it
    model_cutoff: str | None = None # the model's REAL training cutoff (self-reported by vendor)
    observed_utc: str | None = None # when you observed the completion
    recipient: str = "third_party"  # third_party | self
    source: str = ""

    def canaries_in(self, values):
        return scan_text(self.text, values)
