# TCGA-SARC reproducible SVM experiments

COS40005 Computing Technology Project A investigates classification of six sarcoma subtypes using 254 patients and 20,531 source gene records. Protocol 2.0 compares 24 SVM configurations: MinMax or Standard scaling, ANOVA gene selection or PCA, 50/100/150 genes or components, and Linear or RBF kernels.

## Results and project status

Official training is complete on Windows for batch `windows-official-01`: 24 configurations and 360 outer-fold fits, with passed automated validation. Evaluation uses repeated nested cross-validation: five outer folds, three repeats and four inner folds. These are research results, not a clinically validated diagnostic system.

| Reference | Role |
| --- | --- |
| `87f3e6ce1bb3e7fa53e513a22b480abb63998882` | Frozen training release |
| `67ad3e764dadf13827421ab2d6f78f85809b42b3` on `Vy/protocol2-results` | Official aggregate results and evidence ZIP |
| `39c4eff7fe7bba9c4f1607013e87998a35661d59` | Initial dashboard source commit |
| `Vy/protocol2-dashboard` | Original reporting source and reviewed Notebook 02 outputs |
| `Vy/protocol2-complete` / `protocol2-v1.0` | Integrated Protocol 2.0 baseline: source, official aggregates and reporting |

Start with [Notebook 02](notebooks/02_protocol2_results_dashboard.ipynb) for saved aggregate tables and figures viewable on GitHub. The standalone HTML is the preferred interactive presentation: it provides a configuration explorer and PNG downloads without Jupyter. Obtain the reviewed `report.html` and `report_provenance.json` from the team's approved distribution location, or generate them using the [dashboard guide](docs/protocol2_dashboard.md). No hosted report or release download is assumed to exist yet.

Reporting tests pass on macOS; the user has manually verified the HTML selector and figure downloads there. Windows **reporting** reproduction and independent scientific peer review remain pending. The [Model Selection Report](reports/protocol2_model_selection.md) proposes a provisional baseline and comparators for Protocol 3.0; no new protocol or implementation is approved by that recommendation.

## Workflow and repository map

Windows training → validated aggregate evidence → read-only reporting → Jupyter analysis and a separately exported HTML report. The reporting layer does not retrain models or regenerate predictions. Notebook Run All displays analysis; HTML export is opt-in. This integrated branch includes the original official ZIP and aggregate tables in [results/protocol2/windows-official-01/](results/protocol2/windows-official-01/). Notebook 02 uses that ZIP directly; no manual evidence copy or branch merge is needed. Clone normally (not shallow or single-branch) so the exact original results commit remains available for provenance verification.

| Location | Purpose |
| --- | --- |
| `src/data/` | Source auditing and canonical data preparation |
| `src/experiments/` | Shared scientific pipeline, nested search and workflow orchestration |
| `configs/svm.json`, `results/splits/` | Protocol 2.0 settings and frozen outer/inner assignments |
| `src/reporting/` | Aggregate validation, figures and standalone HTML |
| `notebooks/01_data_exploration.ipynb` | Initial exploration; local execution outputs require separate privacy review |
| `notebooks/02_protocol2_results_dashboard.ipynb` | Official aggregate analysis with reviewed saved outputs |
| `results/protocol2/windows-official-01/` | Included official aggregate CSVs, original ZIP and unchanged validation metadata |
| `results/dashboards/` | Local generated HTML, provenance and PNGs; excluded from source commits |
| `tests/` | Workflow and reporting tests; authentic reporting checks require the official ZIP |
| `archive/week01/`, `reports/` | Historical submissions, validation records and scientific reports |

The training CLI is `python -m src.experiments.workflow`. It preserves nine required run artifacts, validates predictions independently and builds consolidated evidence. Read the [workflow guide](docs/protocol2_workflow.md) for run/resume, validation and private exports, or the [Windows operator guide](docs/protocol2_windows.md). Do not rerun the completed official batch merely to view results.

## Development setup

Use Python 3.12 in an isolated environment. Installation is explicit; the runner never installs or upgrades packages. For training-workflow development on macOS, follow these commands in an appropriate development checkout, not the reporting environment:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-protocol2-lock.txt
.venv/bin/python -m src.experiments.workflow prepare-data
.venv/bin/python -m src.experiments.workflow preflight
.venv/bin/python -m src.experiments.workflow smoke
```

Preparation refuses overwrites and publishes CRLF TSVs only after verifying the frozen dataset hash. Preparation/preflight do not change split assignments; run/resume do not prepare data. Official execution requires a reviewed, committed, clean training checkout. Do not transfer a macOS virtual environment to Windows.

For reporting, use the separate environment and exact commands in the [dashboard guide](docs/protocol2_dashboard.md). Training-workflow tests use `.venv/bin/python -m unittest discover -s tests -v`; reporting-only tests should use the dedicated reporting environment and official-ZIP variable documented there. The EDA notebook has separate optional notebook dependencies.

The retained [PCA-order workflow](docs/pca_order_experiment.md) is a separate experiment round, not evidence of an approved future protocol. Its CSV-only results are not official dashboard inputs. Legacy SVM commands remain available; historical folders retain their original provenance and are excluded from new-workflow validation.

Read [data provenance](DATA_SOURCES.md) and the [supplied data notice](DATA_LICENSE.txt). Clinical columns and identifiers are excluded from predictors; repeated gene records remain separate features. Training locks pin versions rather than platform-specific wheel hashes; each batch records its environment and code provenance. Keep patient-level data and private run evidence out of externally shared reporting artifacts.

Use the tagged Protocol 2.0 integration as the fixed reference for future research. After supervisor approval, start subsequent development on a separate branch from `protocol2-v1.0`; preserve this release and its evidence unchanged. Protocol 3.0 implementation has not begun here.
