# Standardized Protocol 2.0 workflow

This interface implements the existing [scientific design](../archive/week01/docs/experiment_protocol.md). It does not authorize a training batch or claim human approval. Vỹ operates the experiment machine; Dung and the team review results. New evidence is separate from historical recovery and later Protocol 3.0 work.

Official execution is planned for native Windows. Follow [the Windows operator guide](protocol2_windows.md) for reviewed-release checkout, environment setup and all PowerShell commands. macOS tests are development evidence only.

## Environment and preflight

Use Python 3.12 and the isolated environment in the root README. On Windows replace `.venv/bin/python` with `.venv\Scripts\python.exe`; on Linux use the macOS form. Training uses one numerical thread and sequential GridSearchCV. The lock preserves the six original scientific pins and adds transitive version pins. The workflow never modifies packages automatically.

```sh
.venv/bin/python -m src.experiments.workflow list
.venv/bin/python -m src.experiments.workflow prepare-data
.venv/bin/python -m src.experiments.workflow preflight
.venv/bin/python -m src.experiments.workflow preflight --official
```

Preflight verifies package versions, raw hashes, the frozen processed-file hash, every prepared measurement and mapped label, 254 unique patients, 20,531 gene records, class counts, and both saved split files against manifests and seed-derived assignments. `--official` also requires a clean committed checkout. Development preflight can pass with `git_dirty: true`, explicitly recorded. Failures exit nonzero.

Optional `--output results/protocol2-development/NEW-NAME.json` saves a new report, refusing existing files.

Preparation is explicit, never a run/preflight/resume side effect. It stages preparation with **CRLF TSV serialization**, checks the existing dataset hash, then publishes absent files. This addresses the documented macOS LF/CRLF issue without changing values or expected hashes. Existing files are not overwritten. A mismatch stops publication; investigate rather than edit manifests or regenerate splits.

## Smoke and scope selection

```sh
.venv/bin/python -m src.experiments.workflow smoke --batch results/protocol2-smoke/setup-check-01
.venv/bin/python -m src.experiments.workflow run --configuration SVM-MM-ANOVA-50-LINEAR --batch results/protocol2/one-config-01
.venv/bin/python -m src.experiments.workflow run --branch standard-pca --batch results/protocol2/standard-pca-01
```

Smoke executes one real outer fold of one configuration with the full approved inner grid. Default: MinMax + ANOVA-50 + linear SVM. A different single ID can be selected. Smoke may use dirty development code, records that fact, and ends `smoke_only`. It has no official performance summary and cannot pass full-run validation or become official through resume.

Branch choices: `minmax-anova`, `standard-anova`, `minmax-pca`, `standard-pca`. Each selects six configurations. Repeated `--configuration` arguments select distinct individual IDs. Unknown/duplicate IDs are errors.

## Official batch after review

Keep one clean reviewed commit, environment, dataset, and machine throughout execution:

```sh
.venv/bin/python -m src.experiments.workflow run --all --batch results/protocol2/vy-official-01
```

This performs 24 configurations, 15 outer evaluations each, and 18,360 pipeline fits including inner search/refits. Each configuration gets a unique run ID. Existing batches are rejected. Omitting `--batch` creates and prints a timestamp/UUID path.

Training reuses the existing pipeline, candidate generation, inner split selection, temporary preprocessing cache, feature extraction and metric summarization. Each inner training fold fits the full pipeline; the winner refits on outer training data. Outer test samples never participate in tuning/preprocessing.

All nine required artifacts live under `BATCH/runs/CONFIGURATION/RUN_ID/`. Additional `.checkpoints/` files are restart transactions. Manifests add timestamps, mode, code/environment/data identities, numerical library versions, attempt history, seeds and validation status without removing legacy fields. Submission drafts always mark human review pending.

## Monitoring and safe restart

```sh
.venv/bin/python -m src.experiments.workflow status --batch results/protocol2/vy-official-01
.venv/bin/python -m src.experiments.workflow resume --batch results/protocol2/vy-official-01
```

Console output updates per completed outer fold. Status lists all planned configurations, committed-fold counts and validation status, and can run from another terminal.

Each completed fold is an immutable checksum-bearing transaction, saved only after predictions, search evidence and feature details pass consistency checks. Aggregate run files are atomic projections. A persisted `finalizing` state remains recoverable; `complete` is published only after independent validation and artifact sealing. All 15 verified checkpoints can be finalized with zero additional fits. Resume verifies provenance and every committed fold before skipping it. Interrupted uncommitted folds are recomputed. Temporary search caches are not restart evidence.

Warnings or failed candidates stop execution. Warnings remain visible and block automatic resume. Completed runs are revalidated and skipped, never silently retrained. Corruption or changed provenance stops restart. No command selects a retry because its score is higher.

Normal interruption releases `.writer.lock`; force-killing may leave it. After confirming the process stopped, inspect the recorded PID and use:

```sh
.venv/bin/python -m src.experiments.workflow unlock --batch results/protocol2/vy-official-01 --pid THE_RECORDED_PID
```

Unlock refuses a mismatched PID or a live process. A reused PID requires investigation. Publication prefers hard links and falls back to a same-directory staged copy/rename under an exclusive reservation. Unsupported replacement stops; stale publication reservations require operator inspection. A crash before initial run-manifest creation requires investigation rather than speculative recovery.

## Validation, reports and ZIPs

```sh
.venv/bin/python -m src.experiments.workflow validate --batch results/protocol2/vy-official-01
.venv/bin/python -m src.experiments.workflow report --batch results/protocol2/vy-official-01
.venv/bin/python -m src.experiments.workflow export --batch results/protocol2/vy-official-01 --audience team
```

Successful official run/resume automatically validates and reports. `validate` is read-only. Reporting/export requires the same clean release and environment. Full validation requires the recorded environment as well as the release. Another machine can run `verify-export --zip PATH` for byte integrity without claiming equivalent training or full provenance validation.

Outputs:

```text
summary.csv
comparison.csv
experiment_manifest.json
environment.txt
data_checksums.json
split_checksums.json
preflight_report.json
validation_summary.json
run_register.csv
reports/model_comparison.md
reports/subtype_analysis.csv
reports/confusion_matrices.csv
reports/repeat_scores.csv
runs/CONFIGURATION/RUN_ID/       # all nine required original new-run artifacts
evidence_bundle.zip             # aggregate-only external review
```

Subsets are reportable; a full comparison is declared only with all 24 valid configurations. The reference is Standard + ANOVA-150 + linear. If absent, deltas stay empty; historical scores are never substituted. Duplicate run IDs, unregistered folders, missing artifacts, hash changes and incomplete runs are rejected. Separate batches are not pooled automatically.

The external ZIP omits run folders, patient-level predictions and checkpoints. It retains aggregate subtype/confusion tables. Explicit team export produces `team_evidence_bundle.zip` containing all nine original artifacts, including the Protocol-required Sample ID/Patient ID columns. Keep it in the approved private team channel; do not upload it to external AI services. Neither ZIP includes raw/prepared expression data. Existing ZIP paths are refused; reports may be regenerated from validated runs, while an existing ZIP remains a preserved snapshot.

The legacy independent validator counts predictions to recalculate metrics independently of the runner's metric function. It checks search candidates/winners, assignments, retained genes, selected-gene counts, PCA dimensions/variance validity, hashes and completion. These checks establish consistency, not arbitrary edited files' execution authenticity. Hashes are not signatures; peer reproduction remains useful. ANOVA ranks and PCA variance values are not independently refitted during validation.

Comparison is exploratory/descriptive. Repeats reuse patients and overlapping training sets. The 15 outer evaluations are not independent observations; SD is not a confidence interval. Reports do not claim significance from highest means, clinical validity, or unbiased final performance after selecting a model from outer scores. Read MFS/UPS errors and minority SS/MPNST results alongside overall metrics.

## Validation & Tests contribution

Run `.venv/bin/python -m unittest discover -s tests -v`. Existing tests cover leakage, fold isolation, inner pipeline fitting, caching equivalence and independent metrics. New tests execute real searches on artificial data in temporary folders and check restart, warnings, corruption, duplicates, completeness, privacy exports and source identity. Synthetic fixtures never become research results. Real-data smoke stays separate.

Historical evidence is untouched. Member 4's recovered originals need no retraining; Member 3's historical gaps remain a separate recovery task. Providing a full-batch command does not authorize execution.

Workflow format is now version 2; old development smoke artifacts remain unchanged and are not migrated. ZIPs carry `EXPORT_CHECKSUMS.json`, with exact exported entry hashes separated from original source hashes. `verify-export --zip PATH` verifies them read-only. `export --output BATCH/new-name.zip` creates a new snapshot and never replaces an existing ZIP. External JSON copies omit local interpreter paths; original private artifacts are unchanged.
