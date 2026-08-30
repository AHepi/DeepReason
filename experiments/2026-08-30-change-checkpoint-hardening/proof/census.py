"""Census of every committed run root: what the record says, and what the two
continuation verbs would actually do with it.

Read-only by construction: it opens no writable Harness and copies nothing.
`results_summary` and `derive_terminal_authority` are both pure readers, which
is why the census can run over evidence roots without disturbing them.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py

Writes census.json beside itself and prints the tallies SPEC.md cites.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "census.json"


def committed_roots() -> list[Path]:
    """Every tracked run root, addressed by its own run-status.json.

    `git ls-files` rather than a filesystem walk: an untracked root is not
    evidence, and a gitignored home under experiments/ would otherwise inflate
    the population differently on every container.
    """
    listing = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    roots = []
    for line in listing:
        if not line.endswith("/run-status.json"):
            continue
        root = REPO / line[: -len("/run-status.json")]
        # A run root carries its own manifest; a loose evidence copy of a
        # run-status.json does not, and is not a root.
        if (root / "run-manifest.json").exists() or (root / "log.jsonl").exists():
            roots.append(root)
    return sorted(roots)


def row(root: Path) -> dict:
    from deepreason.application.results import results_summary
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    entry: dict = {"root": str(root.relative_to(REPO))}
    try:
        manifest = load_run_manifest(root / MANIFEST_NAME)
        entry["schema_version"] = str(getattr(manifest, "schema_version", None))
    except Exception as error:
        manifest = None
        entry["manifest_error"] = f"{type(error).__name__}: {error}"
        entry["schema_version"] = "ABSENT:NO_MANIFEST"
    try:
        summary = results_summary(root)
    except Exception as error:  # a root the reader cannot open is itself data
        entry["reader_error"] = f"{type(error).__name__}: {error}"
        return entry
    run = summary.get("run", {})
    terminal = summary.get("terminal", {})
    verification = summary.get("verification", {})
    entry.update(
        state=run.get("state"),
        stop_reason=run.get("stop_reason"),
        amend_ready=terminal.get("amend_ready"),
        valid_typed_terminal=terminal.get("valid_typed_terminal"),
        stop_reason_resumable=terminal.get("stop_reason_resumable"),
        continuation_authority=terminal.get("continuation_authority"),
        stored_replay_valid=verification.get("valid"),
        verification_source=verification.get("source"),
    )
    try:
        # The manifest is not optional here even though the signature allows
        # it: without one the derivation short-circuits to
        # `historical_read_only` for every root, which is what `amend` would
        # see only if it had lost its own bound manifest.
        authority = derive_terminal_authority(root, manifest=manifest)
        entry["authority_status"] = authority.status
        entry["authority_current_valid"] = bool(authority.current_valid)
        entry["authority_detail_code"] = authority.detail_code
    except Exception as error:
        entry["authority_error"] = f"{type(error).__name__}: {error}"
    return entry


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    roots = committed_roots()
    rows = []
    for index, r in enumerate(roots, 1):
        print(f"[{index}/{len(roots)}] {r.relative_to(REPO)}", flush=True)
        rows.append(row(r))

    def tally(key):
        return dict(Counter(str(r.get(key, "ABSENT")) for r in rows).most_common())

    triples = Counter(
        (str(r.get("state")), str(r.get("stop_reason")), str(r.get("amend_ready")))
        for r in rows
    )
    gap = [
        r["root"]
        for r in rows
        if r.get("authority_current_valid") and r.get("stored_replay_valid") is False
    ]
    stranded = [
        r["root"]
        for r in rows
        if not r.get("authority_current_valid")
        and r.get("authority_status") not in (None, "current_open_uncommitted")
    ]
    no_terminal = [
        r["root"] for r in rows if r.get("authority_status") == "current_open_uncommitted"
    ]
    full_files_no_receipt = [
        r["root"]
        for r in rows
        if r.get("state") == "failed" and r.get("continuation_authority") is not True
    ]
    payload = {
        "population": len(rows),
        "schema_version": tally("schema_version"),
        "state": tally("state"),
        "stop_reason": tally("stop_reason"),
        "amend_ready": tally("amend_ready"),
        "stored_replay_valid": tally("stored_replay_valid"),
        "verification_source": tally("verification_source"),
        "authority_status": tally("authority_status"),
        "triples": {" | ".join(k): v for k, v in triples.most_common()},
        "A2_gap_authority_valid_but_replay_invalid": sorted(gap),
        "A1_failed_without_continuation_authority": sorted(full_files_no_receipt),
        "no_terminal_finalize_population": sorted(no_terminal),
        "stranded_neither_amend_nor_finalize": sorted(stranded),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"population: {payload['population']}")
    print(f"schema_version: {payload['schema_version']}")
    print("triples (state | stop_reason | amend_ready):")
    for key, count in triples.most_common():
        print(f"  {' | '.join(key)}  -> {count}")
    print(f"amend_ready: {payload['amend_ready']}")
    print(f"stored_replay_valid: {payload['stored_replay_valid']}")
    print(f"verification_source: {payload['verification_source']}")
    print(f"authority_status: {payload['authority_status']}")
    print(f"A2 gap (authority valid AND stored replay invalid): {len(gap)}")
    for path in sorted(gap):
        print(f"  {path}")
    print(f"A1 failed without continuation authority: {len(full_files_no_receipt)}")
    print(f"finalize population (current_open_uncommitted): {len(no_terminal)}")
    for path in sorted(no_terminal):
        print(f"  {path}")
    print(f"stranded (neither amend nor finalize): {len(stranded)}")
    for path in sorted(stranded):
        print(f"  {path}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
