# Team guide current SVM experiments

Start with the [project overview](../README.md) and [data exploration notebook](../notebooks/01_data_exploration.ipynb), then follow this order.

If a biology, data, or statistics term is unfamiliar, look it up in the [glossary](glossary.md).

1. Read [the experiment protocol](experiment_protocol.md): shared data, preprocessing, nested validation, assignments, and search rules.
2. Follow [running experiments](running_experiments.md): verify splits, smoke-check, and run your six assigned configurations.
3. Follow [submission requirements](submission_requirements.md): audit your outputs and hand off the complete run folder using [the template](templates/submission.md).
4. The leader/reviewer records decisions in [the submission register](submission_register.csv).
5. Follow [combining results](combining_results.md) to compare accepted runs across repeats and subtypes.

Current settings: [configs/svm.json](../configs/svm.json). Current runner: `python -m src.experiments.svm`.

View [the experiment tree](experiment_tree.md) for the full assignment map.

Instructions live in `docs/`; accepted reports in `reports/`; local full outputs in `results/`. Current SVM experiments have not yet produced accepted comparison results.
