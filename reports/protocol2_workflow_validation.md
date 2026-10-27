# Protocol 2.0 workflow: release-blocker fixes and Windows preparation

Reviewed development date: 27 October 2026. Branch remains `Vy/pipeline-development`; base HEAD remains `e01c61e1ddb4a07a826d7a42b89e2828a4438612`. This is an uncommitted implementation awaiting human review. No official training, commits, pushes, merges, branch switches, split regeneration, historical evidence edits or external patient-data uploads occurred.

Recommendation: **READY FOR HUMAN REVIEW**. This is not approval for official training and not a claim of native Windows verification.

## Changes and root causes

| Issue | Root cause | Implemented fix |
| --- | --- | --- |
| Crash during finalization | `complete` was projected before validation and artifact hashes; resume then demanded a seal that did not exist. | `workflow_run.py` persists `finalizing` before final projections. Metrics are computed in that state. Independent audit accepts it only through an explicit internal `finalizing=True` argument; ordinary validation still requires `complete`. Validation and all eight non-manifest artifact hashes are written before the final atomic manifest commits `complete`. |
| Recoverable completed folds | A full set of successful folds could be stranded by interrupted finalization. | Resume validates checkpoint checksums, identity, sample/fold assignments, search winners and feature evidence, then rebuilds projections and seals with zero new fits. A `finalizing` run missing checkpoints is rejected rather than refitted. Completed sealed runs are validated and left byte-identical. |
| External manifest checksum mismatch | Packaging removed the manifest's run map while retaining its original checksum as if it described exported bytes. | `EXPORT_CHECKSUMS.json` contains separate `source_artifact_sha256` and `entry_sha256`. Entry hashes are computed from exact payload bytes, including sanitized copies. Every ZIP entry except the inventory itself is covered, avoiding circular references. |
| Missing archive integrity verification | CRC alone did not validate the advertised SHA-256 inventory. | New read-only `verify-export --zip PATH` verifies exact entry coverage, hashes, duplicate/unsafe names and ZIP integrity. Export invokes it before publication. Added/removed/modified entries and invalid archives fail. Hashes are not signatures; retain the emitted whole-ZIP hash through a trusted channel. |
| Local paths in external evidence | `python_executable` included machine-local usernames and home paths. | External JSON copies drop that field and redact absolute local-path strings. Internal artifacts and private team copies remain unchanged. The strict aggregate allowlist excludes predictions, checkpoints and expression matrices. |
| Filesystem portability | Immutable publication assumed hard-link support. | All publishers use an exclusive destination reservation; hard links are preferred, with a same-directory fsynced copy/rename fallback when unsupported. Windows sharing violations fail closed. Files are closed before rename; no target overwrite is permitted by cooperating publishers. |
| Cross-checkout source byte consistency | Some provenance-hashed requirements/configuration files lacked explicit Git line-ending rules. | `.gitattributes` now also fixes `configs/*.yaml`, `requirements.txt` and `requirements-protocol2-lock.txt` to LF. Existing raw/split `-text` rules remain unchanged. Canonical preparation still requires exact CRLF TSV bytes and the frozen SHA-256. |

Workflow metadata format is version **2**, distinct from scientific Protocol **2.0**. Earlier development smoke folders and their code hashes are retained unchanged; they are not migrated or relabelled. `export --output BATCH/new-name.zip` makes a new immutable snapshot when a default ZIP already exists. Original source hashes in an external validation-summary copy are explicitly labelled as source hashes.

The legacy validator's only change is an optional internal finalization-state argument. Its public/default audit still requires completed runs; metric, split, search and feature checks are unchanged. No training module was changed.

## Files and proposed implementation commit

New in this follow-up: `docs/protocol2_windows.md`.

Edited in this follow-up: `.gitattributes`, `README.md`, `docs/README.md`, `docs/protocol2_workflow.md`, this report, `src/experiments/validate_svm.py`, the four workflow modules, and `tests/test_workflow.py`. Existing uncommitted preparation/test/requirements changes from the earlier implementation remain part of the release.

Proposed complete commit scope, after review and explicit approval:

```text
.gitattributes
README.md
docs/README.md
docs/protocol2_workflow.md
docs/protocol2_windows.md
reports/protocol2_workflow_validation.md
requirements-protocol2-lock.txt
src/data/prepare.py
src/experiments/README.md
src/experiments/validate_svm.py
src/experiments/workflow.py
src/experiments/workflow_checks.py
src/experiments/workflow_run.py
src/experiments/workflow_report.py
tests/test_workflow.py
tests/test_workflow_data.py
```

Do not commit or push `.venv/`, generated `data/processed/`, `__pycache__/`, downloaded wheels, temporary files, or generated `results/protocol2*` logs/checkpoints/reports/ZIPs. Do not add private team evidence to Git or external AI services. The already tracked original inputs and frozen split files stay unchanged; do not remove them or force-add generated replacements. Historical submissions remain untouched.

## Actual macOS verification

Environment: isolated CPython **3.12.13**, macOS arm64, existing pinned dependency versions unchanged. `pip check` passes. Compilation and Git whitespace checks pass.

| Check | Actual result and evidence |
| --- | --- |
| Full automated suite | **45 tests passed**, 0 failures, 0 skips, 28.415 seconds. `results/protocol2-development/windows-release/tests-release.log`. Earlier intermediate logs are retained, not overwritten. |
| Crash-boundary regression | One genuine synthetic nested run supplies 15 checkpoints. The test simulates abrupt exceptions bypassing normal run cleanup immediately before and after each of **15 artifact/manifest writes**: **30 cases**. Every recovery uses zero additional calls to `fit_search`, preserves run ID/checkpoint hashes, passes independent validation and leaves a subsequent completed-run resume byte-idempotent. |
| Missing/corrupt checkpoint protection | Finalizing with a missing checkpoint fails without fitting. Existing checksum-corruption and rehashed-invalid-prediction tests continue to reject evidence before reuse. |
| ZIP integrity | Both external and team archives pass every exact payload SHA-256 check. For each audience, modified, missing, extra, duplicate entries and invalid archive bytes are rejected: **10 tampering cases**. Tests also invoke the actual `verify-export` CLI entry point without loading experiment settings. |
| Privacy | Tests inject Unix and Windows paths with `PRIVATE_OPERATOR`; external payloads contain neither that username nor synthetic patient/sample IDs. Team run files remain byte-identical. Neither bundle contains datasets. Tests verify source evidence is unchanged by exporting. |
| Portable filesystem tests | Unicode/spaced paths; simulated unsupported hard links exercise copy fallback; duplicate targets are refused; simulated Windows sharing violations leave no partially published target and allow a later retry. Executed on macOS, not a Windows kernel. |
| Environment policy tests | A Windows-shaped identity can match itself; Mac-to-Windows resume and changed code/data/split/package/commit identities are rejected. This is policy testing, not Windows execution. |
| Development preflight | Passed, explicitly dirty Git. Raw hashes, canonical hash, source values/labels, 254 patients, 20,531 genes, 762 outer and 3,048 inner assignments verified. `windows-release/preflight.json`. |
| New real-data smoke | `results/protocol2-smoke/windows-portability-mac-01`, `SVM-STD-PCA-50-LINEAR`, run `20261027T121841Z-0692ab7503ce`. **smoke_only**, one outer fold, 51 predictions, zero warning bytes, 21 pipeline fits. Current code and all artifact hashes match. `windows-release/smoke-verification.json`. |

After the Windows-specific stale-lock assertion adjustment, the targeted workflow-suite rerun passed **15 tests**, 0 failures, in 20.586 seconds; its log is `windows-release/regression-release.log`. The assertion expects the deliberate manual-recovery refusal on Windows and the live-PID refusal on POSIX. No training implementation changed after the full-suite run or new smoke.

Tests use temporary synthetic data; those fixtures are not research evidence. Three older one-fold Mac smokes from the prior implementation remain historical development diagnostics. No completed real-data 762-prediction configuration or official 24-configuration comparison was generated. The official `results/protocol2/` namespace remains absent.

## Scientific assessment

Verified byte-identical to HEAD: `configs/svm.json`, `configs/data.yaml`, direct scientific requirements, raw inputs, all frozen split files, `svm.py`, `pipeline.py`, `common.py`, `validation.py`, and `metrics.py`. Git reports no changes under historical `archive/`.

The approved 254-patient six-class cohort, 24 configurations, sizes 50/100/150, linear/RBF grids, seeds, training-only transforms, 5×3 outer CV and four-fold inner CV are unchanged. Metrics remain complete-repeat macro-F1 and balanced accuracy, with sample SD across three repeats. Search candidate scores and outer-fit feature summaries remain required. PCA fitted loadings/models and independent ANOVA/PCA refits are not newly claimed as saved evidence. Reports remain exploratory, not an unbiased estimate of the winner selected from outer scores.

Canonical dataset SHA-256 remains `e468ea37ed3863cb6c0c46bbe05fda398bae30b627586ff3ed94f2cea0e2476d`.

## Windows dependency availability and policy

Executed pip's binary-only resolver/download with `--platform win_amd64 --python-version 312 --implementation cp --abi cp312` against the unchanged lock. All **9 pinned distributions** downloaded successfully; no Windows packages were installed into the Mac environment. The first sandboxed attempt failed DNS, and the explicitly approved network retry succeeded.

Native `cp312-win_amd64` wheels were obtained for numpy 2.3.5, pandas 3.0.1, scikit-learn 1.7.2 and scipy 1.16.2. Universal wheels were obtained for joblib 1.5.2, threadpoolctl 3.6.0, python-dateutil 3.0.0, six 1.17.0 and tzdata 2026.5. Wheel metadata accepts Python 3.12. Filenames, metadata requirements and actual downloaded SHA-256 hashes are recorded in `results/protocol2-development/windows-release/windows-wheel-inventory.json`.

Availability/resolution is verified; native Windows installation, DLL loading, tests, filesystem behavior, preflight and smoke are **NOT yet verified**. Windows ARM64 and 32-bit are not covered.

No provenance policy was weakened: new Windows batches use their own Windows identity, and resume demands the same identity. A Mac smoke is not a Windows prerequisite artifact and cannot be reused as a Windows fold. Exact Python patch/build, OS, package inventory and numerical-library metadata are retained. The lock is a version lock, not a fully hashed interpreter/wheel lock. OS/package updates can block resume; freeze the approved environment during the batch.

Use local NTFS storage. Atomic rename and fsync do not guarantee storage-controller durability after power loss. Unsupported filesystems, active antivirus/open-file sharing locks, external concurrent writers and stale publication reservations can require operator intervention. Initial run setup interrupted before its first manifest remains a fail-closed manual-investigation case. Windows stale writer-lock recovery is explicitly manual and never uses `os.kill(pid, 0)`. No Windows peak RAM/runtime measurements exist.

## Exact operator instructions and remaining gates

The complete, ordered [PowerShell operator guide](../docs/protocol2_windows.md) includes:

1. Clone and detach at the exact reviewed release SHA (not an invented current SHA).
2. `py -3.12 -m venv .venv` and explicit `.venv\Scripts\python.exe` invocations.
3. Binary-only pinned installation and dependency checks.
4. Canonical preparation/hash verification without split changes.
5. Tests and compilation.
6. Clean official preflight.
7. Native Windows smoke and expected status.
8. Explicitly authorized all-24 training.
9. Status monitoring.
10. Interruption/stale-lock recovery and resume.
11. Completed-batch validation.
12. Private/external snapshot exports and read-only ZIP verification.

The guide uses actual supported CLI commands, documents failure messages, UTF-8 output, expected artifacts, and no-overwrite behavior. Do not copy the macOS virtual environment.

Before official training: human review of the fixes and expanded tests; explicitly approved clean release commit; approved transfer/publication of that release; successful native Windows environment installation, full tests, preflight and smoke; review of those actual Windows results; explicit authorization for the official 24-configuration batch. A dirty-development preflight pass does not satisfy the official gate.

**READY FOR HUMAN REVIEW**
