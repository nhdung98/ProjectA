# Combining SVM experiment results

Choose exactly one accepted run for each of the 24 configurations before ranking scores. Record actual submitters and review decisions in [the register](submission_register.csv). Do not choose a best-scoring rerun silently.

Copy [the SVM selection template](templates/svm_comparison_selection.json) to `results/svm/selection.json`. Fill in the agreed code commit and all run paths. All runs must use that same clean commit and pass the independent validator.

```powershell
python -m src.experiments.compare_svm results/svm/selection.json --output results/svm/comparison
```

The destination must be new. The command verifies all 24 runs before writing overall, repeat, subtype, confusion-matrix, and selected-parameter tables plus a report and checksums.

Compare linear versus RBF for the same scaler, method, and size. Compare feature sizes within each branch and scaling for otherwise matching choices. Read macro-F1 and balanced accuracy alongside every subtype's recall/F1, all three repeats, and confusion patterns. Check selected C/gamma values and runtime. Runtime includes tuning and refitting and depends on the machine.

MPNST has nine patients and SS has ten. Repeats reuse these patients; their standard deviations are not confidence intervals. A winner selected from the outer comparison is a follow-up candidate, not independently validated final performance. Any new tuning needs a separately recorded plan.

Full outputs stay under ignored `results/svm/`; publish accepted summaries under `reports/svm/` only after review.
