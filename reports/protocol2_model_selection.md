# Protocol 2.0 model selection for Protocol 3.0 planning

**Status: provisional research recommendation, pending supervisor and independent peer review.** No Protocol 3.0 experimental design, implementation or clinical use is approved by this report.

## 1. Decision and evidence

Use **StandardScaler + ANOVA (150 genes) + Linear SVM** as the initial baseline candidate. Retain the matched RBF configuration and a matched PCA alternative; use scaling and feature-count controls to investigate why results differ. This recommendation combines observed performance, repeat variability and recorded computational cost. It does not establish that Linear SVM is statistically superior.

Evidence is the completed Windows batch `windows-official-01`: 254 patients, six subtypes, 24 configurations and 360 completed outer-fold fits. The frozen training release is `87f3e6ce1bb3e7fa53e513a22b480abb63998882`; the published results commit is `67ad3e764dadf13827421ab2d6f78f85809b42b3`. Evaluation uses three repeats of five-fold outer CV with four-fold inner tuning. Each complete repeat provides one held-out prediction per patient; preprocessing and hyperparameter selection belong within the training partitions.

The original [evidence ZIP](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/evidence_bundle.zip) was checked against SHA-256 `a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c` and its Git blob. Its `experiment_manifest.json` and `validation_summary.json` identify the training provenance and passed audits for all 24 configurations. Aggregate consistency checks pass; this report does not repeat the private patient-level audit or claim that hashes authenticate execution independently.

## 2. Leading configurations and credible alternatives

Values below are read from [summary.csv](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/summary.csv). All IDs have the prefix `SVM-`; STD means StandardScaler and MM means MinMaxScaler. ANOVA sizes count genes; PCA sizes count components. Scores are unitless. SD is the sample SD of three complete repeat scores, not a confidence interval. Rows are selected for performance and controlled-comparison relevance, not presented as a new inferential analysis.

| Configuration | Macro-F1 mean | Sample SD | Balanced accuracy mean | Recorded seconds |
| --- | ---: | ---: | ---: | ---: |
| STD-ANOVA-150-LINEAR | 0.771658 | 0.002694 | 0.767179 | 76.099 |
| STD-ANOVA-150-RBF | 0.768492 | 0.019437 | 0.764024 | 234.671 |
| STD-ANOVA-100-RBF | 0.765283 | 0.025035 | 0.768495 | 233.063 |
| MM-ANOVA-150-RBF | 0.763746 | 0.012927 | 0.760486 | 232.236 |
| MM-PCA-150-RBF | 0.736047 | 0.031575 | 0.729348 | 393.855 |
| STD-PCA-150-LINEAR | 0.722685 | 0.028622 | 0.704684 | 216.608 |

The Linear baseline has the highest observed mean Macro-F1 among all 24 configurations. Its lead over the matched RBF model is only **0.003166** (approximately 0.317 percentage points). The original [comparison.csv](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/comparison.csv) uses this Linear configuration as its reference and explicitly labels differences exploratory/descriptive. Being the reference is not evidence that it was selected independently of these outcomes.

STD-ANOVA-100-RBF deserves retention as a feature-budget comparator: it has lower mean Macro-F1 but slightly higher mean balanced accuracy than the proposed baseline. A single metric does not resolve every trade-off. MM-ANOVA-150-RBF supplies a close alternative with a different scaler. The two PCA candidates have lower observed means but preserve meaningful tests of representation choice; they should not be described as equally strong on the present primary metric.

Recorded runtime sums completed outer-fold work, including inner search and refit; it is not standalone inference latency or total wall-clock deployment cost. The matched RBF configuration took approximately **3.08 times** the recorded time of Linear on this run. These timings are machine- and grid-dependent, not a hardware-independent kernel benchmark. Linear therefore offers a practical candidate for further investigation, without establishing that the biological decision boundary is linear.

## 3. Repeat stability and subtype trade-offs

The [repeat scores](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/reports/repeat_scores.csv) show baseline Macro-F1 values **0.772274, 0.773992 and 0.768709**. The matched RBF values are **0.751271, 0.764638 and 0.789567**. Linear has smaller observed split variation, but RBF exceeds it in the third repeat. Three dependent scores cannot establish a reliable probability of one model outperforming the other.

The [subtype analysis](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/reports/subtype_analysis.csv) gives the following means of repeat-level F1:

| Subtype | Unique patients | STD-ANOVA-150-LINEAR | STD-ANOVA-150-RBF |
| --- | ---: | ---: | ---: |
| LMS | 104 | 0.896617 | 0.893061 |
| DDLPS | 57 | 0.823612 | 0.863300 |
| UPS | 49 | 0.667088 | 0.654295 |
| MFS | 25 | 0.525041 | 0.533629 |
| SS | 10 | 1.000000 | 1.000000 |
| MPNST | 9 | 0.717593 | 0.666667 |

RBF's higher DDLPS and MFS F1 argues against dismissing it based only on the overall ranking. MFS remains weak for both. The baseline's MPNST F1 sample SD is **0.081381**, much larger than its overall Macro-F1 SD; overall stability can conceal small-class variability. SS's perfect observed F1 is based on only ten unique patients and does not demonstrate certainty on future patients.

The [confusion matrices](https://github.com/nhdung98/ProjectA/blob/67ad3e764dadf13827421ab2d6f78f85809b42b3/results/protocol2/windows-official-01/reports/confusion_matrices.csv) expose a particular baseline weakness: **21/75 MFS prediction events (28.0%) were classified as UPS**, while **20/147 UPS events (13.6%) were classified as MFS**. MPNST has **18/27 correct events (66.7%)**. These are pooled events across three repeats, not independent patients. The baseline confusion matrix has 762 events from the same 254 people. Subtype F1 above averages per-repeat scores rather than deriving F1 from that pooled matrix.

## 4. Limits of the selection

- All 24 candidates were compared on overlapping evaluation data. Choosing the maximum creates winner-selection bias; the selected score is not an unbiased estimate of a newly chosen workflow's future performance.
- Repeats reuse patients and overlapping training sets. Neither 15 folds nor 762 events provide 15 or 762 independent experimental units. Repeat SD describes split variation only. No p-values, confidence intervals, superiority probabilities or significance claims are inferred here.
- Low-support SS and MPNST results are especially uncertain. Class-specific errors matter even where macro averages look stable; balanced accuracy and Macro-F1 capture different aspects of performance.
- One cohort and one execution setting do not establish transportability, causal biological interpretation or clinical readiness. ANOVA selection does not by itself establish reproducible biomarkers.
- Do not use these outer-test results to tune additional choices and then present the same scores as unbiased validation of those choices. Any subsequent exploratory reuse must remain labelled as such.

## 5. Provisional comparator strategy and next questions

**Primary baseline:** retain STD-ANOVA-150-LINEAR as a fixed starting candidate because it combines the highest observed Macro-F1, low observed repeat variation and lower recorded runtime. This is a resource-conscious research decision, not a proven winner.

**Core comparators:** retain STD-ANOVA-150-RBF to change only the kernel, and STD-PCA-150-LINEAR to examine reduction at the same scaler/kernel and nominal dimension. Genes and components are different representations, so this is not an equivalence of biological information.

**Targeted controls:** retain STD-ANOVA-100-RBF for the feature-budget question and MM-ANOVA-150-RBF for a scaler comparison against STD-ANOVA-150-RBF. If representation-by-scaling interaction is in scope, include MM-PCA-150-RBF matched against MM-ANOVA-150-RBF. Avoid attributing differences between unmatched pipelines to one factor. The team should agree the final comparison budget rather than automatically repeating every possible configuration.

Before Protocol 3.0 implementation, obtain supervisor/team agreement on:

1. A fixed candidate set, primary metric, secondary subtype outcomes and a revised selection mechanism. If pipeline choice is optimized, place that choice inside the training-side selection procedure of any new evaluation; do not select using its outer test data.
2. Uncertainty-aware paired comparisons that account for patient reuse and the full selection procedure. Choose the method and assumptions before analysing new outcomes; naive tests on fold/repeat scores are inappropriate. Additional splits of this already-inspected cohort do not erase prior selection bias.
3. Controlled scaling, reduction and feature-budget ablations with all fitted preprocessing confined to training partitions. Investigate gene-selection stability and PCA behaviour without making unsupported biomarker claims.
4. Error-focused review of MFS/UPS and low-support subtypes, and a plan for genuinely independent held-out or external evidence if available and approved. No such validation set is established by this report.
5. Comparable runtime measurement under fixed hardware, grids and parallelism. Preserve the original Protocol 2.0 artifacts unchanged as the reference round.

The immediate decision is to carry a justified Linear baseline and explicit alternatives into planning. It is not permission to train Protocol 3.0 or to claim the selected configuration is clinically ready.
