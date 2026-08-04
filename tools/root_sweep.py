"""One sweep of every openable run root. Re-run verbatim before and after.

Probe rule: a missing attribute returns a falsy default indistinguishable from
a real measurement, so every attribute is asserted before its value is read.
"""

import pathlib
import sys

from deepreason.harness import Harness
from deepreason.module_events import recorded_module_fingerprints
from deepreason.verification.report import verify_root_report

out = pathlib.Path(sys.argv[1])
lines = []
for root in sorted({p.parent for p in pathlib.Path("experiments").rglob("log.jsonl")}):
    try:
        report = verify_root_report(root)
        for field in ("valid", "epistemic_checks_passed", "epistemic"):
            assert hasattr(report, field), f"report has no {field}"
        blind = sum(
            1 for f in report.epistemic if f.check == "adjudication-blindness"
        )
        harness = Harness(root, read_only=True)
        assert hasattr(harness.state, "att"), "state has no att"
        # Module fingerprints (rung 4). Absence is the valid answer for every
        # root recorded before the observable existed, so this reports a count
        # rather than demanding one; a sweep that never read the field would
        # report "byte-identical" while proving nothing about it.
        assert hasattr(harness, "log"), "harness has no log"
        stamps = recorded_module_fingerprints(harness)
        modules = sorted(
            {m.module_id for stamp in stamps for m in stamp.modules}
        )
        lines.append(
            f"{str(root):72} valid={str(report.valid):5} "
            f"epistemic_passed={str(report.epistemic_checks_passed):5} "
            f"att={len(harness.state.att):3} blind={blind} "
            f"modules={','.join(modules) if modules else '-'}"
        )
    except Exception as error:
        lines.append(f"{str(root):72} ERROR {type(error).__name__}: {error}")
out.write_text("\n".join(lines) + "\n")
print(f"SWEEP COMPLETE: {len(lines)} roots -> {out}")
