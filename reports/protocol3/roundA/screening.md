# Round A screening report

Technical checks and inner-validation results only. Round A does not predict outer test patients, so this report contains no outer-test performance estimates. Numbers use a decimal comma (0,75 means 0.75).

## 1. Completion and runtime

Check that every pipeline finished all five outer-training searches. A fit is one training operation. Seconds/fit uses accumulated inner-fit and refit time; wall minutes is elapsed fold time and can be shorter when fits run in parallel. Setup and final packaging are excluded. Member identifies the assigned batch, not necessarily the person operating the machine. Dev indicates development mode. Different computers and parallel settings prevent a controlled speed comparison.

| Pipeline | Member | Commit | Dev | Status | Folds | Fits | Seconds/fit | Wall minutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01-MF | 1 | bf2c2ba20 | no | complete | 5/5 | 25 | 0,11 | 0,1 |
| P01-ST | 1 | bf2c2ba20 | no | complete | 5/5 | 25 | 0,10 | 0,1 |
| P02 | 1 | bf2c2ba20 | no | complete | 5/5 | 105 | 0,32 | 0,6 |
| P03 | 1 | bf2c2ba20 | no | complete | 5/5 | 105 | 0,31 | 0,6 |
| P04 | 1 | bf2c2ba20 | no | complete | 5/5 | 405 | 0,31 | 2,2 |
| P05 | 1 | bf2c2ba20 | no | complete | 5/5 | 105 | 0,38 | 0,7 |
| P06 | 2 | 26e8d1125 | no | complete | 5/5 | 105 | 1,20 | 0,7 |
| P07 | 2 | bf2c2ba20 | no | complete | 5/5 | 185 | 223,95 | 107,1 |
| P08 | 2 | 26e8d1125 | no | complete | 5/5 | 305 | 1,09 | 1,5 |
| P09 | 3 | bf2c2ba20 | no | complete | 5/5 | 305 | 0,30 | 1,6 |
| P10 | 3 | bf2c2ba20 | no | complete | 5/5 | 305 | 0,81 | 4,3 |
| P11 | 4 | bf2c2ba20 | no | complete | 5/5 | 105 | 0,19 | 0,4 |
| P12 | 4 | bf2c2ba20 | no | complete | 5/5 | 85 | 2,09 | 3,0 |
| P13 | 4 | bf2c2ba20 | no | complete | 5/5 | 165 | 0,17 | 0,5 |

## 2. Warnings and convergence

Warnings flag conditions that need review, including failure to converge. Refit iterations shows the largest recorded iteration count among outer-training refits versus the allowed limit; it does not summarize every inner fit. N/a means this iteration comparison is not reported for that model. Zero recorded warnings is encouraging but does not prove scientific correctness.

| Pipeline | Total | Warning categories | Refit iterations (maximum/limit) | Example |
| --- | --- | --- | --- | --- |
| P01-MF | 0 | none | n/a |  |
| P01-ST | 0 | none | n/a |  |
| P02 | 0 | none | n/a |  |
| P03 | 0 | none | n/a |  |
| P04 | 0 | none | n/a |  |
| P05 | 0 | none | n/a |  |
| P06 | 0 | none | 197/5000 |  |
| P07 | 0 | none | 4375/10000 |  |
| P08 | 0 | none | 175/5000 |  |
| P09 | 0 | none | 183/5000 |  |
| P10 | 0 | none | 126/5000 |  |
| P11 | 0 | none | n/a |  |
| P12 | 0 | none | n/a |  |
| P13 | 0 | none | n/a |  |

## 3. Selected parameters and inner-validation scores

Each row describes one outer fold's training data. Inner CV compares parameter combinations; g* is the combination with the highest mean inner macro-F1, using the declared tie rule. R1-F1 means repeat 1, fold 1. These scores were used to choose parameters, so they are not independent test scores or final evidence that one pipeline is better. An empty parameter dictionary means there was nothing to tune.

| Pipeline | Fold | Selected parameters (g*) | Inner macro-F1 |
| --- | --- | --- | --- |
| P01-MF | R1·F1 | {} | 0,097 |
| P01-MF | R1·F2 | {} | 0,098 |
| P01-MF | R1·F3 | {} | 0,097 |
| P01-MF | R1·F4 | {} | 0,097 |
| P01-MF | R1·F5 | {} | 0,096 |
| P01-ST | R1·F1 | {} | 0,153 |
| P01-ST | R1·F2 | {} | 0,159 |
| P01-ST | R1·F3 | {} | 0,157 |
| P01-ST | R1·F4 | {} | 0,138 |
| P01-ST | R1·F5 | {} | 0,153 |
| P02 | R1·F1 | {"model__C": 0.1} | 0,741 |
| P02 | R1·F2 | {"model__C": 0.1} | 0,774 |
| P02 | R1·F3 | {"model__C": 0.1} | 0,676 |
| P02 | R1·F4 | {"model__C": 0.1} | 0,772 |
| P02 | R1·F5 | {"model__C": 0.01} | 0,736 |
| P03 | R1·F1 | {"model__C": 0.01} | 0,743 |
| P03 | R1·F2 | {"model__C": 1} | 0,772 |
| P03 | R1·F3 | {"model__C": 0.01} | 0,712 |
| P03 | R1·F4 | {"model__C": 0.1} | 0,772 |
| P03 | R1·F5 | {"model__C": 0.1} | 0,726 |
| P04 | R1·F1 | {"model__C": 0.1, "select__k": 500} | 0,780 |
| P04 | R1·F2 | {"model__C": 1, "select__k": 150} | 0,772 |
| P04 | R1·F3 | {"model__C": 0.01, "select__k": 150} | 0,712 |
| P04 | R1·F4 | {"model__C": 0.1, "select__k": 150} | 0,772 |
| P04 | R1·F5 | {"model__C": 0.01, "select__k": 2000} | 0,765 |
| P05 | R1·F1 | {"model__C": 0.01} | 0,722 |
| P05 | R1·F2 | {"model__C": 0.01} | 0,738 |
| P05 | R1·F3 | {"model__C": 0.01} | 0,675 |
| P05 | R1·F4 | {"model__C": 0.01} | 0,698 |
| P05 | R1·F5 | {"model__C": 0.01} | 0,687 |
| P06 | R1·F1 | {"model__C": 10} | 0,737 |
| P06 | R1·F2 | {"model__C": 0.001} | 0,749 |
| P06 | R1·F3 | {"model__C": 0.01} | 0,683 |
| P06 | R1·F4 | {"model__C": 0.001} | 0,730 |
| P06 | R1·F5 | {"model__C": 0.001} | 0,720 |
| P07 | R1·F1 | {"model__C": 0.1, "model__l1_ratio": 0.5} | 0,752 |
| P07 | R1·F2 | {"model__C": 1, "model__l1_ratio": 0.1} | 0,740 |
| P07 | R1·F3 | {"model__C": 0.01, "model__l1_ratio": 0.1} | 0,733 |
| P07 | R1·F4 | {"model__C": 0.1, "model__l1_ratio": 0.5} | 0,764 |
| P07 | R1·F5 | {"model__C": 1, "model__l1_ratio": 0.9} | 0,733 |
| P08 | R1·F1 | {"model__C": 0.001, "model__alpha": 0.5} | 0,737 |
| P08 | R1·F2 | {"model__C": 0.001, "model__alpha": 0.5} | 0,750 |
| P08 | R1·F3 | {"model__C": 10, "model__alpha": 1} | 0,699 |
| P08 | R1·F4 | {"model__C": 0.1, "model__alpha": 0.5} | 0,709 |
| P08 | R1·F5 | {"model__C": 0.1, "model__alpha": 1} | 0,706 |
| P09 | R1·F1 | {"model__C": 0.01, "select__k": 2000} | 0,796 |
| P09 | R1·F2 | {"model__C": 0.01, "select__k": 2000} | 0,742 |
| P09 | R1·F3 | {"model__C": 0.001, "select__k": 1000} | 0,747 |
| P09 | R1·F4 | {"model__C": 0.01, "select__k": 1000} | 0,754 |
| P09 | R1·F5 | {"model__C": 0.1, "select__k": 2000} | 0,764 |
| P10 | R1·F1 | {"model__C": 0.01, "select__k": 500} | 0,797 |
| P10 | R1·F2 | {"model__C": 0.001, "select__k": 500} | 0,744 |
| P10 | R1·F3 | {"model__C": 0.1, "select__k": 500} | 0,731 |
| P10 | R1·F4 | {"model__C": 0.01, "select__k": 1000} | 0,751 |
| P10 | R1·F5 | {"model__C": 0.001, "select__k": 500} | 0,760 |
| P11 | R1·F1 | {"model__shrink_threshold": null} | 0,633 |
| P11 | R1·F2 | {"model__shrink_threshold": null} | 0,634 |
| P11 | R1·F3 | {"model__shrink_threshold": null} | 0,628 |
| P11 | R1·F4 | {"model__shrink_threshold": null} | 0,643 |
| P11 | R1·F5 | {"model__shrink_threshold": null} | 0,647 |
| P12 | R1·F1 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,650 |
| P12 | R1·F2 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,686 |
| P12 | R1·F3 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,604 |
| P12 | R1·F4 | {"model__max_features": 0.01, "model__min_samples_leaf": 3} | 0,673 |
| P12 | R1·F5 | {"model__max_features": "sqrt", "model__min_samples_leaf": 3} | 0,683 |
| P13 | R1·F1 | {"model__n_neighbors": 1, "select__k": 100} | 0,741 |
| P13 | R1·F2 | {"model__n_neighbors": 3, "select__k": 500} | 0,724 |
| P13 | R1·F3 | {"model__n_neighbors": 5, "select__k": 500} | 0,681 |
| P13 | R1·F4 | {"model__n_neighbors": 3, "select__k": 100} | 0,764 |
| P13 | R1·F5 | {"model__n_neighbors": 5, "select__k": 100} | 0,742 |

## 4. Search-grid boundaries (same edge selected in at least 3/5 folds)

A grid is the list of parameter values tested. Repeatedly selecting its smallest or largest value may suggest trying beyond that range; it does not prove that a better value exists. Extend once is the protocol's recommendation for a single extension before freezing, followed by rerunning the affected Round A pipeline. A natural limit cannot be extended; short grids are exempt under the declared rule. These are recommendations only: this report changes no settings.

| Pipeline | Parameter | Edge | Folds | Recommended action |
| --- | --- | --- | --- | --- |
| P04 | select__k | 150 | 3/5 | extend once: one step past 150; choose the value |
| P05 | model__C | 0.01 | 5/5 | extend once: add 0.001 |
| P06 | model__C | 0.001 | 3/5 | extend once: add 0.0001 |
| P09 | select__k | 2000 | 3/5 | extend once: add 4000 |
| P10 | select__k | 500 | 4/5 | extend once: add 250 |
| P11 | model__shrink_threshold | None | 5/5 | natural limit: nothing to extend |
| P12 | model__max_features | sqrt | 4/5 | not applicable: only 2 grid values |
| P12 | model__min_samples_leaf | 3 | 5/5 | not applicable: only 2 grid values |
| P13 | select__k | 100 | 3/5 | not applicable: only 2 grid values |

## 5. Reference reproduction check (P02)

P02 repeats the previous SVM reference configuration. This compares every available candidate's inner-fold score with the archived run and reports the largest absolute difference. A match supports reproducibility of that reference search; it does not validate all other models or estimate performance on new patients.

Maximum absolute difference from archived Round 1 inner scores: 2.22e-16: **match**.

## 6. Before creating the `p3.0-frozen` tag

Freezing locks the code and configuration for official Round B evaluation. Resolve technical issues and the protocol's boundary decisions first. Round A searches are screening evidence; Round B runs all three repeats separately and produces outer-test predictions.

- Resolve errors and review warnings in sections 1-2, documenting any accepted warnings.
- For each extend-once recommendation in section 4, agree the value, extend the grid once in `configs/protocol3.json`, rerun the affected Round A pipeline with `--replace`, and regenerate this report. Preserve earlier submissions.
- Do not remove pipelines because their inner scores are low. Exclusion is permitted only for inability to run within the declared time budget.
