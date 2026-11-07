# Round A expansion 1: execution status

The five approved expansion runs completed. These are leader-operated reruns; member IDs retain the original batch assignment and do not identify who operated the computer. Original member submissions and the original Round A reports are preserved.

Training/config revision: `4b10b0a99faf9b623427a55491f216383e4eeb75`. Python 3.12.12 and all protocol-pinned package versions were verified. All 24 Protocol 3 tests passed in this environment before execution.

| Pipeline | Folds | Fits | Recorded training warnings | Wall minutes |
| --- | ---: | ---: | ---: | ---: |
| P04 | 5/5 | 505 | 0 | 1.33 |
| P05 | 5/5 | 125 | 0 | 0.38 |
| P06 | 5/5 | 125 | 0 | 0.87 |
| P09 | 5/5 | 405 | 0 | 1.34 |
| P10 | 5/5 | 405 | 0 | 1.27 |

Total: 1,565 fits. Each saved inner candidate, score mean, selected winner and output checksum was checked. No outer-test predictions were generated. No second extension, frozen tag or Round B run was performed.

## Submitted evidence

- ZIP: `results/p3/submissions/member1/roundA-member1-20261105T173755Z-f3a0bedd.zip`; LOG: `results/p3/logs/member1/20261106-003752-c081f405.log`.
- ZIP: `results/p3/submissions/member2/roundA-member2-20261105T173816Z-a8ddc550.zip`; LOG: `results/p3/logs/member2/20261106-003813-207900cb.log`.
- ZIP: `results/p3/submissions/member3/roundA-member3-20261105T174001Z-3bfd405e.zip`; LOG: `results/p3/logs/member3/20261106-003958-9f7cb97a.log`.

The config contains one additional value for each of P04/P05/P06/P09/P10. See docs/protocol3_expansion_decision.md. Reviewing the rerun outcomes and preparing the frozen release remain subsequent steps. Select these extension archives explicitly when combining with unaffected original pipelines; do not silently choose the highest-scoring rerun.
