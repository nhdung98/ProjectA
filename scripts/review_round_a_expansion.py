"""Review an explicit original/extension evidence selection without fitting models."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    from src.p3.pipelines import candidates
    from src.p3.screen import screen
    config = json.loads((ROOT / 'configs/protocol3.json').read_text(encoding='utf-8'))
    extension = json.loads((ROOT / 'reports/protocol3/roundA-expansion-1/run_status.json').read_text(encoding='utf-8'))
    original = {r['pipeline']: r['source_zip'] for r in csv.DictReader(
        (ROOT / 'reports/protocol3/roundA/sources.csv').open(encoding='utf-8'))}
    expanded = {r['pipeline']: r['source_zip'] for r in extension['pipelines']}
    selected = {**original, **expanded}
    specs = {s['id']: s for s in config['pipelines']}
    require(set(selected) == set(specs), 'Missing or unexpected pipeline selection')
    out = ROOT / 'reports/protocol3/roundA-post-expansion'
    evidence = ROOT / 'results/p3/review/roundA-post-expansion'
    out.mkdir(parents=True, exist_ok=True)
    sources, reviews, log_reviews = [], [], []
    checked_revisions = set()
    scientific_paths = ['src/p3/engine.py', 'src/p3/pipelines.py', 'src/p3/transforms.py',
                        'src/p3/inputs.py', 'src/experiments', 'configs/data.yaml', 'configs/svm.json',
                        'requirements.txt', 'requirements-experiments.txt', 'requirements-protocol3.txt', 'results/splits']
    for name, spec in specs.items():
        path = ROOT / selected[name]
        with ZipFile(path) as z:
            summary = json.loads(z.read('submission_summary.json'))
            require(summary['round'] == 'A' and summary['status'] == 'complete', name + ': incomplete archive')
            m = json.loads(z.read(name + '/manifest.json'))
            require(m['pipeline'] == name and m['spec'] == spec and m['candidates'] == candidates(spec), name + ': grid/spec mismatch')
            require(m['packages'] == config['packages'] and m['python'].startswith('3.12.'), name + ': environment mismatch')
            require(m['status'] == 'complete' and m['round'] == 'A' and not m['predict_outer']
                    and not m['development'] and not m['git_dirty_code'], name + ': run flags mismatch')
            owner = next(int(i) for i, entry in config['members'].items() if name in entry['pipelines'])
            require(m['member'] == owner and summary['member'] == owner, name + ': owner mismatch')
            require([(f['repeat'], f['fold'], f['status']) for f in m['folds']] == [(1, i, 'complete') for i in range(1, 6)], name + ': incomplete folds')
            require(not any(p.endswith('predictions.csv') for p in z.namelist()), 'Outer predictions present')
            revision = m['git_commit']
            archived_config_raw = subprocess.check_output(['git', 'show', revision + ':configs/protocol3.json'], cwd=ROOT)
            archived_config = json.loads(archived_config_raw)
            require(m['config_sha256'] in {hashlib.sha256(archived_config_raw).hexdigest(),
                    hashlib.sha256(archived_config_raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')).hexdigest()}, name + ': config hash mismatch')
            # Only the five approved grid additions may differ across the two screening stages.
            expected_config = json.loads(json.dumps(config))
            for old in archived_config['pipelines']:
                current = next(s for s in expected_config['pipelines'] if s['id'] == old['id'])
                if old['id'] in expanded:
                    for key, values in old['grid'].items():
                        require(set(values).issubset(current['grid'][key]), 'Original grid not retained')
                    current['grid'] = old['grid']
            require(expected_config == archived_config, name + ': unapproved config difference')
            require(next(s for s in archived_config['pipelines'] if s['id'] == name) == spec, name + ': selected old spec differs')
            if revision not in checked_revisions:
                changed = subprocess.check_output(['git', 'diff', '--name-only', revision, 'HEAD', '--', *scientific_paths], cwd=ROOT, text=True)
                require(not changed.strip(), 'Scientific code/splits differ: ' + changed)
                checked_revisions.add(revision)
            require(set(m['outputs']) == {'search_results.csv', 'feature_details.json', 'warnings.csv'}, name + ': output inventory mismatch')
            files = {f: z.read(name + '/' + f) for f in m['outputs']}
            for filename, raw in files.items():
                require(hashlib.sha256(raw).hexdigest() == m['outputs'][filename], name + ': checksum mismatch')
            rows = list(csv.DictReader(io.StringIO(files['search_results.csv'].decode())))
            grid = candidates(spec)
            require(len(rows) == len(grid) * 5, name + ': search row count mismatch')
            for fold in m['folds']:
                block = sorted([r for r in rows if int(r['repeat']) == 1 and int(r['fold']) == fold['fold']], key=lambda r: int(r['candidate']))
                require(len(block) == len(grid), name + ': missing candidates')
                means = []
                for i, row in enumerate(block):
                    require(int(row['candidate']) == i and json.loads(row['params']) == grid[i], name + ': candidate mismatch')
                    scores = [float(row[f'inner_{j}']) for j in range(1, 5)]
                    require(all(math.isfinite(s) and 0 <= s <= 1 for s in scores), name + ': invalid inner score')
                    means.append(sum(scores) / 4)
                    require(abs(means[-1] - float(row['mean_inner'])) < 1e-12, name + ': mean mismatch')
                best = max(range(len(grid)), key=lambda i: means[i])
                require(fold['best_candidate'] == best and fold['best_params'] == grid[best]
                        and abs(fold['best_inner'] - means[best]) < 1e-12, name + ': winner mismatch')
                require([r['selected'] for r in block] == [str(i == best) for i in range(len(grid))], name + ': selected flags mismatch')
                expected_test = 50 if fold['fold'] == 5 else 51
                require(fold['test_samples'] == expected_test and fold['train_samples'] == 254 - expected_test
                        and fold['fits'] == 4 * len(grid) + 1, name + ': sample/fit counts mismatch')
            warnings = list(csv.DictReader(io.StringIO(files['warnings.csv'].decode())))
            require(len(warnings) == sum(f['warnings'] for f in m['folds']), name + ': warning count mismatch')
            details = json.loads(files['feature_details.json'])
            require([(d['repeat'], d['fold']) for d in details] == [(1, i) for i in range(1, 6)], name + ': feature details incomplete')
            destination = evidence / f'member{owner}' / name
            destination.mkdir(parents=True, exist_ok=True)
            for filename, raw in {**files, 'manifest.json': z.read(name + '/manifest.json')}.items():
                (destination / filename).write_bytes(raw)
            sources.append(dict(pipeline=name, stage='expansion-1' if name in expanded else 'original',
                                source_zip=selected[name], zip_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                training_commit=revision, config_sha256=m['config_sha256']))
            reviews.append(dict(pipeline=name, stage=sources[-1]['stage'], folds=5,
                                fits=sum(f['fits'] for f in m['folds']), warnings=len(warnings),
                                refit_iterations=[d.get('n_iter') for d in details],
                                selected=[f['best_params'] for f in m['folds']]))
        if not any(r['source_zip'] == selected[name] for r in log_reviews):
            logs = [p for p in (ROOT / f'results/p3/logs/member{owner}').glob('*.log')
                    if path.name in p.read_text(encoding='utf-8', errors='replace')]
            require(len(logs) == 1, 'Missing or ambiguous corresponding run log')
            text = logs[0].read_text(encoding='utf-8')
            require('Completed. Log saved:' in text and 'Traceback (most recent call last)' not in text, 'Run log reports failure')
            log_reviews.append(dict(source_zip=selected[name], log=logs[0].relative_to(ROOT).as_posix(),
                                    log_sha256=hashlib.sha256(logs[0].read_bytes()).hexdigest(), status='reviewed complete'))
    screen(config, [evidence / f'member{i}' for i in range(1, 5)], out)
    screening = json.loads((out / 'screening.json').read_text(encoding='utf-8'))
    original_actions = []
    for hit in screening['boundary']:
        if hit['pipeline'] in expanded and hit['action'].startswith('extend once:'):
            original_actions.append(dict(hit))
            hit['action'] = 'extension already used: record remaining boundary; do not extend again'
    screening.update(expansion_completed=True, extension_round=1, original_helper_recommendations=original_actions,
                     compatibility='Two global configs expected: five expanded grids and nine unchanged original entries. Exact pipeline specs, scientific code, packages and saved splits verified.',
                     selected_sources=sources, log_review=log_reviews)
    (out / 'screening.json').write_text(json.dumps(screening, indent=2), encoding='utf-8')
    text = (out / 'screening.md').read_text(encoding='utf-8')
    text = text.replace('# Round A screening report', '# Round A screening report — after the one-time expansion', 1)
    paragraphs = text.split('\n\n')
    paragraphs = [p for p in paragraphs if not p.startswith('**Warning:** runs used ')]
    text = '\n\n'.join(paragraphs)
    notice = ('**Evidence selection:** five expansion runs replace their original versions; nine unchanged entries reuse original runs. '
              'Two global config hashes are expected because only affected pipelines were rerun. Exact selected pipeline specifications, '
              'training implementation, package versions and saved split contents were checked for compatibility. '
              'All corresponding execution logs were reviewed. Sources are listed in sources.csv.\n\n')
    text = text.replace('## 1.', notice + '## 1.', 1)
    for hit in original_actions:
        text = text.replace(hit['action'], 'extension already used: record remaining boundary; do not extend again')
    start = text.index('A grid is the list')
    end = text.index('\n\n', start)
    text = text[:start] + ('A grid is the list of values tested. The five approved expansions have now been completed. '
            'A remaining edge selection is a documented search-range limitation, not a reason for a second expansion. '
            'Natural limits and two-value grid exemptions retain their original meanings. No settings are changed by this report.') + text[end:]
    old = '- For each extend-once recommendation in section 4, agree the value, extend the grid once in `configs/protocol3.json`, rerun the affected Round A pipeline with `--replace`, and regenerate this report. Preserve earlier submissions.'
    text = text.replace(old, '- The one permitted expansion is complete. Record residual boundary hits without expanding or rerunning again solely for that reason.')
    text = text.replace('- Do not remove pipelines because', '- Confirm the final pipeline list, comparison pairs, ROPE and simplicity order; then freeze the shared release. This report does not create a tag or authorize Round B automatically.\n- Do not remove pipelines because')
    (out / 'screening.md').write_text(text, encoding='utf-8')
    with (out / 'sources.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(sources[0])); writer.writeheader(); writer.writerows(sources)
    (out / 'validation_review.json').write_text(json.dumps(dict(pipelines=reviews, logs=log_reviews,
        selected_fits=sum(r['fits'] for r in reviews), recorded_warnings=sum(r['warnings'] for r in reviews),
        note='Consistency checks on saved evidence, not independent reproduction of training.'), indent=2), encoding='utf-8')
    print(f'Reviewed {len(reviews)} entries; {sum(r["fits"] for r in reviews)} fits; {sum(r["warnings"] for r in reviews)} warnings')


if __name__ == '__main__':
    main()
