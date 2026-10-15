# Evidence snapshot for the initial experiment summary

Results snapshot: 13 October 2026. Copied into the repository on 15 October 2026.

These files support the [methodology and findings summary](../../initial_experiments_summary.md). They preserve the reports and aggregate result tables used to write it. They do not declare formal acceptance of the SVM comparison or include full training archives.

| Snapshot file | Original source |
| --- | --- |
| `logistic_regression_report.md` | Repository-local `results/comparison/round1/report.md` |
| `svm_review.md` | Presentation workspace `team-review-20261013-with-member2-reproduction/review.md` |
| `scores.csv` | Same workspace comparison directory, same filename |
| `repeat_scores.csv` | Same workspace comparison directory, same filename |
| `subtype_summary.csv` | Same workspace comparison directory, same filename |
| `confusion_matrices.csv` | Same workspace comparison directory, same filename |

The presentation workspace is `C:/Users/LENOVO/OneDrive/Documents/ChatGPT/Project A`. This machine-specific location records provenance only; reading the summary does not require access to it.

The copied reports are unchanged. Their original relative links refer to their original report locations, including plots and artifacts not copied here. Use the links in the summary to navigate the included evidence.

## Interpretation

- Logistic Regression results are the recorded accepted leader-run shared-runner round, not member-attributed submissions.
- SVM Member 2 results are leader reproductions, compared with the original rounded summaries.
- SVM Member 4 scores were checked from predictions, but its complete feature-details audit remained outstanding.
- Three repeats reuse the same 254 patients. Repeat standard deviations measure split variation, not confidence intervals.
- Paired win counts in the summary are descriptive calculations from `scores.csv`, matching configurations on all factors except the factor being compared.
- Configuration and workload totals exclude duplicate reproduction runs, incomplete runs, and smoke tests.
- [Checksums](checksums.json) record SHA-256 values for the six copied evidence files.
