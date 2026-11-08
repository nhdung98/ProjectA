"""Training-fold gene filters and the prior-shift decision rule added in protocol 3.0."""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.feature_selection import SelectorMixin
from sklearn.utils.validation import check_is_fitted, validate_data


class ExpressionFilter(SelectorMixin, BaseEstimator):
    """Keep genes expressed above a log2 threshold in enough training samples.

    An absolute sample count, rather than a percentage, keeps genes that are only
    active in the two smallest subtypes. With ``top_mad`` set, the expressed genes
    are further reduced to the most variable ones by median absolute deviation,
    measured on the log2 scale before any scaler.
    """

    def __init__(self, log2_threshold=1.0, min_samples=5, top_mad=None):
        self.log2_threshold = log2_threshold
        self.min_samples = min_samples
        self.top_mad = top_mad

    def fit(self, x, y=None):
        x = validate_data(self, x, dtype=np.float64)
        expressed = (x > self.log2_threshold).sum(axis=0) >= self.min_samples
        support = expressed.copy()
        if self.top_mad is not None:
            kept = np.flatnonzero(expressed)
            if len(kept) < self.top_mad:
                raise ValueError(f"Only {len(kept)} expressed genes; cannot keep the top {self.top_mad} by MAD")
            values = x[:, kept]
            mad = np.median(np.abs(values - np.median(values, axis=0)), axis=0)
            # Stable sort keeps the earlier gene when MAD values tie at the cut-off.
            top = kept[np.argsort(-mad, kind="stable")[: self.top_mad]]
            support = np.zeros_like(expressed)
            support[top] = True
        self.support_ = support
        return self

    def _get_support_mask(self):
        check_is_fitted(self, "support_")
        return self.support_


class PriorShift(ClassifierMixin, BaseEstimator):
    """Predict argmax_c p(c|x) * prior_c ** (-alpha), with priors from the training fold.

    alpha = 0 is the unadjusted classifier; alpha = 1 fully removes the training priors.
    One shared alpha avoids tuning six class thresholds on a handful of rare cases.
    """

    def __init__(self, estimator=None, alpha=0.0):
        self.estimator = estimator
        self.alpha = alpha

    def fit(self, x, y):
        self.estimator_ = clone(self.estimator).fit(x, y)
        self.classes_ = self.estimator_.classes_
        counts = np.array([np.sum(np.asarray(y) == label) for label in self.classes_], dtype=np.float64)
        self.priors_ = counts / counts.sum()
        return self

    def predict(self, x):
        check_is_fitted(self, "estimator_")
        adjusted = self.estimator_.predict_proba(x) * self.priors_ ** (-float(self.alpha))
        return self.classes_[np.argmax(adjusted, axis=1)]

