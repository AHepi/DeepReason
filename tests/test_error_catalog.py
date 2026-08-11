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


def test_catalog_covers_44_entries():
    assert len(CATALOG) == 44


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
