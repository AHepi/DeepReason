# Results — the two-call seat protocol

Honest-ledger segments. What the record shows, and the residue.

## 2026-08-22 — SUPERSEDED next segment. Written from a defective tree.

**Correction, stated plainly.** SPEC.md's M9 measured the SIGNATURE of
`qualification_subject_payload(manifest, profile)`, saw no `Config` parameter,
and concluded that a Config-only change moves no qualification subject digest
and costs zero requalification. That conclusion was wrong. `Config` reaches the
subject INDIRECTLY, through two fields of the manifest the subject embeds
wholesale. Measuring the signature is not measuring the content, and this is
the second time in this tranche that a claim carried a passing check while
being false about a neighbouring assertion (the first was E43's, recorded in
ERRATA).

**The measurement.** Same committed fixture
(`tests/test_reusable_qualification.py::_manifest` / `_profile`), same probe,
run on this tree and on the tranche base `e1ea05e82`, three times each —
deterministic within a tree, different across them:

    e1ea05e82  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
    this tree  a5d81e5d34f516358649ee1f011642adf80d1fc072c6d774a1ba7be8d27108f0

Diffing the subject PAYLOAD localises it to exactly two keys, and no others:

    engine_config_json   gains "SPLIT_BUDGET_EXTRACTION_TOKENS":512
                         and    "SPLIT_BUDGET_SEAT_PROTOCOL":"auto"
    source_config_hash   76e35e16... -> a63f4526...

Nothing else in the 1268-line payload moved: not the provider profile, not its
digest, not the policy preset, not the pair inventory, not the route table.

**Which profiles moved, and the price per home (R13).** Every profile, in the
sense that matters: the subject digest is a function of the whole manifest, and
`engine_config_json` is in every v6 manifest regardless of which provider
profile is bound. So the price is not per-profile — it is **one full
qualification battery per `DEEPREASON_HOME`** (~14 minutes, ~1160 calls) on the
first `deepreason qualify` after this lands, paid once. A home with seat
bindings additionally re-runs the per-profile loop, one battery per distinct
bound profile digest, for `status`/readiness granularity only; a run's launch
still depends solely on the combination subject.

Reported, not stopped — the operator's standing instruction for this cost.

**What it does NOT mean.** No committed root is invalidated and no cached
verdict becomes wrong: a stale cache entry describes a subject that no longer
exists, so it simply stops matching and the battery re-runs. Replay is
untouched — `Config` is genuinely invisible to it, which is the half of the
map's claim that survives.

**The map claim this corrects.** `docs/map/INV-frozen-surfaces.md` says, under
"Where authority is allowed to live instead": "A `Config` value costs nothing to
add and is invisible to replay." The second clause is true. The first is not,
and the counter-example is this tranche. Corrected in place with a check, and
ledgered in `docs/ERRATA.md`.

**Residue.** The digest comparison above is over ONE committed fixture. It
localises the move to two keys and shows nothing else drifted, which is what
was needed; it is not a claim about every manifest shape in the tree.


## 2026-08-23 — the price is zero after all, and the full gate is what said so

**Correction to the segment above, which is itself a correction.** That segment
measured the digest moving and wrote it up as an inherent cost: "one full
qualification battery per DEEPREASON_HOME". That was a description of a
DEFECTIVE implementation, not of the design. The full gate said so, in 40
failures, and a digest comparison alone never could have.

**What the gate found.** 39 of the 40 were one cause: the two new `Config`
fields were reaching every manifest's `engine_config_json` and
`source_config_hash`, which moved the qualification subject digest, 22 frozen
manifest wire-byte goldens, and the shipped-digest pin
(`test_the_shipped_qualification_subject_digest_does_not_move`, whose docstring
says in as many words that moving it "costs a ~14-minute qualification battery
per home"). The repo already owns the remedy:
`run_manifest.py::_versioned_source_config_data` drops `Config` keys that
postdate the frozen goldens, and eight prior knobs are in that list for exactly
this reason. The two `SPLIT_BUDGET_` keys join them.

**The measurement, after.** Same committed fixture, same probe:

    e1ea05e82  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
    this tree  b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386

Byte-identical. **No qualification subject digest moves; the requalification
price is zero per home** (R13). The protocol's effect is still fully recorded —
per attempt, in `split_leg` / `split_max_tokens` / `split_notice`, which says
which leg produced what under which budget, and is a stronger record than a
Config echo would have been.

**The 40th failure** was mine and unrelated: `MockEndpoint`'s new two-parameter
script detection read `_fn.__code__`, which callable OBJECTS do not have, and
several suites script the endpoint with one. It now falls back to the
one-parameter contract.

**One derived golden legitimately moved.** The Wave A incident fixture's A3
generated-root digest, `71f9ae10357a...` -> `5bccbcafb361...`. Measured to the
character before it was touched — across three generated roots and every file in
them, exactly one file differed, and within it exactly one inserted field group
on one line:

    ,"natural_stop":true,"split_leg":"","split_notice":"","split_max_tokens":null

That is precisely the R6 data the operator asked to be recorded. A1 and A2 are
byte-identical, and every descriptor SHA-256 — the actual evidence the fixture
exists to preserve — is unchanged. The test still pins byte-identity and still
pins first-run == second-run determinism; only the derived value moved.

**Census miss, recorded as a finding.** SPEC.md's blast-radius census listed the
13 test files that name `LLMAttempt` and classified them MUST NOT MOVE. It was
right about all 13. It missed
`tests/test_incident_wave_a_v2_fixtures.py`, which never names `LLMAttempt` —
it GENERATES a root and pins its bytes. A name-based census cannot see a
consumer that reaches the record through behaviour rather than through an
import, and the full gate is what covers that gap. This is the same shape as
the two prior census misses the `dr-spec-change` skill already records.

**Residue.** The two `data.pop` lines mean a run's manifest does not state
whether the split protocol was armed. The per-attempt record does, on every
attempt, which is why this is judged a better trade and not a loss — but it is
a real difference, and a reader reconstructing a run's configuration from the
manifest alone will not find it there.
