"""narrate(harness) — the event log as chain-of-thought prose (spec §8).

A VIEW, not a type: a deterministic templated rendering of the append-only
history that reads like reasoning — proposals connected to attacks,
refutations, reinstatements, blocked rulings, and spawned problems with
logical connectors (and / but / so / maybe / however). No LLM call, no
randomness: connector choice rotates by event seq, so the same log always
narrates identically (replay-stable, like every view).
"""

from deepreason.informal.skeleton import parse_skeleton
from deepreason.ontology import Rule, SpawnTrigger

# Openers rotate deterministically within a class by seq — the but/and/or/
# maybe texture without nondeterminism. The first sentence takes none.
_OPENERS = {
    "progress": ("And", "So", "Then", "Meanwhile"),
    "setback": ("But", "However", "Yet"),
    "hedge": ("Maybe", "Perhaps", "Or maybe"),
    "consequence": ("So", "And so", "Thus"),
}

# Measure inputs that are bookkeeping, not narrative: accumulated and
# flushed as one deliberation aside rather than a sentence per call.
_NOISE_TAGS = (
    "trial-llm", "audit-llm", "conj-noregister", "synth-noregister",
    "batch-crit", "arg-crit", "hv-floor-nomeasure", "hv-nomeasure",
    "property-relevance-trial", "spec-generation",
)

_SPAWN_LINES = {
    SpawnTrigger.SUCCESSOR: "a successor problem took its place, carrying the refuted candidate's contract",
    SpawnTrigger.DISCRIMINATION: "rival survivors remained, so a discrimination problem was opened",
    SpawnTrigger.INTEGRATION: "two accepted-but-unrelated results invited an integration problem",
    SpawnTrigger.CONNECTION: "an isolated result was asked to connect to its neighbourhood",
    SpawnTrigger.REMOVE_ARBITRARINESS: "an accepted result measured arbitrary, so a sharpening problem was opened",
    SpawnTrigger.EXPLANATION_DEBT: "unexpected reach raised an explanation debt",
    SpawnTrigger.RESEARCH: "an observation-valued commitment demanded evidence, so a research problem was opened",
    SpawnTrigger.AUDIT_CRITIC: "the critic itself came under audit",
}

# Named-signal prose (checked BEFORE the _NOISE_TAGS startswith sweep, which
# would otherwise swallow the arg-crit-*/batch-crit-* variants).
_SIGNAL_LINES = {
    "browser-pass": ("progress",
                     "the candidate was rendered and driven in the browser and "
                     "passed every scripted step"),
    "browser-spec-overrun": ("hedge",
                             "the browser interaction spec was unusable — a spec "
                             "defect, not the candidate's fault"),
    "vision-crit": ("progress",
                    "the vision critic looked at the rendered screenshots and "
                    "found no visible fault"),
    "vision-crit-overridden-by-execution": ("hedge",
                                            "a visual complaint was overridden: "
                                            "the target's execution oracle passes"),
    "arg-crit-overridden-by-execution": ("hedge",
                                         "an argued case was overridden: the "
                                         "target's execution oracle passes"),
    "arg-crit-cx-rejected": ("setback",
                             "the critic's counterexample failed to ground, and "
                             "the rejection reason was echoed back for a retry"),
    "batch-crit-cx-retry": ("consequence",
                            "the overridden critics got one shared retry with "
                            "the gate's verdicts in hand"),
    "property-wipeout-quarantine": ("hedge",
                                    "a proposed property indicted every "
                                    "candidate at once, so its verdict was "
                                    "quarantined"),
    "experiment-design": ("progress",
                          "the experimenter proposed new input generators"),
    "property-design": ("progress",
                        "the property designer conjectured new correctness "
                        "checkers"),
    "disc-attempts-exhausted": ("consequence",
                                "an unresolvable rivalry hit its attempt cap "
                                "and was set aside as unresolved"),
    "embedder": ("progress",
                 "the run stamped its embedding geometry — model, library "
                 "versions, sentinel hash — so drift is detectable on the "
                 "record"),
    "embedder-fallback": ("setback",
                          "the configured embedding backend was unavailable, "
                          "so the run degraded to the hashing embedder"),
}

_BLOCK_LINES = {
    "ensemble-split": "the two judges disagreed, so the ruling was blocked rather than averaged",
    "referential-integrity": "the ruling failed to quote the exchange, so it was screened out",
    "paraphrase-flip": "the verdict flipped under paraphrase, so it carried no weight",
    "order-swap": "the verdict reversed when the candidates swapped places, so it was discarded",
    "unresolved-standard": "no standard resolved for the trial, so nothing was ruled",
}


def _snippet(harness, aid: str, limit: int = 90) -> str:
    artifact = harness.state.artifacts.get(aid)
    if artifact is None:
        return aid[:12]
    ref = artifact.content_ref
    text = ref[len("inline:"):] if ref.startswith("inline:") else ""
    skeleton = parse_skeleton(text) if text else None
    if skeleton is not None:
        text = skeleton.claim
    text = " ".join(text.split())
    return f"'{text[:limit]}'" if text else aid[:12]


def _school(harness, aid: str) -> str:
    artifact = harness.state.artifacts.get(aid)
    school = artifact.provenance.school if artifact else None
    return f" (from {school})" if school else ""


class _Prose:
    """Accumulates classified sentences into paragraphs, choosing openers
    deterministically and flushing deliberation asides."""

    def __init__(self) -> None:
        self.paragraphs: list[list[str]] = [[]]
        self._noise = 0
        self._first = True

    def aside(self, n: int = 1) -> None:
        self._noise += n

    def _flush_noise(self) -> None:
        if self._noise:
            self.paragraphs[-1].append(
                f"({self._noise} exchange{'s' if self._noise != 1 else ''} "
                "of deliberation along the way.)"
            )
            self._noise = 0

    def paragraph(self) -> None:
        self._flush_noise()
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def say(self, clazz: str, text: str, seq: int) -> None:
        self._flush_noise()
        if self._first:
            sentence = text[0].upper() + text[1:]
            self._first = False
        else:
            options = _OPENERS[clazz]
            opener = options[seq % len(options)]
            sentence = f"{opener} {text}"
        if not sentence.endswith((".", ".)", "?")):
            sentence += "."
        self.paragraphs[-1].append(sentence)

    def render(self) -> str:
        self._flush_noise()
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def narrate(harness, *, upto_seq: int | None = None, window: int | None = None) -> str:
    """Render the log (or its recent ``window``) as connected reasoning
    prose. Deterministic: same log, same words."""
    if window is not None:
        events = list(harness.recent_events(window))
    else:
        events = list(harness.log.read(upto_seq=upto_seq))
    if not events:
        return "(nothing has happened yet)"

    transitions: dict[int, list[tuple[str, str | None, str]]] = {}
    for seq, aid, old, new in harness.transitions():
        transitions.setdefault(seq, []).append((aid, old, new))

    prose = _Prose()
    for event in events:
        _narrate_event(harness, event, prose)
        # Status transitions land after the event that caused them.
        for aid, old, new in transitions.get(event.seq, ()):
            if old is None and new == "accepted":
                continue  # plain registration: not a turn in the reasoning
            if old == "refuted" and new == "accepted":
                prose.say("setback",
                          f"the attack itself fell, and {aid[:12]} was reinstated",
                          event.seq)
            elif new == "refuted":
                prose.say("consequence", f"{aid[:12]} was refuted", event.seq)
            else:
                prose.say("hedge", f"{aid[:12]} became {new}", event.seq)
    return prose.render()


def _narrate_event(harness, event, prose: _Prose) -> None:
    seq, inputs = event.seq, list(event.inputs)
    tag = inputs[0] if inputs else ""

    if event.rule == Rule.SPAWN:
        for pid in event.outputs:
            problem = harness.state.problems.get(pid)
            if problem is None:
                continue
            trigger = problem.provenance.trigger
            if trigger == SpawnTrigger.SEED:
                prose.paragraph()
                desc = " ".join(problem.description.split())[:140]
                prose.say("progress", f"a problem was posed: {desc}", seq)
            else:
                prose.paragraph()
                line = _SPAWN_LINES.get(trigger, f"a {trigger.value} problem was opened")
                prose.say("progress", line, seq)
        return

    if event.rule == Rule.CONJ:
        artifacts = [a for a in event.state_diff.a_add]
        if not artifacts:
            return
        head = artifacts[0]
        extra = f", and {len(artifacts) - 1} sibling(s) with it" if len(artifacts) > 1 else ""
        prose.say("progress",
                  f"the conjecturer{_school(harness, head)} proposed "
                  f"{_snippet(harness, head)}{extra}", seq)
        return

    if event.state_diff.att_add:
        # Attack edges narrate whatever rule carried them (Crit, a plain
        # registration with warrants, a Merge supplying a dangling target).
        for attacker, target in event.state_diff.att_add:
            prose.say("setback",
                      f"a critic attacked {target[:12]}: {_snippet(harness, attacker)}",
                      seq)
        return

    if event.rule == Rule.CRIT:
        if event.state_diff.a_add:
            prose.say("hedge",
                      f"a critic spoke but attacked nothing: "
                      f"{_snippet(harness, event.state_diff.a_add[0])}", seq)
        return

    if event.rule == Rule.RESEED:
        prose.say("progress", "a school was reseeded to a fresh stance", seq)
        return

    if event.rule == Rule.MEASURE:
        # Named-signal prose FIRST: the noise sweep below matches by
        # startswith, so 'arg-crit' would otherwise swallow
        # 'arg-crit-overridden-by-execution' etc.
        if tag == "cycle":
            n = event.inputs[1] if len(event.inputs) > 1 else "?"
            focus = event.inputs[2] if len(event.inputs) > 2 else "-"
            prose.paragraph()
            prose.say("progress",
                      (f"cycle {n} turned to {focus}" if focus != "-"
                       else f"cycle {n} found nothing to work"), seq)
            return
        if tag in _SIGNAL_LINES:
            kind, line = _SIGNAL_LINES[tag]
            prose.say(kind, line, seq)
            return
        if any(t.startswith(_NOISE_TAGS) or t in _NOISE_TAGS for t in inputs):
            prose.aside()
            return
        if tag.startswith("gate:"):
            reason = tag.split(":", 1)[1]
            prose.say("hedge",
                      f"this had been tried before — the gate blocked a "
                      f"candidate ({reason})", seq)
            return
        if tag.startswith("trial-blocked:"):
            reason = tag.split(":", 1)[1]
            line = _BLOCK_LINES.get(reason, f"a trial was blocked ({reason})")
            prose.say("setback", line, seq)
            return
        if tag.startswith("audit-hit:"):
            prose.say("setback",
                      "an audit caught the judge flipping, and the old ruling's "
                      "validity came under attack", seq)
            return
        if tag.startswith("intervention:"):
            prose.say("progress",
                      f"the response ladder stepped in ({tag.split(':', 1)[1]})", seq)
            return
        if tag == "dropped-call":
            tokens = event.llm.tokens if event.llm else 0
            prose.say("setback",
                      f"a call burned {tokens} tokens but produced nothing usable",
                      seq)
            return
        for aid, value in event.state_diff.hv_set.items():
            prose.say("hedge",
                      f"{aid[:12]} measured hard-to-vary at {value:.2f}", seq)
        for aid, value in event.state_diff.reach_set.items():
            if value > 0:
                prose.say("hedge",
                          f"{aid[:12]} reached {int(value)} problem(s) it wasn't "
                          f"built for", seq)
            else:
                prose.say("hedge", f"{aid[:12]} lost its reach", seq)
        return
    # Register / Merge / Reveal / Adj: quiet unless a transition follows.
