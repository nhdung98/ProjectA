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
    lines = ["# Báo cáo screening vòng A", "",
             "Chỉ chứa thông tin kỹ thuật và điểm inner. Vòng A không dự đoán outer test, nên không có điểm outer nào để xem.", ""]
    if missing:
        lines += [f"**Thiếu pipeline:** {', '.join(missing)}.", ""]
    if len(configs) > 1:
        lines += [f"**Cảnh báo:** các run dùng {len(configs)} phiên bản config khác nhau ({', '.join(configs)}). "
                  "Pipeline nào sửa config thì chạy lại vòng A trước khi đóng băng.", ""]
    lines += ["## 1. Trạng thái và runtime", "",
              table(["Pipeline", "Member", "Commit", "Dev", "Trạng thái", "Fold", "Fit", "Giây/fit", "Phút"],
                    [[r["pipeline"], r["member"], r["commit"], "có" if r["development"] else "không", r["status"], r["folds"],
                      r["fits"], fmt(r["seconds_per_fit"], 2), fmt(r["minutes"], 1)] for r in inventory]),
              "", "## 2. Warning và hội tụ", "",
              table(["Pipeline", "Tổng", "Theo loại", "n_iter lúc refit (max/giới hạn)", "Ví dụ"],
                    [[r["pipeline"], r["total"], r["by_category"], r["refit_max_iter"], r["example"][:120]] for r in warnings_rows]),
              "", "## 3. Tham số được chọn (g*) và điểm inner", "",
              table(["Pipeline", "Fold", "g*", "Inner macro-F1"],
                    [[p["pipeline"], f"R{p['repeat']}·F{p['fold']}", p["g_star"],
                      "—" if p["best_inner"] is None else fmt(p["best_inner"])] for p in picks]),
              "", "## 4. Chạm biên grid (≥ 3/5 fold ở cùng một biên)", ""]
    lines += [table(["Pipeline", "Tham số", "Biên", "Số fold", "Việc cần làm"],
                    [[h["pipeline"], h["parameter"], h["edge"], h["folds"], h["action"]] for h in hits])
              if hits else "Không có pipeline nào chạm biên."]
    lines += ["", "## 5. Kiểm tra engine bằng P02", ""]
    if gap is None:
        lines.append("Chưa có kết quả P02.")
    else:
        lines.append(f"Điểm inner của P02 so với Round 1 lệch tối đa {gap:.2e}: "
                     + ("**khớp**." if gap < 1e-9 else "**KHÔNG khớp. Dừng lại và tìm lỗi engine trước khi đóng băng.**"))
    lines += ["", "## 6. Trước khi gắn tag `p3.0-frozen`", "",
              "- Sửa mọi lỗi và warning ở mục 1–2, hoặc ghi rõ vì sao chấp nhận.",
              "- Mỗi dòng \"extend once\" ở mục 4: mở rộng grid đúng một bước trong `configs/protocol3.json`, "
              "chạy lại vòng A cho pipeline đó với `--replace`, rồi chạy lại lệnh này.",
              "- Không loại pipeline vì điểm thấp. Chỉ được bỏ pipeline không chạy nổi trong ngân sách thời gian.", ""]
    (out / "screening.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {out / 'screening.md'}")
