"""Build a fresh pipeline for each training fold."""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, StandardScaler


def log_expression(values):
    """Compress expression values; this fixed transform learns no parameters."""
    return np.log2(values + 1)


def build_pipeline(configuration, settings):
    scaler = configuration["scaler"]
    if scaler not in {"standard", "minmax"}:
        raise ValueError(f"Unknown scaler: {scaler}")
    steps = [
        ("log", FunctionTransformer(log_expression, validate=True)),
        ("variance", VarianceThreshold(settings["preprocessing"]["variance_threshold"])),
        ("scale", StandardScaler(with_mean=True, with_std=True) if scaler == "standard"
         else MinMaxScaler(feature_range=(0, 1), clip=False)),
    ]
    reduction, k = configuration["reduction"], configuration["k"]
    if reduction == "anova":
        steps.append(("reduction", SelectKBest(score_func=f_classif, k=k)))
    elif reduction == "pca":
        steps.append(("reduction", PCA(n_components=k, **settings["pca"])))
    elif reduction != "none":
        raise ValueError(f"Unknown reduction: {reduction}")
    order = configuration.get("order", "scale_pca")
    if order not in {"scale_pca", "pca_scale"}:
        raise ValueError(f"Unknown preprocessing order: {order}")
    if order == "pca_scale":
        if reduction != "pca":
            raise ValueError("PCA-before-scaling requires PCA reduction")
        steps = [steps[0], steps[1], steps[3], steps[2]]
    steps.append(("model", SVC(kernel=configuration["kernel"], **settings["model"])))
    return Pipeline(steps)


def feature_details(pipeline, features):
    """Record the actual training-fold features, rather than a global list."""
    retained = np.asarray(features)[pipeline.named_steps["variance"].get_support()]
    details = {"retained_after_variance": retained.tolist()}
    reducer = pipeline.named_steps.get("reduction")
    if isinstance(reducer, SelectKBest):
        details["selected_genes"] = retained[reducer.get_support()].tolist()
    elif isinstance(reducer, PCA):
        details["pca"] = {
            "n_components": int(reducer.n_components_),
            "explained_variance_ratio": reducer.explained_variance_ratio_.tolist(),
            "total_explained_variance_ratio": float(reducer.explained_variance_ratio_.sum()),
        }
    return details
