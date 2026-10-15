# Comparison with Member 2 reproduction results

Member 2's six missing result folders were regenerated at the leader's request from the original clean training commit. This comparison uses those new results alongside the previously checked Member 1 and Member 3 folders and Member 4 excerpts. It does not substitute new run IDs for the original Member 2 run IDs.

All 24 performance scores in this table were checked against available predictions. Member 4's feature-details audit still requires its original archives. Training-code equivalence was checked, but the formal comparison tool's exact-commit requirement has not been changed. Reproduction consistency is not validation on an external patient cohort.

| Configuration | Macro-F1 mean +/- SD | Balanced accuracy | Evidence |
| --- | ---: | ---: | --- |
| SVM-STD-ANOVA-150-LINEAR | 0.772 +/- 0.003 | 0.767 | leader_reproduction_complete_validated |
| SVM-STD-ANOVA-150-RBF | 0.768 +/- 0.019 | 0.764 | leader_reproduction_complete_validated |
| SVM-STD-ANOVA-100-RBF | 0.765 +/- 0.025 | 0.768 | leader_reproduction_complete_validated |
| SVM-MM-ANOVA-150-RBF | 0.764 +/- 0.013 | 0.760 | complete_evidence_checks_passed |
| SVM-MM-PCA-150-RBF | 0.736 +/- 0.032 | 0.729 | complete_evidence_checks_passed |
| SVM-MM-ANOVA-150-LINEAR | 0.735 +/- 0.033 | 0.734 | complete_evidence_checks_passed |
| SVM-STD-ANOVA-100-LINEAR | 0.735 +/- 0.007 | 0.742 | leader_reproduction_complete_validated |
| SVM-STD-ANOVA-50-RBF | 0.734 +/- 0.042 | 0.730 | leader_reproduction_complete_validated |
| SVM-MM-ANOVA-100-RBF | 0.728 +/- 0.019 | 0.733 | complete_evidence_checks_passed |
| SVM-MM-PCA-50-RBF | 0.727 +/- 0.018 | 0.711 | complete_evidence_checks_passed |
| SVM-MM-PCA-150-LINEAR | 0.726 +/- 0.013 | 0.711 | complete_evidence_checks_passed |
| SVM-MM-PCA-100-RBF | 0.724 +/- 0.026 | 0.716 | complete_evidence_checks_passed |
| SVM-STD-PCA-150-LINEAR | 0.723 +/- 0.029 | 0.705 | available_content_checks_passed_incomplete_evidence |
| SVM-MM-ANOVA-100-LINEAR | 0.721 +/- 0.007 | 0.722 | complete_evidence_checks_passed |
| SVM-STD-PCA-100-LINEAR | 0.714 +/- 0.025 | 0.697 | available_content_checks_passed_incomplete_evidence |
| SVM-STD-PCA-150-RBF | 0.714 +/- 0.015 | 0.699 | available_content_checks_passed_incomplete_evidence |
| SVM-STD-PCA-50-RBF | 0.709 +/- 0.057 | 0.694 | available_content_checks_passed_incomplete_evidence |
| SVM-STD-PCA-100-RBF | 0.708 +/- 0.024 | 0.695 | available_content_checks_passed_incomplete_evidence |
| SVM-MM-PCA-100-LINEAR | 0.708 +/- 0.028 | 0.686 | complete_evidence_checks_passed |
| SVM-MM-PCA-50-LINEAR | 0.706 +/- 0.029 | 0.690 | complete_evidence_checks_passed |
| SVM-MM-ANOVA-50-RBF | 0.704 +/- 0.058 | 0.702 | complete_evidence_checks_passed |
| SVM-STD-PCA-50-LINEAR | 0.704 +/- 0.032 | 0.691 | available_content_checks_passed_incomplete_evidence |
| SVM-STD-ANOVA-50-LINEAR | 0.692 +/- 0.046 | 0.690 | leader_reproduction_complete_validated |
| SVM-MM-ANOVA-50-LINEAR | 0.688 +/- 0.044 | 0.686 | complete_evidence_checks_passed |

## Findings

The highest mean in this comparison is `SVM-STD-ANOVA-150-LINEAR`, macro-F1 0.772 with repeat sample SD 0.003. This is a candidate selected using the outer comparison, not independently validated final performance.

Repeated scores use the same 254 patients; SD is split variation, not a confidence interval. No claim of statistical significance is made. Runtime depends on hardware and should not be treated as a controlled cross-member benchmark.

Read [subtype summaries](subtype_summary.csv), [repeat scores](repeat_scores.csv), [confusion patterns](confusion_matrices.csv), and [selected parameters](selected_parameters.csv). The original Member 2 predictions were unavailable, so reproduction agreement is assessed against the original three-decimal summary only.

## Next checks

Obtain Member 4 feature details for complete preprocessing acceptance. Retain both original reported and reproduced Member 2 records, and document which run IDs are used for the final report. Agree how to handle scientifically identical training commits before using the formal comparison command. Add the proposed majority and no-reduction baselines before claiming the advantage of feature reduction.
