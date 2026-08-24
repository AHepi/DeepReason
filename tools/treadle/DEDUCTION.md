# Deduction under treadle 0.3.0 -- ONE package, no second install

Everything ships INSIDE this treadle zip (repo-assets/); nothing else to
pip-install. Kimi: this supersedes 0.2.1 -- unzip over the same install.

## Apply (exact)

    unzip -o treadle-0.3.0.zip -d ~/tools/
    cd ~/tools/treadle
    python3 -m venv .venv && . .venv/bin/activate || true   # some sandboxes cannot
    # create venvs (no symlink support); in that case install without one:
    pip install -e ".[dev]"          # console script lands in ~/.local/bin if no venv
    pytest -q                        # `python3 -m treadle` also works from 0.4.0                                  # must print: 19 passed
    cd /path/to/target-repo
    cp ~/tools/treadle/repo-assets/derivation_check.py scripts/
    mkdir -p zoo/derivations rules
    cp ~/tools/treadle/repo-assets/DERIVATION_FORMAT.md zoo/derivations/FORMAT.md
    cp -r ~/tools/treadle/repo-assets/skills/deduction skills/
    # append the [stage.deduction] block + DED- routing from
    # repo-assets/treadle.toml to the repo's treadle.toml
    cp -r ~/tools/treadle/repo-assets/derivations-example rules/example/
    python3 scripts/derivation_check.py rules/example/rules.json \
        rules/example/theory.json rules/example/example-derivation.json
    # must print: RESULT: PASS (4 step(s) replayed; conclusion matches target)
    git add scripts zoo rules skills treadle.toml && git commit -m "build: deduction stage (treadle 0.3.0)"

## Before any real proof-search task: author rules/rules.json

The checker is rule-AGNOSTIC: the rule system is data. Transcribing the
frozen calculus's inference rules into DERIVATION_RULES_V1 is a reviewed
task, not a formality:
- one board task, cone rules/rules.json, the frozen calculus doc as
  read context; acceptance = a schema lint plus checker replay of one
  known-good hand derivation;
- side conditions you cannot express in the pattern language become
  {"kind": "MANUAL", "text": "..."} -- the checker returns
  CANNOT_VERIFY for those steps and strict acceptance fails, which is
  correct: a rule transcript is not authority until the owner reviews
  it (round-trip it like a pin);
- until that review, a PASS certifies conformance to the TRANSCRIPT,
  not to the calculus. Say so in any record that cites it.

## Task shape

    python3 scripts/swarm_gate.py add DED-T7 \
      --goal "Derive row T7 from the frozen rule system" \
      --cone "zoo/derivations/T7.json" \
      --base $(git rev-parse HEAD) \
      --accept "python3 scripts/derivation_check.py rules/rules.json rules/theory.json zoo/derivations/T7.json" \
      --out-of-scope "no rule edits, no theory edits, no record edits"

Closure recomputation and ledger emission stay deterministic tasks (no
model); a model's CANNOT_DERIVE is never evidence of non-derivability --
that claim belongs to jacquard's countermodel search.
