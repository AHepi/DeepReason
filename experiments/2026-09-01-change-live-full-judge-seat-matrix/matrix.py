#!/usr/bin/env python3
"""Offline domain, safety, and resume primitives for the full-judge matrix."""
from __future__ import annotations
import argparse, contextlib, fcntl, hashlib, itertools, json, os, re, struct
import tempfile, threading, unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
SEAT_SCHEMA = "deepreason.full-judge-seat-case.v1"
STRUCTURAL_SCHEMA = "deepreason.full-judge-structural-case.v1"
FORBIDDEN_REASONING = frozenset({"high", "max", "xhigh"})
RESULT_FIELDS = ("case_id", "status", "code", "message", "stage",
                 "exception_type", "pointer", "dispatch_history")
_CALL_SLOTS = threading.BoundedSemaphore(3)
class MatrixRefusal(RuntimeError):
    """Typed campaign refusal whose stable code is present in ``str(exc)``."""
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}" if message else code)
def canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
def _sha256_id(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()
def load_domain(path: str | os.PathLike[str]) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        domain = json.load(handle)
    if domain.get("schema") != "deepreason.full-judge-matrix-domain.v1":
        raise MatrixRefusal("DOMAIN_SCHEMA_UNSUPPORTED")
    return domain
def seat_counts(model_count: int) -> dict[str, int]:
    if isinstance(model_count, bool) or model_count < 1:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    return {
        "judge_pairs": model_count**2,
        "core_courts": model_count**3,
        "no_variator": model_count**4,
        "with_variator": model_count**5,
        "total": model_count**4 + model_count**5,
    }
def transport_counts(model_count: int) -> dict[str, int]:
    per_model = 3 * 2 * 3 * 4 * 3 * (1 + 5)
    return {"per_model": per_model, "total": model_count * per_model}
def domain_counts(domain: Mapping[str, Any]) -> dict[str, int]:
    model_count = len(domain["fixture_catalog"])
    seat = seat_counts(model_count)["total"]
    transport = transport_counts(model_count)["total"]
    return {"seat": seat, "transport": transport, "combined": seat + transport}
def normalize_model_id(model_id: str) -> str:
    if not isinstance(model_id, str):
        raise MatrixRefusal("MODEL_ID_NOT_STRING")
    folded = unicodedata.normalize("NFKC", model_id).casefold()
    return re.sub(r"[^a-z0-9]", "", folded)
def _ordered_raw_ids(model_ids: Iterable[str]) -> list[str]:
    raw = list(model_ids)
    if any(not isinstance(item, str) or not item for item in raw):
        raise MatrixRefusal("MODEL_ID_INVALID")
    if len(set(raw)) != len(raw):
        raise MatrixRefusal("DUPLICATE_RAW_MODEL_ID")
    return sorted(raw, key=lambda item: item.encode("utf-8"))
def freeze_catalog(model_ids: Iterable[str]) -> dict[str, Any]:
    accepted: list[str] = []
    excluded: list[dict[str, str]] = []
    for model_id in _ordered_raw_ids(model_ids):
        if "kimik3" in normalize_model_id(model_id):
            excluded.append({"model_id": model_id, "code": "KIMI_K3_FORBIDDEN"})
        else:
            accepted.append(model_id)
    return {
        "model_ids": accepted,
        "excluded": excluded,
        "catalog_sha256": hashlib.sha256(canonical_json(accepted)).hexdigest(),
    }
def _seat_case(catalog_sha256: str, critic: str, defender: str, judge0: str,
               judge1: str, variator: str | None, prefix: str) -> dict[str, Any]:
    fields = {"schema": SEAT_SCHEMA, "catalog_sha256": catalog_sha256,
              "critic": critic, "defender": defender, "judge0": judge0,
              "judge1": judge1, "variator": variator}
    return {**fields, "case_id": _sha256_id(fields), "prefix": prefix}
def iter_seat_cases(model_ids: Iterable[str], *, catalog_sha256: str
                    ) -> Iterator[dict[str, Any]]:
    models = freeze_catalog(model_ids)["model_ids"]
    if not models:
        raise MatrixRefusal("EMPTY_MODEL_CATALOG")
    anchor = models[0]
    seen: set[str] = set()
    plans = (
        ("judge_pairs", ((anchor, anchor, j0, j1, None) for j0, j1 in itertools.product(models, repeat=2))),
        ("core_courts", ((anchor, d, j0, j1, None) for d, j0, j1 in itertools.product(models, repeat=3))),
        ("no_variator", ((*parts, None) for parts in itertools.product(models, repeat=4))),
        ("with_variator", itertools.product(models, repeat=5)),
    )
    for prefix, assignments in plans:
        for assignment in assignments:
            row = _seat_case(catalog_sha256, *assignment, prefix)
            if prefix == "with_variator":
                yield row
                continue
            if row["case_id"] not in seen:
                seen.add(row["case_id"])
                yield row
def structural_case_ids(domain: Mapping[str, Any]) -> list[str]:
    case_ids: list[str] = []
    for group in domain["structural_domains"]:
        assignments: Iterable[Any]
        if group["combination"] == "cartesian":
            axes = group["axes"]
            keys = list(axes)
            assignments = (
                dict(zip(keys, values))
                for values in itertools.product(*(axes[key] for key in keys))
            )
        elif group["combination"] == "enumerated_cases":
            assignments = (
                value if isinstance(value, dict) else {"case": value}
                for value in group["cases"]
            )
        else:
            raise MatrixRefusal("STRUCTURAL_COMBINATION_UNSUPPORTED", group["name"])
        before = len(case_ids)
        for assignment in assignments:
            case_ids.append(_sha256_id({"schema": STRUCTURAL_SCHEMA,
                                        "group": group["name"],
                                        "assignment": assignment}))
        if len(case_ids) - before != group["expected_count"]:
            raise MatrixRefusal("STRUCTURAL_COUNT_MISMATCH", group["name"])
    return case_ids
def length_prefixed_set_digest(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values, key=lambda item: item.encode("utf-8")):
        encoded = value.encode("utf-8")
        digest.update(struct.pack(">I", len(encoded)))
        digest.update(encoded)
    return digest.hexdigest()
def validate_provider_body(body: Mapping[str, Any]) -> None:
    model_id = body.get("model")
    if not isinstance(model_id, str) or not model_id:
        raise MatrixRefusal("MODEL_ID_INVALID")
    if "kimik3" in normalize_model_id(model_id):
        raise MatrixRefusal("KIMI_K3_FORBIDDEN")
    if "reasoning_effort" not in body or body["reasoning_effort"] is None:
        raise MatrixRefusal("REASONING_EFFORT_REQUIRED")
    effort = body["reasoning_effort"]
    if isinstance(effort, str) and effort.strip().casefold() in FORBIDDEN_REASONING:
        raise MatrixRefusal("FORBIDDEN_REASONING_EFFORT")
    if isinstance(effort, int) and not isinstance(effort, bool) and effort > 2_000:
        raise MatrixRefusal("FORBIDDEN_REASONING_EFFORT")
def build_provider_body(model_id: str, reasoning: str | int | None) -> dict[str, Any]:
    if reasoning is None:
        raise MatrixRefusal("REASONING_EFFORT_REQUIRED")
    if isinstance(reasoning, bool) or not isinstance(reasoning, (str, int)):
        raise MatrixRefusal("REASONING_EFFORT_INVALID")
    if isinstance(reasoning, int):
        effort = "low" if reasoning <= 2_000 else "high"
    else:
        effort = reasoning
    body = {"model": model_id, "reasoning_effort": effort}
    validate_provider_body(body)
    return body
def guarded_complete(config_authority: str, manifest: Mapping[str, Any],
                     body: Mapping[str, Any],
                     complete: Callable[[Mapping[str, Any]], Any]) -> Any:
    contracts = manifest.get("trial_contracts")
    required = ("defender[0]", "judge[0]", "judge[1]")
    authorized = (
        config_authority == "defended_trial"
        and manifest.get("authority") == "defended_trial"
        and isinstance(contracts, Mapping)
        and all(contracts.get(seat) for seat in required)
    )
    if not authorized:
        raise MatrixRefusal("DEFENDED_TRIAL_NOT_AUTHORIZED")
    validate_provider_body(body)
    with _CALL_SLOTS:
        return complete(body)
def run_bounded(tasks: Sequence[Callable[[], Any]], *, workers: int = 3) -> list[Any]:
    worker_count = min(3, max(1, workers))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        return list(pool.map(lambda task: task(), tasks))
@contextlib.contextmanager
def coordinator_lock(path: str | os.PathLike[str]) -> Iterator[None]:
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MatrixRefusal("COORDINATOR_ALREADY_RUNNING") from exc
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
def safe_result_bytes(result: Mapping[str, Any], *, secret: str | None = None) -> bytes:
    safe = {field: result[field] for field in RESULT_FIELDS if field in result}
    proposed = canonical_json(safe)
    if secret and secret.encode("utf-8") in proposed:
        proposed = canonical_json({"case_id": str(result.get("case_id", "withheld")),
            "status": "unexpected_error", "code": "SECRET_BEARING_DIAGNOSTIC_WITHHELD",
            "message": "Diagnostic withheld because it contained credential bytes."})
    return proposed
def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp_path.unlink(missing_ok=True)
def atomic_terminal_write(path: str | os.PathLike[str], result: Mapping[str, Any],
                          *, secret: str | None = None) -> None:
    target = Path(path)
    if target.exists():
        raise MatrixRefusal("TERMINAL_RESULT_IMMUTABLE")
    _atomic_bytes(target, safe_result_bytes(result, secret=secret))
def prepare_attempt(root: str | os.PathLike[str], *, domain_sha256: str,
                    catalog_sha256: str) -> Path:
    attempt_root = Path(root)
    attempt_root.mkdir(parents=True, exist_ok=True)
    binding_path = attempt_root / "binding.json"
    binding = {"domain_sha256": domain_sha256, "catalog_sha256": catalog_sha256}
    if binding_path.exists():
        previous = json.loads(binding_path.read_text(encoding="utf-8"))
        if previous.get("domain_sha256") != domain_sha256:
            raise MatrixRefusal("DOMAIN_DIGEST_MISMATCH")
        if previous.get("catalog_sha256") != catalog_sha256:
            raise MatrixRefusal("CATALOG_DIGEST_MISMATCH")
    else:
        _atomic_bytes(binding_path, canonical_json(binding))
    attempts = sorted(
        (path for path in attempt_root.glob("attempt-[0-9][0-9][0-9][0-9]") if path.is_dir()),
        key=lambda path: path.name,
    )
    if attempts and not (attempts[-1] / "INTERRUPTED.json").exists():
        raise MatrixRefusal("ATTEMPT_ALREADY_ACTIVE")
    next_path = attempt_root / f"attempt-{len(attempts) + 1:04d}"
    next_path.mkdir()
    _atomic_bytes(next_path / "attempt.json", canonical_json({**binding, "status": "active"}))
    return next_path
def mark_interrupted(attempt: str | os.PathLike[str]) -> None:
    atomic_terminal_write(
        Path(attempt) / "INTERRUPTED.json",
        {"status": "interrupted", "message": "Attempt retained unchanged; resume rotates."},
    )
def _enumerate_fixture() -> None:
    domain = load_domain(Path(__file__).with_name("MATRIX_DOMAIN.json"))
    model_count = len(domain["fixture_catalog"])
    counts = seat_counts(model_count)
    print(
        f"CATALOG_MODELS={model_count} JUDGE_PAIRS={counts['judge_pairs']} "
        f"CORE_COURTS={counts['core_courts']} NO_VARIATOR={counts['no_variator']} "
        f"WITH_VARIATOR={counts['with_variator']} TOTAL={counts['total']}"
    )
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--fixture-catalog", action="store_true", required=True)
    args = parser.parse_args(argv)
    if args.command == "enumerate" and args.fixture_catalog:
        _enumerate_fixture()
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
