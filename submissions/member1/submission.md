# Experiment submission

<<<<<<< Updated upstream
- Submitter: Member 1
- Configuration ID: `SVM-MM-ANOVA-50-LINEAR`, `SVM-MM-ANOVA-50-RBF`, `SVM-MM-ANOVA-100-LINEAR`, `SVM-MM-ANOVA-100-RBF`, `SVM-MM-ANOVA-150-LINEAR`, `SVM-MM-ANOVA-150-RBF`
- Run ID: pending official run creation
=======
- Submitter: Truong Nam Hung - 105556375 [Member 1]
- Configuration IDs: six assigned MinMax + ANOVA configurations
- Run IDs: `20261012T072552Z-3fc22e4b`, `20261012T072943Z-02717c69`, `20261012T073715Z-76fbc2fb`, `20261012T073935Z-d8df65a0`, `20261012T074535Z-55c37c7c`, `20261012T074815Z-2c7cd463`
>>>>>>> Stashed changes
- Code commit: `2d14aa920a8f4dec5fe0fbe364a43c17222e294d`
- Recorded working tree clean: Yes
- Protocol: 2.0 / SVM experiment
<<<<<<< Updated upstream
- Validation report status: Passed (`19/19` unit tests)
- Total tuning/refit/prediction runtime: not yet recorded
- Warnings or failures: None in local validation
- Archive location: `submissions/member1/`
- Notes or deviations: This submission scaffold follows the official template and is ready to receive the actual run artifacts once Member 1 output folders are generated.

Include all files listed in [submission requirements](../../docs/submission_requirements.md).
=======
- Validation report status: Passed for all six runs (15 outer folds and 762 predictions per run)
- Total tuning/refit/prediction runtime: 1,929.22 seconds (32.15 minutes)
- Warnings or failures: None; all six `warnings.log` files are empty
- Submission location: `submissions/member1/runs/` (one folder per configuration and run ID)
- Notes or deviations: Each run folder includes the required run evidence, `validation.json`, and a configuration-specific `submission.md` based on the team template. Readable run/validation summaries are in [logs/](logs/member1_20261012_072552_50-100-150-LINEAR+RBF/).

| Configuration | Run ID | Validation | Run folder |
| --- | --- | --- | --- |
| `SVM-MM-ANOVA-50-LINEAR` | `20261012T072552Z-3fc22e4b` | passed | [Run folder](runs/SVM-MM-ANOVA-50-LINEAR/20261012T072552Z-3fc22e4b) |
| `SVM-MM-ANOVA-50-RBF` | `20261012T072943Z-02717c69` | passed | [Run folder](runs/SVM-MM-ANOVA-50-RBF/20261012T072943Z-02717c69) |
| `SVM-MM-ANOVA-100-LINEAR` | `20261012T073715Z-76fbc2fb` | passed | [Run folder](runs/SVM-MM-ANOVA-100-LINEAR/20261012T073715Z-76fbc2fb) |
| `SVM-MM-ANOVA-100-RBF` | `20261012T073935Z-d8df65a0` | passed | [Run folder](runs/SVM-MM-ANOVA-100-RBF/20261012T073935Z-d8df65a0) |
| `SVM-MM-ANOVA-150-LINEAR` | `20261012T074535Z-55c37c7c` | passed | [Run folder](runs/SVM-MM-ANOVA-150-LINEAR/20261012T074535Z-55c37c7c) |
| `SVM-MM-ANOVA-150-RBF` | `20261012T074815Z-2c7cd463` | passed | [Run folder](runs/SVM-MM-ANOVA-150-RBF/20261012T074815Z-2c7cd463) |

Use the six linked run folders as the per-configuration submissions. See [the official submission requirements](../../docs/submission_requirements.md).
>>>>>>> Stashed changes
