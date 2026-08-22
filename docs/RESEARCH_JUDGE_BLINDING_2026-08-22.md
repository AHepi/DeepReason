# Judge blinding and provenance leakage — external research note

Operator-supplied 2026-08-22, committed verbatim below the rule. The
claims and links are EXTERNAL and unverified by this repository's own
instruments; nothing here is evidence in the record's sense. Treat as
design intelligence, the same standing as
docs/OLLAMA_CLOUD_OPERATIONS.md.

Consumption points, recorded so this note is read where it matters:

- **Judge-audit evidence base.** Any design leaning on LLM judges must
  consult this alongside the committed judge-audit tranche (CLAUDE.md,
  solo-run law: judges are suspect-by-default). Finding 1 below gives
  external, quantified support for structural blinding: bias lives in
  the label, not the content, and the minimum viable leak is the
  single bit "same-origin or not."
- **Rung 6 (frame render semantics), binding requirement when its
  prompt is written:** provenance-shaped fields are OMITTED from
  rendered packs, never blanked or tagged "redacted" — the placebo
  result shows a present-but-empty provenance slot draws MORE judge
  attention than a populated one. The renderer emits no empty
  provenance slots, and a check pins it.
- **Recorded non-fix, so nobody proposes the tranche:** warrant prose
  that self-identifies ("as in our earlier result") cannot be
  neutralized by any envelope or render rule. The standing answer is
  the existing law — judge prose is never status-changing on its own;
  demonstrative, typed outcomes carry the weight. A "warrant
  anonymizer" is not a fix and should not be built.
- **Out of scope:** the cryptographic selective-disclosure section
  (BBS+, nullifiers, credential wallets) solves adversarial
  multi-party trust. DeepReason is a single-operator harness; blinding
  is achieved by the renderer not including provenance. Relevant only
  if the harness ever becomes multi-party.

---

## Operator-supplied text, verbatim

Blinding works, which is the finding that most justifies your
architecture. In [Self- and Other-Labels Induce Bidirectional Bias in
LLM Judges](https://www.alphaxiv.org/abs/2608.18091), apparent
self-preference under blind evaluation collapses to nothing once
selection quality and judge severity are controlled — the coefficient
falls to β_S = +0.003 on the average score, and the only surviving
effect runs *against* self-preference
[Blind Evaluation](https://www.alphaxiv.org/abs/2608.18091?page=5).
Attach a label to the identical content and the effect reappears at
β_L = +0.43, with the actual-source effect and the label×source
interaction both non-significant
[Label Effect](https://www.alphaxiv.org/abs/2608.18091?page=6). The
bias is in the label, not the content. Remove the label and it goes
away.

The detail that matters most for your design: those labels named no
model. They were the anonymous phrases "your own selection" and
"another language model," chosen specifically to isolate the
self–other distinction from model identity
[Label Design](https://www.alphaxiv.org/abs/2608.18091?page=4). So the
minimum viable leak is not a key ID or a proposer name — it is the
single bit *same-origin or not*. That bit alone moved nine of ten
judges, six of them symmetrically inflating under self-labels while
deflating under other-labels.

Score deviation from no-label baseline (identical content), per judge:

| Judge | Self-label | Other-label |
| --- | --- | --- |
| Qwen3.6-35B | +0.131 | −0.523 |
| Gemini 3.1 Pro | +0.302 | −0.339 |
| Qwen3.6-Plus | +0.175 | −0.444 |
| Kimi K2.6 | +0.147 | −0.386 |
| Mistral Large 3 | +0.081 | −0.265 |
| Grok 4.3 | +0.126 | −0.195 |
| DeepSeek-V4-Pro | +0.443 | +0.101 |
| Claude Opus 4.7 | +0.275 | −0.023 |
| GPT-5.5 | −0.019 | −0.340 |

### Your nullifier is more dangerous than I implied

This is where I'd revise my earlier answer. A nullifier scoped
per-conjecture leaks exactly that same-origin bit if the critic ever
sees it — and the research says that bit is the entire effect. Keep
the tag comparison strictly gateway-side, never in the critic's input.
Same reasoning kills the placeholder-field idea, and here the evidence
is sharper than intuition.
[Label Effects](https://www.alphaxiv.org/abs/2604.05593) ran a placebo
condition — a syntactically identical label reading
`Source of the answer: [TAG]` with the Human/AI semantics stripped —
and found it "often elicits the largest LogRatio, suggesting that an
underspecified label can attract extra processing to the label region
because it has no semantic meaning"
[Placebo Label](https://www.alphaxiv.org/abs/2604.05593?page=13). A
redacted-but-present provenance slot draws more attention than a
populated one. Omit the field entirely.

That paper also gives you the mechanism, which is worth knowing
because it tells you why prompt-level fixes won't hold. Across every
model and every label condition, judges allocate *denser attention to
the label region than to the content region* at the judgment step, and
label dominance is stronger under Human labels
[Attention Allocation](https://www.alphaxiv.org/abs/2604.05593?page=5).
Their recommendation is explicit and matches what you're building:
"blind or identity-controlled judging to verify that LLM judges depend
on the content itself"
[Recommendation](https://www.alphaxiv.org/abs/2604.05593?page=8).

### The clustering attack is real and the fix is expensive

My warning about per-proposer keys partitioning the corpus is exactly
the documented weakness of hash-based selective disclosure.
[On Cryptographic Mechanisms for the Selective Disclosure of
Verifiable Credentials](https://www.alphaxiv.org/abs/2401.08196)
states it plainly: the presentation proof contains the issuer-signed
commitment, so that identifier "links each VP uniquely to one VC, and
therefore to its Holder" — meaning the holder must use a *different
credential for every presentation*, with the issuer supplying distinct
versions containing the same attributes salted differently, and a live
channel to replenish them
[Hiding Commitment Linkability](https://www.alphaxiv.org/abs/2401.08196?page=21).
In your system that means a fresh signed envelope per conjecture, not
per proposer — operationally the reason gateway re-signing is so
tempting.

| Mechanism | Unlinkable | Fast | Compact | Quantum-safe |
| --- | --- | --- | --- | --- |
| Salted hash list (SD-JWT style) | ± [Assessment](https://www.alphaxiv.org/abs/2401.08196?page=30) | ++ | − | + |
| Merkle tree | ± | ++ | + | + |
| [BBS/BBS+](https://www.alphaxiv.org/abs/2401.08196) | ++ | ± | + | − |

BBS gets you unlinkability from a single signature, with the
randomness generated holder-side rather than requiring issuer batches
[BBS Tradeoff](https://www.alphaxiv.org/abs/2401.08196?page=30) — but
it rests on pairing assumptions that do not survive quantum, where
hash-based commitments can simply be instantiated with Dilithium,
Falcon, or SPHINCS+
[Quantum Safety](https://www.alphaxiv.org/abs/2401.08196?page=21). If
your harness is long-lived, that trade matters more than the
linkability one.

### The part no crypto fixes

One sobering result on the human side.
[Credential Disclosure in EU Digital Identity Wallets](https://www.alphaxiv.org/abs/2606.06354)
found roughly 20% of users disclosed their official ID to news
websites, and a decision-time assistant only reduced disclosure
mistakes from about 15% to 7%
[Oversharing](https://www.alphaxiv.org/abs/2606.06354?page=1).
Whoever configures your redaction function will overshare by default,
and a warning won't stop them. That is the argument for making
`redact` the only constructor of the critic's input type rather than a
policy someone selects — the residual-risk number is what a
well-designed nudge achieves, and 7% of conjectures leaking provenance
is not a property you can recover from downstream.

The warrant itself remains uncovered by all of this. Nothing in the
literature I found addresses normalizing a justification so it doesn't
encode its own origin, and given that judges attend to provenance
regions preferentially even when those regions are semantically empty,
a warrant carrying "as in our earlier result" will dominate whatever
your envelope discloses.
