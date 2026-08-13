import re

from deepreason.error_catalog import CATALOG, lookup


def _raise_site_codes(path: str, prefix: str) -> set[str]:
    text = open(path).read()
    return {m for m in re.findall(rf'"({prefix}[A-Z0-9_]+)"', text)}


def test_catalog_keys_are_real_qualification_codes():
    real = _raise_site_codes("src/deepreason/qualification.py", "QUALIFICATION_")
    catalog_keys = {k for k in CATALOG if k.startswith("QUALIFICATION_")}
    assert catalog_keys <= real, catalog_keys - real


def test_catalog_keys_are_real_doctor_codes():
    real = _raise_site_codes("src/deepreason/cli/doctor.py", "DOCTOR_")
    catalog_keys = {k for k in CATALOG if k.startswith("DOCTOR_")}
    assert catalog_keys <= real, catalog_keys - real


def test_catalog_covers_48_entries():
    assert len(CATALOG) == 48


def test_catalog_keys_are_real_intake_codes():
    from deepreason.intake_form import (
        INTAKE_CYCLES_CEILING_EXCEEDED,
        INTAKE_SEAT_CONFLICT,
    )

    real = {INTAKE_SEAT_CONFLICT, INTAKE_CYCLES_CEILING_EXCEEDED}
    catalog_keys = {k for k in CATALOG if k.startswith("INTAKE_")}
    assert catalog_keys == real


def test_lookup_known_code_returns_entry():
    entry = lookup("QUALIFICATION_TIER_UNQUALIFIED")
    assert entry is not None
    assert entry.code == "QUALIFICATION_TIER_UNQUALIFIED"
    assert entry.summary
    assert entry.what_it_means
    assert entry.next_action


def test_lookup_unknown_code_returns_none_not_error():
    assert lookup("NOT_A_REAL_CODE") is None


def test_every_entry_has_nonempty_fields():
    for code, entry in CATALOG.items():
        assert entry.code == code
        assert entry.summary.strip()
        assert entry.what_it_means.strip()
        assert entry.next_action.strip()


def test_catalog_keys_are_real_results_codes():
    """Implements R13: every RESULTS_* gloss names a code `results.py` really raises.

    The catalog is a second, optional surface over the typed record — a key
    with no raise site would document a refusal that cannot happen.
    """

    real = _raise_site_codes("src/deepreason/application/results.py", "RESULTS_")
    catalog_keys = {k for k in CATALOG if k.startswith("RESULTS_")}
    assert catalog_keys == real, catalog_keys ^ real
