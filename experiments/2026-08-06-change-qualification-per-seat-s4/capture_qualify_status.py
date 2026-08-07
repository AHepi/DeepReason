"""Capture `deepreason qualify --json`/`deepreason status --json` output
for a single-profile (no --seat) test home, using an injected executor
so no real provider call is made. Used identically before and after
this tranche's src/ edits to prove R6's byte-identity (SPEC.md Item S6).

Usage: python capture_qualify_status.py <suffix>
Writes <suffix>-qualify.json and <suffix>-status.json in this directory.
"""

import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "src")

from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.cli.main import main
from deepreason.provider_profile import (
    ProviderProfileV1,
    setup_provider_profile_path,
    write_provider_profile,
)


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        ),
    )


def main_capture(suffix: str) -> None:
    home = Path(f"/tmp/s4_{suffix}_home")
    os.environ["DEEPREASON_HOME"] = str(home)
    os.environ["DEEPREASON_S4_CAPTURE_KEY"] = "not-a-real-secret"

    profile = ProviderProfileV1.create(
        provider="generic",
        endpoint="https://example.invalid/v1",
        model_id="capture-test-model",
        family="fixture",
        context_window_tokens=65536,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_S4_CAPTURE_KEY",
        output_mechanism="native_json_schema",
    )
    write_provider_profile(profile, setup_provider_profile_path(environ=os.environ))

    here = Path(__file__).parent
    with patch(
        "deepreason.qualification.default_qualification_executor",
        _qualified_report,
    ):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["qualify", "--yes", "--json"])
        (here / f"{suffix}-qualify.json").write_text(buf.getvalue())

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            main(["status", "--json"])
        (here / f"{suffix}-status.json").write_text(buf2.getvalue())


if __name__ == "__main__":
    main_capture(sys.argv[1])
