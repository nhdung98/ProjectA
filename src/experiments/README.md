# Experiment code map

Run all commands from the repository root. Shared code stays in this package so existing imports and last week's rerun commands keep working.

| Role | Files |
| --- | --- |
| Shared data and environment checks | `common.py` |
| Shared preprocessing and models | `pipeline.py` |
| Shared outer validation and metrics | `validation.py`, `metrics.py` |
| Earlier SVM runner and shared nested search | `svm.py` |
| Earlier SVM evidence validation and collection | `validate_svm.py`, `compare_svm.py` |

Experiment settings live in `configs/`; scaler choice and pipeline order belong to each configuration. Learned preprocessing is fitted within training folds. `svm.py` also holds the shared inner-split checks; do not delete it when archiving earlier results. Protocol 3.0 code lives in `src/p3/` and imports these modules without changing them, so the hashed protocol 2.0 files stay unchanged.

For protocol 2.0 commands, use [the archive guide](../../archive/week01/README.md). The PCA-order runner is kept at the commit named in [the week 2 archive](../../archive/week02/README.md).
