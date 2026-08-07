import sys
sys.path.insert(0, "src")
from datetime import datetime, timezone
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.cli.doctor import production_contract_pairs, exercise_production_contract_case
import deepreason.llm.adapter as adapter_mod

def profile(**updates):
    values = dict(
        provider="openai", endpoint="https://api.example.com/v1", model_id="model-default",
        model_revision="rev-a", family="family-a", context_window_tokens=262144,
        maximum_completion_tokens=4096, credential_env="DEEPREASON_TEST_KEY",
    )
    values.update(updates)
    return ProviderProfileV1.create(**values)

default_profile = profile(model_id="model-default")
profile_a = profile(model_id="model-a")
profile_b = profile(model_id="model-b")

manifest = build_preparation_manifest(
    default_profile,
    question="Why is the sky blue?",
    compiled_at=datetime(2026, 8, 6, tzinfo=timezone.utc).isoformat(),
    seat_bindings={"conjecturer": profile_a, "judge": profile_b},
)

print("roles model_ids:", {role: [r.model_id for r in routes] for role, routes in manifest.roles.items()})

pairs = production_contract_pairs(manifest)
print("total pairs:", len(pairs))
by_role = {}
for p in pairs:
    by_role.setdefault(p.role, []).append(p)
print("roles with pairs:", sorted(by_role))

# pick one pair each from conjecturer (model-a) and judge (model-b), if present
target_roles = [r for r in ("conjecturer", "judge") if r in by_role]
print("target roles found:", target_roles)

dispatch_log = []

class FakeEndpoint:
    def __init__(self, model_id, endpoint_id):
        self.model_id = model_id
        self.endpoint_id = endpoint_id
        self.model = model_id
        self.name = "https://api.example.com/v1"
        self.family = "family-a"
        self.model_revision = "rev-a"
        self.context_window_tokens = 262144
        self.max_tokens = 4096
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None
        self.last_transport_diagnostics = ()
        self.last_transport_attempts = 1

    def complete(self, request, **kwargs):
        dispatch_log.append(self.model_id)
        # minimal valid-ish stub; exact validity doesn't matter for THIS measurement,
        # we're only checking WHICH endpoint got the call, not full case success.
        return "{}"

def fake_endpoint_from_spec(spec):
    return FakeEndpoint(spec.get("model"), spec.get("endpoint_id"))

adapter_mod._endpoint_from_spec = fake_endpoint_from_spec

for role in target_roles:
    pair = by_role[role][0]
    print(f"--- exercising role={role} pair.model_id={pair.model_id} ---")
    try:
        exercise_production_contract_case(manifest, pair, 0)
    except Exception as e:
        print("  (case raised, expected given stub response):", type(e).__name__, str(e)[:200])

print("dispatch_log (which model_id actually received .complete()):", dispatch_log)
print("expected order:", [by_role[r][0].model_id for r in target_roles])
print("MATCH:", dispatch_log == [by_role[r][0].model_id for r in target_roles])

# Refined check: within each role's own exercise, EVERY dispatched call
# (including retries) must target ONLY that role's own bound model_id --
# zero cross-contamination is the actual claim being measured.
print()
print("=== per-role dispatch purity ===")
idx = 0
per_role_calls = {}
# re-run cleanly, resetting the log between roles to attribute calls correctly
for role in target_roles:
    dispatch_log.clear()
    pair = by_role[role][0]
    try:
        exercise_production_contract_case(manifest, pair, 0)
    except Exception:
        pass
    per_role_calls[role] = list(dispatch_log)
    expected_model = pair.model_id
    purity = all(m == expected_model for m in dispatch_log)
    print(f"role={role} expected_model={expected_model} calls={dispatch_log} PURE={purity}")

all_pure = all(
    all(m == by_role[r][0].model_id for m in calls)
    for r, calls in per_role_calls.items()
)
print("ALL ROLES DISPATCH-PURE (zero cross-contamination):", all_pure)

print()
print("=== default-role purity check (summarizer, unbound, should stay model-default) ===")
dispatch_log.clear()
pair = by_role["summarizer"][0]
try:
    exercise_production_contract_case(manifest, pair, 0)
except Exception:
    pass
print(f"role=summarizer expected_model={pair.model_id} calls={dispatch_log}")
print("PURE:", all(m == pair.model_id for m in dispatch_log))
