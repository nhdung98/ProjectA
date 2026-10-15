# Member 2 — new reproduction results

Six configurations were rerun at the leader's request using the original training commit and unchanged saved splits. These are reproduction results, not the original Member 2 submission.

All six completed 15 outer evaluations and independent output checks, with 762 predictions per configuration and empty warning logs.

| Configuration | Macro-F1 mean +/- SD | Balanced accuracy | Original reported summary matches | Run |
| --- | ---: | ---: | --- | --- |
| SVM-STD-ANOVA-50-LINEAR | 0.692 +/- 0.046 | 0.690 | True | [Files](runs/SVM-STD-ANOVA-50-LINEAR/20261013T022440Z-e88d439a) |
| SVM-STD-ANOVA-50-RBF | 0.734 +/- 0.042 | 0.730 | True | [Files](runs/SVM-STD-ANOVA-50-RBF/20261013T024858Z-4fc499d6) |
| SVM-STD-ANOVA-100-LINEAR | 0.735 +/- 0.007 | 0.742 | True | [Files](runs/SVM-STD-ANOVA-100-LINEAR/20261013T031244Z-dc09734a) |
| SVM-STD-ANOVA-100-RBF | 0.765 +/- 0.025 | 0.768 | True | [Files](runs/SVM-STD-ANOVA-100-RBF/20261013T032602Z-a1fd2c59) |
| SVM-STD-ANOVA-150-LINEAR | 0.772 +/- 0.003 | 0.767 | True | [Files](runs/SVM-STD-ANOVA-150-LINEAR/20261013T034657Z-3614ed00) |
| SVM-STD-ANOVA-150-RBF | 0.768 +/- 0.019 | 0.764 | True | [Files](runs/SVM-STD-ANOVA-150-RBF/20261013T035519Z-aac8660a) |

The original rounded summaries can be compared with these new scores. The original predictions are unavailable, so agreement at summary precision does not establish identical original predictions.

Read [run provenance and audit evidence](reproduction_manifest.json), [subtype summaries](subtype_summary.csv), [repeat scores](repeat_scores.csv), [confusion matrices](confusion_matrices.csv), and [selected parameters](selected_parameters.csv).
