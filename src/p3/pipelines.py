"""Build each protocol 3.0 pipeline from its declared stages."""
from itertools import product
import json

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.svm import SVC

from src.experiments.common import ROOT
from src.experiments.pipeline import log_expression
from .transforms import ExpressionFilter, PriorShift

CONFIG = ROOT / "configs/protocol3.json"


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def pipeline_spec(config, pipeline_id):
    for spec in config["pipelines"]:
        if spec["id"] == pipeline_id:
            return spec
    raise ValueError(f"Unknown pipeline: {pipeline_id}")


def candidates(spec):
    """Grid candidates in declared order: the first parameter varies slowest.

    The order is part of the protocol because absolute ties go to the first candidate.
    """
    grid = spec["grid"]
    return [dict(zip(grid, values)) for values in product(*grid.values())]


def build_model(model, seed):
    kind = model["type"]
    if kind == "dummy":
        return DummyClassifier(strategy=model["strategy"], random_state=seed)
    if kind == "svm":
        # Same SVC settings as protocol 2.0, so P02 reproduces Round 1.
        return SVC(kernel="linear", class_weight=model["class_weight"], probability=False,
                   tol=0.001, max_iter=-1, cache_size=200)
    if kind in {"lr_l2", "lr_l2_prior"}:
        estimator = LogisticRegression(solver="lbfgs", class_weight=model["class_weight"],
                                       max_iter=model["max_iter"], tol=model["tol"])
        return PriorShift(estimator) if kind == "lr_l2_prior" else estimator
    if kind == "lr_elasticnet":
        return LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5,
                                  class_weight=model["class_weight"], max_iter=model["max_iter"],
                                  tol=model["tol"], random_state=seed)
    if kind == "pam":
        return NearestCentroid(priors=model["priors"])
    if kind == "rf":
        return RandomForestClassifier(n_estimators=model["n_estimators"], class_weight=model["class_weight"],
                                      random_state=seed, n_jobs=1)
    if kind == "knn":
        return KNeighborsClassifier(weights=model["weights"])
    raise ValueError(f"Unknown model type: {kind}")


def build_pipeline(spec, config):
    """Every fitted stage sits inside one pipeline, so each training fold refits all of them."""
    filters, seed = config["filters"], config["seed"]
    steps = [("log", FunctionTransformer(log_expression, validate=True))]
    expressed = dict(log2_threshold=filters["low_expression_log2"], min_samples=filters["low_expression_min_samples"])
    stage = spec["filter"]
    if stage == "F0":
        steps.append(("filter", VarianceThreshold(0.0)))
    elif stage == "F1":
        steps.append(("filter", ExpressionFilter(**expressed)))
    elif stage == "F2":
        steps.append(("filter", ExpressionFilter(**expressed, top_mad=filters["mad_top_n"])))
    elif stage != "none":
        raise ValueError(f"Unknown filter: {stage}")
    if spec["scaler"] == "standard":
        steps.append(("scale", StandardScaler()))
    elif spec["scaler"] != "none":
        raise ValueError(f"Unknown scaler: {spec['scaler']}")
    if spec["select"] == "anova":
        steps.append(("select", SelectKBest(f_classif)))
    elif spec["select"] != "none":
        raise ValueError(f"Unknown selection: {spec['select']}")
    if spec.get("smote"):
        # After selection, as Blagus & Lusa recommend; samplers only act during fit.
        steps.append(("smote", SMOTE(k_neighbors=config["smote_k_neighbors"], random_state=seed)))
    steps.append(("model", build_model(spec["model"], seed)))
    pipeline = Pipeline(steps)
    pipeline.set_params(**spec.get("fixed", {}))
    return pipeline


def parameters(spec, candidate):
    """Translate declared grid names to pipeline names; PriorShift holds C one level deeper."""
    if spec["model"]["type"] == "lr_l2_prior":
        return {("model__estimator__C" if key == "model__C" else key): value for key, value in candidate.items()}
    return dict(candidate)


def fits_per_repeat(spec, inner_folds=4, outer_folds=5):
    return outer_folds * (inner_folds * len(candidates(spec)) + 1)
