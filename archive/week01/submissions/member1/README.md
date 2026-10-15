# Member 1 – SVM submissions (MinMax + ANOVA)

- Submitter: Truong Nam Hung - 105556375 (Member 1)
- Code commit recorded by all six runs: `2d14aa920a8f4dec5fe0fbe364a43c17222e294d` (clean)
- Protocol: 2.0 / SVM experiment
- Validation: all six runs passed the independent validator
- Total tuning/refit/prediction runtime: 1,929.22 seconds (32.15 minutes)
- Warnings: empty for all six runs

| Configuration | Run ID | Validation | Macro-F1 (mean ± SD, 3 repeats) | Balanced accuracy (mean ± SD) | Runtime (seconds) | Run folder |
| --- | --- | --- | --- | --- | ---: | --- |
| `SVM-MM-ANOVA-50-LINEAR` | `20261012T072552Z-3fc22e4b` | passed | 0.688 ± 0.044 | 0.686 ± 0.040 | 229.41 | [Run](runs/SVM-MM-ANOVA-50-LINEAR/20261012T072552Z-3fc22e4b) |
| `SVM-MM-ANOVA-50-RBF` | `20261012T072943Z-02717c69` | passed | 0.704 ± 0.058 | 0.702 ± 0.066 | 450.40 | [Run](runs/SVM-MM-ANOVA-50-RBF/20261012T072943Z-02717c69) |
| `SVM-MM-ANOVA-100-LINEAR` | `20261012T073715Z-76fbc2fb` | passed | 0.721 ± 0.007 | 0.722 ± 0.001 | 139.02 | [Run](runs/SVM-MM-ANOVA-100-LINEAR/20261012T073715Z-76fbc2fb) |
| `SVM-MM-ANOVA-100-RBF` | `20261012T073935Z-d8df65a0` | passed | 0.728 ± 0.019 | 0.733 ± 0.023 | 358.46 | [Run](runs/SVM-MM-ANOVA-100-RBF/20261012T073935Z-d8df65a0) |
| `SVM-MM-ANOVA-150-LINEAR` | `20261012T074535Z-55c37c7c` | passed | 0.735 ± 0.033 | 0.734 ± 0.029 | 157.87 | [Run](runs/SVM-MM-ANOVA-150-LINEAR/20261012T074535Z-55c37c7c) |
| `SVM-MM-ANOVA-150-RBF` | `20261012T074815Z-2c7cd463` | passed | 0.764 ± 0.013 | 0.760 ± 0.011 | 594.06 | [Run](runs/SVM-MM-ANOVA-150-RBF/20261012T074815Z-2c7cd463) |

Each run folder contains the complete experiment evidence, its independent `validation.json`, and a configuration-specific `submission.md` following the team template. Readable run and validation summaries are in [logs/](logs/member1_20261012_072552_50-100-150-LINEAR+RBF/). See [submission requirements](../../docs/submission_requirements.md).
