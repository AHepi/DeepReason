"""Schools (spec §11.1) and allocation (§11.2) — islands in conjecture,
panmixia in criticism.

A school is a persistent conditioning regime for gamma-calls, registered as
an attackable school-policy artifact (Refl). Constitution = lineage
inheritance: school k's packs draw exemplars from accepted artifacts with
provenance.school == k — curation-free by construction. Reseed is
succession, not deletion (D8): a new policy artifact + a Reseed event; the
roster is a deterministic function of the log. Schools never touch att/dep,
adjudication, or statuses.
"""

from contextlib import contextmanager
import copy
import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Provenance, Rule, SpawnTrigger, Status
from deepreason.ontology.frozen import FrozenDict

# One-time global curation, declared (§11.1 cold start; §17 residue).
STANCE_LIBRARY = {
    "mechanist": "demand a causal mechanism",
    "skeptic": "counterexample first",
    "unifier": "seek the covering principle",
    "empiric": "anchor in cases",
    "formalist": "derivation first",
    "historicist": "precedent and succession",
    "adversary": "strongest attack on the incumbent",
    "minimalist": "parsimony pressure",
}
_STANCES = list(STANCE_LIBRARY)


def _policy_content(
    school_id: str,
    stance: str,
    reseed_of: str | None = None,
    crossover_from: str | None = None,
) -> str:
    body = {"school_policy": {"school": school_id, "stance": stance}}
    if reseed_of:
        body["school_policy"]["reseed_of"] = reseed_of
    if crossover_from:
        body["school_policy"]["crossover_from"] = crossover_from
    return json.dumps(body, sort_keys=True)


def roster(harness) -> dict[str, dict]:
    """Latest policy per school, in event order — deterministic from the log."""
    out: dict[str, dict] = {}
    for aid, artifact in harness.state.artifacts.items():
        if artifact.codec != "json" or not artifact.content_ref.startswith("inline:"):
            continue
        try:
            body = json.loads(artifact.content_ref[len("inline:"):])
        except ValueError:
            continue
        policy = body.get("school_policy")
        if isinstance(policy, dict) and "school" in policy:
            out[policy["school"]] = {**policy, "artifact_id": aid}
    return out


def init_schools(harness, config) -> dict[str, dict]:
    """Seed N_SCHOOLS from the stance library (idempotent across reloads)."""
    existing = roster(harness)
    for i in range(config.N_SCHOOLS):
        school_id = f"school-{i}"
        if school_id in existing:
            continue
        stance = _STANCES[i % len(_STANCES)]
        harness.create_artifact(
            _policy_content(school_id, stance),
            codec="json",
            provenance=Provenance(role="seed", school=school_id),
            rule=Rule.REFL,
        )
    return roster(harness)


def reseed(
    harness, school_id: str, current: dict, reason: str, crossover_from: str | None = None
) -> dict:
    """Rotate the laggard's stance seed; logged as a Reseed event. The prior
    policy artifact persists (D8) — succession, not deletion. crossover_from
    (§11.4) records the most-distant school so the reseeded school's next
    gamma-calls draw that foreign lineage's exemplars — rotating the stance
    alone just yields the same echo in a new voice (a skeptic mutating its own
    math). Attention only; never status."""
    next_stance = _STANCES[(_STANCES.index(current["stance"]) + 1) % len(_STANCES)]
    harness.create_artifact(
        _policy_content(
            school_id, next_stance,
            reseed_of=current["artifact_id"], crossover_from=crossover_from,
        ),
        codec="json",
        provenance=Provenance(role="seed", school=school_id),
        rule=Rule.RESEED,
    )
    harness.record_measure(inputs=["intervention:reseed", f"school:{school_id}", reason])
    return roster(harness)[school_id]


def crossover_exemplars(harness, school_id: str, k: int = 3) -> list[str]:
    """§11.4 forced crossover: if the school's current policy names a
    crossover_from (set on a convergence reseed), return that foreign school's
    top-k accepted conjecture artifacts (most recent lineage first,
    deterministic id tiebreak) so gamma must reconcile divergent lineages
    instead of mutating its own echo chamber. Empty when no crossover is
    pending. Attention only — pack shaping, never status (D2)."""
    foreign = (roster(harness).get(school_id) or {}).get("crossover_from")
    if not foreign:
        return []
    state = harness.state
    cands = [
        aid
        for aid, a in state.artifacts.items()
        if a.provenance.school == foreign
        and a.provenance.role.value in ("conjecturer", "synthesizer")
        and state.status.get(aid) == Status.ACCEPTED
    ]
    cands.sort(key=lambda aid: (-state.artifacts[aid].provenance.event_seq, aid))
    return cands[:k]


def lineage_size(harness, school_id: str) -> int:
    return sum(
        1
        for a in harness.state.artifacts.values()
        if a.provenance.school == school_id
        and a.provenance.role.value in ("conjecturer", "synthesizer")
    )


def stance_weight(harness, school_id: str, config) -> float:
    """Identity migrates from seed to lineage (STANCE_DECAY schedule)."""
    decay = float(config.STANCE_DECAY) if config.STANCE_DECAY else 20.0
    return max(0.0, 1.0 - lineage_size(harness, school_id) / decay)


def _with_cross_examiner(harness, assigned: list[str], schools: dict, config) -> list[str]:
    """Cross-examination floor (§11.2, the XEXAM_SHARE knob): ownership
    allocation is rich-get-richer — a refuted candidate spawns a successor
    OWNED by its school, so an early lead compounds (observed live: 64:1
    lineage; the rival stance effectively never generated). When the
    smallest lineage falls below XEXAM_SHARE of the owner's, it joins the
    assignment as cross-examiner until it catches back up. Deterministic
    (a function of log + config) and attention-only — never status."""
    share = float(config.XEXAM_SHARE or 0)
    if not share or len(schools) < 2:
        return assigned
    owner = assigned[0]
    starved = min(
        (s for s in schools if s not in assigned),
        key=lambda s: (lineage_size(harness, s), s),
        default=None,
    )
    if starved is None:
        return assigned
    # Integer floor: fires only once the owner has a real lead (at share
    # 0.15, from owner lineage 7 up), so tiny early lineages keep pure
    # ownership and the first mover isn't instantly cross-examined.
    if lineage_size(harness, starved) < int(share * lineage_size(harness, owner)):
        return assigned + [starved]
    return assigned


def allocate(harness, problem, schools: dict[str, dict], config) -> list[str]:
    """Deterministic function of (log, config) — no per-problem curation."""
    if not schools:
        return []
    everyone = sorted(schools)
    trigger = problem.provenance.trigger
    # Fan-out classes: exactly where rival programmes should compete.
    if trigger in (SpawnTrigger.SEED, SpawnTrigger.DISCRIMINATION, SpawnTrigger.INTEGRATION):
        return everyone
    # Ownership by provenance: lineages follow through on their problem-shifts —
    # with a cross-examination floor so ownership cannot starve a rival school.
    if trigger in (SpawnTrigger.SUCCESSOR, SpawnTrigger.REMOVE_ARBITRARINESS):
        for fid in problem.provenance.from_:
            artifact = harness.state.artifacts.get(fid)
            if artifact is not None and artifact.provenance.school in schools:
                return _with_cross_examiner(
                    harness, [artifact.provenance.school], schools, config
                )
        return everyone
    # Other triggers: owner if known, else fan out.
    for fid in problem.provenance.from_:
        artifact = harness.state.artifacts.get(fid)
        if artifact is not None and artifact.provenance.school in schools:
            return _with_cross_examiner(
                harness, [artifact.provenance.school], schools, config
            )
    return everyone


class SchoolPopulationRegistryError(ValueError):
    pass


class UnknownSchoolPopulationBackend(SchoolPopulationRegistryError, KeyError):
    pass


@dataclass(frozen=True)
class SchoolPopulationRegistration:
    backend_id: str
    backend: "SchoolPopulationBackend"
    pinned_fingerprint: dict


class SchoolPopulationBackend(Protocol):
    def fingerprint(self) -> dict[str, Any]: ...

    def init_schools(self, harness, config) -> dict[str, dict]: ...

    def roster(self, harness) -> dict[str, dict]: ...

    def allocate(self, harness, problem, schools: dict[str, dict], config) -> list[str]: ...

    def reseed(
        self, harness, school_id: str, current: dict, reason: str,
        crossover_from: str | None = None,
    ) -> dict: ...


class SchoolPopulationRegistry:
    """Resolve only trusted registered names; model output never routes policy."""

    def __init__(self, backends: Iterable[SchoolPopulationBackend] = ()) -> None:
        self._registrations: dict[str, SchoolPopulationRegistration] = {}
        for backend in backends:
            self.register(backend)

    def register(
        self,
        backend: SchoolPopulationBackend,
        *,
        backend_id: str | None = None,
    ) -> SchoolPopulationRegistration:
        if not all(
            hasattr(backend, attr)
            for attr in ("fingerprint", "init_schools", "roster", "allocate", "reseed")
        ):
            raise TypeError("backend does not implement the school-population protocol")
        fingerprint = backend.fingerprint()
        resolved = backend_id or str(
            fingerprint.get("backend") or getattr(backend, "name", "")
        )
        if not resolved:
            raise SchoolPopulationRegistryError(
                "backend fingerprint has no backend identifier"
            )
        if resolved in self._registrations:
            raise SchoolPopulationRegistryError(
                f"school-population backend already registered: {resolved}"
            )
        if fingerprint.get("backend") not in {None, resolved}:
            raise SchoolPopulationRegistryError(
                "backend identifier disagrees with fingerprint"
            )
        registration = SchoolPopulationRegistration(
            backend_id=resolved,
            backend=backend,
            pinned_fingerprint=FrozenDict(copy.deepcopy(fingerprint)),
        )
        self._registrations[resolved] = registration
        return registration

    def get(self, backend_id: str) -> SchoolPopulationRegistration:
        try:
            registration = self._registrations[backend_id]
        except KeyError as error:
            raise UnknownSchoolPopulationBackend(
                f"unknown school-population backend: {backend_id}"
            ) from error
        if not self.fingerprint_is_pinned(backend_id):
            raise SchoolPopulationRegistryError(
                "school-population backend fingerprint changed after registration"
            )
        return registration

    resolve = get

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def fingerprint(self, backend_id: str) -> dict[str, Any]:
        return self._registrations[backend_id].backend.fingerprint()

    def fingerprint_is_pinned(self, backend_id: str) -> bool:
        registration = self._registrations[backend_id]
        return canonical_json(registration.backend.fingerprint()) == canonical_json(
            registration.pinned_fingerprint
        )


class DefaultSchoolPopulationBackend:
    """Today's behavior, unchanged, made resolvable by name."""

    def fingerprint(self) -> dict[str, Any]:
        return {"backend": "default", "stance_count": len(_STANCES)}

    def init_schools(self, harness, config) -> dict[str, dict]:
        return init_schools(harness, config)

    def roster(self, harness) -> dict[str, dict]:
        return roster(harness)

    def allocate(self, harness, problem, schools: dict[str, dict], config) -> list[str]:
        return allocate(harness, problem, schools, config)

    def reseed(
        self, harness, school_id: str, current: dict, reason: str,
        crossover_from: str | None = None,
    ) -> dict:
        return reseed(harness, school_id, current, reason, crossover_from)


class RoundRobinSchoolPopulationBackend:
    """A deliberately dumb alternative: allocation by rotation.

    It discards every rule ``allocate`` encodes — the fan-out classes, the
    ownership-by-provenance lookup, and the cross-examination floor — and
    hands each problem to exactly one school chosen by rotation. The point
    is not that this is good; it is that the socket admits a strategy that
    disagrees with the default, so "pluggable" is a property of the code
    rather than a claim about it.

    The rotation key is the problem id, NOT a call counter: allocation must
    stay a function of (log, config), or a reopened run would allocate
    differently from the session that wrote it and replay would diverge.
    """

    def fingerprint(self) -> dict[str, Any]:
        return {"backend": "round-robin", "stance_count": len(_STANCES)}

    def init_schools(self, harness, config) -> dict[str, dict]:
        return init_schools(harness, config)

    def roster(self, harness) -> dict[str, dict]:
        return roster(harness)

    def allocate(self, harness, problem, schools: dict[str, dict], config) -> list[str]:
        if not schools:
            return []
        everyone = sorted(schools)
        digest = sha256_hex(canonical_json(problem.id))
        return [everyone[int(digest, 16) % len(everyone)]]

    def reseed(
        self, harness, school_id: str, current: dict, reason: str,
        crossover_from: str | None = None,
    ) -> dict:
        return reseed(harness, school_id, current, reason, crossover_from)


SCHOOL_POPULATION = SchoolPopulationRegistry()
SCHOOL_POPULATION.register(DefaultSchoolPopulationBackend(), backend_id="default")
SCHOOL_POPULATION.register(
    RoundRobinSchoolPopulationBackend(), backend_id="round-robin"
)

# The single place the active backend's NAME lives, so no call site spells it.
# A run-selected name (rung 5's "a run configured with the alternative") would
# replace this constant's value, not the call sites.
_ACTIVE_BACKEND_ID = "default"


def active_backend() -> SchoolPopulationBackend:
    """The registered population backend every caller resolves through."""

    return SCHOOL_POPULATION.resolve(_ACTIVE_BACKEND_ID).backend


@contextmanager
def population_backend(backend_id: str):
    """Run a scope with a chosen registered backend active.

    Selection deliberately lives here rather than on ``Config``: a new
    top-level ``Config`` field enters ``source_config_hash`` and the
    qualification subject digest unless ``run_manifest.py`` is told to scrub
    it per schema version, and that file is a frozen surface. Which backend
    a run used stays recoverable from the record regardless — the scheduler
    stamps the resolved backend's fingerprint into the log.

    The name is resolved BEFORE the selection moves, so an unknown name
    leaves the process on its previous backend rather than on a broken one.
    """

    global _ACTIVE_BACKEND_ID

    SCHOOL_POPULATION.resolve(backend_id)
    previous = _ACTIVE_BACKEND_ID
    _ACTIVE_BACKEND_ID = backend_id
    try:
        yield SCHOOL_POPULATION.resolve(backend_id).backend
    finally:
        _ACTIVE_BACKEND_ID = previous
