# Running SVM experiment

Read the [protocol](experiment_protocol.md) first. Run commands from the repository root. The exact settings are in `configs/svm.json`; do not edit them independently.

Official runs require a Git clone of the team repository, checked out at the leader's reviewed commit. A ZIP download can be used for reading, but cannot supply the commit evidence required for official submissions.

## 1. Set up and check

Use Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-experiments.txt
python -m src.data.prepare
python -m src.experiments.svm check
python -m unittest discover -s tests -v
```

The leader prepares assignments once using `python -m src.experiments.svm prepare-splits`. Both outer and inner assignments are included in Git. Members load and verify them; they do not generate different splits. Existing files are never silently replaced.

## 2. Find your configurations

```powershell
python -m src.experiments.svm list
```

Members 1-4 own min-max/ANOVA, standard/ANOVA, min-max/PCA, and standard/PCA respectively. Each owns six configurations: three sizes crossed with two kernels.

## 3. Check one complete nested search

```powershell
python -m src.experiments.svm run --configuration SVM-MM-ANOVA-50-LINEAR --smoke
```

Smoke runs perform one outer fold's complete inner search but receive no final metrics. For an uncommitted implementation check, `--development` allows a full run; this cannot qualify as an official clean-commit submission.

## 4. Run your six configurations

Replace 1 with your member number:

```powershell
python -m src.experiments.svm run --member 1
```

Run from the team's agreed clean commit. Check `git status --short` first; it should show no changes. Keep personal notebook edits in a separate working copy or branch, and use a clean clone for official runs. Alternatively, repeat `--configuration ID` to select specific configurations. Every command creates new folders under `results/svm/<configuration>/<run-id>/`. A failed run stops; completed earlier configurations remain available. Do not run all 24 unless assigned a team-wide rerun.

The search temporarily caches identical training-fold preprocessing across parameter candidates. It never reuses a fitted transformation across different training folds, and removes the cache after each outer search. This saves repeated PCA work without changing the search grid.

## 5. Validate and submit

```powershell
python -m src.experiments.validate_svm results/svm/CONFIGURATION/RUN-ID --report results/svm/CONFIGURATION/RUN-ID/validation.json
```

Substitute actual folder names. Follow the [submission requirements](submission_requirements.md). The validator checks outer predictions and independently recalculates metrics, checks the saved search grid and chosen parameters, and verifies data, split, and training-code hashes. It does not rerun every model; a reviewer should additionally reproduce at least one agreed configuration from the same commit.
