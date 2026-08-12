"""Human-readable prose for typed error/refusal codes, keyed by code string.

Purely additive: every key here must be byte-identical to a real raise-site
code string (tests/test_error_catalog.py proves this), and nothing here may
ever rename a code or replace its raw message — this is a second, optional
surface a caller may consult, never a substitute for the typed record.

Covers the QUALIFICATION_* and DOCTOR_* families (44 of 572 typed codes
found by the 2026-08-11 census, experiments/2026-08-11-change-qualification-
messages-s4b/ERROR_CENSUS.md) plus 3 INTAKE_* codes raised by
`intake_form.py`'s own field validators (not part of the census — new codes
this same program minted, catalogued from birth rather than added after the
fact). The remaining ~528 QUALIFICATION_*/DOCTOR_*-sibling codes are explicit
residue for follow-on tranches, one family at a time — see that tranche's
PARKED.md. Do not treat CATALOG's coverage as complete.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErrorCatalogEntry(BaseModel):
    """One code's plain-language gloss: what it is, and what to do."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    summary: str
    what_it_means: str
    next_action: str


def _entry(code: str, summary: str, what_it_means: str, next_action: str) -> ErrorCatalogEntry:
    return ErrorCatalogEntry(
        code=code,
        summary=summary,
        what_it_means=what_it_means,
        next_action=next_action,
    )


_QUALIFY_RETRY = "Retry: deepreason qualify"

CATALOG: dict[str, ErrorCatalogEntry] = {
    e.code: e
    for e in (
        _entry(
            "QUALIFICATION_V6_REQUIRED",
            "Reusable production qualification accepts only RunManifest schema 6.",
            "Your run's manifest (the compiled configuration a run carries) is on an "
            "older schema version. Qualification — the ~14-minute battery that "
            "certifies a model can fill each role before a real run may use it — "
            "only reuses evidence gathered against schema 6.",
            "Recompile your manifest at the current schema version, then " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_POLICY_PRESET_MISMATCH",
            "Reusable qualification requires the repository-owned V6 policy preset.",
            "Your manifest's control-plane policy (the set of rules governing what "
            "a run is allowed to do) does not match the one preset qualification "
            "evidence is keyed against.",
            "Use the standard preset (no custom control-plane policy edits), then "
            + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_SUBJECT_INVALID",
            "The qualification subject digest is invalid.",
            "A subject digest (a fingerprint identifying exactly what was "
            "qualified — the manifest, route inventory, and provider profile "
            "together) failed a basic format check before any cache lookup.",
            "This usually indicates a corrupted or hand-edited cache path; "
            + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_NOT_CONFIGURED",
            "No completed reusable qualification exists for this exact subject.",
            "Nothing has ever qualified this exact combination of manifest, "
            "routes, and provider profile.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_CACHE_UNAVAILABLE",
            "The qualification cache cannot be inspected safely.",
            "The cache file exists but could not be read (permissions, a "
            "filesystem error, or similar) — not a statement about whether the "
            "qualification itself is valid.",
            "Check file permissions on the qualification cache directory, then "
            + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_CACHE_UNSAFE",
            "The qualification cache entry must be a bounded regular file.",
            "The cache path resolved to something other than a plain, "
            "size-bounded file (a symlink, a directory, or a file that changed "
            "size while being read) — refused for safety, not because the "
            "qualification itself failed.",
            "Delete the suspicious cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_INCOMPLETE",
            "Incomplete qualification evidence is never reusable.",
            "A cached qualification bundle exists but is missing required "
            "evidence — the harness will not treat a partial result as a pass.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_CACHE_INVALID",
            "The qualification cache entry is invalid or incomplete.",
            "The cached file could be read but failed to parse as a valid "
            "qualification record.",
            "Delete the cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_CACHE_NONCANONICAL",
            "The qualification cache entry is not in canonical form.",
            "The cache file's bytes do not match the exact serialization the "
            "harness itself would have written — a sign of hand-editing or "
            "corruption, not a fresh qualification result.",
            "Delete the cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_SUBJECT_MISMATCH",
            "The qualification cache entry belongs to another behavior subject.",
            "The cache file's own recorded subject digest does not match the "
            "subject it was looked up under — a cross-contamination guard, not a "
            "normal miss.",
            "Delete the cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_CACHE_CONFLICT",
            "Different completed evidence already exists for this subject.",
            "Two different qualification results are trying to occupy the same "
            "cache slot — a write-race guard.",
            "Re-run " + _QUALIFY_RETRY + "; if this recurs, avoid qualifying the "
            "same subject concurrently from two sessions.",
        ),
        _entry(
            "QUALIFICATION_TIER_NOT_RECORDED",
            "No durable qualification tier exists for this exact subject.",
            "The reduced ('shallow') qualification tier — a lighter battery for "
            "smaller models — has never been recorded for this subject either.",
            _QUALIFY_RETRY + " (add --shallow if targeting the reduced tier)",
        ),
        _entry(
            "QUALIFICATION_TIER_INVALID",
            "The qualification tier record is invalid or incomplete.",
            "The cached shallow-tier record could be read but failed to parse.",
            "Delete the tier cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_TIER_NONCANONICAL",
            "The qualification tier record is not in canonical form.",
            "The tier cache file's bytes do not match the exact serialization "
            "the harness would have written.",
            "Delete the tier cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_TIER_SUBJECT_MISMATCH",
            "The qualification tier record belongs to another behavior subject.",
            "The tier cache file's own recorded subject digest does not match "
            "the subject it was looked up under.",
            "Delete the tier cache entry and " + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_PROFILE_MISMATCH",
            "Completed qualification evidence belongs to another provider profile.",
            "The cached qualification was run against a different provider "
            "profile (endpoint, model, or credential) than the one now in use.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_PAIR_INVENTORY_MISMATCH",
            "Completed qualification pair inventory differs from the manifest.",
            "The cached qualification covered a different set of role/route "
            "pairs than your current manifest needs — it may cover foreign pairs "
            "or be missing pairs your manifest requires.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_TIER_SHALLOW",
            'This provider/model is qualified at tier "shallow" only.',
            "Full V6 reasoning (the standard reasoning engine) is refused for "
            "this provider/model — it passed only the reduced battery.",
            'Use: deepreason reason --shallow "YOUR QUESTION"',
        ),
        _entry(
            "QUALIFICATION_TIER_UNQUALIFIED",
            'This provider/model concluded qualification at tier "unqualified".',
            "Neither the full nor the reduced battery passed for this "
            "provider/model.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_EXECUTION_FAILED",
            "Injected qualification execution did not complete successfully.",
            "The qualification battery itself (the test calls to the provider) "
            "did not finish — a provider-side or network failure during "
            "qualification, not a result about the model's capability.",
            'The reduced engine remains available: deepreason reason --shallow '
            '"YOUR QUESTION"; otherwise ' + _QUALIFY_RETRY,
        ),
        _entry(
            "QUALIFICATION_EXECUTION_INVALID",
            "Injected qualification execution returned invalid sanitized evidence.",
            "The qualification battery completed but produced evidence that "
            "failed validation — a data-shape problem, not necessarily a "
            "capability failure.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_RUN_MANIFEST_V6_REQUIRED",
            "Production-contract qualification accepts only RunManifest v6.",
            "The manifest handed to the doctor (the production-contract "
            "qualification checker) is on an older schema version.",
            "Recompile your manifest at schema version 6.",
        ),
        _entry(
            "DOCTOR_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED",
            "Production qualification requires frozen route-seat behavioral authority.",
            "Your manifest has no `route_seat_behavioral_capability_plan` — the "
            "frozen record of which route/seat pairs are authorized to run which "
            "behavioral contracts.",
            "Recompile your manifest so this plan is populated before qualifying.",
        ),
        _entry(
            "DOCTOR_BEHAVIORAL_CONTRACT_GRANT_REQUIRED",
            "A production contract lacks exact route-seat authority.",
            "One of the route/seat pairs the doctor is checking has no matching "
            "entry in the manifest's behavioral capability plan.",
            "Add the missing route-seat entry to the manifest's capability plan.",
        ),
        _entry(
            "DOCTOR_PRODUCTION_CONTRACT_MISMATCH",
            "The constructed production contract differs from the active pair.",
            "The contract the doctor built from the manifest does not match the "
            "contract versions actually configured.",
            "Check `control_plane_policy.contract_versions` against your "
            "manifest's actual route/seat pairs.",
        ),
        _entry(
            "DOCTOR_REQUEST_ENVELOPE_CAPACITY_REQUIRED",
            "Production qualification requires a finite prompt-plus-completion capacity.",
            "One role/seat is missing a `context_window_tokens` value — the "
            "doctor cannot bound how much a call may cost without it.",
            "Set `context_window_tokens` for every role/seat in your manifest.",
        ),
        _entry(
            "DOCTOR_CLASSIFICATION_PAIR_INVENTORY_MISMATCH",
            "Classification evidence differs from exact route-seat contracts.",
            "The doctor's classification pass covers a different set of "
            "route/seat pairs than the manifest actually configures.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_CLASSIFICATION_FOREIGN_ROUTE",
            "Classification evidence contains a foreign route seat.",
            "The classification result references a route/seat pair that is not "
            "part of this manifest at all — a cross-contamination guard.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_CONTRACT_REPAIR_GRANT_EXCEEDED",
            "A case exceeds its frozen repair grant.",
            "The number of repair attempts (bounded correction passes) used "
            "during qualification exceeded what the manifest's repair policy "
            "authorizes for that contract.",
            "Either accept the failure or widen the repair grant in your "
            "manifest's `contract_schema_repair_policy`, then " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_MISSING",
            "The production-contract doctor report is absent.",
            "No doctor report file exists where one is required for this "
            "operation.",
            _QUALIFY_RETRY + " to generate one.",
        ),
        _entry(
            "DOCTOR_REPORT_UNSAFE",
            "The production-contract doctor report cannot be inspected safely.",
            "The report path resolved to something other than a plain, "
            "size-bounded file (a symlink, a directory, or a file that changed "
            "while being read).",
            "Delete the suspicious report file and " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_TOO_LARGE",
            "The production-contract doctor report exceeds the fixed byte ceiling.",
            "The report file is larger than the harness will trust as a genuine "
            "qualification report — likely corrupted.",
            "Delete the report file and " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_INVALID",
            "The production-contract doctor report is not valid strict JSON.",
            "The report file could be read but failed to parse.",
            "Delete the report file and " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_NONCANONICAL",
            "The production-contract doctor report is not in canonical form.",
            "The report file's bytes do not match the exact serialization the "
            "harness would have written — hand-editing or corruption.",
            "Delete the report file and " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_MANIFEST_V6_REQUIRED",
            "Production-contract qualification validation requires RunManifest v6.",
            "The manifest supplied alongside the report is on an older schema "
            "version.",
            "Recompile your manifest at schema version 6.",
        ),
        _entry(
            "DOCTOR_REPORT_SCHEMA_VERSION_MISMATCH",
            "The production-contract doctor report does not qualify RunManifest v6.",
            "The report itself records a different manifest schema version than "
            "6.",
            _QUALIFY_RETRY + " against a v6 manifest.",
        ),
        _entry(
            "DOCTOR_REPORT_MANIFEST_MISMATCH",
            "The production-contract doctor report belongs to another manifest.",
            "The report's recorded manifest hash does not match the manifest you "
            "supplied.",
            _QUALIFY_RETRY + " against this exact manifest.",
        ),
        _entry(
            "DOCTOR_REPORT_PAIR_INVENTORY_MISMATCH",
            "The production-contract doctor report differs from the manifest pair inventory.",
            "The report covers a different set of route/seat pairs than your "
            "current manifest configures.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_REPAIR_GRANT_EXCEEDED",
            "A production-contract doctor case exceeds manifest repair authority.",
            "One case in the report used more repair attempts than your "
            "manifest's `contract_schema_repair_policy` authorizes.",
            "Widen the repair grant in your manifest or accept the failure, "
            "then " + _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_PAIR_UNQUALIFIED",
            "The production-contract doctor report contains an unqualified pair.",
            "At least one route/seat pair in the report did not pass "
            "qualification.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_SUMMARY_UNQUALIFIED",
            "The production-contract doctor report is not qualified.",
            "The report's own summary states the manifest as a whole is not "
            "qualified.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_QUALIFIED_PAIR_COUNT_MISMATCH",
            "The qualified pair count differs from the manifest pair inventory.",
            "The report's own count of qualified pairs does not match how many "
            "the manifest actually needs.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_REPORT_CLASSIFICATION_MISMATCH",
            "The doctor report lacks the exact deterministic route-seat classification.",
            "The report is missing (or has a mismatched) route-seat model "
            "classification the doctor requires.",
            _QUALIFY_RETRY,
        ),
        _entry(
            "DOCTOR_OUTPUT_CONFLICT",
            "The qualification report cannot overwrite the RunManifest.",
            "The `--out` path you gave for writing the doctor report collides "
            "with a manifest file.",
            "Choose a different `--out` path.",
        ),
        _entry(
            "INTAKE_SEAT_CONFLICT",
            "Two seat groups bind the same role to different profiles.",
            "In your intake form's `seats` mapping, two group names — one of "
            "them possibly an alias, like `simulation` for `conjecture` — "
            "resolve to the same underlying role but name different "
            "provider profiles. The form itself no longer refuses this "
            "(all-configs-allowed, 2026-08-12); once seats are wired to a "
            "run, the same precedence rule `seat_bindings.resolve_seat_bindings` "
            "uses applies (a direct group beats an alias, then "
            "alphabetically-later-group-wins).",
            "Give both group names the same profile if you want the choice "
            "to be unambiguous, or bind only one of them.",
        ),
        _entry(
            "INTAKE_CYCLES_CEILING_EXCEEDED",
            "The requested cycle budget exceeds the V6 ceiling.",
            "Your intake form's `cycles` value is higher than the fixed "
            "maximum the standard reasoning engine accepts.",
            "Lower `cycles` to the ceiling or below.",
        ),
    )
}


def lookup(code: str) -> ErrorCatalogEntry | None:
    """Return the catalog entry for `code`, or None if not yet cataloged.

    Never raises for an unknown code — the catalog is explicitly partial
    (44 of 572 known typed codes as of 2026-08-11); callers must treat a
    missing entry as "not yet documented," not as an error of their own.
    """

    return CATALOG.get(code)
