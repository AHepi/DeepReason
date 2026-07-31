"""Render probe_results.json as the evidence document attached to the run.

Markdown rather than JSON because the attachment path admits documents, and a
table is what the model has to reason over. Every number here is measured; no
aggregate is presented without the per-task cells underneath it, because the
question explicitly forbids hiding a partial result inside a mean.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    source, destination = sys.argv[1], sys.argv[2]
    with open(source) as handle:
        data = json.load(handle)

    jolts = data["jolts"]
    tasks = list(data["task_prompts"])
    order = ["baseline"] + [name for name in jolts if name != "baseline"]

    lines = [
        "# Measured attractor collapse in glm-5.2, and what nine jolts do to it",
        "",
        f"Model `{data['model']}`, {data['samples']} independent calls per cell, "
        "`reasoning_effort: none`.",
        "",
        "`top_mass` is the share of samples landing on the single most common "
        "answer. **1.0 is total collapse**; the floor at this sample count is "
        f"{round(1 / data['samples'], 4)}. `distinct` counts distinct normalised "
        "answers.",
        "",
        "## The tasks",
        "",
    ]
    for name, prompt in data["task_prompts"].items():
        lines.append(f"- `{name}`: {prompt}")

    lines += ["", "## top_mass by jolt and task", "",
              "| jolt | " + " | ".join(tasks) + " |",
              "|---|" + "---|" * len(tasks)]
    for jolt in order:
        row = []
        for task in tasks:
            cell = jolts[jolt].get(task, {})
            row.append("n/a" if cell.get("top_mass") is None else f"{cell['top_mass']:.2f}")
        lines.append(f"| `{jolt}` | " + " | ".join(row) + " |")

    lines += ["", "## distinct answers by jolt and task", "",
              "| jolt | " + " | ".join(tasks) + " |",
              "|---|" + "---|" * len(tasks)]
    for jolt in order:
        row = [str(jolts[jolt].get(task, {}).get("distinct", "n/a")) for task in tasks]
        lines.append(f"| `{jolt}` | " + " | ".join(row) + " |")

    lines += ["", "## Full histograms", "",
              "The mode alone hides whether a jolt spread the mass or merely moved "
              "it to a different single answer. These are the counts.", ""]
    for jolt in order:
        lines.append(f"### `{jolt}`")
        lines.append("")
        for task in tasks:
            cell = jolts[jolt].get(task, {})
            histogram = cell.get("histogram") or {}
            rendered = ", ".join(f"{k!r}x{v}" for k, v in histogram.items())
            lines.append(
                f"- `{task}` — samples {cell.get('samples')}, "
                f"distinct {cell.get('distinct')}, top_mass {cell.get('top_mass')}: "
                f"{rendered}"
            )
        lines.append("")

    lines += [
        "## What the driver did, exactly",
        "",
        "Each cell is N independent HTTPS calls to the provider's chat-completions "
        "endpoint with `max_tokens: 256` and `reasoning_effort: none`. Answers are "
        "normalised by lowercasing, stripping surrounding punctuation and "
        "collapsing whitespace, then truncated to 64 characters. A call that "
        "failed after three retries is dropped, so `samples` may be below N — "
        "check it before comparing cells.",
        "",
        "Sampling knobs per jolt: `temperature_high` T=1.3; `temperature_max` "
        "T=1.8; `top_p_wide` T=1.0 with top_p=0.99; `seed_varied` sends an "
        "explicit per-call `seed` at default temperature. The remaining jolts "
        "change only the prompt or system message and leave sampling at the "
        "provider default.",
        "",
        "`school_stance` rotates a system message naming `school-0..school-4` and "
        "asserting each school has a distinct temperament — this harness's own "
        "schools mechanism reduced to its per-call conditioning effect.",
        "",
        "## Known limits of this evidence",
        "",
        "- One model family. Every number is glm-5.2.",
        "- Six tasks, all short-answer with a known dominant response. Nothing "
        "here measures collapse in framings or solution shapes, which is where "
        "the question says the cost actually falls.",
        "- N per cell is small. A `top_mass` difference of one or two samples is "
        "not a result; state which differences survive that.",
        "- Answer normalisation can merge genuinely different answers ('7' and "
        "'seven') or split identical ones. The histograms are given so you can "
        "check whether any conclusion depends on that.",
    ]

    with open(destination, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
