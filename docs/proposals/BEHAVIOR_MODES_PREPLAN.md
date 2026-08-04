# Pre-plan: behavior modes and behavior bundles (system-wide dials)

Status: PARKED — idea only, not a captured request. No tranche exists.
When picked up, route through `dr-change-orchestrator` starting at
`dr-capture-request` with the operator's words below as the request.

Origin: operator conversation, 2026-08-04 (monitor session, branch
`claude/handover-defect-audit-33pv3d`), during the rung-4/5 delivery
program. Deliberately deferred: "After this project is complete, we need
to run tests. But before that, what would it take..."

## The operator's words (verbatim)

> what would it take create system wide dials. Like with top-p, top-k,
> max token, frequency penality and so on. The purpose not to replace
> config, but to change the functioning of DeepReason: argument mode to
> map out arguments, explore mode to brainstorm, creative mode to map
> possibilities and so on. All the elements exist, it's just the frozen
> surface limits how the system behaves. I was thinking maybe use
> explore mode to generate content, then critical mode to run the full
> harness. The idea is not just to change behaviour, but create
> behaviour bundles.

## The core insight

A "mode" is a named recipe over knobs that already exist. Sampling
dials (temperature, top-p, completion tokens) live in the provider
profile; behavior knobs (active spawn rules, cycle budgets, criticism
budgets, capability opt-ins, shallow vs full engine) live in config.
Nothing frozen constrains the VALUES of those knobs — the frozen
surfaces guard the bookkeeping (event application, digests, manifest
schemas, replay formats). A mode layer therefore composes existing
settings above an untouched harness. No frozen surface needs to move.

## Sketched modes

- **Explore (brainstorm):** hot sampling, generous spawn rules,
  criticism at minimum, large token budget. Wide net, keep everything.
- **Argument (map arguments):** budgets force every conjecture to
  receive criticism cycles; debt rules used hard; the record reads as
  claims-with-objections.
- **Creative (map possibilities):** hot sampling plus
  disconnection/succession rules favored, so runs branch rather than
  converge.
- **Critical (the judge):** cold sampling, full harness, full
  criticism, replay validation — essentially today's defaults.

## Behavior bundles (the pipeline idea)

"Explore generates, critical judges" is conjecture then refutation.
The chaining machinery already exists and is legal: run explore mode as
its own run root, harvest survivors, attach them as frozen evidence
(`--attach`, dossier digest) to a critical-mode run — or chain via
amendment epochs. Each stage is its own run root with its own typed
record; nothing append-only is violated. A bundle is a ladder script,
same shape as existing experiment ladders:

    setup -> explore run -> harvest survivors -> critical run -> audit

## What it would take (priced)

1. **Preset layer** — small tranche. A named-mode table resolving to
   config + provider-profile values at setup time. No frozen contact.
2. **Mode stamp in the typed record** — one rung-4-shaped tranche.
   NOT a manifest field (frozen, hard no). Follow the rung-4 template
   exactly: optional typed payload on the event record
   (`module-fingerprints.v1` precedent, tranche
   `experiments/2026-08-04-change-rung4-module-fingerprints/`),
   reader-before-writer, absence-tolerant for all committed roots,
   contract clause in `Event._process_payload_contract`, sweep probe in
   its own separate commit.
3. **Bundle ladder scripts** — one per bundle, under `experiments/`.
4. **Qualification cost** — the recurring price. The provider profile
   is part of the qualification subject digest, so every distinct
   sampling recipe is a new subject: ~14-minute battery once per mode
   per home, then ~1 s cache hits. Four modes ≈ one hour one-time.
   This is by design and is a feature: each mode is qualified as what
   it actually is.

## Epistemological guardrail (write into the spec when captured)

The mode changes how content is GENERATED, never what counts as
EVIDENCE. Explore output is conjecture material; only the critical
run's typed record is admissible. A bundle must never let explore-mode
prose skip the criticism stage and land as a finding — the bundle
scripts enforce the ordering mechanically, the way ladders enforce
setup → qualify → reason. If this ordering is breakable, the Popperian
premise of the harness is broken with it.

## Also parked in the same conversation (separate idea, separate doc
## if picked up)

A "mini reason harness" for weak executor models (Haiku-class): a
driver script owns the tranche loop, the model fills typed slots
validated against schemas, all commands run by the driver, gates as
pre-commit hooks, stateless calls with disk as the only memory.
Distinct from this proposal; recorded here only so the pointer
survives.
