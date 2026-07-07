#!/usr/bin/env python3
"""Verify-first self-test. Plant markers, simulate model completions, and prove
the harness (1) certifies a FRESH (post-cutoff) marker seen in a third-party
completion, corroborated by how many carry it; (2) does NOT manufacture leads on
the held-out arm; (3) GATES a pre-cutoff marker as weights-explainable (that is
surfacing's membrane, not this one); (4) ignores a self-addressed completion;
(5) gates an impossible pre-seed sighting; (6) refuses a run with no control arm;
(7) only matches a marker that stands ALONE. No network, no keys.
"""
from __future__ import annotations
from canary import make_seeded, make_held_out
from registry import Registry
from sighting import Sighting, scan_text
from harness import run_panel

fails = 0
def check(cond, msg):
    global fails
    print(("ok  · " if cond else "FAIL· ") + msg)
    fails += 0 if cond else 1


CUTOFF = "2026-01-01"
FRESH = "2026-03-01T00:00:00Z"     # seeded AFTER cutoff -> cannot be in weights
STALE = "2025-06-01T00:00:00Z"     # seeded BEFORE cutoff -> could be in weights


def completion(canaries, recipient="third_party", cutoff=CUTOFF, observed="2026-04-01T00:00:00Z", source="x"):
    body = "user B's answer contained: " + " ".join(c.value for c in canaries) + " (verbatim)."
    return Sighting(text=body, model="hosted-model", model_cutoff=cutoff,
                    observed_utc=observed, recipient=recipient, source=source)


# 1. Clean: FRESH markers seen in third-party completions after seeding; held-out never appear.
reg = Registry()
fresh = [make_seeded(channel=f"doc{i}", seeded_utc=FRESH) for i in range(3)]
held = [make_held_out() for _ in range(3)]
for c in fresh + held:
    reg.add(c)
sightings = [
    completion([fresh[0]], source="user B"),
    completion([fresh[0]], source="user C"),   # fresh[0] corroborated by TWO third-party sightings
    completion([fresh[1]], source="user D"),
    completion([fresh[2]], source="user E"),
]
v = run_panel(reg, sightings)
check(v["control_fpr"] == 0, f"held-out FPR is 0 (got {v['control_fpr']})")
check(len(v["certified_leads"]) == 3, f"all 3 fresh markers certified (got {len(v['certified_leads'])})")
check(v["certified_leads"].get(fresh[0].value) == 2, "fresh[0] corroborated by 2 third-party sightings")
check("CLEAN" in v["verdict"], "verdict CLEAN when controls pass")
check(v["base_rate"] < 1e-30, f"chance base-rate negligible ({v['base_rate']:.1e})")

# 2. FRESHNESS gate: a STALE (pre-cutoff) marker -> could be in the weights -> surfacing's job.
reg2 = Registry()
stale = make_seeded(channel="old-doc", seeded_utc=STALE)
reg2.add(stale); reg2.add(make_held_out())
v2 = run_panel(reg2, [completion([stale], source="user F")])
check(stale.value in v2["weights_gated"], "pre-cutoff marker is WEIGHTS-gated (could be training)")
check(len(v2["certified_leads"]) == 0, "weights-explainable hit is not certified as inference leakage")

# 3. Recipient gate: a marker seen only in a SELF-addressed completion is not cross-session.
reg3 = Registry()
f3 = make_seeded(seeded_utc=FRESH)
reg3.add(f3); reg3.add(make_held_out())
v3 = run_panel(reg3, [completion([f3], recipient="self")])
check(len(v3["certified_leads"]) == 0, "self-addressed completion is not certified")

# 4. Impossible gate: observed BEFORE the marker was seeded.
reg4 = Registry()
f4 = make_seeded(seeded_utc=FRESH)
reg4.add(f4); reg4.add(make_held_out())
v4 = run_panel(reg4, [completion([f4], observed="2026-02-01T00:00:00Z")])
check(f4.value in v4["impossible"], "pre-seed sighting is IMPOSSIBLE (gated)")

# 5. Fabrication: a held-out marker turns up in a completion -> control catches it.
reg5 = Registry()
f5 = make_seeded(seeded_utc=FRESH); h5 = make_held_out()
reg5.add(f5); reg5.add(h5)
v5 = run_panel(reg5, [completion([f5]), completion([h5], source="fabricated")])
check(bool(v5["control_fpr"]) and v5["control_fpr"] > 0, f"fabricated sighting spikes held-out FPR ({v5['control_fpr']})")
check("INVALID" in v5["verdict"], "fabricated/contaminated pipeline -> verdict INVALID")
check(len(v5["certified_leads"]) == 0, "invalid run certifies nothing")

# 6. Performative guard: no held-out arm -> INVALID.
reg6 = Registry()
f6 = make_seeded(seeded_utc=FRESH); reg6.add(f6)
v6 = run_panel(reg6, [completion([f6])])
check("INVALID" in v6["verdict"], "no held-out arm -> INVALID (performative guard)")

# 7. Word-boundary.
val = make_seeded().value
check(scan_text(val, [val]) == [val], "a marker standing alone is detected")
check(scan_text("z" + val + "z", [val]) == [], "a marker inside a larger token is NOT detected")

print("\n" + ("SOME CHECKS FAILED" if fails else "all crosstalk-harness checks passed"))
raise SystemExit(1 if fails else 0)
