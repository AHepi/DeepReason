# Stress-Test Campaign Plan

*Registered 2026-07-04, before any campaign run. Budget: total raised to
8M tokens; ~4.4M available. Each run is hard-capped by the TokenMeter;
caps below sum to ~2.75M, leaving a reserve. Baselines come from already
logged runs where a matched one exists (no re-spend). Expectations are
stated before results; a surprising failure is a finding, not a bug to
hide.*

| # | Test | Command sketch | Cap | What it stresses | Pre-stated expectation |
|---|---|---|---|---|---|
| T1 | Flash-everything downgrade audit | `--model deepseek-v4-flash --suite republic --cycles 10` | 250k | Angle-2 downgrade-then-audit: whole system on the cheap model (judge seat 2 stays pro — cross-model) | Valid-JSON stays >0.9; attack validity >0.9; trial-guard blocks still occur. Falsified if flash criticism stops felling bad candidates (refutations/cycle drops >50% vs batch_decay_probe baseline) |
| T2 | Reasoning dose-response | tides, `--reasoning none\|1000\|default`, 5 cycles each | 300k | The angle-1 dial measured on quality, not just cost | Survivor count and coverage flat across arms (D2); tokens/call monotone in the dial. Falsified if `none` arm loses >30% survivors |
| T3 | Endurance + max diversity | tides+republic seeded in ONE root, 30 cycles, 8 schools, `--stance-decay 60`, spec injection | 800k | Long-horizon dynamics: problem rotation, integration share, discrimination, audits (3 firings), school novelty at N=8 | No capture-flag hysteresis lock; criticism debt stays <ceiling; frontier grows sublinearly (criticism keeps up). Watch for reseeds — first live sighting |
| T4 | Adversarial domain (occult suite) | `--suite occult --cycles 8` | 250k | Epistemically hostile terrain: a question inviting unfalsifiable answers | The system passes by refusing: small/empty frontier, rubric refutations dominate, any survivor states real checkable forbidden cases (debunking-shaped mechanisms like self-fulfilling belief, birth-season effects). Falsified if vague "cosmic energy" claims survive kappa-causal |
| T5 | Judge integrity under audit pressure | republic, `--set AUDIT_PERIOD=3 --set TRIAL_PARAPHRASE_N=3`, 9 cycles | 300k | Trial guard + paraphrase-invariance audits at 3x frequency, first live planted-flaw data | Ensemble-split and paraphrase-flip blocks rise (more screens = more catches); no valid conviction lost (survival_rate not driven to 0) |
| T6 | Merge / distributed operation | two independent 6-cycle republic runs, then `deepreason merge` + replay check | 400k | P3 G-Set union live: two graphs on the same problem merged; adjudication and gate after merge | Merge is lossless (artifact union), no status corruption (replay byte-for-byte post-merge), cross-graph near-dups get gated on next cycles |
| T7 | Relapse pressure / resume | +4 cycles on the finished runs/cache_staged root | 150k | Anti-relapse gate precision on a mature root: does it block resubmissions without blocking novel work | Gate diagnostics show hash/semantic blocks >0; admitted-but-novel still >0. Falsified if the gate starves admission entirely (false-positive lockout) |
| T8 | Cachebench refresh | free (no API) after all runs | 0 | Whether the campaign's added volume changes the cache verdicts | Exact hit rate stays <20% (packs keep being unique); if it flips, the refuted designs' reinstatement machinery gets its first live test via a counter-warrant |

Analysis deliverable: one insights report comparing all arms on the
standing instrument set (per-role valid-JSON/tokens, attack validity,
refutations/cycle, trial-guard blocks, capture flags, school novelty,
spec transmission, survivor HV/coverage) + qualitative frontier reads.
