# Protocol 2.0 reporting guide

## 1. Purpose and official evidence

This layer reads validated Windows aggregates; it does not train models, read expression data or regenerate predictions. The HTML is a reviewed team deliverable, not merely a development preview.

| Reference | Value |
| --- | --- |
| Batch | `windows-official-01` |
| Training release | `87f3e6ce1bb3e7fa53e513a22b480abb63998882` |
| Results commit | `67ad3e764dadf13827421ab2d6f78f85809b42b3` |
| Initial dashboard commit | `39c4eff7fe7bba9c4f1607013e87998a35661d59` |
| Results / reporting branches | `Vy/protocol2-results` / `Vy/protocol2-dashboard` |
| ZIP path at results commit | `results/protocol2/windows-official-01/evidence_bundle.zip` |
| Expected ZIP SHA-256 | `a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c` |

Use a separate reporting checkout/environment; keep the frozen Windows training checkout unchanged. No results-branch merge is required.

## 2. Architecture and entry points

| File | Responsibility |
| --- | --- |
| `src/reporting/dashboard_inputs.py` | Exact schemas, checksums, validation attestations and aggregate arithmetic |
| `src/reporting/protocol2_dashboard.py` | Figures, Git-blob provenance verification and export CLI |
| `src/reporting/dashboard_layout.py` | Offline HTML layout, shared selector and downloads |
| `notebooks/02_protocol2_results_dashboard.ipynb` | Read-only analysis; separate optional export cell |
| `requirements-dashboard.txt` | Pinned direct plotting/notebook dependencies |
| `tests/test_dashboard*.py` | General safeguards and official-evidence checks |

Inputs are `summary.csv`, `comparison.csv`, `reports/repeat_scores.csv`, `reports/subtype_analysis.csv`, `reports/confusion_matrices.csv`, `validation_summary.json` and `experiment_manifest.json`. Prefer the original verified external ZIP, which includes these files and export-specific checksums.

## 3. Official Jupyter Notebook

Open [Notebook 02](../notebooks/02_protocol2_results_dashboard.ipynb) on GitHub to inspect its reviewed saved aggregate outputs without executing it. GitHub renders static figures/tables, not the standalone HTML's interactive controls.

For execution, open the same file in VS Code/Jupyter with the reporting Python environment. The requirements install a kernel and execution libraries, not a JupyterLab server. Select the environment directly in VS Code, or register it for an existing Jupyter frontend with `python -m ipykernel install --user --name protocol2-dashboard --display-name 'Protocol 2.0 Dashboard'` using the reporting executable.

Run cells in order. The default `SOURCE` is `results/dashboard-inputs/67ad3e7/evidence_bundle.zip` below the repository root; the full results SHA and Git path are verified against the local Git blob. `PROTOCOL2_BATCH` can override that path. Edit `SOURCE`, `RESULTS_COMMIT` and `RESULTS_GIT_PATH` together for other official evidence.

The narrative is overview → pipelines/ranking → subtype overview → configuration details → optional supporting analysis. Changing `CONFIGURATION` updates all three detail figures. `SHOW_SUPPLEMENT` enables additional tables and charts.

**Run All does not automatically export or publish HTML.** Leave `PROTOCOL2_EXPORT` unset or `0` for ordinary analysis. Enable `RUN_EXPORT=True` in the final cell, or set `PROTOCOL2_EXPORT=1`, only for explicit export. `PROTOCOL2_REPORT_OUTPUT` selects a new output directory. Existing directories are never overwritten.

## 4. macOS reproduction

Run from the reporting checkout root with Python 3.12 installed. Use the reporting environment, not the frozen training `.venv`:

```sh
python3.12 -m venv results/dashboard-development/.venv
PYTHON="$PWD/results/dashboard-development/.venv/bin/python"
"$PYTHON" -m pip install -r requirements-dashboard.txt
"$PYTHON" -m pip check
export MPLCONFIGDIR="$PWD/results/dashboard-development/mpl-cache"
git fetch origin refs/heads/Vy/protocol2-results:refs/remotes/origin/Vy/protocol2-results
```

Copy using binary I/O with exclusive creation. If already present, skip the copy and verify its checksum instead; never overwrite the evidence:

```sh
"$PYTHON" -c "import pathlib,subprocess; p=pathlib.Path('results/dashboard-inputs/67ad3e7/evidence_bundle.zip'); p.parent.mkdir(parents=True,exist_ok=True); data=subprocess.check_output(['git','show','67ad3e764dadf13827421ab2d6f78f85809b42b3:results/protocol2/windows-official-01/evidence_bundle.zip']); p.open('xb').write(data)"
export PROTOCOL2_OFFICIAL_ZIP="$PWD/results/dashboard-inputs/67ad3e7/evidence_bundle.zip"
"$PYTHON" -c "import os,pathlib,hashlib; h=hashlib.sha256(pathlib.Path(os.environ['PROTOCOL2_OFFICIAL_ZIP']).read_bytes()).hexdigest(); print(h); assert h=='a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c'"
"$PYTHON" -B -m unittest discover -s tests -p 'test_dashboard*.py' -v
```

Stop if any checksum/test fails. Generate only after successful verification:

```sh
REPORT="results/dashboards/windows-official-01-$(date +%Y%m%d-%H%M%S)"
"$PYTHON" -m src.reporting.protocol2_dashboard \
  --input "$PROTOCOL2_OFFICIAL_ZIP" --output "$REPORT" \
  --results-commit 67ad3e764dadf13827421ab2d6f78f85809b42b3 \
  --results-git-path results/protocol2/windows-official-01/evidence_bundle.zip \
  --configuration SVM-MM-ANOVA-50-LINEAR --configuration SVM-MM-PCA-50-LINEAR \
  --configuration SVM-STD-ANOVA-50-LINEAR --configuration SVM-STD-PCA-50-LINEAR
open "$REPORT/report.html"
```

The four `--configuration` arguments choose the supplementary fixed stability comparison; they do not exclude any configuration from the main ranking or selector. The default CLI selection, if omitted, is the first four validated IDs. The main explorer starts with the workflow reference, explicitly not an unbiased winner claim.

## 5. Windows reproduction

Use a separate reporting checkout; do not reuse the training environment:

```powershell
git clone --branch Vy/protocol2-dashboard --single-branch https://github.com/nhdung98/ProjectA.git ProjectA-dashboard
cd ProjectA-dashboard
py -3.12 -m venv results\dashboard-development\.venv
$python = Join-Path $PWD 'results\dashboard-development\.venv\Scripts\python.exe'
& $python -m pip install -r requirements-dashboard.txt
& $python -m pip check
$env:MPLCONFIGDIR = Join-Path $PWD 'results\dashboard-development\mpl-cache'
git fetch origin refs/heads/Vy/protocol2-results:refs/remotes/origin/Vy/protocol2-results
```

Copy through Python, not PowerShell text redirection. Skip this exclusive-copy command only if the destination already exists; verify it below:

```powershell
& $python -c "import pathlib,subprocess; p=pathlib.Path('results/dashboard-inputs/67ad3e7/evidence_bundle.zip'); p.parent.mkdir(parents=True,exist_ok=True); data=subprocess.check_output(['git','show','67ad3e764dadf13827421ab2d6f78f85809b42b3:results/protocol2/windows-official-01/evidence_bundle.zip']); p.open('xb').write(data)"
$env:PROTOCOL2_OFFICIAL_ZIP = 'results/dashboard-inputs/67ad3e7/evidence_bundle.zip'
$hash = (Get-FileHash $env:PROTOCOL2_OFFICIAL_ZIP -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne 'a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c') { throw 'Evidence checksum mismatch' }
& $python -B -m unittest discover -s tests -p 'test_dashboard*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Dashboard tests failed' }
$report = Join-Path $PWD ('results/dashboards/windows-official-01-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& $python -m src.reporting.protocol2_dashboard --input $env:PROTOCOL2_OFFICIAL_ZIP --output $report --results-commit 67ad3e764dadf13827421ab2d6f78f85809b42b3 --results-git-path results/protocol2/windows-official-01/evidence_bundle.zip --configuration SVM-MM-ANOVA-50-LINEAR --configuration SVM-MM-PCA-50-LINEAR --configuration SVM-STD-ANOVA-50-LINEAR --configuration SVM-STD-PCA-50-LINEAR
if ($LASTEXITCODE -ne 0) { throw 'Dashboard generation failed' }
Invoke-Item (Join-Path $report 'report.html')
```

Run the notebook with export disabled and manually check the Windows browser selector/downloads. Windows reporting remains unverified until those steps pass on Windows. Always stop and resolve installation/fetch errors before proceeding.

## 6. Outputs, tests and provenance

A complete report contains `report.html`, `report_provenance.json` and 78 PNGs at 300 dpi. Six images appear in the primary reading flow; runtime is optional. The validation-coverage chart remains in Supplementary Evidence. All 24 configuration detail panels and figure downloads are accessible offline.

The reviewed macOS presentation is locally available at `results/dashboards/windows-official-01-redesign-01/report.html` when that generated directory is present; it is not tracked or guaranteed in a fresh clone. Each regeneration uses a new directory.

The 16 automated tests cover schemas, hashes, missing/invalid evidence, source mutation, figure values and scales, repeat SD, selector structure and provenance. Set `PROTOCOL2_OFFICIAL_ZIP` explicitly: without it the four official tests skip. Confirm **16 passed and zero skipped**, rather than accepting a partial test run.

Before publication, macOS checks passed against official evidence; the user separately confirmed configuration switching, PNG downloads and presentation review. Automated HTML tests inspect structure rather than executing browser JavaScript. Independent scientific peer review remains pending.

The loader verifies export-specific ZIP hashes, original validation attestations and aggregate arithmetic. `--results-commit` and `--results-git-path` verify the ZIP against the exact Git blob. Provenance records input and reporting-module hashes, source/results commits and plotting-library versions. Checksums detect corruption, not forgery; these checks do not repeat the private patient-level audit.

Direct dependencies are pinned; transitive dependencies, fonts and OS differences may change rendered image bytes. Record the reporting commit when distributing a regenerated artifact. Partial reporting requires `--allow-partial` and is labelled INCOMPLETE; it is not an acceptable complete official publication. Never use `--allow-synthetic` for the official report.

## 7. Interpretation, privacy and publication

Macro-F1 is the mean of six class F1 scores within each repeat, then averaged across three complete repeats. Sample SD uses `ddof=1`; it is not a confidence interval. Repeats share patients and overlapping training sets. Pooled confusion matrices count 762 prediction events from 254 patients, not 762 independent patients. Per-class F1 averages repeat scores, not the pooled matrix's F1.

SS has 10 patients and MPNST nine. Mean±SD may extend outside 0–1 without implying an observed F1 outside that range. Ranking 24 candidates is exploratory; selecting the largest score introduces winner-selection bias. No significance or clinical-readiness claim follows. See the [Model Selection Report](../reports/protocol2_model_selection.md) for provisional Protocol 3.0 planning.

Only Notebook 02's reviewed aggregate outputs may be committed for GitHub preview. Review text, tables, PNGs, HTML, metadata and traces before each publication. Notebook 01 retains its Git version; preserve its local outputs without staging them. Never stage `.DS_Store`, patient records, expression data, private predictions, ZIP copies, generated HTML/PNG collections, synthetic outputs, environments, caches or backups.

Distribute reviewed `report.html` and `report_provenance.json` together through a private GitHub release tied to the reporting commit, or an approved access-controlled team folder. Record artifact checksums and the results SHA; verify access for supervisors/clients without making the repository public. This is a recommendation, not an existing hosted artifact. No HTML upload is part of the documentation task. The 78 embedded PNGs are downloadable from the report and need not be committed separately.
