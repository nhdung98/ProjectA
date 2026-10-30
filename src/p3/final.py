"""Refit the chosen pipeline on all 254 patients and save the bundle the app loads."""
import json

import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold

from src.experiments.common import write_json
from .engine import prepare_destination, run_pipeline
from .inputs import load_inputs, provenance, require_frozen, verify_environment
from .pipelines import pipeline_spec


def final(config, pipeline_id, jobs, replace, output):
    require_frozen(config)
    summary_path = output / "roundB/analysis/summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    if pipeline_id is None:
        if summary is None:
            raise ValueError("Run analyze first, or name the pipeline with --pipeline")
        pipeline_id = summary["selected"]
    packages = verify_environment(config)
    inputs = load_inputs(config)
    data, features = inputs["data"], inputs["features"]
    everyone = np.arange(len(data))
    settings = config["final"]["inner_validation"]
    # Same tuning procedure as an inner CV, now over the whole cohort; nothing is held out.
    inner = list(StratifiedKFold(**settings).split(np.zeros(len(data)), data["subtype"]))
    destination = output / "final" / pipeline_id
    prepare_destination(destination, replace)
    models = []
    manifest = dict(round="final", member=None, development=False, tuning=settings, **provenance(config, packages))
    run = run_pipeline(pipeline_spec(config, pipeline_id), config, inputs,
                       [dict(repeat=0, fold=0, train=everyone, test=np.array([], dtype=int), inner=inner)],
                       destination, predict_outer=False, manifest=manifest, jobs=jobs, models=models)
    if run["status"] != "complete":
        raise SystemExit(f"Final refit failed; see {destination / 'manifest.json'}")
    joblib.dump(models[0], destination / "model.joblib")
    (destination / "input_features.txt").write_text("\n".join(features) + "\n", encoding="utf-8")
    fold = run["folds"][0]
    card = dict(pipeline=pipeline_id, name=pipeline_spec(config, pipeline_id)["name"], labels=inputs["labels"],
                trained_on=len(data), selected_params=fold["best_params"], tuning_inner_macro_f1=fold["best_inner"],
                input="Raw RSEM values for the genes in input_features.txt, in that order; the model applies log2(x+1)",
                reported_performance=None if summary is None else dict(
                    meta_select_macro_f1=summary["meta_select"]["mean"], sd=summary["meta_select"]["sd"],
                    note="Nested CV estimate of the whole selection procedure; the pipeline's own outer score is not reported"),
                calibration="none: predict() returns a class label only",
                packages=packages, git_commit=manifest["git_commit"], config_sha256=manifest["config_sha256"])
    write_json(destination / "model_card.json", card)
    print(f"Saved {destination}: {pipeline_id} with {fold['best_params']}")
