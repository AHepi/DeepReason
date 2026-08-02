# Triage run: surviving answer (run-0a3e93d6, 58 accepted survivors)

Top eight surviving conjectures, newest first. Survivors of live
cross-school criticism from four schools; accepted does not mean true.

## d645297b783567c7 (seq 1156)

The priority-6 observability gap in verify_root_report reduces to a classification logic defect: verify_root_report routes three pre-v6 roots to a verdict path instead of an error path, causing the sweep instrument to report 11 ERROR-level results while the direct-load census reports 14 raising manifests. The discrepancy is refuted if the pre-v6 roots surface as verdicts rather than errors by design, as a documented and intentional classification would mean the 3-root census delta is expected behavior rather than an observability bug.

## cd5450d3485f24a4 (seq 1156)

024cbd0e1e4f contradicts the direct-load census: verify_root_report abstracts pre-v6 roots to the verdict path, meaning the 3-root delta is a true classification discrepancy (instrument sees failures the other does not). Refuted if pre-v6 roots surfacing as verdicts rather than errors is a documented, intentional behavior, OR if verify_root_report is an internal diagnostic not relied upon for correctness decisions.

## bbd39c1d52656ef1 (seq 1156)

The verify_root_report classification discrepancy integrates with the isolated observability gap: it shares mechanism with resolve_conjecture_route in that both classify system states into error vs verdict paths, and the pre-v6 root routing is refuted if the sweep instrument and direct-load census use identical ERROR definitions, which would eliminate the 3-root delta and collapse the discrepancy to a measurement artifact.

## ae5fa20a34c329f3 (seq 1156)

024cbd0e1e4f abstracts SRC_001 and SRC_002 by representing their census-instrument disagreement as a generalizable observability gap. Specifically, the Priority 6 directive abstracts the concrete '11 ERROR vs 14 raising manifests' counting discrepancy into a universalized test: asserting that verify_root_report produces consistent error vs verdict classification for pre-v6 roots. This abstraction is refuted if the pre-v6 roots' routing to the verdict path is isolated purely to the direct-load instrument's tallying logic, rather than being a generalizable classification divergence in verify_root_report itself that can be tested independently of the census sweep.

## 529d43d91bf48bf0 (seq 1156)

The priority-6 observability gap integrates with the priority-3 import-availability test: the unexplained classification delta in verify_root_report depends on the continued importability and callability of the routing and criticism-assignment surfaces (resolve_conjecture_route and compile_criticism_assignments), because if those routing entry points silently rot, the verdict-vs-error path that surfaces pre-v6 roots becomes unreachable, masking the 3-root census delta entirely. This relation is REFUTED IF the verify_root_report classification path for pre-v6 roots is functionally independent of resolve_conjecture_route and compile_criticism_assignments (e.g., the report is produced by a direct, hard-coded branch that does not flow through those functions).

## 3cef78c38252df29 (seq 1156)

The foundation artifact 024cbd0e1e4f depends on verify_root_report routing pre-v6 roots through a verdict path rather than an error path. It is refuted if the 3-root census delta (11 ERROR vs 14 raising manifests) is a measurement artifact with no behavioral consequence, because that would mean the observed classification discrepancy in verify_root_report has no functional or observational significance.

## d91a203752f1cb65 (seq 994)

DEPENDS ON: SRC_004 depends on SRC_005 because the test design (assert ERROR vs verdict classification for three pre-v6 roots) presupposes the prior investigation SRC_005 mandates (determine whether the delta is by design or by bug). The test is vacuous — it asserts an unknown expectation — without the design determination SRC_005 requires. This is a sequential dependence: investigation gates the test. Refuted if the test can be written with a parameterised expectation (assert ERROR OR assert verdict, document which) that does not require prior design knowledge — in that case the test is self-contained and does not depend on the investigation.

## 320c39ab6c25fd52 (seq 994)

SHARED MECHANISM: the census-delta gap (SRC_004/SRC_005) and the recovery-guard gap (SRC_001) share a failure mechanism — a guard that silently converts an error-class event into a non-error-class event (verify_root_report converts ERROR to verdict; the recovery guard converts a context-receipt error into a silent proceed). Both are silent-classification-drift defects where the system presents a degraded condition as normal. Refuted if the recovery guard does not perform classification but instead performs state transition or fallback — i.e., if its mechanism is recovery execution, not error reclassification.
