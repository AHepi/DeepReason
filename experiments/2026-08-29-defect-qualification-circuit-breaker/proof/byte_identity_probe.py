import json, sys
sys.path.insert(0, ".")
from tests.test_cli_production_doctor_v6 import _manifest, _admitted_case
from deepreason.cli.doctor import run_production_contract_doctor
r = run_production_contract_doctor(
    _manifest(), case_executor=lambda m, p, i: _admitted_case(i))
print(json.dumps(r.model_dump(mode="json", by_alias=True, exclude_none=True),
                 sort_keys=True, separators=(",", ":")))
