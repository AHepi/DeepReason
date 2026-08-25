<!-- DR-SEAM-calculus-x-rules -->
Verified-at: f9fcd1136
Verify: python -m pytest tests/test_frame_render.py -q
Owns: src/deepreason/calculus/render.py
Sides: DR-SUB-calculus, DR-SUB-rules

# calculus x rules

**NEW at Rung 6, and the pair genuinely did not interact before.** `INDEX.md`'s
matrix had no row for it because `rules/` imported nothing from `calculus/`
through Rungs 3c, 4 and 5 — the claim substrate was reached from the scheduler,
the CLI, the MCP facade, `programs.py` and `invariants.py`, never from a rule.
Rung 6's frame slice is the first thing a rule needs from the calculus, and the
edge is recorded here rather than left as a fact only a grep would find.

## The agreement

The seam is NARROW IN BOTH DIRECTIONS, and the two directions differ in kind.
Three symbols cross in total.

**`rules` → `calculus`, and it is ATTENTION.** `rules/conj.py` and
`rules/crit.py` call `calculus.render.render_frame_slice_context` and
`render_frame_crisis_context`, each returning `str | None`. `calculus/` decides
WHAT a consulted frame says about itself; `rules/` decides when to ask and hands
the answer to `llm/` as pack text. Nothing else in `calculus/` is importable by
a rule. The returned text is built from replayed state, stored nowhere, and
moves no label — A9's render half and Prop 12.5 at the render layer. A rule that
could obtain a DECISION from this module would be a generation seat reading
standing into evidence, which is what L-5 forbids.

**`calculus` → `rules`, and it is a WARRANT CONSTRUCTOR.** Rung 5's promotion
sweep calls `rules.warrants.register_fail_warrant` when a promotion criterion
returns `fail` (an `overrun` mints nothing). It is one symbol, deliberately: the
tree has exactly one warrant constructor, and a promotion criterion minting its
own would be a second authority over what an attack edge is.

**So the edge is a CYCLE, not a tree, and the first version of this document
said otherwise.** It claimed "nothing in `calculus/` imports `rules/` at all, so
the edge is acyclic" — written before the check was run, and the check refuted
it in the same commit. The cycle is safe because the two directions never meet:
the import that goes down is inside `promotion.py`, the import that comes up is
inside `render.py`, neither module imports the other's counterpart, and both are
function-local imports so neither is a load-time cycle. What makes it worth
pinning rather than tolerating is that a widening in either direction would join
them — a render that minted anything, or a promotion criterion that rendered.

`check: python -c "import ast,pathlib; T=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; n=[x for t in T for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.calculus')]; mods={x.module for x in n}; seen={a.name for x in n for a in x.names}; assert mods == {'deepreason.calculus.render'}, sorted(mods); assert seen == {'render_frame_crisis_context', 'render_frame_slice_context'}, sorted(seen)"`
`check: python -c "import ast,pathlib; T={p.name: ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/calculus').rglob('*.py')}; hits={f: sorted(a.name for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.rules') for a in x.names) for f, t in T.items()}; hits={f: v for f, v in hits.items() if v}; assert hits == {'promotion.py': ['register_fail_warrant']}, hits"`
`check: python -c "import ast,pathlib; r=ast.parse(pathlib.Path('src/deepreason/calculus/render.py').read_text()); assert not [x for x in ast.walk(r) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.rules')]; p=ast.parse(pathlib.Path('src/deepreason/calculus/promotion.py').read_text()); assert not [x for x in ast.walk(p) if isinstance(x, ast.ImportFrom) and (x.module or '') == 'deepreason.calculus.render']"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The only crossing | `calculus/render.py` | `render_frame_slice_context`, `render_frame_crisis_context` | a rule receives TEXT; it never receives a grant, a label or a decision |
| Rung 7's succession context uses the SAME crossing | `calculus/render.py` | `render_frame_slice_context` returns the succession pack for a succession trial | the seam did not widen: no new symbol crosses, no new pack section exists, and `llm/packs.py` learns nothing about succession |
| The consult path is not widened for it | `calculus/render.py` | `frame_slices` calls `consulted` and `frames` unchanged | `invariants.py`'s `standing-integrity` check reads `consulted`; a render that needed it widened would reach into frozen surface 3 |
| Which problem a critic's frame belongs to | `rules/crit.py` | `_target_problem` | the frame shown agrees with the standard `_problem_context` leads the pack with |
| Every pack in scope | `rules/conj.py`, `rules/crit.py` | three `render_*_pack` call sites | §9.5's "in every pack in scope" — see `DR-SEAM-llm-x-rules` for the census check |
| Nothing here can write | `calculus/render.py` | no `harness.` mutator, no `create_artifact`, no `register_` | A9: render acts only through attention |
| The one symbol going the other way | `calculus/promotion.py` | `rules.warrants.register_fail_warrant` | a failed promotion criterion mints through the tree's ONE warrant constructor, never its own |

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/render.py').read_text()); bad=[n.func.attr for n in ast.walk(t) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith(('create_', 'register_', 'commit_', 'append_'))]; assert not bad, bad"`
`check: grep -q "def _target_problem" src/deepreason/rules/crit.py && python -m pytest tests/test_frame_render.py::test_the_frame_reaches_a_conjecture_pack_end_to_end -q`

## Why the render lives in `calculus/` and not in `llm/`

Because what a frame slice SAYS is a calculus question and what it COSTS is a
pack question, and the two decay differently. §9.5 fixes the content — the
articulation digest, the standing attackers, the departure directive — and it
changes when the calculus changes. The budget, the caps and the compressibility
flags change when the token economy changes. Putting the text in `llm/packs.py`
would have made every §9.5 amendment a change to the pack renderer, and would
have required `llm/` to import `calculus` for a body it does not reason about.

The alternative that was NOT taken, recorded so it is not re-proposed: passing a
`FrameSliceV1` structure into the renderers. It reverses the import (`llm` →
`calculus`) to no benefit, since `llm/` would immediately flatten it to text.
`frozen_evidence_context` and `citable_evidence_context` already cross as
strings for the same reason.

## The succession exception rides this seam without widening it (Rung 7)

§9.7's one proper render exception — the succession pack suppresses the
incumbent's frame slice and renders both articulation digests — lands ENTIRELY
on the calculus side. `render.frame_slices` returns `()` for a succession
trial and `render_frame_slice_context` returns the succession context instead,
so the two names `rules/` imports are unchanged and the import check above
still pins the crossing to exactly those two.

That was a design constraint, not a convenience. A new pack section would have
needed `llm/packs.py` to know what a succession is, and a new symbol crossing
here would have made the seam two crossings wide for a case that is a
different TEXT rather than a different relationship. It also inherits the
existing slot's non-droppability for free, which a new section would have had
to re-argue.

`check: python -m pytest tests/test_calculus_succession.py::test_the_incumbents_frame_slice_is_suppressed tests/test_calculus_succession.py::test_both_articulation_digests_are_rendered -q`
`check: ! grep -q "succession" src/deepreason/llm/packs.py`

## Traps

- **Believing this seam is one-directional.** It is not, and the first draft of
  this document asserted that it was. `calculus/promotion.py` has imported
  `rules.warrants.register_fail_warrant` since Rung 5. The check above pins
  BOTH directions by name, so a second back-edge fails here rather than being
  discovered by the next reader who assumes a tree.
- **A rule reaching past `render.py` into the rest of the calculus.** The
  check above pins the import set to exactly this one module and these two
  names. A rule that imported `standing.consulted` directly would be reading
  the consult path that `invariants.py`'s frozen-surface check also reads, and
  a later widening for the rule's convenience would move a frozen surface.
- **Assuming "in every pack in scope" is a property of `render_crit_pack`.**
  It is a property of its CALL SITES, and there are three, not two: the
  atomic-decomposition path in `crit.py` exists only after a batch critic
  exhausts its schema, and the first implementation of Rung 6 missed it. The
  census check lives in `DR-SEAM-llm-x-rules` and counts sites.
- **Reading the succession suppression as a second exception.** It is ONE
  site, in `frame_slices`, and both renderers inherit it. A future change that
  suppressed inside `render_frame_slice_context` instead would leave
  `render_frame_crisis_context` still rendering the incumbent's wounds as
  though they were the frame's own crisis — a succession pack posed in the
  incumbent's vocabulary, which is exactly the bias the exception removes. The
  check under the succession section above pins the site by function name.
- **Expecting `calculus/render.py` to fail loudly on a broken frame.** It does
  not, deliberately: `frames` answers False for a scope that no longer
  compiles, and `declared_departures` skips an undecodable body. A render that
  raised would take down a pack for a presentation fault. What reports the
  fault is `departure_declaration_wf` and `verify_root`'s
  `standing-integrity`, on the record, where it is attackable.
`check: python -m pytest tests/test_frame_render.py::test_a_problem_outside_the_scope_carries_no_frame_slice -q`
