# Run-local website imports

Chunked website designs may request a small, controlled set of project-specific browser
capabilities without adding npm dependencies to DeepReason. The component manifest remains the
single accepted plan. It states the art direction first, then the capability slot, intended use,
provider preference, approved exports, component ownership, lifecycle, reduced-motion behavior,
fallback, and byte budget.

The trusted import service runs only after the design survives and before component problems are
spawned. It checks the nested `IMPORT_POLICY`, researches registry/package metadata, resolves exact
versions, creates an exact npm lockfile with lifecycle scripts disabled, verifies integrity and
licences, stores every package archive with the run, generates a bounded API capsule and alias, and
uses the run's exact archived esbuild toolchain to prove the selected exports exist. Component
prompts receive only their approved capsules, not full READMEs or the whole catalog.

Components access packages through `DeepReasonImports.<alias>`. Direct imports, `require`, remote
URLs, CDNs, undeclared exports, and undeclared aliases fail the component commitment. Animated
components declare initialization and cleanup exports. WebGL owners additionally declare a canvas,
pixel-ratio cap, context-loss behavior, reduced-motion behavior, and static fallback.

Assembly extracts component JavaScript and CSS, bundles both with the stored toolchain, records
esbuild metadata for byte attribution, and inlines the results into the existing self-contained
HTML export. Browser verification remains network-disabled. Replay reads the stored archives,
lockfile, aliases, capsules, and toolchain record; it never resolves `latest` or contacts npm.

Registry outages, downloads, integrity mismatches, forbidden install scripts, malformed archives,
and unavailable tooling are operational failures. They produce an `import-deferred` event and no
warrant, leaving the design schedulable. Demonstrated slot, export, licence, compatibility, remote
dependency, and byte-budget failures use the ordinary criticism path. External package facts are
stored as evidence artifacts and cited from the warrant validity node; package archives themselves
are import artifacts, not evidence.

The built-in `baseline`, `classless`, and `layout` assets are unchanged. They remain the offline
technical floor and selectable local fallbacks. Runtime providers extend the same catalog,
assembler, import provenance, dependence graph, support pass, browser checks, and replay model.
