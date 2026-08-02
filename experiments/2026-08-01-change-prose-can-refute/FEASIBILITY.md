# Feasibility: criticism from a proposal's own point of view

Requested under R7-R12 of `REQUEST.md`. R10 gated all design behind this
survey; R11/C7 required it in plain language, so this file deliberately carries
no code names or coined terms.

Eleven agents: six independent surveyors of what exists, one assessment, three
adversarial skeptics, one writer. **All three skeptics refuted the assessment**,
and the report below follows the skeptics rather than the assessment wherever
they disagreed. Verdict carried forward: feasible with additions.

---

**Can this be built on what is already there?**

Yes — as an addition, not an unlock. Nothing has to be torn out and nothing has to be permitted at the moment the model is asked; but the parts that would actually carry the experiment (something to choose an author-side critic, somewhere in the record to hold the obligation, and any way at all to measure the result) do not exist and would have to be made.

---

**What already exists that it could stand on**

Every proposal the system registers carries a label saying which point of view produced it. In the thirty-one recorded runs that can still be opened, that label is present on every single proposing piece of work — no gaps.

There is a complete, live machinery for criticism across points of view: a plan of who must examine what, a record of each attempt, a record of what is still owed, and a note in the record for each completed exposure. Thousands of these records exist across twenty-seven runs. Critics are already routed by point of view, and the criticism the model produces is already stamped with the critic's own point of view — so a same-side criticism would be recognisable in the record without inventing a single new label.

The system also already sends the critic a one-line statement of its own stance. And, crucially, the system already looks up the author's point of view at the moment it decides who should criticise — that lookup is exactly how it excludes the author today.

One channel already produces a real defeat under today's settings: where a proposal states a claim that can be checked mechanically, a failed check mints a genuine defeat with no permission gate at all. That has happened inside a run using the points-of-view machinery and drove a proposal owned by one point of view to "defeated".

Finally, and this belongs under "what exists" because it is written down: the design documents state a deliberate intent that criticism should cross these lines freely, and that the separate points of view are meant to be islands only on the proposing side. The current exclusion is therefore designed, not incidental.

---

**What does not exist and would have to be made**

- Anything that would choose the author's own point of view as critic. The only chooser subtracts the author by construction.
- Any place in the record that can hold such an obligation. The existing one refuses outright to be written with author and critic the same, and there is no alternative.
- Any second way of noting an exposure. The one that exists makes a finished run's record fail its soundness check if author and critic match.
- Any switch to turn it on. The settings block has a fixed, closed list of options with nothing resembling this.
- Any way to measure the result. There is no comparison anywhere between same-side and cross-side criticism; the project's own experiment plan lists that comparison as a known gap.
- Any baseline to compare against. Not one same-side criticism exists anywhere, by three independent counts — and, just as importantly, no proposal has ever been examined by more than one point of view either, so the "cross-side" arm has never been instantiated on a shared piece of work either.

---

**The operator's premise**

Half true, and the false half changes the shape of the problem.

True where it matters to the model: the text sent to a critic never says who wrote the thing being criticised. Targets arrive under blank stand-in names. Across every recorded criticism prompt, not one carries an author label supplied by the system.

False about the system as a whole: the harness knows the author before it makes the call, and reads that label precisely in order to exclude the author. What is missing is a way of *showing* it and a decision to *use* it — not the information.

This correction matters practically. Four of the six earlier surveys reported same-side criticism as forbidden at the point where the model is asked. It is not. Nothing at that boundary sees the author at all. Only three places block it: the chooser, the obligation record's own rules, and the end-of-run soundness check on the exposure note.

One caveat that nobody has tested: a model might still guess the author's side from the flavour of the writing. That was never measured.

---

**Risks, worst first**

**1. The system's own study says this cannot be fixed by narrowing what is shared.** The operator's own worry — a point of view criticising its own work is close to marking its own homework — is real, and the obvious reassurance fails on this repository's own evidence. Earlier this session it was argued that the risk is small because a critic sees none of its own side's prior work. But this repository contains a study whose predictions and thresholds were fixed before any of it ran, and one arm removed that shared prior work entirely. The drift toward sameness persisted at the same level. Its recorded conclusion is that the pull is inside the model, not in the text it is sent. Removing shared context therefore buys no independence. The same study also found that making the stance line permanent made the points of view *less* distinct, not more.

**2. Criticism across points of view is already criticism by the same model, so the comparison is confounded before it starts.** Every recorded run used one model reached one way, with all points of view bound to the same seat. The entire measured difference between today's "different" critic and a same-side critic is one line of stance text. Whatever independence the current rule looks like it is protecting has never actually been present in a run — and nothing in the system can currently tell the two conditions apart.

**3. Reusing the existing record machinery would break a live run, badly and silently.** If a same-side exposure is noted using either existing mechanism, the next round of criticism in that same run reconstructs who has already examined what — without checking authorship — and then tries to build an obligation record that refuses author-equals-critic. The run would fail with an unhandled error before it even contacted the model, leaving no proper explanation of why it stopped. This is conditional on reusing the existing notes, which is exactly what the existing machinery invites.

**4. It touches the check that pronounces a finished run's record sound — a part of the system marked as not to be changed without approval.** A same-side exposure written the existing way makes the record fail that check. That failure channel is already loaded: ten finished runs carry forty-four failures of exactly this kind and already read as unsound, so new failures would be hard to distinguish from existing debt. Two verification layers already disagree about whether those existing failures are fatal or merely unfinished business.

**5. On the prose side, the experiment can only produce commentary.** The system forces commentary-only for all text work regardless of settings, and every recorded run ran that way. Twenty-six openable runs ran criticism and produced no defeats at all. Criticism is not even linked to what it criticised except by a note. Prose is, by this project's own standard, not evidence.

**6. But one channel is not commentary-only, and it is blind to who did the work.** The mechanical checking path fires on every proposal, has no permission gate, and has produced a real defeat inside a run using the points-of-view machinery. It does not record which point of view performed it. So an experimental path cannot be assumed purely observational — and if it does defeat something, the record will not show that the blow came from the author's own side. (This was misidentified earlier in the session; the correction widens the reachable channel rather than narrowing it.)

**7. Showing the model who wrote the thing would make the author label an input to deciding what stands** — which the design documents say is impossible *by construction*, and it is only impossible because the label is never shown. Nothing in the end-of-run check would catch it, because that check compares a fingerprint of the whole text sent and never re-reads it. Combined with risk 6, a shown author label becomes an input to a process that can change a proposal's standing.

**8. "Same point of view" is a weaker idea than it sounds.** The label is not part of what makes a piece of work identical, so identical text from two points of view collapses into one, credited to whoever wrote it first. The label has no format rules, and one recorded run used freehand names. A point of view whose own defining record has been defeated still counts as live.

**9. The existing obligation stays fully in force.** This is additional work, not a substitute, and there is no per-round cap at all on the criticism pass when the points-of-view machinery is in use — the cap belongs to the older path. When the spending limit runs out mid-round, the remaining batches are still attempted and each writes more failure records. Against that, the obligation per proposal is one-off, so the steady-state cost is bounded.

**10. The evidence base is partial and uneven.** Fourteen of forty-five recorded runs cannot be opened at all; every count above is over the thirty-one that can. Most recorded defeats sit in runs from an earlier era with none of the points-of-view machinery. There is exactly one run where a real defeat and the points-of-view machinery appear together, and that single run is the entire basis for saying the mechanical channel works under this machinery.

---

**What remains genuinely unknown**

- Which of two quite different things is intended: showing the model who wrote the thing, or merely dispatching an author-side critic without telling it. The second needs no change to what the model sees and carries much less risk. No survey settled this.
- Whether same-side criticism should count toward, be excluded from, or sit entirely beside the standing requirement that each accepted proposal be examined by another point of view. This decides whether the frozen soundness check is touched at all.
- Whether commentary-only output is an acceptable experimental result.
- Whether the mechanical defeat channel is in or out of scope. It is the one place this could change a proposal's standing today, and it is blind to authorship by design — which may be the right answer or a violation, depending on the operator's reading.
- Whether the forty-four existing failures are a parked defect or accepted behaviour. Until that is settled, new results in that channel are not legible.
- Whether the operator wants the points of view to be genuinely different models first. They are all one model today; a mode for binding them to separate routes exists, has never run, and covers only the proposing side.
- What the experiment would be compared against, given no baseline exists in either direction.
- Whether hardening the design documents' "preferentially different" into an absolute exclusion was a recorded decision. No survey found the reasoning written down anywhere.
- Whether a critic can infer the author's side from the writing itself. Never tested, and it bears directly on whether the current rule protects anything in practice.
- Whether the written design intent that criticism should deliberately cross these lines is a constraint the operator accepts, or one this experiment is meant to revisit.
