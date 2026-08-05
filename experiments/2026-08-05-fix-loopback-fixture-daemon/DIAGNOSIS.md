# Diagnosis: SUPERSEDED — see "Correction" below

**This document named the wrong primary cause and is corrected in place
rather than rewritten, because the wrong turn is itself evidence about
how this defect hides.** The original text is preserved unchanged below
the correction.

## Correction (2026-08-05, same tranche, before any fix)

`_provider_server` and `ProviderState` in
`scripts/wheel_operational_smoke.py` ARE dead code — that finding
stands, and every measurement supporting it is reproducible. But they
are **not the fixture the smoke actually uses**, so their deadness is
not the defect.

The live mechanism is `_install_loopback_fixture` (called at line 3039),
which copies `scripts/wheel_loopback_sitecustomize.py` into the
installed venv's `purelib` as `sitecustomize.py`. Python imports that on
every interpreter start in the venv, and its `_start_if_enabled()`
(line 1224) binds `DEEPREASON_WHEEL_LOOPBACK_PORT` and starts a
`serve_forever` daemon **inside the `deepreason` child process** — not
inside the smoke process. So the smoke process legitimately has one
thread and no sockets; that observation never implied a dead fixture.

Verified directly: with the fixture env set and the sitecustomize on the
path, a bare `python -c` binds the port and the listener answers —
`listener UP inside the process: sitecustomize started it`. The
sitecustomize is sound in isolation.

**What that leaves, and why the exception was invisible.** The provider
runs in the child, so the only place its failure can surface is the
child's stderr — and `_run` discards exactly that. On
`subprocess.TimeoutExpired` (line 1475) it raises
`OperationalSmokeFailure(stage=..., failure_kind=FAILURE_TIMEOUT,
timeout=True) from None`, never reading `TimeoutExpired.stdout` or
`.stderr`, which carry the partial child output. A `sitecustomize.py`
that raises prints its traceback to that stderr and lets the
interpreter continue — producing precisely the observed shape: no
listener, connection refused, retry backoff, 600s timeout, and a typed
record that names the stage and nothing else.

So the operator's instruction — "capture the thread's actual exception
first" — could not be satisfied from the smoke's own output, because
the instrument throws that exception away. Obtaining it requires
re-running the child by hand against a `--keep` venv, which is the next
step and is where the real primary cause will be named.

## Primary cause, NAMED (2026-08-05)

**The fixture's `sitecustomize.py` is shadowed by the distribution's
own, so it is never imported and its server never starts.**

`_install_loopback_fixture` copies the fixture to the venv's purelib as
`sitecustomize.py` and relies on `site` importing it at interpreter
start. Debian/Ubuntu images ship their own
`/usr/lib/python3.11/sitecustomize.py` (here a symlink to
`/etc/python3.11/sitecustomize.py`), and in the venv's `sys.path` that
directory sits AHEAD of purelib. `import sitecustomize` therefore
resolves to the distribution's file; the fixture's copy is never
executed, `_start_if_enabled()` never runs, no listener binds, every
provider call is refused at TCP, the qualification workers back off, and
the stage exhausts its 600-second timeout.

Measured in the `--keep` venv:

    $ ls -la /usr/lib/python3.11/sitecustomize.py
    lrwxrwxrwx ... -> /etc/python3.11/sitecustomize.py

    sys.path in the venv:
      [2] /usr/lib/python3.11        <-- distro sitecustomize
      [4] .../site-packages          <-- venv purelib (fixture copied here)

    $ python -c "import sitecustomize; print(sitecustomize.__file__)"
    /usr/lib/python3.11/sitecustomize.py          # the distro's, not ours

    in-process, with the full fixture env set:
      sitecustomize imported : True
      ENABLE env in-process  : '1'
      PORT env in-process    : '54173'
      _ACTIVE_SERVER present : False
      _start_if_enabled      : AttributeError -- module has no such attribute
      listener               : DOWN -> [Errno 111] Connection refused

The `AttributeError` is the decisive line: the module that got imported
under the name `sitecustomize` is not the fixture, and has none of its
symbols.

**No exception is raised anywhere**, which is why stderr was empty at
every level and why the concealment described above mattered so much.
Nothing failed; the wrong file simply won a name collision.

Implicated code (1 site):

- `scripts/wheel_operational_smoke.py`, `_install_loopback_fixture`
  (~line 1296) — `target = purelib / "sitecustomize.py"`, an activation
  mechanism that assumes the name is unclaimed.

Falsifiable prediction (what `dr-reproduce` must show):

    # Installing the same fixture body under a mechanism that cannot be
    # shadowed -- a .pth file, which `site` executes for EVERY site
    # directory rather than importing one winner by name -- must bring
    # the listener up in the venv on this same container:
    import sitecustomize -> still the distro's file (unchanged)
    listener on the profile port -> UP, answers /v1/chat/completions

Ruled out, in order:

1. **The operator's suspect window** — "the fixture may be choking on a
   request shape it predates". No request shape is involved: the
   connection is refused at TCP before any protocol is exchanged, and
   the fixture body serves a realistic schema-bearing request correctly
   when reached (REPRO.md). Nothing the rung program changed is
   implicated.
2. **This document's own first answer** — that `_provider_server` being
   dead code was the cause. It IS dead code, but it is not the fixture
   in use; see the Correction above.
3. **The container cannot serve loopback HTTP** — a control server binds
   and answers immediately.

**Correction to the previous tranche and to this document's original
corollary:** I wrote that "the operational smoke has never passed". That
is wrong, and the shadowing explains why. The failure is
environment-dependent: it appears on Debian-family images that ship a
distro `sitecustomize`, and NOT on runners whose Python has none — which
includes GitHub Actions' `setup-python`, macOS and Windows. So the smoke
can very well have run clean on 2026-07-27 elsewhere, exactly as the
operator recalled, while being unable to pass in this container. The
operator's memory was right and my corollary was wrong.

---

# ORIGINAL (superseded) — preserved as written

# Diagnosis: the loopback provider is dead code — `_provider_server` has never been called, in any commit

Primary cause: `scripts/wheel_operational_smoke.py` defines the entire
embedded provider fixture — `ProviderState` and `_provider_server`,
which constructs the `ThreadingHTTPServer` and starts the
`serve_forever` daemon — and **never calls either of them, at any point
in the file's history**. `main()` reserves a port number with
`_unused_loopback_port()` (which binds `port 0`, reads the assigned
number, and immediately CLOSES the socket), writes that number into the
provider profile as `http://127.0.0.1:<port>/v1`, and then proceeds to
`setup` and `qualify` without ever binding it. Every provider call from
the installed wheel is therefore refused, the qualification workers
enter their connect-retry backoff, and the stage exhausts its 600-second
subprocess timeout.

The daemon thread did not die. **It was never started.**

Evidence:

- **The daemon's stderr, captured as instructed, is EMPTY** (0 bytes
  across a full `--keep` run to timeout). That absence is the finding,
  not a gap in it: `ThreadingHTTPServer` reports handler failures
  through `handle_error` and a dying `serve_forever` thread surfaces
  through `threading.excepthook`, both to stderr. No exception was
  recorded because no thread existed to raise one.
- **AST over the whole file history — 14 commits, creation to HEAD —
  gives `calls=0 name_refs=0` at EVERY commit**, and
  `ProviderState()` instantiations = 0 likewise. The symbol appears
  exactly once in the file today (`grep -c` → 1): its own `def`.
- **The file was CREATED already broken.** `git log --diff-filter=A`
  names one commit, `82c73367` ("WIP: checkpoint blocked clean-wheel
  qualification", 2026-07-23), adding 1045 lines and removing 0. The
  fixture has been unreachable since the line that wrote it.
- **The runtime state matches exactly.** The smoke process holds one
  thread and zero sockets at 206s elapsed; nothing listens on the
  profile's endpoint (`[Errno 111] Connection refused`, no
  `/proc/net/tcp` LISTEN entry); the `qualify` subprocess holds 2s of
  CPU against 175s elapsed with its four workers in
  `hrtimer_nanosleep`. A control `ThreadingHTTPServer` in the same
  container was reachable immediately, so the container is not at
  fault.
- **The port function itself is a release-then-hope pattern.**
  `_unused_loopback_port` (lines 1274-1277) exits its `with` block,
  closing the listener, and returns the bare integer — so even a
  correctly-wired call site would be binding a port it had already let
  go. Recorded because it shapes the fix.

Implicated code (2 sites):

- `scripts/wheel_operational_smoke.py:1178-1248` — `_provider_server`,
  defined and never referenced.
- `scripts/wheel_operational_smoke.py:2978` — `provider_port =
  _unused_loopback_port()` in `main()`, the place where the server
  should be constructed and started and is not.

Falsifiable prediction (what `dr-reproduce` must show):

    # Importing the smoke module and calling the dead function directly
    # must produce a LIVE listener that answers the provider protocol,
    # proving the fixture is correct and merely unreachable:
    _provider_server(ProviderState(...)) -> server bound, thread alive
    POST /v1/chat/completions            -> 200 with a usable completion

If that holds, the fixture body is sound and the defect is exactly the
missing wiring, so the fix is to call it — not to rewrite it.

Ruled out: **the operator's suspect window.** The instruction offered
"the fixture last ran clean 2026-07-27, and the rung program changed
provider-profile and config surfaces since — the fixture may be choking
on a request shape it predates." The record refutes this in both
halves. The fixture cannot have run clean on 2026-07-27, because
`_provider_server` had zero call sites on that date and on every other
date in the file's history; and it cannot be choking on any request
shape, because no request has ever reached it — the connection is
refused at TCP, before a single byte of protocol is exchanged. Nothing
the rung program changed is implicated. This was checked first and
directly rather than assumed away, per GOAL.md's method constraint.

Corollary worth stating plainly: **the operational smoke has never
passed.** `.github/workflows/wheel-smoke.yml` has run it as a required
step since `82c73367`, so that CI job has been unable to succeed for
the whole time the file has existed. The previous tranche's S1 wrote
that "the `serve_forever` thread had exited"; that reading was wrong in
its mechanism while right in its observations, and is corrected here.
