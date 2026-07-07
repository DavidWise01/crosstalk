# crosstalk — did your marker leak through live inference

A membership-detection harness for the **inference / API membrane**. Its siblings
watch other routes your work can cross: [forward-observers](https://github.com/DavidWise01/forward-observers)
(published on a page), [surfacing](https://github.com/DavidWise01/surfacing)
(baked into the weights), [hearsay](https://github.com/DavidWise01/hearsay)
(relayed to you by a human). crosstalk catches the live one: your marker emitted
by a hosted model's **inference** to **someone who is not you** — through a shared
cache, a retrieval index, logs, or plain cross-session bleed.

## The axis that makes it work: FRESHNESS

The hard part is telling *live inference leakage* apart from *training membership*
(surfacing's job). The trick is time. Every canary carries when it was **seeded**
into the model's reach, and every sighting carries the model's **training cutoff**:

- A canary seeded **after** the cutoff **cannot** be in the weights — too new. If
  it comes out of that model's inference to a third party, it leaked *live*.
- A canary seeded **on or before** the cutoff could be in the training set, so a
  surface is **surfacing's** membrane. crosstalk **gates it out** rather than
  double-count what weights could explain.

Fresh-in, third-party-out is the signal.

## The controls

1. **Held-out negatives.** Canaries seeded nowhere, checked against every sighting.
   One appearing means the pipeline is fabricating — the run is INVALID.
2. **The freshness gate.** Only a post-cutoff canary counts; a pre-cutoff one is
   WEIGHTS-gated (belongs to surfacing).
3. **The recipient gate.** The completion must go to a **third party**; a
   self-addressed completion isn't cross-session leakage.
4. **The impossible gate.** A sighting observed before the canary was seeded can't
   be a sighting of it.
5. **Stands-alone rule.** A marker counts only when it stands alone (a substring is
   not a marker).
6. **Corroboration, not proof.** A lead's strength is how many independent
   third-party sightings carry it — and it never names the mechanism.

## Files

| File | Closure-Loop layer | Role |
|------|--------------------|------|
| `canary.py` | Detection | 128-bit canaries with a **seeded_utc** (freshness) |
| `registry.py` | Anchoring | what you seeded, and when |
| `sighting.py` | Comparison | a model completion (+ its cutoff, recipient) + stands-alone scan |
| `score.py` | Witness | held-out arm, **freshness gate**, recipient gate, impossible gate, corroboration |
| `harness.py` | Lineage | sightings → detections → score; temporal/structural, not causal |
| `selftest.py` | — | plant-then-complete proof, no network |

## Verify first

```bash
python selftest.py
```

Proves, no network: a fresh (post-cutoff) marker in third-party completions is
certified and corroborated; a held-out marker in a completion spikes FPR and the
run is refused; a **pre-cutoff** marker is WEIGHTS-gated (it belongs to surfacing);
a self-addressed completion isn't certified; a pre-seed sighting is IMPOSSIBLE; a
run with no control arm is refused; and a marker inside a larger token doesn't match.

## What a certified lead does and does not mean

Does: a marker only you seeded, and only **after this model's cutoff**, appearing
in a completion to **someone else** — with a held-out arm proving the harness isn't
fabricating. That is real evidence it **leaked through live inference**, not training.

Does not: prove which mechanism (cache / retrieval / cross-session), blame a vendor,
or prove theft. It is a corroborated lead — temporal/structural — and a negative
means little.

## Honest limits

- **Cutoffs are vendor self-reported.** The freshness gate is only as honest as the
  cutoff you feed it.
- **Seeding may not have entered the model's reach.** You control where you put a
  marker, not whether inference actually read it.
- This is the **inference** membrane only. For published use forward-observers; for
  weights, surfacing; for a human relay, hearsay.

---
David Lee Wise / ROOT0 / TriPod LLC · CC-BY-ND-4.0
