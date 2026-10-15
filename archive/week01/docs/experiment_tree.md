# Experiment tree — SVM experiment

24 configurations; six per member. All branches use the same saved nested splits.

```text
254 patients
└── Outer: 5 stratified folds × 3 repeats
    ├── 50–51 held-out test patients
    └── 203–204 development patients
        └── Inner: 4 stratified folds; select by mean macro-F1
            └── log2(x+1) → training-only constant removal
                ├── MinMaxScaler
                │   ├── ANOVA — Member 1
                │   │   ├── 50 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 100 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 150 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   ├── PCA — Member 3
                │   │   ├── 50 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 100 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 150 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                ├── StandardScaler
                │   ├── ANOVA — Member 2
                │   │   ├── 50 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 100 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 150 genes
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   ├── PCA — Member 4
                │   │   ├── 50 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 100 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
                │   │   ├── 150 components
                │   │   │   ├── Linear: search C
                │   │   │   └── RBF: search C × gamma
```

C: `[0.01, 0.1, 1, 10, 100]`. RBF gamma: `["scale", 0.001, 0.01, 0.1]`.

After selection, refit the full pipeline on outer training patients and predict the untouched outer test patients. Each configuration saves 762 predictions. Total workload: 18,360 pipeline fits.

See the [protocol](experiment_protocol.md) and [member commands](running_experiments.md).
