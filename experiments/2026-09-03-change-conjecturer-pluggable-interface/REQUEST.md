# REQUEST — the conjecturer's brief and form as a pluggable, configurable interface

Tranche: `experiments/2026-09-03-change-conjecturer-pluggable-interface/`
Opened: 2026-09-03
Phase family: `dr-change-orchestrator` (capture → spec → plan → execute → validate → deliver)
Phase reached by this document: `dr-capture-request`
Base: `main` at `2d84a86cd`
Branch: `claude/conjecturer-pluggable-interface-bnyrhx`

**This window is DESIGN PHASE ONLY.** It ends at FEASIBILITY.md + SPEC.md +
CHECKLIST.md, approved by the operator. No production code is written here.

---

## 1. The operator's words, VERBATIM (2026-09-03)

This section is the authority. Nothing below it may contradict it, and it is
never edited — only appended to.

> "History should be in evidence. That's a good move.
>  But I'm still unsure what to do with episodes.
>  For now, Can you write a prompt that makes conjecturer for a pluggable
>  interface? So evidence gets a plugin, history gets a plugin,
>  neighbouring conjecturers get a plugin. The plugin should be generic
>  so the information an LLM sees can be increased or shrunk at will. It
>  shouldn't be typed. And formatting can be done with the plugin. i want
>  to test freely how conjecturers respond to various input format. And
>  the form that needs filling out also needs to be adaptable so it can
>  be adjusted for an LLMs capabilities or desired output behaviour. And
>  again, these must be configurable with defaults..For now, figuring out
>  how it might be achieved is the first step. Then creating a spec that
>  can be worked on later."

## 1a. AMENDMENT 1 — the operator's words, VERBATIM (2026-09-03)

Received mid-phase, appended before it was acted on, per the ledger rule
(`dr-change-orchestrator`, "The ledger rule").

> "I just realised conjectures are not uniform. They aren't strictly
>  typed, but their input interface influences its relationship with the
>  epistemic state at large. And it's relationship with it materially
>  changes its outputs. Success at filling out a forms appears to be a
>  weak point because the machine doesn't accommodate the material affect
>  an input has on output. Outputs need strict minimum standards, but
>  maybe adapting the accepted outputs so they compile is something worth
>  doing. I ran a study that looks at why LLMs keep failing, and they
>  appear to respond differently to different inputs in a consistent way.
>  ... after perfecting history injections, change the artifact, then
>  measure how it's behaviour changes with respect to the epistemology."

**Operator-supplied evidence, NOT ingested.** The amendment refers to "a study
that looks at why LLMs keep failing". Its content was not supplied with the
message. It is recorded here as an OUTSTANDING INPUT (see §5, Q5): when the
operator supplies it, it is quoted into this file as operator-supplied
evidence — never as authority over the record. Per CLAUDE.md's evidence
discipline, model prose is never evidence; the census in FEASIBILITY.md is the
record-side instrument that answers the same question.

---

## 2. Requirements, numbered

Derived by splitting §1 and §1a into separately-checkable obligations. Each
carries the clause it comes from. No requirement is ever deleted — only marked
`superseded-by:<n>` or `deferred (operator approved <where>)`.

### From §1 (the original request)

**R1 — the conjecturer's brief becomes a pluggable interface.**
Source: "Can you write a prompt that makes conjecturer for a pluggable
interface?" Scope note: the operator's sentence is elliptical; the object of
"makes ... for a pluggable interface" is fixed by the three examples that
immediately follow it (evidence, history, neighbouring conjecturers), all of
which are INPUT SECTIONS of the conjecturer's brief. Read as: the material the
conjecturer seat is shown is assembled from plugins, not from a fixed renderer.

**R2 — evidence gets a plugin.**
Source: "So evidence gets a plugin".

**R3 — history gets a plugin.**
Source: "history gets a plugin". Related to the operator's opening line,
"History should be in evidence. That's a good move." — history is IN the
evidence family, and also gets its own plugin.

**R4 — neighbouring conjecturers get a plugin.**
Source: "neighbouring conjecturers get a plugin".

**R5 — the plugin interface is GENERIC.**
Source: "The plugin should be generic". One interface serves all three of
R2/R3/R4 and any future section; there is no per-section bespoke interface.

**R6 — information shown to the LLM can be increased or shrunk at will.**
Source: "so the information an LLM sees can be increased or shrunk at will."
Read as: every plugin exposes quantity/extent knobs, settable without a code
edit.

**R7 — the plugin is NOT TYPED.**
Source: "It shouldn't be typed." Verbatim; the monitor's reading of what this
constrains is at §3 M1, and it is a reading, not the operator's words.

**R8 — formatting can be done within the plugin.**
Source: "And formatting can be done with the plugin."

**R9 — free testing of how conjecturers respond to various input formats.**
Source: "i want to test freely how conjecturers respond to various input
format." This is a capability requirement on the DELIVERABLE (varying a format
must be cheap and repeatable), not merely a wish.

**R10 — the FORM that needs filling out is adaptable.**
Source: "And the form that needs filling out also needs to be adaptable so it
can be adjusted for an LLMs capabilities or desired output behaviour."
Two named adjustment axes: (a) an LLM's capabilities, (b) desired output
behaviour.

**R11 — all of it configurable, with defaults.**
Source: "And again, these must be configurable with defaults.." The "again"
points at the standing modularity law (CLAUDE.md, 2026-08-26) and the
maximum-configurable-surface law (2026-08-29 P9).

**R12 — this phase produces feasibility first, then a spec.**
Source: "For now, figuring out how it might be achieved is the first step.
Then creating a spec that can be worked on later." Binding on THIS window:
FEASIBILITY.md before SPEC.md; SPEC.md is written to be executed later, by
someone else, from the artifacts alone.

**R13 — episodes are NOT decided here.**
Source: "But I'm still unsure what to do with episodes." An explicit statement
of unresolved intent. Nothing in this tranche decides what episodes are or
does anything with them.

### From §1a (Amendment 1)

**R14 — conjectures are not uniform, and the input interface materially
changes the output.**
Source: "conjectures are not uniform. They aren't strictly typed, but their
input interface influences its relationship with the epistemic state at large.
And it's relationship with it materially changes its outputs." Read as a
premise the design must accommodate, not as a change request on its own.

**R15 — form-filling failure is a named weak point the machine does not
accommodate.**
Source: "Success at filling out a forms appears to be a weak point because the
machine doesn't accommodate the material affect an input has on output."

**R16 — outputs need strict minimum standards.**
Source: "Outputs need strict minimum standards". A FLOOR requirement: whatever
becomes adaptable, something does not.

**R17 — adapting accepted outputs so they compile is worth doing.**
Source: "but maybe adapting the accepted outputs so they compile is something
worth doing." Hedged by the operator ("maybe ... worth doing"), so it is
captured as a requirement to PRICE and RECOMMEND, not as an approved
obligation.

**R18 — LLMs respond differently to different inputs, consistently.**
Source: "I ran a study that looks at why LLMs keep failing, and they appear to
respond differently to different inputs in a consistent way." A claim from
operator-held evidence not yet supplied (§5 Q5). It motivates measurement; it
is not itself admitted as record evidence.

**R19 — sequence: history injections first, then the artifact, then measure.**
Source: "after perfecting history injections, change the artifact, then
measure how it's behaviour changes with respect to the epistemology."
Three ordered steps, each of which must be separable.

---

## 3. MONITOR'S READING — NOT the operator's words

Everything in this section is interpretation by the monitor, supplied with the
window instruction and with Amendment 1. It is kept separate so a later reader
can tell authority from reading. Where a reading and the operator's words could
diverge, the words win.

### M1 — the brief becomes an ordered list of section plugins
The conjecturer's brief ("pack") becomes an ORDERED LIST OF SECTION PLUGINS
chosen and parameterised by configuration. Each plugin owns one source of
information (the problem, the checks, open criticisms, evidence incl.
history-as-evidence, the neighbourhood, the live neighbourhood, school stance,
scratch, the closing directive, the question restated) and owns its own
FORMATTING. "Not typed" (R7) means the plugin's OUTPUT is free text the harness
does not interpret; the RECORD of what ran stays typed (which plugins, which
version, which parameters, how many bytes each rendered) — that is the existing
pack-plan / exposure-receipt family, not a new one.

### M2 — knobs, and today's values as defaults
"Increased or shrunk at will" (R6) = every plugin exposes its knobs as
parameters: how many items, whole or distilled, head length, ordering, whether
to include failed/refuted lineage, etc. Today's values are the DEFAULTS.
Acceptance: the default configuration renders a pack BYTE-IDENTICAL to today's
on a fixed record. Nothing changes unless someone configures it.

### M3 — the form has two halves, wire and parse
The FORM (R10) is a registered, versioned artifact selectable per seat, with two
halves that must be kept distinct: the WIRE form the model sees (schema or prose
instructions, adjustable per model capability) and the PARSE that maps a reply
into the harness's internal typed candidate, which does not change. Wire form
varies; the internal artifact does not.

### M4 — the modularity law's three layers, and who may author a plugin
Registry of section plugins and forms (VERSIONED), per-seat layout as
configuration (FREE), a protocol for adding a plugin without a source edit
(FROZEN change protocol). Operator-authored plugins load from a home-directory
location the way model profiles do; an operator's plugin is trusted (the
operator authors treadle tasks on the same basis); nothing model-authored is
ever a plugin. Formatting without code — a template layer — is worth pricing
alongside code plugins.

### M5 — scope is the conjecturer seat
Scope: the CONJECTURER seat. The critic and other seats follow on the same
interface; SPEC.md names the seam but does not design them.

### M6 — episodes get a slot and no more
Episodes are NOT decided (R13); the spec leaves a plugin slot where a generator
pool could be rendered and says no more.

### M7 (Amendment 1) — wire form varies, artifact and its checks do not
Two halves, named and kept apart: the WIRE FORM (what the model is asked to
write, how leniently it is read back) may vary per model and per experiment; the
ARTIFACT that enters the epistemic state (claim, commitments, discharges) and
every admission check it faces do not vary. "Strict minimum standards" (R16) =
the artifact and its checks. A lenient reader that normalises a looser reply
into the same typed artifact is in scope (R17); any leniency that changes what
is admitted, ranked, immune, or refuted is out of scope and a STOP.

### M8 (Amendment 1) — failure is a measured, input-shaped quantity
FEASIBILITY.md adds a census over committed roots (P-S1, P-A1, P-A2, the M1
arms): every conjecturer reply classified by why it failed (cut off at the cap,
wrong structure, missing discharge, semantic rejection) per model and per pack
shape. The operator's own study of why LLMs fail is ingested into REQUEST.md as
operator-supplied evidence, quoted, never as authority over the record.

### M9 (Amendment 1) — artifact SHAPE is an experimental variable, never a
### privilege
Artifact SHAPE is an experimental variable of the form registry, not a new kind:
the experiment recipe gains "hold the brief, change the form, measure admission
rate, diversity, and criticism outcomes", blind-judged. Shape must never buy
rank, immunity, or evidence (formalism-optional law); the architecture test
asserts it.

### M10 (Amendment 1) — sequence
Sequence, per the operator (R19): history first, then artifact shape, each as
its own measured step; the spec orders the recipe accordingly.

---

## 4. Map preflight — resolved ids

Per `dr-drive-harness` §4 and CLAUDE.md's MAP PREFLIGHT rule, recorded here so
every later phase starts from the same map. Read in this order: the invariants,
then the seam, then the subsystems.

**Read first, always**
| id | document | why it is on this list |
|---|---|---|
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | the five surfaces; the build's candidate contacts are 3, 4, 5 |
| `DR-INV-render-layout` | `docs/map/INV-render-layout.md` | the DIRECT PRECEDENT: a registered, versioned, argument-or-env-selected policy consumed by `render_conj_pack`, shipped 2026-08-28 with ZERO frozen-surface contact, and the document states exactly why |

**The seam, before either side**
| id | document | why |
|---|---|---|
| `DR-SEAM-llm-x-rules` | `docs/map/SEAM-llm-x-rules.md` | the brief and the form both live on this seam: `rules/` decides what to ask and what the answer means, `llm/` decides how it is asked |

**Subsystems and concepts**
| id | document | why |
|---|---|---|
| `DR-SUB-llm` | `docs/map/SUB-llm.md` | adapter, firewall, packs, wire contracts, repair, profiles |
| `DR-SUB-rules` | `docs/map/SUB-rules.md` | the epistemic moves the form's parse half feeds |
| `DR-CON-conjecture-source` | `docs/map/CON-conjecture-source.md` | `rules/conj.py::conj`, the one entry point; owns the sections built OUTSIDE the renderer |
| `DR-CON-packs-and-token-economy` | `docs/map/CON-packs-and-token-economy.md` | `PackIR`/`PackSection`, `allocate_pack`, `render_conj_pack`'s 20 section slots |
| `DR-CON-model-profiles` | `docs/map/CON-model-profiles.md` | the home-directory loading precedent for operator-authored artifacts (M4), and the natural place to name a model's preferred form (M3) |
| `DR-CON-seats` | `docs/map/CON-seats.md` | per-seat selection (M3, M5) |
| `DR-CON-conjecture-kinds` | `docs/map/CON-conjecture-kinds.md` | the R-g guardrail: kind/shape may never buy rank, admission or acceptance (M9) |
| `DR-CON-successor-questions` | `docs/map/CON-successor-questions.md` | the 2026-08-29 P9 precedent for a plugin-shaped, registered, versioned DESTINATION |
| `DR-INV-reference-menu` | `docs/map/INV-reference-menu.md` | the one authority for legal handle sets — bears on whether a free-text evidence plugin can keep citations citable |
| `DR-SUB-evidence` | `docs/map/SUB-evidence.md` | attached dossiers, admitted blocks, byte-checked citations |
| `DR-SUB-workflow` | `docs/map/SUB-workflow.md` | the pack-plan / exposure-receipt record family (M1) |
| `DR-SUB-manifest` | `docs/map/SUB-manifest.md` | **frozen** surfaces 4 and 5; the qualification subject |
| `DR-SUB-verification` | `docs/map/SUB-verification.md` | **frozen** surface 3 |

**Gaps found in the map (findings, not blockers).** `INDEX.md`'s seam matrix
lists `llm x model-profiles` and `model-profiles x scheduler` as *not yet
written*, and `CON-packs-and-token-economy` declares
`packs-and-token-economy x rules` undocumented. The form's per-model selection
(M3) and the sections built outside the renderer (`DR-CON-conjecture-source`)
sit on exactly those unwritten seams. Creating them is scoped in CHECKLIST.md,
not skipped.

---

## 5. Outstanding questions for the operator

Batched, per `dr-ask-the-right-question` §4. Each survives the dominance test
(the operator's recorded values do not settle it) AND changes real stakes.
Answers land here as amendments; none blocks FEASIBILITY.md.

- **Q1 — the road choice**, if the prices come out close. Carried to
  FEASIBILITY.md §"Roads" with a recommendation.
- **Q2 — may a free-text evidence plugin break citation?** R7 says the plugin
  is not typed; citation handles are the mechanism by which a conjecturer can
  point at admitted evidence bytes. If a plugin renders evidence its own way,
  the handles it prints must still resolve, or citation is lost for that
  configuration.
- **Q3 — may the form's PARSE half ever vary per model?** The monitor's reading
  (M3, M7) says NO. Asked because R10's "adjusted for an LLMs capabilities"
  could be read either way, and the two readings differ in what counts as
  evidence rather than in how content is generated.
- **Q4 — R17's leniency, how far.** "Adapting the accepted outputs so they
  compile" is operator-hedged. The monitor's reading (M7) admits normalisation
  that yields the SAME typed artifact and refuses anything that changes what is
  admitted. Confirmation wanted because this is the boundary the whole
  amendment turns on.
- **Q5 — the study.** Amendment 1 cites a study of why LLMs keep failing whose
  content was not supplied. Requested for quoting into §1a as operator-supplied
  evidence.

---

## 6. Out of scope (stated by the window instruction)

Implementing anything; the critic seat's design; deciding episodes (R13); the
transport, F4, F7 and hv tranches; anything on the model-profile experiment
branch except reading its measurements as evidence.

## 7. Frozen surfaces

None are edited in this phase. FEASIBILITY.md must NAME every contact the build
WOULD make — surfaces 3, 4 and 5 are the candidates — with
`tools/blast_radius.py`'s own computed result pasted, so the operator sees the
price before approving.
