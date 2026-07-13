"""Vendored capability catalog (assets/): a small tiered catalog, not one
compulsory framework — the baseline is a technical floor only; every
aesthetic choice is a selectable, on-the-record option."""

from deepreason import assets


def test_catalog_offers_selectable_options():
    names = assets.catalog_names()
    assert {"classless", "layout"} <= names
    catalog = assets.catalog()
    for name in names:
        assert catalog[name].strip(), f"option {name} is empty"


def test_baseline_is_a_technical_floor_not_an_aesthetic():
    """The universally injected tier makes no visual-identity decision:
    no fonts, no palette, no component styling — those live in selectable
    options so a single visual system cannot become a silent shared
    attractor across schools and runs."""
    baseline = assets.baseline()
    assert baseline.strip()
    assert "box-sizing" in baseline           # the floor it does provide
    assert "prefers-reduced-motion" in baseline
    assert "font-family" not in baseline      # aesthetics stay selectable
    assert "--" not in baseline.split("*/")[-1] or "var(" not in baseline


