"""Verified inputs and provenance shared by every protocol 3.0 command."""
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from src.experiments import svm
from src.experiments.common import ROOT, load_dataset, sha256, shared_splits
from src.experiments.validation import fold_indices

# Files whose content defines a run. Round B compares them with the frozen tag.
CODE_PATHS = ["src/p3", "src/experiments", "configs", "requirements.txt",
              "requirements-experiments.txt", "requirements-protocol3.txt", "results/splits"]


def split_settings(config):
    """Protocol 3.0 reuses the 2.0 cohort and split settings rather than copying them."""
    return json.loads((ROOT / config["split_settings"]).read_text(encoding="utf-8"))


def verify_environment(config):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("Use Python 3.12 for protocol 3.0")
    packages = {name: version(name) for name in config["packages"]}
    if packages != config["packages"]:
        raise ValueError(f"Package versions differ from requirements-protocol3.txt: {packages}")
    return packages


def load_inputs(config):
    """Load the dataset and the shared outer and inner splits, checking every checksum."""
    settings = split_settings(config)
    dataset = ROOT / settings["dataset"]
    if not dataset.exists():
        raise ValueError(f"{settings['dataset']} is missing. Run: python -m src.data.prepare")
    data, features, values = load_dataset(settings)
    outer = shared_splits(data, settings)
    inner = svm.shared_inner(data, outer, settings)
    return dict(settings=settings, data=data, features=features, values=values, outer=outer, inner=inner,
                labels=settings["labels"])


def outer_folds(inputs, repeats):
    """Outer folds with inner (fit, validation) pairs indexed within the outer training set."""
    data, inner = inputs["data"], inputs["inner"]
    folds = []
    for repeat, fold, train, test in fold_indices(inputs["outer"], data):
        if repeat in repeats:
            folds.append(dict(repeat=repeat, fold=fold, train=train, test=test,
                              inner=svm.inner_indices(data.iloc[train], inner, repeat, fold)))
    return folds


def git(*args):
    windows = Path(r"C:\Program Files\Git\cmd\git.exe")
    executable = str(windows) if windows.exists() else "git"
    result = subprocess.run([executable, *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def code_hashes():
    files = []
    for relative in CODE_PATHS:
        path = ROOT / relative
        files += sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                        and not p.name.startswith(".")) if path.is_dir() else [path]
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in files if p.exists()}


def provenance(config, packages):
    return dict(git_commit=git("rev-parse", "HEAD"), git_dirty_code=bool(git("status", "--porcelain", "--", *CODE_PATHS)),
                packages=packages, python=platform.python_version(),
                machine=dict(system=platform.system(), release=platform.release(), processor=platform.processor(),
                             machine=platform.machine(), cpu_count=os.cpu_count()),
                config_sha256=sha256(ROOT / "configs/protocol3.json"), code_sha256=code_hashes())


def require_committed_code():
    if not git("rev-parse", "HEAD"):
        raise ValueError("Run from a Git clone; the commit identifies the code that produced the results")
    if git("status", "--porcelain", "--", *CODE_PATHS):
        raise ValueError("Code, config or splits have uncommitted changes. Commit them, or use --development for local checks")


def require_frozen(config):
    """Round B must run from code and config identical to the frozen tag."""
    require_committed_code()
    tag = config["frozen_tag"]
    if not git("rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"):
        raise ValueError(f"Tag {tag} is missing. Run: git fetch --tags")
    changed = git("diff", "--name-only", tag, "HEAD", "--", *CODE_PATHS)
    if changed is None or changed:
        raise ValueError(f"Code or config differs from {tag}; round B must use the frozen protocol")
