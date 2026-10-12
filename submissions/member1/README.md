# Member 1 – SVM submissions (MinMax + ANOVA)

- Submitter: Member 1
- Pushed: 2026-10-12
- Code commit used for validation: `2d14aa920a8f4dec5fe0fbe364a43c17222e294d` (clean working tree)
- Protocol: 2.0 / SVM experiment
- Validation report status: Passed (`19/19` unit tests)
- Total tuning/refit/prediction runtime: Not yet recorded for the six official configurations
- Warnings or failures: None in the local validation suite
- Archive location: `submissions/member1/`
- Notes or deviations: This is the submission scaffold for the six assigned Member 1 run records. The full official runs are not yet present in this workspace; the folder is prepared to receive the actual output artifacts.

<<<<<<< Updated upstream
| Configuration | Kernel | Run status |
| --- | --- | --- |
| `SVM-MM-ANOVA-50-LINEAR` | Linear | assigned |
| `SVM-MM-ANOVA-50-RBF` | RBF | assigned |
| `SVM-MM-ANOVA-100-LINEAR` | Linear | assigned |
| `SVM-MM-ANOVA-100-RBF` | RBF | assigned |
| `SVM-MM-ANOVA-150-LINEAR` | Linear | assigned |
| `SVM-MM-ANOVA-150-RBF` | RBF | assigned |

This folder follows the general submission layout and keeps the validation evidence required before official SVM submission output files are added.
=======
| Configuration | Run ID | Validation | Macro-F1 (mean ± SD, 3 repeats) | Balanced accuracy (mean ± SD) | Runtime (seconds) | Submission folder |
| --- | --- | --- | --- | --- | ---: | --- |
| `SVM-MM-ANOVA-50-LINEAR` | `20261012T072552Z-3fc22e4b` | passed | 0.688 ± 0.044 | 0.686 ± 0.040 | 229.41 | [Run folder](runs/SVM-MM-ANOVA-50-LINEAR/20261012T072552Z-3fc22e4b) |
| `SVM-MM-ANOVA-50-RBF` | `20261012T072943Z-02717c69` | passed | 0.704 ± 0.058 | 0.702 ± 0.066 | 450.40 | [Run folder](runs/SVM-MM-ANOVA-50-RBF/20261012T072943Z-02717c69) |
| `SVM-MM-ANOVA-100-LINEAR` | `20261012T073715Z-76fbc2fb` | passed | 0.721 ± 0.007 | 0.722 ± 0.001 | 139.02 | [Run folder](runs/SVM-MM-ANOVA-100-LINEAR/20261012T073715Z-76fbc2fb) |
| `SVM-MM-ANOVA-100-RBF` | `20261012T073935Z-d8df65a0` | passed | 0.728 ± 0.019 | 0.733 ± 0.023 | 358.46 | [Run folder](runs/SVM-MM-ANOVA-100-RBF/20261012T073935Z-d8df65a0) |
| `SVM-MM-ANOVA-150-LINEAR` | `20261012T074535Z-55c37c7c` | passed | 0.735 ± 0.033 | 0.734 ± 0.029 | 157.87 | [Run folder](runs/SVM-MM-ANOVA-150-LINEAR/20261012T074535Z-55c37c7c) |
| `SVM-MM-ANOVA-150-RBF` | `20261012T074815Z-2c7cd463` | passed | 0.764 ± 0.013 | 0.760 ± 0.011 | 594.06 | [Run folder](runs/SVM-MM-ANOVA-150-RBF/20261012T074815Z-2c7cd463) |

Each folder contains one complete run, its independent `validation.json`, and a configuration-specific `submission.md` based on the team template. Readable run and validation summaries are in [logs/](logs/member1_20261012_072552_50-100-150-LINEAR+RBF/), following the Member 3 log naming convention. See [the submission index](submission.md) and [submission requirements](../../docs/submission_requirements.md).
>>>>>>> Stashed changes
