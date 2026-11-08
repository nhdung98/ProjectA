# Dung review: Protocol 3 result validation

Branch: `finalized-protocol3`, based on An's `protocol3` branch.

This review adds submission checks and regression tests. It preserves the pipeline
definitions, grids, filtering, nested CV, screening, META-SELECT, statistics and
deployment selection rules. Both dummy variants and all proposed pipelines remain.

Round B analysis now loads the verified cohort and saved splits before accepting
predictions. It checks all repeats, sample/patient identities, true labels, fold
assignments, declared candidates, inner-score means, tie-breaking and selected
parameters. Submitted configuration, training-code/split hashes and package versions
must match the analysis checkout. Output inventories must be complete.

Use the same reviewed source revision for every member's runs and collection.
Run `python -m unittest discover -s tests -p "test_protocol3*.py" -v`.
The added tests use synthetic evidence, not full TCGA experiments.

Local verification used Python 3.14.2 and scikit-learn 1.8.0, rather than the pinned
Python 3.12 / scikit-learn 1.7.2 environment. Verification in the pinned environment
and the existing technical screening/frozen-tag steps are still required before
official runs. A branch named finalized does not bypass those checks.

Checks establish consistency of submitted evidence; they do not prove that a
third party actually executed the reported training.
