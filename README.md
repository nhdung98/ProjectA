# TCGA SARC machine learning

We compare machine learning pipelines that predict 6 sarcoma subtypes from gene expression. The prepared dataset has 254 patients and 20,531 gene records. Gene expression measures how active a gene is in a sample; the subtype is the label we predict.

## Start here

For official member runs, clone the repository and use the reviewed commit. A ZIP download does not contain the Git history needed to record that commit.

```powershell
git clone https://github.com/nhdung98/ProjectA.git
cd ProjectA
```

Use Python 3.12. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-experiments.txt
python -m src.data.prepare
python -m src.experiments.svm check
python -m unittest discover -s tests -v
```

The two original inputs are included in `data/raw/`. Preparation creates `data/processed/` locally. The runner checks the pinned numerical package versions and the shared split assignments before experiments.

Read the [team guide](docs/team_guide.md) for the workflow, assignments, submission rules, and validation commands. Read the [experiment protocol](docs/experiment_protocol.md) before running an experiment. Official runs should use the team's agreed commit with a clean working tree.

## Repository layout

| Folder or file | Purpose |
| --- | --- |
| `configs/` | Shared data paths and experiment settings |
| `data/raw/` | Two unchanged source datasets included in Git |
| `data/processed/` | Generated datasets and merge checks; ignored by Git |
| `src/data/` | Audit the inputs and prepare the dataset |
| `src/experiments/` | Shared training, splits, metrics, validation, and comparison tools |
| `notebooks/` | Guided data exploration |
| `tests/` | Checks for leakage prevention, splits, metrics, and output review |
| `docs/` | Team instructions, protocol, submission register, and templates |
| `reports/` | Accepted comparison summaries and validation evidence |
| `results/` | Local experiment outputs; only common splits are included in Git |

## Explore the data

```powershell
python -m pip install -r requirements-notebooks.txt
```

Open [01_data_exploration.ipynb](notebooks/01_data_exploration.ipynb) and select the virtual environment's Python interpreter. Run preparation first, then restart the notebook kernel and run all cells. The notebook explains the data and reads prepared outputs. It does not fit experiment preprocessing.

## Run an experiment

List the configurations, then run your assigned ID:

```powershell
python -m src.experiments.svm list
python -m src.experiments.svm run --member 1
```

The current round has 24 SVM configurations, six per member. Each configuration performs 15 outer refits, with four-fold inner GridSearch for each: five stratified outer folds repeated three times. Preprocessing is fitted inside training folds. Follow the [running guide](docs/running_experiments.md) and [submission requirements](docs/submission_requirements.md) to validate and hand off the outputs.

See the [experiment tree](docs/experiment_tree.md) for all 24 configurations and member assignments.

## Read the results

Follow the [comparison guide](docs/combining_results.md) to review accepted SVM submissions across repeats and subtypes. Accepted SVM comparison results are not available yet.

## Data and dependencies

[DATA_SOURCES.md](DATA_SOURCES.md) records provenance and input checksums. [DATA_LICENSE.txt](DATA_LICENSE.txt) preserves the supplied dataset notice. Repeated gene records remain separate features; clinical columns are not model inputs.

`configs/data.yaml` uses JSON syntax, which is valid YAML; preserve that syntax when editing. `configs/svm.json` contains the current agreed SVM settings. Paths resolve from the repository root.

`requirements.txt` installs data preparation dependencies. `requirements-experiments.txt` adds the numerical experiment packages, and `requirements-notebooks.txt` adds optional notebook and plotting tools. These files pin direct dependencies; they are not a complete environment lock.

## PCA-order experiment: one command, one CSV

Use the [PCA-order protocol](docs/pca_order_experiment.md) for this week's assignments and setup. After setup, each member runs:

```powershell
python -m src.experiments.pca_order check
python -m src.experiments.pca_order run --member 1
```

Replace `1` with your assigned member number. Submit only `results/pca_order/memberN_results.csv`; partial files are not submissions. The collector recalculates team metrics from the four member CSVs. Official runs must use the same reviewed commit and a clean working tree.
