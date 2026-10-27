# Experiment code map

Run all commands from the repository root. Use `python -m src.experiments.workflow` for new Protocol 2.0 work. Shared scientific code remains compatible with legacy commands.

| Role | Files |
| --- | --- |
| Standardized Protocol 2.0 interface | `workflow.py` |
| Preflight and new-run validation gates | `workflow_checks.py` |
| Atomic fold checkpoints, resume, progress | `workflow_run.py` |
| Descriptive reports and privacy-aware export | `workflow_report.py` |
| Current PCA-order command | `pca_order.py` (CLI entry point), `pca_order_csv.py` (runner and collector) |
| Shared data and environment checks | `common.py` |
| Shared preprocessing and models | `pipeline.py` |
| Shared outer validation and metrics | `validation.py`, `metrics.py` |
| Earlier SVM runner and shared nested search | `svm.py` |
| Earlier SVM evidence validation and collection | `validate_svm.py`, `compare_svm.py` |

Experiment settings live in `configs/`; scaler choice and pipeline order belong to each configuration. Learned preprocessing is fitted within training folds. The current runner reuses candidate generation, inner split validation and GridSearchCV from `svm.py`; do not delete that module when archiving earlier results.

Read the [standardized workflow guide](../../docs/protocol2_workflow.md). PCA-order and legacy SVM commands remain separate workflows; new Protocol 2.0 batches never import historical result folders.
