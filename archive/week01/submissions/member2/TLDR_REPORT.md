# Member 2 (Hung) – Executive Summary & Results Report

**Submitter:** Bui Tien Hung (Member 2)  
**Branch:** `member2-svm-submissions`  
**Execution Commit:** `5d9076790437c7be304395ff702e9f4f11136899` (verified clean working tree)  
**Protocol Version:** 2.0 (Nested Stratified CV: 5 outer folds × 3 repeats, 4 inner folds)  
**Pipeline:** $\log_2(x+1) \to \text{VarianceThreshold}(0) \to \text{StandardScaler} \to \text{ANOVA SelectKBest} \to \text{SVC}$  

---

## 1. Executive Summary
* **Assigned Pipeline**: `StandardScaler` + `ANOVA` feature selection on 50, 100, and 150 genes across Linear and RBF kernels (6 configurations total, 4,590 model fits).
* **Audit & Quality**: **100% of 6 configurations passed independent audit** with `validate_svm.py`. All `warnings.log` files are 0 bytes (no convergence or fit warnings). Zero data leakage (transformers fitted strictly inside inner/outer training folds).
* **Key Finding**: Feature size is the primary performance driver. Scaling gene count from 50 to 150 improves Macro-F1 by nearly **+8%** for Linear SVM.
* **Top Performing Model**: **`SVM-STD-ANOVA-150-LINEAR`** achieved **Macro-F1 of $0.772 \pm 0.003$** and Balanced Accuracy of **$0.767 \pm 0.007$**, with remarkably high stability across repeated splits.

---

## 2. Official Results Scoreboard

All metrics computed over 762 held-out test predictions (3 repeats of 254 patients):

| Configuration ID | Kernel | Genes ($k$) | Run ID | Status | Macro-F1 (Mean ± SD) | Balanced Acc (Mean ± SD) | Runtime |
|:---|:---:|:---:|:---|:---:|:---:|:---:|:---:|
| `SVM-STD-ANOVA-50-LINEAR` | Linear | 50 | `20261012T025050Z-d2d653e4` | ✅ Passed | $0.692 \pm 0.046$ | $0.690 \pm 0.035$ | 147s |
| `SVM-STD-ANOVA-50-RBF` | RBF | 50 | `20261012T025318Z-d1db4f6e` | ✅ Passed | $0.734 \pm 0.042$ | $0.730 \pm 0.042$ | 338s |
| `SVM-STD-ANOVA-100-LINEAR` | Linear | 100 | `20261012T025857Z-46a19635` | ✅ Passed | $0.735 \pm 0.007$ | $0.742 \pm 0.005$ | 145s |
| `SVM-STD-ANOVA-100-RBF` | RBF | 100 | `20261012T030123Z-14fb358a` | ✅ Passed | $0.765 \pm 0.025$ | $0.768 \pm 0.022$ | 324s |
| **`SVM-STD-ANOVA-150-LINEAR`** | **Linear** | **150** | `20261012T030648Z-7ff14d84` | **✅ Passed** | **$0.772 \pm 0.003$** | **$0.767 \pm 0.007$** | **138s** |
| `SVM-STD-ANOVA-150-RBF` | RBF | 150 | `20261012T030908Z-b74ed4f7` | ✅ Passed | $0.768 \pm 0.019$ | $0.764 \pm 0.020$ | 320s |

---

## 3. Analysis & Insights for the Team Leader

1. **Dimensionality Effect ($50 \to 100 \to 150$ genes)**:
   * **50 genes**: Underperforms (Macro-F1 0.692 – 0.734) with higher split variation ($\pm 0.046$). 50 genes appear insufficient to cleanly separate rare subtypes like SS (10 samples) and MPNST (9 samples).
   * **100 genes**: Noticeable leap (+4.3% in Linear, +3.1% in RBF).
   * **150 genes**: Delivers the strongest discrimination (Macro-F1 ~0.77), indicating that retaining more top-ranked ANOVA genes preserves key marker expression profiles without succumbing to the curse of dimensionality.

2. **Linear vs. RBF Comparison**:
   * At smaller dimensions ($k=50, 100$), the non-linear **RBF kernel** wins significantly over Linear (+4.2% at $k=50$, +3.0% at $k=100$).
   * At $k=150$, the **Linear kernel catches up and edges out RBF** ($0.772$ vs. $0.768$) while running in **less than half the time** (138s vs. 320s) and exhibiting **extremely low variance** ($\pm 0.003$ vs. $\pm 0.019$).
   * **Recommendation**: `SVM-STD-ANOVA-150-LINEAR` is our strongest candidate for the final model comparison.

3. **Stability & Reproducibility**:
   * Both `100-LINEAR` ($\text{SD} = 0.007$) and `150-LINEAR` ($\text{SD} = 0.003$) show outstanding stability across repeated patient reshufflings, confirming that ANOVA ranking combined with z-score standardization produces robust decision boundaries.

---

## 4. Deliverables & Handoff Locations

* **Git Tracking (Lightweight)**:
  * Documentation & summary: [`submissions/member2/README.md`](README.md)
  * Independent validation logs: `submissions/member2/logs/validate_*.log`
* **Shared Team Drive (Full Archives)**:
  * Packaged ZIPs containing all 762 predictions, search grids, fold-by-fold feature lists, and metrics:
    * `results/svm/SVM-STD-ANOVA-50-LINEAR_20261012T025050Z-d2d653e4.zip`
    * `results/svm/SVM-STD-ANOVA-50-RBF_20261012T025318Z-d1db4f6e.zip`
    * `results/svm/SVM-STD-ANOVA-100-LINEAR_20261012T025857Z-46a19635.zip`
    * `results/svm/SVM-STD-ANOVA-100-RBF_20261012T030123Z-14fb358a.zip`
    * `results/svm/SVM-STD-ANOVA-150-LINEAR_20261012T030648Z-7ff14d84.zip`
    * `results/svm/SVM-STD-ANOVA-150-RBF_20261012T030908Z-b74ed4f7.zip`
