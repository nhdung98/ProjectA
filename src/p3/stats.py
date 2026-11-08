"""Metrics and the single statistical test registered in protocol 3.0."""
import numpy as np
from scipy import stats
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, matthews_corrcoef
from sklearn.metrics import precision_recall_fscore_support


def pooled_metrics(true, predicted, labels):
    precision, recall, f1, support = precision_recall_fscore_support(true, predicted, labels=labels, zero_division=0)
    return dict(macro_f1=float(f1_score(true, predicted, labels=labels, average="macro", zero_division=0)),
                balanced_accuracy=float(balanced_accuracy_score(true, predicted)),
                mcc=float(matthews_corrcoef(true, predicted)),
                per_class={label: dict(precision=float(precision[i]), recall=float(recall[i]), f1=float(f1[i]),
                                       support=int(support[i])) for i, label in enumerate(labels)},
                confusion_matrix=confusion_matrix(true, predicted, labels=labels).tolist())


def macro_f1(true, predicted, labels):
    return float(f1_score(true, predicted, labels=labels, average="macro", zero_division=0))


def wilson(successes, total, confidence=0.95):
    """Wilson score interval; stays inside [0, 1] for small counts and extreme proportions."""
    if total == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(0.5 + confidence / 2)
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (float(max(0.0, centre - half)), float(min(1.0, centre + half)))


def correlated_ttest(differences, rope, rho):
    """Bayesian correlated t-test (Benavoli et al. 2017) for paired per-fold differences.

    The variance is inflated by 1/n + rho/(1-rho), the Nadeau-Bengio correction for
    folds that share training data. Returns P(worse), P(practically equivalent), P(better)
    for the second pipeline, where differences are second minus first.
    """
    d = np.asarray(differences, dtype=np.float64)
    n, mean = len(d), float(d.mean())
    sd = float(d.std(ddof=1))
    if sd == 0:
        # All folds agree exactly: the posterior is a point mass at the mean.
        return dict(mean=mean, sd=0.0, worse=float(mean < -rope), equivalent=float(-rope <= mean <= rope),
                    better=float(mean > rope))
    scale = np.sqrt(1 / n + rho / (1 - rho)) * sd
    posterior = stats.t(df=n - 1, loc=mean, scale=scale)
    worse, below = float(posterior.cdf(-rope)), float(posterior.cdf(rope))
    return dict(mean=mean, sd=sd, worse=worse, equivalent=below - worse, better=1 - below)


def conclusion(result, threshold):
    """Registered reading rule: conclude only when one probability reaches the threshold.

    Returns the region with the highest probability and whether it reached the threshold.
    """
    region = max(["worse", "equivalent", "better"], key=result.get)
    return region, result[region] >= threshold
