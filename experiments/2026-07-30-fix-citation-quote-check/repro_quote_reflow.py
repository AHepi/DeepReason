"""Reproduction: the citation quote check tests line layout, not text.

Offline. Touches no production code and no committed run root's contents.
Run:  python3 experiments/2026-07-30-fix-citation-quote-check/repro_quote_reflow.py
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

from deepreason.admission import AdmissionInput, admit_sources
from deepreason.evidence.citations import check_candidate_citations
from deepreason.llm.contracts import EvidenceRefClaimV1
from deepreason.storage.blobs import BlobStore

PROVENANCE_KW = dict(supplied_by="repro", acquisition_method="fixture", note=None)

# Hard-wrapped at ~72 columns, exactly as a human-authored dossier is.
WRAPPED = (
    "# Open challenge\n"
    "\n"
    "23 has stood since 1976 despite: decades of hand construction;\n"
    "numerical alternating-least-squares searches; SAT and Groebner-basis\n"
    "attacks; and a large reinforcement-learning search that rediscovered\n"
    "23 without beating it.\n"
).encode("utf-8")


def _fixture():
    from deepreason.evidence.models import AttachedSourceProvenanceV1

    dossier, _ = admit_sources(
        [AdmissionInput(locator="challenge.md", data=WRAPPED)],
        problem_ref="question-" + "0" * 32,
        provenance=AttachedSourceProvenanceV1(**PROVENANCE_KW),
    )
    store = BlobStore(Path(tempfile.mkdtemp()) / "blobs")
    store.put(WRAPPED)
    block = next(b for b in dossier.blocks if b.text is None and b.span_end - b.span_start > 80)
    canonical = WRAPPED[block.span_start : block.span_end].decode("utf-8")
    return dossier, store, block, canonical


def _code(dossier, store, block, quote):
    checks = check_candidate_citations(
        (EvidenceRefClaimV1(block=block.id, quote=quote),), dossier, store
    )
    return checks[0].code


def part_one():
    dossier, store, block, canonical = _fixture()
    assert "\n" in canonical, "fixture block must span a wrap"

    exact = canonical[:120]
    reflowed = exact.replace("\n", " ")
    fabricated = re.sub(r"\b1976\b", "1979", reflowed)

    print("PART 1 - fixture, one block, three quotes")
    print(f"  block spans {canonical.count(chr(10))} hard newline(s)")
    print(f"  exact bytes incl. newline : {_code(dossier, store, block, exact)}")
    print(f"  same text, newline->space : {_code(dossier, store, block, reflowed)}")
    print(f"  fabricated (1976 -> 1979) : {_code(dossier, store, block, fabricated)}")
    print()
    return _code(dossier, store, block, reflowed), _code(dossier, store, block, fabricated)


ROOT = Path(
    "experiments/live_research_2026-07-29/openchallenge/runs/"
    "run-27b80f26bd398c718360e97e2a403593"
)


def part_two():
    """Corroboration: replay the field failure's own 15 (block, quote) pairs."""

    dossier_doc = json.loads((ROOT / "evidence-dossier.json").read_text())
    blobs = {p.name: p.read_bytes() for p in ROOT.glob("blobs/*/*")}
    texts = {
        b["id"]: blobs[b["source_sha256"]][b["span_start"] : b["span_end"]].decode("utf-8")
        for b in dossier_doc["blocks"]
    }
    pairs = set()
    for raw in blobs.values():
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for m in re.finditer(
            r'"block"\s*:\s*"([0-9a-f]+)"\s*,\s*"quote"\s*:\s*"((?:[^"\\]|\\.)*)"', text
        ):
            pairs.add((m.group(1), json.loads('"' + m.group(2) + '"')))

    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    exact = reflow = absent = unresolved = 0
    for ref, quote in pairs:
        hit = [t for bid, t in texts.items() if bid.startswith(ref)]
        if not hit:
            unresolved += 1
        elif quote in hit[0]:
            exact += 1
        elif norm(quote) in norm(hit[0]):
            reflow += 1
        else:
            absent += 1

    print(f"PART 2 - the committed root's own quotes ({len(pairs)} distinct)")
    print(f"  exact byte sub-span            : {exact}")
    print(f"  present only after reflow      : {reflow}")
    print(f"  absent under any whitespace    : {absent}")
    print(f"  block unresolvable             : {unresolved}")
    print()
    return exact, reflow, absent, unresolved


if __name__ == "__main__":
    reflowed_code, fabricated_code = part_one()
    exact, reflow, absent, unresolved = part_two()

    total = exact + reflow + absent + unresolved
    print("VERDICT")
    print(
        f"  honest reflowed quote and fabricated quote share one code: "
        f"{reflowed_code == fabricated_code} ({reflowed_code})"
    )
    print(
        f"  field failure is the same mechanism: "
        f"{total > 0 and reflow == total}"
    )
