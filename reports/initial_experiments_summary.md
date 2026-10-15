# Initial sarcoma classification experiments: methodology and findings

Written: 15 October 2026. Results snapshot: 13 October 2026.

## Scope

Our study investigates how preprocessing, feature reduction, and classifier settings affect the classification of six soft-tissue sarcoma subtypes using gene-expression data. The objective is to identify promising pipelines while examining performance across individual subtypes and repeated data splits.

This report summarizes the previously reviewed Logistic Regression round and the four-member SVM comparison, including the leader's Member 2 reproduction. It preserves the evidence status of that comparison; it does not mark the SVM round as formally accepted. It does not incorporate experiments completed after the snapshot date.

The results cover **32 predictive pipeline configurations and one majority-class reference**, evaluated through hundreds of outer cross-validation fits. The SVM design additionally includes thousands of model fits for parameter tuning. These counts describe repeated experiments on one dataset, rather than independent patient cohorts.

## 1. Methodology

### 1.1 Dataset and preparation

We used the TCGA-SARC gene-expression and clinical files obtained from the cBioPortal Firehose Legacy study. The expression file already contains processed RSEM measurements. Our project starts with these numerical measurements rather than raw RNA-sequencing reads.

We matched expression profiles to clinical records using sample identifiers, transposed the expression matrix so that each row represents one tumor sample, and retained samples belonging to the six target subtypes.

| Subtype | Abbreviation | Patients |
| --- | --- | ---: |
| Leiomyosarcoma | LMS | 104 |
| Dedifferentiated liposarcoma | DDLPS | 57 |
| Undifferentiated pleomorphic sarcoma | UPS | 49 |
| Myxofibrosarcoma | MFS | 25 |
| Synovial sarcoma | SS | 10 |
| Malignant peripheral nerve sheath tumor | MPNST | 9 |
| **Total** | | **254** |

The dataset contains **254 tumor samples from 254 distinct patients and 20,531 initial gene-expression features**. Only gene-expression columns enter the models. Sample and patient identifiers support tracking and validation checks. The target comes from the clinical `Cancer Type Detailed` label mapped to the six subtype abbreviations.

Nine matched samples fall outside the selected classification cohort: five with nonspecific soft-tissue labels, two desmoid/aggressive fibromatosis samples, and two pleomorphic liposarcoma samples. Two clinical records have no matching expression profile. The preparation audit found no missing expression measurements.

Repeated gene identifiers remain separate source records, with unique feature-column names. We preserve their measurements and order rather than combining them.

See [data provenance](../DATA_SOURCES.md) and the [preparation implementation](../src/data/prepare.py).

### 1.2 Preprocessing and feature representation

Each model uses a pipeline containing the following steps:

1. **Log transformation:** Apply `log2(x + 1)` to compress large expression values while retaining zeros.
2. **Constant-feature removal:** Remove features with zero variance in the relevant training samples.
3. **Scaling:** Apply either standard scaling or min-max scaling.
4. **Feature reduction:** Apply ANOVA selection, PCA, or no reduction, depending on the configuration.
5. **Classification:** Fit the specified classifier.

Standard scaling uses each feature's training mean and standard deviation. Min-max scaling uses its training minimum and maximum. Held-out samples use the fitted training transformation; min-max values can therefore fall outside the training range.

ANOVA selection ranks features using their expression differences across the training classes and retains the highest-ranked 50, 100, or 150 features. PCA constructs 50, 100, or 150 components from combinations of the original features. **Selected genes and PCA components represent different kinds of inputs**, even when their counts are equal.

The SVM pipelines use randomized PCA with seed 42 and no whitening. We record selected gene features for ANOVA and explained-variance information for PCA.

Learned preprocessing and reduction fit only on the relevant training samples. The fixed log transform learns no parameters. See the [pipeline implementation](../src/experiments/pipeline.py).

### 1.3 First round: Logistic Regression

The first round compared eight predictive configurations:

- Standard scaling without feature reduction.
- Min-max scaling without feature reduction.
- Standard scaling with ANOVA selecting 50, 100, or 150 genes.
- Standard scaling with PCA producing 50, 100, or 150 components.

All configurations used the same fixed regularized Logistic Regression settings: L2 regularization, `C = 1.0`, the `lbfgs` solver, and a maximum of 5,000 iterations. This round did not tune parameters.

A majority-class classifier provided an additional reference. It always predicts the most frequent training class. These were leader-run shared-runner experiments, rather than submissions attributed to the four SVM experiment owners.

### 1.4 Second round: SVM

The SVM round evaluated 24 configurations across four experiment owners.

| Member | Scaling | Representation | Sizes | Kernels |
| --- | --- | --- | --- | --- |
| 1 | Min-max | ANOVA-selected genes | 50, 100, 150 | Linear and RBF |
| 2 | Standard | ANOVA-selected genes | 50, 100, 150 | Linear and RBF |
| 3 | Min-max | PCA components | 50, 100, 150 | Linear and RBF |
| 4 | Standard | PCA components | 50, 100, 150 | Linear and RBF |

Each member evaluated six configurations: three representation sizes multiplied by two kernels. Linear SVM uses linear decision functions in the input feature representation. RBF SVM uses a radial basis function kernel to allow nonlinear decision boundaries.

The current rounds used **no class weighting or resampling**. Random Forest and established clinical-marker baselines remain planned work in this snapshot.

### 1.5 Validation and parameter tuning

Both rounds used five stratified outer folds repeated three times, with seed 42 and shared saved splits. Each outer evaluation trained on approximately 203-204 samples and tested on 50-51 samples.

The SVM round used **`GridSearchCV` with four-fold stratified inner cross-validation** within each outer training set:

| Parameter | Search values |
| --- | --- |
| `C` | `0.01`, `0.1`, `1`, `10`, `100` |
| RBF `gamma` | `scale`, `0.001`, `0.01`, `0.1` |
| Selection metric | Mean inner-fold macro-F1 |

Linear SVM searched five parameter candidates. RBF SVM searched 20 combinations of `C` and `gamma`. Gamma does not apply to the linear kernel.

Every inner candidate fit includes the complete preprocessing and reduction pipeline. Scaling, constant-feature removal, ANOVA selection, and PCA therefore learn from the corresponding inner training fold only. After selecting parameters, the winning pipeline refits on the outer training set and predicts the untouched outer test samples.

Parameter selection runs separately for each configuration and outer fold. Different folds may select different values. "Best" means best among the tested combinations according to the inner validation metric.

Patient identifiers provide an additional check against overlap between training and test samples. See the [SVM settings](../configs/svm.json), [experiment protocol](../archive/week01/docs/experiment_protocol.md), and [nested validation implementation](../src/experiments/svm.py).

### 1.6 Evaluation metrics

A held-out prediction is a prediction for a sample excluded from the model's training and parameter tuning for that outer evaluation. Its known label allows us to measure prediction quality.

For each repeat, we combine predictions from all five outer test folds into one set of 254 held-out predictions. We calculate metrics from this pooled set rather than averaging small test-fold subtype scores.

The principal metrics are:

- **Macro-F1:** Average F1 across the six subtypes, giving each subtype equal weight.
- **Balanced accuracy:** Average recall across the six subtypes.
- **Subtype precision, recall, and F1:** To identify uneven performance.
- **Confusion matrices:** To identify which subtypes the models confuse.

We report the mean and sample standard deviation across the three repeats. The standard deviation describes sensitivity to the data splits. It is **not a confidence interval**, because the repeats reuse the same patients. See the [metric implementation](../src/experiments/metrics.py).

### 1.7 Scale of the experiments

| Experimental round | Configurations | Outer evaluations | Held-out predictions |
| --- | ---: | ---: | ---: |
| Logistic Regression plus majority reference | 9 | 135 | 6,858 |
| SVM | 24 | 360 | 18,288 |
| **Total** | **33** | **495** | **25,146** |

Each configuration produces `254 x 3 = 762` outer held-out predictions. Each SVM member produces `6 x 762 = 4,572`.

The complete SVM design entails **18,000 inner tuning fits and 360 outer refits**, totaling **18,360 model fits**:

- Linear: `12 configurations x 15 outer splits x 4 inner folds x 5 candidates = 3,600` inner fits.
- RBF: `12 configurations x 15 outer splits x 4 inner folds x 20 candidates = 14,400` inner fits.
- Outer refits: `24 configurations x 15 outer splits = 360`.

These are workload counts implied by the complete design, not an inventory of every historical process invocation. They exclude additional reproduction runs, smoke tests, and incomplete exploratory runs. They distinguish unique configurations, model fits, and sample-level predictions; none represents independent patient cohorts.

## 2. Key findings

### 2.1 ANOVA-150 produced the leading configuration in both rounds

In the Logistic Regression round, standard scaling with ANOVA selecting 150 genes achieved the highest mean macro-F1, **0.765**, compared with **0.727** for the standard-scaled model without reduction. The improvement was approximately **0.038**, and ANOVA-150 exceeded the baseline in all three repeats.

In the SVM round, the leading configuration was **standard scaling with ANOVA-150 and a linear kernel**, achieving mean macro-F1 **0.772** and balanced accuracy **0.767**.

| Configuration | Mean macro-F1 | Repeat SD | Balanced accuracy |
| --- | ---: | ---: | ---: |
| LR, standard scaling, no reduction | 0.727 | 0.018 | 0.743 |
| LR, standard scaling, ANOVA-150 | 0.765 | 0.010 | 0.749 |
| LR, standard scaling, PCA-100 | 0.754 | 0.018 | 0.753 |
| SVM, standard scaling, ANOVA-150, linear | 0.772 | 0.003 | 0.767 |
| SVM, standard scaling, ANOVA-150, RBF | 0.768 | 0.019 | 0.764 |
| SVM, standard scaling, ANOVA-100, RBF | 0.765 | 0.025 | 0.768 |
| SVM, min-max scaling, ANOVA-150, RBF | 0.764 | 0.013 | 0.760 |
| SVM, min-max scaling, PCA-150, RBF | 0.736 | 0.032 | 0.729 |

The leading SVM score is approximately 0.007 above the leading Logistic Regression score. This is a descriptive cross-round comparison: Logistic Regression used fixed parameters, whereas SVM used nested tuning. It does not establish that SVM is generally superior.

The majority-class reference had macro-F1 approximately 0.097 and balanced accuracy 0.167 in the Logistic Regression round.

### 2.2 Representation size strongly affected ANOVA performance

All four SVM ANOVA families improved as the retained feature count increased from 50 to 100 to 150.

| ANOVA pipeline | 50 genes | 100 genes | 150 genes |
| --- | ---: | ---: | ---: |
| Standard scaling, linear | 0.692 | 0.735 | 0.772 |
| Standard scaling, RBF | 0.734 | 0.765 | 0.768 |
| Min-max scaling, linear | 0.688 | 0.721 | 0.735 |
| Min-max scaling, RBF | 0.704 | 0.728 | 0.764 |

This supports retaining 150 genes as a strong candidate within the tested ANOVA settings. It does not show that 150 is optimal beyond the tested range.

In the Logistic Regression round, both ANOVA-50 and PCA-50 performed below the no-reduction baseline. Aggressive reduction therefore removed useful predictive information under those settings.

### 2.3 ANOVA usually outperformed PCA, but not in every matched comparison

Across the 12 SVM comparisons matched by scaling, representation size, and kernel, ANOVA achieved higher mean macro-F1 in **9 of 12 cases**. These are descriptive counts calculated from the 24-row score table, not independent statistical tests.

The strongest ANOVA configuration reached **0.772**, while the strongest PCA configuration reached **0.736**. Some PCA configurations nevertheless outperformed their ANOVA counterparts, particularly at smaller representation sizes.

PCA showed a different pattern in the Logistic Regression round: PCA-100 produced the highest balanced accuracy, **0.753**, while PCA-150 had a lower macro-F1 than PCA-100. Increasing representation size does not guarantee improvement across methods.

### 2.4 RBF usually beat linear, but the leading configuration was linear

RBF achieved higher mean macro-F1 in **9 of the 12 matched SVM kernel comparisons**. Nevertheless, the highest-scoring configuration used a linear kernel.

For standard-scaled ANOVA-150, linear SVM achieved **0.772**, compared with **0.768** for RBF. The corresponding repeat standard deviations were **0.003** and **0.019**.

Kernel choice therefore depends on representation and scaling. The results support comparing both kernels rather than assuming additional nonlinear flexibility will always improve performance.

### 2.5 Scaling changed performance and subtype tradeoffs

Standard scaling achieved higher mean macro-F1 in **7 of 12 matched SVM scaling comparisons**. It performed well with larger ANOVA feature sets, while min-max scaling performed better in several PCA comparisons.

In the Logistic Regression round, switching the no-reduction model from standard to min-max scaling increased macro-F1 from **0.727 to 0.742**, but decreased balanced accuracy from **0.743 to 0.733**. Mean MFS F1 decreased from **0.484 to 0.445**.

Scaling should therefore be assessed using both aggregate and subtype metrics.

### 2.6 MFS remained the most persistent classification difficulty

The leading SVM configuration produced the following subtype results:

| Subtype | Patients | Mean F1 |
| --- | ---: | ---: |
| LMS | 104 | 0.897 |
| DDLPS | 57 | 0.824 |
| UPS | 49 | 0.667 |
| MFS | 25 | 0.525 |
| SS | 10 | 1.000 |
| MPNST | 9 | 0.718 |

The highest MFS mean F1 across all SVM configurations was approximately **0.539**, achieved by min-max scaling with ANOVA-150 and RBF. This configuration did not lead the overall macro-F1 ranking.

For the leading linear SVM, **9, 6, and 6 of the 25 MFS samples** were predicted as UPS across the three repeats. MFS/UPS confusion remains a concrete target for follow-up analysis.

### 2.7 Aggregate improvements did not benefit every subtype

In the Logistic Regression round, ANOVA-150 improved MPNST mean F1 from **0.646 to 0.763** and SS mean F1 from **0.893 to 0.965**. However, UPS decreased from **0.670 to 0.651**, and MFS decreased from **0.484 to 0.476**.

Selecting a pipeline from its overall score alone can conceal important subtype weaknesses.

## 3. Interpretation and evidence limitations

The strongest current candidate is standard scaling with ANOVA selecting 150 genes and a linear SVM. Its three macro-F1 scores were approximately **0.772, 0.774, and 0.769**, indicating low split variation within this dataset.

Several limitations constrain the conclusions:

- SS and MPNST contain only ten and nine patients. Their scores are sensitive to a small number of changed predictions.
- Perfect SS performance reflects repeated evaluation of the same ten patients, not independent confirmation.
- Low performance variation does not establish stable gene selection. Gene-selection stability requires a separate analysis.
- Choosing the leading configuration from outer results does not independently validate the selected pipeline.
- The SVM comparison lacks a matched no-reduction baseline, so it cannot establish the benefit of reduction relative to using all available genes.
- Member 2's comparison uses leader reproduction results; agreement with the original submission was assessed against rounded summaries.
- Member 4's prediction-based performance checks passed, but its complete feature-details audit remained outstanding at the snapshot date.
- Training-code equivalence was checked across the reviewed commits, but the formal comparison tool's exact-commit policy had not been changed.
- Cross-member runtime differences do not provide a controlled speed benchmark because execution hardware differs.

The Logistic Regression round passed its recorded output checks. All 24 SVM performance scores were checked against available predictions, but the remaining preprocessing evidence and formal commit-comparability decisions still needed resolution at the snapshot date.

## 4. Next steps

The next stage will add matched no-dimensional-reduction baselines, evaluate Random Forest, and define a baseline using established gene markers already used in sarcoma diagnosis.

The marker baseline will require checking each marker's clinical assay meaning and coverage in the expression matrix. Gene-expression measurements cannot directly substitute for fusion, amplification, or protein assays.

Further analysis should prioritize MFS/UPS errors, minority-subtype performance, and stability of selected genes. Independent-cohort validation will be needed before making claims about generalization or clinical usefulness.

The experiments support prioritizing promising pipelines and designing the next comparisons. They do not establish an independently validated diagnostic model.

## 5. Evidence and provenance

The accompanying [evidence snapshot](evidence/initial-experiments-20261013/README.md) preserves the result reports and tables used for this summary. These are historical copies for traceability, not newly accepted run folders or a replacement for the full experiment archives.

- [Logistic Regression report](evidence/initial-experiments-20261013/logistic_regression_report.md).
- [SVM comparison review and evidence status](evidence/initial-experiments-20261013/svm_review.md).
- [SVM configuration scores](evidence/initial-experiments-20261013/scores.csv).
- [SVM repeat scores](evidence/initial-experiments-20261013/repeat_scores.csv).
- [SVM subtype summary](evidence/initial-experiments-20261013/subtype_summary.csv).
- [SVM confusion matrices](evidence/initial-experiments-20261013/confusion_matrices.csv).

Within each copied source report, original relative links retain the source report's context; the evidence snapshot README identifies the original locations. The links above and the source-code links elsewhere in this summary resolve within this repository.
