# Results — the two-call seat protocol

Honest-ledger segments. What the record shows, and the residue.

## 2026-08-22 — the requalification price is NOT zero, and my earlier claim was wrong

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
