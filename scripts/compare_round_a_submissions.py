"""Rebuild the descriptive Round A comparison from original member ZIPs; no fitting."""
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from src.p3.screen import screen
    config = json.loads((ROOT / 'configs/protocol3.json').read_text(encoding='utf-8'))
    evidence = ROOT / 'results/p3/review/roundA'
    output = ROOT / 'reports/protocol3/roundA'
    output.mkdir(parents=True, exist_ok=True)
    expected = {s['id']: s for s in config['pipelines']}
    found, records, sources = {}, [], []
    for path in sorted((ROOT / 'results/p3/submissions').glob('member*/*.zip')):
        with ZipFile(path) as archive:
            summary = json.loads(archive.read('submission_summary.json'))
            if summary['round'] != 'A' or summary['status'] != 'complete':
                continue
            for item in summary['pipelines']:
                name = item['pipeline']
                if name in found or name not in expected:
                    raise ValueError(f'Duplicate or unexpected pipeline: {name}; select runs explicitly')
                manifest_raw = archive.read(name + '/manifest.json')
                manifest = json.loads(manifest_raw)
                assert manifest['spec'] == expected[name] and manifest['packages'] == config['packages']
                assert manifest['member'] == summary['member'] and manifest['status'] == 'complete'
                assert manifest['round'] == 'A' and not manifest['predict_outer']
                assert not manifest['development'] and not manifest['git_dirty_code']
                assert [(f['repeat'], f['fold']) for f in manifest['folds']] == [(1, i) for i in range(1, 6)]
                assert not any(n.endswith('predictions.csv') for n in archive.namelist())
                files = {}
                assert set(manifest['outputs']) == {'search_results.csv', 'feature_details.json', 'warnings.csv'}
                for filename, digest in manifest['outputs'].items():
                    raw = archive.read(name + '/' + filename)
                    assert hashlib.sha256(raw).hexdigest() == digest, (name, filename)
                    files[filename] = raw
                search = list(csv.DictReader(io.StringIO(files['search_results.csv'].decode())))
                grid = manifest['candidates']
                assert len(search) == 5 * len(grid)
                for fold in manifest['folds']:
                    rows = sorted((r for r in search if int(r['repeat']) == 1 and int(r['fold']) == fold['fold']),
                                  key=lambda r: int(r['candidate']))
                    assert len(rows) == len(grid)
                    means = []
                    for index, row in enumerate(rows):
                        assert int(row['candidate']) == index and json.loads(row['params']) == grid[index]
                        scores = [float(row[f'inner_{i}']) for i in range(1, 5)]
                        assert all(0 <= s <= 1 for s in scores)
                        means.append(statistics.mean(scores))
                        assert abs(means[-1] - float(row['mean_inner'])) < 1e-12
                    best = max(range(len(grid)), key=lambda i: means[i])
                    assert fold['best_candidate'] == best and fold['best_params'] == grid[best]
                    assert abs(fold['best_inner'] - means[best]) < 1e-12
                    assert [r['selected'] for r in rows] == [str(i == best) for i in range(len(grid))]
                destination = evidence / f'member{summary["member"]}' / name
                destination.mkdir(parents=True, exist_ok=True)
                for filename, raw in {**files, 'manifest.json': manifest_raw}.items():
                    (destination / filename).write_bytes(raw)
                found[name] = manifest
                scores = [f['best_inner'] for f in manifest['folds']]
                records.append(dict(pipeline=name, member=summary['member'], name=expected[name]['name'],
                                    mean_winning_inner_macro_f1=statistics.mean(scores),
                                    sd_winning_inner_macro_f1=statistics.stdev(scores),
                                    **{f'fold{i + 1}': s for i, s in enumerate(scores)},
                                    wall_seconds=sum(f['wall_seconds'] for f in manifest['folds']),
                                    fits=sum(f['fits'] for f in manifest['folds']),
                                    warnings=sum(f['warnings'] for f in manifest['folds'])))
                sources.append(dict(pipeline=name, source_zip=path.relative_to(ROOT).as_posix(),
                                    zip_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                    training_commit=manifest['git_commit'], config_sha256=manifest['config_sha256']))
    assert set(found) == set(expected), f'Missing pipelines: {set(expected) - set(found)}'
    assert len({s['config_sha256'] for s in sources}) == 1
    screen(config, [evidence / f'member{i}' for i in range(1, 5)], output)
    records.sort(key=lambda r: r['mean_winning_inner_macro_f1'], reverse=True)
    pairs = []
    for pair in config['ablations']:
        a, b = (found[p]['folds'] for p in (pair['from'], pair['to']))
        differences = [y['best_inner'] - x['best_inner'] for x, y in zip(a, b)]
        pairs.append(dict(**pair, mean_inner_difference=statistics.mean(differences),
                          folds_higher=sum(d > 1e-12 for d in differences),
                          folds_lower=sum(d < -1e-12 for d in differences),
                          folds_tied=sum(abs(d) <= 1e-12 for d in differences)))
    for filename, rows in [('inner_comparison.csv', records), ('paired_inner_differences.csv', pairs), ('sources.csv', sources)]:
        with (output / filename).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    lines = ['# Round A team comparison', '',
             'All 14 executable entries (13 proposed pipelines, including two Dummy variants) completed five outer-training searches. No outer-test predictions were generated.', '',
             '**These are selected inner-CV scores, not independent generalization estimates.** Each fold contributes its best candidate mean across four inner validation folds. The SD below describes variation between those five selected scores; it is not a confidence interval. Search spaces differ, so the ordering is descriptive and must not be used to eliminate pipelines or claim superiority.', '',
             '| Pipeline | Mean winning inner macro-F1 | SD | Wall minutes | Warnings |',
             '| --- | ---: | ---: | ---: | ---: |']
    for row in records:
        lines.append(f"| {row['pipeline']} {row['name']} | {row['mean_winning_inner_macro_f1']:.4f} | {row['sd_winning_inner_macro_f1']:.4f} | {row['wall_seconds']/60:.2f} | {row['warnings']} |")
    lines += ['', '## Descriptive observations', '',
              '- P09 and P04 have the highest mean selected inner scores, approximately 0.761. This is not a final winner declaration.',
              '- P10 has the highest single selected inner score, but exceeds matched P09 in only two of five folds. These results do not establish a benefit from SMOTE.',
              '- P07 is the practical runtime bottleneck, approximately 107 minutes. Machines and parallel settings differ; this is not a controlled efficiency benchmark.',
              '- P02 reproduces archived inner scores to numerical precision; see screening.md.',
              '- P04, P05, P06, P09 and P10 trigger the declared boundary-screening rule. Resolve and document those choices before freezing Round B. No grids were changed by this comparison.', '',
              '## Evidence and next steps', '',
              'Original ZIPs are authoritative. Member 3 also committed loose files whose newline conversion changes a checksum; this report extracts bytes directly from ZIPs. sources.csv identifies every selected archive and recorded training commit. P07 was submitted by Kien under the member-2 assignment; P06/P08 were submitted separately. Different recorded commits contain identical training/config/split content as checked in the preceding audit.', '',
              'Review screening.md, decide any one-time grid extensions, rerun affected Round A pipelines if required, then commit and tag the final configuration. Run all Round B repeats separately. No Round B performance or META-SELECT generalization result is available yet.', '',
              'Reproduce with `python scripts/compare_round_a_submissions.py`. This script reads saved evidence only and performs no model fitting.']
    (output / 'comparison.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Comparison saved: {output}')


if __name__ == '__main__':
    main()
