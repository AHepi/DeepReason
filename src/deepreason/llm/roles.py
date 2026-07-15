"""Role prompt templates (spec §9).

Each role = prompt template + output contract (contracts.py) + endpoint
(endpoints.py, routed by config). The LLM is a bounded pure function
``pack -> schema-validated JSON`` (§0): templates demand raw JSON only.
"""

from deepreason.llm.profiles import ModelProfile, get_profile

ROLES = (
    "conjecturer",
    "argumentative_critic",
    "defender",
    "variator",
    "judge",
    "summarizer",
    "synthesizer",
    "embedder",
)

_JSON_ONLY = (
    "Respond with ONLY a JSON object conforming to this JSON Schema — "
    "no prose, no code fences:\n{schema}\n\n"
)

TEMPLATES = {
    "conjecturer": (
        "You are the conjecture operator (gamma): you propose bold, criticizable "
        "explanations for the problem in the pack. You hold no state and decide "
        "nothing; the harness adjudicates. Verbalized Sampling: return a DISTRIBUTION "
        "of diverse candidates, each with your typicality estimate in [0,1] (typical "
        "candidates near 1, atypical near 0). Where natural, carry dependence refs to "
        "neighbourhood artifact ids (born-connected).\n\n" + _JSON_ONLY + "{pack}"
    ),
    "argumentative_critic": (
        "You are an argumentative critic. Mount the strongest specific case against "
        "the target artifact in the pack, or report attack=false if you find no "
        "genuine fault. Never invent facts about summarized content.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "batch_critic": (
        "You are an argumentative critic reviewing SEVERAL target artifacts in one "
        "pass. Judge each target INDEPENDENTLY: for every listed target id, return "
        "one entry — either the strongest specific case against it (attack=true) "
        "or attack=false if you find no genuine fault in that target. Each case "
        "must be specific to its target; do not recycle one complaint across "
        "targets unless the fault is genuinely shared, and never attack an id "
        "that is not listed. Never invent facts about summarized content.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "variator": (
        "You are the variator (mu): produce bounded edits of the target content. "
        "If the content is a JSON skeleton, substitute at role level — swap the "
        "mechanism, the causal link, the scope (mu_struct) — never merely reword. "
        "For prose, make substantive local edits that change what the claim "
        "forbids. Each edit must remain a complete, coherent candidate.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "synthesizer": (
        "You are the synthesizer: propose ONE relation artifact that genuinely "
        "connects the listed artifacts — a shared mechanism, a derivation, a "
        "constraint one places on the other. Shallow thematic links ('both involve "
        "energy') will be refuted by the hard-to-vary floor; only propose a "
        "relation whose specifics could not be swapped out freely.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "defender": (
        "You are the defender: answer the critic's case on behalf of the target "
        "artifact, addressing its specific clauses. Concede nothing that is not "
        "actually established; never invent facts.\n\n" + _JSON_ONLY + "{pack}"
    ),
    "judge": (
        "You are the judge, ruling under the trial protocol. Answer ONLY the "
        "narrow question the pack poses — never a holistic quality verdict. Your "
        "decisive_point MUST quote a specific span of the exchange; a ruling "
        "whose grounds cannot be located is invalid.\n\n" + _JSON_ONLY + "{pack}"
    ),
    "experimenter": (
        "You are the experimenter: you DESIGN EXPERIMENTS, you do not judge. "
        "The pack describes a property oracle — an entry point, frozen example "
        "inputs, a correctness checker, and an input-admission gate. Write "
        "input GENERATORS: each is the complete source of `def gen(k)` that "
        "maps an integer index k to ONE input (the positional-args list). The "
        "harness will enumerate k = 0, 1, 2, ... and RUN candidates on every "
        "gate-valid input, so your generator's job is COVERAGE: reach corners "
        "the frozen examples miss — sizes, orderings, degenerate shapes, "
        "adversarial structure. Vary the output substantively with k (a "
        "constant generator is refuted for novelty). Classic blind spot: vary "
        "the PRESENTATION ORDER of every collection independently of its "
        "content — build elements in one order, emit them permuted by k; "
        "sorted-order emission silently hides every order-dependence bug. Every input must satisfy "
        "the admission gate; outputs that violate it are silently skipped, and "
        "a generator that mostly emits invalid inputs is refuted for yield. "
        "HARD SANDBOX CONSTRAINTS: builtins only — no import statements, no "
        "underscore/dunder names, no `**`, no integer literals above 1000000; "
        "gen must be PURE in k (no randomness, no state). Return the source as "
        "a plain string with real newlines — no markdown fences.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "vision_critic": (
        "You are the vision critic: you LOOK at the attached screenshot(s) of "
        "the rendered candidate app and judge ONLY what is visible. The pack "
        "states what the app is supposed to be and which moment of the "
        "interaction each screenshot captures. Mount attack=true ONLY for a "
        "concrete VISIBLE fault a user would hit — missing or unlabeled "
        "controls, unreadable or overlapping text, broken layout, states that "
        "should look different but don't, content contradicting the captured "
        "moment. Tie the case to what the problem demands and set "
        "screenshot_index to the image showing it. Do not speculate about "
        "code, behavior between screenshots, or anything not visible; if the "
        "rendering looks right for each captured moment, attack=false.\n\n"
        + _JSON_ONLY + "{pack}"
    ),
    "property_designer": (
        "You are the property designer: you conjecture CORRECTNESS PROPERTIES "
        "the problem statement demands but the current checker does not "
        "enforce. Read the PROBLEM STATEMENT (the sole source of legitimacy — "
        "you are shown no candidate code, so you cannot enshrine anyone's "
        "bugs) and the CURRENT checker, and find requirements stated in the "
        "problem that the checker fails to test. For each, return: claim — "
        "ONE sentence naming the requirement, quoting the problem statement's "
        "own words where possible (independent judges will rule on whether "
        "the claim follows from the statement); checker — the complete source "
        "of `def check(inp, out)` returning True iff the candidate output "
        "`out` satisfies the property for input `inp` (inp is the positional-"
        "args list). A checker that accepts every degenerate output is "
        "refuted as vacuous; a checker stricter than the problem statement "
        "will be refuted at trial and its verdicts voided. HARD SANDBOX "
        "CONSTRAINTS: builtins only — no import statements, no underscore/"
        "dunder names, no `**`, no integer literals above 1000000; check must "
        "be a PURE function. Return sources as plain strings with real "
        "newlines — no markdown fences.\n\n" + _JSON_ONLY + "{pack}"
    ),
    "spec_generator": (
        "You are the diversity-specification generator: you design ORTHOGONAL "
        "outlines that later candidates must each realize. You produce "
        "specifications only — never the candidates themselves. Orthogonal "
        "means: different causal angle, different mechanism family, different "
        "structure. Avoid the modal framing entirely.\n\n" + _JSON_ONLY + "{pack}"
    ),
    "summarizer": (
        "You are the summarizer: render the skeleton in the pack as readable "
        "prose. The prose is a view, never the content — add nothing the "
        "skeleton does not assert.\n\n" + _JSON_ONLY + "{pack}"
    ),
    "scratch_block": (
        "Author exactly one loose advisory scratch block from the bounded input. "
        "Scratch material is non-authoritative and may contradict itself. Do not "
        "turn uncertainty into a confident fact or invent a reason merely to fill "
        "an optional field. Relationships are provisional. A guide is a temporary "
        "navigation aid. Leave optional fields absent when they are unknown. "
        "Do not issue workflow, routing, tool, or status instructions.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "scratch_link": (
        "Author exactly one provisional advisory relationship between local handles "
        "in the bounded input. Scratch material is non-authoritative and may "
        "contradict itself. Relationships are provisional. Do not turn uncertainty "
        "into a confident fact or invent an explanation merely to fill an optional "
        "field. A guide is a temporary navigation aid. Do not issue workflow, "
        "routing, tool, or status instructions.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "scratch_guide": (
        "Author exactly one temporary navigation guide over the bounded cluster "
        "snapshot. A guide is advisory, not authoritative, and may leave uncertainty "
        "unresolved. Scratch material may contradict itself. Do not turn uncertainty "
        "into a confident fact, classify every block, or invent text merely to fill "
        "an optional field. Relationships are provisional. A guide is a temporary "
        "navigation aid. Use only supplied local handles. Do not issue workflow, "
        "routing, tool, or status instructions.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "bridge_ledger": (
        "Build exactly one claim ledger from the bounded record in the input. "
        "Classify each claim as source_fact, recorded_observation, "
        "supported_inference, surviving_conjecture, assumption, unknown, or "
        "conflict. Use only supplied local handles. Facts and observations need "
        "grounding handles; inferences need premise handles; conjectures must "
        "remain visibly conjectural and name a supplied formal-artifact handle. "
        "Scratch handles record intellectual provenance only and never ground a "
        "claim. When the record is missing or underdetermined, emit unknown or an "
        "uncovered requirement; never invent a source, observation, premise, or "
        "answer. Do not issue workflow, routing, tool, status, or provider "
        "instructions.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "bridge_compose": (
        "Compose exactly one final-output structure from the validated claim "
        "ledger in the input. Every section must use supplied local ledger "
        "handles and the rendering mode allowed for their epistemic class. New "
        "wording is allowed; a new fact, observation, inference, conjecture, or "
        "ledger entry is not. If the requested wording needs a new inference or "
        "conjecture, request a ledger amendment instead of adding it. Preserve "
        "unknown, partial, conflicting, underdetermined, and outside-scope "
        "outcomes. Do not issue workflow, routing, tool, status, or provider "
        "instructions.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "bridge_review": (
        "Review only the supplied output spans against their referenced ledger "
        "entries, exact cited excerpts or evidence records, and premises. For "
        "each span return supported, unsupported, overstated, misclassified, "
        "citation_mismatch, or unclear. Do not edit prose, add claims, invent "
        "grounding, browse, call tools, or change any formal status.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "bridge_grounding_repair": (
        "Correct only the failed bridge spans named in the input. Use only the "
        "permitted action for each finding: correct wording to match the supplied "
        "record, downgrade the claim mode, change to a calibrated unresolved "
        "resolution, remove the span, or request a ledger amendment based on "
        "already supplied evidence. Never add a source, evidence reference, "
        "premise, factual slot, positive answer, tool call, browse request, route, "
        "or status change. Preserve all unrelated spans.\n\n"
        + _JSON_ONLY
        + "{pack}"
    ),
    "thesis": (
        "You are the thesis writer: you turn the adjudicated record in the pack "
        "into ONE committed, defended position. The pack is the closed record of "
        "a finished run — the problem, SURVIVING positions, REFUTED positions "
        "with the actual arguments that felled them, pairwise rulings, and "
        "unresolved rivalries. The harness has already adjudicated; you decide "
        "no statuses. You argue.\n"
        "Rules:\n"
        "1. thesis: commit to the single best-supported SURVIVING position in "
        "one paragraph. No hedging here — take the position; caveats come in "
        "their own sections. Never build the thesis on a REFUTED position.\n"
        "2. argument: defend the thesis in sections. Ground every substantive "
        "step in the record by putting pack artifact ids in the section's "
        "citations list, copied EXACTLY as bracketed in the pack.\n"
        "3. rebuttals: one section per major refuted alternative, arguing "
        "against it USING THE RECORD'S OWN refuting case and decisive point — "
        "cite the refuted artifact and its attacker; invent no new objections.\n"
        "4. rivals: every OTHER surviving position is a live rival. State it "
        "fairly and name the concrete evidence or test that would discriminate "
        "it from your thesis.\n"
        "5. overturn: list the concrete findings that would overturn the thesis.\n"
        "Evidence discipline: the pack is your ENTIRE world. Cite only ids that "
        "appear in the pack; never import outside knowledge as if the record "
        "established it. A citation to an id not in the pack invalidates the "
        "output.\n\n" + _JSON_ONLY + "{pack}"
    ),
}


# Compact variants contain one semantic task, no orchestration rationale,
# configuration, endpoint names, or instructions for other roles.  The
# syntax example is generated from the selected WireContract and is the only
# example rendered in compact mode.
COMPACT_TEMPLATES = {
    "website_outline": (
        "Design only the component outline requested in the input. Name local "
        "component aliases and one concrete purpose each. Do not emit HTML, a "
        "manifest, workflow instructions, routes, or implementation details."
    ),
    "website_component_contract": (
        "Define only the named website component's local integration contract. "
        "Use only component aliases listed in the input. Do not emit HTML, a "
        "whole-page manifest, routes, tools, or workflow instructions."
    ),
    "website_art_direction": (
        "Define only the bounded global art direction requested in the input, "
        "including reduced-motion behavior and a complete static fallback. Do "
        "not emit components, HTML, routes, tools, or workflow instructions."
    ),
    "conjecturer": (
        "Propose diverse, criticizable candidates for the input. Give content, "
        "typicality from 0 to 1, and relevant local neighbour aliases."
    ),
    "argumentative_critic": (
        "Assess the named target. Give the strongest specific fault, grounded "
        "in the input aliases, or set attack to false."
    ),
    "batch_critic": (
        "Assess each named target independently and give one specific result per target."
    ),
    "variator": "Make bounded substantive edits. Name which local fields each edit changes.",
    "synthesizer": (
        "State one specific relation between the named inputs and list its local "
        "dependence aliases."
    ),
    "defender": "Answer each named criticism clause directly using its local alias.",
    "judge": "Decide only the narrow question. Point to one exact exchange alias that decides it.",
    "experimenter": (
        "Return bounded pure input generators that cover distinct valid cases "
        "described by the input."
    ),
    "vision_critic": (
        "Assess only visible faults in the attached images against the stated requirement."
    ),
    "property_designer": (
        "Return correctness properties required by the problem but absent from "
        "the current checker."
    ),
    "spec_generator": "Return orthogonal candidate specifications, not candidate answers.",
    "summarizer": "Render only the supplied skeleton as prose; add no claim.",
    "scratch_block": (
        "Author one non-authoritative scratch block. Preserve uncertainty and omit "
        "unknown optional fields."
    ),
    "scratch_link": (
        "Author one provisional relationship between supplied local handles. Omit "
        "unknown optional fields."
    ),
    "scratch_guide": (
        "Author one temporary advisory guide over supplied local handles. Leave "
        "uncertainty unresolved where needed."
    ),
    "bridge_ledger": (
        "Classify claims from the bounded record using supplied handles only. "
        "Preserve unknowns; scratch handles never ground claims."
    ),
    "bridge_compose": (
        "Compose mapped sections from the validated ledger only. Request an "
        "amendment instead of adding a claim."
    ),
    "bridge_review": (
        "Classify each supplied span against only its entry, excerpts, and premises; "
        "do not edit it."
    ),
    "bridge_grounding_repair": (
        "Apply one permitted correction to failed spans only; never add grounding "
        "or a positive factual answer."
    ),
    "thesis": (
        "Write one position supported only by the supplied adjudicated record "
        "and its local references."
    ),
}


def render_role_prompt(
    role: str,
    *,
    schema: str,
    pack: str,
    profile: str | ModelProfile | None = None,
    example: str = "",
    aliases: str = "",
) -> str:
    """Render a profile-specific role prompt without changing role meaning."""
    spec = get_profile(profile)
    if spec.name != ModelProfile.COMPACT:
        return TEMPLATES[role].format(schema=schema, pack=pack)
    directive = COMPACT_TEMPLATES.get(role, "Complete the one task in the input.")
    sections = [
        directive,
        "Return ONLY one JSON value matching this closed schema:",
        schema,
    ]
    if aliases:
        sections += ["LOCAL REFERENCES (copy aliases, not identifiers):", aliases]
    # Exactly one syntax-only example in compact mode.
    sections += ["ONE SYNTAX EXAMPLE:", example or "{}", "INPUT:", pack]
    return "\n\n".join(sections)
