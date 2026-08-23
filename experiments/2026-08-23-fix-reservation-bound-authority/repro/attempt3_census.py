"""Re-derive attempt 3's bound disagreement from its committed root alone.

Usage:  python attempt3_census.py <root>

Reads only typed records. Establishes, without re-running anything:
  * exactly one authorized work attempt never reached the provider;
  * its prompt digest matched its reservation, so verify_dispatch passed and
    the prompt term of the guard is pinned to the reservation's own
    prompt_bound_tokens;
  * the controller settled that seat's cap below its route ceiling at the
    cycle the run died;
  * the two sides of the guard, and their difference.
"""

import json
import pathlib
import sys


def _objects(root, kind):
    d = root / "objects" / kind
    return [json.loads(p.read_text())["data"] for p in sorted(d.glob("*"))] if d.is_dir() else []


def main(root):
    root = pathlib.Path(root)
    reservations = _objects(root, "workflow-token-reservation-v2")
    authorizations = _objects(root, "workflow-dispatch-authorization-v1")
    attempts = _objects(root, "workflow-provider-attempt-v1")

    dispatched = {(a["work_id"], a["attempt_index"]) for a in attempts}
    orphans = [a for a in authorizations if (a["work_id"], a["attempt_index"]) not in dispatched]
    by_id = {r["id"]: r for r in reservations}

    print(f"reservations {len(reservations)}  authorizations {len(authorizations)} "
          f" provider attempts {len(attempts)}  authorized-never-dispatched {len(orphans)}")
    if len(orphans) != 1:
        print("expected exactly one refused dispatch")
        return 1

    refused = orphans[0]
    booked = by_id[refused["reservation_ref"]]
    seat = refused["route_lease"]
    print(f"\nrefused dispatch: role={seat['role']} seat={seat['seat']} contract={refused['contract_id']}")
    print(f"  prompt digest matches its reservation: {refused['prompt_sha256'] == booked['prompt_sha256']}")
    print(f"  booked  prompt_bound={booked['prompt_bound_tokens']} "
          f"completion_bound={booked['completion_bound_tokens']} reserved={booked['reserved_tokens']}")

    policies = []
    for p in (root / "objects" / "artifact").glob("*"):
        d = json.loads(p.read_text())["data"]
        if (d.get("provenance") or {}).get("role") == "controller":
            policies.append(json.loads(d["content_ref"].removeprefix("inline:")))
    print(f"\ncontroller policy artifacts: {len(policies)}")
    for body in policies:
        print(f"  cycle={body['cycle']} knobs={body['knobs']}")

    knob = f"cap:{seat['role']}"
    settled = next((b["knobs"][knob] for b in policies if knob in b["knobs"]), None)
    if settled is None:
        print(f"\nno settled cap for {knob}; the dispatch cap is unrecoverable from this root")
        return 1

    amount = booked["reserved_tokens"]
    dispatch_bound = booked["prompt_bound_tokens"] + settled
    print(f"\n  reservation.amount (booked, recorded) = "
          f"{booked['prompt_bound_tokens']} + {booked['completion_bound_tokens']} = {amount}")
    print(f"  reservation_bound  (dispatch, NOT recorded) = "
          f"{booked['prompt_bound_tokens']} + {settled} = {dispatch_bound}")
    print(f"  disagreement = {amount - dispatch_bound} "
          f"= route ceiling {booked['completion_bound_tokens']} - settled cap {settled}")
    return 0 if amount != dispatch_bound else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
