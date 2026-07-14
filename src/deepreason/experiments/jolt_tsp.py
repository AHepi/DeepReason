"""Deterministic instruments for the positive-headroom TSP jolt pilot v3.1."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from hashlib import sha256
from itertools import permutations
from statistics import median
from typing import Iterable

from deepreason.canonical import canonical_json, sha256_hex

CITY_IDS = tuple(str(index) for index in range(14))
MOVEMENT_DIRECTIVE = (
    "Produce a complete valid tour whose undirected edge set differs from the\n"
    "incumbent's by at least two edges, and attempt to reduce the total\n"
    "Manhattan distance. Output must use the required JSON tour schema."
)
J3_PREFIX = (
    "Work in an edge-replacement representation rather than extending the\n"
    "previous sequence patterns. No additional facts about the optimum are\n"
    "available."
)
J4_PREFIX = (
    "A strictly better valid tour is known to exist, but its score and\n"
    "structure are withheld. Recent candidates have preserved most incumbent\n"
    "edges."
)
J6_DIRECTIVE = (
    "Produce the attempt that the recent candidate history makes least\n"
    "likely. Avoid the modal continuation and seek a substantially different\n"
    "valid tour."
)
OBSERVATION_SIGNAL = "jolt-tsp-observation-v3.1"
TRIGGER_SIGNAL = "jolt-tsp-trigger-v3.1"
ACTION_SIGNAL = "jolt-tsp-action-v3.1"
EVALUATOR_FINGERPRINT = sha256(b"deepreason-jolt-tsp14-manhattan-v3.1").hexdigest()


def generate_instance(seed: int) -> dict:
    rng = random.Random(seed)
    coordinates: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    while len(coordinates) < 14:
        point = (rng.randrange(0, 100), rng.randrange(0, 100))
        if point not in seen:
            seen.add(point)
            coordinates.append(point)
    return {
        "seed": seed,
        "cities": [
            {"id": str(index), "x": point[0], "y": point[1]}
            for index, point in enumerate(coordinates)
        ],
    }


def coordinates(instance: dict) -> dict[str, tuple[int, int]]:
    return {row["id"]: (int(row["x"]), int(row["y"])) for row in instance["cities"]}


def instance_ids(instance: dict) -> tuple[str, ...]:
    return tuple(row["id"] for row in instance["cities"])


def distance_matrix(instance: dict) -> tuple[tuple[int, ...], ...]:
    points = coordinates(instance)
    ids = instance_ids(instance)
    return tuple(
        tuple(
            abs(points[a][0] - points[b][0]) + abs(points[a][1] - points[b][1])
            for b in ids
        )
        for a in ids
    )


def validate_tour(value) -> tuple[str, ...] | None:
    if not isinstance(value, list) or len(value) != 14:
        return None
    if any(not isinstance(city, str) for city in value):
        return None
    tour = tuple(value)
    if tour[0] != "0" or set(tour) != set(CITY_IDS) or len(set(tour)) != 14:
        return None
    return tour


def parse_tour(text: str) -> tuple[str, ...] | None:
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return None
    return validate_tour(value.get("tour")) if isinstance(value, dict) else None


def canonical_tour(tour: Iterable[str]) -> tuple[str, ...]:
    value = tuple(tour)
    if not value or value[0] != "0":
        raise ValueError("tour must start at 0")
    reverse = ("0", *reversed(value[1:]))
    return min(value, reverse)


def edge_set(tour: Iterable[str]) -> frozenset[tuple[str, str]]:
    value = tuple(tour)
    pairs = zip(value, (*value[1:], value[0]))
    return frozenset(tuple(sorted((left, right), key=int)) for left, right in pairs)


def tour_distance(instance: dict, tour: Iterable[str]) -> int:
    matrix = distance_matrix(instance)
    index = {city_id: offset for offset, city_id in enumerate(instance_ids(instance))}
    value = tuple(tour)
    return sum(
        matrix[index[a]][index[b]]
        for a, b in zip(value, (*value[1:], value[0]))
    )


def retained_edge_fraction(tour: Iterable[str], incumbent: Iterable[str]) -> float:
    return len(edge_set(tour) & edge_set(incumbent)) / 14.0


def held_karp(instance: dict) -> dict:
    """Exact integer Held-Karp solver with one reproducible canonical witness."""
    matrix = distance_matrix(instance)
    n = len(matrix)
    # (mask,last) -> (cost, path excluding initial 0 but including last)
    dp: dict[tuple[int, int], tuple[int, tuple[int, ...]]] = {}
    for last in range(1, n):
        dp[(1 << (last - 1), last)] = (matrix[0][last], (last,))
    for size in range(2, n):
        next_dp: dict[tuple[int, int], tuple[int, tuple[int, ...]]] = {}
        for mask in range(1, 1 << (n - 1)):
            if mask.bit_count() != size:
                continue
            for last in range(1, n):
                bit = 1 << (last - 1)
                if not mask & bit:
                    continue
                prior_mask = mask ^ bit
                options = []
                for prior in range(1, n):
                    row = dp.get((prior_mask, prior))
                    if row is not None:
                        options.append((row[0] + matrix[prior][last], row[1] + (last,)))
                if options:
                    next_dp[(mask, last)] = min(options)
        dp.update(next_dp)
    full = (1 << (n - 1)) - 1
    candidates = []
    for last in range(1, n):
        cost, path = dp[(full, last)]
        tour = canonical_tour(("0", *(str(city) for city in path)))
        candidates.append((cost + matrix[last][0], tour))
    best_cost, best_tour = min(candidates)
    certificate = {
        "algorithm": "held-karp-v1",
        "exact_distance": best_cost,
        "canonical_optimal_tour": list(best_tour),
        "evaluator_fingerprint": EVALUATOR_FINGERPRINT,
    }
    certificate["certificate_sha256"] = sha256_hex(canonical_json(certificate))
    return certificate


def brute_force(instance: dict) -> tuple[int, tuple[str, ...]]:
    ids = tuple(row["id"] for row in instance["cities"])
    best: tuple[int, tuple[str, ...]] | None = None
    for tail in permutations(ids[1:]):
        tour = canonical_tour(("0", *tail))
        row = (tour_distance(instance, tour), tour)
        if best is None or row < best:
            best = row
    assert best is not None
    return best


def instance_problem_description(instance: dict) -> str:
    points = ", ".join(
        f"{row['id']}=({row['x']},{row['y']})" for row in instance["cities"]
    )
    return (
        "FINITE 14-CITY MANHATTAN TSP. Cities: " + points + ". Produce a Hamiltonian "
        "cycle beginning at city \"0\"; return to 0 is implicit. Minimise total "
        "Manhattan distance. Candidate content MUST be one JSON object exactly in "
        "this useful shape: {\"tour\":[\"0\",...,\"13\"],\"rationale\":\"short text\"}. "
        "The tour must contain every city ID exactly once and must not repeat 0 at the end."
    )


def score_feedback(history: list[dict]) -> str:
    lines = [
        "VERIFIER SCORE FEEDBACK (same rendering in every arm; lower is better):"
    ]
    valid = [row for row in history if row["valid"]]
    if not valid:
        lines.append("- no prior valid tours")
    else:
        for index, row in enumerate(valid):
            lines.append(
                f"- valid[{index:03d}] admission={row['admission_id']} "
                f"total_distance={row['distance']}"
            )
    return "\n".join(lines)


def ordinary_history_render(history: list[dict]) -> str:
    lines = ["RECENT VALID TOUR HISTORY (ordinary sequence representation):"]
    valid = [row for row in history if row["valid"]][-8:]
    if not valid:
        lines.append("- none")
    for row in valid:
        lines.append(
            f"- admission={row['admission_id']} "
            f"tour={','.join(row['canonical_tour'])}"
        )
    return "\n".join(lines)


def matrix_render(instance: dict) -> str:
    matrix = distance_matrix(instance)
    lines = ["FULL SYMMETRIC MANHATTAN-DISTANCE MATRIX (rows/columns 0..13):"]
    lines.extend(" ".join(str(value) for value in row) for row in matrix)
    return "\n".join(lines)


def incumbent_edges_render(incumbent: tuple[str, ...]) -> str:
    edges = sorted(edge_set(incumbent), key=lambda edge: (int(edge[0]), int(edge[1])))
    return "INCUMBENT UNDIRECTED EDGES (lexicographic endpoint order):\n" + "\n".join(
        f"- {left}--{right}" for left, right in edges
    )


def recent_edge_differences(history: list[dict], incumbent: tuple[str, ...]) -> str:
    incumbent_edges = edge_set(incumbent)
    lines = ["RECENT TOUR EDGE-DIFFERENCE SUMMARIES:"]
    for index, row in enumerate([item for item in history if item["valid"]][-8:]):
        edges = frozenset(tuple(edge) for edge in row["edges"])
        removed = sorted(incumbent_edges - edges, key=lambda edge: (int(edge[0]), int(edge[1])))
        added = sorted(edges - incumbent_edges, key=lambda edge: (int(edge[0]), int(edge[1])))
        lines.append(
            f"- recent[{index}] admission={row['admission_id']} "
            f"removed={';'.join(a+'--'+b for a,b in removed) or 'none'} "
            f"added={';'.join(a+'--'+b for a,b in added) or 'none'}"
        )
    return "\n".join(lines)


def treatment_context(
    arm: str,
    *,
    instance: dict,
    history: list[dict],
    incumbent: tuple[str, ...] | None,
    median_retained: float | None,
    failure_classes: list[str],
) -> str:
    feedback = score_feedback(history)
    ordinary = ordinary_history_render(history)
    if arm == "J0":
        return feedback + "\n\n" + ordinary
    if arm == "J1":
        return "\n\n".join((feedback, ordinary, MOVEMENT_DIRECTIVE))
    if arm == "J3":
        if incumbent is None:
            raise ValueError("J3 requires incumbent")
        return "\n\n".join((
            feedback,
            matrix_render(instance),
            incumbent_edges_render(incumbent),
            recent_edge_differences(history, incumbent),
            J3_PREFIX,
            MOVEMENT_DIRECTIVE,
        ))
    if arm == "J4":
        failures = ", ".join(sorted(set(failure_classes))) if failure_classes else "none"
        diagnostics = (
            "DETERMINISTIC VERIFIER DIAGNOSTICS:\n"
            "- incumbent_valid=true\n"
            "- strictly_better_valid_tour_certified=true\n"
            f"- recent_median_retained_edge_fraction={median_retained:.6f}\n"
            f"- recent_schema_or_validity_failure_classes={failures}"
        )
        return "\n\n".join(
            (feedback, ordinary, diagnostics, J4_PREFIX, MOVEMENT_DIRECTIVE)
        )
    if arm == "J6":
        return "\n\n".join((feedback, ordinary, J6_DIRECTIVE))
    raise ValueError(f"unknown arm: {arm}")


def branch_order(instance_seed: int, source_digest: str, prereg_digest: str) -> tuple[str, ...]:
    seed_bytes = f"{instance_seed}:{source_digest}:{prereg_digest}".encode("utf-8")
    seed_hex = sha256(seed_bytes).hexdigest()
    arms = ["J0", "J1", "J3", "J4", "J6"]
    random.Random(int(seed_hex, 16)).shuffle(arms)
    return tuple(arms)


def trigger_window(
    history: list[dict], *, incumbent: tuple[str, ...], optimum: int,
    r_med: float, r_low: float, successful_calls: int,
    hard_orbit_blocks: int = 0, operationally_quiescent: bool = True,
) -> dict:
    valid = [row for row in history if row["valid"]]
    window = valid[-8:]
    source_best = min((row["distance"] for row in valid), default=10**18)
    before = valid[:-8]
    before_best = min((row["distance"] for row in before), default=10**18)
    fractions = [retained_edge_fraction(row["canonical_tour"], incumbent) for row in window]
    headroom_ratio = (
        (source_best - optimum) / source_best if source_best < 10**18 and source_best else 0.0
    )
    improvements = [row for row in window if row["distance"] < before_best]
    payload = {
        "successful_calls": successful_calls,
        "valid_admissions": len(valid),
        "window_size": len(window),
        "source_best_distance": source_best,
        "exact_optimal_distance": optimum,
        "headroom_ratio": headroom_ratio,
        "window_improvements": len(improvements),
        "median_retained_edge_fraction": median(fractions) if fractions else None,
        "low_overlap_count": sum(value < r_low for value in fractions),
        "r_med": r_med,
        "r_low": r_low,
        "hard_orbit_blocks": hard_orbit_blocks,
        "operationally_quiescent": operationally_quiescent,
    }
    payload["eligible"] = bool(
        successful_calls >= 10
        and len(valid) >= 12
        and len(window) == 8
        and not improvements
        and payload["median_retained_edge_fraction"] >= r_med
        and payload["low_overlap_count"] <= 1
        and hard_orbit_blocks == 0
        and operationally_quiescent
        and source_best > optimum
        and headroom_ratio >= 0.03
    )
    payload["certified_completion"] = source_best == optimum
    return payload


def calibration_thresholds(
    histories: list[list[dict]], *, optima: list[int] | None = None
) -> dict | None:
    fractions: set[float] = set()
    for history in histories:
        valid_prefix: list[dict] = []
        for row in history:
            if not row["valid"]:
                continue
            valid_prefix.append(row)
            incumbent = min(
                valid_prefix,
                key=lambda item: (item["distance"], item["canonical_tour"]),
            )
            fractions.add(
                retained_edge_fraction(
                    row["canonical_tour"], incumbent["canonical_tour"]
                )
            )
    candidates = sorted(fractions | {0.60, 0.35}, reverse=True)
    valid_pairs = []
    for r_med in candidates:
        for r_low in sorted(candidates):
            if r_low > r_med:
                continue
            fired_instances = 0
            bad_fire = False
            for history_index, history in enumerate(histories):
                fired = False
                call_indices = sorted({int(row["call_index"]) for row in history})
                for call_index in call_indices:
                    prefix = [
                        row for row in history if int(row["call_index"]) <= call_index
                    ]
                    valid = [row for row in prefix if row["valid"]]
                    if call_index + 1 < 10 or len(valid) < 12:
                        continue
                    window = valid[-8:]
                    incumbent = min(valid, key=lambda item: (item["distance"], item["canonical_tour"]))
                    before_best = min((row["distance"] for row in valid[:-8]), default=10**18)
                    overlaps = [retained_edge_fraction(row["canonical_tour"], incumbent["canonical_tour"]) for row in window]
                    has_improvement = any(row["distance"] < before_best for row in window)
                    trips = median(overlaps) >= r_med and sum(value < r_low for value in overlaps) <= 1
                    if optima is not None:
                        source_best = min(row["distance"] for row in valid)
                        optimum = optima[history_index]
                        headroom = (
                            (source_best - optimum) / source_best if source_best else 0.0
                        )
                        trips = trips and source_best > optimum and headroom >= 0.03
                    first_call = min(int(row["call_index"]) for row in window)
                    gate_blocks = sum(
                        bool(row.get("gate_blocked"))
                        for row in history
                        if first_call <= int(row["call_index"]) <= call_index
                    )
                    trips = trips and gate_blocks == 0
                    if trips and has_improvement:
                        bad_fire = True
                    if trips and not has_improvement:
                        fired = True
                fired_instances += int(fired)
            if fired_instances >= 2 and not bad_fire:
                valid_pairs.append((r_med, r_low, fired_instances))
    if not valid_pairs:
        return None
    r_med, r_low, count = max(valid_pairs, key=lambda row: (row[0], -row[1], row[2]))
    return {"R_med": r_med, "R_low": r_low, "fired_instances": count}


@dataclass(frozen=True)
class Checkpoint:
    instance_seed: int
    source_state_digest: str
    incumbent: tuple[str, ...]
    history_digest: str
    remaining_calls: int
    remaining_tokens: int
    scheduler_cursor: None = None
    liveness: tuple = ()
    cooldowns: tuple = ()
    pending_queues: tuple = ()
    retry_state: tuple = ()

    def payload(self) -> dict:
        return {
            "schema": "deepreason-jolt-tsp-checkpoint-v3.1",
            "instance_seed": self.instance_seed,
            "source_state_digest": self.source_state_digest,
            "incumbent": list(self.incumbent),
            "history_digest": self.history_digest,
            "remaining_calls": self.remaining_calls,
            "remaining_tokens": self.remaining_tokens,
            "scheduler_cursor": self.scheduler_cursor,
            "liveness": list(self.liveness),
            "cooldowns": list(self.cooldowns),
            "pending_queues": list(self.pending_queues),
            "retry_state": list(self.retry_state),
        }
