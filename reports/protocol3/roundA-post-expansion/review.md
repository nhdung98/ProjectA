# Post-expansion Round A review

Corresponding execution logs and selected ZIP evidence were reviewed, and the
combined English screening report was regenerated. No training,
second extension, frozen tag or Round B execution was performed in this review.

## Selected evidence

Use expansion-1 results for P04, P05, P06, P09 and P10. Retain original results for
P01-MF, P01-ST, P02, P03, P07, P08, P11, P12 and P13. This selection follows the
approved rerun decision, not which run obtained a higher score. Exact ZIP names,
hashes and training commits are recorded in sources.csv.

All 14 entries completed five folds: 2,670 fits in the selected evidence set.
Recorded training warnings: zero. Both the original and expansion runs remain in
Git; the original Round A screening and comparison reports have not been replaced.

## Checks completed

- Selected ZIP output inventories and SHA-256 checksums match their manifests.
- Assigned member, exact pipeline specification, candidate grid, Python 3.12 and
  pinned package versions agree with the intended run.
- Inner candidate counts, score ranges/means, selected flags, tie-breaking,
  manifest winners, fit counts and train/test sample counts are consistent.
- Feature-details records cover all five folds, and warning counts agree.
- Corresponding execution logs end successfully and contain no traceback.
- Selected scientific implementation and saved split content match the current
  release. Two global config hashes are expected because only five grids changed;
  unaffected pipeline specifications match exactly. Those original runs do not
  need repeating solely to acquire the new global hash.
- No selected archive contains outer-test predictions.
- P02's largest candidate-level inner-score difference from the archived reference
  is 2.22e-16, consistent with numerical precision.

These checks establish consistency of submitted evidence; they do not constitute
independent reproduction of every training fit.

## Remaining boundary observations

P10 selects ANOVA k=250 in three of five folds. The one allowed expansion has
already been used: retain the current grid and document this limitation. P11's
no-shrinkage setting is a natural endpoint. P12's two-value searches and P13's
two-value gene-count search remain exempt under the declared screening rule.
No further expansion is proposed.

## Next decision

There are no unresolved execution failures or recorded training warnings in the
selected evidence. The leader can now confirm the final pipeline list, statistical
comparison settings and simplicity order, and freeze a common release for Round B.
Do not interpret these selected inner scores as final generalization performance.

Reproduce this review without training:

```powershell
python scripts/review_round_a_expansion.py
```

Read screening.md for the full tables and validation_review.json for the machine-
readable pipeline and log review. No freeze tag has been created as part of this review.
