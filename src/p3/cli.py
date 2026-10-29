"""Protocol 3.0 commands: check, smoke, run, screen, analyze, sensitivity, final."""
import argparse
from pathlib import Path
import sys

from src.experiments.common import ROOT
from .inputs import load_inputs, outer_folds, provenance, require_committed_code, require_frozen, verify_environment
from .pipelines import build_pipeline, candidates, fits_per_repeat, load_config, parameters, pipeline_spec
from .engine import prepare_destination, run_pipeline

OUTPUT = ROOT / "experiments/p3.0"
SMOKE = ROOT / "results/p3/smoke"


def member_pipelines(config, member, chosen):
    owned = config["members"][str(member)]["pipelines"]
    if chosen:
        unknown = [p for p in chosen if p not in owned]
        if unknown:
            raise ValueError(f"Member {member} does not run {', '.join(unknown)}; their batch is {', '.join(owned)}")
        return list(dict.fromkeys(chosen))
    return owned


def validate_config(config):
    ids = [spec["id"] for spec in config["pipelines"]]
    assigned = sum((m["pipelines"] for m in config["members"].values()), [])
    if sorted(assigned) != sorted(ids) or len(set(ids)) != len(ids):
        raise ValueError("Every pipeline must belong to exactly one member")
    for spec in config["pipelines"]:
        pipeline = build_pipeline(spec, config)
        for candidate in candidates(spec):
            pipeline.set_params(**parameters(spec, candidate))
    for name in config["selection"]["simplicity_order"] + [p for pair in config["ablations"] for p in (pair["from"], pair["to"])]:
        pipeline_spec(config, name)
    if sorted(config["selection"]["simplicity_order"]) != sorted(config["selection"]["eligible"]):
        raise ValueError("The simplicity order must rank exactly the eligible pipelines")


def check(config, member):
    packages = verify_environment(config)
    validate_config(config)
    print("Checking raw files, prepared expression values and shared splits...", flush=True)
    inputs = load_inputs(config)
    print(f"Verified {len(inputs['data'])} patients, {len(inputs['features'])} genes, "
          f"{len(inputs['outer'])} outer and {len(inputs['inner'])} inner assignments.")
    proof = provenance(config, packages)
    print(f"Python {proof['python']}, commit {proof['git_commit'] or 'unknown'}"
          + (", uncommitted code changes" if proof["git_dirty_code"] else ", code committed"))
    for number, info in config["members"].items():
        if member and int(number) != member:
            continue
        fits = {p: fits_per_repeat(pipeline_spec(config, p)) for p in info["pipelines"]}
        print(f"Member {number} ({info['name']}, {info['batch']}): " + ", ".join(f"{p} {n}" for p, n in fits.items())
              + f" fits per repeat; round A {sum(fits.values())}, round B {3 * sum(fits.values())}")


def smoke(config, member, chosen, jobs):
    """One outer fold per pipeline: real runtime and early errors. Outer test is not predicted."""
    from .screen import reference_difference
    packages = verify_environment(config)
    inputs = load_inputs(config)
    first = outer_folds(inputs, {1})[:1]
    manifest = dict(round="smoke", member=member, **provenance(config, packages))
    for pipeline_id in member_pipelines(config, member, chosen):
        spec = pipeline_spec(config, pipeline_id)
        destination = SMOKE / pipeline_id
        prepare_destination(destination, replace=True)
        result = run_pipeline(spec, config, inputs, first, destination, predict_outer=False, manifest=manifest, jobs=jobs)
        record = result["folds"][0]
        if record["status"] != "complete":
            raise SystemExit(f"{pipeline_id} failed: {record['error']}")
        per_fold = record["wall_seconds"]
        print(f"  {pipeline_id}: {record['fits']} fits, {per_fold:.0f} s for one outer fold; "
              f"estimated round A {5 * per_fold / 60:.1f} min, round B {15 * per_fold / 60:.1f} min with --jobs {jobs}")
        if pipeline_id == config["reference"]["pipeline"]:
            difference = reference_difference(config, destination)
            print(f"  {pipeline_id} inner scores vs Round 1: max difference {difference:.2e}"
                  + (" (match)" if difference < 1e-9 else " (MISMATCH: stop and report)"))


def run(config, round_name, member, chosen, jobs, replace, development, submission_outputs=None):
    if round_name == "B":
        if development:
            raise ValueError("Round B cannot use --development; it must run from the frozen tag")
        require_frozen(config)
    elif not development:
        require_committed_code()
    packages = verify_environment(config)
    inputs = load_inputs(config)
    repeats = {1} if round_name == "A" else {1, 2, 3}
    folds = outer_folds(inputs, repeats)
    manifest = dict(round=round_name, member=member, development=development, repeats=sorted(repeats),
                    **provenance(config, packages))
    for pipeline_id in member_pipelines(config, member, chosen):
        destination = OUTPUT / f"round{round_name}" / f"member{member}" / pipeline_id
        prepare_destination(destination, replace)
        if submission_outputs is not None:
            submission_outputs.append(destination)
        # Round A is screening: outer test samples are never predicted, so nobody can see outer scores.
        result = run_pipeline(pipeline_spec(config, pipeline_id), config, inputs, folds, destination,
                              predict_outer=round_name == "B", manifest=manifest, jobs=jobs)
        if result["status"] != "complete":
            raise SystemExit(f"{pipeline_id} failed; see {destination / 'manifest.json'}")
        print(f"Saved {destination.relative_to(ROOT)}", flush=True)


def main():
    # Member names are Vietnamese; a redirected Windows console must not crash on them.
    sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="python -m src.p3", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    checker = commands.add_parser("check", help="verify environment, data, splits and config")
    checker.add_argument("--member", type=int, choices=[1, 2, 3, 4])
    for name, text in [("smoke", "one outer fold per pipeline to measure runtime"), ("run", "nested CV for a member's batch")]:
        command = commands.add_parser(name, help=text)
        command.add_argument("--member", type=int, choices=[1, 2, 3, 4], required=True)
        command.add_argument("--pipeline", action="append", help="limit to these pipelines of the batch")
        command.add_argument("--jobs", type=int, default=1, help="parallel fits (default 1)")
        if name == "run":
            command.add_argument("--round", choices=["A", "B"], required=True)
            command.add_argument("--replace", action="store_true", help="rerun a pipeline whose folder exists")
            command.add_argument("--development", action="store_true", help="round A only: allow uncommitted code")
    for name, text in [("screen", "round A screening report"), ("analyze", "round B tables and report")]:
        command = commands.add_parser(name, help=text)
        command.add_argument("folders", nargs="+", type=Path, help="member result folders")
        command.add_argument("--out", type=Path)
    sensitivity = commands.add_parser("sensitivity", help="one-repeat sensitivity analysis")
    sensitivity.add_argument("--analysis", choices=["S-TSS", "S-206", "S-5CLASS"], required=True)
    sensitivity.add_argument("--pipeline", action="append", required=True)
    sensitivity.add_argument("--jobs", type=int, default=1)
    sensitivity.add_argument("--replace", action="store_true")
    final = commands.add_parser("final", help="refit the chosen pipeline on all 254 patients for the app")
    final.add_argument("--pipeline", help="defaults to the pipeline chosen by analyze")
    final.add_argument("--jobs", type=int, default=1)
    final.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    config = load_config()
    if args.command == "check":
        check(config, args.member)
    elif args.command == "smoke":
        smoke(config, args.member, args.pipeline, args.jobs)
    elif args.command == "run":
        from .submission import member_submission
        requested = member_pipelines(config, args.member, args.pipeline)
        with member_submission(ROOT / 'results/p3/submissions' / f'member{args.member}',
                               args.round, args.member, requested) as outputs:
            run(config, args.round, args.member, args.pipeline, args.jobs, args.replace, args.development,
                submission_outputs=outputs)
    elif args.command == "screen":
        from .screen import screen
        screen(config, args.folders, args.out or OUTPUT / "roundA/screening")
    elif args.command == "analyze":
        from .analyze import analyze
        analyze(config, args.folders, args.out or OUTPUT / "roundB/analysis")
    elif args.command == "sensitivity":
        from .sensitivity import sensitivity
        sensitivity(config, args.analysis, args.pipeline, args.jobs, args.replace, OUTPUT / "sensitivity" / args.analysis)
    else:
        from .final import final
        final(config, args.pipeline, args.jobs, args.replace, OUTPUT)


