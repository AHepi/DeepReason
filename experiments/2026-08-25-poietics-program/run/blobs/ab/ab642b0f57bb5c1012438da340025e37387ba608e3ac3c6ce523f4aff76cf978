# Section 12 — Mutation testing: the measurement that inverted the project's self-assessment

*Period: 2026-08-25. Sources: `scripts/mutation_probe.py`, `zoo/mutations/REGISTRY.json`,
`zoo/mutations/RUN_2026-08-25.md`, `zoo/mutations/BACKLOG.md`, `tests/test_mutation_registry.py`,
field reports FR-30 and FR-31.*

## 12.1 What prompted it

The project had operated since 2026-08-17 under rule **FR-18**: *a guard is not installed
until it has been shown to FAIL on a planted violation.* On 2026-08-25 two incidents showed
that rule to be correct but **unrepeated**.

First: a constant naming the two challenge kinds that reach a rule's blocker atom,
`_RULE_TARGET_BLOCKING_KINDS = frozenset({"undercut", "wound"})`, lost the member `"wound"`.
**The entire suite stayed green at 677 passing tests.** The decision RT-6 was, at that
moment, held by nothing. It surfaced only because an independent reviewer, asked "what could
revert without a test catching it?", happened to name that constant.

Second, and worse: **the first guard written to close that gap was itself vacuous.** It
iterated the constant it was meant to hold:

    for kind in compile_module._RULE_TARGET_BLOCKING_KINDS:

so removing a member merely ran one fewer subtest. 95 became 94, nothing failed, and the
guard looked installed. Reading it would not have caught that; re-running the plant did, in
about a second.

The diagnosis (FR-30): FR-18 is a **ritual performed once**, by hand, by whoever remembers,
never performed again — while the guard it certified ages against code that moves. A rotted
guard is indistinguishable from a working one, because both are green.

## 12.2 The instrument

`scripts/mutation_probe.py` turns the plant into a standing registry. Each entry is a single
syntactically-valid source edit that would silently reverse a commitment, and names the
**decision** it reverses rather than the file it lives in.

The indexing choice is load-bearing. Generic mutation testing (flip `>` to `>=`) measures
line coverage with extra steps and buries the reader in equivalent mutants. This repository
has an authority chain — a byte-pinned specification, then a record of sixteen accepted
decisions, then the implementation — so the report answers **"which decisions are actually
held?"**

Verdicts: `CAUGHT` (suite failed), `SURVIVED` (suite passed — the decision is not held
against that edit), `ERROR` (the tree would not collect; counted as caught but reported
separately as uninformative).

## 12.3 The result

    CAUGHT 16   SURVIVED 46   ERROR 0   of 62
    3 of 26 decisions held against every registered mutation

The suite at the time of measurement: **701 test methods, 2,985 subtests, 28,987 lines of
test code** against **13,206 lines of engine across 29 modules**.

**The suite holds three of twenty-six commitments.**

## 12.4 What SURVIVED does and does not mean

It does **not** mean the code is wrong. Every one of these 46 edits was applied to code that
is, as far as anyone can determine, correct. Three independent model reviews run the same
morning returned **15/15 CONFORMS** across the RT, DF and REG clusters, and they were right
about the code.

A survivor means something narrower and worse: **nothing would tell you if it stopped being
correct.**

## 12.5 Controls

A run reporting everything broken is as useless as one reporting nothing. Three controls
were passed before the number was recorded:

| control | result |
|---|---|
| Full suite on an **unmutated** sandbox copy | 701 passed, 2,985 subtests — identical to the working tree |
| Verdict **reproducibility** across three runs (two in-tree, one sandboxed) | 26 common verdicts, **zero disagreements** |
| Survivors read by hand for **equivalent mutants** | three spot-checked, all genuine (below) |

Spot-checked survivors:

- `integer-detail-accepts-bool` — `type(value) is int` → `isinstance(value, int)`. In Python
  `isinstance(True, int)` is `True`, so a bool is admitted as an integer detail. Reverses the
  exact-type value vocabulary via a change that reads as a style preference.
- `reg1-discharge-vocabulary-grows` — adds `"compensating_transport"` to the registry's known
  discharge kinds: the structure the specification protects with *"may grow only through a
  registry version change."*
- `rule-block-effect-from-challenge-case` — rule-target blocking derives from `challenge-case`
  rather than `open-challenge`, so a discharge stops lifting the block.

## 12.6 Decision coverage

| decision / invariant | caught | registered | held |
|---|---|---|---|
| AU-3 | 1 | 2 | no |
| AU-4 | 0 | 2 | no |
| AU-6 | 0 | 1 | no |
| Adapter profile | 1 | 1 | **YES** |
| DF-1 | 3 | 6 | no |
| DF-2 | 1 | 2 | no |
| INV-canonical-determinism | 0 | 3 | no |
| INV-cert-reading | 0 | 1 | no |
| INV-closure-cut-coherence | 0 | 1 | no |
| INV-deterministic-binding-order | 0 | 1 | no |
| INV-draft-namespaces | 0 | 2 | no |
| INV-frame-policy | 0 | 1 | no |
| INV-generated-id-purity | 0 | 1 | no |
| INV-ground-closed-universe | 0 | 2 | no |
| INV-no-status-inference | 2 | 5 | no |
| INV-no-unguarded-negation | 1 | 1 | **YES** |
| INV-pack-independence | 0 | 1 | no |
| INV-replay-fold | 0 | 1 | no |
| INV-untrusted-boundary | 0 | 3 | no |
| INV-value-vocabulary | 0 | 2 | no |
| INV-well-founded | 0 | 3 | no |
| REG-1 | 0 | 6 | no |
| RT-1 | 2 | 7 | no |
| RT-2 | 0 | 1 | no |
| RT-6 | 3 | 4 | no |
| SO-2 residual | 2 | 2 | **YES** |

## 12.7 Survivors by file — the distribution is the finding

| survivors | registered | file |
|---|---|---|
| 6 | 6 | `src/poietics/pff/registry.py` |
| 6 | 7 | `src/poietics/pff/validate.py` |
| 4 | 4 | `src/poietics/binding/plan.py` |
| 4 | 4 | `src/poietics/canonical.py` |
| 3 | 3 | `src/poietics/cli.py` |
| 3 | 5 | `src/poietics/explain/report.py` |
| 3 | 3 | `src/poietics/generation/extract.py` |
| 3 | 4 | `src/poietics/ground/model.py` |
| 3 | 3 | `src/poietics/packs/empirical.py` |
| 2 | 2 | `src/poietics/generation/ollama.py` |
| 2 | 2 | `src/poietics/ground/evaluate.py` |
| 2 | 4 | `src/poietics/pff/model.py` |
| 1 | 1 | `src/poietics/binding/finalize.py` |
| 1 | 1 | `src/poietics/binding/model.py` |
| 1 | 2 | `src/poietics/explain/model.py` |
| 1 | 1 | `src/poietics/generation/model.py` |
| 1 | 9 | `src/poietics/pff/compile.py` |
| 0 | 1 | `scripts/independent_review.py` |

`compile.py` lost **1 of 9**. It is the file the three semantic freezes (RT, DF, REG) were
implemented in during this cycle, each guard written under FR-18 and shown red on a planted
violation before installation.

Everything guarded the ordinary way fell over: `registry.py` **6/6**, `validate.py` **6/7**,
`canonical.py` **4/4**, `binding/plan.py` **4/4**.

**Guards proved against a planted violation hold. Guards written by writing a test do not.**
This is not a claim about diligence. The ordinary test is written by *reading the code and
asserting what it does*, so it agrees with the code by construction, and goes on agreeing
after the code stops being right.

`registry.py`'s 6/6 is the loudest single result: the discharge-compatibility vocabulary can
grow, `rebut` can become dischargeable, `revoke` can lose explicit retraction, a checker id
can go incoherent with its version — all with 701 tests green. That vocabulary is precisely
what decision REG-1 was accepted to defend.

## 12.8 Full mutation table

Every registered mutation, its verdict, the decision it reverses, and why it is silent.


### `au3-closure-gains-payload-hash` — **CAUGHT**

- **Decision:** AU-3
- **File:** `src/poietics/pff/model.py`
- **Reverses:** ClosureRecord gains the payload_hash the owner accepted it should NOT have, on the reading that a closure's payload is carried inline
- **Why silent:** it looks like bringing ClosureRecord into line with CertificateRecord, and an empty default breaks no construction site

```diff
- selector: Selector
    members: frozenset[RecordRef] = field(default_factory=frozenset)
+ selector: Selector
    payload_hash: str = ""
    members: frozenset[RecordRef] = field(default_factory=frozenset)
```

### `adapter-temperature-sampling` — **CAUGHT**

- **Decision:** Adapter profile
- **File:** `scripts/independent_review.py`
- **Reverses:** the review harness starts sampling, so a recorded parameter stops describing the call that was made
- **Why silent:** a substring guard survived this exact edit once already; only an AST walk over every chat() call catches it

```diff
- model=job.model, temperature=0.0, seed=17,
+ model=job.model, temperature=0.7, seed=17,
```

### `defect-effect-from-open-challenge` — **CAUGHT**

- **Decision:** DF-1
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** The defect's diagnosis atom is now derived from `open-challenge(c)`, so discharging the defect deletes the diagnosis instead of only closing the obligation -- the retention that DF-1's whole lifecycle rests on ("a later discharge changes whether the obligation is open, and does not delete the diagnosis") is gone.
- **Why silent:** Collapsing a three-line conditional into one uniform body is the archetypal tidy-up, the ternary is the only thing distinguishing the two effect kinds, and the reversal shows up only after a discharge lands -- a single test in `tests/test_zoo_defect_lifecycle.py` stands between this edit and a green suite.
- **Note:** DF-1 (the retained diagnosis derives from challenge-case, NOT open-challenge)

```diff
- positive=frozenset(
                    {
                        challenge_case
                        if effect_role is CompilationRole.DEFECT_EFFECT
                        else open_challenge
                    }
                ),
+ positive=frozenset({open_challenge}),
```

### `df1-drop-pair-c-citation` — **CAUGHT**

- **Decision:** DF-1
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** the compiler's record of why the binding was accepted stops citing pair C and cites case 12 instead --- both halves of DF-1 condition 1 at once
- **Why silent:** a comment edit shows up as documentation churn, and case 12 is a real passing conformance case so the citation looks supported

```diff
- # THE EVIDENCE IS PAIR C, not conformance case 12.
+ # The evidence is conformance case 12.
```

### `obligation-drops-discharge-gate` — **CAUGHT**

- **Decision:** DF-1
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** DF-1's second binding disappears: `open-problem-face(c)` no longer closes when the challenge is discharged, so the obligation stays open forever and the discharged/undischarged pair the acceptance record calls pair C collapses into one state.
- **Why silent:** The comment block immediately above says a discharge "does not delete the diagnosis", so removing the discharge gate looks like enforcing DF-1 rather than reversing half of it; it also removes a negative literal, which reads as strengthening the no-unguarded-negation posture.
- **Note:** DF-1 (`face_discharged(w)` binds to the compiled `discharged(c)`)

```diff
- # DF-1's second binding: `face_discharged(w)` is the
                    # compiled `discharged(c)`.
                    negative=frozenset(
                        {
                            _generated_atom(
                                CompilationRole.DISCHARGED,
                                record.ref,
                            )
                        }
                    ),
+ # DF-1: a later discharge does not delete the retained
                    # diagnosis, so this rule carries no discharge gate.
                    negative=frozenset(),
```

### `obligation-indexed-by-face` — **CAUGHT**

- **Decision:** DF-2
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** Re-indexes the derived obligation on the problem face instead of the challenge, which is the face-indexed reading DF-2 declined to implement; it silently changes the derived atom's identity, and where several defects name one face it aggregates them into a single obligation whose partial-discharge behaviour is the case DF-2 says the two indexings disagree on.
- **Why silent:** The specification writes the rule over the face, so this looks like closing a known deviation rather than reversing an accepted approximation, and with one defect per face the compiled program is identical except for the atom's spelling.
- **Note:** DF-2 (one obligation per CHALLENGE, accepted as a deliberate approximation of the face-indexed rule)

```diff
- open_problem_face = _generated_atom(
                CompilationRole.OPEN_PROBLEM_FACE,
                record.ref,
            )
+ open_problem_face = _generated_atom(
                CompilationRole.OPEN_PROBLEM_FACE,
                record.problem_face_atom,
            )
```

### `ground-holds-predicate` — **CAUGHT**

- **Decision:** INV-no-status-inference
- **File:** `src/poietics/ground/model.py`
- **Reverses:** The ground model itself publishes a predicate that reads support off the fixed-point status, which is precisely the inference the specification forbids; LIVE stops being a package-relative computational result at the API surface and becomes a supported/holds answer that callers can and will take at face value.
- **Why silent:** It is purely additive and looks like a harmless convenience wrapper over `status_of`; nothing in the suite constrains the vocabulary or the public surface of Evaluation, so the whole suite stays green.
- **Note:** cross-cutting rule quoted in AU-7: "No module SHALL infer truth, support, acceptance, confidence, or probability from the fixed-point status"

```diff
- def status_of(self, atom: AtomRef) -> Status:
        """Return the derived status of an atom in this evaluation."""
+ def holds(self, atom: AtomRef) -> bool:
        """Whether this evaluation supports the atom."""

        return atom in self.live

    def status_of(self, atom: AtomRef) -> Status:
        """Return the derived status of an atom in this evaluation."""
```

### `report-exposes-acceptance` — **CAUGHT**

- **Decision:** INV-no-status-inference
- **File:** `src/poietics/explain/model.py`
- **Reverses:** The report module now reads acceptance straight off the fixed-point status, publishing `report.accepted` as API — exactly the inference the specification forbids and the module docstring promises it does not make.
- **Why silent:** The guard that exists (`test_the_report_carries_no_score_or_count_field`) inspects `DiscernmentReport.__dataclass_fields__`, and a property is not a dataclass field, so the whole suite stays green — 691 passed — while the forbidden word becomes public surface.
- **Note:** the cross-cutting sentence: "No module SHALL infer truth, support, acceptance, confidence, or probability from the fixed-point status" (AU-7 restates it as binding every module)

```diff
- if self.status is Status.LIVE and not self.live_cases:
            # A live atom with no live case is a base fact, which is fine; a
            # live atom whose live cases were dropped is not.  The distinction
            # is enforced in report.py, which knows the base partition.
            pass
+ if self.status is Status.LIVE and not self.live_cases:
            # A live atom with no live case is a base fact, which is fine; a
            # live atom whose live cases were dropped is not.  The distinction
            # is enforced in report.py, which knows the base partition.
            pass

    @property
    def accepted(self) -> bool:
        """Whether the queried atom came out accepted
```

### `closed-negative-literal-unguarded` — **CAUGHT**

- **Decision:** INV-no-unguarded-negation
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** Every closed negative literal in a rule body becomes an unguarded default negation: the rule case no longer requires `closure-ready(literal.closure)`, so a rule whose closure failed or is open now fires as LIVE on the absence of the negated atom instead of going SUSPENDED. This is the one construct the core specification names to keep negation closed.
- **Why silent:** The closure is already resolved and checked at admission, so the ground conjunct looks like a redundant re-assertion of something the validator guaranteed; nothing in the compiled rule's shape hints that the conjunct is what carries the fail-closed semantics.
- **Note:** spec invariant: no unguarded default negation -- every negative literal sits behind its closure gate

```diff
- *(
                _generated_atom(CompilationRole.CLOSURE_READY, literal.closure)
                for literal in record.negative
            ),
+ 
```

### `rt1-default-blocker-closure` — **CAUGHT**

- **Decision:** RT-1
- **File:** `src/poietics/pff/model.py`
- **Reverses:** RuleRecord.blocker_closure becomes optional, which is the `optional` reading the owner explicitly declined
- **Why silent:** a default reads as a convenience for callers rather than as a semantic reversal, and every existing construction site keeps working

```diff
- #: supports, and the owner took `required`.
    blocker_closure: RecordRef
+ #: supports, and the owner took `required`.
    blocker_closure: RecordRef | None = None
```

### `rule-clear-conjunct-conditional-on-faces` — **CAUGHT**

- **Decision:** RT-1
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** RT-1 authorises the conjunct unconditionally, in explicit contrast to the rejected `optional` reading where it was conditional. Under this edit any rule that names a face silently opts out of being blockable at the rule level, so RT-2's rule-target route dies for exactly the rules that have faces.
- **Why silent:** It reads as de-duplication -- a faced rule already carries `clear(f)` for each face, so `rule-clear` looks redundant -- and the conditional is invisible unless a test drives a rule-target challenge against a rule that also owns faces.
- **Note:** RT-1 (every rule gains the `rule-clear` conjunct UNCONDITIONALLY)

```diff
- rule_clear,
        }
        negative = {_source_atom(literal.atom) for literal in record.negative}
+ *((rule_clear,) if not record.faces else ()),
        }
        negative = {_source_atom(literal.atom) for literal in record.negative}
```

### `rt6-drop-wound` — **CAUGHT**

- **Decision:** RT-6
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** a `wound` targeting a RULE stops landing on that rule's blocker atom and falls through to the face-blocking branch, collapsing the partition RT-6 accepted
- **Why silent:** the whole suite stayed green at 677 tests when this was first planted; `undercut` was the only kind any real-compiler route drove

```diff
- _RULE_TARGET_BLOCKING_KINDS = frozenset({"undercut", "wound"})
+ _RULE_TARGET_BLOCKING_KINDS = frozenset({"undercut"})
```

### `rt6-wide-rule-blocker-domain` — **CAUGHT**

- **Decision:** RT-6
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** It takes RT-6's WIDE reading: a closure over challenges targeting one of the rule's own faces is accepted as that rule's blocker domain, so rule and face blocker spaces overlap instead of partitioning -- on the pin's battery instance B1 that is `fail`/`SUSPENDED` where the accepted narrow reading gives `pass`/`rule-clear` LIVE.
- **Why silent:** One added `and` line inside a long boolean, phrased as though a rule's own faces obviously belong to the rule; the surrounding comment still says the opposite, which a skimming reviewer will not read against the code. This one IS held: `tests/test_local_selector_scope.py::NarrowRuleBlockerDomainTests::test_a_closure_over_the_rules_own_face_is_refused` fails, so it is a sentinel rather than a gap.
- **Note:** RT-6 (a rule's blocker closure is a closure over challenges targeting THAT RULE, not its faces)

```diff
- selected_entry = self._lookup_any(selected_target)
            role_mismatch = (
                selected_entry is not None
                and selected_entry.kind
                in {RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE}
            )
        if role_mismatch:
+ selected_entry = self._lookup_any(selected_target)
            role_mismatch = (
                selected_entry is not None
                and selected_target not in rule.faces
                and selected_entry.kind
                in {RecordKind.ATOM, RecordKind.RULE, RecordKind.FACE}
            )
        if role_mismatch:
```

### `rule-clear-negates-face-blockers` — **CAUGHT**

- **Decision:** RT-6
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** This is exactly the wide reading RT-6 rejected: `rule-clear(r)` now also fails when any of r's FACES has an open challenge, so the two blocker spaces overlap instead of partitioning, and on the pin's battery instance B1 `rule-clear` goes SUSPENDED where the accepted narrow reading gives LIVE.
- **Why silent:** It looks like an obvious completeness fix ("a rule is not clear if one of its faces is under challenge") and it changes no rule head's status: `live-case` already carries each face's `clear(f)` conjunct, so the only thing that moves is the status of the `rule-clear` atom itself.
- **Note:** RT-6 (the narrow domain: a rule's blocker space and its faces' blocker spaces PARTITION)

```diff
- negative=frozenset({has_open_challenge_rule}),
+ negative=frozenset(
                    {
                        has_open_challenge_rule,
                        *(
                            _generated_atom(
                                CompilationRole.HAS_OPEN_CHALLENGE,
                                ref,
                            )
                            for ref in record.faces
                        ),
                    }
 
```

### `contrary-to-collapses-cycles` — **CAUGHT**

- **Decision:** SO-2 residual
- **File:** `src/poietics/explain/report.py`
- **Reverses:** CONTRARY_TO becomes cycle-forming in the only place that consults cycle-forming relations, so wherever one contrary is derived from the other the pair is collapsed into a CYCLE summary node — a conflict summarised as a derivation loop, the exact conflation the acceptance disqualified.
- **Why silent:** The decision is guarded as data — `test_accepted_no_change_decisions.py` reads `_CYCLE_SETTLING_EDGE_KINDS` and asserts CONTRARY_TO is not in it — and this edit leaves that frozenset untouched; adding the successor in one direction only also leaves the existing contrary-edge fixture acyclic, so all 691 tests pass.
- **Note:** SO-2 residual — ACCEPTED: `BLOCKS` only; CONTRARY_TO is disqualified by symmetry

```diff
- elif edge.kind in _CYCLE_SETTLING_EDGE_KINDS:
            successors[edge.target].add(edge.source)
+ elif edge.kind in _CYCLE_SETTLING_EDGE_KINDS:
            successors[edge.target].add(edge.source)
        elif edge.kind is EdgeKind.CONTRARY_TO:
            # A contrary is a dependency too: each side turns on the other.
            successors[edge.target].add(edge.source)
```

### `so2-contrary-is-cycle-forming` — **CAUGHT**

- **Decision:** SO-2 residual
- **File:** `src/poietics/explain/report.py`
- **Reverses:** CONTRARY_TO becomes cycle-forming, so every contrary pair is summarised as a derivation loop --- the exact conflation the acceptance disqualified by symmetry
- **Why silent:** it reads as making the cycle detector more thorough, and CONTRARY_TO genuinely is symmetric so a loop 'exists'

```diff
- _CYCLE_SETTLING_EDGE_KINDS: frozenset[EdgeKind] = frozenset({EdgeKind.BLOCKS})
+ _CYCLE_SETTLING_EDGE_KINDS: frozenset[EdgeKind] = frozenset({EdgeKind.BLOCKS, EdgeKind.CONTRARY_TO})
```

### `certificate-payload-hash-optional` — **SURVIVED**

- **Decision:** AU-3
- **File:** `src/poietics/pff/model.py`
- **Reverses:** AU-3 is an ASYMMETRY held as a choice -- a closure carries no payload_hash because its payload is inline, a certificate carries one because its payload is not. Defaulting the certificate's field to "" dissolves the half that makes the choice meaningful: a certificate record can now exist that binds a checker and nothing about the payload it attests, so the shape no longer distinguishes the two records at all.
- **Why silent:** It reads as the same leniency AU-3 grants closures ('a checker with no payload can omit it'), _require_string accepts the empty default, and every fixture supplies a real hash -- so the replay test that asserts a certificate binds both checker and payload_hash still sees a truthy value and all 691 tests pass; only validate_package's CHECKER_PAYLOAD check, a layer away, would ever notice.
- **Note:** AU-3

```diff
- subject: RecordRef
    result: CheckResult
    payload_hash: str
+ subject: RecordRef
    result: CheckResult
    payload_hash: str = ""
```

### `au4-reserved-prefix-exempts-atoms` — **SURVIVED**

- **Decision:** AU-4
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** It loosens the validator to accommodate the specification's printed closed-negative-literal example -- exactly the accommodation AU-4 declined -- so a package may now CARRY a `__pff__:atom:discharged:challenge-c1` record and default-negate it, which I confirmed by construction: the base tree refuses that package with `reserved_id` and the mutated tree ADMITS it.
- **Why silent:** Both AU-4 tests plant the `__pff__:` id only in the reference position (an unresolved ref, still refused) and the one reserved-prefix test plants it on a RULE, so nothing in the suite ever puts the prefix on an atom record -- all 682 tests stay green.
- **Note:** AU-4 ("a __pff__: atom is a compiler artifact and never a package record")

```diff
- if record.id.startswith(RESERVED_ID_PREFIX):
+ if kind is not RecordKind.ATOM and record.id.startswith(
                RESERVED_ID_PREFIX
            ):
```

### `reserved-id-check-narrowed-to-atoms` — **SURVIVED**

- **Decision:** AU-4
- **File:** `src/poietics/binding/plan.py`
- **Reverses:** AU-4's load-bearing invariant -- a `__pff__:` name is a compiler artifact and never a package record -- which the identity gate enforces for every policy-supplied target. Narrowed to atoms, an untrusted-draft policy may claim reserved ids for rules, certificates and RT-1's blocker closures, letting authored records collide with compiled ones.
- **Why silent:** `test_f12_f14_f72_f76_f83_f84_target_boundaries` substitutes each bad target through `replace_record_target(..., DraftRecordKind.ATOM, ...)` only, so TARGET_RESERVED_ID is driven for atoms and nothing else. The edit reads as tightening the check to the case AU-4 actually names, since the acceptance sentence says 'a `__pff__:` atom'.
- **Note:** AU-4

```diff
- elif target.id.startswith("__pff__:"):
+ elif source.kind is DraftRecordKind.ATOM and target.id.startswith(
            "__pff__:"
        ):
```

### `cli-unreadable-is-just-a-refusal` — **SURVIVED**

- **Decision:** AU-6
- **File:** `src/poietics/cli.py`
- **Reverses:** It collapses the accepted exit-code taxonomy so that an unreadable or unparseable input is reported with the same code as a validated-and-refused package, erasing the documented distinction between "the tool refused your package" and "the tool could not read your input".
- **Why silent:** Every CLI test compares result.code against the imported constant and never against the literal number, so test_a_missing_file_is_distinguished_from_a_refused_package keeps passing while distinguishing nothing; verified green, 691 passed.
- **Note:** AU-6 / the accepted command-line contract in cli.py: "0 success; 1 the package was refused; 2 a usage error; 3 the input could not be read or parsed"

```diff
- EXIT_USAGE = 2
EXIT_UNREADABLE = 3
+ EXIT_USAGE = 2
EXIT_UNREADABLE = EXIT_REFUSED
```

### `defect-derives-role-swapped` — **SURVIVED**

- **Decision:** DF-1
- **File:** `src/poietics/explain/report.py`
- **Reverses:** The two defect-lifecycle rules trade places in the provenance projection: the retention dependency is drawn as a DERIVES edge while the defect's actual effect on its diagnosis is demoted to a reversed REQUIRES, so the graph no longer shows the challenge deriving the retained diagnosis.
- **Why silent:** Both roles are DF-1 additions with adjacent names, and the swap keeps the frozenset the same size and the file reading naturally; nothing in the suite asserts a DERIVES edge for the defect lifecycle, so the mutated tree still passes 691 tests.
- **Note:** DF-1/DF-2 — a defect DERIVES its retained diagnosis; `open-problem-face-rule`, like `clear-face` and `clear-rule`, is a dependency and not a derivation

```diff
- CompilationRole.DEFECT_EFFECT,
+ CompilationRole.OPEN_PROBLEM_FACE_RULE,
```

### `df1-defect-problem-face-required-only-for-face-targets` — **SURVIVED**

- **Decision:** DF-1
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** A `defect` challenge that targets a rule or an atom may now name no problem-face atom at all and still be admitted (nothing else supplies the contract -- with no registry target contract for the kind the validator's fallback allows ATOM, RULE and FACE targets), so the retention rule DF-1 authorises compiles with no diagnosis to retain.
- **Why silent:** "problem FACE atom" reads as a face-only concern, and DF-1/DF-2 are argued entirely in face terms, so restricting the requirement to face targets looks like tightening a check rather than opening one; the fixture defect targets a face, so the added conjunct never changes an outcome -- 682 tests still pass.
- **Note:** DF-1 (the defect lifecycle's retained diagnosis) and profile §4.2's defect shape

```diff
- if challenge.kind == "defect" and challenge.problem_face_atom is None:
+ if (
                challenge.kind == "defect"
                and challenge.target_kind is RecordKind.FACE
                and challenge.problem_face_atom is None
            ):
```

### `df1-discharge-closure-may-scope-another-challenge` — **SURVIVED**

- **Decision:** DF-1
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** A challenge's `discharge_closure` may now be a closure over ANOTHER challenge's discharges: the identity that makes DF-1's binding mean anything (the closure is the discharge domain OF THIS challenge) stops being enforced at admission, and with it DF-2's per-challenge obligation identity.
- **Why silent:** It reads as a copy-paste fix -- the selector's `record_type` is checked to be DISCHARGE eight lines above, so aligning the kind test with it looks like correcting an inconsistency; and the guard only bites on a closure naming a different challenge, which no fixture does, so the suite stays green (682 passed).
- **Note:** DF-1 (discharge_domain(w) binds to c.discharge_closure); DF-2 (one obligation per challenge)

```diff
- elif selected_challenge != challenge.ref:
                    selected_entry = self._lookup_any(selected_challenge)
                    role_mismatch = (
                        selected_entry is not None
                        and selected_entry.kind is RecordKind.CHALLENGE
                    )
+ elif selected_challenge != challenge.ref:
                    selected_entry = self._lookup_any(selected_challenge)
                    role_mismatch = (
                        selected_entry is not None
                        and selected_entry.kind is RecordKind.DISCHARGE
                    )
```

### `open-problem-face-node-becomes-face` — **SURVIVED**

- **Decision:** DF-2
- **File:** `src/poietics/explain/report.py`
- **Reverses:** The open obligation is reported as a FACE node while still keyed on the challenge reference, presenting DF-2's per-challenge approximation as the face-indexed rule the acceptance explicitly declined to implement — and naming a face record that does not exist.
- **Why silent:** A later key in the same dict literal quietly overrides the `_CHALLENGE_ROLES` expansion, so the comment in `_CHALLENGE_ROLES` that records the DF-2 reasoning is left intact and still appears to govern; the role name itself reads like a face, and no test asserts the node kind or id of an open-problem-face atom — 691 passed.
- **Note:** DF-2 — ACCEPTED: per challenge; the open obligation is owned by the CHALLENGE, which is the per-challenge indexing showing up in the provenance graph

```diff
- **{role: NodeKind.RULE_CASE for role in _RULE_BLOCKING_ROLES},
}
+ **{role: NodeKind.RULE_CASE for role in _RULE_BLOCKING_ROLES},
    # The open obligation is about a face, so it reads as a face node.
    CompilationRole.OPEN_PROBLEM_FACE: NodeKind.FACE,
}
```

### `blocker-closures-ordered-by-rule-not-by-id` — **SURVIVED**

- **Decision:** INV-canonical-determinism
- **File:** `src/poietics/binding/finalize.py`
- **Reverses:** The materialised blocker closures stop being ordered by their own stable id and become ordered by the rule they cover, so the package's closure collection is no longer in the canonical (id, version) order every other collection the binder emits is in.
- **Why silent:** The existing assertion is `tuple(c.ref for c in package.closures) == tuple(r.blocker_closure for r in package.rules)` -- it compares the closures against rule order, which is precisely what the mutation sorts by, so it passes by construction; and canonical.py re-sorts records before hashing, so no digest pin moves either.
- **Note:** canonical ordering of top-level record collections

```diff
- for rule in plan.rules
            ),
            key=lambda closure: _record_ref_key(closure.ref),
        )
    )
+ for rule in plan.rules
            ),
            key=lambda closure: closure.selector.where["target"],
        )
    )
```

### `reader-hides-duplicate-closure-members` — **SURVIVED**

- **Decision:** INV-canonical-determinism
- **File:** `src/poietics/canonical.py`
- **Reverses:** Passing a frozenset dedupes before _set_members can see the duplicates, so a document whose closure names atom:a@1 twice is accepted instead of refused (verified: refused on trunk, silently deduped after the edit). Two distinct documents then read back to one package with one hash, and the replay fold accepts a malformed closure payload -- the inline payload AU-3 relies on -- without a word.
- **Why silent:** It reads as making the closure branch consistent with the rule branch three cases above, which already builds positive/negative/faces with frozenset(...); the duplicate guard is pinned only for direct construction, never through parse_package, so all 691 tests pass.
- **Note:** the model's set-member invariant ("Copy a set-valued field without hiding duplicate raw members") and the canonical round trip's injectivity

```diff
- members=tuple(
                    _read_ref(item, path="members")
                    for item in body.get("members", ())
                ),
+ members=frozenset(
                    _read_ref(item, path="members")
                    for item in body.get("members", ())
                ),
```

### `sort-key-drops-the-version` — **SURVIVED**

- **Decision:** INV-canonical-determinism
- **File:** `src/poietics/canonical.py`
- **Reverses:** It reintroduces, on plain reference sets, exactly the partial order that _sort_key's own docstring says was the cross-process hash bug for closed-negative literals: two versions of one id inside a set-valued reference array tie, sorted() is stable, and the tie falls through to frozenset iteration order, so canonical_semantic_json and package_hash stop being pure functions of semantic content.
- **Why silent:** It reads as a simplification toward the specification's literal phrase 'sorted by stable ID', it only bites when one set holds two versions of the same id (no fixture does), and the whole suite stays green -- 691 passed -- while a rule whose positive body names atom:x@1 and atom:x@2 hashes differently in every interpreter process.
- **Note:** canonical byte determinism (the module's own recorded choice: a set member is ordered by its EXACT reference, id AND version)

```diff
- if type(value) in (RecordRef, VersionToken):
        return (value.id, value.version)
+ if type(value) in (RecordRef, VersionToken):
        return (value.id,)
```

### `pack-witness-may-be-empty` — **SURVIVED**

- **Decision:** INV-cert-reading
- **File:** `src/poietics/packs/empirical.py`
- **Reverses:** An atom certificate may now carry an empty witness and still satisfy the checker contract, so a primitive claim with no witness at all can pass and be placed in the base's `live` partition — the direct-witness requirement that keeps the base from filling itself.
- **Why silent:** Nothing in the suite asserts the shipped contract's detail-field value types, and every certificate the reference fixture builds sets a nonempty `witness:<id>`, so the loosened type is never exercised; it reads as dropping an over-strict string constraint.
- **Note:** the pack's CERT reading, stated at ATOM_WITNESS: "a passed direct witness enters `live`" — a certified primitive claim carries a witness

```diff
- checker_id=ATOM_WITNESS,
        version=1,
        uses={CheckerUse.CERTIFICATE},
        certificate_subject_kinds={RecordKind.ATOM},
        detail_fields=(
            CheckerDetailField(
                key="witness", value_type=CheckerDetailType.NONEMPTY_STRING
            ),
        ),
+ checker_id=ATOM_WITNESS,
        version=1,
        uses={CheckerUse.CERTIFICATE},
        certificate_subject_kinds={RecordKind.ATOM},
        detail_fields=(
            CheckerDetailField(
                key="witness", value_type=CheckerDetailType.STRING
            ),
        ),
```

### `closure-empty-cut-inherits-package-cut` — **SURVIVED**

- **Decision:** INV-closure-cut-coherence
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** A closure declaring an empty `cut_id` is admitted under any package cut, and -- because `cut_valid` also gates the result-coherence check -- it additionally escapes `closure_result_mismatch`, so cut-free closure evidence rides into a package that pins a cut and its declared result is never recomputed.
- **Why silent:** It reads as "an unset cut inherits the package's", the kind of defaulting a maintainer adds for convenience; `model.py` only requires `cut_id` to be a string, and no fixture leaves it empty, so the suite stays green (682 passed).
- **Note:** closure cut coherence (a closure is admitted only under the package's own cut)

```diff
- cut_valid = closure.cut_id == self.package.header.cut_id
+ cut_valid = closure.cut_id in {self.package.header.cut_id, ""}
```

### `source-rank-table-disagrees-with-model` — **SURVIVED**

- **Decision:** INV-deterministic-binding-order
- **File:** `src/poietics/binding/plan.py`
- **Reverses:** The single canonical draft-source order. plan.py's `_sorted_sources` and model.py's `_draft_kind_rank` (which BindingIssue uses to REJECT non-canonical `sources`) must agree; after this they disagree about CLOSURE versus EVIDENCE_REQUEST, so any diagnostic mixing the two is emitted in an order its own constructor refuses.
- **Why silent:** Nothing in the suite builds a BindingIssue whose sources mix a CLOSURE source with an EVIDENCE_REQUEST source -- COVERAGE issues are split by kind and the collision fixture pairs an atom with a rule -- so both tables stay green while silently disagreeing. The two-place agreement is stated nowhere and pinned by no test.
- **Note:** the deterministic _SOURCE_KIND_RANK ordering

```diff
- DraftRecordKind.CLOSURE: 2,
    DraftRecordKind.EVIDENCE_REQUEST: 3,
+ DraftRecordKind.CLOSURE: 3,
    DraftRecordKind.EVIDENCE_REQUEST: 2,
```

### `gen-body-literal-may-be-rule` — **SURVIVED**

- **Decision:** INV-draft-namespaces
- **File:** `src/poietics/generation/extract.py`
- **Reverses:** A body literal may now name a rule rather than an atom, so an untrusted draft can assert a rule as a premise of another rule — a program shape the draft schema's namespace typing refuses.
- **Why silent:** Same blind spot as the head case: c13 collapses all three namespaces onto one id, and no fixture points a positive literal at a rule. Full suite stayed green at 691 passed, and the edit looks like a symmetry fix applied alongside the head reference.
- **Note:** type-directed draft namespaces (test c13's named invariant): a rule's positive body literals resolve in the atom namespace only

```diff
- positive_issue = _reference_issue(
                reference,
                atom_ids,
                rule_ids | evidence_ids,
            )
+ positive_issue = _reference_issue(
                reference,
                atom_ids | rule_ids,
                evidence_ids,
            )
```

### `gen-rule-head-may-be-rule` — **SURVIVED**

- **Decision:** INV-draft-namespaces
- **File:** `src/poietics/generation/extract.py`
- **Reverses:** A language model may now emit a rule whose head names another rule; extraction admits it and materialises a DraftRule whose head DraftRef points at a rule record, which the type-directed namespace exists to refuse.
- **Why silent:** The namespace test (c13) deliberately gives one id to all three record kinds, so it cannot discriminate widened namespaces, and the draft_reference_kind fixtures never point a head at a rule. Full suite stayed green at 691 passed.
- **Note:** type-directed draft namespaces (test c13's named invariant): a rule head resolves in the atom namespace only

```diff
- head_issue = _reference_issue(
            rule.head,
            atom_ids,
            rule_ids | evidence_ids,
        )
+ head_issue = _reference_issue(
            rule.head,
            atom_ids | rule_ids,
            evidence_ids,
        )
```

### `pack-frame-policy-loosened` — **SURVIVED**

- **Decision:** INV-frame-policy
- **File:** `src/poietics/packs/empirical.py`
- **Reverses:** An atom no longer has to sit in the package's own frame — any nonempty frame is admitted — so records from a different comparison boundary can enter one fixed point, while the policy id still reads "frame:exact-package" and registry.version still reads 1, so REG-1's id-suffix check passes over a registry whose content now says the opposite of its name.
- **Why silent:** No test asserts the shipped pack registry's frame policy mode (only test fixtures construct their own EXACT_PACKAGE policies), and every record in the reference fixture carries FRAME, which satisfies both modes, so nothing in the suite ever exercises the difference.
- **Note:** the pack's frame policy `frame:exact-package` (FramePolicyMode.EXACT_PACKAGE), and REG-1's plainly stated hole: an author who edits registry content without bumping registry.version defeats the suffix check completely

```diff
- FramePolicy(
                frame_policy_id=FRAME_POLICY,
                version=1,
                mode=FramePolicyMode.EXACT_PACKAGE,
            ),
+ FramePolicy(
                frame_policy_id=FRAME_POLICY,
                version=1,
                mode=FramePolicyMode.NONEMPTY,
            ),
```

### `gen-evidence-subject-version-unpinned` — **SURVIVED**

- **Decision:** INV-generated-id-purity
- **File:** `src/poietics/generation/extract.py`
- **Reverses:** An evidence request may now name its subject rule at a different version than the rule that cites it, so the evidence/rule linkage stops being version-pinned and a draft can bind evidence to a version of a rule that is not the one in the package.
- **Why silent:** The subject_mismatch fixtures vary the subject's id, never its version alone, so the weakened comparison is never exercised; full suite stayed green at 691 passed. The edit reads as tolerating a harmless version drift inside one draft.
- **Note:** generated ids are pure functions of source ids and versions — draft references are pinned by (id, version), not by id

```diff
- elif request.subject.identity != users[0].identity:
+ elif request.subject.id != users[0].id:
```

### `ground-pff-atoms-exempt-from-universe` — **SURVIVED**

- **Decision:** INV-ground-closed-universe
- **File:** `src/poietics/ground/model.py`
- **Reverses:** The trusted-boundary refusal of out-of-universe references is switched off for exactly the namespace the compiler mints (`compile.py` builds atom refs as `__pff__:role(token)`), so a compiled rule may name an atom that is in no partition: it can never become live or excluded, its head silently suspends, and `status_of` raises KeyError for a reference the program was allowed to contain.
- **Why silent:** It reads as an obviously true remark -- compiler-generated atoms are synthesised downstream, so why would the author have declared them -- and no fixture anywhere puts a `__pff__:` reference into a GroundProgram, so the three missing-reference subtests in tests/test_ground_model.py still fail closed on their plain `missing` atom (verified: a rule with negative target `__pff__:blocked(x)` goes from refused to accepted).
- **Note:** ground programs reject references to unknown atoms; AU-4's `__pff__:` atoms are compiler artifacts

```diff
- unknown = referenced - atoms
        if unknown:
+ unknown = {
            ref
            for ref in referenced - atoms
            if not str(ref).startswith("__pff__:")
        }
        if unknown:
```

### `ground-rule-type-check-widened` — **SURVIVED**

- **Decision:** INV-ground-closed-universe
- **File:** `src/poietics/ground/model.py`
- **Reverses:** A GroundRule subclass that overrides `__post_init__` is admitted without its bodies ever being frozen or copied, so a caller keeps a live reference to a rule body and can add atoms to it after the program has been validated -- defeating both the immutability guarantee and the unknown-atom check that ran before the mutation.
- **Why silent:** `isinstance` is the idiomatic form and the exact-type test looks like an oversight; the one test guarding it (`test_rejects_mutable_duck_typed_rules`) uses a duck-typed class that is not a GroundRule at all, so it still raises TypeError (verified: a `Loose(GroundRule)` subclass keeps a plain `set` body, gains an undeclared atom after construction, and flips its head from LIVE to SUSPENDED).
- **Note:** trusted ground boundary: "rules must contain only immutable GroundRule records"; the validated universe is fixed at admission

```diff
- if any(type(rule) is not GroundRule for rule in frozen):
+ if any(not isinstance(rule, GroundRule) for rule in frozen):
```

### `certificate-why-gains-supported` — **SURVIVED**

- **Decision:** INV-no-status-inference
- **File:** `src/poietics/canonical.py`
- **Reverses:** The evaluation certificate -- whose own docstring says it carries no score, count, or confidence -- now derives a support claim from the fixed-point status and ships it inside the replayable bytes, which is precisely the inference no module may make.
- **Why silent:** It looks like a convenience for report consumers who do not want to walk the trace; the certificate's shape test asserts only the seven TOP-LEVEL keys and the no-score test screens that same top-level key set, so a forbidden term one level down inside `why` passes untouched -- 691 tests green.
- **Note:** the cross-cutting rule AU-7 names as binding every module: "No module SHALL infer truth, support, acceptance, confidence, or probability from the fixed-point status"

```diff
- "status": status,
        "conflict": conflict,
        "why": dict(why or {}),
+ "status": status,
        "conflict": conflict,
        "why": {**dict(why or {}), "supported": status == "LIVE"},
```

### `cli-evaluate-reports-acceptance` — **SURVIVED**

- **Decision:** INV-no-status-inference
- **File:** `src/poietics/cli.py`
- **Reverses:** The whole-package readout now names an `accepted` field computed from LIVE, turning a package-relative computational status into an acceptance verdict — exactly the field the schema invariant says does not exist, emitted by the one module the user actually reads.
- **Why silent:** The only guard on acceptance vocabulary (test_no_report_carries_an_acceptance_word) inspects `why` output alone; the evaluate document is only ever checked for keys it must contain, never for keys it must not, and it reads as a harmless convenience alias for downstream consumers.
- **Note:** "No module SHALL infer truth, support, acceptance, confidence, or probability from the fixed-point status" (core spec) and "No truth, acceptance, support, confidence, or probability field" (schema invariant); the cross-cutting rule AU-7 leans on

```diff
- "frame_id": package.header.frame_id,
        **partition,
    }
+ "frame_id": package.header.frame_id,
        "accepted": list(partition["atoms"]["live"]),
        **partition,
    }
```

### `conflict-view-says-supported` — **SURVIVED**

- **Decision:** INV-no-status-inference
- **File:** `src/poietics/explain/model.py`
- **Reverses:** The emitted vocabulary stops describing the conflict axis ("live and no live contrary") and starts asserting support: `pff why` prints `"conflict": "SUPPORTED"` and `evaluation_certificate` (which is handed `report.conflict.value`) certifies a LIVE atom as supported.
- **Why silent:** Every in-suite assertion compares enum identity (`assertIs(report.conflict, ConflictView.LIVE_UNCOUNTERED)`), never the value; the CLI's byte-level guard `test_no_report_carries_an_acceptance_word` searches for lowercase `"support`, which the uppercase enum value slips past — verified: the mutated tree emits SUPPORTED and 691 tests still pass.
- **Note:** the cross-cutting sentence: no module SHALL infer truth, support, acceptance, confidence, or probability from the fixed-point status

```diff
- LIVE_UNCOUNTERED = "LIVE_UNCOUNTERED"
+ LIVE_UNCOUNTERED = "SUPPORTED"
```

### `pack-transport-prefix-dropped` — **SURVIVED**

- **Decision:** INV-pack-independence
- **File:** `src/poietics/packs/empirical.py`
- **Reverses:** Transport arguments stop being prefix-typed, and — because tests/test_pack_independence.py computes its forbidden-token set FROM ARGUMENT_TYPES — the engine-wide guard silently stops looking for the literal "transport:" in any engine module, so an engine that hard-codes a pack prefix now passes.
- **Why silent:** The guard reads what it guards, so removing the prefix removes two of its tokens rather than failing it: the suite stays green and only the subtest count moves (2909 to 2863), and the vacuity control test_the_guard_catches_every_shape_of_violation only ever plants "component:", so the transport family has no control. The module's own comment ("Pack naming conventions; the specification constrains neither") invites the deletion.
- **Note:** milestone 8 pack independence — the engine SHALL contain no pack-specific token — together with the pack's ArgumentTypeContract prefix typing

```diff
- ArgumentTypeContract(
        argument_type_id=TRANSPORT, version=1, required_prefix="transport:"
    ),
+ ArgumentTypeContract(argument_type_id=TRANSPORT, version=1),
```

### `cli-replay-reorders-the-log` — **SURVIVED**

- **Decision:** INV-replay-fold
- **File:** `src/poietics/cli.py`
- **Reverses:** The command line now repairs the log before folding it, so a log that is not append-only folds as though it were: the contiguity refusal inside fold() is handed an already-sorted sequence, and order-dependent operations (a revocation arriving before the record it revokes) are silently rewritten into a legal order.
- **Why silent:** The only broken-log test writes a lone seq 3, a gap that sorting cannot repair, so it still exits with sequence_not_contiguous; no test in the suite feeds an out-of-order log, and the edit reads as ordinary tolerance for concatenated logs.
- **Note:** the append-only replay fold — "Fold the append-only log into a package"; ReplayCode.SEQUENCE_NOT_CONTIGUOUS is enforced inside fold(), not in parse_events()

```diff
- result = fold(
            events,
            cut=args.cut,
+ result = fold(
            sorted(events, key=lambda event: event.get("seq", 0)),
            cut=args.cut,
```

### `gen-capture-digest-unchecked` — **SURVIVED**

- **Decision:** INV-untrusted-boundary
- **File:** `src/poietics/generation/model.py`
- **Reverses:** A CapturedContent may now carry a digest that does not hash its own bytes, so the envelope's prompt/response digests stop attesting the captured bytes and become an unchecked claim that downstream replay and canonical-bytes consumers trust.
- **Why silent:** The digest is always computed by capture_generation, so no test ever constructs a CapturedContent with a mismatched digest through the factory; the mismatch fixtures in the extract tests plant the disagreement by other means. Full suite stayed green at 691 passed. It also reads as a performance edit (skip rehashing multi-megabyte captures) rather than a removal of a check.
- **Note:** prompt/response capture is immutable and self-attesting (the CAPTURE_DIGEST_MISMATCH contract in extract.py)

```diff
- if sha256 != _content_digest(data):
            raise ValueError("sha256 does not match data")
+ if not sha256.startswith("sha256:"):
            raise ValueError("sha256 does not match data")
```

### `gen-provider-error-ignored` — **SURVIVED**

- **Decision:** INV-untrusted-boundary
- **File:** `src/poietics/generation/ollama.py`
- **Reverses:** A provider reply carrying both an `error` and a `response` is no longer refused; it falls through to the shape checks and is captured as an ordinary successful generation, so failed provider work is recorded as a normal untrusted draft source.
- **Why silent:** Every provider-error fixture sends `error` alone, so the added conjunct is never false in the suite; full suite stayed green at 691 passed. The edit reads as tolerance for providers that attach a warning alongside usable output.
- **Note:** fail-closed at the untrusted boundary (ollama_provider_error refusal); a provider-errored attempt is not a draft source

```diff
- if "error" in values:
        error = values["error"]
+ if "error" in values and "response" not in values:
        error = values["error"]
```

### `gen-transport-retry-loop` — **SURVIVED**

- **Decision:** INV-untrusted-boundary
- **File:** `src/poietics/generation/ollama.py`
- **Reverses:** One AttemptRef can now consume two provider invocations, so a retry is folded silently into a single recorded attempt instead of being minted as a second attempt with relation=RETRY and a parent.
- **Why silent:** The suite's only guard on this is an AST count of syntactic `transport(...)` call sites in the module (`call_names.count("transport") == 1`), which a loop leaves at one, and no fixture drives status 503 (only 201, 429, 500 are tested); full suite stayed green at 691 passed.
- **Note:** adapter profile / transport-invoked-exactly-once; AttemptRelation lineage (RETRY is a separate, parented attempt)

```diff
- response = transport(transport_request)
    if type(response) is not OllamaTransportResponse:
        raise TypeError("transport must return an OllamaTransportResponse")
    _validate_transport_response(response)
+ for _attempt in range(2):
        response = transport(transport_request)
        if type(response) is not OllamaTransportResponse:
            raise TypeError("transport must return an OllamaTransportResponse")
        _validate_transport_response(response)
        if response.status != 503:
            break
```

### `integer-detail-accepts-bool` — **SURVIVED**

- **Decision:** INV-value-vocabulary
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** `CheckerDetailType` is documented as a "small deterministic value vocabulary" and the whole module holds the line with `type(x) is T` -- `_require_version` refuses `True` as a version, and the suite pins that refusal explicitly. Under `isinstance`, `True` satisfies BOTH `INTEGER` and `BOOLEAN`, so the vocabulary stops partitioning and a certificate's detail passes a shape check while carrying a value of the wrong declared type into the canonical bytes.
- **Why silent:** Verified green (691 passed): `isinstance` reads as the idiomatic spelling and is what a linter or a reviewer's habit suggests, and no certificate anywhere in the tree or the tests puts a bool in a field declared INTEGER, so the conflation has no witness.
- **Note:** exact-type value vocabulary: a bool is never an integer

```diff
- if self is CheckerDetailType.INTEGER:
            return type(value) is int
+ if self is CheckerDetailType.INTEGER:
            return isinstance(value, int)
```

### `selector-where-exempt-from-float-rule` — **SURVIVED**

- **Decision:** INV-value-vocabulary
- **File:** `src/poietics/canonical.py`
- **Reverses:** A closure record is a semantic record, and its selector's where mapping now accepts floats: verified that a closure with where={"min_confidence": 0.87} canonicalises to bytes containing 0.87 and hashes cleanly, so a confidence/probability enters the package hash through the one door the specification's float rule exists to shut.
- **Why silent:** It looks like the metadata exemption already argued for in _plain's docstring ('a selector where is registry-defined free-form data'), it changes no existing bytes because no fixture carries a float there, and the one float test in the suite plants its float in certificate.details -- so all 691 tests pass.
- **Note:** "Floating-point values SHALL NOT occur in semantic records" (the spec rule _plain enforces, whose ONLY accepted exemption is non-semantic metadata)

```diff
- def _dataclass(record: object, *, path: str) -> dict[str, Any]:
    return {
        field.name: _plain(getattr(record, field.name), path=f"{path}.{field.name}")
        for field in fields(record)
    }
+ def _dataclass(record: object, *, path: str) -> dict[str, Any]:
    return {
        field.name: _plain(
            getattr(record, field.name),
            path=f"{path}.{field.name}",
            semantic=field.name != "where",
        )
        for field in fields(record)
    }
```

### `ground-excluded-premise-still-supports` — **SURVIVED**

- **Decision:** INV-well-founded
- **File:** `src/poietics/ground/evaluate.py`
- **Reverses:** A rule whose positive premise is already EXCLUDED stops being disqualified as external support, so an atom whose only support runs through an excluded atom is no longer placed in the greatest unfounded set and comes back SUSPENDED instead of EXCLUDED.
- **Why silent:** The deleted guard looks redundant with the `rule.positive & unfounded` guard below it, because an excluded atom is normally also in the unfounded set; the only discriminating shape is a base-excluded atom that itself has a supporting rule, and no fixture in tests/test_ground_evaluate.py gives a base-excluded atom any rule at all -- all 691 tests and 2909 subtests stay green (verified: atoms {o,b,h}, o protected-open, b base-excluded, b:-o, h:-b flips h from EXCLUDED to SUSPENDED).
- **Note:** well-founded semantics: EXCLUDED must propagate through positive premises; SUSPENDED is not EXCLUDED

```diff
- if rule.positive & excluded:
                    continue
                if rule.negative & live:
                    continue
+ if rule.negative & live:
                    continue
```

### `ground-negative-block-requires-all-live` — **SURVIVED**

- **Decision:** INV-well-founded
- **File:** `src/poietics/ground/evaluate.py`
- **Reverses:** A single LIVE negative target no longer blocks a rule from counting as external support -- only a wholly live negative body does -- so a rule that is definitively dead still keeps its head out of the unfounded set and the head is reported SUSPENDED instead of EXCLUDED.
- **Why silent:** It reads as making the guard symmetric with `definitely_enabled`'s subset tests (`rule.negative <= excluded`), and the two spellings coincide whenever a rule has at most one negative literal, which is true of every negative-body fixture except one whose negative targets are all excluded (verified: atoms {n,m,h}, h :- not n, not m with n base-live flips h from EXCLUDED to SUSPENDED).
- **Note:** well-founded semantics: exclusion propagates through a definitively blocked negative body; EXCLUDED distinct from SUSPENDED

```diff
- if rule.negative & live:
                    continue
+ if rule.negative and rule.negative <= live:
                    continue
```

### `ground-partition-overlap-narrowed` — **SURVIVED**

- **Decision:** INV-well-founded
- **File:** `src/poietics/ground/model.py`
- **Reverses:** An Evaluation may now record one atom as both EXCLUDED and SUSPENDED (or LIVE and SUSPENDED), and `status_of` silently resolves the overlap in favour of whichever branch comes first -- the two statuses stop being disjoint at the type boundary, which is where the distinction is enforced for every caller that builds an Evaluation without going through `evaluate`.
- **Why silent:** It reads as dead-code removal: `evaluate` computes `suspended` as the complement of live and excluded, so those two disjunctions can never fire on its output, and every fixture reaches Evaluation through `evaluate`.
- **Note:** the three-valued result is a partition; SUSPENDED is genuinely distinct from EXCLUDED

```diff
- if live & excluded or live & suspended or excluded & suspended:
+ if live & excluded:
```

### `checker-id-version-incoherence-admitted` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** The same id-versus-declared-version coherence REG-1 accepted for registries, at the one other place the tree already enforced it: `materialised-selector/v1` is the checker whose semantics the admission core implements locally, and a certificate binds its checkers BY VERSION. Dropping the clause admits a contract whose id claims `v1` while its `version` field declares 2 -- an internally incoherent build artifact, which REG-2 says is exactly what must be refused where it is defined.
- **Why silent:** Verified green (691 passed): the surviving conjunct still locks the id to the semantics enum, so the check looks intact and merely de-duplicated; every shipped and test contract declares version 1, so nothing observes the removed clause.
- **Note:** REG-1

```diff
- if (
            declares_materialised_id != declares_materialised_semantics
            or (declares_materialised_semantics and self.version != 1)
        ):
+ if declares_materialised_id != declares_materialised_semantics:
```

### `reg1-discharge-vocabulary-grows` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** The v0.1 discharge-kind vocabulary is closed and the registry is its sole authority; `validate.py:1353` gates `discharge.kind` on `known_discharge_kinds` and nothing else. Widening it converts a REFUSAL at admission (`unknown_discharge_kind`) into an ADMISSION whose type-match merely compiles excluded -- a package the engine used to reject now enters the fixed point, with no registry version change.
- **Why silent:** Verified green (691 passed, and the one test that loops over `known_discharge_kinds` simply ran one more passing subtest): adding a name to a frozenset of strings looks like vocabulary housekeeping, and the added kind appears in no compatibility row, so every completeness cross-check in `__post_init__` still holds.
- **Note:** REG-1

```diff
- "passed_local_closure",
    }
)
+ "passed_local_closure",
        "compensating_transport",
    }
)
```

### `reg1-face-kind-vocabulary-grows` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** The core spec closes the face-kind list ("The allowed face kinds in v0.1 are: type, version, source, witness, frame, transport, grade, coverage, closure, interpretation, retention, localisation, recovery"), and `PFF_V01_FACE_KINDS` is the engine's sole carrier of that closure -- it gates `predicate.allowed_face_kinds` at registry definition, `face.kind` at admission, and `required_face_kind` on challenge target contracts. Widening it lets a registry author declare, and a package carry, a face kind v0.1 does not define, without any registry version change.
- **Why silent:** Verified green (691 passed): the constant is never compared against the specification's list by any test, and an unused member trips none of the subset checks in `__post_init__`, so the diff reads as one word added to a list of thirteen.
- **Note:** REG-1

```diff
- "retention",
        "localisation",
        "recovery",
    }
)
+ "retention",
        "localisation",
        "recovery",
        "provenance",
    }
)
```

### `reg1-rebut-becomes-dischargeable` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** The core spec's normative discharge compatibility table gives `rebut` NO admissible discharge kind ("none; a malformed rebuttal is blocked by a separate undercut"); this row edit makes a rebut dischargeable, at an unchanged registry_id and an unchanged registry.version -- the exact content drift REG-1's acceptance record names as the hole its id-suffix check cannot see.
- **Why silent:** Verified green (691 passed): the suite pins the `undercut` and `defect` rows exactly and nothing at all about `rebut`, and the shipped row is the one row whose value is an ABSENCE, so adding a member reads as filling in an oversight rather than contradicting a table.
- **Note:** REG-1

```diff
- DischargeCompatibility(challenge_kind="rebut"),
+ DischargeCompatibility(
        challenge_kind="rebut",
        admissible_discharge_kinds={"malformed_or_inapplicable"},
    ),
```

### `reg1-revoke-loses-explicit-retraction` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/registry.py`
- **Reverses:** The same normative table, in the direction the specification's safeguard sentence does not even mention: the sentence gates GROWTH ("may grow only through a registry version change"), so a SHRINK is unguarded twice over. An already-admitted package that discharges a revoke by explicit retraction silently flips its type-match atom from live to excluded at the same registry_id, version and package hash.
- **Why silent:** Verified green (691 passed): no test and no zoo instance drives a `revoke` discharge, so the row exists only as data; deleting a member reads as tidying a kind nobody uses.
- **Note:** REG-1

```diff
- challenge_kind="revoke",
        admissible_discharge_kinds={
            "successor_version_transport",
            "explicit_retraction",
        },
+ challenge_kind="revoke",
        admissible_discharge_kinds={
            "successor_version_transport",
        },
```

### `reg1-suffix-convention-last-component-only` — **SURVIVED**

- **Decision:** REG-1
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** The accepted convention -- "the id's suffix after the final `/` is a dot-separated sequence of non-negative integers whose LAST component is registry.version" -- becomes "whatever the last dot-component is, if it happens to be a number", so `pff-core+empirical/v0.1`, `.../draft.1` and `.../2024-06.1` are all admitted as declaring version 1. The one line REG-1 flagged for reversal is reversed without the record changing.
- **Why silent:** The last component is the one the convention is about, so testing only it looks like the same rule stated more directly; every shipped id is all-numeric, so no identifier moves and all 682 tests pass.
- **Note:** REG-1's flagged [C] convention, enforced by REG-3 at admission

```diff
- if components and all(part.isdigit() for part in components)
+ if components and components[-1].isdigit()
```

### `coverage-tolerates-unaccounted-closure-bindings` — **SURVIVED**

- **Decision:** RT-1
- **File:** `src/poietics/binding/plan.py`
- **Reverses:** The COVERAGE gate's exactness in the other direction: the plan is supposed to account for every bound identity, and this lets a policy smuggle in closure identities that belong to no draft rule, so the plan carries targets with no origin and no record.
- **Why silent:** Suite stays fully green; the only closure bindings any fixture supplies are the well-formed one-per-rule set, so RECORD_BINDING_EXTRA is never driven with a CLOSURE source. The edit reads as a narrow, defensible exemption for records the engine materialises itself rather than as a hole in the bijection.
- **Note:** RT-1 / the binder's source-to-record bijection

```diff
- extra_records = supplied_record_sources - expected_record_sources
+ extra_records = {
        record_source
        for record_source in supplied_record_sources - expected_record_sources
        if record_source.kind is not DraftRecordKind.CLOSURE
    }
```

### `origin-coherence-exempts-closures` — **SURVIVED**

- **Decision:** RT-1
- **File:** `src/poietics/binding/model.py`
- **Reverses:** The fourth coherence row RT-1 added -- (CLOSURE, RULE_BLOCKER_CLOSURE, DraftRecordKind.CLOSURE) -- stops being enforced, so a closure record's provenance edge may now claim any role and any draft source; the field's own comment says a record whose provenance the plan cannot account for is 'exactly what this layer exists to prevent'.
- **Why silent:** The guard for this is `test_only_three_rank_aligned_origin_triples_are_coherent`, which still enumerates only the pre-RT-1 ATOM/RULE/CERTIFICATE kinds and roles -- it never constructs a CLOSURE origin at all, so the exemption is invisible to it, and plan.py keeps building correct closure origins on its own.
- **Note:** RT-1 / BindingOrigin coherence

```diff
- if (self.target_kind, self.role, self.source.kind) not in coherent:
            raise ValueError("incoherent binding origin")
+ if self.target_kind is not RecordKind.CLOSURE and (
            self.target_kind,
            self.role,
            self.source.kind,
        ) not in coherent:
            raise ValueError("incoherent binding origin")
```

### `rt1-blocker-closure-accepts-none` — **SURVIVED**

- **Decision:** RT-1
- **File:** `src/poietics/pff/model.py`
- **Reverses:** RT-1 took `required` as a TYPED RecordRef, not RecordRef | None; this makes RuleRecord(..., blocker_closure=None) constructible, so a rule can again opt out of being blockable and the requirement survives only as a keyword the caller must spell.
- **Why silent:** It is the same None-tolerant shape FaceRecord.depends_on_version already has two dataclasses below, the field keeps its bare `RecordRef` annotation and its RT-1 comment (so the diff never touches anything that says 'required'), no construction site changes, and the suite stays at 691 passed -- the registry's existing rt1 mutation attacks the default, and nothing pins the runtime type.
- **Note:** RT-1

```diff
- if type(self.blocker_closure) is not RecordRef:
            raise TypeError("rule blocker_closure must be an exact RecordRef")
+ if self.blocker_closure is not None and (
            type(self.blocker_closure) is not RecordRef
        ):
            raise TypeError("rule blocker_closure must be an exact RecordRef")
```

### `rt1-closure-coverage-becomes-optional` — **SURVIVED**

- **Decision:** RT-1
- **File:** `src/poietics/binding/plan.py`
- **Reverses:** RT-1 was accepted as `required`, which the binder implements by demanding a CLOSURE identity binding for EVERY draft rule; intersecting the expected set with what the policy happened to supply restores exactly the `optional` reading RT-1 rejected, and with it the RT-1a admission domain the acceptance authorised deleting.
- **Why silent:** The whole suite stays green -- 691 tests, 2909 subtests -- because no test ever drives a policy that omits a rule's closure binding, so the RECORD_BINDING_MISSING path for CLOSURE sources is never exercised; a reader sees only 'do not demand bindings the policy did not offer', and the reversal shows up in production as a bare KeyError deep in rule construction instead of the fail-closed coverage diagnostic.
- **Note:** RT-1

```diff
- expected_record_sources = atom_sources | rule_sources | closure_sources
+ expected_record_sources = atom_sources | rule_sources | (
        closure_sources
        & {_record_source(binding) for binding in policy.record_bindings}
    )
```

### `rule-blocking-roles-become-face-nodes` — **SURVIVED**

- **Decision:** RT-1
- **File:** `src/poietics/explain/report.py`
- **Reverses:** `has-open-challenge-rule` and `rule-clear` are reported as FACE nodes keyed on the rule reference, so the graph shows a rule's blocker space as face-shaped — the wide reading RT-6 rejected — and those nodes silently lose their status, since only ATOM and RULE_CASE nodes carry one.
- **Why silent:** The comment above the constant says these roles are to a rule what has-open-challenge and clear are to a face, so mapping them to FACE reads as consistency housekeeping; `test_record_nodes_carry_no_status` is satisfied either way (a FACE node is *supposed* to have no status) and no test asserts the node kind or id of a rule-blocking atom — 691 passed.
- **Note:** RT-1/RT-2/RT-6 — the rule's own blockability atoms take the RULE's node kind, and a rule's blocker space and its faces' blocker spaces partition

```diff
- **{role: NodeKind.RULE_CASE for role in _RULE_BLOCKING_ROLES},
+ **{role: NodeKind.FACE for role in _RULE_BLOCKING_ROLES},
```

### `rule-block-effect-from-challenge-case` — **SURVIVED**

- **Decision:** RT-2
- **File:** `src/poietics/pff/compile.py`
- **Reverses:** Rule-target blocking stops depending on `open-challenge(c)` and derives straight from `challenge-case(c)`, so a discharged rule-target challenge blocks the rule forever -- the discharge no longer lifts the block, which is the only thing that makes RT-2's second route to rule applicability a lifecycle rather than a permanent verdict.
- **Why silent:** It reads as aligning the new rule-target route with the defect route that sits three lines above it, and the entire suite stays green (682 passed) because the only rule-target challenge driven through the real compiler is the undercut in `tests/test_zoo_rule_target_blocking.py`'s `COMPILER_CROSSCHECK`, which carries no discharge; every discharged rule-target instance is scored against the frozen hand-built twin instead.
- **Note:** RT-2 (the admitted rule-target route) / the challenge profile's discharge lifecycle

```diff
- positive=frozenset(
                    {
                        challenge_case
                        if effect_role is CompilationRole.DEFECT_EFFECT
                        else open_challenge
                    }
                ),
+ positive=frozenset(
                    {
                        challenge_case
                        if effect_role
                        in (
                            CompilationRole.DEFECT_EFFECT,
                            CompilationRole.RULE_BLOCK_EFFECT,
                        )
                        else open_challenge
                    }
                ),
```

### `role-binding-only-for-locally-evaluable-closures` — **SURVIVED**

- **Decision:** RT-6
- **File:** `src/poietics/pff/validate.py`
- **Reverses:** Every closure whose checker declares `LocalClosureSemantics.NONE` (supplied evidence, the registry default) stops being role-checked at all, so on that whole class a rule's blocker closure may be a closure over anything -- another rule's challenges, its own faces' challenges -- and a challenge's discharge closure may point anywhere: RT-6's narrow domain and DF-1's binding are simply not enforced there.
- **Why silent:** `local_evaluation is None` means "this checker has no code-owned semantics", which reads like "nothing here to check", and the helper's docstring already frames role diagnostics as dependent checks; every fixture closure uses `materialised-selector/v1`, which has semantics, so the suite stays green (682 passed).
- **Note:** RT-6 (narrow rule blocker domain) and DF-1's binding, via the profile's closure role binding

```diff
- return local_evaluation is None or local_evaluation.selector_supported
+ return local_evaluation is not None and local_evaluation.selector_supported
```
