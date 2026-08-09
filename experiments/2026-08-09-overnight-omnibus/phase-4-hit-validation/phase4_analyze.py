"""Phase 4 step 3: compute the agreement matrix, per-check flip rates,
validated-contradiction rate, and false-negative rate, from the typed
re-judgment records only.

Usage: python3 phase4_analyze.py HIT_REJUDGE_JSON NON_HIT_REJUDGE_JSON OUT_JSON
"""

import json
import sys
from collections import Counter
from pathlib import Path

hit_path = Path(sys.argv[1])
non_hit_path = Path(sys.argv[2])
out_path = Path(sys.argv[3])

hit_data = json.loads(hit_path.read_text())["results"]
non_hit_data = json.loads(non_hit_path.read_text())["results"]

# -- hits: agreement matrix + validated rate --
matrix = Counter()
flip_a = flip_b = flip_c = 0
validated = 0
for r in hit_data:
    a = r["check_a_pair_swapped"]["satisfies_hit_rule"]
    b = r["check_b_skeptic_framed"]["satisfies_hit_rule"]
    c = r["check_c_verbatim_repeat"]["satisfies_hit_rule"]
    matrix[(a, b, c)] += 1
    if not a:
        flip_a += 1
    if not b:
        flip_b += 1
    if not c:
        flip_c += 1
    if r.get("validates"):
        validated += 1

n_hits = len(hit_data)

# -- non-hits: false-negative probe --
false_negatives = sum(1 for r in non_hit_data if r.get("false_negative_flip"))
flip_by_check_nonhit = {
    "check_a_pair_swapped": sum(1 for r in non_hit_data if r["check_a_pair_swapped"]["satisfies_hit_rule"]),
    "check_b_skeptic_framed": sum(1 for r in non_hit_data if r["check_b_skeptic_framed"]["satisfies_hit_rule"]),
    "check_c_verbatim_repeat": sum(1 for r in non_hit_data if r["check_c_verbatim_repeat"]["satisfies_hit_rule"]),
}
n_non_hits = len(non_hit_data)

out = {
    "n_hits_sampled": n_hits,
    "validated_count": validated,
    "validated_rate": (validated / n_hits) if n_hits else None,
    "agreement_matrix_a_b_c": {f"{a}_{b}_{c}": count for (a, b, c), count in sorted(matrix.items())},
    "flip_rate_check_a_pair_swapped": (flip_a / n_hits) if n_hits else None,
    "flip_rate_check_b_skeptic_framed": (flip_b / n_hits) if n_hits else None,
    "flip_rate_check_c_verbatim_repeat": (flip_c / n_hits) if n_hits else None,
    "n_non_hits_sampled": n_non_hits,
    "false_negative_count": false_negatives,
    "false_negative_rate": (false_negatives / n_non_hits) if n_non_hits else None,
    "false_negative_flips_by_check": flip_by_check_nonhit,
}
out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
print(json.dumps(out, indent=2, sort_keys=True))
