#!/usr/bin/env python3
"""ARM V's critic endpoint: the shared loopback stub, with vacuous objections.

    python critic_stub.py --bank FILE [--port N] [--state FILE]
    python critic_stub.py --self-test

WHAT THIS IS. A local HTTP endpoint bound to the `argumentative_critic` role
ALONE. Every other seat in ARM V talks to the real provider exactly as in ARM
C; only the critic's replies come from here, and they come from a fixed bank
that carries no content about its targets (`make_vacuous_bank.py`,
`check_vacuity.py`).

THE STUB IS NOT RE-MINTED. `scripts/wheel_operational_smoke.py` already owns
the one loopback provider fixture in this repository, and `cycle_soak.py`
imports it rather than writing a second one ("the ONE stub, reused"). This
imports the same module and OVERRIDES exactly one thing: the content returned
for the argumentative-critic contract. Everything else — the request shape, the
schema synthesis for every other contract, the usage accounting, the 500 on an
unsatisfiable fixture — is the shared stub's, unchanged. A second stub would be
a second thing to keep in agreement with the harness's evolving wire contracts,
and it would drift.

WHY EVERY OTHER CONTRACT MUST STILL BE ANSWERED. This endpoint receives more
than criticism: the production-contract doctor probes it during qualification,
and a role's endpoint answers whatever its qualification battery asks. An
unsatisfied fixture is an HTTP 500, which trips the qualification circuit
breaker for the WHOLE endpoint. So anything that is not the critic contract
falls through to the shared stub's own synthesiser, untouched.

WHAT MAKES THE OBJECTIONS REACH THE NEXT CANDIDATE. Nothing here. That is the
discharge channel's job (`DR-CON-discharge-channel`), and it treats an
`observe_only` criticism identically whoever wrote it — a critic-role artifact
plus a `["scrutiny", target, critic]` Measure, walked by `open_criticisms` and
rendered into the conjecturer's binding block. ARM V changes the CONTENT of the
objection and nothing about its route, which is the whole design, and which
step 31 proves on the record rather than asserting here.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys
import threading

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import wheel_operational_smoke as _smoke  # noqa: E402  (the ONE stub, reused)

# The contracts whose CONTENT this stub replaces. Everything else falls through
# to the shared synthesiser. Listed rather than pattern-matched: a title this
# tranche has not seen is a contract it has not thought about, and answering it
# with an objection would be worse than answering it generically.
CRITIC_TITLES = frozenset({"ArgumentativeCriticOutput", "BatchCriticWireV2"})


class VacuousCritic:
    """Serves bank entries round-robin, so the sequence is deterministic."""

    def __init__(self, bank: dict) -> None:
        self.bank = bank
        self.entries = [e["text"] for e in bank["entries"]]
        if not self.entries:
            raise SystemExit("REFUSED: the bank is empty; ARM V would send no objection")
        self.lock = threading.Lock()
        self.cycle = itertools.cycle(range(len(self.entries)))
        self.served: list[int] = []

    def next_text(self) -> str:
        with self.lock:
            index = next(self.cycle)
            self.served.append(index)
        return self.entries[index]

    def response_for_schema(self, schema: dict, prompt: str):
        title = schema.get("title")
        if title not in CRITIC_TITLES:
            return _smoke.response_for_schema(schema, prompt)
        if title == "BatchCriticWireV2":
            aliases = (schema["$defs"]["BatchCriticCaseWireV2"]["properties"]
                       ["target_alias"].get("enum", []))
            return {"cases": [
                # attack=True: ARM V's objections must travel the SAME route as
                # ARM C's. An objection filed as no-attack would take a
                # different path through the record and the arms would differ
                # in more than content, which is the one thing ARM V may not do.
                {"target_alias": alias, "attack": True, "case": self.next_text()}
                for alias in aliases
            ]}
        return {"attack": True, "case": self.next_text()}


def serve_vacuous_critic(bank_path: pathlib.Path, port: int = 0, state_path: pathlib.Path | None = None):
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    critic = VacuousCritic(bank)
    original = _smoke.response_for_schema
    _smoke.response_for_schema = critic.response_for_schema
    state = _smoke.ProviderState()
    server, thread = _smoke._provider_server(state)
    return server, thread, critic, state, original


def self_test() -> int:
    """The stub answers the critic contract from the bank, and everything else
    from the shared synthesiser — both checked, because getting either wrong
    breaks a different thing."""

    sys.path.insert(0, str(HERE))
    import make_vacuous_bank  # noqa: PLC0415

    bank = make_vacuous_bank.build(median=600, iqr=(400, 900), count=12,
                                   seed=20260909)
    critic = VacuousCritic(bank)

    from deepreason.llm.contracts import ArgumentativeCriticOutput  # noqa: PLC0415

    schema = ArgumentativeCriticOutput.model_json_schema()
    reply = critic.response_for_schema(schema, "criticise this")
    assert reply["attack"] is True and reply["case"] in critic.entries, reply
    parsed = ArgumentativeCriticOutput.model_validate(reply)
    print(f"critic contract: answered from the bank, {len(reply['case'])} chars, "
          f"and the reply VALIDATES against the shipped contract "
          f"(attack={parsed.attack})")

    served = {critic.response_for_schema(schema, "x")["case"] for _ in range(12)}
    assert served == set(critic.entries), "round robin does not cover the bank"
    print(f"round robin covers all {len(critic.entries)} entries, deterministically")

    # A non-critic contract must be untouched: this endpoint is qualified by
    # the production-contract doctor, and an unsatisfied fixture is a 500 that
    # trips the circuit breaker for the whole endpoint.
    other = {"title": "ScratchBlockWireV1"}
    passthrough = critic.response_for_schema(other, "think")
    assert passthrough == _smoke.response_for_schema(other, "think"), passthrough
    print("a non-critic contract falls through to the shared stub, byte-identical")

    empty = dict(bank)
    empty["entries"] = []
    try:
        VacuousCritic(empty)
    except SystemExit:
        print("an empty bank REFUSES rather than serving no objection")
    else:
        print("FAIL: an empty bank was accepted")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=None)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--state", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.bank:
        ap.error("--bank is required")
    server, thread, critic, state, _original = serve_vacuous_critic(
        pathlib.Path(args.bank), args.port,
        pathlib.Path(args.state) if args.state else None)
    print(json.dumps({"endpoint": f"http://127.0.0.1:{server.server_address[1]}/v1",
                      "bank_digest": critic.bank.get("digest"),
                      "entries": len(critic.entries)}, sort_keys=True), flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
