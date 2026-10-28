# Protocol 2.0 aggregate results dashboard

## Redesigned official report

Current presentation: `results/dashboards/windows-official-01-redesign-01/report.html`. The previous official report and its 53 PNGs remain untouched. The redesigned report has six initially visible figures: pipeline heatmap, all-configuration ranking, subtype overview, and the selected configuration's subtype, confusion and stability charts. Runtime is collapsed by default; validation and fixed-comparison stability are supplementary. All 24 configurations remain available through one selector; numerical-table buttons select the same three-chart explorer. Download links for all figures are in Supplementary Evidence.

The export contains 78 PNGs (six global figures plus three per configuration), although only six appear in the primary narrative. This deliberately separates exhaustive downloadable exports from the reading experience. All 78 are embedded in the standalone HTML, which is 24,032,998 bytes in this build. No CDN or network assets are used. Pipeline order/colours are consistent; raw confusion scales are 0–312 and normalized scales 0–100%. Mean ± sample SD endpoints are preserved, including values beyond 0–1. Every PNG includes batch/training/results provenance.

The notebook now follows overview → pipeline comparison → ranking → subtype overview → configuration explorer → optional supporting analysis. Its last cell exports only if `RUN_EXPORT=True` or `PROTOCOL2_EXPORT=1`. Default execution analyzes in memory without writing report outputs. The executed analysis-only copy is `results/dashboards/windows-official-01-redesign-notebook-01/official_results.ipynb`. This official notebook verifies the fixed results commit and refuses synthetic or partial inputs. Use the explicit SOURCE/results parameters and final export switch when changing notebook inputs.

To regenerate, use the official CLI command below with a **new output directory**, for example `results/dashboards/windows-official-01-redesign-02`. Set `PROTOCOL2_OFFICIAL_ZIP` and run `python -B -m unittest discover -s tests -p 'test_dashboard*.py' -v` for all 16 generic and official tests. Browser interaction and download actions still need a real-browser manual check: the available browser tool blocks local file URLs. HTML structure, shared-selector panel contents and figure download mappings were checked, but this is not claimed as browser execution.

This separate reporting layer does not import the training workflow, fit models, read expression data or patient predictions, or change input evidence. Keep the Windows training checkout at `87f3e6ce1bb3e7fa53e513a22b480abb63998882`. Develop and install this dashboard in a separate reporting checkout/environment. No training-release files need to change.

## Open the report

Double-click `report.html` in Edge, Chrome, Firefox or Safari. It works offline: charts and configuration-selection JavaScript are embedded. Select any validated configuration to inspect its confusion matrix and six subtype F1 scores. Share the HTML alone, or the separate `figures/` PNGs (300 dpi). Keep `report_provenance.json` alongside the report for provenance review.

The official report is `results/dashboards/windows-official-01-67ad3e7-final/report.html`. Its inputs are verified against results commit `67ad3e764dadf13827421ab2d6f78f85809b42b3`, batch `windows-official-01`, trained at `87f3e6ce1bb3e7fa53e513a22b480abb63998882`.

The separate development preview remains `results/dashboards/synthetic-demo-final/report.html`. Every development chart is marked **SYNTHETIC DEMONSTRATION — NOT RESEARCH RESULTS**. It must not appear in research results as experimental evidence.

## Windows installation and generation

Run PowerShell in the root of the **separate dashboard checkout**, containing `src/reporting/`. Python 3.12 must already be installed. These commands use an explicit environment executable, so activation and execution-policy changes are unnecessary.

```powershell
py -3.12 -m venv results\dashboard-development\.venv
$python = Join-Path $PWD 'results\dashboard-development\.venv\Scripts\python.exe'
& $python -m pip install -r requirements-dashboard.txt
& $python -m pip check
$env:MPLCONFIGDIR = Join-Path $PWD 'results\dashboard-development\mpl-cache'
& $python -B -m unittest discover -s tests -p test_dashboard.py -v
& $python -m src.reporting.protocol2_dashboard --help
```

After the Windows batch has finished and the original workflow has successfully validated/exported it, copy its **external aggregate evidence ZIP** to a separate input directory. Alternatively, provide the original batch directory; only the seven allowlisted aggregate inputs are read. Do not copy expression data for reporting. Replace the example input path below with the actual exported file. Use a new output directory each time.

```powershell
$batch = 'C:\Protocol2Evidence\completed-batch\evidence_bundle.zip'
$report = Join-Path $PWD ('results\dashboards\official-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& $python -m src.reporting.protocol2_dashboard --input $batch --output $report
if ($LASTEXITCODE -ne 0) { throw 'Dashboard generation refused; inspect the validation error.' }
Invoke-Item (Join-Path $report 'report.html')
```

The CLI accepts `--input`, `--output`, `--allow-partial`, `--allow-synthetic`, repeatable `--configuration`, and paired `--results-commit`/`--results-git-path`. The latter verify the input ZIP bytes against that exact local Git blob and display the resolved 40-character results commit separately from the training commit. For example, append `--configuration SVM-STD-ANOVA-150-LINEAR --configuration SVM-MM-PCA-50-RBF` to choose repeat-stability lines. This does not limit the ranking or configuration selector. The default CLI stability selection is the first four validated configurations in fixed configuration order, not the highest scores. The official notebook selects one fixed 50-linear configuration per pipeline.

## Reproduce the published official dashboard

In the reporting checkout, after environment setup above, fetch without switching or merging. Copy the ZIP through Python binary I/O (PowerShell text redirection can corrupt ZIP bytes). The copy refuses to overwrite an existing evidence file; if already present, skip only that copy command and let report generation verify it against Git.

```powershell
git fetch origin refs/heads/Vy/protocol2-results:refs/remotes/origin/Vy/protocol2-results
git rev-parse 67ad3e7
& $python -c "import pathlib,subprocess; p=pathlib.Path('results/dashboard-inputs/67ad3e7/evidence_bundle.zip'); p.parent.mkdir(parents=True,exist_ok=True); data=subprocess.check_output(['git','show','67ad3e764dadf13827421ab2d6f78f85809b42b3:results/protocol2/windows-official-01/evidence_bundle.zip']); p.open('xb').write(data)"
$env:PROTOCOL2_OFFICIAL_ZIP = 'results/dashboard-inputs/67ad3e7/evidence_bundle.zip'
& $python -B -m unittest discover -s tests -p 'test_dashboard*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Dashboard tests failed.' }
$report = Join-Path $PWD ('results/dashboards/windows-official-01-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& $python -m src.reporting.protocol2_dashboard --input $env:PROTOCOL2_OFFICIAL_ZIP --output $report --results-commit 67ad3e764dadf13827421ab2d6f78f85809b42b3 --results-git-path results/protocol2/windows-official-01/evidence_bundle.zip --configuration SVM-MM-ANOVA-50-LINEAR --configuration SVM-MM-PCA-50-LINEAR --configuration SVM-STD-ANOVA-50-LINEAR --configuration SVM-STD-PCA-50-LINEAR
if ($LASTEXITCODE -ne 0) { throw 'Official dashboard generation refused.' }
Invoke-Item (Join-Path $report 'report.html')
```

Expected with the redesigned generator: 24 validated configurations, six per pipeline, 78 PNGs, both full commit SHAs and `windows-official-01` visible in HTML. No synthetic or partial flags are used. Tests referencing authentic evidence skip unless `PROTOCOL2_OFFICIAL_ZIP` is set.

Without `--allow-partial`, anything short of a fully validated 24-configuration batch is refused. With that flag, the report is visibly **INCOMPLETE** and includes all 24 status entries; only individually validated, consistent rows are plotted. Missing required aggregate files may leave only the status overview. A hash mismatch or unknown schema is always refused, even in partial mode. This tool does not reconstruct missing report inputs or repair failed runs. Do not use `--allow-synthetic` on an official reporting invocation.

## Jupyter notebook

Open `notebooks/02_protocol2_results_dashboard.ipynb` using an existing Jupyter frontend or VS Code with notebook support. The requirements install the kernel and execution libraries, not a JupyterLab server. For VS Code, select the reporting environment above directly. For an existing Jupyter frontend, register the kernel once:

```powershell
& $python -m ipykernel install --user --name protocol2-dashboard --display-name 'Protocol 2.0 Dashboard'
```

Select **Protocol 2.0 Dashboard** and run cells in order. The notebook defaults to the official ZIP copied above and verifies its fixed results commit/path. Edit `SOURCE`, `RESULTS_COMMIT` and `RESULTS_GIT_PATH` together for another official batch. `PROTOCOL2_BATCH` can override the source path. The final export cell defaults to disabled; enable `RUN_EXPORT` or set `PROTOCOL2_EXPORT=1`, with a fresh `PROTOCOL2_REPORT_OUTPUT` directory if desired. Analysis and plotting do not export files. Change `CONFIGURATION` once to update all three notebook detail views. Keep executed notebooks out of Git.

## Input and interpretation contract

The loader expects the exact frozen workflow column schemas in `summary.csv`, `comparison.csv`, `reports/repeat_scores.csv`, `reports/subtype_analysis.csv`, `reports/confusion_matrices.csv`, plus `validation_summary.json` and `experiment_manifest.json`. It verifies directory hashes or ZIP export-specific entry hashes, run audit identities/attestations, commit consistency, cohort/class ordering, repeat coverage, confusion denominators, and arithmetic consistency of existing metrics. It never reads or recomputes predictions. Old submissions and smoke outputs are not automatically converted into official results.

Macro-F1 is the equally weighted six-class F1 averaged across three complete repeats. Each repeat contains 254 held-out predictions across its outer folds. Error bars are sample SD (`ddof=1`) of the three repeat scores; they are not confidence intervals. Confusion charts pool 762 prediction events from the same 254 patients, with row totals 312, 171, 147, 75, 30 and 27 in explicit order LMS, DDLPS, UPS, MFS, SS, MPNST. Per-class F1 averages repeat scores, not the pooled confusion matrix. Runtime is the recorded sum of completed outer-fold durations, converted from seconds to minutes; it excludes failed attempts and reporting overhead and depends on the machine.

Ranking is descriptive/exploratory, not evidence of statistical superiority. Selecting the winner using these outer-CV scores introduces winner-selection bias. Repeats and overlapping training folds are not independent test samples. Small SS/MPNST supports warrant care. Original audit attestations plus aggregate consistency checks are not a new patient-level audit; checksums detect corruption, not forgery. Human peer review is not inferred.

## Privacy, reproducibility and integration

Exports include configuration IDs, safe batch label, source commit, aggregate charts, input/reporter hashes, plotting-library versions and UTC generation time. They omit raw manifests, run IDs, absolute input/environment paths, patient identifiers and expression data. HTML requires no network assets. Inputs are checked again before HTML publication. Output directories may not overlap evidence; existing outputs are never overwritten. If interrupted, an output may contain partial PNGs: use a fresh directory, not that unfinished report.

Within this repository all reports must be under `results/dashboards/` or `results/dashboard-development/`, both covered by the existing results ignore rule. Do not stage generated HTML/PNGs, synthetic fixtures, executed notebooks, caches, logs or the reporting `.venv`. Direct plotting/notebook dependencies are pinned separately; transitive packages, OS/fonts and rendering bytes are not locked across platforms. Metric checks are strict, but byte-identical Windows/macOS images are not promised. Review and test on real Windows before calling this Windows-verified.

After the official Windows batch completes: retain its frozen release SHA, validate/export with that release, copy the aggregate snapshot to the reporting checkout, generate without development flags, verify the displayed source commit matches the frozen release, and review all 24 statuses before sharing. A future reviewed dashboard commit can be maintained separately; installing it is not a reason to update the training checkout.
