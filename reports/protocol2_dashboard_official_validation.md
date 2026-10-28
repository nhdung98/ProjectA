# Official results dashboard integration

Batch: `windows-official-01`.

Training release: `87f3e6ce1bb3e7fa53e513a22b480abb63998882`.

Published results: `67ad3e764dadf13827421ab2d6f78f85809b42b3`, repository `nhdung98/ProjectA`, remote branch `origin/Vy/protocol2-results`.

The evidence ZIP was copied with binary Git blob I/O to `results/dashboard-inputs/67ad3e7/evidence_bundle.zip`. Its SHA-256 is `a0a7311bb31f3aa6c11be9fbaa751fe82eb8ad9b3d59781a117fa6e998644b7c`. Official evidence was not modified. The report's new paired results-provenance arguments verify exact ZIP bytes against the results commit before rendering, then display the full results SHA separately from the training SHA.

## Deliverables

- HTML: `results/dashboards/windows-official-01-67ad3e7-final/report.html`.
- PNGs: `results/dashboards/windows-official-01-67ad3e7-final/figures/` — 53 files at 300 dpi: five overview charts plus confusion/subtype charts for each of 24 configurations.
- Provenance: `results/dashboards/windows-official-01-67ad3e7-final/report_provenance.json`.
- Reusable notebook: `notebooks/02_protocol2_results_dashboard.ipynb`, defaults to official inputs and publication provenance, with no stored outputs.
- Executed notebook: `results/dashboards/windows-official-01-notebook-67ad3e7-final/official_results.ipynb`. Its sibling report/figures are a second execution of the same official inputs.
- Synthetic previews remain separately under `results/dashboards/synthetic-demo-final/`; they are never inputs to the official report.

## Verification

Run the reporting environment with `PROTOCOL2_OFFICIAL_ZIP=results/dashboard-inputs/67ad3e7/evidence_bundle.zip` and `python -B -m unittest discover -s tests -p 'test_dashboard*.py' -v`. All **14 tests passed**: 11 generic dashboard tests and three real-evidence integration tests. Log: `results/dashboard-development/official-tests.log`.

The official tests independently use standard-library CSV parsing and arithmetic to check all 72 repeat Macro-F1/balanced-accuracy scores, 24 repeat means and sample SDs per metric, 432 subtype rows and 2,592 confusion cells. Recomputed aggregate precision, recall and F1 agree to 12 decimal places. No patient predictions were read or regenerated. Confusion figure arrays match official pooled counts and row percentages; subtype bars, ranking bars and stability lines match source metrics. Each configuration has 762 held-out prediction events over three repeats, representing the same 254 patients. Saved audit records total 360 outer folds across 24 configurations; all four scaler/reduction pipelines contain six configurations.

All five CSV payloads in the ZIP match the corresponding Git files at the results commit byte-for-byte. Full ZIP entry checksums and original validation attestations pass. The source training SHA matches the frozen release. This establishes consistency with published evidence, not an independent rerun of patient-level validation or proof of execution authenticity.

All three notebook code cells were executed through a real Python 3.12 Jupyter kernel using official inputs, without synthetic/partial flags. Runtime labels were adjusted to avoid collisions in the real data; generation and tests were repeated after that change. The final HTML includes all 24 selector options, all detail panels, and the official batch and commit identities. Both CLI and notebook outputs are generated separately, without overwriting prior reports.

Browser interaction remains **UNVERIFIED**: the available browser tool previously rejected local `file:` URLs under its URL-security policy. No workaround server or alternate browser surface was used. HTML structure and image assets can be inspected without that interaction; a person should open the report in a desktop browser and select several configurations before distribution. This reporting execution was on macOS, not Windows. Windows instructions are provided but not claimed executed. Some real configurations have nearly identical runtime/performance, so leader lines identify points without shifting their coordinates.

## Git protection and proposed commit plan

Before fetching, all nine uncommitted dashboard source files were copied into `results/dashboard-development/pre-official-backup/dashboard-work.zip`, with per-file SHA-256 inventory and a tracked-diff snapshot. These backups remain ignored and untouched. Fetch updated only remote metadata. No branch switch, merge, commit, push, model training or official evidence edit occurred.

The active branch remains `Vy/pipeline-development`, HEAD `87f3e6ce1bb3e7fa53e513a22b480abb63998882`. The tracked working tree and index are unchanged; the following 11 dashboard files are untracked additions (including updates to the backed-up dashboard work):

1. `docs/protocol2_dashboard.md`
2. `notebooks/02_protocol2_results_dashboard.ipynb`
3. `reports/protocol2_dashboard_validation.md`
4. `reports/protocol2_dashboard_official_validation.md`
5. `requirements-dashboard.txt`
6. `src/reporting/__init__.py`
7. `src/reporting/dashboard_inputs.py`
8. `src/reporting/protocol2_dashboard.py`
9. `tests/dashboard_fixture.py`
10. `tests/test_dashboard.py`
11. `tests/test_dashboard_official.py`

Dashboard source is maintained on the dedicated branch
`Vy/protocol2-dashboard`, based on the frozen Protocol 2.0
training release. The source commit includes 13 dashboard
source, notebook, test, and documentation files.

Before publishing, review the staged diff, run
`git diff --cached --check`, and verify all 16 dashboard
automated tests.

Keep generated HTML, PNG figures, copied evidence ZIPs,
environments, backups, and patient-level data outside
the dashboard source commit.

The official results can be retrieved from the verified
Protocol 2.0 results commit. Integration with the results
branch is optional and should be evaluated separately.