"""Round A screening: technical facts and inner CV only. Outer test is never read."""
import json
import math

import pandas as pd

from src.experiments.common import ROOT, write_json
from .pipelines import pipeline_spec
from .results import fmt, load_runs, runtime, selected_params, table, warning_counts


def reference_difference(config, folder):
    """Largest gap between new P02 inner scores and the archived Round 1 search, for the folds present."""
    archived = json.loads((ROOT / config["reference"]["run"] / "search_results.json").read_text(encoding="utf-8"))
    lookup = {(r["repeat"], r["fold"], json.dumps(r["params"], sort_keys=True)): r["scores"] for r in archived}
    search = pd.read_csv(folder / "search_results.csv")
    gaps = []
    for _, row in search.iterrows():
        reference = lookup.get((row["repeat"], row["fold"], row["params"]))
        if reference is None:
            return math.inf
        gaps += [abs(row[f"inner_{i + 1}"] - value) for i, value in enumerate(reference)]
    return max(gaps)


def next_step(values, edge):
    """Suggested one-step extension when the grid is evenly spaced on a log or linear scale."""
    numbers = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(numbers) != len(values) or 0 in numbers:
        return f"one step past {edge}; choose the value"
    ratios = {round(b / a, 6) for a, b in zip(numbers, numbers[1:])}
    if len(ratios) == 1:
        ratio = ratios.pop()
        return f"add {edge * ratio:g}" if edge == numbers[-1] else f"add {edge / ratio:g}"
    return f"one step past {edge}; choose the value"


def boundary_hits(config, spec, chosen):
    """Parameters whose selected value sits on the same grid edge in enough outer folds."""
    rules = config["screening"]
    hits = []
    by_repeat = {}
    for (repeat, _), params in chosen.items():
        by_repeat.setdefault(repeat, []).append(params)
    for name, values in spec["grid"].items():
        for repeat, picks in sorted(by_repeat.items()):
            for edge in dict.fromkeys([values[0], values[-1]]):
                count = sum(1 for p in picks if p[name] == edge)
                if count < rules["boundary_min_folds"]:
                    continue
                if len(values) < rules["boundary_min_values"]:
                    verdict = f"not applicable: only {len(values)} grid values"
                elif edge in rules["natural_limits"].get(name, []):
                    verdict = "natural limit: nothing to extend"
                else:
                    verdict = f"extend once: {next_step(values, edge)}"
                hits.append(dict(pipeline=spec["id"], parameter=name, repeat=repeat, edge=edge,
                                 folds=f"{count}/{len(picks)}", action=verdict))
    return hits


def screen(config, folders, out):
    runs = load_runs(folders, "A")
    expected = [spec["id"] for spec in config["pipelines"]]
    missing = [p for p in expected if p not in runs]
    inventory, warnings_rows, picks, hits = [], [], [], []
    for pipeline_id in [p for p in expected if p in runs]:
        run, spec = runs[pipeline_id], pipeline_spec(config, pipeline_id)
        manifest, cost = run["manifest"], runtime(run)
        complete = sum(1 for f in manifest["folds"] if f["status"] == "complete")
        inventory.append(dict(pipeline=pipeline_id, member=manifest["member"], commit=(manifest["git_commit"] or "")[:9],
                              development=manifest["development"], status=manifest["status"], folds=f"{complete}/5",
                              fits=cost["fits"], seconds_per_fit=cost["seconds_per_fit"],
                              minutes=cost["wall_seconds"] / 60, config_sha256=manifest["config_sha256"][:12]))
        counts = warning_counts(run)
        iterations = [d["n_iter"] for d in run["details"] if "n_iter" in d]
        limit = spec["model"].get("max_iter")
        warnings_rows.append(dict(pipeline=pipeline_id, total=int(sum(counts.values())),
                                  by_category="; ".join(f"{k} {v}" for k, v in counts.items()) or "none",
                                  refit_max_iter=f"{max(iterations)}/{limit}" if iterations and limit else "n/a",
                                  example=run["warnings"]["message"].iloc[0] if len(run["warnings"]) else ""))
        chosen = selected_params(run)
        for f in manifest["folds"]:
            if f["status"] == "complete":
                picks.append(dict(pipeline=pipeline_id, repeat=f["repeat"], fold=f["fold"],
                                  g_star=json.dumps(f["best_params"], sort_keys=True), best_inner=f["best_inner"]))
            else:
                picks.append(dict(pipeline=pipeline_id, repeat=f["repeat"], fold=f["fold"], g_star="failed: " + f["error"],
                                  best_inner=None))
        hits += boundary_hits(config, spec, chosen)
    reference = config["reference"]["pipeline"]
    gap = reference_difference(config, runs[reference]["folder"]) if reference in runs else None
    configs = sorted({row["config_sha256"] for row in inventory})
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "screening.json", dict(inventory=inventory, warnings=warnings_rows, selected=picks,
                                            boundary=hits, missing=missing,
                                            reference_max_difference=None if gap is None or math.isinf(gap) else gap,
                                            config_sha256=configs))
    lines = ["# Round A screening report", "",
             "Technical checks and inner-validation results only. Round A does not predict outer test patients, so this report contains no outer-test performance estimates. Numbers use a decimal comma (0,75 means 0.75).", ""]
    if missing:
        lines += [f"**Missing pipelines:** {', '.join(missing)}.", ""]
    if len(configs) > 1:
        lines += [f"**Warning:** runs used {len(configs)} different configurations ({', '.join(configs)}). "
                  "Rerun affected pipelines with the agreed configuration before freezing.", ""]
    lines += ["## 1. Completion and runtime", "",
              "Check that every pipeline finished all five outer-training searches. A fit is one training operation. Seconds/fit uses accumulated inner-fit and refit time; wall minutes is elapsed fold time and can be shorter when fits run in parallel. Setup and final packaging are excluded. Member identifies the assigned batch, not necessarily the person operating the machine. Dev indicates development mode. Different computers and parallel settings prevent a controlled speed comparison.", "",
              table(["Pipeline", "Member", "Commit", "Dev", "Status", "Folds", "Fits", "Seconds/fit", "Wall minutes"],
                    [[r["pipeline"], r["member"], r["commit"], "yes" if r["development"] else "no", r["status"], r["folds"],
                      r["fits"], fmt(r["seconds_per_fit"], 2), fmt(r["minutes"], 1)] for r in inventory]),
              "", "## 2. Warnings and convergence", "",
              "Warnings flag conditions that need review, including failure to converge. Refit iterations shows the largest recorded iteration count among outer-training refits versus the allowed limit; it does not summarize every inner fit. N/a means this iteration comparison is not reported for that model. Zero recorded warnings is encouraging but does not prove scientific correctness.", "",
              table(["Pipeline", "Total", "Warning categories", "Refit iterations (maximum/limit)", "Example"],
                    [[r["pipeline"], r["total"], r["by_category"], r["refit_max_iter"], r["example"]] for r in warnings_rows]),
              "", "## 3. Selected parameters and inner-validation scores", "",
              "Each row describes one outer fold's training data. Inner CV compares parameter combinations; g* is the combination with the highest mean inner macro-F1, using the declared tie rule. R1-F1 means repeat 1, fold 1. These scores were used to choose parameters, so they are not independent test scores or final evidence that one pipeline is better. An empty parameter dictionary means there was nothing to tune.", "",
              table(["Pipeline", "Fold", "Selected parameters (g*)", "Inner macro-F1"],
                    [[p["pipeline"], f"R{p['repeat']}·F{p['fold']}", p["g_star"],
                      "—" if p["best_inner"] is None else fmt(p["best_inner"])] for p in picks]),
              "", "## 4. Search-grid boundaries (same edge selected in at least 3/5 folds)", "",
              "A grid is the list of parameter values tested. Repeatedly selecting its smallest or largest value may suggest trying beyond that range; it does not prove that a better value exists. Extend once is the protocol's recommendation for a single extension before freezing, followed by rerunning the affected Round A pipeline. A natural limit cannot be extended; short grids are exempt under the declared rule. These are recommendations only: this report changes no settings.", ""]
    lines += [table(["Pipeline", "Parameter", "Edge", "Folds", "Recommended action"],
                    [[h["pipeline"], h["parameter"], h["edge"], h["folds"], h["action"]] for h in hits])
              if hits else "No grid-boundary flags."]
    lines += ["", "## 5. Reference reproduction check (P02)", "",
              "P02 repeats the previous SVM reference configuration. This compares every available candidate's inner-fold score with the archived run and reports the largest absolute difference. A match supports reproducibility of that reference search; it does not validate all other models or estimate performance on new patients.", ""]
    if gap is None:
        lines.append("P02 results are not available yet.")
    else:
        lines.append(f"Maximum absolute difference from archived Round 1 inner scores: {gap:.2e}: "
                     + ("**match**." if gap < 1e-9 else "**MISMATCH. Investigate before freezing.**"))
    lines += ["", "## 6. Before creating the `p3.0-frozen` tag", "",
              "Freezing locks the code and configuration for official Round B evaluation. Resolve technical issues and the protocol's boundary decisions first. Round A searches are screening evidence; Round B runs all three repeats separately and produces outer-test predictions.", "",
              "- Resolve errors and review warnings in sections 1-2, documenting any accepted warnings.",
              "- For each extend-once recommendation in section 4, agree the value, extend the grid once in `configs/protocol3.json`, rerun the affected Round A pipeline with `--replace`, and regenerate this report. Preserve earlier submissions.",
              "- Do not remove pipelines because their inner scores are low. Exclusion is permitted only for inability to run within the declared time budget.", ""]
    (out / "screening.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {out / 'screening.md'}")
