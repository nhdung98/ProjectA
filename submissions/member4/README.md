# Member 4 — Vy: StandardScaler + PCA + SVM

Status: **six complete runs independently validated; pending peer review and team-leader acceptance**.

Training commit: `2d14aa920a8f4dec5fe0fbe364a43c17222e294d` (the agreed experiment commit). This results branch adds reporting artifacts only; it does not change training code, data, grids, seeds, or cross-validation assignments.

- [Experiment report](member4_report.md)
- [Summary: components, kernels, Macro-F1, balanced accuracy and runtime](member4_summary.csv)
- [Per-subtype precision, recall and F1](member4_subtypes.csv)
- [Repeat scores](repeat_scores.csv)
- [Confusion matrix counts](confusion_matrices.csv)
- [PCA/kernel comparison](charts/pca_kernel_comparison.png)
- [Run and archive register](run_register.json)
- [Command logs](evidence/logs/)

Each run has 15 complete outer folds and 762 held-out predictions. All original warning logs are empty. All 19 existing unit tests and both smoke tests passed. Reported SD is the sample SD across three complete repeat scores, not a confidence interval. These are Member 4 results only; the accepted 24-configuration team comparison is not yet supplied here.

## Evidence and review

`evidence/runs/` contains compact review excerpts: settings, provenance, metrics, predictions, search results, warning logs, validation reports and submission notes. **These excerpts are not complete submission folders**: the large `feature_details.json` files are retained in the original full-run archives. The original per-file hashes and archive SHA-256 values are recorded in `run_register.json`.

Full run folders remain under ignored `results/svm/<configuration>/<run-id>/`. Six complete ZIP archives are retained separately for the team's normal handoff, as required by the repository. Reviewers should obtain those archives, extract them without overwriting existing evidence, and run the original independent validator using the agreed training commit and pinned environment.

Paths in these public report copies are relative to the repository root. Interpreter paths in displayed commands use `.venv/bin/python`. The `run_folder` field in public validation copies and the displayed logs was normalized for portability. Original run outputs, validation reports, command logs and archives were not edited. Metric values, predictions, settings, selected parameters and run IDs are unchanged.

## macOS preparation note

Preparation on macOS produced LF line endings while the shared manifests describe CRLF bytes. A read-only CRLF conversion was first proven to match the existing reviewed checksum exactly. The LF file was backed up and only the prepared TSV serialization was restored. Source values, labels, patient identities, source hashes and exact seed-derived outer/inner assignments passed checks. No split manifest was regenerated and no experiment setting was changed.

The supplied helper calls preparation again and can reintroduce this platform-specific checksum mismatch. Official runs were therefore orchestrated outside the reviewed clone using the original runner and validator, without repeating preparation after canonical-byte restoration. This is an operational serialization correction, not a scientific-method change.

## Reproduction

Use a separate clean checkout of the training commit and Python 3.12 with `requirements-experiments.txt`. Verify preparation, the existing split checks and unit tests before fitting. Inspect the original complete archives and validation evidence before deciding whether a peer reproduction is required; do not silently select a best-scoring rerun.

For a complete extracted run (not a public excerpt):

```sh
.venv/bin/python -m src.experiments.validate_svm results/svm/CONFIGURATION/RUN_ID --report results/svm/CONFIGURATION/RUN_ID/validation.json
```
