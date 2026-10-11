"""Audit a completed run without using the runner's metric calculations."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .common import ROOT, load_dataset, sha256, shared_splits, verify_environment
from .svm import load_settings, shared_inner, candidates, INNER
from .svm import provenance


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_run(folder, settings, data, splits):
    """Check identities, fold assignments, completion, and independently counted scores."""
    folder = Path(folder)
    manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    predictions = pd.read_csv(folder / "predictions.csv")
    details = json.loads((folder / "feature_details.json").read_text(encoding="utf-8"))
    require(manifest["status"] == "complete" and not manifest["smoke"], "Only complete full runs can pass validation")
    require(config["shared"] == settings and not config["smoke"], "Run settings differ from the reviewed configuration")
    configuration = config["configuration"]
    choices = settings["configurations"]
    require(configuration in choices, "Unexpected configuration settings")
    require(manifest["configuration"] == configuration["id"], "Manifest configuration mismatch")
    for key, expected in [("source_sha256", settings["source_sha256"]),
                          ("dataset_sha256", sha256(ROOT / settings["dataset"])),
                          ("split_sha256", sha256(ROOT / "results/splits/outer.csv")),
                          ("packages", settings["packages"])]:
        require(manifest[key] == expected, f"Run provenance mismatch: {key}")
    # Documentation can change after a run. The executable experiment code must match.
    # Review and reporting tools do not train models and can be added after a run.
    training_files = ["__init__.py", "pipeline.py", "validation.py", "metrics.py", "common.py", "svm.py"]
    for name in training_files:
        path = ROOT / "src/experiments" / name
        relative = path.relative_to(ROOT).as_posix()
        require(manifest["code_sha256"].get(relative) == sha256(path), f"Training code changed: {relative}")

    inner = shared_inner(data, splits, settings)
    require(manifest['inner_split_sha256'] == sha256(INNER), 'Inner assignments mismatch')
    require(manifest['code_sha256'].get('configs/svm.json') == sha256(ROOT/'configs/svm.json'), 'Search configuration hash mismatch')
    require((folder/'warnings.log').stat().st_size == 0, 'Warnings require resolution')
    tuning = json.loads((folder/'search_results.json').read_text(encoding='utf-8'))
    grid = candidates(configuration, settings)
    require(len(tuning) == len(grid)*15, 'Incomplete inner search results')
    for fit in manifest['folds']:
        records = [r for r in tuning if r['repeat']==fit['repeat'] and r['fold']==fit['fold']]
        require([r['candidate'] for r in records] == list(range(len(grid))), 'Candidate order mismatch')
        require([r['params'] for r in records] == grid, 'Search grid mismatch')
        for record in records:
            scores = np.asarray(record['scores'])
            require(len(scores)==4 and np.isfinite(scores).all() and ((scores>=0)&(scores<=1)).all(), 'Invalid inner scores')
            np.testing.assert_allclose(scores.mean(),record['mean_score'],rtol=0,atol=1e-12)
        best = records[int(np.argmax([r['mean_score'] for r in records]))]
        require(fit['best_params']==best['params'], 'Chosen parameters do not match search winner')
        np.testing.assert_allclose(fit['best_inner_score'],best['mean_score'],rtol=0,atol=1e-12)
        require(fit['inner_folds']==4 and fit['search_candidates']==len(grid), 'Search fit count mismatch')
    expected_pairs = {(r, f) for r in range(1, settings["validation"]["n_repeats"] + 1)
                      for f in range(1, settings["validation"]["n_splits"] + 1)}
    require(len(manifest["folds"]) == len(expected_pairs), "Incorrect fit count")
    require({(f["repeat"], f["fold"]) for f in manifest["folds"]} == expected_pairs, "Missing or repeated fits")
    for fold in manifest["folds"]:
        test = splits.loc[(splits["repeat"] == fold["repeat"]) & (splits["fold"] == fold["fold"])]
        require(fold["status"] == "complete", "A fit failed or did not converge")
        require(fold["test_samples"] == len(test) and fold["train_samples"] == len(data) - len(test), "Fit sample counts mismatch")
        require(np.isfinite(fold["runtime_seconds"]) and fold["runtime_seconds"] >= 0, "Invalid fit runtime")
    require(len(details) == len(expected_pairs), "Missing feature details")
    require({(d["repeat"], d["fold"]) for d in details} == expected_pairs, "Repeated or missing feature-detail folds")
    features = [column for column in data if column.startswith("gene__")]
    values = data[features].to_numpy(dtype=float)
    for detail in details:
        test_ids = splits.loc[(splits["repeat"] == detail["repeat"]) &
                             (splits["fold"] == detail["fold"]), "Sample ID"]
        train_mask = ~data["Sample ID"].isin(test_ids).to_numpy()
        # A retained gene must vary in the training samples, in the original column order.
        support = np.ptp(np.log2(values[train_mask] + 1), axis=0) > 0
        expected_genes = np.asarray(features)[support].tolist()
        require(detail["retained_after_variance"] == expected_genes, "Training-fold retained genes mismatch")
        if configuration["reduction"] == "anova":
            selected = detail["selected_genes"]
            require(len(selected) == configuration["k"] and len(set(selected)) == len(selected), "Incorrect ANOVA selection count")
            require(set(selected).issubset(expected_genes), "ANOVA selected an excluded or unknown gene")
        elif configuration["reduction"] == "pca":
            pca = detail["pca"]
            ratios = np.asarray(pca["explained_variance_ratio"])
            require(pca["n_components"] == configuration["k"] and len(ratios) == configuration["k"], "Incorrect PCA component count")
            require(np.isfinite(ratios).all() and (ratios >= 0).all() and ratios.sum() <= 1 + 1e-12, "Invalid PCA explained variance")
            np.testing.assert_allclose(ratios.sum(), pca["total_explained_variance_ratio"], rtol=0, atol=1e-12)
    require((folder / "warnings.log").is_file(), "Missing warning log")
    require(len(predictions) == len(splits), "Incorrect prediction count")
    require(predictions["configuration"].eq(configuration["id"]).all(), "Prediction configuration mismatch")
    require(not predictions.duplicated(["repeat", "Sample ID"]).any(), "Repeated predictions")
    joined = predictions.merge(splits, on=["repeat", "Sample ID"], suffixes=("_prediction", "_split"), validate="one_to_one")
    require(len(joined) == len(splits), "Missing or unexpected predicted samples")
    for left, right in [("fold_prediction", "fold_split"), ("Patient ID_prediction", "Patient ID_split"), ("true_subtype", "subtype")]:
        require(joined[left].equals(joined[right]), f"Prediction metadata mismatch: {left}")

    labels = settings["labels"]
    require(metrics["label_order"] == labels, "Metric label order mismatch")
    require(len(metrics["repeats"]) == settings["validation"]["n_repeats"], "Incorrect metric repeat count")
    require([r["repeat"] for r in metrics["repeats"]] == list(range(1, settings["validation"]["n_repeats"] + 1)), "Metric repeat order mismatch")
    scores = []
    for repeat in metrics["repeats"]:
        group = predictions.loc[predictions["repeat"] == repeat["repeat"]]
        require(set(group["Sample ID"]) == set(data["Sample ID"]), "Incomplete prediction repeat")
        confusion = np.zeros((len(labels), len(labels)), dtype=int)
        for true, predicted in zip(group["true_subtype"], group["predicted_subtype"]):
            require(true in labels and predicted in labels, "Unexpected predicted or true label")
            confusion[labels.index(true), labels.index(predicted)] += 1
        diagonal, support, predicted_count = np.diag(confusion), confusion.sum(axis=1), confusion.sum(axis=0)
        precision = np.divide(diagonal, predicted_count, out=np.zeros(len(labels)), where=predicted_count != 0)
        recall = diagonal / support
        f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(len(labels)), where=(precision + recall) != 0)
        np.testing.assert_array_equal(confusion, repeat["confusion_matrix"])
        np.testing.assert_allclose([f1.mean(), recall.mean()], [repeat["macro_f1"], repeat["balanced_accuracy"]], rtol=0, atol=1e-12)
        for i, label in enumerate(labels):
            stored = repeat["per_class"][label]
            np.testing.assert_allclose([precision[i], recall[i], f1[i], support[i]],
                                       [stored["precision"], stored["recall"], stored["f1"], stored["support"]], rtol=0, atol=1e-12)
        scores.append([f1.mean(), recall.mean()])
    scores = np.asarray(scores)
    for i, name in enumerate(["macro_f1", "balanced_accuracy"]):
        np.testing.assert_allclose([scores[:, i].mean(), scores[:, i].std(ddof=1)],
                                   [metrics["summary"][name]["mean"], metrics["summary"][name]["sample_std"]], rtol=0, atol=1e-12)
    return predictions, metrics, {"status": "passed", "configuration": configuration["id"],
                                  "fits": len(expected_pairs), "predictions": len(predictions),
                                  "inner_search_checked": True, "inner_split_sha256": sha256(INNER),
                                  "warning_log_empty": (folder / "warnings.log").stat().st_size == 0,
                                  "metrics_independently_recomputed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_folder", type=Path, help="Folder containing a completed run")
    parser.add_argument("--reference", type=Path, help="Completed baseline to compare against")
    parser.add_argument("--report", type=Path, help="Optional JSON validation report")
    args = parser.parse_args()
    settings = load_settings()
    verify_environment(settings)
    data, _, _ = load_dataset(settings)
    splits = shared_splits(data, settings)
    shared_inner(data, splits, settings)
    predictions, metrics, report = audit_run(args.run_folder.resolve(), settings, data, splits)
    if args.reference:
        previous, old_metrics, _ = audit_run(args.reference.resolve(), settings, data, splits)
        keys = ["repeat", "fold", "Sample ID"]
        pd.testing.assert_frame_equal(predictions.sort_values(keys).reset_index(drop=True), previous.sort_values(keys).reset_index(drop=True))
        require(metrics == old_metrics, "Reproduced metrics differ from reference")
        report["reference_predictions_and_metrics_match"] = True
    report.update(run_folder=str(args.run_folder.resolve()),
                  split_sha256=sha256(ROOT / "results/splits/outer.csv"),
                  validator_sha256=sha256(Path(__file__)), protocol_version=settings["protocol_version"])
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, AssertionError, KeyError, FileNotFoundError) as error:
        raise SystemExit(f"Validation failed: {error}") from error
