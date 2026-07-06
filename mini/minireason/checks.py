"""M1 — skeleton contract + program checks (MINI_PLAN §3.4).

Free criticism is the only criticism that measured cost-positive at low
base error: in the basin arms, mechanical checks refuted candidates with
zero judge tokens. Each candidate's OWN falsifiability claims (forbidden
cases with ``predicate:``/``program:`` evals) compile into runnable checks;
a failed check is the only refutation source in v0. ``rubric:`` cases are
carried on the interface but never judged in the loop — that is the
offline instrument's job (judge.py).

Commitment ids and eval semantics are the parent's exactly, so a mini log
replays under the parent with identical verdicts (G6).
"""

import contextlib
import json
import re
import signal

from pydantic import BaseModel, Field, ValidationError

from minireason.log import canonical_json, sha256_hex

SKELETON_WF_ID = "skeleton-wf"
PREDICATE_TIMEOUT_S = 2  # wall bound on hostile predicates (e.g. 10**10**8)


@contextlib.contextmanager
def _deadline(seconds: int):
    """Bound a predicate's wall time (POSIX main thread; elsewhere it runs
    unbounded, as the parent does). Safe for determinism: verdicts are
    logged as warrants and replay never re-evaluates, so a timeout can
    only shape the live run, never fork the log."""
    if hasattr(signal, "SIGALRM") and signal.getsignal(signal.SIGALRM) in (
            signal.SIG_DFL, signal.default_int_handler, None):
        def _raise(signum, frame):
            raise TimeoutError(f"predicate exceeded {seconds}s")

        old = signal.signal(signal.SIGALRM, _raise)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        yield


class ForbiddenCase(BaseModel):
    case: str = Field(min_length=1)
    eval: str  # "predicate:<expr>" | "program:<ref>" | "rubric:<spec-id>"
    observation_valued: bool = False


class Scope(BaseModel):
    covers: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)


class Skeleton(BaseModel):
    claim: str
    mechanism: str
    scope: Scope = Field(default_factory=Scope)
    forbidden: list[ForbiddenCase] = Field(default_factory=list)
    prose_notes: str | None = None  # rendered, never adjudicated


def parse_skeleton(text: str) -> Skeleton | None:
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or "claim" not in data or "mechanism" not in data:
        return None
    try:
        return Skeleton.model_validate(data)
    except ValidationError:
        return None


# --- eval machinery (parent programs.py, ported) ----------------------------

_SAFE_NAMES = {
    "len": len, "any": any, "all": all, "min": min, "max": max, "abs": abs,
    "sum": sum, "str": str, "int": int, "float": float, "sorted": sorted,
    "re": re, "json": json,
}


def _json_wf(text: str) -> tuple[str, dict]:
    try:
        json.loads(text)
        return "pass", {"parsed": True}
    except Exception as e:  # noqa: BLE001 - verdicts must not crash the loop
        return "fail", {"error": str(e)}


def _skeleton_wf(text: str) -> tuple[str, dict]:
    """Parses as a skeleton AND forbids at least one case — forbid nothing
    => refuted by a program: demarcation made real."""
    skeleton = parse_skeleton(text)
    if skeleton is None:
        return "fail", {"error": "content does not parse as a skeleton"}
    if not skeleton.forbidden:
        return "fail", {"error": "forbids nothing: empty attack surface (§6)"}
    return "pass", {"forbidden_cases": len(skeleton.forbidden)}


PROGRAMS = {"json-wf": _json_wf, "skeleton_wf": _skeleton_wf}


def evaluable(eval_spec: str) -> bool:
    kind, _, arg = eval_spec.partition(":")
    return kind == "predicate" or (kind == "program" and arg in PROGRAMS)


def evaluate(eval_spec: str, text: str, codec: str = "utf8") -> tuple[str, dict]:
    """Run the check on the candidate's real bytes; (verdict, trace). A
    verdict is a pure function of content — no wall-clock ever enters."""
    kind, _, arg = eval_spec.partition(":")
    if kind == "predicate":
        # Safe names go in GLOBALS: comprehensions inside eval resolve free
        # names via globals (parent bug, kept fixed).
        namespace = {"__builtins__": {}, **_SAFE_NAMES, "content": text, "codec": codec}
        try:
            with _deadline(PREDICATE_TIMEOUT_S):
                return ("pass" if bool(eval(arg, namespace)) else "fail"), {}
        except BaseException as e:  # noqa: BLE001 - incl. TimeoutError: a bomb is a failed verdict
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return "fail", {"error": str(e)[:200]}
    if kind == "program" and arg in PROGRAMS:
        return PROGRAMS[arg](text)
    raise ValueError(f"not evaluable in the loop: {eval_spec}")


# --- compilation -------------------------------------------------------------

def forbidden_commitment_id(case: ForbiddenCase) -> str:
    """The parent's deterministic id — same skeleton, same interface."""
    return "fc:" + sha256_hex(canonical_json({
        "case": case.case, "eval": case.eval,
        "observation_valued": case.observation_valued,
    }))[:12]


def compile_checks(text: str) -> list[dict]:
    """All commitments a candidate's content compiles to, parent-record
    shape: skeleton-wf plus one per forbidden case (rubric cases included —
    carried on the interface, judged only offline)."""
    out = [{"id": SKELETON_WF_ID, "eval": "program:skeleton_wf",
            "observation_valued": False, "budget": {"extra": {}}}]
    skeleton = parse_skeleton(text)
    for case in skeleton.forbidden if skeleton else []:
        out.append({"id": forbidden_commitment_id(case), "eval": case.eval,
                    "observation_valued": case.observation_valued,
                    "budget": {"extra": {"case": case.case}}})
    return out


def run_checks(text: str, checks: list[dict], codec: str = "utf8") -> list[dict]:
    """Evaluate every loop-evaluable check; returns failure traces only.
    Any failure refutes (the only refutation source in v0)."""
    failures = []
    for c in checks:
        if not evaluable(c["eval"]):
            continue
        verdict, detail = evaluate(c["eval"], text, codec)
        if verdict == "fail":
            failures.append({"commitment": c["id"], "eval": c["eval"],
                             "verdict": verdict, **detail})
    return failures
