# Protocol 2.0 presentation redesign validation

## Backup gate

Before editing, all 11 untracked dashboard files were archived outside the working tree at `/Users/elvyx/Downloads/TCGA_SARC-ML/dashboard-backups/20261028-211430/dashboard-source.zip`. Paths and contents were preserved; every archived member was checked against the SHA-256 inventory in the sibling `verification.json`. All 11 passed. The official ZIP matched its Git blob; branch and HEAD were verified before proceeding. This backup includes the final pre-redesign work, unlike the earlier nine-file backup.

## Outputs and presentation

- New official HTML: `results/dashboards/windows-official-01-redesign-01/report.html`.
- PNGs: its `figures/` directory; 78 files, rendered at 300 dpi.
- Executed notebook: `results/dashboards/windows-official-01-redesign-notebook-01/official_results.ipynb`.
- Reusable notebook: `notebooks/02_protocol2_results_dashboard.ipynb`.
- Provenance: new output's `report_provenance.json`.

Six figures are initially visible in the reading flow: pipeline heatmap, ranking, 24×6 subtype heatmap, selected subtype details, selected confusion and selected repeat stability. Runtime is an optional seventh; validation coverage and a fixed four-configuration stability comparison are supplementary. One selector controls all three configuration-detail charts. The initial selection is explicitly labelled as the existing workflow reference. Numerical-table buttons select the explorer; supplementary download links reference embedded PNGs.

Total export count is **78 = six global + 24 confusion + 24 subtype + 24 stability**. HTML size is **24,032,998 bytes** (about 24.03 MB). Hidden/offline detail images increase file size; they do not increase the main-view figure count. All previous official and synthetic reports are preserved, including their original 53 PNGs each.

## Changed files in this redesign

1. `src/reporting/protocol2_dashboard.py`: subtype overview; per-configuration stability; consistent pipeline ordering/colours; shared confusion scales; visible subtype supports; untruncated mean±SD; PNG provenance; delegation to new HTML renderer.
2. `src/reporting/dashboard_layout.py` (new): overview cards, narrative layout, exact score table, shared selector, collapsible runtime/evidence, offline PNG download mappings.
3. `notebooks/02_protocol2_results_dashboard.ipynb`: same narrative; six analysis/export code cells; separate opt-in export; no saved source-notebook outputs.
4. `tests/test_dashboard.py`: redesigned panel/selector structure, provenance, download coverage and updated export count.
5. `tests/test_dashboard_official.py`: checks all heatmap values, runtime coordinates, status values, per-configuration stability, confusion scales and every subtype SD endpoint against official source tables.
6. `docs/protocol2_dashboard.md`: redesigned report paths, counts, notebook/export instructions and limitations.
7. `reports/protocol2_dashboard_redesign_validation.md` (new): this record.

No frozen training source, scientific configuration, official evidence or dependency pins were changed.

## Validation actually performed

The command below completed **16 tests in 11.556 seconds, all passed**, with no model training:

```sh
MPLCONFIGDIR=results/dashboard-development/mpl-cache PROTOCOL2_OFFICIAL_ZIP=results/dashboard-inputs/67ad3e7/evidence_bundle.zip results/dashboard-development/.venv/bin/python -B -m unittest discover -s tests -p 'test_dashboard*.py' -v
```

Log: `results/dashboard-development/redesign-tests.log`.

Checks cover all 24 configurations, official ZIP/Git identity and CSV equality, sample means/SDs, subtype scores, confusion counts/percentages, ranking, both heatmaps, runtime coordinates and stability scores. Subtype error-bar endpoints are checked numerically and axis bounds include the complete interval. Raw confusion scales are consistently 0–312; percentages 0–100%. Source input bytes are unchanged by rendering; output overwrites and evidence-overlapping destinations are refused. Generic failure tests use explicitly synthetic fixtures only; the delivered report uses official data exclusively.

All six notebook code cells executed successfully through a real Python 3.12 Jupyter kernel, with export disabled. Only the execution harness saved the separate executed notebook. No report.html appeared in that notebook-output directory. The notebook source remains without executed outputs. Representative subtype overview, subtype detail and stability PNGs were visually inspected. An HTML parser verified six initially visible images, 24 selector options and 78 total embedded images. Every embedded PNG matches its standalone PNG byte-for-byte; saved reporter hashes match the current reporting modules.

## Figure provenance

Batch `windows-official-01`; training commit `87f3e6ce1bb3e7fa53e513a22b480abb63998882`; results commit `67ad3e764dadf13827421ab2d6f78f85809b42b3`. Input ZIP SHA-256: `a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c`.

| Figures | Source and transformation |
|---|---|
| Ranking, pipeline heatmap | `summary.csv`: supplied Macro-F1 means/sample SDs; pipeline arrangement is presentation only. |
| Runtime | `summary.csv`: recorded seconds / 60 against supplied mean Macro-F1. |
| Subtype overview and 24 subtype details | `reports/subtype_analysis.csv`: means across three repeat F1 scores; details retain sample SD (`ddof=1`), plus supplied Macro-F1 mean/SD from summary. |
| 24 confusion figures | `reports/confusion_matrices.csv`: sum three repeats by true/predicted label; row-normalize counts to percentages. |
| 24 stability figures and supplementary comparison | `reports/repeat_scores.csv`: original scores in repeat order. |
| Validation | Original manifest/audit attestations plus strict aggregate consistency checks. |

No predictions were generated or recomputed. The report explains that 762 events represent repeated evaluation of the same 254 patients; SS has only 10 and MPNST 9. Sample SD is not a confidence interval; descriptive ordering is not statistical superiority; clinical usefulness is not established by this report.

## Remaining limitations and Git state

Browser interaction and download activation are **unverified in an actual browser**. The available browser tool previously blocked local `file:` URLs; no workaround was used. Regression tests check HTML panel membership, selector wiring, provenance and download mappings, but do not execute browser JavaScript. A manual browser check of all selector views and sample PNG downloads remains necessary before publication. Windows execution is not claimed; this reporting validation ran on macOS. Aggregate validation does not repeat the private patient-level audit, and hashes are not signatures.

The repository remains on `Vy/pipeline-development` at the frozen training commit. All dashboard files remain untracked, nothing is staged, and no branch switch, merge, commit or push occurred. Generated evidence copies, reports, caches, executed notebooks and logs remain under ignored results directories. Review the new source and presentation before any separate dashboard commit.
