# First Round Results

All eight configurations and the dummy reference passed validation.

These are leader-run experiments produced with the shared runner, not submissions attributed to individual members.

Code snapshot: `37f01cd2bb234ed941e3b76eff08e6b7558958ce`. Protocol: 1.1. All runs recorded a clean working tree and used identical data and saved splits.

## Overall Scores

| Configuration | Macro-F1 mean ± SD | Balanced accuracy mean ± SD | Macro-F1 change from baseline |
| --- | ---: | ---: | ---: |
| LR-STD-NONE | 0.727 ± 0.018 | 0.743 ± 0.014 | +0.000 |
| LR-MM-NONE | 0.742 ± 0.015 | 0.733 ± 0.012 | +0.014 |
| LR-STD-ANOVA-50 | 0.689 ± 0.022 | 0.683 ± 0.010 | -0.038 |
| LR-STD-ANOVA-100 | 0.752 ± 0.026 | 0.741 ± 0.021 | +0.024 |
| LR-STD-ANOVA-150 | 0.765 ± 0.010 | 0.749 ± 0.013 | +0.038 |
| LR-STD-PCA-50 | 0.687 ± 0.025 | 0.695 ± 0.028 | -0.040 |
| LR-STD-PCA-100 | 0.754 ± 0.018 | 0.753 ± 0.015 | +0.027 |
| LR-STD-PCA-150 | 0.738 ± 0.005 | 0.752 ± 0.008 | +0.011 |
| DUMMY-MOST-FREQUENT | 0.097 ± 0.000 | 0.167 ± 0.000 | -0.631 |

SD is the sample standard deviation across three repeats. It describes split variation, not a confidence interval. The dummy is a reference and is excluded from ranking.

## Repeat Scores

| Configuration | Repeat 1 | Repeat 2 | Repeat 3 |
| --- | ---: | ---: | ---: |
| LR-STD-NONE | 0.745 | 0.708 | 0.729 |
| LR-MM-NONE | 0.738 | 0.729 | 0.759 |
| LR-STD-ANOVA-50 | 0.673 | 0.715 | 0.680 |
| LR-STD-ANOVA-100 | 0.724 | 0.757 | 0.775 |
| LR-STD-ANOVA-150 | 0.756 | 0.763 | 0.775 |
| LR-STD-PCA-50 | 0.663 | 0.687 | 0.712 |
| LR-STD-PCA-100 | 0.750 | 0.738 | 0.774 |
| LR-STD-PCA-150 | 0.736 | 0.734 | 0.744 |
| DUMMY-MOST-FREQUENT | 0.097 | 0.097 | 0.097 |

## Subtype Results

The table shows mean F1 across repeats. Supports are distinct patients per repeat; they are not multiplied by three.

| Configuration | LMS (n=104) | DDLPS (n=57) | UPS (n=49) | MFS (n=25) | SS (n=10) | MPNST (n=9) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LR-STD-NONE | 0.866 | 0.805 | 0.670 | 0.484 | 0.893 | 0.646 |
| LR-MM-NONE | 0.890 | 0.831 | 0.700 | 0.445 | 0.933 | 0.652 |
| LR-STD-ANOVA-50 | 0.867 | 0.819 | 0.596 | 0.420 | 0.982 | 0.451 |
| LR-STD-ANOVA-100 | 0.897 | 0.826 | 0.641 | 0.450 | 0.945 | 0.752 |
| LR-STD-ANOVA-150 | 0.893 | 0.842 | 0.651 | 0.476 | 0.965 | 0.763 |
| LR-STD-PCA-50 | 0.859 | 0.784 | 0.627 | 0.470 | 0.876 | 0.508 |
| LR-STD-PCA-100 | 0.876 | 0.812 | 0.675 | 0.515 | 0.967 | 0.681 |
| LR-STD-PCA-150 | 0.865 | 0.815 | 0.683 | 0.504 | 0.906 | 0.656 |
| DUMMY-MOST-FREQUENT | 0.581 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

![Macro-F1 across repeats](plots/repeat_scores.png)

![Subtype F1 scores](plots/subtype_scores.png)

## Interpretation

LR-STD-ANOVA-150 has the highest mean macro-F1 (0.765), compared with 0.727 for the standard-scaled baseline. Its score is higher than the baseline in 3 of three repeats.

For that configuration, MFS has the lowest mean subtype F1 (0.476). Overall scores must be read alongside the subtype table and confusion matrices.

MPNST has only nine patients and SS has ten. Their scores can change substantially when a few predictions change. Inspect per-repeat precision, recall, and F1 rather than treating a small overall difference as settled evidence.

This is an internal comparison on the same 254 patients. The top score was selected from this comparison; it is not an independently validated estimate for the selected model. Further tuning requires validation inside the training data. These results do not establish clinical diagnostic performance.

Runtime is recorded separately from predictive scores. All runs used one numerical thread on the same computer; timing still reflects local execution conditions.

## Complete Evidence

- [Overall scores and runtime](overall_scores.csv)
- [Scores and baseline differences for every repeat](repeat_scores.csv)
- [Precision, recall, F1, and support for every subtype and repeat](subtype_repeat_scores.csv)
- [Subtype summary](subtype_summary.csv)
- [All 27 confusion matrices in long form](confusion_matrices.csv)
- [Selected run IDs and code commit](selection.json)
- [Validation decisions and input checksums](comparison_manifest.json)

The full run folders preserve settings, held-out predictions, feature details, warnings, and per-split runtime. They are ignored by Git; the selected summary tables and figures can be shared with the report.
