"""Generate and check the sample assignments used by every member."""
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold


def generate_splits(data, settings):
    splitter = RepeatedStratifiedKFold(**settings)
    rows = []
    # Keep split bookkeeping small; expression has more than 20,000 columns.
    metadata = data[["Sample ID", "Patient ID", "subtype"]]
    for number, (_, test) in enumerate(splitter.split(np.zeros(len(data)), data["subtype"])):
        block = metadata.iloc[test].copy()
        block.insert(0, "fold", number % settings["n_splits"] + 1)
        block.insert(0, "repeat", number // settings["n_splits"] + 1)
        rows.append(block)
    return pd.concat(rows, ignore_index=True)


def validate_splits(splits, data, settings, labels):
    """Reject incomplete assignments and any patient overlap."""
    required = ["repeat", "fold", "Sample ID", "Patient ID", "subtype"]
    if list(splits.columns) != required:
        raise ValueError("Unexpected split-file columns")
    if len(splits) != len(data) * settings["n_repeats"]:
        raise ValueError("Incomplete split file")
    if data["Patient ID"].duplicated().any():
        raise ValueError("Repeated patients require a revised splitting protocol")
    indexed = data[["Sample ID", "Patient ID", "subtype"]].set_index("Sample ID")
    ids = set(indexed.index)
    if set(splits["repeat"]) != set(range(1, settings["n_repeats"] + 1)):
        raise ValueError("Unexpected repeat numbers")
    for repeat, group in splits.groupby("repeat"):
        if set(group["Sample ID"]) != ids or group["Sample ID"].duplicated().any():
            raise ValueError(f"Repeat {repeat}: samples must appear exactly once")
        if set(group["fold"]) != set(range(1, settings["n_splits"] + 1)):
            raise ValueError("Unexpected fold numbers")
        reference = indexed.loc[group["Sample ID"]]
        for column in ["Patient ID", "subtype"]:
            if reference[column].tolist() != group[column].tolist():
                raise ValueError(f"Split metadata differs from dataset: {column}")
        for _, test in group.groupby("fold"):
            train = indexed.loc[~indexed.index.isin(test["Sample ID"])]
            if set(test["Patient ID"]) & set(train["Patient ID"]):
                raise ValueError("Patient leakage between training and test sets")
            if set(test["subtype"]) != set(labels) or set(train["subtype"]) != set(labels):
                raise ValueError("Each training and test fold must contain every class")


def fold_indices(splits, data):
    """Resolve saved Sample IDs to the current, verified dataset order."""
    for (repeat, fold), group in splits.groupby(["repeat", "fold"], sort=True):
        test_mask = data["Sample ID"].isin(group["Sample ID"]).to_numpy()
        yield int(repeat), int(fold), np.flatnonzero(~test_mask), np.flatnonzero(test_mask)
