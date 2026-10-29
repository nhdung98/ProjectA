"""Load and verify the run folders that members submit."""
import json
from pathlib import Path

import pandas as pd

from src.experiments.common import sha256


def pipeline_folders(folders):
    found = []
    for folder in folders:
        folder = Path(folder)
        if (folder / "manifest.json").exists():
            found.append(folder)
        elif folder.is_dir():
            found += sorted(p for p in folder.iterdir() if (p / "manifest.json").exists())
        else:
            raise FileNotFoundError(f"No result folder at {folder}")
    if not found:
        raise ValueError("No pipeline results found in the given folders")
    return found


def load_runs(folders, round_name):
    """Every pipeline once, from the stated round, with outputs matching their checksums."""
    runs = {}
    for folder in pipeline_folders(folders):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        name = manifest["pipeline"]
        if manifest.get("round") != round_name:
            raise ValueError(f"{folder} is from round {manifest.get('round')}, not round {round_name}")
        if name in runs:
            raise ValueError(f"{name} appears twice: {runs[name]['folder']} and {folder}")
        required = {'search_results.csv', 'feature_details.json', 'warnings.csv'}
        if round_name == 'B':
            required.add('predictions.csv')
        if set(manifest.get('outputs', {})) != required:
            raise ValueError(f'{folder} has an incomplete or unexpected output inventory')
        for filename, expected in manifest["outputs"].items():
            if sha256(folder / filename) != expected:
                raise ValueError(f"{folder / filename} changed after the run")
        if set(p.name for p in folder.iterdir()) - set(manifest["outputs"]) - {"manifest.json"}:
            raise ValueError(f"{folder} contains files the run did not write")
        predictions = folder / "predictions.csv"
        if round_name == "A" and predictions.exists():
            raise ValueError(f"{folder} holds outer predictions; round A must stay blind to outer test")
        runs[name] = dict(folder=folder, manifest=manifest,
                          search=pd.read_csv(folder / "search_results.csv"),
                          warnings=pd.read_csv(folder / "warnings.csv"),
                          details=json.loads((folder / "feature_details.json").read_text(encoding="utf-8")),
                          predictions=pd.read_csv(predictions) if predictions.exists() else None)
    return runs


def selected_params(run):
    return {(f["repeat"], f["fold"]): f.get("best_params") for f in run["manifest"]["folds"] if f["status"] == "complete"}


def runtime(run):
    folds = [f for f in run["manifest"]["folds"] if f["status"] == "complete"]
    seconds = sum(f["inner_fit_seconds"] + f["refit_seconds"] for f in folds)
    fits = sum(f["fits"] for f in folds)
    return dict(fits=fits, fit_seconds=seconds, seconds_per_fit=seconds / fits if fits else None,
                wall_seconds=sum(f["wall_seconds"] for f in folds))


def warning_counts(run):
    frame = run["warnings"]
    if frame.empty:
        return {}
    return frame["message"].str.split(":").str[0].value_counts().to_dict()


def fmt(value, digits=3):
    """Decimal comma, matching the team's protocol documents."""
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace(".", ",")


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)
