# Fix: activate the loopback fixture by a `.pth` import instead of the claimable name `sitecustomize`

Guarantee restored: **the operational smoke's provider fixture starts in
the installed venv regardless of whether the host Python already ships a
`sitecustomize` module.**

## Change sites (exhaustive)

1. `scripts/wheel_operational_smoke.py`, `_install_loopback_fixture`
   (~lines 1313-1317): stop copying the fixture to
   `purelib / "sitecustomize.py"`, where any distribution-supplied
   `sitecustomize` earlier on `sys.path` silently wins the name. Copy it
   to a distinctive module name in purelib and write a companion `.pth`
   file whose single `import` line activates it. `site` executes EVERY
   `.pth` in EVERY site directory, so there is no winner-takes-all name
   to lose. Return the module path, keeping the caller's containment
   assertion (`environment.resolve() not in fixture_path.resolve().parents`)
   meaningful and unchanged.

That is the whole fix: one function, both files it writes are inside the
disposable venv, and the fixture body is copied byte-for-byte as before.

## Why this mechanism

Proven on this container before being proposed, in the `--keep` venv
that reproduces the defect:

    sitecustomize still the distro one: /usr/lib/python3.11/sitecustomize.py
    fixture module imported via .pth  : True
    listener: UP  <-- shadowing defeated

The distro keeps the `sitecustomize` name; the fixture no longer needs
it. `.pth` activation is the same mechanism coverage.py and similar
tools use for exactly this reason.

## Regression artifact

`experiments/2026-08-05-fix-loopback-fixture-daemon/repro.py` — its
structural half still reports the dead `_provider_server` (unchanged by
this fix; see Explicitly not changed) and its behavioural half still
shows the fixture body serving. The inversion to demonstrate is the
instrument's own exit code: `python -u scripts/wheel_operational_smoke.py`
from rc=1 (`stage: qualify`, `failure_kind: timeout`) to rc=0.

New conditions this fix must be tested against:

1. **The listener must come up in the real smoke**, not only in the hand
   -built probe — i.e. the run must proceed PAST `STAGE_QUALIFY`, which
   it has never done on this container.
2. **`wheel_smoke.py` must stay green**, since it shares neither the
   fixture nor the venv but does share the repo.
3. **`tests/test_wheel_operational.py` must stay green unedited.** Its
   `test_diagnostic_installation_wraps_exact_current_source_seams`
   bootstraps the fixture as `sitecustomize.py` on its OWN `PYTHONPATH`,
   which precedes `/usr/lib`, so it is independent of the install
   mechanism this fix changes. If it fails, this fix is wrong.

## Existing tests at risk

`grep -rn "sitecustomize" tests/` → one file,
`tests/test_wheel_operational.py`, at lines 32, 34, 257, 268. All four
refer to the SOURCE path (`scripts/wheel_loopback_sitecustomize.py`) or
to a test-local `bootstrap/sitecustomize.py` on an explicit
`PYTHONPATH`. None asserts on the name the smoke installs into purelib.
The file's 108 tests passed before this change and must pass unedited
after it.

## Explicitly not changed

- **`scripts/wheel_loopback_sitecustomize.py` itself** — not renamed,
  not edited. It is the source of the fixture body, which is correct;
  only its INSTALLED name and activation change. Renaming the source
  would touch the four test references above for no behavioural gain.
- **`_provider_server` / `ProviderState`** — genuinely dead code
  (DIAGNOSIS.md, AST over all 14 commits), and genuinely NOT the
  fixture in use. Deleting them is a cleanup, not this defect, and
  removing ~70 lines while fixing a hang would obscure which change
  made the smoke pass. PARKED.
- **`_run`'s discard of child output on `TimeoutExpired`** — the
  concealment mechanism that made this defect take three tranches to
  name. It is a real defect and it is NOT the cause of the failure; the
  end state the operator asked for is reached without it. PARKED with a
  strong recommendation, because the next fixture failure will hide the
  same way.
- **`_unused_loopback_port`'s bind-then-release** — a latent race
  (another process may take the port between release and the child's
  bind). Not implicated here: the port was free and simply never bound.
  PARKED.
- **`src/` — nothing.** The evidence never implicated the product. The
  operator's suspect window (provider-profile and config surfaces) is
  ruled out: no request ever reached the fixture.

## Estimated diff

~8 lines in 1 file. Far under the 150-line budget.

## Approval gate

GOAL.md class is `defect`; estimate ≤150 lines; no frozen surface (the
change is confined to `scripts/`, and the five surfaces are all under
`src/`). **Proceeds to `dr-implement-fix`.**
