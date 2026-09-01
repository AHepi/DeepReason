# Model profiles — reference copies

These are documents a human wrote about a model. **The harness does not read
this directory.** It reads exactly one place:

    $DEEPREASON_HOME/model-profiles/<model-id>/agent.md
    (or ~/.deepreason/model-profiles/<model-id>/agent.md when DEEPREASON_HOME
    is unset)

Operator, 2026-09-01, deciding it: *"Home directory only, nothing ships"*. So a
fresh container knows nothing about any model, every seat runs with the
reasoning knob omitted, the split-budget protocol stands down with a typed
notice, and the run's record stamps a registry with zero profiles in it. That
is the designed state, not a gap — the harness is not supposed to hold an
opinion about a model it was not given.

Installing one is a human act, and one command:

    cp -r docs/model-profiles/glm-5.3 "${DEEPREASON_HOME:-$HOME/.deepreason}/model-profiles/"

To see where the harness is looking and what it found:

    python -c "from deepreason.model_profiles import profiles_root, registry_fingerprint; print(profiles_root()); print(registry_fingerprint())"

## What a document may say

Prose, freely — the harness ignores all of it — around exactly one fenced
block whose info string is `deepreason-model-profile-v1`. Zero blocks, two
blocks, or an unclosed block is a typed error rather than a guess.

The declared `model_id` inside the block is the key. The directory name is a
convenience, so a provider's own spelling (`gpt-oss:120b`) never needs escaping.

Absence stays absent: every field but `schema`, `model_id` and `measured_on` is
optional, and the loader supplies nothing the author did not write. Where the
committed record does not measure something, the field is LEFT OUT rather than
filled from memory — several are left out below for exactly that reason, and
`docs/map/CON-model-profiles.md` says why that matters.

## What the harness actually acts on

Only two fields reach the wire, and only where the harness would otherwise have
had to invent a value:

- `reasoning.extraction_value` — what the split protocol's emission leg sends.
- `reasoning.disabling_values` — whether a configured value really stops this
  model thinking, which is what decides whether `auto` splits this seat at all.

Everything else is read by a human or by the probe. **Nothing here can veto a
configured value.** Operator, 2026-09-01: *"Harness is supposed to accommodate
all possible future models and configurations."* A `reasoning:` setting your
run config names travels to the provider exactly as written, whatever these
documents say; where a document disagrees with it, you get a disclosure on
stderr and the run proceeds.
