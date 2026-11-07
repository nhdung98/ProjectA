# PCA order with automatic CSV results

Scope: PCA order only. No Random Forest, Logistic Regression, ANOVA, new class weighting, or new feature counts. This is the current experiment protocol. The [archived SVM protocol](../../week01/docs/experiment_protocol.md) records the earlier round.

## Scientific comparison

Compare these complete pipelines:

1. `log2(x+1) -> training-only constant filter -> scaling -> PCA -> SVM` (control).
2. `log2(x+1) -> training-only constant filter -> PCA -> scaling -> SVM` (new order).

The second order scales **components**, not original genes. PCA still centers its inputs internally. Moving scaling changes both the PCA representation and the scale presented to SVM; this is a comparison of complete pipeline orders, not an isolated test of only one of those effects. Whitening stays off in both orders.

Reuse the same 254 patients, saved outer/inner splits, seeds, PCA settings, SVM settings and C/gamma grids. Both orders fit inside every inner training fold, then refit on outer training data. Do not fit PCA before cross-validation.

## Assignments

| Member | Scaler | Kernel | Component counts | Orders | Configurations |
| --- | --- | --- | --- | --- | ---: |
| 1 | Standard | Linear | 50, 100, 150 | Both | 6 |
| 2 | Standard | RBF | 50, 100, 150 | Both | 6 |
| 3 | Min-max | Linear | 50, 100, 150 | Both | 6 |
| 4 | Min-max | RBF | 50, 100, 150 | Both | 6 |

This deliberately reruns 12 control configurations and adds 12 reversed-order configurations. Each member produces matched pairs on one computer. Earlier submissions are context, not inputs to this round's CSV collector. Member numbers are experiment assignments, not the seven-person Group 1 roster.

Each member produces 90 outer evaluations and 4,572 held-out predictions. Linear members perform 1,890 model fits each; RBF members perform 7,290 each because their tuning grids are larger. Equal configuration counts do not imply equal runtime. Team total: 24 configurations, 18,360 model fits, 18,288 held-out predictions.

## Release and setup

The leader must commit and publish this runner, its tests, protocol and `configs/pca_order.json` together, then distribute **one exact reviewed commit SHA**. Members check out that commit in a clean clone. Do not start official runs from an uncommitted working copy. The collector must use the same release commit and pinned environment.

Use Python 3.12 and the existing pinned packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-experiments.txt
python -m src.data.prepare
python -m src.experiments.pca_order check
```

The check verifies the environment, source data, prepared values and existing saved split files. Members do not create new splits. The runner is sequential and uses one numerical thread, matching the prior protocol.

## One command per member

Member 1 runs:

```powershell
python -m src.experiments.pca_order run --member 1
```

Members 2, 3 and 4 replace the final number. No model settings, metric calculations, filenames, plots, notebooks, ZIPs or RARs need to be created manually.

Each member gets **one completed CSV** at a fixed path:

```text
results/pca_order/member1_results.csv
results/pca_order/member2_results.csv
results/pca_order/member3_results.csv
results/pca_order/member4_results.csv
```

Each file has **4,572 prediction rows**, covering six configurations, three repeats and all 254 patients. Each row records:

- Configuration ID, member, scaler, kernel, component count and PCA order.
- Repeat, outer fold, sample/patient IDs, actual subtype and predicted subtype.
- Selected C/gamma, winning inner macro-F1, fold sample counts, retained-feature count, runtime and total PCA explained variance.
- Protocol, exact commit, code/data/split identities, package versions, run ID, start time and completion state.
- An embedded canonical-text checksum for detecting accidental edits without a separate checksum file.

Gamma is the literal string `NA` for linear SVM. No summary, metadata, log, status or archive file is required from a member. The collector calculates scores directly from the predictions.

### Completion, interruption and existing files

While running, the runner writes `member1_results.partial.csv`, checkpointing after each completed outer fold. It may briefly use a `.tmp` file during an atomic checkpoint write. Neither is a submission.

After all assigned configurations finish, the runner checks the complete CSV and publishes `member1_results.csv`. Successful completion leaves **only that final CSV** for the member. Publication uses a same-filesystem hard link followed by removal of the partial name: it is atomic and refuses an existing destination. The results filesystem must support hard links (for example, a normal NTFS checkout); unsupported publication fails and preserves the partial checkpoint rather than falling back to an unsafe overwrite.

A warning, training failure or interruption stops the run and retains the partial checkpoint. A force-killed process might leave a `.tmp` file; the previous partial checkpoint remains the authoritative diagnostic file. The collector rejects partial filenames and incomplete content.

Both an existing final file and an existing partial run block a new run. There is no automatic overwrite or resume. Preserve or explicitly move a previous file before intentionally rerunning, and record the reason. Never select a retry because its score is higher. The exclusive partial-file reservation prevents two member commands from writing the same result concurrently.

**Handoff:** send only `memberN_results.csv`, without ZIP/RAR packaging. Upload/download the original CSV; do not open and resave it in Excel. Local saving does not automatically transfer it to the leader or GitHub.

## Leader: collect four CSVs

Place the four final CSVs in `results/pca_order/` on the leader's computer, or provide their actual paths. No other member files are needed.

```powershell
python -m src.experiments.pca_order collect results/pca_order/member1_results.csv results/pca_order/member2_results.csv results/pca_order/member3_results.csv results/pca_order/member4_results.csv --output results/pca_order/comparison-01
```

Use the same reviewed commit and pinned environment. Provide exactly one CSV per member and a new output directory. The collector validates all inputs before writing the comparison. It rejects:

- Partial/incomplete CSVs, duplicate members, wrong assignments and missing configurations.
- Failed checksums, mismatched commit/code/data/splits/packages, and mixed run identities.
- Missing, duplicate or incorrectly assigned predictions, patient IDs and actual labels.
- Unknown predicted labels, nonfinite numeric fields, invalid sample counts, impossible PCA variance, inconsistent fold evidence, and C/gamma outside the agreed grid.

It independently calculates:

- `team_summary.csv`: 24 configuration rows with metric means and sample SDs.
- `paired_order_comparison.csv`: 12 matched comparisons; positive deltas favor PCA before scaling.
- `team_repeat_scores.csv`: 72 repeat-level macro-F1 and balanced-accuracy rows.
- `team_subtypes.csv`: subtype precision, recall, F1 and support per repeat.
- `team_confusions.csv`: confusion matrices per configuration and repeat.
- `sources.csv`: selected input paths, byte checksums and run IDs.

These are leader-generated analysis outputs. Members still hand over just one CSV each. Keep their four CSVs as the original evidence; the collector does not modify them.

## Interpretation and verification limits

Macro-F1 is primary; balanced accuracy and subtype scores remain required. Compare both orders using the same scaler, kernel and component count. Report repeat scores and subtype effects, especially MFS/UPS and the small SS/MPNST groups. Repeats reuse patients; sample SD is not a confidence interval. Do not claim clinical validation or significance from descriptive mean differences.

Automatic checks establish consistency and completeness of prediction evidence, not execution authenticity. The single CSV records selected parameters and the winning inner score, but does not contain every candidate score. The collector verifies that C/gamma belong to the agreed grid; it cannot independently prove that those parameters won the search or reconstruct every inner fit. The runner selects them using the reviewed GridSearchCV implementation. Embedded hashes detect accidental changes but are not signatures and can be recomputed by someone editing a file. Retain one peer reproduction as a separate scientific check. Runtime is not a controlled cross-member benchmark.
