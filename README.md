# TCGA-SARC reproducible SVM experiments

COS40005 Project A: classify six sarcoma subtypes using 254 patients and 20,531 source gene records.

Use **`python -m src.experiments.workflow`** for new Protocol 2.0 experiments. It wraps the existing scientific pipeline and nested search, retains the nine required artifacts, independently validates predictions, and builds consolidated evidence. Scientific settings remain in [configs/svm.json](configs/svm.json).

Official training will run on a separate native Windows PC. Use the [Windows PowerShell operator guide](docs/protocol2_windows.md); do not transfer the macOS `.venv`. The commands below are for macOS development.

## Setup on macOS

Use Python 3.12 in an isolated environment. Installation is explicit; the runner never installs or upgrades packages.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-protocol2-lock.txt
.venv/bin/python -m src.experiments.workflow prepare-data
.venv/bin/python -m src.experiments.workflow preflight
.venv/bin/python -m src.experiments.workflow smoke
```

Preparation is explicit, refuses overwrites, and publishes CRLF TSVs only after verifying the existing frozen dataset hash. Neither preparation nor preflight creates or changes split assignments or manifests. Run/resume never prepare data.

## Official execution after review

Review and commit the implementation first; official execution requires a clean checkout. This development branch remains uncommitted pending approval. Once approved, the operator runs:

```sh
.venv/bin/python -m src.experiments.workflow run --all --batch results/protocol2/vy-official-01
```

This starts the full 24-configuration batch. Do not run it to test installation. Successful completion automatically validates runs, generates reports, and writes aggregate-only `evidence_bundle.zip`.

Monitor from another terminal:

```sh
.venv/bin/python -m src.experiments.workflow status --batch results/protocol2/vy-official-01
```

Read the [workflow guide](docs/protocol2_workflow.md) for individual configurations, preprocessing branches, interruption/resume, private team export, and validation limits.

## Repository map

| Location | Purpose |
| --- | --- |
| `src/data/` | Source auditing and preparation |
| `src/experiments/` | Shared scientific code and workflow orchestration |
| `configs/svm.json` | Unchanged Protocol 2.0 cohort, grid, and seeds |
| `results/splits/` | Frozen outer/inner assignments and manifests |
| `results/protocol2/` | New official batches; ignored by Git |
| `results/protocol2-smoke/` | Diagnostic runs, excluded from official reports |
| `results/protocol2-development/` | Local implementation verification evidence |
| `tests/` | Synthetic execution, leakage, integrity, restart, and report tests |
| `archive/week01/` | Historical submissions and original Protocol 2.0 instructions |
| `reports/` | Historical research findings and evidence snapshots |

The retained [PCA-order workflow](docs/pca_order_experiment.md) is a separate experiment round. Its CSV-only results are not inputs here. Legacy SVM commands remain available. New workflow validation deliberately excludes historical folders; preserve their original commits and provenance separately.

Run `.venv/bin/python -m unittest discover -s tests -v` for automated checks. Tests use artificial datasets and temporary folders; they do not launch the complete TCGA batch. [The EDA notebook](notebooks/01_data_exploration.ipynb) requires optional notebook dependencies.

Read [data provenance](DATA_SOURCES.md) and the [supplied data notice](DATA_LICENSE.txt). Clinical columns and identifiers are excluded from predictors. Repeated gene records remain separate features. The lock pins versions, not platform-specific wheel hashes; Python build, installed packages, numerical libraries, platform and code hashes are recorded per batch.
