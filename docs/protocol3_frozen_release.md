# Protocol 3.0 frozen release for Round B

Release tag: `p3.0-frozen`. The tag identifies the common release commit; obtain
its full SHA with `git rev-parse 'p3.0-frozen^{commit}'`. Creating this tag locally
does not publish it. Members must wait until the leader publishes the release.

## Confirmed experiment settings

- Preserve all 13 proposed pipelines, with two Dummy variants: 14 executable entries.
- Retain the single completed expansion: P04 adds k=100; P05 adds C=0.001;
  P06 adds C=0.0001; P09 adds k=4000; P10 adds k=250. All original values remain.
- No further grid expansion. P10's residual k=250 boundary is documented in the
  post-expansion screening report.
- Use the same 254-patient cohort, six labels, saved outer/inner assignments and
  seed 42. Outer validation has five folds repeated three times; inner CV has four folds.
- Fit learned preprocessing only on training data. Retain existing class weights,
  feature filters, resampling placement and classifier settings.
- Primary metric: macro-F1 from pooled held-out predictions within each repeat.
  Report the mean and sample SD across three repeats; SD is not a confidence interval.
- Parameter selection uses mean inner macro-F1 with the declared candidate-order
  tie rule. META-SELECT uses inner scores across P02-P13, with the declared
  simplicity rank and candidate ordering for exact ties. Dummy entries are excluded.
- Retain all 11 declared paired comparisons. Their definitions and ordering are
  recorded in `configs/protocol3.json`; comparisons that replace multiple stages
  are complete-strategy comparisons rather than isolated component effects.
- Bayesian correlated t-test: rho=0.2, primary ROPE +/-0.01, sensitivity ROPE
  +/-0.02, decision probability 0.95. Keep repeat 1 for the specified Wilson intervals.
- Preserve the deployment shortlist rule and simplicity order:
  P11, P03, P02, P05, P04, P06, P08, P09, P07, P10, P13, P12.
  The shortlist includes inconclusive comparisons; it is not proof of equivalence.
  META-SELECT evaluates its selection procedure, not the separately chosen deployed model.
- Python 3.12 and every package version declared in `configs/protocol3.json` are required.

These settings confirm the existing executable design; no scientific settings
were changed while preparing the release tag. The source configuration, rather
than this prose summary, defines exact grids and comparison pairs.

## Member commands after publication

From a clone with the pinned environment and prepared data, fetch and select the
exact tag. A detached checkout is intentional and ensures a common source revision.

```powershell
git fetch origin --tags
git switch --detach p3.0-frozen
python -m src.p3 check
```

Each member runs only their assigned batch:

```powershell
python -m src.p3 run --round B --member 1 --jobs 2
python -m src.p3 run --round B --member 2 --jobs 2
python -m src.p3 run --round B --member 3 --jobs 2
python -m src.p3 run --round B --member 4 --jobs 2
```

All three repeats run afresh; Round A results do not substitute for Round B.
Member IDs identify batches; any reassignment of operators must be documented.
No --development override or changes to code/config/splits are permitted.

ZIPs and LOGs are created automatically under `results/p3/submissions/memberN/`
and `results/p3/logs/memberN/`. From the release checkout, create a result branch
after running. Example for member 1:

```powershell
git switch -c results/member1-roundB
git add results/p3/submissions/member1/ results/p3/logs/member1/
git commit -m "Submit member 1 Round B results and logs"
git push -u origin results/member1-roundB
```

The leader reviews result branches before deciding whether to merge. Do not
force-push, replace the frozen tag, or push results directly onto the shared release branch.

## Separate analyses

Optional S-TSS still needs its predefined drop threshold; S-206 needs the reviewed
sample list. They are not prerequisites for the main Round B runs and are not
declared ready by this release. Any later scientific changes must be separately
versioned rather than silently changing the frozen release.
