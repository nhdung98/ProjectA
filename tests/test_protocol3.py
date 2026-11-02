"""Protocol 3.0: config, new transformers, nested CV engine, statistics and the analysis commands."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.experiments.validation import fold_indices, generate_splits
from src.p3 import analyze as analysis
from src.p3.engine import run_pipeline, write_outputs
from src.p3.inputs import split_settings
from src.p3.inputs import code_hashes
from src.experiments.common import ROOT, sha256
from src.p3.pipelines import build_pipeline, candidates, fits_per_repeat, load_config, parameters, pipeline_spec
from src.p3.results import load_runs
from src.p3.screen import boundary_hits, screen
from src.p3.stats import conclusion, correlated_ttest, wilson
from src.p3.transforms import ExpressionFilter, PriorShift

CONFIG = load_config()
GRID_SIZES = {"P01-MF": 1, "P01-ST": 1, "P02": 5, "P03": 5, "P04": 20, "P05": 5, "P06": 5, "P07": 9, "P08": 15,
              "P09": 15, "P10": 15, "P11": 5, "P12": 4, "P13": 8}


def cohort():
    settings = split_settings(CONFIG)
    labels = sum(([label] * count for label, count in settings["class_counts"].items()), [])
    data = pd.DataFrame({"Sample ID": [f"s{i}" for i in range(254)], "Patient ID": [f"p{i}" for i in range(254)],
                         "subtype": labels})
    return data, generate_splits(data, settings["validation"]), settings["labels"]


def fake_run(folder, spec, round_name, data, outer, labels, rng, inner_shift=0.0):
    """A complete run folder with plausible numbers, written through the engine's own writer."""
    grid = candidates(spec)
    search, details, predictions, folds = [], [], [], []
    repeats = [1] if round_name == "A" else [1, 2, 3]
    for repeat, fold, train, test in fold_indices(outer, data):
        if repeat not in repeats:
            continue
        means = rng.uniform(0.6, 0.8, len(grid)) + inner_shift
        best = int(np.argmax(means))
        for c, candidate in enumerate(grid):
            search.append(dict(repeat=repeat, fold=fold, candidate=c, params=json.dumps(candidate, sort_keys=True),
                               inner_1=means[c], inner_2=means[c], inner_3=means[c], inner_4=means[c],
                               mean_inner=means[c], selected=c == best, fit_seconds=1.0))
        details.append(dict(repeat=repeat, fold=fold))
        folds.append(dict(repeat=repeat, fold=fold, status="complete", best_candidate=best, best_params=grid[best],
                          best_inner=float(means[best]), fits=4 * len(grid) + 1, inner_fit_seconds=4.0 * len(grid),
                          refit_seconds=1.0, wall_seconds=4.0 * len(grid) + 1, warnings=0))
        folds[-1].update(train_samples=len(train), test_samples=len(test))
        rows = data.iloc[test]
        guesses = np.where(rng.uniform(size=len(test)) < 0.8, rows["subtype"], rng.choice(labels, len(test)))
        predictions += [dict(pipeline=spec["id"], repeat=repeat, fold=fold, **{"Sample ID": s, "Patient ID": p},
                             true_subtype=t, predicted_subtype=g)
                        for s, p, t, g in zip(rows["Sample ID"], rows["Patient ID"], rows["subtype"], guesses)]
    manifest = dict(round=round_name, member=1, development=False, git_commit="abc", config_sha256="cfg",
                    machine=dict(system="Test", machine="x", cpu_count=1), pipeline=spec["id"], status="complete",
                    folds=folds)
    manifest.update(member=next(int(i) for i, m in CONFIG['members'].items() if spec['id'] in m['pipelines']),
                    git_dirty_code=False, config_sha256=sha256(ROOT / 'configs/protocol3.json'),
                    code_sha256=code_hashes(), packages=CONFIG['packages'], spec=spec, candidates=grid)
    write_outputs(folder / spec["id"], manifest, search, details, predictions if round_name == "B" else None, [])


class ConfigChecks(unittest.TestCase):
    def test_grid_sizes_and_fit_counts_follow_the_proposal(self):
        self.assertEqual({spec["id"]: len(candidates(spec)) for spec in CONFIG["pipelines"]}, GRID_SIZES)
        # 2,305 fits per repeat in the proposal, plus 25 for running both dummy variants.
        self.assertEqual(sum(fits_per_repeat(spec) for spec in CONFIG["pipelines"]), 2305 + 25)
        assigned = sum((member["pipelines"] for member in CONFIG["members"].values()), [])
        self.assertEqual(sorted(assigned), sorted(GRID_SIZES))
        self.assertEqual(len(CONFIG["ablations"]), 11)

    def test_candidates_keep_declared_order_for_tie_breaks(self):
        grid = candidates(pipeline_spec(CONFIG, "P07"))
        self.assertEqual(grid[:2], [{"model__l1_ratio": 0.1, "model__C": 0.01}, {"model__l1_ratio": 0.1, "model__C": 0.1}])
        self.assertEqual([c["model__C"] for c in candidates(pipeline_spec(CONFIG, "P02"))], [0.01, 0.1, 1, 10, 100])

    def test_every_candidate_is_a_valid_pipeline_setting(self):
        for spec in CONFIG["pipelines"]:
            pipeline = build_pipeline(spec, CONFIG)
            for candidate in candidates(spec):
                pipeline.set_params(**parameters(spec, candidate))
        steps = [name for name, _ in build_pipeline(pipeline_spec(CONFIG, "P10"), CONFIG).steps]
        self.assertEqual(steps, ["log", "filter", "scale", "select", "smote", "model"])


class TransformChecks(unittest.TestCase):
    def test_expression_filter_uses_an_absolute_count_of_training_samples(self):
        x = np.zeros((10, 3))
        x[:5, 0] = 2.0   # expressed in exactly 5 samples: kept
        x[:4, 1] = 2.0   # expressed in 4 samples: dropped
        x[:, 2] = 1.0    # not above the threshold
        self.assertEqual(ExpressionFilter().fit(x).get_support().tolist(), [True, False, False])

    def test_mad_keeps_the_most_variable_expressed_genes(self):
        rng = np.random.default_rng(0)
        x = 5 + rng.normal(size=(20, 4)) * np.array([0.1, 2.0, 1.0, 3.0])
        self.assertEqual(ExpressionFilter(top_mad=2).fit(x).get_support().tolist(), [False, True, False, True])
        with self.assertRaises(ValueError):
            ExpressionFilter(top_mad=5).fit(x)

    def test_filter_ignores_values_it_was_not_fitted_on(self):
        rng = np.random.default_rng(1)
        x = rng.uniform(0, 4, size=(30, 50))
        train, test = x[:20], x[20:]
        fitted = ExpressionFilter(top_mad=10).fit(train)
        changed = np.vstack([train, test * 100])
        self.assertEqual(fitted.transform(test).shape, (10, 10))
        self.assertTrue(np.array_equal(fitted.get_support(), ExpressionFilter(top_mad=10).fit(changed[:20]).get_support()))

    def test_prior_shift_matches_plain_regression_at_alpha_zero(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=(60, 3))
        y = np.array(["a"] * 45 + ["b"] * 15)
        x[y == "b"] += 0.7
        base = LogisticRegression().fit(x, y)
        plain = PriorShift(LogisticRegression(), alpha=0).fit(x, y)
        shifted = PriorShift(LogisticRegression(), alpha=1).fit(x, y)
        self.assertTrue(np.array_equal(plain.predict(x), base.predict(x)))
        self.assertEqual(plain.priors_.tolist(), [0.75, 0.25])
        self.assertGreater((shifted.predict(x) == "b").sum(), (plain.predict(x) == "b").sum())

    def test_smote_only_acts_during_fit(self):
        spec = {**pipeline_spec(CONFIG, "P10"), "filter": "none", "fixed": {"select__k": 5}}
        rng = np.random.default_rng(3)
        y = np.array(["a"] * 30 + ["b"] * 6)
        x = rng.uniform(0, 10, size=(36, 8))
        model = build_pipeline(spec, CONFIG).fit(x, y)
        self.assertEqual(len(model.predict(x[:7])), 7)


class EngineChecks(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(4)
        labels = ["A", "B", "C"]
        y = np.repeat(labels, [24, 16, 12])
        values = rng.uniform(0, 30, size=(len(y), 12))
        values[:, :3] += np.where(y[:, None] == "A", 40, 0)
        self.data = pd.DataFrame({"Sample ID": [f"s{i}" for i in range(len(y))],
                                  "Patient ID": [f"p{i}" for i in range(len(y))], "subtype": y})
        self.inputs = dict(data=self.data, features=[f"g{i}" for i in range(12)], values=values, labels=labels)
        from sklearn.model_selection import StratifiedKFold
        outer = list(StratifiedKFold(3, shuffle=True, random_state=0).split(values, y))
        self.folds = [dict(repeat=1, fold=i + 1, train=train, test=test,
                           inner=list(StratifiedKFold(4, shuffle=True, random_state=0).split(train, y[train])))
                      for i, (train, test) in enumerate(outer)]
        self.spec = {**pipeline_spec(CONFIG, "P09"), "filter": "F0", "grid": {"select__k": [3, 6], "model__C": [0.1, 1]}}

    def test_round_a_never_predicts_outer_test(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "P09"
            manifest = run_pipeline(self.spec, CONFIG, self.inputs, self.folds, folder, predict_outer=False, manifest={})
            self.assertEqual(manifest["status"], "complete")
            self.assertFalse((folder / "predictions.csv").exists())
            search = pd.read_csv(folder / "search_results.csv")
            self.assertEqual(len(search), 3 * 4)
            self.assertEqual(search.groupby("fold")["selected"].sum().tolist(), [1, 1, 1])

    def test_round_b_predicts_each_sample_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "P09"
            run_pipeline(self.spec, CONFIG, self.inputs, self.folds, folder, predict_outer=True, manifest={})
            predictions = pd.read_csv(folder / "predictions.csv")
            self.assertEqual(sorted(predictions["Sample ID"]), sorted(self.data["Sample ID"]))
            details = json.loads((folder / "feature_details.json").read_text(encoding="utf-8"))
            self.assertEqual(len(details[0]["selected_genes"]), json.loads(
                (folder / "manifest.json").read_text(encoding="utf-8"))["folds"][0]["best_params"]["select__k"])

    def test_exact_ties_keep_the_first_declared_candidate(self):
        spec = {**pipeline_spec(CONFIG, "P01-MF"), "grid": {"model__strategy": ["most_frequent", "prior"]}}
        with tempfile.TemporaryDirectory() as temporary:
            manifest = run_pipeline(spec, CONFIG, self.inputs, self.folds, Path(temporary) / "P01", predict_outer=False,
                                    manifest={})
        self.assertEqual({f["best_candidate"] for f in manifest["folds"]}, {0})


class StatisticsChecks(unittest.TestCase):
    def test_correlated_ttest_reproduces_the_worked_example(self):
        d = [0.001, 0.022, 0.018, 0.027, 0.017, 0.007, 0.018, 0.005, 0.031, 0.040, 0.024, 0.023, 0.034, 0.010, 0.008]
        result = correlated_ttest(d, rope=0.01, rho=0.2)
        self.assertAlmostEqual(result["worse"], 0.00, places=2)
        self.assertAlmostEqual(result["equivalent"], 0.09, places=2)
        self.assertAlmostEqual(result["better"], 0.91, places=2)
        self.assertEqual(conclusion(result, 0.95), ("better", False))
        self.assertAlmostEqual(correlated_ttest(d, rope=0.02, rho=0.2)["better"], 0.44, places=2)

    def test_identical_folds_give_a_point_mass(self):
        self.assertEqual(correlated_ttest([0.0] * 15, 0.01, 0.2)["equivalent"], 1.0)

    def test_wilson_matches_the_results_template(self):
        self.assertEqual([round(v, 3) for v in wilson(6, 9)], [0.354, 0.879])
        self.assertEqual([round(v, 3) for v in wilson(0, 9)], [0.0, 0.299])
        self.assertEqual([round(v, 3) for v in wilson(9, 10)], [0.596, 0.982])


class AnalysisChecks(unittest.TestCase):
    def test_boundary_rule_ignores_short_grids_and_natural_limits(self):
        picks = {(1, f): {"select__k": 2000, "model__C": 0.001} for f in range(1, 4)}
        picks.update({(1, f): {"select__k": 500, "model__C": 1} for f in (4, 5)})
        hits = boundary_hits(CONFIG, pipeline_spec(CONFIG, "P09"), picks)
        self.assertEqual([(h["parameter"], h["edge"]) for h in hits], [("select__k", 2000), ("model__C", 0.001)])
        self.assertEqual(hits[0]["action"], "extend once: add 4000")
        knn = {(1, f): {"select__k": 100, "model__n_neighbors": 1} for f in range(1, 6)}
        actions = [h["action"] for h in boundary_hits(CONFIG, pipeline_spec(CONFIG, "P13"), knn)]
        self.assertEqual(actions, ["not applicable: only 2 grid values", "natural limit: nothing to extend"])

    def test_meta_select_breaks_ties_by_declared_simplicity(self):
        search = lambda selected: pd.DataFrame([dict(repeat=1, fold=1, candidate=0, params="{}", mean_inner=0.8,
                                                     selected=selected)])
        prediction = pd.DataFrame([dict(pipeline="x", repeat=1, fold=1, **{"Sample ID": "s0"}, true_subtype="LMS",
                                        predicted_subtype="LMS")])
        runs = {p: dict(search=search(True), predictions=prediction) for p in CONFIG["selection"]["eligible"]}
        chosen, _ = analysis.meta_select(CONFIG, runs, ["LMS"])
        self.assertEqual(chosen["pipeline"].tolist(), [CONFIG["selection"]["simplicity_order"][0]])

    def test_round_a_folders_must_not_hold_outer_predictions(self):
        data, outer, labels = cohort()
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fake_run(folder, pipeline_spec(CONFIG, "P06"), "A", data, outer, labels, np.random.default_rng(0))
            load_runs([folder], "A")
            (folder / "P06/predictions.csv").write_text("leak\n")
            with self.assertRaises(ValueError):
                load_runs([folder], "A")

    def test_edited_outputs_are_rejected(self):
        data, outer, labels = cohort()
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fake_run(folder, pipeline_spec(CONFIG, "P06"), "B", data, outer, labels, np.random.default_rng(0))
            with (folder / "P06/predictions.csv").open("a") as handle:
                handle.write("P06,1,1,s0,p0,LMS,LMS\n")
            with self.assertRaises(ValueError):
                load_runs([folder], "B")

    def test_screen_and_analyze_produce_their_reports(self):
        data, outer, labels = cohort()
        rng = np.random.default_rng(5)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for spec in CONFIG["pipelines"]:
                fake_run(root / "roundA", spec, "A", data, outer, labels, rng)
                fake_run(root / "roundB", spec, "B", data, outer, labels, rng, 0.1 if spec["id"] == "P07" else 0.0)
            screen(CONFIG, [root / "roundA"], root / "screening")
            screening_text = (root / "screening/screening.md").read_text(encoding="utf-8")
            self.assertIn("Round A screening report", screening_text)
            sections = screening_text.split('## ')[1:]
            self.assertEqual(len(sections), 6)
            for section in sections:
                explanation = section.split('\n\n', 2)[1]
                self.assertGreater(len(explanation), 80)
                self.assertFalse(explanation.startswith('|'))
            with patch.object(analysis, 'load_inputs', return_value=dict(
                    data=data, outer=outer, labels=labels, settings=split_settings(CONFIG))):
                analysis.analyze(CONFIG, [root / "roundB"], root / "analysis")
            summary = json.loads((root / "analysis/summary.json").read_text(encoding="utf-8"))
            # P07's inner scores are shifted up, so META-SELECT picks it in every fold.
            self.assertEqual(summary["meta_select"]["frequency"], {"P07": 15})
            self.assertIn(summary["selected"], CONFIG["selection"]["eligible"])
            report = (root / "analysis/report.md").read_text(encoding="utf-8")
            for heading in ["## 1. Bảng A", "## 5. Câu 1", "## 7. Câu 3", "## 10. Runtime"]:
                self.assertIn(heading, report)


if __name__ == "__main__":
    unittest.main()
