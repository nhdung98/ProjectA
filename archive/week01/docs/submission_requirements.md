# Submission requirements — SVM experiment

Submit one archive per complete configuration. Use the agreed clean code commit; preserve every generated file. Do not choose the highest-scoring rerun silently.

## Required files

| File | Purpose |
| --- | --- |
| `config.json` | Exact shared settings and assigned configuration |
| `run_manifest.json` | Commit, data/split/code hashes, runtime, completion, and chosen parameters |
| `predictions.csv` | 762 outer held-out predictions |
| `metrics.json` | Repeat and subtype scores, summaries, and confusion matrices |
| `feature_details.json` | Features fitted on each outer training set |
| `search_results.json` | All candidate scores for four inner folds in every outer fold |
| `warnings.log` | Must be empty for acceptance |
| `validation.json` | Saved independent output audit |
| `submission.md` | Member name, configuration/run IDs, commit, runtime, and notes |

Use [the submission template](templates/submission.md). Run the validation command in the [running guide](running_experiments.md). Only complete, non-smoke, warning-free runs with all 15 outer folds and the full search evidence qualify. The selected parameters must maximize the saved mean inner score using the agreed tie rule.

Archive the complete run folder, share it through the team's normal shared folder, and provide the leader its location. Do not include environments or duplicated raw data. The reviewer extracts into a new folder without overwriting existing evidence, reruns the validator, checks the agreed clean commit and warnings, and records `pending_review`, `accepted`, `needs_rerun`, or `superseded` in [the submission register](submission_register.csv).

Development runs are not official member submissions. A peer should reproduce an agreed configuration and compare sorted predictions and metrics before accepting the team workflow. Follow [combining results](combining_results.md) for the comparison.
