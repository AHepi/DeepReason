"""M2 — stance rotation + problem turnover (MINI_PLAN §3.5).

Fast rotation (decay 5) measured best on BOTH novelty (late/early 0.973 vs
0.846 control) and school separation (0.690 vs 0.545); measured on n=1 arm,
so the M2 smoke doubles as its second measurement — if late/early degrades,
fall back to 10 and note it. Problem turnover is the strongest anti-basin
force measured (the only run whose novelty ROSE, 1.12): never loop a dry
problem — that is the 4.3x burn.
"""

# The parent's one-time global curation (spec §11.1), kept verbatim.
STANCE_LIBRARY = {
    "mechanist": "demand a causal mechanism",
    "skeptic": "counterexample first",
    "unifier": "seek the covering principle",
    "empiric": "anchor in cases",
    "formalist": "derivation first",
    "historicist": "precedent and succession",
    "adversary": "strongest attack on the incumbent",
    "minimalist": "parsimony pressure",
}
_STANCES = list(STANCE_LIBRARY)

STANCE_DECAY = 5  # conjecture calls before a stance rotates regardless
TURNOVER_K = 8    # draws without a new distinct survivor => problem is dry


class Rotation:
    """One active stance; rotate on (a) the orbit detector naming this
    stance's school, or (b) stance age exceeding STANCE_DECAY conjectures."""

    def __init__(self, decay: int = STANCE_DECAY, start: str | None = None) -> None:
        self.decay = decay
        self.stance = start or _STANCES[0]
        self.age = 0
        self.rotations = 0

    @property
    def directive(self) -> str:
        return STANCE_LIBRARY[self.stance]

    def tick(self) -> None:
        self.age += 1

    def due(self, orbit_school: str | None) -> str | None:
        """Reason to rotate now, or None."""
        if orbit_school is not None and orbit_school == self.stance:
            return f"orbit:{orbit_school}"
        if self.age >= self.decay:
            return f"decay:{self.age}"
        return None

    def rotate(self) -> str:
        self.stance = _STANCES[(_STANCES.index(self.stance) + 1) % len(_STANCES)]
        self.age = 0
        self.rotations += 1
        return self.stance


class Turnover:
    """Per-problem novelty budget: K draws (conjecture calls) without a new
    distinct survivor => advance to the next problem in the queue."""

    def __init__(self, k: int = TURNOVER_K) -> None:
        self.k = k
        self.dry_draws = 0

    def draw(self, new_survivors: int) -> None:
        self.dry_draws = 0 if new_survivors > 0 else self.dry_draws + 1

    @property
    def dry(self) -> bool:
        return self.dry_draws >= self.k

    def reset(self) -> None:
        self.dry_draws = 0
