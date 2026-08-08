# REPORT — Rung O1 grounded-overlay offline retrodiction

Every number below is recomputable by the pasted command immediately
above or below it, from `experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl`
(the driver's own machine-readable output, committed alongside this
report) or by re-running the named overlay script directly. MEASURE
ONLY — no file under `src/`, `tests/`, or `tools/` was touched to
produce any number here.

## Method

```
$ python3 experiments/2026-08-08-change-grounded-overlay-o1/scripts/run_all_overlays.py
[1/48] ... [48/48] ... done
SWEEP COMPLETE: 48 roots -> .../overlay_results.jsonl
real 4m6.408s
$ wc -l experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl
48 experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl
```

Corpus: every `experiments/**/log.jsonl` root (SPEC.md A7), 48 total.
11 roots raise `UnsupportedRunManifestVersionError` on open (schema
versions 1-3, pre-v6) — the SAME 11-root baseline
`docs/map/INV-frozen-surfaces.md` documents for `tools/root_sweep.py`'s
own corpus, confirming this tranche's corpus enumeration against the
existing instrument rather than inventing a new one. 37 roots opened
and were measured by all four overlays.

## Per-root summary table (all 48 roots)

Columns: `nodes`/`att` = O1a's artifact/attack-edge counts (pasted
BEFORE preferred-extension computation, per the guardrail);
`ctrl_sccs` = O1a controversy SCCs; `skeptical` = artifacts
skeptically-accepted-under-preferred-but-blocked-from-grounded;
`fb` = O1b accepted+formally-backed count; `comparable`/`excluded` =
O1b pair counts; `accepted`/`floating`/`chains` = O1c accepted count,
floating-component count, and the subset that are multi-node chains
(not vacuous singletons); `warrants`/`flips` = O1d warrant count and
single-warrant-flip count.

```
$ python3 -c "
import json
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row = json.loads(line)
    root = row['root']
    o1a, o1b, o1c, o1d = row['o1a'], row['o1b'], row['o1c'], row['o1d']
    if '_error' in o1a:
        print(f'{root} | ERROR {o1a[\"_error\"]}'); continue
    print(
        f'{root} | nodes={o1a[\"node_count\"]} att={o1a[\"att_edge_count\"]} ctrl_sccs={len(o1a[\"controversy_sccs\"])} skeptical={len(o1a[\"skeptical_accepted_not_grounded\"])}'
        f' | fb={o1b[\"accepted_formally_backed_count\"]} comparable={o1b[\"comparable_pair_count\"]} excluded={o1b[\"excluded_pair_count\"]}'
        f' | accepted={o1c[\"accepted_count\"]} floating={len(o1c[\"floating_components\"])} chains={sum(1 for f in o1c[\"floating_components\"] if f[\"kind\"]==\"chain\")}'
        f' | warrants={o1d[\"warrant_count\"]} flips={sum(v for k,v in o1d[\"flip_histogram\"].items() if k!=\"0\")}'
    )
"
experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752 | nodes=42 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=42 floating=70 chains=0 | warrants=0 flips=0
experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc | nodes=117 att=1 ctrl_sccs=0 skeptical=0 | fb=16 comparable=0 excluded=120 | accepted=116 floating=171 chains=1 | warrants=1 flips=0
experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829 | nodes=100 att=0 ctrl_sccs=0 skeptical=0 | fb=23 comparable=0 excluded=253 | accepted=100 floating=137 chains=1 | warrants=0 flips=0
experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c | nodes=71 att=0 ctrl_sccs=0 skeptical=0 | fb=6 comparable=0 excluded=15 | accepted=71 floating=113 chains=1 | warrants=0 flips=0
experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c | nodes=38 att=0 ctrl_sccs=0 skeptical=0 | fb=12 comparable=0 excluded=66 | accepted=38 floating=32 chains=0 | warrants=0 flips=0
experiments/2026-08-05-testphase-live-validation/home-testphase/runs/run-a518e33a75507207633f864ba6a864b1 | nodes=45 att=0 ctrl_sccs=0 skeptical=0 | fb=5 comparable=0 excluded=10 | accepted=45 floating=63 chains=1 | warrants=0 flips=0
experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949 | nodes=95 att=0 ctrl_sccs=0 skeptical=0 | fb=5 comparable=0 excluded=10 | accepted=95 floating=163 chains=1 | warrants=0 flips=0
experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd | nodes=177 att=0 ctrl_sccs=0 skeptical=0 | fb=28 comparable=0 excluded=378 | accepted=177 floating=272 chains=2 | warrants=0 flips=0
experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484 | nodes=102 att=0 ctrl_sccs=0 skeptical=0 | fb=28 comparable=0 excluded=378 | accepted=102 floating=122 chains=2 | warrants=0 flips=0
experiments/bronze_feedback_v1_superseded_2026-07-14/observe_only | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_feedback_v1_superseded_2026-07-14/trial_required | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_flat_2026-07-13/deepseek-v4-pro | nodes=34 att=11 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=23 floating=22 chains=0 | warrants=11 flips=0
experiments/bronze_flat_2026-07-13/kimi-k2_6 | nodes=15 att=4 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=11 floating=8 chains=0 | warrants=4 flips=0
experiments/bronze_flat_2026-07-13/qwen3_5_397b | nodes=25 att=8 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=17 floating=16 chains=0 | warrants=8 flips=0
experiments/bronze_pilot_2026-07-14 | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_repertoire_v2_2026-07-14/deepseek-v4-pro | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_repertoire_v2_2026-07-14/gpt-oss_120b | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_repertoire_v2_2026-07-14/kimi-k2_6 | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/bronze_repertoire_v2_2026-07-14/qwen3_5_397b | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/gemma4_dna_unattended_2026-07-12 | ERROR UnsupportedRunManifestVersionError: schema version 1 unsupported
experiments/gemma4_dna_unattended_3_2026-07-12 | ERROR UnsupportedRunManifestVersionError: schema version 1 unsupported
experiments/glm_judge_2026-07-14 | ERROR UnsupportedRunManifestVersionError: schema version 2 unsupported
experiments/jolt_architecture_2026-07-16/run | ERROR UnsupportedRunManifestVersionError: schema version 3 unsupported
experiments/live_coin_canonicity_2026-07-31/home/runs/run-c5f901f38208e862f4ce2fe60a26e551 | nodes=29 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=29 floating=38 chains=0 | warrants=0 flips=0
experiments/live_compare_2026-07-28/deepseek/shallow-runs/shallow-dc6fe3f9c26cede686906a16 | nodes=28 att=1 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=27 floating=26 chains=0 | warrants=1 flips=0
experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf | nodes=69 att=1 ctrl_sccs=0 skeptical=0 | fb=5 comparable=0 excluded=10 | accepted=68 floating=109 chains=1 | warrants=1 flips=0
experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332 | nodes=70 att=0 ctrl_sccs=0 skeptical=0 | fb=12 comparable=0 excluded=66 | accepted=70 floating=79 chains=1 | warrants=0 flips=0
experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch2-run-9e9812feefa792179d490db7734825b5 | nodes=46 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=46 floating=64 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/openchallenge/runs/completed-epoch3-run-9e9812feefa792179d490db7734825b5 | nodes=22 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=22 floating=24 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/openchallenge/runs/failed-epoch1-run-0d1f88e18779b7eb6d8c5d6af3473ba7 | nodes=22 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=22 floating=24 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/openchallenge/runs/run-27b80f26bd398c718360e97e2a403593 | nodes=42 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=42 floating=60 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/openchallenge/runs/run-9e9812feefa792179d490db7734825b5 | nodes=22 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=22 floating=24 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/referee/runs/run-d17935a4bf5ffa67c7f6e67b9a637a00 | nodes=47 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=47 floating=74 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/referee/runs/run-e542c3c1fc266943e0260c5aa8d7c107 | nodes=20 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=20 floating=28 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/referee/runs/run-e6c07aec698426a9b21d01399ba6b5b0 | nodes=32 att=0 ctrl_sccs=0 skeptical=0 | fb=6 comparable=0 excluded=15 | accepted=32 floating=35 chains=1 | warrants=0 flips=0
experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a | nodes=79 att=0 ctrl_sccs=0 skeptical=0 | fb=48 comparable=0 excluded=1128 | accepted=79 floating=24 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a | nodes=59 att=0 ctrl_sccs=0 skeptical=0 | fb=23 comparable=0 excluded=253 | accepted=59 floating=32 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a | nodes=53 att=0 ctrl_sccs=0 skeptical=0 | fb=24 comparable=0 excluded=276 | accepted=53 floating=12 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a | nodes=34 att=0 ctrl_sccs=0 skeptical=0 | fb=12 comparable=0 excluded=66 | accepted=34 floating=6 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a | nodes=43 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=43 floating=48 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100 | nodes=30 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=30 floating=48 chains=0 | warrants=0 flips=0
experiments/live_research_2026-07-29/wide/runs/run-5a771259557378224bd68591483817be | nodes=20 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=20 floating=16 chains=0 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-15a53aca8a6fc66a39f382fc688c5346 | nodes=73 att=0 ctrl_sccs=0 skeptical=0 | fb=6 comparable=0 excluded=15 | accepted=73 floating=117 chains=1 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847 | nodes=39 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=39 floating=35 chains=0 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-9ae94bb478990cbecca373fc3bcb1345 | nodes=27 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=27 floating=23 chains=0 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-ac1836b6237b6e9d80b3b0cb492b39f5 | nodes=96 att=0 ctrl_sccs=0 skeptical=0 | fb=6 comparable=0 excluded=15 | accepted=96 floating=163 chains=1 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03 | nodes=37 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=37 floating=33 chains=0 | warrants=0 flips=0
experiments/live_tri_2026-07-27/run-faa5feae126bc2558ea9c6d8d200a90c | nodes=47 att=0 ctrl_sccs=0 skeptical=0 | fb=0 comparable=0 excluded=0 | accepted=47 floating=43 chains=0 | warrants=0 flips=0
```

## O1a — grounded-vs-preferred semantics diff + SCC controversy inventory

### M1 — zero attack-graph controversy across the whole corpus

```
$ python3 -c "
import json
total_controversy=total_undecided=total_skeptical=total_too_large=0
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1a=row['o1a']
    if '_error' in o1a: continue
    total_controversy+=len(o1a['controversy_sccs']); total_undecided+=o1a['undecided_count']
    total_skeptical+=len(o1a['skeptical_accepted_not_grounded'])
    total_too_large+=sum(1 for c in o1a['components'] if c['status']=='TOO_LARGE')
print(total_controversy, total_undecided, total_skeptical, total_too_large)
"
0 0 0 0
```
Across all 37 openable roots, zero attack-graph SCCs contain an
undecided (`label0=="suspended"`) artifact, zero artifacts are
`label0`-suspended at all, zero artifacts are skeptically-accepted-
under-preferred-but-blocked-from-grounded, and zero components hit the
16-node `TOO_LARGE` cap. **Grounded and preferred coincide on every
committed root in this corpus.** This is a genuine negative result,
not a script defect: `att` itself is small (26 edges total across 37
roots — M2 below) and every edge observed forms a simple attacker->
target chain with no cycle, so `label0` never produces `"suspended"`
for anything. O1a's TOO_LARGE guardrail (`scripts/check_o1a_
too_large_guardrail.py`) was independently verified to fire correctly
on a synthetic 20-node odd cycle (CHECKLIST.md step 4) — it was never
exercised on real data because no root's undecided component was ever
non-empty.

### M2 — total attack-edge volume, corpus-wide

```
$ python3 -c "
import json
n=a=0
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1a=row['o1a']
    if '_error' in o1a: continue
    n+=o1a['node_count']; a+=o1a['att_edge_count']
print('artifacts:',n,'att edges:',a)
"
artifacts: 1947 att edges: 26
```

## O1b — joint-execution unsatisfiability probe

### M3 — the machine-comparable-gate restriction excludes the entire corpus

```
$ python3 -c "
import json
from collections import Counter
reasons=Counter(); total_fb=total_comp=0
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1b=row['o1b']
    if '_error' in o1b: continue
    total_fb+=o1b['accepted_formally_backed_count']; total_comp+=o1b['comparable_pair_count']
    for e in o1b['excluded_reasons']: reasons[e['reason']]+=1
print('formally_backed:',total_fb,'comparable_pairs:',total_comp,'excluded:',dict(reasons))
"
formally_backed: 265 comparable_pairs: 0 excluded: {'not both exec-oracle-class': 2772, 'no shared problem': 302}
```
265 accepted+formally-backed artifact instances exist across the
corpus (summed per-root), and **zero** pairs meet O1b's own
machine-comparable-input-gate restriction (SPEC.md A4: same problem AND
both carry an exec-oracle-class commitment with an identical entry
name). 2772 of the 3074 excluded pairs fail because they are not both
`program:exec_oracle` — spot-checked on the corpus's single largest
formally-backed root below (M4) — meaning this program's accepted
formally-backed artifacts overwhelmingly carry `predicate:` or
`program:property_oracle` commitments instead, which declare no
machine-legible input domain in the ontology today (SPEC.md Q4's own
finding). The dynamic-fuzz half of the probe (`oracle.run` reuse,
SENTINEL trick) was therefore **never exercised on real data** — it is
verified correct only by the hand-built unit-level checks run during
CHECKLIST.md step 6, not by this sweep. Named as residue below.

### M4 — spot-check: the largest formally-backed root, reason breakdown

```
$ python3 -c "
import sys; sys.path.insert(0,'experiments/2026-08-08-change-grounded-overlay-o1/scripts')
import pathlib, o1b_joint_execution_probe as m
from collections import Counter
root = pathlib.Path('experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a')
r = m.analyze_root(root)
print(r['accepted_formally_backed_count'], r['comparable_pair_count'],
      Counter(e['reason'] for e in r['excluded_reasons']))
"
48 0 Counter({'not both exec-oracle-class': 1128})
```
All C(48,2)=1128 pairs on this root (48 accepted formally-backed
artifacts) are excluded for the identical reason: none of them carry
a `program:exec_oracle` commitment.

## O1c — floating-foundation clusters on the dependence graph

### M5 — isolated vacuous singletons vs genuine multi-node floating chains

```
$ python3 -c "
import json
isolated=chain=0; roots_with_chains=set(); sizes=[]
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1c=row['o1c']
    if '_error' in o1c: continue
    for f in o1c['floating_components']:
        if f['kind']=='isolated': isolated+=1
        else:
            chain+=1; roots_with_chains.add(row['root']); sizes.append(f['size'])
print('isolated:',isolated,'chains:',chain,'roots_with_chains:',len(roots_with_chains))
print('chain sizes, descending:',sorted(sizes,reverse=True))
"
isolated: 2360 chains: 14 roots_with_chains: 12
chain sizes, descending: [28, 28, 28, 21, 21, 11, 11, 11, 11, 10, 10, 10, 10, 10]
```
2360 accepted artifacts are isolated (zero `dep` edges either way) —
the vacuous case: trivially "supported" by `final_labels`'s own
`all([])==True`, without ever citing evidence or admission. This is
expected and low-signal on its own (many claims are legitimately
standalone). The genuinely interesting catch is the **14 multi-node
floating chains across 12 roots**, up to 28 artifacts each — connected
clusters of accepted artifacts that DO cite each other via `dependence`
refs, but whose WHOLE transitive closure never reaches a `SEED`/
`IMPORT`/`USER` artifact. These are exactly the "self-supporting
clusters" O1c's own preplan text names.

### M6 — the two largest floating chains, spot-checkable by root and member ids

```
$ python3 -c "
import json
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1c=row['o1c']
    if '_error' in o1c: continue
    for f in o1c['floating_components']:
        if f['kind']=='chain' and f['size']>=21:
            print(row['root'], f['size'], f['members'][:3])
"
experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc 21 ['024cbd0e...', '02a7b170...', '045d8829...']
experiments/2026-08-02-stress-triplet/home-workshop/runs/run-1a0d4168a446f052bc7ccc9aa20b9829 28 ['08fedf4d...', '12917e9c...', '14b9a83d...']
experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-6995cd12124d2697030bb4b9e48f79bd 28 ['042f7635...', '10e34f6f...', '1217377a...']
experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/run-79900e7847544b09bfb266518e2d8484 28 ['084384ac...', '0e251135...', '0f946f0f...']
experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332 21 ['0eb9c94c...', '14e084ed...', '15769cf4...']
```
Full member id lists are in `overlay_results.jsonl`'s own `o1c.
floating_components` rows for these five roots — every id is spot-
checkable with `Harness(root, read_only=True).state.artifacts[<id>]`.

## O1d — load-bearing-warrant sensitivity distributions

### M7 — zero single-warrant flips across the whole corpus

```
$ python3 -c "
import json
accepted=warrants=0; histo={}
for line in open('experiments/2026-08-08-change-grounded-overlay-o1/overlay_results.jsonl'):
    row=json.loads(line); o1d=row['o1d']
    if '_error' in o1d: continue
    accepted+=o1d['accepted_count']; warrants+=o1d['warrant_count']
    for k,v in o1d['flip_histogram'].items(): histo[k]=histo.get(k,0)+v
print('accepted:',accepted,'warrants:',warrants,'histogram:',histo)
"
accepted: 1921 warrants: 26 histogram: {'0': 1921}
```
Every one of the 1921 accepted artifacts across the corpus has ZERO
single-warrant flips — removing any one of the corpus's 26 warrants
never changes any accepted artifact's status. This matches M2's own
`att`=26 finding (one attack edge per warrant, no closure fan-out
observed in this corpus) and is consistent with each attack's target
having no OTHER path to acceptance depending on that specific edge's
absence — i.e., in every observed case, an artifact is either
unattacked (acceptance independent of any single warrant) or its one
attacker's removal doesn't change the graph's fixpoint (the attacked
artifact was already refuted for a reason that removing one warrant
doesn't undo, or the attack wasn't decisive alone). No accepted
artifact in this corpus rests its acceptance on exactly one edge.

## TOO_LARGE guardrail (independent of real-data results)

```
$ python3 experiments/2026-08-08-change-grounded-overlay-o1/scripts/check_o1a_too_large_guardrail.py
TOO_LARGE reported for component size 20 in 0.0002s
```
