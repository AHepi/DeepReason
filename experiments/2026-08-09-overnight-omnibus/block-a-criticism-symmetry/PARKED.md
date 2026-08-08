# Block A — parked items

## P1 (GAP, not a defect): the reverse arm is structurally impossible with today's seat vocabulary

**What's missing:** Rung C2's full self/cross design matrix
(docs/proposals/CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md) needs to vary
BOTH sides independently -- which model conjectures, and which model
criticizes. Today's seat vocabulary only lets Block A vary the
conjecture side. `GROUP_ROLES` (src/deepreason/seat_bindings.py:34-38)
defines exactly three groups:

    GROUP_ROLES = {
        "conjecture": frozenset({"conjecturer", "variator"}),
        "coder": frozenset({"property_designer", "encoder"}),
        "scratch": frozenset({"conjecturer", "synthesizer", "summarizer"}),
    }
    GROUP_ALIASES = {"simulation": "conjecture"}

There is no `"critic"` group, and `argumentative_critic` is not a
member of any `GROUP_ROLES` set. `valid_group_names()`
(seat_bindings.py:55) returns exactly `{conjecture, coder, scratch,
simulation}`. `--seat critic=...` or `--seat argumentative_critic=...`
is rejected by CLI validation before any provider call is made -- this
is a typed refusal, not a stochastic miss.

**Consequence for this tranche:** Block A can run SELF (glm both
sides) and CROSS-conjecture (gemma conjectures, glm criticizes), but
NOT the mirror CROSS-critic cell (glm conjectures, gemma criticizes).
The comparison this block reports is therefore "own critic facing a
foreign conjecture" vs "own critic facing its own conjecture" -- it
cannot yet isolate whether asymmetry (if found) comes from the
CONJECTURER's foreignness or the CRITIC's identity, because the critic
is glm-5.2 in both cells. That confound is inherent to today's seat
vocabulary, not a flaw in this block's design.

**Ready prompt for a critic-seat rung (do not implement without
operator approval -- this is a change, route through
`dr-change-orchestrator`):**

> Add a `critic` entry to `GROUP_ROLES` in
> `src/deepreason/seat_bindings.py` mapping to
> `{"argumentative_critic"}`, so `--seat critic=PATH` binds the critic
> role independently of the conjecture role group. This unblocks Rung
> C2's full design matrix (docs/proposals/CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md),
> which today can only vary the conjecture side. `dr-capture-request`
> should ledger this ask verbatim. `dr-spec-change` must confirm
> whether this touches any frozen surface --
> `docs/map/INV-frozen-surfaces.md` lists state digests, harness event
> application, replay-validation formats, manifest schemas, and
> qualification-subject digests as frozen; seat-binding digest
> computation in `seat_bindings.py` is NOT on that list as of
> 2026-08-09, but confirm during spec, do not assume from this note
> alone. Also confirm interaction with `PARKED.md P1` from
> `experiments/2026-08-08-live-two-seat-ab-s6/` (the `coder` group's
> `property_designer` role has no public dispatch path -- a new
> `critic` group must be checked against the same class of dispatch-path
> question before being declared usable, not just declared bindable).

This gap is itself a deliverable of Block A: it tells Rung C2's
designer exactly what to build before the full pre-registered program
can run its critic-side cells.
