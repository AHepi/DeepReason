---
name: review-response
description: The find -> verify -> refute-or-accept-in-writing -> act loop for every external review received (FR-21, FR-25), and the author defect ledger that reviews are required to cite. This loop replaced the unattended driver; see MODULES.md.
---

# Review Response (new in 0.5; the loop that replaced M2)

<!-- PROMPT-CORE-BEGIN -->
A review is evidence, not a verdict. Every review received gets a
written disposition; every finding in it gets exactly one of two fates.

1. VERIFY FIRST: re-establish each finding against the sources or by
   running code (FR-25) before acting. A reviewer without execution
   access returning MISSING on an execution-dependent claim is correct
   behavior - the verification is yours to run, not theirs to guess.
2. REFUTE OR ACCEPT, in writing, per finding:
   - refuted: state the evidence, in the disposition, with a test
     pinning the refutation where possible. A refuted finding is as
     valuable as an accepted one - record it, never silently drop it;
   - accepted: name the action taken in the same disposition. An
     accepted finding without an action is not yet accepted.
   A reviewer's REASONING can be wrong while its WARNING is right;
   dispose of the two separately.
3. THE DISPOSITION is one document per review: verdict table, narrow
   green (what the reviewer's packet did and did not contain), and the
   per-finding fates. It cross-links from the artifact reviewed.
4. AUTHOR DEFECT LEDGER: maintain a running list of the author's own
   verified failure modes (one line each: defect, instance, direction).
   Feed it to adversarial reviewers - naming the author's documented
   bias measurably sharpens attack. Two integrity rules: entries only
   for VERIFIED defects, and errors in BOTH directions recorded - a
   ledger that only shows one direction is itself the tidy story it
   warns against.
5. ESCALATION DISCIPLINE (FR-21): a review that shows you closed a
   question that was the owner's to decide is accepted by REOPENING the
   question - restating options, moving your view to a marked
   view - never by defending the closure. Having been corrected for
   closing is not a license to feign neutrality: state views as views.
6. The loop ends when every finding has a fate and every action is
   done or filed. Then, and only then, the next review round.
<!-- PROMPT-CORE-END -->
