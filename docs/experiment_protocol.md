# Experiment protocol: SVM experiment

Protocol 2.0, agreed 11 October 2026. This is the current member experiment plan.

## Data and fixed preprocessing

Use the same 254 unique patients, 20,531 gene records, and six labels: LMS 104, DDLPS 57, UPS 49, MFS 25, SS 10, MPNST 9. Keep repeated gene records separate. Only `gene__` columns are model inputs; exclude labels, identifiers, and clinical columns.

Every pipeline follows `log2(x + 1) -> VarianceThreshold(0) -> scaling -> ANOVA or PCA -> SVC`. Fit constant removal, scaling, and reduction inside each inner training fold. Refit the selected complete pipeline on outer training data before outer prediction. Do not fit preprocessing on the full cohort or on all outer training data before the inner search. No SMOTE, imputation, class weighting, or extra models in this round.

## Shared nested validation

Outer evaluation: five stratified folds repeated three times, seed 42. Reuse `results/splits/outer.csv`; each outer fold tests 50-51 patients and develops on 203-204. Every patient receives one held-out prediction per repeat.

Inner search: four stratified folds, shuffled with seed 42 within each outer training set. Saved assignments are in `results/splits/inner.csv`. Each inner training set has 152-153 patients; every inner training and validation fold must contain all six classes. No outer test patient may enter inner training or validation. The runner checks source values, labels, patient identities, and both split checksums; altered assignments stop execution.

## Member assignments

| Member | Scaling | Reduction | Sizes | Kernels |
| --- | --- | --- | --- | --- |
| 1 | Min-max | ANOVA | 50, 100, 150 genes | Linear and RBF |
| 2 | Standard | ANOVA | 50, 100, 150 genes | Linear and RBF |
| 3 | Min-max | PCA | 50, 100, 150 components | Linear and RBF |
| 4 | Standard | PCA | 50, 100, 150 components | Linear and RBF |

ANOVA uses `SelectKBest(f_classif)` to rank original genes, without a p-value cutoff. PCA produces components, not selected genes. Keep randomized PCA fixed: seed 42, no whitening, iterated power 7, oversamples 10, QR normalization. Training-fold feature counts must support the requested size.

## SVM parameter search

Linear: search `C = [0.01, 0.1, 1, 10, 100]`. RBF: search the same C crossed with `gamma = ["scale", 0.001, 0.01, 0.1]`. Gamma does not apply to linear. Keep SVC class weights None, probability False, tolerance 0.001, maximum iterations -1, and cache size 200 MB.

C controls the penalty for margin violations; larger C penalizes them more strongly. RBF gamma controls how local each sample's influence is. These are tuned only inside the inner validation.

Select the highest mean inner-fold macro-F1. Exact ties select the first candidate in the declared grid order: ascending C, then declared gamma order. Do not choose parameters using outer predictions. Save all candidate fold scores and the selected parameters for every outer fold. A warning or failed candidate makes the run incomplete and requires review.

## Evaluation and workload

Macro-F1 gives every subtype equal weight when averaging its F1 score. Balanced accuracy averages recall across the six subtypes.

Each configuration has 15 outer refits and 762 held-out predictions. Linear uses 315 pipeline fits; RBF uses 1,215. Each member runs three sizes for both kernels: six configurations and 4,590 fits. Total: 24 configurations and 18,360 fits.

Calculate macro-F1, balanced accuracy, per-subtype precision/recall/F1/support, and confusion matrices from all 254 held-out predictions separately for each repeat. Report three repeat scores, their mean and sample standard deviation, plus runtime. Repeats reuse patients; the standard deviation is split variation, not a confidence interval. Pay particular attention to MPNST and SS because their counts are small.

## Acceptance

Official runs use the same reviewed commit with a clean working tree and shared settings in `configs/svm.json`. Smoke and development runs are checks, not official submissions. Preserve generated outputs. Follow [submission requirements](submission_requirements.md) and [comparison rules](combining_results.md). Repeatedly choosing a winner from outer scores does not independently validate a final model.
