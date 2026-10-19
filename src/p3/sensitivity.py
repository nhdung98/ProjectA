"""One-repeat sensitivity analyses: site-grouped folds, the 206 reviewed cases, and five classes."""
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

from src.experiments.common import ROOT, sha256, write_json
from .engine import prepare_destination, run_pipeline
from .inputs import load_inputs, outer_folds, provenance, require_frozen, verify_environment
from .pipelines import pipeline_spec
from .stats import pooled_metrics


def tissue_source_site(sample_ids):
    """TCGA barcodes carry the collecting site in their second field, e.g. TCGA-3B-A9HR-01 -> 3B."""
    return sample_ids.str.split("-").str[1]


def generated_folds(data, outer_splitter, groups, seed, inner_splits):
    """Fresh seeded outer folds with stratified inner folds inside each outer training set."""
    y = data["subtype"].to_numpy()
    folds, rows = [], []
    for fold, (train, test) in enumerate(outer_splitter.split(np.zeros(len(data)), y, groups), 1):
        if groups is not None and set(groups[train]) & set(groups[test]):
            raise ValueError("A site appears in both training and test folds")
        splitter = StratifiedKFold(n_splits=inner_splits, shuffle=True, random_state=seed)
        inner = list(splitter.split(np.zeros(len(train)), y[train]))
        folds.append(dict(repeat=1, fold=fold, train=train, test=test, inner=inner))
        rows += [dict(outer_fold=fold, inner_fold=0, **{"Sample ID": s}) for s in data["Sample ID"].iloc[test]]
        rows += [dict(outer_fold=fold, inner_fold=i, **{"Sample ID": s})
                 for i, (_, validation) in enumerate(inner, 1) for s in data["Sample ID"].iloc[train[validation]]]
    return folds, pd.DataFrame(rows)


def record_splits(assignments, folder, settings):
    """Save new assignments with a manifest; a rerun must reproduce them exactly."""
    path, manifest = folder / "splits.csv", folder / "splits_manifest.json"
    if path.exists():
        if not pd.read_csv(path).equals(assignments) or json.loads(manifest.read_text(encoding="utf-8"))["splits_sha256"] != sha256(path):
            raise ValueError(f"{path} no longer matches its seeded generator")
        return
    folder.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(path, index=False, lineterminator="\n")
    write_json(manifest, {**settings, "splits_sha256": sha256(path)})


def subset(inputs, mask):
    data = inputs["data"].loc[mask].reset_index(drop=True)
    return {**inputs, "data": data, "values": inputs["values"][np.asarray(mask)]}


def setup(config, analysis, inputs, out):
    seed, inner_splits = config["seed"], inputs["settings"]["inner_validation"]["n_splits"]
    rules = config["sensitivity"]
    if analysis == "S-5CLASS":
        merged = inputs["data"]["subtype"].replace(rules["merged_labels"])
        labels = list(dict.fromkeys(rules["merged_labels"].get(label, label) for label in inputs["labels"]))
        # Same shared folds as the main analysis; only the labels merge.
        return inputs, outer_folds(inputs, {1}), merged.to_numpy(), labels
    if analysis == "S-TSS":
        if rules["s_tss_max_drop"] is None:
            raise ValueError("Set sensitivity.s_tss_max_drop in configs/protocol3.json before running S-TSS; "
                             "the team must fix what counts as a large drop in advance")
        groups = tissue_source_site(inputs["data"]["Sample ID"]).to_numpy()
        splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        folds, assignments = generated_folds(inputs["data"], splitter, groups, seed, inner_splits)
        record_splits(assignments, out / "splits", dict(analysis=analysis, outer="StratifiedGroupKFold by TSS",
                                                        n_splits=5, inner_splits=inner_splits, seed=seed))
        return inputs, folds, None, inputs["labels"]
    listing = ROOT / rules["s206_sample_ids"]
    if not listing.exists():
        raise ValueError(f"S-206 needs the reviewed Cell 2017 sample list at {rules['s206_sample_ids']} "
                         "(one TCGA Sample ID per line)")
    reviewed = {line.strip() for line in listing.read_text(encoding="utf-8").splitlines() if line.strip()}
    unknown = reviewed - set(inputs["data"]["Sample ID"])
    if unknown:
        raise ValueError(f"{len(unknown)} listed samples are not in the cohort, e.g. {sorted(unknown)[0]}")
    reduced = subset(inputs, inputs["data"]["Sample ID"].isin(reviewed).to_numpy())
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    folds, assignments = generated_folds(reduced["data"], splitter, None, seed, inner_splits)
    record_splits(assignments, out / "splits", dict(analysis=analysis, samples=len(reviewed), list_sha256=sha256(listing),
                                                    n_splits=5, inner_splits=inner_splits, seed=seed))
    return reduced, folds, None, inputs["labels"]


def sensitivity(config, analysis, pipelines, jobs, replace, out):
    require_frozen(config)
    packages = verify_environment(config)
    inputs, folds, y, labels = setup(config, analysis, load_inputs(config), out)
    main = ROOT / "experiments/p3.0/roundB/analysis/summary.json"
    reference = json.loads(main.read_text(encoding="utf-8"))["table_a"] if main.exists() else {}
    manifest = dict(round="sensitivity", analysis=analysis, member=None, development=False, **provenance(config, packages))
    results = {}
    for pipeline_id in pipelines:
        destination = out / pipeline_id
        prepare_destination(destination, replace)
        run = run_pipeline(pipeline_spec(config, pipeline_id), config, inputs, folds, destination, predict_outer=True,
                           manifest=manifest, jobs=jobs, y=y, labels=labels)
        if run["status"] != "complete":
            raise SystemExit(f"{pipeline_id} failed; see {destination / 'manifest.json'}")
        predictions = pd.read_csv(destination / "predictions.csv")
        metrics = pooled_metrics(predictions["true_subtype"], predictions["predicted_subtype"], labels)
        main_r1 = reference.get(pipeline_id, {}).get("per_repeat", {}).get("1")
        results[pipeline_id] = dict(macro_f1=metrics["macro_f1"], balanced_accuracy=metrics["balanced_accuracy"],
                                    mcc=metrics["mcc"], main_repeat1_macro_f1=main_r1,
                                    drop=None if main_r1 is None or analysis == "S-5CLASS" else main_r1 - metrics["macro_f1"])
        if analysis == "S-TSS" and results[pipeline_id]["drop"] is not None:
            results[pipeline_id]["large_drop"] = results[pipeline_id]["drop"] > config["sensitivity"]["s_tss_max_drop"]
        print(f"{analysis} {pipeline_id}: macro-F1 {metrics['macro_f1']:.3f}"
              + ("" if main_r1 is None else f" (main R1 {main_r1:.3f})"), flush=True)
    write_json(out / "summary.json", dict(analysis=analysis, labels=labels, pipelines=results))
