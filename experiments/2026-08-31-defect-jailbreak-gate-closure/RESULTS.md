# Results — closing the jailbreak gate (F9)

## 2026-08-31 — the security clause of the 2026-08-29 P2 law is met

**What the record now shows.** On committed root
`experiments/2026-08-27-pc2b-symmetric-reasoning/run`, flipping one byte of the
first recorded provider endpoint — same length, so nothing but a replay can see
it — used to buy the whole operator sequence: `amend` committed epoch 1 and
`continue` then accepted `seq=0`, while the root's own `REPLAY_VALIDATION.json`
still published `valid: true`. It now buys neither. Both verbs refuse typed and
name the two failed checks, and an intact copy of the same root still accepts
both. `proof/RED-forge_amend_ready.txt` -> `proof/GREEN-forge_amend_ready.txt`;
`jailbreak_open: True` -> `False`.

Full gate 4599 passed / 0 failed. docs_verify 5 failed, all on the recorded
baseline list, no delta. `--audit` 1 finding, the parked one. Wheel smoke green
with MCP schemas unchanged.

**What made this tranche different from the one that failed.** The 2026-08-30
tranche built this gate, watched it work on the tamper proof, then watched it
turn EIGHT lifecycle tests red where its spec predicted one, and reverted it. It
did not fail for lack of care; it failed because `verify_root`'s full violation
set answers a broader question than the operator's law, and three of the eight
collisions assert roads that REPAIR an invalid record — a staged amendment
mid-recovery, a bound but unintroduced source. Gating on the whole verdict
strands exactly the roots the recovery paths exist for.

So the question was narrowed, to the SECURITY channel, and the narrowing was
MEASURED before a line was written: with a security-only gate enforced at both
verbs, the eight collision node ids ran `8 passed`, the gate reached 34 times,
zero security findings anywhere; independently, the three amend-path files ran
`65 passed` with the gate evaluated 48 times and refused 0. With the gate armed
for real rather than simulated, the eight ran `8 passed in 580.95s`.

**The road not taken, and why the measurement mattered.** The obvious
implementation is the public accessor `verify_root_report(root).security_valid`
— no private import, three existing precedents in `src/`. It was rejected on
measurement. On the largest committed root
(`experiments/2026-08-12-live-grounded-extension-expansion/run`, 12,991 events)
`verify_root` reports ZERO violations while the report reports 495 SECURITY
findings, 494 of them `transaction-authority: ... unknown v6 task kind
'defended_trial_step'` from its DERIVED stream. That is version skew under the
2026-08-14 law that old runs owe the future nothing — not tampering. A gate on
that accessor refuses a lawful root, which is the "right but breaks lawful
continues" failure mode this tranche was told not to repeat. It also costs 2x
(668.26 s vs 356.76 s on that root) for no extra coverage of the thing being
gated. The two surfaces are kept from drifting by a committed test rather than
by comment: the gate's answer must equal the report's legacy-source security
findings.

**Accepted does not mean true.** Four things this tranche did NOT prove.

1. That the gate catches every tamper. It catches tampers that surface on
   `verify_root`'s legacy security stream. Whether a tamper exists that produces
   ONLY derived-channel findings is unmeasured (PARKED P1).
2. That a record too corrupt to replay is refused. It is not — `verify_root`
   returns `open` on the integrity channel and the gate passes it. Whether such
   a root is continuable at all was not measured (PARKED P2).
3. That the gate is affordable everywhere. It is one `verify_root` per verb:
   ~30 ms/event, linear, 5.9 minutes on the largest committed root. It is paid
   even when the root would be refused for an unrelated reason, which took
   `tests/test_continuation.py` from under a minute to 562 s serial and pushed
   three `SUB-application.md` map checks past docs_verify's own 300 s per-check
   ceiling. Those checks were narrowed to the claims they actually test — the
   gate was not weakened and no test root was exempted — but the underlying
   waste is real and the operator-facing version of it is a slower refusal
   (PARKED P3).
4. That the gate should be un-switchable. That is a READING: the 2026-08-28 law
   says "gates are always optional: with warnings", and this one is not
   optional, on the ground that the 2026-08-29 law calls it a security boundary.
   Recorded so it can be overruled in one line.

**One thing worth carrying forward, independent of this gate.** The mutation
proof's fourth arm widens the channel filter back to every violation and kills
the collision guard. The narrowing — the single decision this tranche turned on,
and the one the previous tranche got wrong — is therefore defended by a
committed test. A future tranche that "simplifies" it fails that test instead of
rediscovering eight red lifecycle tests the expensive way. The general form: when
a tranche's whole value is a distinction, make the distinction's collapse a test.

**Errata raised.** E66 (`gate_collisions.md`'s collision table names the wrong
check set for row 2; the related claim that a v1 manifest makes `verify_root`
RAISE is wrong in the same direction; its "What DID ship" table is superseded).
E67 (`AUDIT_BASELINES.md`'s docs_verify totals and its two `SUB-application`
line-number anchors had drifted before this tranche touched them — re-anchored
by what each check runs, and the CONTAINER-CONDITIONAL row retired, since the
same narrowing took it from 160-213 s to 1 s).
