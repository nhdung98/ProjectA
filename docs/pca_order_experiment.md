# PCA order with automatic CSV results

Scope: PCA order only. No Random Forest, Logistic Regression, ANOVA, new class weighting, or new feature counts. This is the current experiment protocol. The [archived SVM protocol](../archive/week01/docs/experiment_protocol.md) records the earlier round.

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

## Release and Windows setup

This development branch is preparation, not an approved official training release. Start it from `protocol2-v1.0` (`dc232eb6854ecbde4a2e5fabe629a8d630ff416f`). Do not change Protocol 2.0 evidence, grids or splits. After review, distribute one exact Protocol 3.0 commit SHA to all members and the collector. Do not update that checkout during a run or between resume sessions.

The CSV schema and scientific computations are unchanged. The resume context now also binds the full configuration, Python patch version, OS/architecture and scientific/transitive package versions. Legacy partial CSVs without this context are refused; no historical checkpoints are silently upgraded. Clean-checkout checks apply to check/run/validate/collect. An external approved SHA avoids a self-referential commit field in source code.

**Windows-only future runbook. Nothing here authorizes training on macOS.** Use a fresh local NTFS directory, outside OneDrive/Dropbox/network shares. The system temporary directory also needs private writable storage for joblib caches. No runtime/RAM/disk benchmark has been performed; verify available space on both volumes. Do not run multiple member jobs concurrently on the same PC without a resource review.

```powershell
$release = '<APPROVED_40_CHARACTER_PROTOCOL3_COMMIT>'
if ($release -notmatch '^[0-9a-f]{40}$') { throw 'Set the approved release first' }
git clone https://github.com/nhdung98/ProjectA.git ProjectA-protocol3
if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
Set-Location ProjectA-protocol3
git switch --detach $release
if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
function Assert-Release {
    $head = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $head.Trim() -ne $release) { throw 'Wrong release' }
    $dirty = git status --porcelain
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Checkout must be clean' }
}
Assert-Release
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed' }
$py = Join-Path $PWD '.venv\Scripts\python.exe'
& $py -m pip install -r requirements-protocol2-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $py -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
& $py --version
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
```

The existing lock includes the unchanged `requirements-experiments.txt` pins: NumPy 2.3.5, pandas 3.0.1, scikit-learn 1.7.2, SciPy 1.16.2, joblib 1.5.2 and threadpoolctl 3.6.0; it adds python-dateutil 3.0.0, six 1.17.0 and tzdata 2026.5. Use an agreed Python 3.12 patch/build and record it. Do not reuse an environment solely because Protocol 2.0 ran in it. Locks do not pin wheel hashes or guarantee identical BLAS builds; real Windows validation remains required. Resume refuses changes to its recorded versions/platform but is not a cryptographic execution attestation.

## Data and saved splits: verify before execution

Prefer a privately transferred, already verified canonical TSV. Never open and resave it or regenerate splits. Do not call `python -m src.data.prepare` directly: that older entry point may overwrite outputs. The protected wrapper below verifies raw hashes, uses explicit CRLF serialization and refuses overwrites or a changed canonical hash.

```powershell
function Assert-Hash($path, $expected) {
    if (!(Test-Path -LiteralPath $path)) { throw "Missing: $path" }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum mismatch: $path" }
}
$config = Get-Content configs/pca_order.json -Raw | ConvertFrom-Json
foreach ($entry in $config.source_sha256.PSObject.Properties) {
    Assert-Hash $entry.Name $entry.Value
}
# Explicit data preparation only when missing; no training or split generation.
if (!(Test-Path $config.dataset)) {
    & $py -m src.experiments.workflow prepare-data
    if ($LASTEXITCODE -ne 0) { throw 'Canonical preparation failed; preserve existing files' }
}
Assert-Hash $config.dataset 'e468ea37ed3863cb6c0c46bbe05fda398bae30b627586ff3ed94f2cea0e2476d'
$outer = Get-Content results/splits/outer_manifest.json -Raw | ConvertFrom-Json
$inner = Get-Content results/splits/inner_manifest.json -Raw | ConvertFrom-Json
Assert-Hash results/splits/outer.csv $outer.split_sha256
Assert-Hash results/splits/inner.csv $inner.inner_sha256
Assert-Release
```

The manifests belong to the approved commit. `check` also verifies dataset values against raw sources and compares saved assignments to seed-derived assignments in memory; it does not save new splits. It loads the full expression dataset, so it is not part of the macOS non-training test command.

## Filesystem probe and preflight on Windows

This isolated probe tests writes, atomic replacement and hard links without invoking any model or touching member files. The separate Windows non-fitting test command below also exercises the OS lock.

```powershell
New-Item -ItemType Directory -Force results/pca_order | Out-Null
& $py -c "import os,pathlib,tempfile; base=pathlib.Path('results/pca_order'); t=tempfile.TemporaryDirectory(prefix='fs-probe-',dir=base); p=pathlib.Path(t.name); a=p/'a'; b=p/'b'; a.write_bytes(b'probe'); os.replace(a,b); os.link(b,a); assert a.read_bytes()==b'probe'; t.cleanup(); print('Filesystem probe passed')"
if ($LASTEXITCODE -ne 0) { throw 'Filesystem capabilities failed' }
& $py -B -m unittest discover -s tests -p test_pca_order_resume.py -v
if ($LASTEXITCODE -ne 0) { throw 'Non-fitting resume tests failed' }
Assert-Release
& $py -m src.experiments.pca_order check
if ($LASTEXITCODE -ne 0) { throw 'PCA-order preflight failed' }
```

## Member 4: fresh run and explicit resume

**DO NOT RUN UNTIL EXPLICIT USER APPROVAL** — both commands can start model fitting. A resume skips verified completed outer evaluations, but runs missing evaluations from the beginning, including their complete inner search.

```powershell
# DO NOT RUN UNTIL EXPLICIT USER APPROVAL — fresh run
Assert-Release
& $py -m src.experiments.pca_order run --member 4
if ($LASTEXITCODE -ne 0) { throw 'Incomplete: preserve checkpoint and sidecars' }
```

```powershell
# DO NOT RUN UNTIL EXPLICIT USER APPROVAL — resume after interruption
Assert-Release
& $py -m src.experiments.pca_order run --member 4 --resume
if ($LASTEXITCODE -ne 0) { throw 'Resume stopped: preserve evidence and investigate' }
```

Members 1–3 substitute their assignment number. Fresh mode never silently resumes. Both modes refuse an existing final CSV. Do not delete the final file merely to rerun for a better score.

## Checkpoint bundle and recovery contract

For Member N, all paths are inside `results/pca_order/` and Git-ignored:

- `memberN_results.partial.csv`: authoritative checkpoint, atomically replaced after each whole outer evaluation.
- `memberN_results.context.json`: immutable run identity, exact settings/provenance and execution environment; required for resume.
- `memberN_results.activity.jsonl`: start/resume/publication-validation events; diagnostic log, not authoritative scientific state.
- `memberN_results.lock`: persistent OS-lock file. Its existence does not mean a process is active; never delete it to bypass a running process.
- `memberN_results.partial.csv.<random>.tmp`: possible orphan after a force kill. Never read as evidence or promote manually; resume uses only the committed CSV.
- `memberN_results.csv`: final result, published only after full validation.

Each evaluation key is `(configuration, repeat, fold)`. Resume validates exact sample/patient/label coverage for every represented fold, rejects duplicate or incomplete folds, checks fold-constant evidence, allowed C/gamma, context identity and the canonical CSV checksum. Completed rows retain original run ID, start time and scientific values. No inner-search resume exists.

The CSV remains authoritative; context is written once before the initial checkpoint and is never advanced alongside each fold. A crash between context creation and the initial CSV, a truncated context, or a legacy CSV without context fails closed. Preserve the bundle and investigate; do not fabricate missing metadata. Empty/header-only checkpoints have no row checksum to distinguish initialization from truncation and are refused, even with context. If interrupted before the first committed evaluation, preserve the bundle and obtain approval for a fresh run in a clean output location. If a completed checkpoint exists after a validation/publication failure, resume revalidates it before publication, with zero additional evaluations when all folds are present.

Checkpoint writes use a unique same-directory temporary file, flush/fsync, then atomic replace. OS-held locking prevents concurrent same-member writers and releases on process exit. The diagnostic log may end with an interrupted line; it is not used to decide which folds to skip. Orphan temporary files are preserved and ignored. Abrupt power-loss/storage-controller durability has not been tested; filesystem corruption must fail validation, never trigger silent repair.

Final publication still uses a same-filesystem hard link and refuses an existing destination. A crash after creating the final link may leave both names; all later runs refuse the existing final. Use `validate --member N` and preserve both names for review rather than automatically removing evidence. Keep private sidecars after completion; only the final CSV is required by the collector.

## Final validation and private handoff

No fitting occurs in `validate`, but it loads real data and verifies the saved splits. Run on Windows using the same approved release/environment:

```powershell
Assert-Release
& $py -m src.experiments.pca_order validate --member 4
if ($LASTEXITCODE -ne 0) { throw 'Final CSV validation failed' }
Get-FileHash results/pca_order/member4_results.csv -Algorithm SHA256
```

The final file must contain 4,572 prediction rows, six configurations and 90 complete outer evaluations. Its unchanged columns include patient/sample IDs, actual/predicted subtype, selected C/gamma, winning inner score, counts, runtime, total explained variance, code/data/split identities and a canonical-text checksum. Linear gamma remains `NA`. Upload/download the original bytes through approved private storage; do not resave in Excel. Compare SHA-256 after transfer.

## Leader: collect four CSVs

Place the four final CSVs in `results/pca_order/` on the leader's computer, or provide their actual paths. The collector needs only the final CSVs; retain private context/activity sidecars for execution review.

```powershell
Assert-Release
& $py -m src.experiments.pca_order collect results/pca_order/member1_results.csv results/pca_order/member2_results.csv results/pca_order/member3_results.csv results/pca_order/member4_results.csv --output results/pca_order/comparison-01
if ($LASTEXITCODE -ne 0) { throw 'Collection failed; preserve partial output and use a new directory on retry' }
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

These are leader-generated analysis outputs. Members hand over their final CSVs through an approved private channel. Keep their four CSVs as the original evidence; the collector does not modify them.

## Interpretation and verification limits

Macro-F1 is primary; balanced accuracy and subtype scores remain required. Compare both orders using the same scaler, kernel and component count. Report repeat scores and subtype effects, especially MFS/UPS and the small SS/MPNST groups. Repeats reuse patients; sample SD is not a confidence interval. Do not claim clinical validation or significance from descriptive mean differences.

Automatic checks establish consistency and completeness of prediction evidence, not execution authenticity. The single CSV records selected parameters and the winning inner score, but does not contain every candidate score. The collector verifies that C/gamma belong to the agreed grid; it cannot independently prove that those parameters won the search or reconstruct every inner fit. The runner selects them using the reviewed GridSearchCV implementation. Embedded hashes detect accidental changes but are not signatures and can be recomputed by someone editing a file. Retain one peer reproduction as a separate scientific check. Runtime is not a controlled cross-member benchmark.


## Non-fitting development verification and publication

On macOS, run only `python -B -m unittest discover -s tests -p test_pca_order_resume.py -v` with the existing scientific environment. This module uses predefined synthetic checkpoint records and injected callbacks, with production fit/predict entry points blocked. It does not generate CV splits or load the expression dataset. Do not run `test_pca_order_csv.py` or full test discovery on macOS: the existing suite includes real synthetic training. Updated legacy test expectations for private sidecars remain pending an authorized Windows test run.

Resume sidecars add minimal identity/activity evidence without changing metrics or the member CSV schema. They do not add full candidate-level inner-search evidence, PCA loadings, fitted estimators or execution signatures. These limitations remain subject to supervisor review before official training. Resume is intentionally stricter than the collector's existing identity schema: collector checks the six scientific pins in CSVs; sidecars record additional execution versions and must be retained for a cross-machine environment review.

Member CSVs/context/activity and joblib caches are private. `sources.csv` contains absolute paths/run IDs and is not suitable for external publication. Share only reviewed aggregate outputs plus separately sanitized provenance; no patient-level evidence, raw paths or model data. No Protocol 3.0 Jupyter/HTML adapter exists yet; the Protocol 2.0 dashboard cannot consume this schema automatically. Do not commit generated evidence, temporary files, environments or backups.
