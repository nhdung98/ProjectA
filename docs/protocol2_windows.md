# Protocol 2.0: native Windows operator guide

Status: prepared on macOS; native Windows execution remains a release gate. Use a local Windows 10/11 x64 PC and 64-bit CPython 3.12, Git for Windows, and PowerShell. Windows ARM64/32-bit, network shares, OneDrive folders and removable filesystems are not validated targets. Choose a short local NTFS path such as `C:\Research`.

The official run is a NEW Windows batch. Do not copy the Mac `.venv`, smoke batches, or partial training checkpoints into it. Python documents virtual environments as disposable/non-portable: [venv documentation](https://docs.python.org/3.12/library/venv.html). No activation or PowerShell execution-policy change is needed when invoking the interpreter directly.

## Environment and evidence policy

The six approved scientific dependency versions are unchanged. The lock also pins python-dateutil, six and tzdata. All nine Windows-compatible wheels resolved and downloaded successfully on macOS for `cp312` / `win_amd64`; four numerical packages have native Windows wheels and five packages use platform-independent wheels. See `results/protocol2-development/windows-release/windows-wheel-inventory.json` for downloaded filenames, SHA-256 and package metadata. This proves availability, not native import/runtime correctness. Installation and tests below must pass on Windows. Do not change pins to resolve a failure without review.

Choose and record the team's approved Python 3.12 patch/build before starting. Fresh Windows runs record their own exact Python, OS, architecture, package inventory and numerical-library metadata. Resume, full validation and reporting retain strict identity equality with that original Windows run. Updating Python, packages or Windows during a batch can block resume. There is no cross-platform fold reuse or weakened provenance policy. The read-only `verify-export` command checks ZIP integrity on another machine without claiming model reproduction. Independent metric validation on a different environment is not silently treated as identical-environment validation.

Scientific code, hashed configuration and requirements use Git LF rules. Raw datasets and frozen split files have `-text`; do not open/save them in spreadsheet editors. Preparation explicitly requests canonical CRLF TSV bytes and requires SHA-256 `e468ea37ed3863cb6c0c46bbe05fda398bae30b627586ff3ed94f2cea0e2476d`. A serialization mismatch is a STOP, not permission to update the hash or split manifests.

## 1. Obtain the reviewed release

The implementation is currently uncommitted. These are FUTURE operator commands after human review, an approved commit and transfer/publication by an authorized person. No release SHA is invented here. Run the blocks in order; stop on any nonzero exit.

```powershell
$ErrorActionPreference = 'Stop'
function Assert-LastExit { if ($LASTEXITCODE -ne 0) { throw "Previous command failed: $LASTEXITCODE" } }
$ApprovedCommit = Read-Host 'Enter the full team-approved 40-character release commit SHA'
if ($ApprovedCommit -notmatch '^[0-9a-fA-F]{40}$') { throw 'A full approved commit SHA is required' }
Set-Location C:\Research
git -c core.autocrlf=false clone --no-checkout https://github.com/nhdung98/ProjectA.git ProjectA
Assert-LastExit
Set-Location .\ProjectA
git config core.autocrlf false
Assert-LastExit
git checkout --detach $ApprovedCommit
Assert-LastExit
$ActualCommit = git rev-parse HEAD
Assert-LastExit
if ($ActualCommit -ne $ApprovedCommit) { throw 'Wrong release commit' }
git status --short
Assert-LastExit
```

Use a new destination, not an existing checkout with work to preserve. The approved commit must be available from the remote; if it is not, stop and arrange approved release transfer. Never substitute the current branch tip. Historical outputs remain in their original locations.

## 2–3. Create and install the Windows environment

Install a team-approved x64 Python 3.12 build from [Python's Windows instructions](https://docs.python.org/3.12/using/windows.html). Confirm the interpreter selection before creating the environment.

```powershell
py -3.12 -c "import sys,struct; print(sys.version); assert struct.calcsize('P') == 8"
Assert-LastExit
py -3.12 -m venv .venv
Assert-LastExit
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-protocol2-lock.txt
Assert-LastExit
.\.venv\Scripts\python.exe -m pip check
Assert-LastExit
```

Do not copy `.venv` from macOS. Keep this environment unchanged once a batch begins. A missing compatible wheel or dependency conflict must be investigated rather than changing the protocol. macOS resolution did not test Windows DLL loading or operating-system runtime prerequisites.

## 4–6. Prepare, test and preflight

Both original bundled raw inputs and all four frozen split CSV/JSON files must be present. They are already tracked. The canonical processed matrix is generated locally and ignored by Git.

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow prepare-data
Assert-LastExit
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Assert-LastExit
.\.venv\Scripts\python.exe -m compileall -q src tests
Assert-LastExit
git diff --check
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow preflight --official --output results/protocol2-development/windows-preflight-01.json
Assert-LastExit
```

Preparation returns `prepared_and_hash_verified` or `already_present`. It never silently regenerates splits. Official preflight must return `passed`, 254 patients, 20,531 genes, 762 outer assignments and 3,048 inner assignments. It rejects dirty Git, wrong package versions, source/data hashes and altered splits. Use a new report filename for each check; existing reports are protected. Tests train small artificial fixtures, not the official TCGA batch.

## 7. Native Windows smoke gate

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow smoke --configuration SVM-STD-PCA-50-LINEAR --batch results/protocol2-smoke/windows-setup-01
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow status --batch results/protocol2-smoke/windows-setup-01
Assert-LastExit
```

Expected: `smoke_only`, one completed outer fold, 51 predictions and empty warnings. This executes the five-candidate C grid and four inner folds plus one outer refit. Inspect the run manifest and validation artifact. A smoke is not a full 762-prediction validation, cannot become official, and cannot be included in official reports. Record actual Windows results for human review. Do not infer Windows success from macOS results.

## 8–9. Authorized official training and monitoring

Only after Windows tests/preflight/smoke pass and the team explicitly authorizes the official batch:

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow preflight --official
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow run --all --batch results/protocol2/windows-official-01
Assert-LastExit
```

In another PowerShell terminal, from the same repository:

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow status --batch results/protocol2/windows-official-01
```

Keep the PC on mains power and prevent sleep for the session. Run one batch at a time. GridSearchCV uses `n_jobs=1`; numerical libraries are limited to one controlled thread during fitting/prediction. SVC cache is 200 MB. Temporary preprocessing caches require free space on the system temp volume as well as the project volume. No full-batch Windows RAM/runtime measurement has been made; do not infer an ETA from one smoke. All managed artifact text is UTF-8; machine-generated projections have explicit LF and the canonical TSV retains required CRLF.

## 10. Interrupt and resume

Ctrl+C records the interruption and normally releases `.writer.lock`. An uncommitted fold is repeated; verified committed folds are reused. `finalizing` is recoverable with zero new fits when all 15 checkpoints exist. Configuration, run ID, code, data/splits and environment must match. Missing/corrupt checkpoints and warnings stop recovery.

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow resume --batch results/protocol2/windows-official-01
Assert-LastExit
```

After force termination or power loss, inspect the reservation:

```powershell
$WriterLock = Get-Content results/protocol2/windows-official-01/.writer.lock | ConvertFrom-Json
$WriterLock
Get-Process -Id $WriterLock.pid -ErrorAction SilentlyContinue
```

Confirm in Task Manager that the original writer has stopped; PID reuse must be investigated. On Windows `unlock` deliberately refuses automatic removal and never sends a process signal. Only after verifying that no writer is alive, remove **only** the stale lock:

```powershell
Remove-Item -LiteralPath results/protocol2/windows-official-01/.writer.lock
.\.venv\Scripts\python.exe -m src.experiments.workflow resume --batch results/protocol2/windows-official-01
Assert-LastExit
```

Immutable publication prefers hard links. A filesystem that rejects links uses a closed, fsynced, same-directory copy followed by rename under an exclusive `<filename>.publish-lock` directory. Unsupported/locked rename stops instead of silently accepting partial bytes. A crash can leave a publication reservation and temporary file. Never delete checkpoints or force replacement: after proving the writer is stopped, inspect that exact destination and reservation, then remove only an empty stale `.publish-lock` directory if a retry needs it. Do not broadly delete lock directories. Initial setup interrupted before the first run manifest still requires investigation. Automatic recovery does not repair filesystem corruption or guarantee storage-controller durability after power loss. Use local NTFS; avoid concurrent external writers to evidence folders.

## 11–12. Validate and export

A successful official run produces nine artifacts per configuration under `runs/CONFIGURATION/RUN_ID/`, fold checkpoints, consolidated CSV/Markdown reports, manifests/registers, and an automatic external `evidence_bundle.zip`. All 24 configurations must validate for `full_24_comparison: true`. Human review remains pending.

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow validate --batch results/protocol2/windows-official-01
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow verify-export --zip results/protocol2/windows-official-01/evidence_bundle.zip
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow export --batch results/protocol2/windows-official-01 --audience team
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow verify-export --zip results/protocol2/windows-official-01/team_evidence_bundle.zip
Assert-LastExit
```

To make a subsequent external snapshot without overwriting the automatic bundle:

```powershell
.\.venv\Scripts\python.exe -m src.experiments.workflow export --batch results/protocol2/windows-official-01 --audience external --output results/protocol2/windows-official-01/external-review-02.zip
Assert-LastExit
.\.venv\Scripts\python.exe -m src.experiments.workflow verify-export --zip results/protocol2/windows-official-01/external-review-02.zip
Assert-LastExit
```

`verify-export` checks exact entry inventory and SHA-256, rejects duplicate/missing/extra/modified entries and invalid ZIP data, and reports a whole-ZIP hash for transfer comparison. The inventory excludes itself to avoid circular checksums. Source-artifact hashes are explicitly separate from packaged-entry hashes. These are integrity checks, not signatures; retain the sender's whole-ZIP hash through a trusted channel.

External bundles omit patient predictions, checkpoints, expression matrices and machine-local interpreter paths; aggregate subtype/confusion metrics remain. Private bundles retain the nine original files byte-for-byte, including required patient/sample IDs, but exclude datasets and `.venv`. Private validation still needs the approved repository, frozen manifests and verified dataset. Do not upload private bundles to external AI tools. Existing ZIP names are refused. Reports may be refreshed while older ZIPs remain immutable snapshots.

Common stop messages: `Official execution requires ... clean checkout`, `Resume/provenance mismatch`, `Checkpoint checksum mismatch`, `Finalizing run is missing committed checkpoints`, `Warning-bearing run requires review`, `Bundle already exists`, `ZIP entry checksum mismatch`, and `Missing or unexpected ZIP entries`. Investigate the named condition; do not weaken checks or select a higher-scoring retry.
