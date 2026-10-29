# TCGA SARC machine learning

Predict six sarcoma subtypes from gene expression: 254 patients and 20,531 gene records. The current round is **Protocol 3.0**: 13 pipelines benchmarked under one nested CV, with pipeline selection inside inner CV (META-SELECT).

## Current round

Read the [Protocol 3.0 proposal](docs/protocol_3.0_proposal.md) first, then the [nested CV diagram](docs/nested_cv_diagram.md) and the [example of the expected results](docs/mock_results_example.md). All numbers in the example are simulated.

Members run from `finalized-protocol3` at the leader's assigned revision. One `python -m src.p3 run` command automatically creates a result ZIP and a terminal LOG in per-member folders. Members push only those files on `results/memberN-roundA` (or `roundB`); the leader reviews and decides whether to merge. No manual result aggregation or copying is required. The [run guide](docs/protocol3_runbook.md) is the authoritative setup and submission guide.

## One-time setup

Use Python 3.12 and a Git clone, checked out at the exact reviewed commit distributed by the leader. This branch must be committed and published before official runs; a ZIP download does not include the required commit identity.

```powershell
git clone https://github.com/nhdung98/ProjectA.git
cd ProjectA
git switch finalized-protocol3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-protocol3.txt
python -m src.data.prepare
python -m src.p3 check
```

The original inputs are included in `data/raw/`. Preparation creates `data/processed/` locally. All members use the same frozen outer and inner folds in `results/splits/`. Scalers, feature filtering and PCA are fitted inside training folds, including inner GridSearchCV folds.

## Where things live

| Location | Purpose |
| --- | --- |
| [docs/](docs/README.md) | Protocol 3.0, architecture notes and research |
| `src/p3/` | Protocol 3.0 runner, analysis and final model |
| [src/experiments/](src/experiments/README.md) | Protocol 2.0 runner and the shared data, split and metric code |
| `experiments/p3.0/` | Local intermediate runs and leader-extracted evidence |
| `results/p3/submissions/memberN/` | Automatically packaged member result ZIPs |
| `results/p3/logs/memberN/` | Automatically captured member terminal LOGs |
| `src/data/` and `data/` | Data preparation and source inputs |
| `results/splits/` | Frozen patient assignments and manifests |
| [reports/](reports/README.md) | Findings and supporting research evidence |
| [archive/week01/](archive/week01/README.md) | SVM round (protocol 2.0): instructions and original member submissions |
| [archive/week02/](archive/week02/README.md) | PCA-order round: instructions and the commit that holds its runner |
| `tests/` | Pipeline, split, validation and output checks |

## Previous experiments

The SVM code from protocol 2.0 remains runnable through `python -m src.experiments.svm`. Its [rerun guide](archive/week01/README.md) explains how to reproduce the original release or run the retained commands. Old submissions remain historical evidence; they are not inputs to the Protocol 3.0 analysis.

## Development and data exploration

Run the checks with `python -m unittest discover -s tests -v`. For guided exploration, install `requirements-notebooks.txt` and open [the notebook](notebooks/01_data_exploration.ipynb).

[Data sources](DATA_SOURCES.md) and [the supplied dataset notice](DATA_LICENSE.txt) document the inputs. Repeated gene records remain separate features; clinical columns are not model inputs. `configs/data.yaml` uses JSON syntax, which is valid YAML. The requirements files pin direct dependencies, not a complete environment lock.
