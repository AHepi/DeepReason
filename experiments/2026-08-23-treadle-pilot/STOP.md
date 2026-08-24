# STOP 1 — the treadle source is not in the container

Raised: 2026-08-23, at the dr-spec-change boundary (REQUEST.md Q1).
Status: OPEN. No code changed; nothing synthesised.

## The decision, in one sentence

Every install requirement (R1, R2, R4, R5, R6) and every pilot rung
(R11-R18) is downstream of `treadle0.4.1.zip` and its `AGENT_INSTALL.md`,
which C2 makes the operator's to supply, and the file is not present.

## What was searched

    $ ls /mnt/attach            -> empty
    $ ls /mnt/user-data/working -> empty
    $ find / -iname '*treadle*' -not -path '*/proc/*'
      -> only this repo's own git refs for the branch name
    $ find / -iname '*.zip' -not -path '*/proc/*'
      -> only OS/toolchain fixtures (libreoffice, openjdk, go testdata)

## Why nothing may proceed under an assumption

R1 requires the vendored tree to be the shipped source "verbatim", and R2
requires a provenance header asserting version 0.4.1. A reconstruction from
the tranche instruction's description would satisfy neither, and would put
invented source into `tools/treadle/` under a provenance claim that is false
— the exact failure mode the vendoring deviation D1 exists to prevent. R6
(`treadle doctor`, pasted verbatim) and R16 (typed outcomes only) cannot be
met by a stand-in at all.

## Options, priced

A. Operator attaches `treadle0.4.1.zip` to this session.
   Cost: one upload. Unblocks R1-R19 in full; the tranche resumes at
   dr-spec-change with nothing lost.
B. Operator supplies a fetchable source (a URL the container's HTTPS proxy
   can reach, or a GitHub repo added to session scope via `add_repo`).
   Cost: one message. Same unblock, subject to the proxy allowing the host
   and to the fetched bytes being verifiably 0.4.1.
C. Split the tranche: land the governance half now (R7-R10 — the CLAUDE.md
   third-lane paragraph and the AUDIT_BASELINES.md entry), park the install
   and the pilot.
   Cost: a governance paragraph describing a lane that does not exist yet,
   and an AUDIT_BASELINES.md entry naming an instrument no audit can run.
   Both would be findings against this repo's own audit family the moment
   `dr-audit-broken` next runs.

Recommendation: A. B is equivalent if a URL is easier than an upload; C is
not recommended and is listed only so the fork is priced honestly.

## Work banked, so the resume is cheap

- REQUEST.md: operator's words ledgered R1-R19, C1-C7, Q1-Q4.
- Environment verified: branch `claude/treadle-install-pilot-fqwjt5` off
  `origin/main` with `5d9b995ce` confirmed an ancestor; `pip install -e .`
  and pytest/pytest-xdist/jsonschema installed; `deepreason` on PATH.
- T1's acceptance target confirmed against the live tree, not assumed:
  `python tools/docs_verify.py` -> `63 documents, 994 checks` /
  `docs_verify: 3 failed`, all three `CON-run-identity.md` git-history
  checks (lines 200, 202, 204) failing for the shallow clone. This matches
  `docs/AUDIT_BASELINES.md` exactly, so R11's "names the 3 pre-existing
  failures" has a known-correct answer to score the driver against.
- Frozen-surface list read in full (`DR-INV-frozen-surfaces`) for R10; the
  five surfaces are `capabilities/state.py`, `harness.py`, the
  replay-validation formats (`invariants.py`, `verification/`),
  `run_manifest.py` schemas AND validators, and anything altering
  qualification subject digests (`qualification.py`), plus the
  frozen-adjacent `route_fingerprint` in `llm/firewall.py`. No pilot cone
  as described in the instruction reaches any of them: T1 and T3 cone to
  `experiments/2026-08-23-treadle-pilot/*`, T2 is read-only over a
  delivered tranche, T4 is read-only over one doc claim and its code.
- Name-collision check for D2 done in advance: the repo has no root
  `skills/` directory and no `treadle.toml` today, so the shipped tree
  lands without collision against `.claude/skills/`.

## Credential note

The API key was pasted in plaintext in the tranche instruction. It has not
been written to any file, committed, or echoed into any log by this session,
and per C2 it will live only in a gitignored env file at the run step. The
operator may wish to rotate it after the pilot regardless, since it now
exists in a chat transcript.
