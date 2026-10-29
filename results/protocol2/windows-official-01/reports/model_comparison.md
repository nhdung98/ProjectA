# Protocol 2.0 descriptive model comparison

Validated configurations: 24/24. Human peer review: pending.

Reference: SVM-STD-ANOVA-150-LINEAR. Available in this batch.

Macro-F1 is primary. SD is sample SD across three complete repeat scores. Repeats reuse the same 254 patients and overlapping training sets; folds and repeats are not independent observations. SD is not a confidence interval. No t-tests, significance claims or preregistered statistical tests are performed.

This is an exploratory comparison. Selecting a winner from these outer scores does not give an unbiased estimate of the selected model. Read subtype and confusion tables, especially MFS/UPS errors and SS/MPNST with only 10/9 patients. Keep this round separate from later Protocol 3.0 analyses.

| Configuration | Macro-F1 mean | SD | Balanced accuracy |
| --- | ---: | ---: | ---: |
| SVM-STD-ANOVA-150-LINEAR | 0.771658 | 0.002694 | 0.767179 |
| SVM-STD-ANOVA-150-RBF | 0.768492 | 0.019437 | 0.764024 |
| SVM-STD-ANOVA-100-RBF | 0.765283 | 0.025035 | 0.768495 |
| SVM-MM-ANOVA-150-RBF | 0.763746 | 0.012927 | 0.760486 |
| SVM-MM-PCA-150-RBF | 0.736047 | 0.031575 | 0.729348 |
| SVM-MM-ANOVA-150-LINEAR | 0.735148 | 0.033162 | 0.734212 |
| SVM-STD-ANOVA-100-LINEAR | 0.734654 | 0.007309 | 0.742430 |
| SVM-STD-ANOVA-50-RBF | 0.734098 | 0.042160 | 0.729641 |
| SVM-MM-ANOVA-100-RBF | 0.728061 | 0.018799 | 0.732845 |
| SVM-MM-PCA-50-RBF | 0.727128 | 0.018462 | 0.711033 |
| SVM-MM-PCA-150-LINEAR | 0.726222 | 0.012600 | 0.710990 |
| SVM-MM-PCA-100-RBF | 0.724002 | 0.026195 | 0.715912 |
| SVM-STD-PCA-150-LINEAR | 0.722685 | 0.028622 | 0.704684 |
| SVM-MM-ANOVA-100-LINEAR | 0.720552 | 0.007109 | 0.722458 |
| SVM-STD-PCA-100-LINEAR | 0.714102 | 0.025328 | 0.697245 |
| SVM-STD-PCA-150-RBF | 0.713993 | 0.014522 | 0.699421 |
| SVM-STD-PCA-50-RBF | 0.708593 | 0.057305 | 0.694345 |
| SVM-STD-PCA-100-RBF | 0.708412 | 0.023871 | 0.695025 |
| SVM-MM-PCA-100-LINEAR | 0.707688 | 0.028226 | 0.685829 |
| SVM-MM-PCA-50-LINEAR | 0.705892 | 0.029415 | 0.689770 |
| SVM-MM-ANOVA-50-RBF | 0.703986 | 0.058068 | 0.702001 |
| SVM-STD-PCA-50-LINEAR | 0.703721 | 0.032404 | 0.691183 |
| SVM-STD-ANOVA-50-LINEAR | 0.692363 | 0.045754 | 0.689518 |
| SVM-MM-ANOVA-50-LINEAR | 0.687697 | 0.044290 | 0.686114 |

See subtype_analysis.csv, confusion_matrices.csv and repeat_scores.csv. Runtime reflects this machine and local execution conditions.

evidence_bundle.zip is for external review and contains aggregate evidence only. It omits patient-level predictions, fold checkpoints and run artifacts. The local runs/ tree holds all nine original artifacts. An explicit team export includes original Protocol-required identifiers and must stay in the approved team channel.
