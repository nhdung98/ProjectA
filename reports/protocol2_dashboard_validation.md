# Dashboard development validation — 2026-10-28

This is software-development evidence, not official SVM experiment evidence. No model was trained, no predictions were generated, and no historical experiment files were edited. The reviewed training release remains `87f3e6ce1bb3e7fa53e513a22b480abb63998882` on `Vy/pipeline-development`. `git diff --exit-code 87f3e6ce1bb3e7fa53e513a22b480abb63998882` passed: all tracked release files remain unchanged. Dashboard files are new, uncommitted additions.

## New source files

1. `src/reporting/__init__.py`
2. `src/reporting/dashboard_inputs.py`
3. `src/reporting/protocol2_dashboard.py`
4. `notebooks/02_protocol2_results_dashboard.ipynb` (no stored outputs)
5. `requirements-dashboard.txt`
6. `tests/dashboard_fixture.py`
7. `tests/test_dashboard.py`
8. `docs/protocol2_dashboard.md`
9. `reports/protocol2_dashboard_validation.md`

## Verification actually performed

| Check | Result and scope |
|---|---|
| Separate reporting environment | Python 3.12; pinned direct dependencies installed under `results/dashboard-development/.venv`. `python -m pip check`: no broken requirements. Training `.venv` unchanged. |
| Automated tests | `MPLCONFIGDIR=results/dashboard-development/mpl-cache results/dashboard-development/.venv/bin/python -B -m unittest discover -s tests -p test_dashboard.py -v`: **10 passed**, 5.325 seconds in the final run. Log: `results/dashboard-development/dashboard-tests-final.log`. |
| Chart inputs | Tests cover all 24 configurations; repeat coverage, confusion totals and normalization; inconsistent metrics, negative counts/runtime, missing/duplicate rows, NaN, wrong labels and unexpected columns. |
| Validation | Tests cover failed/missing runs, incomplete subsets, full rows with failed/incomplete batch attestations, explicit synthetic opt-in, input hash mismatch and mutation during rendering. |
| ZIPs | Tests cover exact entry hashes, corruption rejection, no extraction, and sanitized external copies whose export-specific hashes differ from original source hashes. |
| Read-only/privacy | Rendering tests compare input bytes before/after, refuse evidence-overlapping outputs and overwrites, and verify no fixture private paths appear in HTML. Only allowlisted aggregate fields are exported. |
| Full CLI generation | Generated `results/dashboards/synthetic-demo-final/report.html` from an explicit 24-configuration synthetic fixture. HTML parser verified 24 selector options, 24 detail panels and 53 embedded PNG images. All 53 standalone PNGs verified at 300 dpi. HTML size: 17,141,680 bytes. |
| Notebook | `nbformat.validate` passed. All three code cells executed through `nbclient`/a real Python kernel with a synthetic two-configuration partial batch; no error outputs. The first sandbox attempt was blocked from opening a local kernel socket; the approved retry succeeded. Executed copy: `results/dashboard-development/executed-dashboard.ipynb`; report: `results/dashboards/notebook-demo-final/report.html`. |
| Visual inspection | Inspected ranking, heatmap, runtime scatter, confusion counts/percentages, subtype F1, repeat stability and validation overview PNGs. Short numbered runtime labels with a separate key replaced overlapping full labels. |
| Browser interaction | Not verified: the embedded browser's URL policy refused the local `file:` URL. No workaround or network server was used. HTML structure and embedded assets were checked; manually exercise the selector in a desktop browser before distribution. |
| Windows | Commands reviewed against the implemented CLI; actual Windows installation, tests, notebook execution and browser interaction remain unverified. |

Final full-preview command:

```sh
MPLCONFIGDIR=results/dashboard-development/mpl-cache results/dashboard-development/.venv/bin/python -B -m src.reporting.protocol2_dashboard --input results/dashboard-development/synthetic-input --output results/dashboards/synthetic-demo-final --allow-synthetic
```

This command has already run; a repeat must use a **new** output directory. Outputs deliberately refuse replacement.

## Limits and proposed integration

No completed official release batch was available for end-to-end verification. Synthetic fixtures exercise the frozen aggregate schema but cannot establish authenticity of research results or prove patient-level validation. The reporter checks original audit attestations and aggregate arithmetic, not the original raw-data/split/prediction audit. Hashes are corruption checks, not signatures. Only direct plotting dependencies are pinned; OS/fonts/transitive dependencies may change image bytes.

Keep all generated files in `results/dashboard-development/` and `results/dashboards/` out of Git, including fixtures, environment, caches, execution helper, logs, executed notebook, HTML, provenance JSON and PNGs. Preliminary `synthetic-demo-01`/`notebook-demo-01` attempts are development-only; use `synthetic-demo-final` as the delivered preview.

After Windows training: preserve the frozen training SHA; complete its existing validation/export; transfer the external aggregate ZIP to a separate reporting checkout; run the documented CLI without synthetic/partial flags; confirm source SHA and 24/24 validated status; manually review the selector and charts, then share aggregate HTML/PNGs. The dashboard additions can undergo their own review and later commit without altering the training release. No commit, push, merge, branch change or official training was performed here.
