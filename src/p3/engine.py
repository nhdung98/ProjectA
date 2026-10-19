"""Nested CV for one pipeline: inner grid search on shared folds, refit, and saved evidence."""
import json
import shutil
import time
import warnings

from joblib import Parallel, delayed
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits

from src.experiments.common import sha256, write_json
from .pipelines import build_pipeline, candidates, parameters

PREDICTION_COLUMNS = ["pipeline", "repeat", "fold", "Sample ID", "Patient ID", "true_subtype", "predicted_subtype"]


def fit_once(spec, config, candidate, x, y, fit, score=None, labels=None):
    """Fit one fresh pipeline; warnings are captured here so parallel workers report them too."""
    with threadpool_limits(limits=config["blas_threads"]), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        start = time.perf_counter()
        model = build_pipeline(spec, config).set_params(**parameters(spec, candidate))
        model.fit(x[fit], y[fit])
        result = None
        if score is not None:
            predicted = model.predict(x[score])
            result = float(f1_score(y[score], predicted, labels=labels, average="macro", zero_division=0))
        seconds = time.perf_counter() - start
    messages = [f"{w.category.__name__}: {str(w.message)[:300]}" for w in caught]
    return model, result, seconds, messages


def inner_task(spec, config, candidate, x, y, fit, validation, labels):
    _, score, seconds, messages = fit_once(spec, config, candidate, x, y, fit, validation, labels)
    return score, seconds, messages


def select(scores):
    """Highest mean inner score; an exact tie keeps the earlier declared candidate, as GridSearchCV does."""
    means = scores.mean(axis=1)
    best = int(np.flatnonzero(means == means.max())[0])
    return best, means


def packed(mask):
    return np.packbits(np.asarray(mask, dtype=bool)).tobytes().hex()


def unpacked(text, length):
    return np.unpackbits(np.frombuffer(bytes.fromhex(text), dtype=np.uint8))[:length].astype(bool)


def feature_details(model, features):
    """Genes actually kept by the training-fold filter and selector of the refit model."""
    steps = model.named_steps
    kept = np.arange(len(features))
    details = {}
    if "filter" in steps:
        mask = steps["filter"].get_support()
        details.update(filter_kept=int(mask.sum()), filter_support_hex=packed(mask))
        kept = kept[mask]
    if "select" in steps:
        kept = kept[steps["select"].get_support()]
        details["selected_genes"] = [features[i] for i in kept]
    final = steps["model"]
    if hasattr(final, "priors_"):
        details["training_priors"] = dict(zip(final.classes_.tolist(), final.priors_.tolist()))
    estimator = getattr(final, "estimator_", final)
    if hasattr(estimator, "n_iter_"):
        details["n_iter"] = int(np.max(estimator.n_iter_))
    return details


def write_outputs(destination, manifest, search, details, predictions, warning_rows):
    destination.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(search).to_csv(destination / "search_results.csv", index=False, lineterminator="\n")
    write_json(destination / "feature_details.json", details)
    pd.DataFrame(warning_rows, columns=["repeat", "fold", "stage", "candidate", "inner_fold", "message"]).to_csv(
        destination / "warnings.csv", index=False, lineterminator="\n")
    if predictions is not None:
        pd.DataFrame(predictions, columns=PREDICTION_COLUMNS).to_csv(
            destination / "predictions.csv", index=False, lineterminator="\n")
    manifest["outputs"] = {p.name: sha256(p) for p in sorted(destination.iterdir()) if p.name != "manifest.json"}
    write_json(destination / "manifest.json", manifest)


def prepare_destination(destination, replace):
    if destination.exists():
        if not replace:
            raise ValueError(f"{destination} already exists. Use --replace to rerun this pipeline")
        shutil.rmtree(destination)


def run_pipeline(spec, config, inputs, folds, destination, *, predict_outer, manifest, jobs=1, y=None, labels=None,
                 models=None):
    """Run every outer fold in ``folds``. Outer test samples are only touched when ``predict_outer``.

    Refit models are discarded unless a ``models`` list is passed to collect them.
    """
    data, features, values = inputs["data"], inputs["features"], inputs["values"]
    y = np.asarray(data["subtype"] if y is None else y, dtype=object)
    labels = inputs["labels"] if labels is None else labels
    grid = candidates(spec)
    manifest = {**manifest, "pipeline": spec["id"], "spec": spec, "predict_outer": predict_outer,
                "candidates": grid, "status": "running", "folds": []}
    search, details, warning_rows = [], [], []
    predictions = [] if predict_outer else None
    for outer in folds:
        repeat, fold, train, test = outer["repeat"], outer["fold"], outer["train"], outer["test"]
        start = time.perf_counter()
        record = dict(repeat=repeat, fold=fold, train_samples=len(train), test_samples=len(test))
        try:
            x, target = values[train], y[train]
            tasks = [(c, i, fit, validation) for c in range(len(grid)) for i, (fit, validation) in enumerate(outer["inner"])]
            results = Parallel(n_jobs=jobs)(delayed(inner_task)(spec, config, grid[c], x, target, fit, validation, labels)
                                            for c, _, fit, validation in tasks)
            scores = np.zeros((len(grid), len(outer["inner"])))
            seconds = np.zeros_like(scores)
            for (c, i, _, _), (score, elapsed, messages) in zip(tasks, results):
                scores[c, i], seconds[c, i] = score, elapsed
                warning_rows += [dict(repeat=repeat, fold=fold, stage="inner", candidate=c, inner_fold=i + 1, message=m)
                                 for m in messages]
            best, means = select(scores)
            for c, candidate in enumerate(grid):
                row = dict(repeat=repeat, fold=fold, candidate=c, params=json.dumps(candidate, sort_keys=True))
                row.update({f"inner_{i + 1}": scores[c, i] for i in range(scores.shape[1])})
                row.update(mean_inner=means[c], selected=c == best, fit_seconds=seconds[c].sum())
                search.append(row)
            model, _, refit_seconds, messages = fit_once(spec, config, grid[best], x, target, np.arange(len(train)))
            warning_rows += [dict(repeat=repeat, fold=fold, stage="refit", candidate=best, inner_fold=0, message=m)
                             for m in messages]
            details.append(dict(repeat=repeat, fold=fold, **feature_details(model, features)))
            if models is not None:
                models.append(model)
            if predict_outer:
                with threadpool_limits(limits=config["blas_threads"]):
                    predicted = model.predict(values[test])
                rows = data.iloc[test]
                predictions += [dict(pipeline=spec["id"], repeat=repeat, fold=fold, **{"Sample ID": s, "Patient ID": p},
                                     true_subtype=t, predicted_subtype=v)
                                for s, p, t, v in zip(rows["Sample ID"], rows["Patient ID"], y[test], predicted)]
            record.update(status="complete", best_candidate=best, best_params=grid[best], best_inner=float(means[best]),
                          fits=int(scores.size + 1), inner_fit_seconds=float(seconds.sum()), refit_seconds=refit_seconds,
                          warnings=sum(1 for w in warning_rows if (w["repeat"], w["fold"]) == (repeat, fold)))
        except Exception as error:
            record.update(status="failed", error=f"{type(error).__name__}: {error}")
        record["wall_seconds"] = time.perf_counter() - start
        manifest["folds"].append(record)
        print(f"{spec['id']} repeat={repeat} fold={fold}: {record['status']} in {record['wall_seconds']:.0f} s"
              + (f", best inner {record['best_inner']:.3f}, {record['warnings']} warnings" if record["status"] == "complete"
                 else f" ({record['error']})"), flush=True)
        if record["status"] == "failed":
            break
        write_outputs(destination, manifest, search, details, predictions, warning_rows)
    manifest["status"] = "failed" if manifest["folds"][-1]["status"] == "failed" else "complete"
    write_outputs(destination, manifest, search, details, predictions, warning_rows)
    return manifest
