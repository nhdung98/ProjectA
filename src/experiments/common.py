"""Shared data integrity, environment, and outer split checks."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from .validation import generate_splits, validate_splits

ROOT = Path(__file__).resolve().parents[2]
SPLIT_PATH = ROOT / "results/splits/outer.csv"
SPLIT_MANIFEST = ROOT / "results/splits/outer_manifest.json"

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def verify_environment(settings):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Use Python 3.12 for this experiment round")
    packages = {name: version(name) for name in settings["packages"]}
    if packages != settings["packages"]:
        raise ValueError(f"Package versions differ from the protocol environment: {packages}")
    return packages


def load_dataset(settings):
    """Verify raw hashes and confirm prepared values still match their sources."""
    for relative, expected in settings["source_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"Changed source file: {relative}")
    dataset = ROOT / settings["dataset"]
    data = pd.read_csv(dataset, sep="\t")
    features = [column for column in data if column.startswith("gene__")]
    if len(data) != settings["expected_samples"] or len(features) != settings["expected_features"]:
        raise ValueError("Dataset dimensions differ from the agreed cohort")
    if data["subtype"].value_counts().to_dict() != settings["class_counts"]:
        raise ValueError("Subtype counts differ from the agreed cohort")
    for column in ["Sample ID", "Patient ID"]:
        if data[column].isna().any() or data[column].eq("").any() or data[column].duplicated().any():
            raise ValueError(f"Missing or repeated identifiers: {column}")
    values = data[features].to_numpy(dtype=np.float64)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Expression must be finite and nonnegative")

    # Hashes alone do not protect an edited processed file. Check its contents too.
    source_settings = json.loads((ROOT / "configs/data.yaml").read_text(encoding="utf-8"))
    clinical = pd.read_csv(ROOT / source_settings["clinical_file"], sep="\t", dtype=str)
    expression = pd.read_csv(ROOT / source_settings["expression_file"], sep="\t",
                             dtype={"Hugo_Symbol": "string", "Entrez_Gene_Id": "string"})
    names = [f"gene__{symbol if pd.notna(symbol) else 'UNNAMED'}__"
             f"{entrez if pd.notna(entrez) else 'NO_ENTREZ'}__row{row + 1}"
             for row, (symbol, entrez) in enumerate(zip(expression.Hugo_Symbol, expression.Entrez_Gene_Id))]
    eligible = clinical.loc[clinical[source_settings["label_column"]].isin(source_settings["target_subtypes"])]
    expected_ids = [sample for sample in expression.columns[2:] if sample in set(eligible["Sample ID"])]
    if features != names or data["Sample ID"].tolist() != expected_ids:
        raise ValueError("Prepared sample or gene order differs from sources")
    original = eligible.set_index("Sample ID").loc[expected_ids]
    for column in ["Patient ID", source_settings["label_column"]]:
        if data[column].tolist() != original[column].tolist():
            raise ValueError(f"Prepared metadata differs from sources: {column}")
    if data["subtype"].tolist() != original[source_settings["label_column"]].map(source_settings["target_subtypes"]).tolist():
        raise ValueError("Prepared labels differ from clinical sources")
    if not np.array_equal(values, expression[expected_ids].to_numpy(dtype=np.float64).T):
        raise ValueError("Prepared expression differs from source measurements; rerun data preparation")
    return data, features, values


def split_metadata(settings):
    return {"dataset_sha256": sha256(ROOT / settings["dataset"]),
            "validation": settings["validation"], "source_sha256": settings["source_sha256"],
            "scikit_learn": version("scikit-learn")}


def shared_splits(data, settings, create=False):
    expected = generate_splits(data, settings["validation"])
    metadata = split_metadata(settings)
    if not SPLIT_PATH.exists():
        if not create:
            raise ValueError("Shared splits are missing. Run prepare-splits first.")
        if SPLIT_MANIFEST.exists():
            raise ValueError("Split manifest exists without assignments; review it before repair")
        SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        expected.to_csv(SPLIT_PATH, index=False, lineterminator="\n")
        write_json(SPLIT_MANIFEST, {**metadata, "split_sha256": sha256(SPLIT_PATH)})
    if not SPLIT_MANIFEST.exists():
        raise ValueError("Shared split manifest is missing")
    stored = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    if stored != {**metadata, "split_sha256": sha256(SPLIT_PATH)}:
        raise ValueError("Shared splits or dataset changed; do not silently regenerate assignments")
    splits = pd.read_csv(SPLIT_PATH)
    validate_splits(splits, data, settings["validation"], settings["labels"])
    # Checking seed-derived assignments detects even a rewritten manifest.
    if not splits.equals(expected):
        raise ValueError("Saved splits do not match the agreed seed and dataset order")
    return splits
