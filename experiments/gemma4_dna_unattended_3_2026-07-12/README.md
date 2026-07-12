# Gemma 4 DNA website — unattended run 3

Date: 2026-07-12

This directory is the complete replayable run root for the third unattended DNA website attempt. It used the full DeepReason engine with the compact model-facing profile. It contains the frozen run manifest, append-only event log, every stored prompt and raw response blob, canonical objects, checkpoint, and typed terminal diagnostic.

## Frozen execution

- Model: `gemma4:31b`
- Provider endpoint: Ollama Cloud
- Engine profile: `full`
- Model, pack, and output profile: `compact`
- Concurrency: `1`
- Total token ceiling: unlimited (`--token-budget 0`)
- Direct calls: `0`
- Compact calls: `30`
- Total recorded tokens: `58,082`
- Unauthorized or alternate-model calls: `0`

All 30 model calls produced schema-valid output on their first attempt. The run recorded zero repair attempts, zero schema-exhaustion failures, zero dropped transports, and zero manifest well-formedness failures.

## Outcome

The workflow stopped at `COMPONENT_BUILD` with:

```json
{
  "code": "NO_COMPONENT_SURVIVOR",
  "component": "c2",
  "path": "/components/c2"
}
```

No invalid or partial website was assembled or exported.

## What succeeded before the stop

Gemma completed the planning cycle, compact design outline, art direction, and all six component contracts. The deterministic compiler produced canonical manifest `ff87020d28a19d1d05ee1d8c6d8a108daff9b6bccba08d4b1f6ef3ea83951418`, and the manifest passed validation. Component C1 then produced a surviving implementation.

## Failure analysis

C2 was the interactive nucleotide sequence builder. Its contract required base-pairing logic, interactive selection, correct/incorrect feedback, sequence display, lifecycle exports, and reduced-motion-safe behavior.

One C2 implementation was admitted as artifact `17871f87efb30c4b4e8cc3eebff18bc23aad9bb44198de15ff7e0503d03049f9`. Its transport output was valid, and its ordinary component interface was accepted. However, the canonical artifact declared the required commitment `lineage-ref@2756970c52af` while its interface contained `"refs": []`. The deterministic lineage check therefore produced the failing demonstrative warrant:

`w:lineage-ref@2756970c52af:17871f87efb30c4b4e8cc3eebff18bc23aad9bb44198de15ff7e0503d03049f9`

That refutation removed the only admitted C2 candidate from survivor status. Later C2 responses remained schema-valid, but the battery-equivalence anti-relapse gate rejected them as equivalent to previously refuted artifacts. Those comparisons included the refuted C2 implementation, a refuted C1 implementation, and a refuted planning artifact. With no surviving C2 candidate after the bounded component cycle, the harness terminated deterministically before assembly.

The immediate cause was therefore a missing canonical lineage reference, followed by recovery candidates being blocked by a broad equivalence gate. It was not token exhaustion, malformed JSON, an endpoint failure, a manifest failure, or a MiniReason downgrade. The cross-component and cross-stage equivalence matches are preserved in `log.jsonl` and warrant further harness diagnosis.

## Security and replay notes

The private credential directory is deliberately excluded. The manifest records only the API-key environment-variable name, never the credential value. Content-addressed filenames and SHA-256 values are replay and integrity identifiers; they are not model routing or acceptance signals.
