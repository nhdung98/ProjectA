# Week 2: PCA-order experiment

This round compared scaling before PCA with scaling after PCA, using one CSV per member. Protocol 3.0 no longer reruns PCA pipelines, so the runner was removed from the current tree. The [original instructions](docs/pca_order_experiment.md) are kept here.

## Rerun or collect later

The runner, its config (`configs/pca_order.json`) and its tests exist at commit `e01c61e` on `main`. Member runs and the leader's `collect` command must use the exact release commit recorded in each member CSV, so check out that commit in a separate clone:

```powershell
git clone https://github.com/nhdung98/ProjectA.git ProjectA-pca-order
cd ProjectA-pca-order
git checkout e01c61e
```

Then follow the setup and commands in the archived instructions. For the current experiment, return to [the main README](../../README.md).
