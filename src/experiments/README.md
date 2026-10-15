# Experiment code map

Run all commands from the repository root. Shared code stays in this package so existing imports and last week's rerun commands keep working.

| Role | Files |
| --- | --- |
| Current PCA-order command | `pca_order.py` (CLI entry point), `pca_order_csv.py` (runner and collector) |
| Shared data and environment checks | `common.py` |
| Shared preprocessing and models | `pipeline.py` |
| Shared outer validation and metrics | `validation.py`, `metrics.py` |
| Earlier SVM runner and shared nested search | `svm.py` |
| Earlier SVM evidence validation and collection | `validate_svm.py`, `compare_svm.py` |

Experiment settings live in `configs/`; scaler choice and pipeline order belong to each configuration. Learned preprocessing is fitted within training folds. The current runner reuses candidate generation, inner split validation and GridSearchCV from `svm.py`; do not delete that module when archiving earlier results.

The current command is `python -m src.experiments.pca_order`. For last week's commands, use [the archive guide](../../archive/week01/README.md).
