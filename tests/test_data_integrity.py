"""Run with python -m unittest discover -s tests -v."""
import copy
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.experiments.metrics import summarize
from src.experiments.pipeline import build_pipeline
from src.experiments.common import ROOT, sha256, shared_splits, write_json
from src.experiments.validation import generate_splits, validate_splits


class ExperimentChecks(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((ROOT / "configs/svm.json").read_text(encoding="utf-8"))
        rng = np.random.default_rng(5)
        self.values = rng.uniform(0, 20, size=(60, 8))
        self.values[:, 0] = 0  # Varies only in the held-out data below.
        self.data = pd.DataFrame({"Sample ID": [f"S{i}" for i in range(60)],
                                  "Patient ID": [f"P{i}" for i in range(60)],
                                  "subtype": np.repeat(self.settings["labels"], 10)})
        self.features = [f"gene__{i}" for i in range(8)]
        self.splits = generate_splits(self.data, self.settings["validation"])

    def test_test_values_cannot_change_fitted_preprocessing(self):
        held_out = np.full((6, 8), 1e8)
        for scaling, reduction in [("standard", "none"), ("minmax", "none"),
                                   ("standard", "anova"), ("standard", "pca")]:
            with self.subTest(scaling=scaling, reduction=reduction):
                config = {"id": "CHECK", "scaler": scaling, "reduction": reduction, "k": 3, "kernel": "linear"}
                pipeline = build_pipeline(config, self.settings)
                pipeline.fit(self.values, self.data["subtype"])
                self.assertFalse(pipeline.named_steps["variance"].get_support()[0])
                logged_train = np.log2(self.values[:, 1:] + 1)
                scaler = pipeline.named_steps["scale"]
                if scaling == "standard":
                    np.testing.assert_allclose(scaler.mean_, logged_train.mean(axis=0))
                    before = scaler.mean_.copy()
                else:
                    np.testing.assert_allclose(scaler.data_max_, logged_train.max(axis=0))
                    before = scaler.data_max_.copy()
                reducer = pipeline.named_steps.get("reduction")
                reduced_before = (reducer.scores_.copy() if reduction == "anova" else
                                  reducer.components_.copy() if reduction == "pca" else None)
                pipeline.predict(held_out)
                np.testing.assert_array_equal(before, scaler.mean_ if scaling == "standard" else scaler.data_max_)
                if reduced_before is not None:
                    np.testing.assert_array_equal(reduced_before, reducer.scores_ if reduction == "anova" else reducer.components_)

    def test_split_completeness_and_repeatability(self):
        validate_splits(self.splits, self.data, self.settings["validation"], self.settings["labels"])
        pd.testing.assert_frame_equal(self.splits, generate_splits(self.data, self.settings["validation"]))
        self.assertEqual(len(self.splits), 180)

    def test_reject_duplicate_assignment(self):
        corrupt = self.splits.copy()
        corrupt.iloc[1] = corrupt.iloc[0]
        with self.assertRaises(ValueError):
            validate_splits(corrupt, self.data, self.settings["validation"], self.settings["labels"])

    def test_reject_patient_overlap_and_changed_labels(self):
        repeated = self.data.copy()
        repeated.loc[1, "Patient ID"] = repeated.loc[0, "Patient ID"]
        with self.assertRaises(ValueError):
            validate_splits(self.splits, repeated, self.settings["validation"], self.settings["labels"])
        corrupt = self.splits.copy()
        corrupt.loc[0, "subtype"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            validate_splits(corrupt, self.data, self.settings["validation"], self.settings["labels"])

    def test_saved_splits_cannot_be_silently_changed(self):
        with tempfile.TemporaryDirectory() as temporary:
            assignments = Path(temporary) / "outer.csv"
            manifest = Path(temporary) / "outer_manifest.json"
            with patch("src.experiments.common.SPLIT_PATH", assignments), \
                    patch("src.experiments.common.SPLIT_MANIFEST", manifest), \
                    patch("src.experiments.common.split_metadata", return_value={"dataset_sha256": "test"}):
                shared_splits(self.data, self.settings, create=True)
                original_bytes = assignments.read_bytes()
                shared_splits(self.data, self.settings, create=True)
                self.assertEqual(original_bytes, assignments.read_bytes())
                corrupt = pd.read_csv(assignments)
                # Swap two same-class samples between folds: valid coverage, different assignments.
                first = corrupt.index[(corrupt["repeat"] == 1) & (corrupt["subtype"] == "LMS")][0]
                second = corrupt.index[(corrupt["repeat"] == 1) & (corrupt["subtype"] == "LMS") &
                                       (corrupt["fold"] != corrupt.loc[first, "fold"])][0]
                corrupt.loc[[first, second], "fold"] = corrupt.loc[[second, first], "fold"].to_numpy()
                corrupt.to_csv(assignments, index=False, lineterminator="\n")
                with self.assertRaisesRegex(ValueError, "changed"):
                    shared_splits(self.data, self.settings)
                write_json(manifest, {"dataset_sha256": "test", "split_sha256": sha256(assignments)})
                with self.assertRaisesRegex(ValueError, "agreed seed"):
                    shared_splits(self.data, self.settings)

    def test_metrics_use_all_samples_per_repeat(self):
        predictions = self.splits.rename(columns={"subtype": "true_subtype"}).copy()
        predictions["predicted_subtype"] = predictions["true_subtype"]
        results = summarize(predictions, self.settings["labels"], self.data["Sample ID"], 3)
        self.assertEqual(results["summary"]["macro_f1"]["mean"], 1)
        self.assertEqual(results["summary"]["macro_f1"]["sample_std"], 0)
        for repeat in results["repeats"]:
            self.assertEqual(sum(c["support"] for c in repeat["per_class"].values()), 60)
        with self.assertRaises(ValueError):
            summarize(predictions.iloc[:-1], self.settings["labels"], self.data["Sample ID"], 3)

    def test_missing_predictions_for_class_have_zero_f1(self):
        predictions = self.splits.rename(columns={"subtype": "true_subtype"}).copy()
        predictions["predicted_subtype"] = "LMS"
        result = summarize(predictions, self.settings["labels"], self.data["Sample ID"], 3)
        self.assertEqual(result["repeats"][0]["per_class"]["MPNST"]["f1"], 0)
        self.assertAlmostEqual(result["summary"]["balanced_accuracy"]["mean"], 1 / 6)


if __name__ == "__main__":
    unittest.main()
