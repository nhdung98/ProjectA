# Round A: single approved grid extension

Decision date: 6 November 2026. Dung requested following An's one-time extension
workflow. The original Round A evidence and reports remain unchanged.

| Pipeline | Additional value | Boundary observed in original screening |
| --- | --- | --- |
| P04 | ANOVA k = 100 | k = 150 in 3/5 folds |
| P05 | C = 0.001 | C = 0.01 in 5/5 folds |
| P06 | C = 0.0001 | C = 0.001 in 3/5 folds |
| P09 | ANOVA k = 4000 | k = 2000 in 3/5 folds |
| P10 | ANOVA k = 250 | k = 500 in 4/5 folds |

P04's grid has no constant lower-end spacing. The additional 100-gene value is a
conservative, interpretable step below 150, specified before the extension run;
it is not a claim about the optimal feature count. All original values remain,
and the existing declared candidate-order tie rule is retained.

No classifiers, preprocessing stages, class weights, CV splits, random seeds,
metrics or deployment-selection rules change. Only the five grids above expand.
This follows the proposal's shared-grid screening approach; the previously
discussed limitation of cross-fold adaptive search-space development still applies.

Rerun all candidates for each affected pipeline using the pinned Python 3.12
environment. The member identifiers below retain assignment/provenance; these
leader-operated reruns must not be attributed as newly executed by those members.

```powershell
python -m src.p3 run --round A --member 1 --pipeline P04 --pipeline P05 --jobs 2
python -m src.p3 run --round A --member 2 --pipeline P06 --jobs 2
python -m src.p3 run --round A --member 3 --pipeline P09 --pipeline P10 --jobs 2
```

There are 1,565 fits in this rerun: 505 + 125 + 125 + 405 + 405.
P07 and all other unaffected pipelines do not need this rerun.

Use an isolated checkout for extension runs so the original tracked loose results
and archives are preserved. New ZIPs/logs retain generated unique names. Do not
pass --replace against original submissions. When collecting mixed original and
extended Round A runs, select archives explicitly: the original comparison script
deliberately rejects duplicate pipelines and cannot blindly ingest both versions.

This is the one permitted extension. Any new boundary hit is recorded as a
limitation, not an instruction to extend a second time, even if the generic
screening helper emits another suggestion. Reviewing extension results and
creating/pushing p3.0-frozen are subsequent tasks; neither is performed merely
by publishing these settings.
