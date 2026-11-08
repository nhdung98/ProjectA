# Round A team comparison

All 14 executable entries (13 proposed pipelines, including two Dummy variants) completed five outer-training searches. No outer-test predictions were generated.

**These are selected inner-CV scores, not independent generalization estimates.** Each fold contributes its best candidate mean across four inner validation folds. The SD below describes variation between those five selected scores; it is not a confidence interval. Search spaces differ, so the ordering is descriptive and must not be used to eliminate pipelines or claim superiority.

| Pipeline | Mean winning inner macro-F1 | SD | Wall minutes | Warnings |
| --- | ---: | ---: | ---: | ---: |
| P09 LR-L2-ANOVA | 0.7606 | 0.0213 | 1.59 | 0 |
| P04 SVM-BAL-K | 0.7604 | 0.0275 | 2.24 | 0 |
| P10 LR-L2-ANOVA-SMOTE | 0.7567 | 0.0250 | 4.26 | 0 |
| P03 SVM-BAL | 0.7451 | 0.0270 | 0.59 | 0 |
| P07 LR-EN-BAL | 0.7444 | 0.0133 | 107.08 | 0 |
| P02 R1-REF | 0.7398 | 0.0396 | 0.60 | 0 |
| P13 KNN | 0.7305 | 0.0311 | 0.52 | 0 |
| P06 LR-L2-BAL | 0.7236 | 0.0249 | 0.70 | 0 |
| P08 LR-L2-PRIOR | 0.7201 | 0.0219 | 1.54 | 0 |
| P05 SVM-BAL-MAD | 0.7039 | 0.0256 | 0.72 | 0 |
| P12 RF-BAL | 0.6590 | 0.0340 | 2.99 | 0 |
| P11 PAM | 0.6371 | 0.0075 | 0.38 | 0 |
| P01-ST DUMMY stratified | 0.1521 | 0.0083 | 0.06 | 0 |
| P01-MF DUMMY most_frequent | 0.0968 | 0.0004 | 0.06 | 0 |

## Descriptive observations

- P09 and P04 have the highest mean selected inner scores, approximately 0.761. This is not a final winner declaration.
- P10 has the highest single selected inner score, but exceeds matched P09 in only two of five folds. These results do not establish a benefit from SMOTE.
- P07 is the practical runtime bottleneck, approximately 107 minutes. Machines and parallel settings differ; this is not a controlled efficiency benchmark.
- P02 reproduces archived inner scores to numerical precision; see screening.md.
- P04, P05, P06, P09 and P10 trigger the declared boundary-screening rule. Resolve and document those choices before freezing Round B. No grids were changed by this comparison.

## Evidence and next steps

Original ZIPs are authoritative. Member 3 also committed loose files whose newline conversion changes a checksum; this report extracts bytes directly from ZIPs. sources.csv identifies every selected archive and recorded training commit. P07 was submitted by Kien under the member-2 assignment; P06/P08 were submitted separately. Different recorded commits contain identical training/config/split content as checked in the preceding audit.

Review screening.md, decide any one-time grid extensions, rerun affected Round A pipelines if required, then commit and tag the final configuration. Run all Round B repeats separately. No Round B performance or META-SELECT generalization result is available yet.

Reproduce with `python scripts/compare_round_a_submissions.py`. This script reads saved evidence only and performs no model fitting.
