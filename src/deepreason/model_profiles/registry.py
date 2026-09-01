"""Where a model's document is found, and what the run's record says about it.

The operator decided both halves on 2026-09-01, verbatim: the document is
``model-profiles/glm-5.3/agent.md``, and it lives in "Home directory only,
nothing ships".  So this module knows one root -- ``$DEEPREASON_HOME/
model-profiles/``, else ``~/.deepreason/model-profiles/`` -- and the installed
package carries no document of its own.  A fresh container therefore knows
nothing about any model, which is the requirement rather than a gap: the
harness is not supposed to have an opinion it was not given.

Three dispositions, and the difference between them is the whole point:

* a model with a document RESOLVES;
* a model with no document resolves to ``None`` -- never an exception, on any
  path (the all-configurations law, 2026-08-12: disclose, never refuse);
* a document that cannot be read, or two documents claiming one id, becomes a
  recorded PROBLEM and the model stays unknown.  It is never swallowed.  A
  loader that caught and continued would make a typo and an absence look the
  same, and the typo is the one a human needs told about.

``registry_fingerprint`` is what the run's record stamps
(`DR-CON-model-profiles`).  It carries identity only -- no wall-clock and no
counter -- so two runs over the same documents stamp byte-identical values and
any difference between two stamps is a difference in the documents themselves.
That is the rule ``module_events.py`` states for every registry it carries, and
this one obeys it rather than inventing its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from deepreason.model_profiles.document import (
    ModelProfileError,
    ModelProfileV1,
    parse_document,
)
from deepreason.provider_profile import provider_state_dir

# Versioned as a whole under the signal contract's VERSIONED layer
# (`DR-INV-signal-contract`): a change to what a declared field MEANS is a
# versioned change; which documents a given home holds is FREE configuration.
MODEL_PROFILE_REGISTRY_VERSION = "model-profiles.v1"

PROFILES_DIRNAME = "model-profiles"
DOCUMENT_FILENAME = "agent.md"

# In-process registrations, for tests and for a plugin that sources documents
# from somewhere this module does not know about.  Deliberately NOT persisted:
# writing a profile from code is the thing this whole concept retires, so the
# only way a document reaches disk is a human putting it there.  A registration
# is marked `registered` rather than `document` in the fingerprint, so a run's
# record always says which profiles a human actually wrote.
_REGISTERED: dict[str, ModelProfileV1] = {}


def profiles_root(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """The one directory the harness looks in."""

    return provider_state_dir(home=home, environ=environ) / PROFILES_DIRNAME


def register(profile: ModelProfileV1) -> None:
    """Register one profile for this process only.  Writes no file."""

    _REGISTERED[profile.model_id] = profile


def unregister(model_id: str) -> None:
    """Drop an in-process registration.  Unknown ids are a no-op."""

    _REGISTERED.pop(model_id, None)


def _load(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[dict[str, ModelProfileV1], list[dict[str, str]], dict[str, str]]:
    """Every document under the root, plus every problem found reading them.

    Returns ``(profiles, problems, sources)``.  Nothing here raises: a caller
    on the dispatch path must be able to ask about a model without a broken
    document three directories away taking its run down.
    """

    profiles: dict[str, ModelProfileV1] = {}
    problems: list[dict[str, str]] = []
    sources: dict[str, str] = {}
    claimed: dict[str, str] = {}

    root = profiles_root(home=home, environ=environ)
    try:
        candidates = sorted(root.glob(f"*/{DOCUMENT_FILENAME}"))
    except OSError as error:
        problems.append(
            {
                "code": "MODEL_PROFILE_ROOT_UNREADABLE",
                "path": str(root),
                "detail": str(error),
            }
        )
        candidates = []

    for path in candidates:
        try:
            profile = parse_document(path.read_text(encoding="utf-8"))
        except ModelProfileError as error:
            problems.append(
                {"code": error.code, "path": str(path), "detail": str(error)}
            )
            continue
        except OSError as error:
            problems.append(
                {
                    "code": "MODEL_PROFILE_UNREADABLE",
                    "path": str(path),
                    "detail": str(error),
                }
            )
            continue
        if profile.model_id in claimed:
            # Choosing between them silently would make the record's stamp a
            # claim about which document answered that nobody could check.
            problems.append(
                {
                    "code": "MODEL_PROFILE_DUPLICATE_ID",
                    "path": str(path),
                    "detail": (
                        f"{profile.model_id!r} is declared by both "
                        f"{claimed[profile.model_id]} and {path}; it resolves "
                        "to neither"
                    ),
                }
            )
            profiles.pop(profile.model_id, None)
            sources.pop(profile.model_id, None)
            continue
        claimed[profile.model_id] = str(path)
        profiles[profile.model_id] = profile
        sources[profile.model_id] = "document"

    for model_id, profile in _REGISTERED.items():
        profiles[model_id] = profile
        sources[model_id] = "registered"

    return profiles, problems, sources


def installed(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, ModelProfileV1]:
    """Every profile this home holds, keyed by its DECLARED id."""

    profiles, _problems, _sources = _load(home=home, environ=environ)
    return profiles


def resolve(
    model_id: str | None,
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ModelProfileV1 | None:
    """This model's profile, or ``None`` if nobody has described it.

    ``None`` is a complete, expected answer and the common one: nothing ships,
    so every model is unknown until a human writes a document.  Callers must
    treat it as a disposition, never as an error.
    """

    if not model_id:
        return None
    return installed(home=home, environ=environ).get(str(model_id))


def registry_fingerprint(
    *,
    home: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict:
    """The identity a run's record stamps for this registry.

    Identity only: no wall-clock, no counter, no path outside the problem
    rows, so two runs over the same documents stamp byte-identical values.
    Problems are carried HERE rather than dropped, because a run that could
    not read a document must say so on its own record -- the record is the
    only admissible evidence, and an unreadable document that left no trace
    would be indistinguishable from a model nobody described.
    """

    profiles, problems, sources = _load(home=home, environ=environ)
    return {
        "registry": MODEL_PROFILE_REGISTRY_VERSION,
        "count": len(profiles),
        "profiles": [
            {
                "model_id": model_id,
                "digest": profiles[model_id].digest,
                "measured_on": profiles[model_id].measured_on.isoformat(),
                "source": sources[model_id],
            }
            for model_id in sorted(profiles)
        ],
        "problem_count": len(problems),
        "problems": sorted(problems, key=lambda row: (row["code"], row["path"])),
    }
