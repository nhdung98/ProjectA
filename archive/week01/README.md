# Week 1: original SVM experiments

This archive separates last week's material from the current PCA-order workflow. `docs/` holds its protocol, assignments, submission templates and register. `submissions/` preserves the original member files, including logs, predictions and review evidence. Moving a submission does not change its review or acceptance status.

## Rerun later

For exact historical code, use a separate clone checked out at the original release recorded in each run's manifest. Commit `92a4177` is the repository snapshot before the PCA-order workflow and this cleanup; individual runs may record an earlier commit. Avoid changing branches in a checkout with uncommitted work.

The retained legacy commands also work from the current repository root:

```powershell
python -m src.experiments.svm check
python -m src.experiments.svm list
python -m src.experiments.svm run --member 1
```

Follow the [running guide](docs/running_experiments.md) and [original protocol](docs/experiment_protocol.md) before assigning reruns. Legacy member numbers and assignments differ from this week's assignments. Official reruns need one agreed, clean release; do not pool runs from different commits without review.

The settings remain in `configs/svm.json`, code remains in `src/experiments/`, and generated reruns still go to `results/svm/`. Run commands from the repository root, not from this archive. The archived selection template is [here](docs/templates/svm_comparison_selection.json).

Original submissions are preserved without editing their recorded paths or checksums. Paths inside manifests and historical reports describe their original locations; resolve an old root-relative `submissions/...` path under `archive/week01/submissions/...` when inspecting these archived files. Embedded historical submission links may likewise refer to their original layout.

Read the [initial findings report](../../reports/initial_experiments_summary.md) for the results and their limitations. For the current experiment, return to [the main README](../../README.md).
