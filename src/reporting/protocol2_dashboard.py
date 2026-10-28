"""Read-only aggregate dashboard: python -m src.reporting.protocol2_dashboard --help."""
import argparse
import base64
from datetime import datetime, timezone
import html
import json
import subprocess
from pathlib import Path
import textwrap
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .dashboard_inputs import CONFIGS, LABELS, COUNTS, Batch, digest, load_batch, read_payloads, require

COLORS = {'MM-ANOVA': '#278e95', 'MM-PCA': '#c68230', 'STD-ANOVA': '#214d78', 'STD-PCA': '#8968a8'}
NOTICE = ('Descriptive ranking only; selecting a winner using outer-CV scores introduces selection bias. '
          'Three repeats reuse the same 254 patients and overlapping training sets. Sample SD (ddof=1) '
          'describes split variation, not a confidence interval or statistical superiority. No significance tests.')


def short(identifier):
    return identifier.removeprefix('SVM-')


def color(identifier):
    scale, reduction, _, _ = CONFIGS[identifier]
    return COLORS[f'{scale}-{reduction}']


def decorate(fig, batch, title, caption):
    fig.suptitle(title, fontsize=15, fontweight='bold', color='#17394b')
    footer = batch.status + '\n' + caption + '\n' + f'Batch {batch.batch_id} · training {batch.commit[:8]} · results {getattr(batch, "results_commit", "not supplied")[:8]}'
    fig.text(.02, .015, '\n'.join(textwrap.fill(line, 130) for line in footer.splitlines()), fontsize=8, color='#374b57')
    fig.tight_layout(rect=(0, .19, 1, .93))
    return fig


def configuration_figure(batch, identifier, kind='confusion'):
    """Notebook-selectable figures, using validated aggregate rows only."""
    require(identifier in batch.valid, 'Configuration has no validated aggregate evidence')
    if kind == 'stability':
        rows = batch.tables['reports/repeat_scores.csv']
        rows = rows[rows.configuration.eq(identifier)].sort_values('repeat')
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(rows['repeat'], rows.macro_f1, marker='o', color=color(identifier))
        for r in rows.itertuples():
            ax.annotate(f'{r.macro_f1:.4f}', (r.repeat, r.macro_f1), xytext=(0, 9), textcoords='offset points', ha='center')
        ax.set(xticks=[1, 2, 3], xlabel='CV repeat', ylabel='Macro-F1 (0–1)', ylim=(0, 1.05))
        return decorate(fig, batch, short(identifier) + ' · repeat stability', 'Three scores from the same 254 patients. Descriptive split variation, not independent replications or confidence intervals.')
    if kind == 'confusion':
        rows = batch.tables['reports/confusion_matrices.csv']
        matrix = rows[rows.configuration.eq(identifier)].groupby(['true_subtype', 'predicted_subtype'])['count'].sum().unstack().loc[LABELS, LABELS].to_numpy()
        percentages = 100 * matrix / matrix.sum(axis=1, keepdims=True)
        fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
        for ax, values, title, fmt in zip(axes, [matrix, percentages], ['Raw prediction counts', 'Row-normalized percentages'], ['.0f', '.1f']):
            image = ax.imshow(values, cmap='Blues', vmin=0, vmax=312 if fmt == '.0f' else 100)
            for i in range(6):
                for j in range(6):
                    ax.text(j, i, format(values[i, j], fmt) + ('%' if fmt == '.1f' else ''), ha='center', va='center', fontsize=9,
                            color='white' if values[i, j] > image.get_clim()[1] * .6 else '#123044')
            ax.set(xticks=range(6), yticks=range(6), xticklabels=LABELS, yticklabels=LABELS,
                   xlabel='Predicted subtype', ylabel='True subtype', title=title)
            fig.colorbar(image, ax=ax, shrink=.7)
        return decorate(fig, batch, short(identifier) + ' · confusion matrix',
                        'Pooled 3 repeats: 762 held-out prediction events from 254 unique patients (not 762 independent patients). '
                        'Row denominators: LMS 312, DDLPS 171, UPS 147, MFS 75, SS 30, MPNST 27.')
    require(kind == 'subtypes', 'Unknown configuration chart')
    detail = batch.tables['reports/subtype_analysis.csv']
    stats = detail[detail.configuration.eq(identifier)].groupby('subtype').f1.agg(['mean', 'std']).loc[LABELS]
    row = batch.tables['summary.csv'].set_index('configuration').loc[identifier]
    means = [row.macro_f1_mean, *stats['mean']]
    errors = [row.macro_f1_sd, *stats['std']]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.bar(range(7), means, yerr=errors, capsize=4, color=['#17394b'] + [color(identifier)] * 6)
    bounds = (min(0, min(np.array(means)-errors)-.03), max(1.08, max(np.array(means)+errors)+.03))
    ax.set(xticks=range(7), xticklabels=['Macro-F1', *[f'{label}\nn={n}' for label,n in zip(LABELS,COUNTS)]], ylim=bounds, ylabel='F1 (0–1); error bars are sample SD')
    return decorate(fig, batch, short(identifier) + ' · macro and subtype F1',
                    'Bars: mean of 3 repeat scores; error bars: sample SD, ddof=1. Macro-F1 weights all 6 classes equally. '
                    'SS: only 10 patients; MPNST: only 9. Mean ± SD may extend beyond 0–1; it is not a confidence interval.')


def subtype_overview(batch):
    rows = batch.tables['reports/subtype_analysis.csv']
    values = rows[rows.configuration.isin(batch.valid)].groupby(['configuration', 'subtype']).f1.mean().unstack().loc[batch.valid, LABELS]
    fig, ax = plt.subplots(figsize=(12, max(7, len(batch.valid)*.30+3)))
    image = ax.imshow(values, vmin=0, vmax=1, cmap='YlGnBu', aspect='auto')
    for i in range(len(values)):
        for j in range(6):
            value=values.iloc[i,j]
            ax.text(j,i,f'{value:.3f}',ha='center',va='center',fontsize=8,color='white' if value>.65 else '#17394b')
    ax.set(yticks=range(len(values)), yticklabels=[short(c) for c in values.index], xticks=range(6),
           xticklabels=[f'{label}\nn={n}' for label,n in zip(LABELS,COUNTS)])
    for label,identifier in zip(ax.get_yticklabels(),values.index): label.set_color(color(identifier))
    fig.colorbar(image,ax=ax,label='Mean repeat subtype F1')
    return decorate(fig,batch,'Subtype performance · all validated configurations',
                    'Each cell averages 3 repeat-level F1 scores; configurations are grouped by pipeline, not averaged together. SS n=10; MPNST n=9.')


def overview_figure(batch):
    fig, ax = plt.subplots(figsize=(12, 7))
    codes = {'VALIDATED': 2, 'INCOMPLETE': 1, 'INVALID': 0}
    from matplotlib.colors import ListedColormap
    values = np.array([codes[s] for s in batch.overview.status]).reshape(4, 6)
    ax.imshow(values, cmap=ListedColormap(['#f5cccc', '#f4e5bb', '#c5e8dc']), vmin=0, vmax=2, aspect='auto')
    for i, row in enumerate(batch.overview.itertuples()):
        ax.text(i % 6, i // 6, row.status, ha='center', va='center', fontsize=10)
    ax.set(xticks=range(6), xticklabels=['50 linear', '50 RBF', '100 linear', '100 RBF', '150 linear', '150 RBF'],
           yticks=range(4), yticklabels=['MinMax + ANOVA', 'Standard + ANOVA', 'MinMax + PCA', 'Standard + PCA'])
    # CONFIGS order is MM ANOVA, MM PCA, STD ANOVA, STD PCA.
    ax.set_yticklabels(['MinMax + ANOVA', 'MinMax + PCA', 'Standard + ANOVA', 'Standard + PCA'])
    return decorate(fig, batch, 'Validation coverage · all 24 configurations',
                    'VALIDATED means original run audit passed and aggregates are consistent. Missing/failed runs are never silently omitted.')


def global_figures(batch, selected):
    yield 'validation-status', overview_figure(batch)
    if not batch.valid:
        return
    scores = batch.tables['summary.csv'].set_index('configuration').loc[batch.valid]
    ranked = scores.sort_values('macro_f1_mean', ascending=True, kind='stable')
    fig, ax = plt.subplots(figsize=(11, max(6, len(ranked) * .32 + 2)))
    ax.barh([short(i) for i in ranked.index], ranked.macro_f1_mean, xerr=ranked.macro_f1_sd,
            capsize=3, color=[color(i) for i in ranked.index])
    ax.set(xlim=(0, 1.05), xlabel='Macro-F1 (0–1): mean ± sample SD across 3 repeats')
    yield 'macro-f1-ranking', decorate(fig, batch, f'Descriptive Macro-F1 ranking · {len(scores)}/24 configurations', 'SD is split variation, not a confidence interval. Missing/invalid runs are listed in the status overview; no values are imputed.')
    fig, ax = plt.subplots(figsize=(12, 6))
    data = np.full((4, 6), np.nan)
    pipelines = list(COLORS)
    for identifier, row in scores.iterrows():
        scale, reduction, k, kernel = CONFIGS[identifier]
        data[pipelines.index(f'{scale}-{reduction}'), [50, 100, 150].index(k) * 2 + (kernel == 'RBF')] = row.macro_f1_mean
    cmap = plt.colormaps['YlGnBu'].with_extremes(bad='#e6eaed')
    image = ax.imshow(np.ma.masked_invalid(data), cmap=cmap, vmin=0, vmax=1, aspect='auto')
    for i in range(4):
        for j in range(6):
            ax.text(j, i, 'unavailable' if np.isnan(data[i, j]) else f'{data[i,j]:.3f}', ha='center', va='center',
                    color='white' if data[i,j] > .65 else '#17394b')
    ax.set(yticks=range(4), yticklabels=pipelines, xticks=range(6), xticklabels=['50 linear', '50 RBF', '100 linear', '100 RBF', '150 linear', '150 RBF'])
    fig.colorbar(image, ax=ax, label='Mean repeat Macro-F1')
    yield 'pipeline-heatmap', decorate(fig, batch, 'Pipeline × feature/component count × kernel', 'MM = MinMaxScaler; STD = StandardScaler. ANOVA sizes count genes; PCA sizes count components. Gray cells have no validated value.')
    yield 'subtype-comparison-heatmap', subtype_overview(batch)
    fig, (ax, key) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={'width_ratios': [2, 1]})
    key.axis('off')
    key.set_title('Configuration key', fontsize=11)
    label_order = {identifier: rank for rank, identifier in enumerate(scores.sort_values('runtime_seconds', kind='stable').index)}
    for number, (identifier, row) in enumerate(scores.iterrows(), start=1):
        ax.scatter(row.runtime_seconds / 60, row.macro_f1_mean, c=color(identifier), marker='s' if CONFIGS[identifier][3] == 'RBF' else 'o', s=65)
        rank = label_order[identifier]
        ax.annotate(str(number), (row.runtime_seconds / 60, row.macro_f1_mean),
                    xytext=(.03 + .94 * rank / max(1, len(scores)-1), .90 + .045 * (rank % 2)),
                    textcoords='axes fraction', fontsize=8, ha='center',
                    arrowprops={'arrowstyle': '-', 'color': '#8d9ba3', 'linewidth': .6})
        key.text(.01, 1 - number / 25, f'{number:02d}  {short(identifier)}', transform=key.transAxes, fontsize=9, color=color(identifier))
    ax.set(xlabel='Recorded completed outer-fold runtime (minutes)', ylabel='Mean repeat Macro-F1 (0–1)', ylim=(0, 1.05))
    yield 'runtime-performance', decorate(fig, batch, 'Runtime versus descriptive performance', 'Runtime sums completed fold timings, including inner search and refit; it excludes failed attempts, report generation and some validation overhead. Circle = linear; square = RBF. Machine-dependent.')
    fig, ax = plt.subplots(figsize=(11, 6))
    for identifier in selected:
        rows = batch.tables['reports/repeat_scores.csv']
        rows = rows[rows.configuration.eq(identifier)].sort_values('repeat')
        ax.plot(rows['repeat'], rows.macro_f1, marker='o', color=color(identifier), label=short(identifier))
    ax.set(xticks=[1, 2, 3], xlabel='Outer CV repeat', ylabel='Macro-F1 (254 held-out predictions per repeat)', ylim=(0, 1.05))
    ax.legend(fontsize=9, loc='best')
    yield 'repeat-stability', decorate(fig, batch, 'Repeat-to-repeat stability · selected configurations', 'Each repeat covers the same 254 patients once. Lines are descriptive; repeat scores are not independent replications.')


def results_provenance(source, commit, git_path):
    """Bind a copied evidence ZIP to exact Git blob bytes, without changing Git state."""
    require(bool(commit) == bool(git_path), 'Supply both results commit and Git path')
    if not commit:
        return None
    import re
    require(re.fullmatch(r'[0-9a-f]{7,40}', commit), 'Invalid results commit')
    require(Path(source).is_file() and Path(source).suffix.lower() == '.zip', 'Git provenance requires a ZIP input')
    require(not git_path.startswith('/') and '..' not in git_path.split('/') and ':' not in git_path and '\\' not in git_path,
            'Invalid results Git path')
    repo = Path(__file__).resolve().parents[2]
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    try:
        full = git('rev-parse', '--verify', commit + '^{commit}').decode().strip()
        original = git('show', full + ':' + git_path)
    except subprocess.CalledProcessError as error:
        raise ValueError('Results commit/blob unavailable in local Git; fetch the results branch first') from error
    require(original == Path(source).read_bytes(), 'Input ZIP differs from results commit blob')
    return dict(results_commit=full, git_path=git_path, evidence_zip_sha256=digest(original))


def generate(source, output, *, allow_partial=False, allow_synthetic=False, selected=None,
             results_commit=None, results_git_path=None):
    publication = results_provenance(source, results_commit, results_git_path)
    batch = load_batch(source, allow_partial=allow_partial, allow_synthetic=allow_synthetic)
    if publication:
        batch.results_commit = publication['results_commit']
    output = Path(output).resolve()
    input_root = batch.source if batch.source.is_dir() else batch.source.parent
    require(not output.is_relative_to(input_root) and not input_root.is_relative_to(output), 'Output must be separate from input evidence')
    repo = Path(__file__).resolve().parents[2]
    if output.is_relative_to(repo):
        require(any(output.is_relative_to(repo / 'results' / name) for name in ('dashboards', 'dashboard-development')),
                'Inside this repository, reports must be under results/dashboards or results/dashboard-development')
    require(not output.exists(), 'Output already exists; choose a new report directory')
    selected = selected or batch.valid[:4]
    require(len(selected) == len(set(selected)) and set(selected).issubset(batch.valid), 'Selected configurations must be unique validated runs')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'figures').mkdir()
    image_tags = {}
    def save(name, fig):
        path = output / 'figures' / (name + '.png')
        fig.savefig(path, dpi=300, facecolor='white')
        plt.close(fig)
        payload = base64.b64encode(path.read_bytes()).decode('ascii')
        image_tags[name] = f'<img alt="{html.escape(name)}" src="data:image/png;base64,{payload}">'
    for name, fig in global_figures(batch, selected):
        save(name, fig)
    for identifier in batch.valid:
        for kind in ('confusion', 'subtypes', 'stability'):
            save(identifier + '-' + kind, configuration_figure(batch, identifier, kind))
    # Detect changes during rendering. Do not publish an HTML report with mixed evidence.
    current, _ = read_payloads(batch.source)
    require({n: digest(p) for n, p in current.items()} == batch.hashes, 'Inputs changed during rendering; report not published')
    provenance = dict(batch_id=batch.batch_id, source_commit=batch.commit, evidence_status=batch.status,
                      generated_utc=datetime.now(timezone.utc).isoformat(), input_sha256=batch.hashes,
                      reporter_sha256={p.name: digest(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')},
                      packages={'matplotlib': matplotlib.__version__, 'numpy': np.__version__, 'pandas': pd.__version__},
                      dpi=300, selected_configurations=selected, warnings=batch.warnings,
                      results_publication=publication)
    (output / 'report_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    from .dashboard_layout import render_report
    doc = render_report(batch, image_tags, provenance, NOTICE)
    (output / 'report.html').write_text(doc, encoding='utf-8')
    return output / 'report.html'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Batch directory or verified evidence ZIP')
    parser.add_argument('--output', type=Path, required=True, help='New separate report directory; never overwritten')
    parser.add_argument('--allow-partial', action='store_true')
    parser.add_argument('--allow-synthetic', action='store_true', help='Explicit development fixtures only; visibly watermarked')
    parser.add_argument('--configuration', action='append', help='Validated ID to include in the stability chart (repeatable)')
    parser.add_argument('--results-commit', help='Results Git commit; verifies copied ZIP against its Git blob')
    parser.add_argument('--results-git-path', help='Repository-relative ZIP path at the results commit')
    args = parser.parse_args()
    try:
        print(generate(args.input, args.output, allow_partial=args.allow_partial,
                       allow_synthetic=args.allow_synthetic, selected=args.configuration,
                       results_commit=args.results_commit, results_git_path=args.results_git_path))
    except (ValueError, OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise SystemExit(f'Report refused: {error}') from error


if __name__ == '__main__':
    main()
