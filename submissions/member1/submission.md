# Member 1 submission index

- Submitter: Truong Nam Hung - 105556375 (Member 1)
- Configurations: six assigned MinMax + ANOVA configurations
- Code commit recorded by all six runs: `2d14aa920a8f4dec5fe0fbe364a43c17222e294d`
- Working tree: recorded clean in each run manifest
- Protocol: 2.0 / SVM experiment
- Validation status: all six runs passed; each includes 15 outer folds and 762 predictions
- Total tuning/refit/prediction runtime: 1,929.22 seconds (32.15 minutes)
- Warnings or failures: none; all six `warnings.log` files are empty
- Submission location: `submissions/member1/runs/` (plain folders; no ZIP archives)
- Run/validation logs: [logs/](logs/member1_20261012_072552_50-100-150-LINEAR+RBF/)

| Configuration | Run ID | Macro-F1 (mean ± SD) | Balanced accuracy (mean ± SD) | Validation | Run folder |
| --- | --- | --- | --- | --- | --- |
| `SVM-MM-ANOVA-50-LINEAR` | `20261012T072552Z-3fc22e4b` | 0.688 ± 0.044 | 0.686 ± 0.040 | passed | [Run](runs/SVM-MM-ANOVA-50-LINEAR/20261012T072552Z-3fc22e4b) |
| `SVM-MM-ANOVA-50-RBF` | `20261012T072943Z-02717c69` | 0.704 ± 0.058 | 0.702 ± 0.066 | passed | [Run](runs/SVM-MM-ANOVA-50-RBF/20261012T072943Z-02717c69) |
| `SVM-MM-ANOVA-100-LINEAR` | `20261012T073715Z-76fbc2fb` | 0.721 ± 0.007 | 0.722 ± 0.001 | passed | [Run](runs/SVM-MM-ANOVA-100-LINEAR/20261012T073715Z-76fbc2fb) |
| `SVM-MM-ANOVA-100-RBF` | `20261012T073935Z-d8df65a0` | 0.728 ± 0.019 | 0.733 ± 0.023 | passed | [Run](runs/SVM-MM-ANOVA-100-RBF/20261012T073935Z-d8df65a0) |
| `SVM-MM-ANOVA-150-LINEAR` | `20261012T074535Z-55c37c7c` | 0.735 ± 0.033 | 0.734 ± 0.029 | passed | [Run](runs/SVM-MM-ANOVA-150-LINEAR/20261012T074535Z-55c37c7c) |
| `SVM-MM-ANOVA-150-RBF` | `20261012T074815Z-2c7cd463` | 0.764 ± 0.013 | 0.760 ± 0.011 | passed | [Run](runs/SVM-MM-ANOVA-150-RBF/20261012T074815Z-2c7cd463) |

Each run folder includes the files required by the [submission requirements](../../docs/submission_requirements.md), plus its saved validation report and individual submission record.
