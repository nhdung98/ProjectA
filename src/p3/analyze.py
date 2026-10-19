"""Round B analysis: every table of the results template, from the submitted run folders."""
import json

import numpy as np
import pandas as pd

from src.experiments.common import ROOT, write_json
from .inputs import split_settings
from .pipelines import pipeline_spec
from .results import fmt, load_runs, runtime, table, warning_counts
from .screen import boundary_hits, reference_difference
from .stats import conclusion, correlated_ttest, macro_f1, pooled_metrics, wilson

FOLDS = [(r, f) for r in (1, 2, 3) for f in range(1, 6)]


def check_runs(config, runs, labels, n_samples):
    expected = [spec["id"] for spec in config["pipelines"]]
    missing = [p for p in expected if p not in runs]
    if missing:
        raise ValueError(f"Missing round B results for {', '.join(missing)}")
    if len({run["manifest"]["config_sha256"] for run in runs.values()}) != 1:
        raise ValueError("Round B runs used different configs; every run must come from the frozen tag")
    samples = None
    for name, run in runs.items():
        manifest, predictions = run["manifest"], run["predictions"]
        done = [(f["repeat"], f["fold"]) for f in manifest["folds"] if f["status"] == "complete"]
        if manifest["status"] != "complete" or done != FOLDS or manifest.get("development"):
            raise ValueError(f"{name} is not a complete official round B run")
        if predictions is None:
            raise ValueError(f"{name} has no outer predictions")
        for repeat, group in predictions.groupby("repeat"):
            if group["Sample ID"].duplicated().any():
                raise ValueError(f"{name} predicts a sample twice in repeat {repeat}")
            ids = frozenset(group["Sample ID"])
            if len(ids) != n_samples:
                raise ValueError(f"{name} repeat {repeat} has {len(ids)} predictions, not {n_samples}")
            samples = samples or ids
            if ids != samples:
                raise ValueError(f"{name} repeat {repeat} covers different samples")
        if not set(predictions["predicted_subtype"]).issubset(labels):
            raise ValueError(f"{name} predicts unknown labels")


def per_repeat(predictions, labels):
    return {r: pooled_metrics(g["true_subtype"], g["predicted_subtype"], labels)
            for r, g in predictions.groupby("repeat", sort=True)}


def per_fold(predictions, labels):
    scores = {(r, f): macro_f1(g["true_subtype"], g["predicted_subtype"], labels)
              for (r, f), g in predictions.groupby(["repeat", "fold"], sort=True)}
    return np.array([scores[key] for key in FOLDS])


def meta_select(config, runs, labels):
    """Choose the (pipeline, candidate) with the best mean inner score in each outer fold.

    Ties go to the simpler pipeline, then the earlier candidate. The winner is always its
    own pipeline's g*, so its outer predictions already exist and nothing is refitted.
    """
    rank = {p: i for i, p in enumerate(config["selection"]["simplicity_order"])}
    pool = pd.concat([runs[p]["search"].assign(pipeline=p) for p in config["selection"]["eligible"]], ignore_index=True)
    pool["rank"] = pool["pipeline"].map(rank)
    chosen, predictions = [], []
    for (repeat, fold), group in pool.groupby(["repeat", "fold"], sort=True):
        winner = group.sort_values(["mean_inner", "rank", "candidate"], ascending=[False, True, True]).iloc[0]
        if not winner["selected"]:
            raise ValueError(f"META-SELECT winner at R{repeat}·F{fold} is not its pipeline's g*; check search results")
        own = runs[winner["pipeline"]]["predictions"]
        block = own[(own["repeat"] == repeat) & (own["fold"] == fold)]
        predictions.append(block.assign(pipeline="META-SELECT"))
        chosen.append(dict(repeat=int(repeat), fold=int(fold), pipeline=winner["pipeline"], params=winner["params"],
                           inner=float(winner["mean_inner"])))
    return pd.DataFrame(chosen), pd.concat(predictions, ignore_index=True)


def equivalence(config, means, folds, rope):
    eligible = config["selection"]["eligible"]
    rank = {p: i for i, p in enumerate(config["selection"]["simplicity_order"])}
    top = min(eligible, key=lambda p: (-means[p], rank[p]))
    rows, group = [], [top]
    for other in [p for p in eligible if p != top]:
        # Differences are top minus other, so "better" is P(top beats other beyond the ROPE).
        result = correlated_ttest(folds[top] - folds[other], rope, config["analysis"]["rho"])
        excluded = result["better"] >= config["analysis"]["decision_probability"]
        rows.append(dict(pipeline=other, mean_difference=result["mean"], p_top_better=result["better"],
                         in_group=not excluded))
        if not excluded:
            group.append(other)
    return dict(top=top, group=group, chosen=min(group, key=rank.get), rows=rows)


def reading(pipeline, region, decided):
    text = {"better": f"{pipeline} tốt hơn", "worse": f"{pipeline} kém hơn", "equivalent": "tương đương"}[region]
    return f"**{text.capitalize() if region == 'equivalent' else text}**" if decided else f"Chưa kết luận, nghiêng {text}"


def summary_cell(values, digits=3):
    return f"{fmt(float(np.mean(values)), digits)} ± {fmt(float(np.std(values, ddof=1)), digits)}"


def recall_cell(metrics, label):
    cls = metrics["per_class"][label]
    hits, total = round(cls["recall"] * cls["support"]), cls["support"]
    low, high = wilson(hits, total)
    return f"{hits}/{total} = {fmt(cls['recall'])} ({fmt(low)}–{fmt(high)})"


def analyze(config, folders, out):
    labels = split_settings(config)["labels"]
    rules = config["analysis"]
    runs = load_runs(folders, "B")
    check_runs(config, runs, labels, split_settings(config)["expected_samples"])
    order = [spec["id"] for spec in config["pipelines"]]
    repeats = {p: per_repeat(runs[p]["predictions"], labels) for p in order}
    folds = {p: per_fold(runs[p]["predictions"], labels) for p in order}
    means = {p: float(np.mean([m["macro_f1"] for m in repeats[p].values()])) for p in order}
    chosen, meta_predictions = meta_select(config, runs, labels)
    meta = per_repeat(meta_predictions, labels)
    meta_folds = per_fold(meta_predictions, labels)
    ablations = []
    for pair in config["ablations"]:
        for rope in (rules["rope"], rules["rope_sensitivity"]):
            result = correlated_ttest(folds[pair["to"]] - folds[pair["from"]], rope, rules["rho"])
            region, decided = conclusion(result, rules["decision_probability"])
            ablations.append(dict(**pair, rope=rope, **result, region=region, decided=decided,
                                  conclusion=reading(pair["to"], region, decided)))
    groups = {rope: equivalence(config, means, folds, rope) for rope in (rules["rope"], rules["rope_sensitivity"])}
    selected = groups[rules["rope"]]["chosen"]
    focus = repeats[selected][rules["ci_repeat"]]
    reference = config["reference"]
    archive = pd.read_csv(ROOT / reference["run"] / "predictions.csv")
    new = runs[reference["pipeline"]]["predictions"]
    merged = new.merge(archive, on=["repeat", "Sample ID"], suffixes=("", "_round1"))
    engine_check = dict(macro_f1=means[reference["pipeline"]],
                        round1_macro_f1=json.loads((ROOT / reference["run"] / "metrics.json").read_text(encoding="utf-8"))["summary"]["macro_f1"]["mean"],
                        prediction_differences=int((merged["predicted_subtype"] != merged["predicted_subtype_round1"]).sum()),
                        compared_predictions=len(merged),
                        inner_max_difference=reference_difference(config, runs[reference["pipeline"]]["folder"]))

    out.mkdir(parents=True, exist_ok=True)
    fold_names = [f"R{r}·F{f}" for r, f in FOLDS]
    pd.DataFrame([dict(pipeline=p, **{f"R{r}": repeats[p][r]["macro_f1"] for r in (1, 2, 3)}, mean=means[p]) for p in order]
                 ).to_csv(out / "table_a.csv", index=False, lineterminator="\n")
    pd.DataFrame([dict(pipeline=p, **dict(zip(fold_names, folds[p]))) for p in order] +
                 [dict(pipeline="META-SELECT", **dict(zip(fold_names, meta_folds)))]).to_csv(
        out / "table_b.csv", index=False, lineterminator="\n")
    pd.concat([runs[p]["search"].assign(pipeline=p) for p in order], ignore_index=True).to_csv(
        out / "table_c.csv", index=False, lineterminator="\n")
    chosen.to_csv(out / "meta_select.csv", index=False, lineterminator="\n")
    pd.DataFrame(ablations).to_csv(out / "ablations.csv", index=False, lineterminator="\n")
    summary = dict(meta_select=dict(per_repeat={r: m["macro_f1"] for r, m in meta.items()},
                                    mean=float(np.mean([m["macro_f1"] for m in meta.values()])),
                                    sd=float(np.std([m["macro_f1"] for m in meta.values()], ddof=1)),
                                    frequency={p: int(n) for p, n in chosen["pipeline"].value_counts().items()}),
                   table_a={p: dict(per_repeat={r: repeats[p][r]["macro_f1"] for r in (1, 2, 3)}, mean=means[p]) for p in order},
                   top=groups[rules["rope"]]["top"], selected=selected,
                   equivalence={str(rope): g for rope, g in groups.items()}, engine_check=engine_check,
                   config_sha256=next(iter(runs.values()))["manifest"]["config_sha256"])
    write_json(out / "summary.json", json.loads(json.dumps(summary, default=float)))

    name = {spec["id"]: f"{spec['id']} {spec['name']}" for spec in config["pipelines"]}
    lines = ["# Kết quả Protocol 3.0 (vòng B)", "",
             "Sinh tự động bởi `python -m src.p3 analyze`. Các ô **Nhận xét** để người phân tích viết.", "",
             "## 0. Kiểm tra engine bằng P02", "",
             f"P02 mean macro-F1 = {fmt(engine_check['macro_f1'], 4)}; Round 1 = {fmt(engine_check['round1_macro_f1'], 4)}. "
             f"Dự đoán khác Round 1: {engine_check['prediction_differences']}/{engine_check['compared_predictions']}. "
             f"Điểm inner lệch tối đa {engine_check['inner_max_difference']:.2e}.",
             "" if engine_check["prediction_differences"] == 0 else "\n**Engine không tái tạo Round 1. Dừng lại, không đọc tiếp.**\n",
             "## 1. Bảng A · macro-F1 gộp 254 ca", "",
             table(["Pipeline", "Vai trò", "R1", "R2", "R3", "Mean ± SD"],
                   [[name[p], pipeline_spec(config, p)["role"]] + [fmt(repeats[p][r]["macro_f1"]) for r in (1, 2, 3)]
                    + [summary_cell([repeats[p][r]["macro_f1"] for r in (1, 2, 3)])] for p in order]),
             "", "> **Nhận xét:** ", "",
             f"## 2. Bảng A2 · metric phụ (recall theo repeat {rules['ci_repeat']}, Wilson CI 95%)", "",
             table(["Pipeline", "BA", "MCC"] + [f"Recall {c}" for c in rules["recall_classes"]],
                   [[name[p], summary_cell([m["balanced_accuracy"] for m in repeats[p].values()]),
                     summary_cell([m["mcc"] for m in repeats[p].values()])]
                    + [recall_cell(repeats[p][rules["ci_repeat"]], c) for c in rules["recall_classes"]] for p in order]),
             "", "> **Nhận xét:** ", "",
             "## 3. Bảng B · macro-F1 theo từng outer fold", "",
             table(["Pipeline"] + fold_names + ["TB 15 fold"],
                   [[p] + [fmt(v) for v in folds[p]] + [fmt(float(folds[p].mean()))] for p in order]),
             "", "## 4. Bảng D · tham số được chọn ở mỗi outer fold", ""]
    hits, rows = [], []
    for p in order:
        grid = pipeline_spec(config, p)["grid"]
        if not grid:
            continue
        picks = {(f["repeat"], f["fold"]): f["best_params"] for f in runs[p]["manifest"]["folds"]}
        rows.append([p] + [" · ".join(str(picks[key][name]) for name in grid) for key in FOLDS])
        hits += boundary_hits(config, pipeline_spec(config, p), picks)
    lines += ["Mỗi ô ghi giá trị theo thứ tự tham số của grid: "
              + "; ".join(f"{s['id']} " + " · ".join(n.split("__")[-1] for n in s["grid"]) for s in config["pipelines"] if s["grid"])
              + ".", "", table(["Pipeline"] + fold_names, rows)]
    lines += ["", "Chạm biên grid ở ≥ 3/5 fold trong một repeat (chỉ báo cáo; grid đã đóng băng):", ""]
    lines += [table(["Pipeline", "Tham số", "Repeat", "Biên", "Số fold", "Ghi chú"],
                    [[h["pipeline"], h["parameter"], f"R{h['repeat']}", h["edge"], h["folds"], h["action"]] for h in hits])
              if hits else "Không có."]
    frequency = summary["meta_select"]["frequency"]
    lines += ["", "## 5. Câu 1 · META-SELECT: con số chính", "",
              table(["Outer fold", "Pipeline thắng (theo inner)", "Tham số", "Điểm inner", "Điểm outer của nó"],
                    [[f"R{c.repeat}·F{c.fold}", name[c.pipeline], c.params, fmt(c.inner),
                      fmt(float(folds[c.pipeline][FOLDS.index((c.repeat, c.fold))]))] for c in chosen.itertuples()]),
              "", "**Tần suất thắng:** " + ", ".join(f"{p} {n}" for p, n in frequency.items()) + ".", "",
              "**META-SELECT:** " + " · ".join(f"R{r} {fmt(m['macro_f1'])}" for r, m in meta.items())
              + f" → **{fmt(summary['meta_select']['mean'])} ± {fmt(summary['meta_select']['sd'])}**.", "",
              "> **Nhận xét:** ", "",
              "## 6. Câu 2 · Ablation (Bayesian correlated t-test)", ""]
    for rope in (rules["rope"], rules["rope_sensitivity"]):
        lines += [f"### ROPE ± {fmt(rope, 2)}" + (" (chính)" if rope == rules["rope"] else " (độ nhạy)"), "",
                  table(["Cặp", "Thay đổi", "Mean d", "Kém hơn", "Tương đương", "Tốt hơn", "Kết luận"],
                        [[f"{a['from']} → {a['to']}", a["change"], f"{a['mean']:+.3f}".replace(".", ","), fmt(a["worse"], 2),
                          fmt(a["equivalent"], 2), fmt(a["better"], 2), a["conclusion"]] for a in ablations if a["rope"] == rope]), ""]
    lines += ["> **Nhận xét:** ", "", "## 7. Câu 3 · Nhóm tương đương và pipeline mang sang app", ""]
    for rope, group in groups.items():
        lines += [f"### ROPE ± {fmt(rope, 2)}" + (" (chính)" if rope == rules["rope"] else " (độ nhạy)"), "",
                  f"T = {name[group['top']]} ({fmt(means[group['top']])}).", "",
                  table(["X", "Mean d (T − X)", "P(T tốt hơn X quá ROPE)", "Kết quả"],
                        [[name[r["pipeline"]], f"{r['mean_difference']:+.3f}".replace(".", ","), fmt(r["p_top_better"]),
                          "Trong nhóm" if r["in_group"] else "Loại"] for r in group["rows"]]),
                  "", f"Nhóm tương đương: {', '.join(group['group'])}. Pipeline đơn giản nhất: **{name[group['chosen']]}**.", ""]
    lines += [f"Hiệu năng của pipeline được chọn phải trích bằng con số META-SELECT "
              f"({fmt(summary['meta_select']['mean'])} ± {fmt(summary['meta_select']['sd'])}), không bằng điểm riêng của nó.", "",
              "> **Nhận xét:** ", "",
              f"## 8. Confusion matrix của {name[selected]} (repeat {rules['ci_repeat']})", "",
              table(["Thật \\ Dự đoán"] + labels + ["Tổng"],
                    [[f"**{label}**"] + row + [sum(row)] for label, row in zip(labels, focus["confusion_matrix"])]),
              "",
              table(["Lớp", "Số ca", "Precision", "Recall", "F1", "Recall 95% Wilson CI"],
                    [[label, c["support"], fmt(c["precision"]), fmt(c["recall"]), fmt(c["f1"]),
                      "–".join(fmt(v) for v in wilson(round(c["recall"] * c["support"]), c["support"]))]
                     for label, c in focus["per_class"].items()]),
              "", f"Macro-F1 {fmt(focus['macro_f1'])}, BA {fmt(focus['balanced_accuracy'])}, MCC {fmt(focus['mcc'])}.", "",
              "> **Nhận xét:** ", "",
              "## 9. Độ nhạy", "",
              f"Chạy sau bước này cho {selected} và P02, P06: `python -m src.p3 sensitivity --analysis S-5CLASS "
              f"--pipeline {selected} --pipeline P02 --pipeline P06` (tương tự cho S-TSS, S-206).", "",
              "## 10. Runtime và số fit", ""]
    costs = {p: runtime(runs[p]) for p in order}
    lines += [table(["Pipeline", "Member", "Fit", "Giây/fit", "Phút (thời gian fit)", "Warning"],
                    [[p, runs[p]["manifest"]["member"], costs[p]["fits"], fmt(costs[p]["seconds_per_fit"], 2),
                      fmt(costs[p]["fit_seconds"] / 60, 1),
                      "; ".join(f"{k} {v}" for k, v in warning_counts(runs[p]).items()) or "0"] for p in order]),
              "", "Máy của từng member:", ""]
    machines = {runs[p]["manifest"]["member"]: runs[p]["manifest"]["machine"] for p in order}
    lines += [f"- Member {m}: {info['system']} {info['machine']}, {info['cpu_count']} lõi" for m, info in sorted(machines.items())]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {out / 'report.md'}; META-SELECT {summary['meta_select']['mean']:.3f}, selected pipeline {selected}")
