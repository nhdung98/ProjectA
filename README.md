# TCGA SARC machine learning

Predict six sarcoma subtypes from gene expression: 254 patients and 20,531 gene records. This week's experiment compares **scaling before PCA** with **scaling after PCA**.

## Member commands

After setup, run your assigned command from the repository root:

| Member | Command | Completed result |
| --- | --- | --- |
| 1 | `python -m src.experiments.pca_order run --member 1` | `results/pca_order/member1_results.csv` |
| 2 | `python -m src.experiments.pca_order run --member 2` | `results/pca_order/member2_results.csv` |
| 3 | `python -m src.experiments.pca_order run --member 3` | `results/pca_order/member3_results.csv` |
| 4 | `python -m src.experiments.pca_order run --member 4` | `results/pca_order/member4_results.csv` |

Each member submits **one CSV**, containing 4,572 held-out predictions with settings and run evidence. No ZIP/RAR, separate metadata or manually calculated metrics. Interrupted runs stay marked `.partial.csv`; existing files block reruns rather than being overwritten.

Read the [PCA-order instructions](docs/pca_order_experiment.md) for assignments, interruption handling and the leader's collection command.

## One-time setup

Use Python 3.12 and a Git clone, checked out at the exact reviewed commit distributed by the leader. This branch must be committed and published before official runs; a ZIP download does not include the required commit identity.

```powershell
git clone https://github.com/nhdung98/ProjectA.git
cd ProjectA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-experiments.txt
python -m src.data.prepare
python -m src.experiments.pca_order check
```

The original inputs are included in `data/raw/`. Preparation creates `data/processed/` locally. All members use the same frozen outer and inner folds in `results/splits/`. Scalers, feature filtering and PCA are fitted inside training folds, including inner GridSearchCV folds.

## Where things live

| Location | Purpose |
| --- | --- |
| [docs/](docs/README.md) | Current experiment instructions |
| `configs/pca_order.json` | Current assignments and search settings |
| [src/experiments/](src/experiments/README.md) | Runners and shared training code |
| `src/data/` and `data/` | Data preparation and source inputs |
| `results/splits/` | Frozen patient assignments and manifests |
| `results/pca_order/` | Generated member CSVs and leader comparisons; ignored by Git |
| [reports/](reports/README.md) | Findings and supporting research evidence |
| [archive/week01/](archive/week01/README.md) | Last week's instructions and original member submissions |
| `tests/` | Pipeline, split, validation and output checks |

## Previous experiments

Last week's SVM code remains runnable through `python -m src.experiments.svm`. Its [rerun guide](archive/week01/README.md) explains how to reproduce the original release or run the retained commands. Old submissions remain historical evidence; they are not inputs to this week's collector.

## Development and data exploration

Run the checks with `python -m unittest discover -s tests -v`. For guided exploration, install `requirements-notebooks.txt` and open [the notebook](notebooks/01_data_exploration.ipynb).

[Data sources](DATA_SOURCES.md) and [the supplied dataset notice](DATA_LICENSE.txt) document the inputs. Repeated gene records remain separate features; clinical columns are not model inputs. `configs/data.yaml` uses JSON syntax, which is valid YAML. The requirements files pin direct dependencies, not a complete environment lock.
