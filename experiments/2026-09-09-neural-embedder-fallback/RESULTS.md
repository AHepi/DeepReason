# Results — the silent hashing fallback

## 2026-09-09 — the warmed embedder was never asked for, and now the run says so

**What the record showed.** All five arms of the brief-variation step-1 tranche
printed `embedder: hashing (hashing-128)` after that session's own
`deepreason embedder-warmup` had returned the neural fingerprint. The tranche
brief named the likely cause: a detached process that could not see the cache
the warmup filled. The record refutes that in one step. A neural backend that
is asked for and cannot be built records an `embedder-fallback` Measure with
its cause; all five logs carry zero such events, and all five completed. What
they carry is the signature of a request never made.

**What was actually wrong.** On the managed `deepreason reason` path,
`preparation._config_for_profile` sets `EMBEDDER_MODEL=None` as one of seven
values the host owns whatever the operator configured, and those seven are the
stated exception to the compiler's own `ENGINE_CONFIG_FIELD_NOT_CARRIED`
disclosure. So the neural default the ordinary install arms was discarded with
no notice, and `ops.make_embedder` returned on its `if not
config.EMBEDDER_MODEL` branch before the `embedder-fallback` record below it
could be reached. The weights were fetched and never consulted, because no code
path ever asked for them.

This is the 2026-08-16 embedder trap recurring one stage earlier. That fix
armed the default by install and surfaced the fallback in `deepreason results`.
Both halves work. Neither reaches a path that overrides the default before
either can see it.

**What was fixed.** A third declared signal, `embedder-unconfigured`, records
the cause on the branch that used to return silently, and `deepreason results`
quotes the recorded text rather than composing its own. The run's log now
answers "why is this geometry hashing?" in every case: the `embedder` stamp for
a neural backend that built, `embedder-fallback` for one asked for and not
built, and this for the case where nothing asked.

Deliberately not `embedder-fallback` for the unset case. R3/R15 of the
2026-08-16 tranche holds that the deliberate hashing escape is no degradation
and records no fallback, and a run-time builder cannot tell that escape from a
host override — both arrive as `EMBEDDER_MODEL is None`. Two compile-stage
roads were examined against the record and rejected first: a carriage notice
carrying the dropped model would RESTORE it at run time, re-deciding which
embedder a configuration selects; under any other code the notice would survive
into the qualification subject payload and move every home's subject digest,
which is frozen surface 5. FIX.md records both with their prices.

**What the record now shows.** Two offline soak roots, same case, same stub,
differing in one value:

| | engine_config.EMBEDDER_MODEL | log | `deepreason results` |
|---|---|---|---|
| treatment | `None` | `embedder-unconfigured` + `embedder hashing-128 / 4226e035204776db` | `hashing (hashing-128) — <cause>` |
| control | `nomic-ai/nomic-embed-text-v1.5` | `embedder nomic-ai/… / d6e3599ce0377000` | `neural (nomic-ai/nomic-embed-text-v1.5)` |

`verify_root`: 0 violations in both. The treatment's hashing sentinel is the
one all five arms carry; the control's neural fingerprint is the one this
session's warmup printed. Full gate 5178 passed, 0 failed, twice.

**A correction this tranche's own verification produced.** The first shipped
version of the recorded cause pointed readers at
`run-manifest.json scratch_policy.embedder_model`. The control root shows that
field is `null` in a run that measured NEURAL, exactly as it is in one that
measured hashing — the manifest carries the embedder in its `engine_config`
echo, which is what `config_from_run_manifest` reads back. A pointer null in
working and broken runs alike sends half its readers to the opposite of the
truth. Corrected in the same tranche, pinned by a test, and ledgered as
`docs/ERRATA.md` E85. DIAGNOSIS.md's wording stands as written: it records what
that phase concluded on the evidence it then had.

**Residue.** Accepted does not mean true, and this tranche accepted less than
it might look like.

- The managed path still cannot USE a configured embedder. Making the decision
  VISIBLE is not making it configurable. `deepreason embedder-warmup` still
  buys a managed run nothing, which means CLAUDE.md's Environment instruction
  to run it at setup is, for `deepreason reason`, currently pointless. Three
  roads priced in PARKED.md P3; the choice is the operator's.
- The five sealed arm roots are unchanged and their distance readings stay on
  the hashing scale. Nothing here retro-fits them, and nothing may.
- The other six host-owned values were not examined (PARKED.md P1).
- Nine `docs_verify` failures on this container were not caused by this tranche
  and were not investigated. About four post-date the recorded baseline.
- No live run. The proof is a stub-driven root, and the claim is bounded to
  that: a live provider would change what the seats say, not how the embedder
  is chosen.
