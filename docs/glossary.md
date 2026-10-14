# Project glossary

A plain-language guide to every biology, medical, data, machine-learning, and statistics term used in this repository: the README, protocol 2.0, the protocol 3.0 proposal, the architecture notes, and the research reports R1–R3.

You do not need a biology or statistics background to read it. Each entry says what the term means in simple words, and, where useful, **why it matters for us**.

**How to use this page**

- New to the project? Read sections 1–3 in order. They take about 15 minutes and cover most of what you need.
- Reading a document and stuck on a word? Search this page (Ctrl+F / Cmd+F).
- Our protocol 3.0 proposal and research reports are written in Vietnamese. Section 13 maps the Vietnamese words used there to the English terms below.

**Contents**

1. The project in one page
2. Biology basics
3. The six sarcoma subtypes
4. Genes and markers you will see
5. Data sources and data processing
6. Machine-learning basics
7. Pipeline stages (S1–S5)
8. Classifiers (models)
9. Validation: how we test models fairly
10. Metrics: how we score models
11. Statistics for comparing pipelines
12. Protocol, workflow, and repository terms
13. Vietnamese ↔ English terms in our docs
14. Common questions

---

## 1. The project in one page

**What we do.** We take tumour samples from 254 sarcoma patients. For each sample we know how active about 20,000 genes are. We train a computer model to read those gene activity numbers and predict which of 6 sarcoma types the tumour is.

**Why it is hard.**

- **Few patients, many measurements.** 254 patients but 20,531 numbers per patient. With so many numbers and so few examples, a model can easily "memorise" noise instead of learning real patterns.
- **Unequal class sizes.** One type (LMS) has 104 patients; another (MPNST) has only 9. Models tend to ignore small groups.
- **Some types are biologically almost the same.** Doctors and scientists themselves struggle to tell MFS from UPS. No model can fully separate things that biology does not separate.
- **Some labels may be wrong.** Our 254 patients include about 48 that were not part of TCGA's expert-reviewed set of 206.

**What we deliver.** A fair, repeatable comparison of many model pipelines, one honest headline score, an explanation of where and why models make mistakes, and later an app and a paper.

**Where we are.** Round 1 (protocol 2.0) compared 24 SVM pipelines. The best reached a macro-F1 of about 0.77. Protocol 3.0 proposes comparing 13 (+2 optional) different pipelines under the same fair testing setup.

---

## 2. Biology basics

| Term | Simple meaning | Why it matters for us |
| --- | --- | --- |
| **Cell** | The smallest living unit. Your body is made of trillions of them. | Tumours are groups of cells that grow when they should not. |
| **DNA** | The instruction book inside every cell. Almost every cell has the same book. | Changes in DNA (mutations) can turn a normal cell into a cancer cell. |
| **Gene** | One "recipe" in the DNA book. Humans have about 20,000 protein-making genes. | Our dataset has one column per gene record (20,531 in total). |
| **Protein** | The molecule a gene recipe produces. Proteins do the actual work in the cell. | Some lab tests (IHC) detect proteins; our data measures RNA instead. |
| **RNA / mRNA** | A temporary copy of a gene recipe. The cell copies a gene into messenger RNA (mRNA), then uses the mRNA to build a protein. | We measure how much mRNA each gene produces. |
| **Gene expression** | How "switched on" a gene is, measured as how much mRNA it makes. High expression = the gene is very active. | This is our input data. Different tumour types switch on different genes. |
| **Transcriptome** | All the mRNA in a sample at once, i.e. the expression of every gene. | Our 20,531 numbers per patient are a transcriptome snapshot. |
| **RNA-seq** (RNA sequencing) | A lab technology that reads all mRNA in a sample and counts how much comes from each gene. | The technology that produced our data. |
| **Microarray** | An older technology that measures gene expression using probes on a chip. | Older studies we cite (Nielsen 2002) used microarrays. |
| **Tumour / neoplasm** | An abnormal lump of cells. It can be benign (not cancer) or malignant (cancer). | All our samples are malignant tumours. |
| **Cancer** | Cells that grow uncontrollably and can spread. | — |
| **Sarcoma** | A cancer that starts in connective tissue: muscle, fat, nerves, fibrous tissue, bone, cartilage. Rare: about 1% of adult cancers. | Our disease. Most cancers are *carcinomas* (from skin or organ linings); sarcomas are different. |
| **Soft tissue sarcoma (STS)** | A sarcoma of soft tissue (muscle, fat, nerve, fibrous tissue), not bone. | All 6 of our types are soft tissue sarcomas. |
| **Subtype** | A specific kind within a disease. Sarcoma has 50+ subtypes. | Our 6 classes (labels) are 6 subtypes. |
| **Histology** | Studying tissue under a microscope. A "histological type" is the type a pathologist assigns by looking at the tissue. | Our labels are histological diagnoses. |
| **Pathologist / pathology** | A doctor who diagnoses disease by examining tissue. Pathology is that field. | Pathologists created our labels. |
| **Pathology review** | A second, expert check of the diagnosis. Cases can be confirmed, changed to another type, or excluded. | TCGA reviewed its cases and kept 206. Our 254 include cases outside that reviewed set. |
| **H&E stain** | The standard pink-and-purple dye used to look at tissue slides. | Pathologists diagnose mostly from H&E slides. |
| **IHC (immunohistochemistry)** | A lab stain that shows whether a specific protein is present in the tissue. | Many "markers" in our research are IHC tests (e.g. S100, SOX10, TLE1). |
| **FISH** | A lab test that lights up specific DNA regions to count copies of a gene. | Used to confirm MDM2 amplification for DDLPS. |
| **qRT-PCR** | A lab test that measures the expression of a few chosen genes very precisely. | Used to confirm marker genes in an independent sample set. |
| **Mutation** | A change in the DNA sequence. | Drives cancer. Not directly in our data, but explains why expression differs. |
| **Copy number / CNV / SCNA** | How many copies of a DNA region a cell has. Normal is 2. **Amplification** = many extra copies; **deletion** = copies lost. SCNA = somatic copy-number alteration. | More copies of a gene usually means more expression. DDLPS is defined by amplification of MDM2/CDK4. |
| **Amplicon** | A stretch of DNA that has been amplified (copied many times). | The 12q13-15 amplicon in DDLPS contains MDM2, CDK4, HMGA2, FRS2, TSPAN31, CTDSP2. |
| **12q13-15** | A location on chromosome 12 (long arm "q", bands 13 to 15). | The DDLPS amplicon. |
| **Fusion gene / translocation** | Two separate genes break and join into one abnormal gene. A translocation is the chromosome swap that causes this. | SS is defined by the SS18–SSX fusion, which gives it a very distinct expression pattern. |
| **Driver** | A genetic change that actually causes the cancer to grow (vs. "passenger" changes that come along for the ride). | Subtypes with one clear driver (SS, DDLPS) are easy to classify. |
| **Karyotype (simple vs complex)** | The overall picture of a cell's chromosomes. *Simple*: one specific change. *Complex*: many random changes. | SS has a simple karyotype; LMS, UPS, MFS have complex ones and look more alike. |
| **Methylation** | Chemical tags on DNA that switch genes off without changing the sequence. Part of **epigenetics**. | The best real-world sarcoma classifier (DKFZ) uses methylation, not RNA. |
| **Epigenetic** | Changes in how genes are switched on/off, without changing the DNA letters. | MPNST loses a gene-silencing system (PRC2), an epigenetic change. |
| **PRC2 / H3K27me3** | PRC2 is a protein complex that silences genes by adding a mark called H3K27me3. | Most MPNSTs lose PRC2 (via EED or SUZ12 loss), so they lose the H3K27me3 mark. |
| **Homeobox genes (HOX)** | Genes that control body plan during development (e.g. HOXA11). | Wrongly switched on in MPNST; HOXA11 separates uterine from soft-tissue LMS. |
| **Differentiation** | How much a tumour cell still looks and behaves like the normal tissue it came from. **Well-differentiated** = still similar; **poorly/undifferentiated** = has lost those features. | Poorly differentiated LMS loses its muscle features and starts to look like UPS. |
| **Smooth muscle** | Involuntary muscle (in blood vessels, uterus, gut). | LMS is a smooth-muscle cancer; smooth-muscle genes (MYOCD, ACTG2, LMOD1) help identify it. |
| **Pleomorphic** | Cells with very irregular, varied shapes and sizes. | "Undifferentiated pleomorphic sarcoma" (UPS) is named for this. |
| **Myxoid stroma** | Jelly-like, mucus-rich material around tumour cells. | The amount of myxoid stroma is the main thing that separates MFS from UPS under the microscope, not a gene. |
| **Tumour microenvironment / immune infiltration** | The non-cancer cells in a tumour sample, such as immune cells (leukocytes) and blood vessels. | Their RNA mixes into the sample, so some confusion between types may come from immune signal, not tumour cells. |
| **Diagnosis vs prognosis** | *Diagnosis*: what disease/type it is. *Prognosis*: how the disease will likely progress (survival, spread). | We do **diagnosis** (subtype). Tools like CINSARC do prognosis and are not baselines for us. |
| **Metastasis** | Cancer spreading to other parts of the body. | Relevant to prognosis tools, not our task. |
| **Uterine vs soft-tissue LMS (ULMS / STLMS)** | LMS arising in the uterus vs elsewhere. | TCGA's 80 reviewed LMS = 53 STLMS + 27 ULMS. We treat them as one class. |
| **NF1 (neurofibromatosis type 1)** | An inherited condition (and a gene) that raises the risk of nerve tumours. | Many MPNSTs are NF1-associated. |
| **GTEx** | A public dataset of gene expression from normal (non-cancer) human tissues. | Used by van IJzendoorn 2019 to compare tumours with normal tissues. |

---

## 3. The six sarcoma subtypes

| Code | Full name | Plain description | Our count (reviewed set) | How easy to classify | Why |
| --- | --- | --- | --- | --- | --- |
| **LMS** | Leiomyosarcoma | Cancer of smooth muscle | 104 (80) | Mostly easy | Strong smooth-muscle and miRNA signal. Poorly differentiated LMS can look like UPS. |
| **DDLPS** | Dedifferentiated liposarcoma | Fat-tissue cancer that has lost its fat-like look | 57 (50) | Very easy | Defined by MDM2/CDK4 amplification; MDM2 expression alone almost separates it perfectly. |
| **UPS** | Undifferentiated pleomorphic sarcoma | A sarcoma with no clear tissue of origin; a "diagnosis of exclusion" | 49 (44) | Hard | Overlaps with MFS and with poorly differentiated LMS. Formerly called MFH (malignant fibrous histiocytoma). |
| **MFS** | Myxofibrosarcoma | A fibrous sarcoma with lots of myxoid (jelly-like) stroma | 25 (17) | Very hard | Molecularly almost the same as UPS. TCGA called them "a single entity with a phenotypic spectrum". |
| **SS** | Synovial sarcoma | Defined by the SS18–SSX fusion gene | 10 (10) | Easy despite small size | One fusion drives a uniform, distinct expression pattern. Round 1 recall ≈ 0.9–1.0. |
| **MPNST** | Malignant peripheral nerve sheath tumour | Cancer of the sheath around nerves | 9 (5) | Very hard | Tiny class, overlaps with SS (both nerve-like), and its labels are the least certain (9 vs 5 reviewed). |

**Key ideas from the research (R1–R3):**

- **MFS ↔ UPS is a spectrum, not two separate things.** Several studies merge them into one group. This sets a "biological ceiling": no model can fully separate them.
- **LMS → UPS errors have a biological reason.** Poorly differentiated LMS gradually loses its muscle features.
- **MPNST ↔ SS** is the second confusion pair, because both look nerve-like in expression.
- **USARC** is the merged "undifferentiated sarcoma" class used by the DKFZ methylation classifier; it combines UPS, MFS, and some pleomorphic liposarcoma.
- **"Biological ceiling"**: the best score that is possible given that biology itself blurs some classes. Our 0.77 may already be close to it.

---

## 4. Genes and markers you will see

| Term | Meaning |
| --- | --- |
| **Marker / biomarker** | A gene or protein whose level tells you something, e.g. which subtype a tumour is. |
| **Gene symbol** | A gene's short name, e.g. `MDM2`. Symbols can be duplicated or renamed. |
| **Entrez ID** | A stable numeric ID for a gene from NCBI. Used together with the symbol in our column names. |
| **Duplicate gene records** | The same symbol appears in more than one row of the source file. We keep them as separate features (decision Q2). |
| **DEG (differentially expressed gene)** | A gene whose expression is significantly different between two groups. |
| **Gene set / signature** | A group of genes that together describe a biological state. |
| **Marker panel** | A fixed, hand-picked list of marker genes (P15 in protocol 3.0). |

**Cheat sheet of genes named in our docs**

| Gene(s) | Linked to | What it tells us |
| --- | --- | --- |
| MDM2, CDK4, HMGA2, FRS2, TSPAN31, CTDSP2 | DDLPS | On the 12q13-15 amplicon. A UPS/MFS sample with very high MDM2 may actually be a mislabelled DDLPS. |
| MYOCD, ACTG2, LMOD1, CASQ2, SLMAP, CFL2, MYLK, SRC | LMS | Smooth-muscle genes. Lower in poorly differentiated LMS. |
| Calponin, h-caldesmon, transgelin, smooth muscle actin | LMS | Smooth-muscle proteins used in IHC. |
| HOXA11, HOXA11-AS | Uterine vs soft-tissue LMS | Best genes for separating ULMS from STLMS. |
| LMOD1, ARL4C | LMS subgroups | Mark LMS subtype I (better prognosis) and II (worse). |
| SS18–SSX1/2/4 | SS | The defining fusion. |
| TLE1, NEURL1, NPAS1 | SS | High in SS. TLE1 is not fully specific. |
| SCD | MPNST | Higher in MPNST than SS. |
| NF1, CDKN2A, EED, SUZ12 | MPNST | Genes lost in MPNST. |
| S100, SOX10 | MPNST | IHC markers for nerve-sheath origin. |
| JADE2 | MFS vs UPS | Best single gene for separating them, yet still overlaps. |
| "Matrix-associated genes" | MFS | Slightly higher in MFS than UPS. |
| TP53, RB1 | UPS/MFS | Commonly deleted tumour-suppressor genes. |

**Important warning (leakage via markers).** Most of these markers were discovered using TCGA-SARC itself, i.e. our own data. Using them as model inputs and then testing on the same data gives an optimistic, unfair score. That is why P15 (marker panel) is for interpretation only and can never be chosen as the winner.

---

## 5. Data sources and data processing

| Term | Meaning |
| --- | --- |
| **TCGA (The Cancer Genome Atlas)** | A large US project that profiled thousands of tumours across 33 cancer types and released the data publicly. |
| **TCGA-SARC** | The sarcoma part of TCGA. Our data comes from here. |
| **Cell 2017 paper** | The main TCGA sarcoma publication: "Comprehensive and Integrated Genomic Characterization of Adult Soft Tissue Sarcomas". Source of the 206 reviewed cases. |
| **The 206 reviewed set** | The 206 cases TCGA kept after expert pathology review (80 LMS, 50 DDLPS, 44 UPS, 17 MFS, 10 SS, 5 MPNST). |
| **Barcode** | TCGA's ID string for a patient/sample, e.g. `TCGA-XX-XXXX-01`. Parts of it encode the hospital (TSS) and the processing plate. |
| **cBioPortal** | A website for exploring cancer genomics data. We downloaded our files from its "Sarcoma (TCGA, Firehose Legacy)" study. |
| **Firehose Legacy** | An older, broader TCGA data release from the Broad Institute. Usually a superset of the published dataset, which is why we have 254 cases, not 206. |
| **PanCancer Atlas** | Another TCGA data release, harmonised across cancer types. |
| **GDC (Genomic Data Commons)** | The US government portal hosting the original TCGA data. |
| **Cohort** | The group of patients in a study. Ours: 254 patients. |
| **Sample** | One tissue piece measured. We have one sample per patient. |
| **Clinical data** | Patient information (age, diagnosis, etc.). We only use the subtype label from it; clinical columns are never model inputs. |
| **Label noise** | Some labels are wrong. Likely in our extra ~48 cases, especially MFS (25 vs 17) and MPNST (9 vs 5). |
| **Mislabel** | A sample with the wrong subtype label. |
| **TSS (tissue source site)** | The hospital that sent the sample to TCGA. Encoded in the barcode. |
| **Plate** | The lab batch a sample was processed in. Also encoded in the barcode. |
| **Batch effect** | Unwanted differences in measurements caused by *how/where* samples were processed, not by biology. A model can learn "which hospital" instead of "which tumour type". |
| **ComBat / ComBat-seq** | Statistical tools that remove batch effects. Excluded from our main pipeline because they can create fake differences when batches and classes are unbalanced (Nygaard 2016). |
| **Raw reads** | The original text output of the sequencing machine. We do **not** have these. |
| **Raw counts** | How many RNA fragments matched each gene. Needed for tools like DESeq2. We do not have them either. |
| **RSEM** | Software that estimates gene expression from RNA-seq reads. Our file contains RSEM *normalized* values, already processed by the source. |
| **Normalization** | Adjusting numbers so samples can be compared fairly (e.g. correcting for how deeply each sample was sequenced). |
| **TPM / FPKM** | Other common units of gene expression. Mentioned in research; we use RSEM normalized values. |
| **DESeq2 / VST / rlog / TMM** | Other normalization methods. They need raw counts, so we cannot use them. |
| **log2(x+1)** | Take each value, add 1, then take the base-2 logarithm. It squashes huge values (a gene at 50,000 vs 50) onto a manageable scale. The "+1" avoids log(0). It works per value, so it learns nothing from other samples and cannot leak. |
| **Expression matrix** | A table: rows = patients, columns = genes, cells = expression values. Ours is 254 × 20,531. |
| **Gene columns (`gene__SYMBOL__ENTREZ__rowN`)** | How our prepared file names each gene feature. Only `gene__` columns go into the model. |
| **Prepared / processed data** | The merged table created by `python -m src.data.prepare`. Not stored in Git. |
| **Data audit** | Checks on the raw inputs (IDs, non-negative values, class counts, hashes) by `src.data.audit`. |
| **Supplementary table (Table S1)** | Extra data published with a paper. Cell 2017 Table S1 lists the 206 reviewed barcodes (workstream W3 needs it). |

---

## 6. Machine-learning basics

| Term | Meaning |
| --- | --- |
| **Model / classifier** | A program that learns from examples and then predicts a category. Ours predicts 1 of 6 subtypes. |
| **Feature** | One input number. For us, one gene's expression value. |
| **Label / class / target** | The answer the model should predict: the subtype. |
| **n** | Number of samples (patients): 254. |
| **p** | Number of features (genes): 20,531. |
| **"Small n, large p" (p ≫ n)** | Many more features than samples. The model can find patterns that are just coincidences. This is the core challenge of gene-expression ML. |
| **Multiclass** | More than two possible answers. We have 6. |
| **Class imbalance** | Some classes have far more samples than others (LMS 104 vs MPNST 9). |
| **Majority / minority (rare) class** | The biggest class (LMS) / the smallest classes (MPNST, SS, MFS). |
| **Training data** | The data a model learns from. |
| **Test data / held-out data** | Data the model never saw during learning. Used only to score it. |
| **Validation data** | Data used *during development* to choose settings, separate from the final test data. |
| **Fit** | Let a step learn from data (e.g. a scaler learns the mean of each gene; a model learns its weights). |
| **Transform** | Apply what was learned to new data without learning anything new. |
| **Predict** | Ask the fitted model for an answer on new data. |
| **Refit** | Fit again from scratch, usually on a larger training set, after choosing the best settings. |
| **Pipeline** | A chain of steps run in order: e.g. filter → scale → select genes → classify. The whole chain is fitted together on training data only. |
| **Configuration / config** | One fully specified pipeline with all its settings, e.g. `SVM-STD-ANOVA-150-LINEAR`. |
| **Parameter** | A value the model learns itself from data (e.g. weights). |
| **Hyperparameter** | A setting *we* choose before training (e.g. C, k, number of trees). Chosen by testing several values. |
| **Grid / grid search** | Try every combination of a list of hyperparameter values and keep the best. `GridSearchCV` in scikit-learn does this with cross-validation. |
| **Candidate** | One hyperparameter combination in the grid. G = number of candidates. |
| **Overfitting** | The model memorises training data, including noise, and performs worse on new data. Big risk when p ≫ n. |
| **Generalization** | How well a model works on new, unseen data. What we really care about. |
| **Regularization** | A penalty that keeps the model simple to prevent overfitting. |
| **L2 (ridge) penalty** | Shrinks all weights towards zero but keeps every gene. |
| **L1 (lasso) penalty** | Pushes many weights to exactly zero, so the model uses only a few genes (built-in gene selection). |
| **Elastic-net (EN)** | A mix of L1 and L2. `l1_ratio` sets the mix (0 = pure L2, 1 = pure L1). |
| **C** | In SVM and logistic regression: the inverse of regularization strength. **Small C = strong regularization (simpler model); large C = weak regularization (fits training data more tightly).** |
| **Supervised vs unsupervised** | *Supervised* steps use the labels (e.g. ANOVA picks genes that differ between subtypes). *Unsupervised* steps do not (e.g. keep genes with high variance). Supervised steps carry more leakage risk. |
| **Seed / random state** | A number that fixes randomness so results can be reproduced exactly. We use 42. |
| **Convergence / ConvergenceWarning** | Some models train step by step until they "settle". If they stop before settling, scikit-learn warns. We treat every warning as an error to review. |
| **`max_iter`, `tol`** | Maximum number of training steps, and how small a change counts as "settled". |
| **Solver (`lbfgs`, `saga`)** | The algorithm that trains a logistic regression. `lbfgs` is fast for L2; `saga` supports elastic-net but is slower. |
| **scikit-learn (sklearn)** | The Python ML library we use (pinned to 1.7.2). |
| **imbalanced-learn (imblearn)** | A library that adds SMOTE and a pipeline that supports resampling. |
| **Baseline** | A simple reference model. If a fancy model cannot beat it, the fancy model is not useful. |
| **Benchmark** | A fair, standardised comparison of several methods on the same data and tests. |
| **Ablation** | Remove or change one part of a pipeline to see how much that part matters. |
| **Interpretability** | Understanding *why* the model predicts what it does (e.g. which genes have big weights). |

---

## 7. Pipeline stages (S1–S5)

Protocol 3.0 builds every pipeline from these stages, in this order:

`log2(x+1) → S1 filter genes → S2 scale → S3 select/extract features → S4 handle imbalance → S5 classifier`

### S1 — Unsupervised gene filtering (fewer, more useful genes, without looking at labels)

| Code / term | Meaning |
| --- | --- |
| **F0 `VarianceThreshold(0)`** | Remove genes that have the same value in every training sample (they carry no information). Used in Round 1. |
| **F1 Low-expression filter** | Keep a gene only if `log2(x+1) > 1` in at least 5 training samples. Removes genes that are basically "off". The threshold is an absolute count (5), not a percentage, so genes active only in tiny classes (MPNST, SS) are not thrown away. |
| **Variance** | How spread out a gene's values are across samples. |
| **MAD (median absolute deviation)** | A measure of spread like variance, but less affected by extreme values. |
| **F2 = F1 + top-5000 by MAD** | After F1, keep the 5,000 genes that vary the most. Must be computed on the log2 scale, before scaling. |

### S2 — Scaling (put genes on comparable scales)

| Code / term | Meaning |
| --- | --- |
| **Z1 `StandardScaler`** | For each gene: subtract its mean, divide by its standard deviation (z-score). Every gene then has mean 0 and SD 1. Default for SVM, LR, kNN. |
| **`MinMaxScaler`** | Rescale each gene to the range 0–1. Used in Round 1 only. |
| **Z0 No scaling** | Tree models (RF, LightGBM) do not care about scale. |

### S3 — Feature selection or extraction (focus on informative genes)

| Code / term | Meaning |
| --- | --- |
| **Feature selection** | Pick a subset of the original genes. You can still name them. |
| **Feature extraction** | Build new combined features from all genes (e.g. PCA). They are no longer single genes. |
| **R0 No selection** | Use all filtered genes and let regularization decide. |
| **R1 ANOVA-F / `SelectKBest(f_classif)`, k** | For each gene, an ANOVA F-test asks: "Is this gene's average clearly different between subtypes?" Keep the top **k** genes. Supervised, so it must be done inside each training fold. |
| **ANOVA** | "Analysis of variance": a statistical test of whether group averages differ. |
| **R2 PCA (principal component analysis)** | Compresses all genes into a few "components" that capture the most variation. Round 1 only; the first components were dominated by LMS and did worse than ANOVA (≈0.70–0.72 vs 0.77). |
| **Component** | One PCA output: a weighted mix of all genes. |
| **R3 Marker panel** | A fixed list of known marker genes. Interpretation only (see section 4 warning). |
| **mRMR, SVM-RFE, Boruta** | More complex selection methods ("wrapper"/"embedded"). Excluded: research shows they do not beat simple filters and they overfit easily. |
| **Filter / wrapper / embedded methods** | *Filter*: score each gene alone (ANOVA). *Wrapper*: repeatedly train models to pick genes (RFE). *Embedded*: selection happens inside model training (L1). |
| **AE / VAE (autoencoder / variational autoencoder)** | Neural networks that compress data. Excluded: no gain with small data. |
| **GSVA / ssGSEA** | Turn gene expression into pathway or gene-set scores. Postponed to a later round. |
| **TabPFN** | A pre-trained model for small tables. Postponed. |
| **Hierarchical (two-level) classification** | First predict a group (e.g. "UPS/MFS"), then the subtype inside it. Postponed. |

### S4 — Handling class imbalance

| Code / term | Meaning |
| --- | --- |
| **I0 Nothing** | Train as is. Round 1 reference. |
| **I1 `class_weight="balanced"`** | Make mistakes on small classes "cost more" during training, in proportion to how rare the class is. Our default. |
| **Cost-sensitive learning** | The general idea behind I1: different errors get different costs. |
| **I2 Prior / threshold shift (α)** | After the model gives probabilities, divide each class's probability by its frequency raised to α. α = 0 changes nothing; α = 1 fully corrects for class frequency. One α is tuned, not 6 separate thresholds, because inner folds only have ~5 MPNST. |
| **Prior (π)** | How common a class is before seeing any data (e.g. LMS ≈ 41% of training data). |
| **Decision threshold / cut-off** | The probability level at which the model says "this class". Moving it changes the trade-off between classes. |
| **I3 SMOTE** | Creates synthetic (fake) samples for small classes by mixing neighbouring real samples. Used only as a **negative control**: research says it barely helps with high-dimensional data. Must run only during fitting, after feature selection. |
| **`k_neighbors`** | How many neighbours SMOTE mixes. Must be smaller than the smallest class in the training fold, so we fix it at 3. |
| **Oversampling / undersampling** | Add samples to small classes / remove samples from large classes. Random undersampling is excluded because it would throw away ~90% of LMS. |
| **I4 Balanced bootstrap (`balanced_subsample`)** | In random forest, each tree is trained on a sample re-balanced between classes. |

### S5 — Classifier

See section 8.

---

## 8. Classifiers (models)

| Code | Model | Simple explanation | Role in protocol 3.0 |
| --- | --- | --- | --- |
| **C0** | **DummyClassifier** | Ignores the genes. `most_frequent` always predicts LMS (macro-F1 ≈ 0.097). `stratified` guesses randomly in proportion to class sizes (≈ 0.167). | The **floor**: any real model must beat it. |
| **C1** | **SVM / SVC (support vector machine)** | Draws boundaries between classes that leave the widest possible gap ("margin"). | Candidate; links to Round 1. |
| — | **Linear kernel** | The boundaries are straight lines/planes. Works well when p ≫ n. | Used. |
| — | **RBF kernel** | Allows curved boundaries. `gamma` controls how local each sample's influence is. Round 1: no better than linear, ~2.2× slower. | Round 1 only. |
| **C2** | **Logistic regression (LR), multinomial, L2** | Learns a weight per gene per class and turns the weighted sum into probabilities for all 6 classes at once. | Candidate. |
| **C3** | **LR elastic-net** | Same, with an L1+L2 penalty, so it also selects genes. | **Main candidate**. |
| **C4** | **PAM / nearest shrunken centroids (NSC)** | Computes the average profile (centroid) of each class, shrinks unimportant genes towards zero, then assigns a sample to the closest centroid. `shrink_threshold` controls how much shrinking. A classic gene-expression method. | Omics baseline. |
| **C5** | **Random forest (RF)** | Many decision trees, each trained on a random sample; they vote. `max_features`, `min_samples_leaf`, `n_estimators` are its settings. | Non-linear baseline. |
| **C6** | **kNN (k-nearest neighbours)** | Predicts the class most common among the k most similar training samples. | Simple baseline. |
| **C7** | **LightGBM** | Gradient boosting: builds trees one after another, each fixing the previous ones' mistakes. Similar to XGBoost. | Optional, exploratory. |
| — | **MLP / deep learning** | Neural networks. Excluded: they need far more than 300 samples. | Excluded. |
| — | **One-vs-rest (OVR)** | Turning a 6-class problem into 6 "this class vs all others" problems. Used when reading SVM weights per class. | — |
| — | **Decision tree** | A flowchart of yes/no questions on gene values. Building block of RF and boosting. | — |
| — | **Ensemble** | Combining several models' predictions. | Option for the app (D11). |
| — | **Calibration / calibrated score** | Adjusting a model's scores so "0.9" really means "right about 90% of the time". | Needed for the app; fitted only on inner data. |

---

## 9. Validation: how we test models fairly

| Term | Meaning |
| --- | --- |
| **Cross-validation (CV)** | Split the data into parts ("folds"). Train on all but one fold, test on the held-out fold, rotate until every fold has been the test once. Every patient gets tested exactly once per round. |
| **Fold** | One part of the split. |
| **k-fold** | CV with k folds. We use 5 outer and 4 inner. |
| **Stratified** | Each fold keeps roughly the same class proportions as the full data, so every fold contains some MPNST and SS. |
| **Repeated CV** | Run the whole CV several times with different shuffles. We repeat the outer CV 3 times (5 folds × 3 repeats = 15 outer splits). |
| **Nested CV** | CV inside CV. The **outer** loop measures performance; the **inner** loop, run only inside each outer training set, chooses hyperparameters. This stops the tuning from "peeking" at the test data. |
| **Outer train / outer test** | ~203 patients used to develop a model / ~51 patients used only for the final score of that fold. |
| **Inner train / inner validation** | Inside outer train: ~152 patients to fit candidates / ~51 to score them. |
| **Held-out prediction** | A prediction for a patient the model never trained on. Each config produces 254 × 3 = 762. |
| **`outer.csv` / `inner.csv`** | Saved split assignments that every member and every pipeline reuses, so results can be compared patient-by-patient. Protected by checksums. |
| **Paired comparison** | Because all pipelines use the same splits, we can compare them fold by fold (pipeline A vs B on the *same* patients). This is much more precise. |
| **Data leakage** | Information from test data sneaks into training (e.g. computing ANOVA on all 254 patients before splitting). Scores look great but are fake. The protocol lists 10 rules (L1–L10) to prevent it. |
| **"Fit inside the fold"** | Every step that learns anything (filter, scaler, ANOVA, SMOTE, model) learns only from the training part of each fold, then is applied to the test part. |
| **Selection bias / optimistic bias** | If you try many pipelines and report the best one's score on the same test data, that score is too high, partly due to luck. "Choosing with the exam, then grading with the same exam." |
| **Winner's curse** | The same idea: the top scorer among many is usually overestimated. |
| **Grouped CV / `StratifiedGroupKFold`** | Keeps all samples of a group (e.g. one hospital/TSS) in the same fold. Tests whether the model learned the hospital rather than the biology (sensitivity analysis S-TSS). |
| **OOF (out-of-fold) predictions** | Predictions made on held-out folds, pooled together. |
| **Independent / external validation** | Testing on a completely different set of patients (another hospital or study). We do **not** have this; re-splitting the same 254 patients is not independent validation. |
| **Hold-out split** | A single train/test split. Less reliable than repeated CV with small data. |

---

## 10. Metrics: how we score models

| Term | Meaning |
| --- | --- |
| **Confusion matrix** | A 6×6 table: rows = true subtype, columns = predicted subtype. The diagonal holds correct predictions; everything else shows which classes get mixed up (e.g. MFS predicted as UPS). |
| **True/false positive/negative (TP, FP, TN, FN)** | For one class: correctly flagged / wrongly flagged / correctly not flagged / missed. |
| **Precision** | Of the samples predicted as class X, how many really are X? "When it says MPNST, is it right?" |
| **Recall (sensitivity)** | Of the samples that really are X, how many did the model find? "Of all MPNST, how many did it catch?" |
| **Specificity** | Of the samples that are *not* X, how many were correctly *not* called X. |
| **F1 score** | Combines precision and recall into one number (their harmonic mean). 1 = perfect, 0 = useless. |
| **Support** | How many true samples a class has (e.g. MPNST support = 9). |
| **Accuracy** | Percentage of all predictions that are correct. Misleading with imbalance: always guessing LMS gives 41%. |
| **Macro-F1** | Compute F1 for each class, then take the plain average. Every subtype counts equally, so MPNST matters as much as LMS. **Our main metric.** |
| **Micro-F1** | Pools all predictions first; dominated by the big classes. Not used as main metric. |
| **"Pooled" macro-F1 per repeat** | We gather all 254 held-out predictions of one repeat and compute macro-F1 once, rather than averaging fold scores. Then we report mean and SD across the 3 repeats. |
| **Per-fold macro-F1** | Macro-F1 for each of the 15 outer folds separately. Used for statistical tests in protocol 3.0. |
| **Balanced accuracy (BA)** | The average of the recall of each class. |
| **MCC (Matthews correlation coefficient)** | A single score from the whole confusion matrix, from −1 (always wrong) through 0 (random) to +1 (perfect). Robust to imbalance. Added in protocol 3.0. |
| **Mean / SD (standard deviation)** | Average / how much values vary. The SD across our 3 repeats shows split-to-split variation; it is **not** a confidence interval, because the repeats reuse the same patients. |
| **Confidence interval (CI)** | A range that likely contains the true value. Wide when data is small. |
| **Wilson CI** | A method for the CI of a proportion (like recall) that works well with tiny counts such as 9 MPNST. |
| **`zero_division=0`** | If a fold has no predictions for a class, precision for that class would be 0/0. This setting defines it as 0 instead of raising a warning. |
| **AUROC** | Area under the ROC curve, a ranking quality score (0.5 = random, 1 = perfect). Seen in research, not our main metric. |
| **Brier score** | Measures how good predicted probabilities are. Seen in research. |
| **Runtime** | Time a run takes. Only comparable between runs on the same machine. |

---

## 11. Statistics for comparing pipelines

| Term | Meaning |
| --- | --- |
| **Statistical significance / p-value** | A way to judge whether a difference is real or could be luck. Small p-value (e.g. < 0.05) = unlikely to be luck. |
| **t-test** | A standard test for whether an average difference is different from zero. |
| **Corrected resampled t-test (Nadeau & Bengio)** | A t-test fixed for repeated CV. Normal t-tests are over-confident because CV folds share training patients; the correction enlarges the uncertainty. |
| **Bayesian correlated t-test (Benavoli 2017)** | Gives three probabilities directly: P(A better), P(practically equal), P(B better). Easier to read than a p-value. |
| **ROPE (region of practical equivalence)** | A band of differences too small to matter. We use ±0.01 macro-F1: differences inside it are "practically the same". |
| **ρ (rho)** | Correlation between folds caused by overlapping training data; ≈ n_test/n ≈ 0.2. Used by the Bayesian test. |
| **df (degrees of freedom)** | A technical number in a t-test; here 15 folds − 1 = 14. |
| **Multiple comparisons** | Running many tests means some will look "significant" by chance. |
| **Holm correction** | A method that adjusts p-values when running many tests, to keep false alarms under control. |
| **Effect size** | How big a difference is, not just whether it exists. With 15 folds, differences below ~0.03–0.05 will usually not be significant. |
| **"No difference" is a valid result** | If two pipelines are statistically equivalent, we report that honestly, and prefer the simpler one. |

---

## 12. Protocol, workflow, and repository terms

### Rounds and protocols

| Term | Meaning |
| --- | --- |
| **Protocol** | The written, agreed rules for running experiments, so everyone does the same thing. |
| **Protocol 2.0** | The current rules (11 Oct 2026) for Round 1: 24 SVM configurations, 4 members × 6 each. |
| **Protocol 3.0 (proposal)** | Draft rules for the next round: 13 core + 2 optional pipelines from several model families. |
| **Round 1** | The SVM experiment under protocol 2.0. Best macro-F1 ≈ 0.77 (Standard scaler + ANOVA 150 + linear SVM). |
| **Configuration ID (e.g. `SVM-MM-ANOVA-50-LINEAR`)** | Model – scaler (MM = min-max, STD = standard) – reduction – size – kernel. |
| **Fit count** | How many times pipelines are trained. Per repeat: 5 × (4·G + 1). Protocol 2.0 total 18,360; protocol 3.0 core ≈ 6,915. |

### Protocol 3.0 vocabulary

| Term | Meaning |
| --- | --- |
| **Stage (S1–S5)** | One step type in the pipeline (section 7). |
| **P01–P15** | The 15 pipeline IDs in the shortlist (e.g. P02 `R1-REF`, P07 `LR-EN-BAL`). |
| **Role** | Why a pipeline is in the list. Instead of trying every combination ("full factorial"), each pipeline answers one question. |
| **Floor (sàn)** | P01 Dummy: the score you get without learning anything. |
| **Reference / baseline (tham chiếu)** | A known point to compare against, e.g. P02 reproduces Round 1. |
| **Ablation** | A pipeline that changes exactly one stage compared with its partner, to measure that stage's effect. |
| **Candidate (ứng viên)** | A pipeline that could become the winner. |
| **Main candidate** | P07 (LR elastic-net), the research's top recommendation. |
| **Negative control (đối chứng âm)** | Something we expect *not* to help (P10 SMOTE). It checks our expectations and shows the method is reported fairly. |
| **Exploratory / optional** | Run only if time allows (P14, P15). |
| **Full factorial** | Trying every combination of every option. Too expensive and adds selection bias. |
| **Regression test** | Checking that new code reproduces old results. P02 must reproduce 0.772 exactly. |
| **Ablation map** | The diagram showing which pipeline differs from which, and in which stage. |
| **Smoke run** | A tiny trial run (1 outer fold) to catch errors and measure time. Not an official result. |
| **Round A — screening** | First pass: run repeat 1 for all pipelines, look only at technical health and inner scores. |
| **"Blind to outer" / sealed (mù outer / niêm phong)** | During screening, outer test predictions are saved but nobody looks at their scores, so nobody can be influenced by them. |
| **Grid-edge rule** | If the chosen hyperparameter sits at the edge of the grid in ≥3 of 5 outer folds, extend the grid by one step, once, then freeze. |
| **Freeze / frozen config (đóng băng), tag `p3.0-frozen`** | Lock all settings with a Git tag before the official run. Nothing may change after this. |
| **Pre-registration** | Writing down in advance what you will run and compare, so you cannot change the plan after seeing results. |
| **Round B — official** | Run repeats 2 and 3 with frozen settings, then unseal and analyse. |
| **META-SELECT** | Our main reported number. In each outer fold, pick the best (pipeline, settings) pair using **inner** scores only, and take its outer predictions. This gives an almost unbiased score for the whole process "pick the best pipeline", with no extra training needed. |
| **Selection frequency** | How often each pipeline wins across the 15 outer folds. Shows stability. |
| **Tie-break order / "simplest first"** | A pre-declared order from simplest (P11 PAM) to most complex (P14 LightGBM) used to break ties. |
| **Equivalence set** | All pipelines not clearly worse than the top one (P(top better beyond ROPE) < 0.95). |
| **"Simplest in the equivalence set"** | The rule for choosing the pipeline for the app: among equally good pipelines, pick the simplest. Its score is reported using META-SELECT, not its own outer score. |
| **Confirmation run with a new seed** | Re-running the top 2–3 with a different outer split. Reduces "lucky split" risk but is still not independent validation. |
| **Sensitivity analysis (phân tích độ nhạy)** | Re-running under changed assumptions to see if conclusions hold. |
| **S-TSS** | Group outer folds by hospital (TSS). A big drop means the model learned the hospital. |
| **S-206** | Use only the 206 expert-reviewed cases. If MPNST/MFS recall rises, label noise was a key problem. |
| **S-5CLASS** | Merge MFS + UPS into one class (5 classes). If the score jumps, much of the error is the biological boundary. |
| **Leakage rules L1–L10** | The list of anti-leakage constraints and their checks (section 6 of the proposal). |
| **Q1–Q12** | Open decisions for the team in protocol 3.0. |
| **W0–W6, W4a–d** | Workstreams (work packages): W0 coordination, W1 engine, W2 statistics, W3 data & labels, W4 running batches, W5 interpretation, W6 documentation & citations. |
| **Engine / runner** | The code that runs pipelines through nested CV and writes results. |
| **Model registry** | A list in code describing every available pipeline, so the runner can run any of them. |
| **Transformer (sklearn)** | A pipeline step with `fit` and `transform` (e.g. `LowExpressionFilter`, `MADSelector`). Not the AI "Transformer" architecture. |
| **Nogueira Φ (stability)** | A score of how similar the selected gene lists are across folds. Stable selection is easier to trust. |
| **Error audit** | Checking misclassified samples by hand against markers (e.g. high MDM2 in a "UPS" sample suggests a mislabelled DDLPS). |
| **Model card** | A short document describing a model's purpose, data, performance, and limits. |

### Research report conventions

| Term | Meaning |
| --- | --- |
| **R1 / R2 / R3** | Our research reports: R1 = catalogue of methods, R2 = baselines from the literature, R3 = sarcoma subtype biology. |
| **`[R1§4]`** | Citation format: section 4 of R1. |
| **[UNVERIFIED]** | A claim not yet checked against the original source. Must be checked (W6) before it goes into a report. |
| **DOI / PMID / PMCID** | Permanent IDs for papers (DOI = any publisher; PMID/PMCID = PubMed / PubMed Central). |
| **Preprint / conference abstract** | Not fully peer reviewed; weaker evidence. |
| **Peer review** | Expert checking before a paper is published. |
| **DKFZ sarcoma classifier** | A real clinical tool (Koelsche 2021) that diagnoses sarcoma subtypes from DNA methylation using random forest. Not directly comparable to our RNA task. |
| **CINSARC** | A 67-gene test that predicts metastasis risk (prognosis, not subtype). |
| **OTTER** | A pan-cancer RNA-seq classifier (mostly paediatric). Reports micro-F1, so not comparable. |
| **t-SNE** | A method for drawing high-dimensional data in 2D to see clusters. |
| **iCluster / clustering** | Grouping samples by similarity without labels. TCGA's clusters split UPS/MFS by DNA changes, not by their labels. |

### Repository and engineering

| Term | Meaning |
| --- | --- |
| **Run / run folder** | One execution of one configuration: `results/svm/<CONFIG>/<RUN_ID>/` with `config.json`, `predictions.csv`, `metrics.json`, `search_results.json`, `warnings.log`, etc. |
| **`search_results.json`** | All inner-CV candidate scores for every outer fold. Required for META-SELECT. |
| **Manifest** | A file recording what produced a result: commit, hashes, settings, runtime, machine. |
| **Checksum / hash / SHA-256** | A fingerprint of a file. If even one byte changes, the fingerprint changes. Used to prove data and splits were not altered. |
| **CRLF / LF** | Line-ending styles (Windows vs Mac/Linux). They change file bytes, and therefore hashes (decision D6). |
| **Commit / clean working tree** | A saved Git snapshot / no uncommitted changes. Official runs must use the agreed commit with a clean tree. |
| **Tag** | A named Git snapshot, e.g. `svm-p2.0`, `p3.0-frozen`. |
| **Validator** | `validate_svm`: independently re-checks a run (recomputes metrics, re-checks the chosen parameters and hashes). |
| **Submission / submission register** | A member's handed-in run / the CSV recording each run's review status (`pending_review`, `accepted`, `needs_rerun`, `superseded`). |
| **Smoke / development run** | Test runs that do not count as official submissions. |
| **Provenance** | The record of where data and results came from. |
| **ADR (architecture decision record)** | A short document recording a technical decision and its reasons. |
| **D1–D16** | Decisions listed in `architecture.md`. |
| **Three products** | Experiments, paper, and app (planned Streamlit demo labelled "research only"). |

---

## 13. Vietnamese ↔ English terms in our docs

| Vietnamese (in docs) | English |
| --- | --- |
| bệnh nhân / ca | patient / case |
| lớp, lớp hiếm | class, rare (minority) class |
| nhãn, nhiễu nhãn | label, label noise |
| biểu hiện gene | gene expression |
| lọc gene không giám sát | unsupervised gene filtering |
| chọn / trích đặc trưng | feature selection / extraction |
| mất cân bằng lớp (imbalance) | class imbalance |
| chuẩn hoá, biến đổi | normalization, transformation |
| phân tầng | stratified |
| gộp (dự đoán gộp) | pooled (pooled predictions) |
| sàn | floor (lowest reference) |
| tham chiếu | reference |
| ứng viên (chính) | (main) candidate |
| đối chứng âm | negative control |
| tuỳ chọn | optional |
| vòng A / vòng B | round A (screening) / round B (official) |
| mù outer, niêm phong | blind to outer, sealed |
| đóng băng config | freeze the config |
| đăng ký trước | pre-registered |
| chệch / thiên lệch do chọn mô hình | (selection) bias |
| lạc quan (kết quả lạc quan) | optimistic (over-estimated) |
| khoảng tin cậy | confidence interval |
| kiểm định | statistical test |
| tương đương thực tế | practically equivalent (inside ROPE) |
| phân tích độ nhạy | sensitivity analysis |
| trần sinh học | biological ceiling |
| phổ liên tục | continuous spectrum |
| biệt hoá (kém biệt hoá) | differentiation (poorly differentiated) |
| cơ trơn | smooth muscle |
| khuếch đại | amplification |
| hội tụ | convergence |
| biên grid | grid edge |
| hoà điểm | tie |
| rò rỉ dữ liệu (leakage) | data leakage |
| diễn giải | interpretation |
| khối lượng (công việc) | workload |

---

## 14. Common questions

**Why not just use accuracy?**
Because a model that always says "LMS" already gets 41% accuracy while being useless for 5 of 6 subtypes. Macro-F1 treats every subtype equally.

**Why is MFS vs UPS so bad, and can a better model fix it?**
Probably not much. Several studies show they are one biological spectrum, separated mainly by how a tissue looks under the microscope (amount of myxoid stroma), not by genes. Some labels may also be wrong. The S-5CLASS and S-206 analyses test this.

**Why can't we look at outer test scores during screening?**
If we adjust anything after seeing test scores, the test is no longer a fair, unseen test, and the final score becomes optimistic.

**Why not report the best pipeline's own score?**
Picking the best of 13 on the same test data inflates its score by luck. META-SELECT includes the choosing step inside the cross-validation, so its score is honest.

**Why is the SD across repeats not a confidence interval?**
The 3 repeats reshuffle the same 254 patients, so they are not independent samples. The SD shows sensitivity to how we split, not uncertainty about new patients.

**Why don't we use the published marker genes as inputs?**
They were discovered on this same TCGA dataset, so using them would let test information leak into training and give an over-optimistic score.

**Why so few hyperparameter values in the grid?**
Each inner validation fold has only 1–2 MPNST patients. Large grids let the selection chase noise in those few patients.
