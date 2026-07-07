#!/usr/bin/env python3
"""Canary generation + anchor records for the CROSSTALK harness.

CROSSTALK watches the INFERENCE / API membrane: your marker coming back out of a
LIVE hosted model's inference to a THIRD PARTY -- via a shared cache, a retrieval
index the model can read, logs, or plain cross-session bleed. Not published on a
page (that is forward-observers), not baked into the weights (that is surfacing),
not relayed to you by a human (that is hearsay): emitted, live, by the model's
own inference machinery to someone who is not you.

The axis that makes CROSSTALK honest is FRESHNESS. Every canary carries the
moment it was seeded into the model's reach:
  - "seeded"   : placed somewhere the model's inference could pick it up (a
                 retrievable doc, a prompt, a tool result), with a seed time.
  - "held_out" : placed NOWHERE -- a control. If it shows up in a completion,
                 the harness is fabricating, and the run is invalid.

A sighting only counts as a clean INFERENCE-membrane hit if the canary was seeded
AFTER the model's training cutoff. A canary older than the cutoff could be in the
weights -- that is surfacing's membrane, and CROSSTALK gates it out rather than
double-count it. Fresh-in, third-party-out is the signal that it leaked through
live inference, not through training.
"""
from __future__ import annotations
import secrets, hashlib, time
from dataclasses import dataclass

ENTROPY_BITS = 128
HEX_LEN = ENTROPY_BITS // 4       # 32 hex chars, ~zero prior probability


def new_value(bits: int = ENTROPY_BITS) -> str:
    return secrets.token_hex(bits // 8)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


@dataclass
class Canary:
    value: str                         # the high-entropy marker
    exposure: str = "seeded"           # seeded | held_out
    seeded_utc: str | None = None      # when it entered the model's reach (None for held_out)
    channel: str = ""                  # where it was seeded (retrieval doc, prompt, tool result)
    context: str = ""
    kind: str = "canary"

    def __post_init__(self):
        self.canonical = f"{self.kind}|{self.value}|{self.exposure}"
        self.hash = "sha256:" + sha256_hex(self.canonical)

    @property
    def held_out(self) -> bool:
        return self.exposure == "held_out"

    def anchor(self) -> dict:
        return {
            "primitive": self.kind,
            "canonical": self.canonical,
            "hash": self.hash,
            "value": self.value,
            "exposure": self.exposure,
            "held_out": self.held_out,
            "seeded_utc": self.seeded_utc,
            "channel": self.channel,
            "context": self.context,
        }


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def make_seeded(channel="", context="", seeded_utc=None, value=None) -> Canary:
    """A marker placed somewhere the model's inference could reach it."""
    return Canary(value or new_value(), exposure="seeded",
                  seeded_utc=seeded_utc or _now(), channel=channel, context=context)


def make_held_out(context="control") -> Canary:
    """A marker placed NOWHERE -- exists only as a control arm."""
    return Canary(new_value(), exposure="held_out", context=context)
