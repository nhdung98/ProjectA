"""Offline HTML presentation of validated aggregates; no evidence writes."""
import html
import json


def render_report(batch, images, provenance, notice):
    esc = html.escape
    publication = provenance.get('results_publication') or {}
    default = 'SVM-STD-ANOVA-150-LINEAR' if 'SVM-STD-ANOVA-150-LINEAR' in batch.valid else next(iter(batch.valid), '')
    def chart(name):
        return images.get(name, '<p>No validated data available.</p>')
    options = ''.join(f'<option value="{c}" {"selected" if c == default else ""}>{c}</option>' for c in batch.valid)
    panels = ''.join(f'<div class="configuration-panel" data-config="{c}" {"hidden" if c != default else ""}>'
                     + ''.join(f'<h3>{title}</h3>'+chart(c+'-'+kind) for kind,title in
                               [('subtypes','Subtype F1 and repeat variability'),('confusion','Where errors occur'),('stability','Stability across three repeats')])
                     + '</div>' for c in batch.valid)
    scores = batch.tables['summary.csv']
    rows = ''.join(f'<tr><td><button class="choose" data-select="{r.configuration}">{r.configuration}</button></td>'
                   f'<td>{r.macro_f1_mean:.6f}</td><td>{r.macro_f1_sd:.6f}</td><td>{r.runtime_seconds/60:.3f}</td></tr>'
                   for r in scores[scores.configuration.isin(batch.valid)].sort_values('macro_f1_mean',ascending=False).itertuples())
    statuses = ''.join(f'<tr><td>{r.configuration}</td><td>{r.status}</td><td>{esc(r.reason)}</td></tr>' for r in batch.overview.itertuples())
    downloads = ''.join(f'<li><a class="figure-download" data-figure="{esc(name)}" download="{esc(name)}.png" href="#">{esc(name)}.png</a></li>' for name in images)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Protocol 2.0 — official results review</title>
<style>body{{margin:0;background:#f0f4f5;color:#203843;font:16px/1.55 system-ui,sans-serif}}header{{background:#153e49;color:white;padding:32px max(4%,calc((100% - 1200px)/2))}}main{{max-width:1200px;margin:auto;padding:20px}}section,details{{background:white;border:1px solid #d9e4e7;border-radius:10px;padding:22px;margin:20px 0}}h1{{margin:8px 0;font-size:32px}}h2{{font-size:23px}}h3{{font-size:18px}}img{{width:100%;height:auto;display:block}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}.card{{background:#e8f2f1;padding:16px;border-radius:8px}}.card strong{{display:block;font-size:25px}}.muted{{color:#526770}}.notice{{border-left:4px solid #c08731;padding-left:15px}}nav a{{color:white;margin-right:20px}}code,pre{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap;font-size:12px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #e0e7e9}}.table-scroll{{max-height:400px;overflow:auto}}button,select{{font:inherit;padding:8px;cursor:pointer}}button.choose{{border:0;background:transparent;color:#155c75;text-align:left;font-size:13px}}select{{max-width:100%;border:1px solid #829da7;border-radius:5px}}summary{{font-weight:650;cursor:pointer}}[hidden]{{display:none!important}}.downloads{{columns:2;font-size:12px;overflow-wrap:anywhere}}@media(max-width:700px){{.downloads{{columns:1}}}}@media print{{nav,.choose{{color:black}}details{{break-inside:avoid}}}}</style></head>
<body><header><p>TCGA-SARC · Protocol 2.0</p><h1>SVM experiment results</h1><p>{esc(batch.status)}</p><nav><a href="#overview">Overview</a><a href="#pipelines">Pipelines</a><a href="#ranking">Ranking</a><a href="#explorer">Explorer</a><a href="#supplement">Evidence</a></nav></header><main>
<section id="overview"><h2>1 · Experiment overview</h2><div class="cards"><div class="card"><strong>{len(batch.valid)}/24</strong>configurations passing automated aggregate checks</div><div class="card"><strong>254</strong>unique patients; six subtypes</div><div class="card"><strong>3 × 5</strong>repeats × outer folds; nested inner tuning</div><div class="card"><strong>{15*len(batch.valid)}</strong>completed outer fits in validated run audits</div></div>
<p><b>Batch:</b> {esc(batch.batch_id)}<br><b>Training commit:</b> <code>{esc(batch.commit)}</code><br><b>Results commit:</b> <code>{esc(publication.get('results_commit','Not supplied / not verified'))}</code></p>
<p>Macro-F1 gives equal weight to the six subtypes. Higher values indicate better performance on these held-out CV predictions. Three repeats reuse the same patients: <b>762 prediction events, not 762 independent patients</b>.</p><p class="notice">SS: only <b>10 patients</b>; MPNST: only <b>9 patients</b>. Automated evidence validation is not clinical validation or human peer-review approval.</p></section>
<section id="pipelines"><h2>2 · Four-pipeline comparison</h2><p>MM means MinMax scaling; STD means Standard scaling. ANOVA selects <b>50, 100 or 150 genes</b>. PCA produces <b>50, 100 or 150 components</b>; components are not individual genes. Each pipeline is tested with Linear and RBF SVM kernels.</p>{chart('pipeline-heatmap')}</section>
<section id="ranking"><h2>3 · All 24 configurations: descriptive ranking</h2><p>Mean Macro-F1 with <b>sample SD across three repeats</b>. Error bars are not confidence intervals. Small score differences do not establish statistical superiority.</p>{chart('macro-f1-ranking')}<details><summary>Exact scores · select a configuration to inspect it</summary><div class="table-scroll"><table><thead><tr><th>Configuration</th><th>Mean Macro-F1</th><th>Sample SD</th><th>Minutes</th></tr></thead><tbody>{rows}</tbody></table></div></details></section>
<section id="subtype-overview"><h2>4 · Which subtypes are difficult?</h2><p>Each cell is the mean of three repeat-level subtype F1 scores. All 24 configurations remain separate. Patient supports appear beside subtype names.</p>{chart('subtype-comparison-heatmap')}</section>
<section id="explorer"><h2>5 · Configuration explorer</h2><label for="configuration">Inspect configuration </label><select id="configuration">{options}</select><p id="selection-status" aria-live="polite">Selected: {default}</p><p>The initial selection is the workflow's reference configuration when available, not an independent confirmation of a winner. Changing the selector updates <b>subtype F1, confusion matrices and repeat stability together</b>.</p><p>Subtype error bars preserve mean ± sample SD, even when extending outside 0–1. Confusion counts pool repeats; percentages divide by each true-subtype row total. Shared colour scales: counts 0–312, percentages 0–100%.</p>{panels}</section>
<details id="runtime"><summary>6 · Optional: recorded runtime versus performance</summary><p>Timings sum completed outer-fold work on the experiment machine. They exclude failed attempts and report generation. They are not a hardware-independent benchmark.</p>{chart('runtime-performance')}</details>
<section id="limitations"><h2>Interpretation and limitations</h2><p>{esc(notice)}</p><p>These results alone do not demonstrate clinical usefulness or generalization to a new clinical population. Perfect scores for a small subtype do not remove uncertainty.</p><p>{' '.join(esc(w) for w in batch.warnings)}</p></section>
<details id="supplement"><summary>7 · Supplementary evidence and all figure downloads</summary><h3>Complete validation coverage</h3>{chart('validation-status')}<div class="table-scroll"><table><thead><tr><th>Configuration</th><th>Status</th><th>Reason</th></tr></thead><tbody>{statuses}</tbody></table></div><h3>Fixed comparison of selected configurations</h3>{chart('repeat-stability')}<h3>All generated PNGs</h3><p>Downloads use the images embedded in this offline HTML. No network connection is required.</p><ul class="downloads">{downloads}</ul><h3>Full provenance</h3><pre>{esc(json.dumps(provenance,indent=2))}</pre></details>
</main><script>
const selector=document.getElementById('configuration');
function selectConfiguration(value){{
 if(!Array.from(selector.options).some(o=>o.value===value))return;
 selector.value=value;
 document.querySelectorAll('.configuration-panel').forEach(panel=>panel.hidden=panel.dataset.config!==value);
 document.getElementById('selection-status').textContent='Selected: '+value;
}}
selector.addEventListener('change',()=>selectConfiguration(selector.value));
document.querySelectorAll('[data-select]').forEach(button=>button.addEventListener('click',()=>{{selectConfiguration(button.dataset.select);document.getElementById('explorer').scrollIntoView({{behavior:'smooth'}});}}));
const figures=new Map(Array.from(document.querySelectorAll('img')).map(img=>[img.alt,img.src]));
document.querySelectorAll('.figure-download').forEach(link=>link.href=figures.get(link.dataset.figure));
</script></body></html>'''
