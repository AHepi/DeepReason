"""GOAL.md's six success criteria, one assertion block each."""
import json, sys, tempfile, pathlib
sys.path.insert(0, ".")
from tests.test_cli_production_doctor_v6 import _manifest, _admitted_case
from deepreason.cli.doctor import (
    PRODUCTION_CASES_PER_PAIR as PER, ProductionContractCaseResultV1,
    QualificationCircuitPolicyV1, run_production_contract_doctor,
    write_production_contract_report, load_production_contract_report)

def refusing(code, calls):
    def ex(m, pair, i):
        calls[pair.role] = calls.get(pair.role, 0) + 1
        if pair.role == "argumentative_critic":
            return ProductionContractCaseResultV1(
                case_id=f"case-{i+1:03d}", first_pass_valid=False, eventual_valid=False,
                repair_count=0, semantic_admission=False, failure_code=code)
        return _admitted_case(i)
    return ex

def codes(r):
    out = {}
    for pr in r.pairs:
        for c in pr.cases + (pr.first_draw_cases or ()):
            out[c.failure_code] = out.get(c.failure_code, 0) + 1
    return out

ok = []
# C1 -- bounded, and PER ROUTE
calls = {}
r401 = run_production_contract_doctor(_manifest(), case_executor=refusing("ENDPOINT_HTTP_401", calls))
assert calls["argumentative_critic"] == PER, calls
assert all(calls[x] == 2 * PER for x in ("thesis", "summarizer", "conjecturer", "judge")), calls
assert r401.summary.qualified_pair_count == 8
ok.append(f"C1 bounded+per-route: dead route {calls['argumentative_critic']} cases (was {4*PER}); "
          f"healthy routes 40 each; {r401.summary.qualified_pair_count}/10 pairs still qualified")

# C2 -- a transient that clears does NOT trip
tcalls = {}
def transient(m, pair, i):
    tcalls[pair.role] = tcalls.get(pair.role, 0) + 1
    if pair.role == "argumentative_critic" and i < 19:
        return ProductionContractCaseResultV1(case_id=f"case-{i+1:03d}", first_pass_valid=False,
            eventual_valid=False, repair_count=0, semantic_admission=False, failure_code="ENDPOINT_HTTP_429")
    return _admitted_case(i)
rt = run_production_contract_doctor(_manifest(), case_executor=transient)
assert rt.circuit_breaker is None and tcalls["argumentative_critic"] == 4 * PER, (rt.circuit_breaker, tcalls)
ok.append(f"C2 transient does not trip: circuit_breaker None, all {tcalls['argumentative_critic']} cases dispatched")

# C3 -- the record distinguishes the two conditions
r429 = run_production_contract_doctor(_manifest(), case_executor=refusing("ENDPOINT_HTTP_429", {}))
assert codes(r401) != codes(r429)
ok.append(f"C3 records differ: 401 -> {sorted(k for k in codes(r401) if k)}; 429 -> {sorted(k for k in codes(r429) if k)}")

# C4 -- switchable OFF, typed WARNING, never a refusal
ocalls = {}
roff = run_production_contract_doctor(_manifest(), case_executor=refusing("ENDPOINT_HTTP_401", ocalls),
                                      circuit_policy=QualificationCircuitPolicyV1(enabled=False))
assert ocalls["argumentative_critic"] == 4 * PER
assert [n.code for n in roff.circuit_breaker.notices] == ["QUALIFICATION_CIRCUIT_BREAKER_DISABLED"]
rin = run_production_contract_doctor(_manifest(), case_executor=refusing("ENDPOINT_HTTP_401", {}),
                                     circuit_policy=QualificationCircuitPolicyV1(code_prefixes=()))
assert [n.code for n in rin.circuit_breaker.notices] == ["QUALIFICATION_CIRCUIT_BREAKER_INERT"]
ok.append("C4 OFF is exhaustive + typed warning, never a refusal; the second road to OFF "
          "(empty prefixes) warns too")

# C5 -- the record survives, complete and typed, and round-trips
with tempfile.TemporaryDirectory() as d:
    t = pathlib.Path(d) / "q.json"
    write_production_contract_report(r401, t)
    assert load_production_contract_report(t) == r401
syn = [c for pr in r401.pairs for c in pr.cases if (c.failure_code or "").startswith("CIRCUIT_OPEN_")]
assert len(syn) == PER and r401.summary.case_count == r401.summary.pair_count * PER
ok.append(f"C5 report complete and round-trips: {len(syn)} synthesized cases, "
          f"case_count {r401.summary.case_count} == {r401.summary.pair_count}x{PER}")

# C6 -- no configuration knob moves a qualification subject digest
from deepreason.config import Config
from deepreason.run_manifest import source_config_hash
before = source_config_hash(Config())
assert before == "6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81", before
ok.append(f"C6 no Config field added: source_config_hash unchanged at {before[:16]}...")

for line in ok: print("  PASS  " + line)
print(f"\n{len(ok)}/6 criteria PASS")
