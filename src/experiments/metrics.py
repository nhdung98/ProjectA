"""Calculate metrics from complete out-of-fold predictions per repeat."""
import numpy as np
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.metrics import precision_recall_fscore_support


def summarize(predictions, labels, sample_ids, n_repeats):
    scores = []
    if len(predictions) != len(sample_ids) * n_repeats:
        raise ValueError("Metrics require all predictions, including every split")
    if set(predictions["repeat"]) != set(range(1, n_repeats + 1)):
        raise ValueError("Unexpected repeats in predictions")
    for repeat, group in predictions.groupby("repeat", sort=True):
        if group["Sample ID"].duplicated().any() or set(group["Sample ID"]) != set(sample_ids):
            raise ValueError("Each sample must have one prediction per repeat")
        true, predicted = group["true_subtype"], group["predicted_subtype"]
        if set(true) != set(labels) or not set(predicted).issubset(labels):
            raise ValueError("Unexpected labels in predictions")
        precision, recall, f1, support = precision_recall_fscore_support(
            true, predicted, labels=labels, zero_division=0)
        scores.append({
            "repeat": int(repeat),
            "macro_f1": float(f1_score(true, predicted, labels=labels, average="macro", zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(true, predicted)),
            "per_class": {label: {"precision": float(precision[i]), "recall": float(recall[i]),
                                  "f1": float(f1[i]), "support": int(support[i])}
                          for i, label in enumerate(labels)},
            "confusion_matrix": confusion_matrix(true, predicted, labels=labels).tolist(),
        })
    summary = {metric: {"mean": float(np.mean([s[metric] for s in scores])),
                        "sample_std": float(np.std([s[metric] for s in scores], ddof=1))}
               for metric in ["macro_f1", "balanced_accuracy"]}
    return {"label_order": labels, "repeats": scores, "summary": summary,
            "interpretation": "Split variation only; not a confidence interval or independent cohorts."}
