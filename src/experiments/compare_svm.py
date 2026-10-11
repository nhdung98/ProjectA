"""Compare an explicit selection of accepted SVM runs."""
import argparse
import json
import pandas as pd
from .common import ROOT, load_dataset, shared_splits, verify_environment, write_json, sha256
from .svm import load_settings, shared_inner, INNER
from .validate_svm import audit_run, require

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('selection');parser.add_argument('--output',required=True)
    args=parser.parse_args();settings=load_settings();verify_environment(settings)
    selection=json.loads((ROOT/args.selection).read_text(encoding='utf-8'))
    require(set(selection['runs'])=={c['id'] for c in settings['configurations']},'Select exactly the 24 configurations')
    require(bool(selection['code_commit']), 'Record the reviewed code commit')
    require(len(set(selection['runs'].values()))==24,'Repeated run path')
    destination=ROOT/args.output
    require(not destination.exists(),'Output folder must be new')
    data,_,_=load_dataset(settings);outer=shared_splits(data,settings);shared_inner(data,outer,settings)
    overall=[];repeats=[];classes=[];confusions=[];parameters=[];proof=[]
    for identifier,relative in selection['runs'].items():
        folder=ROOT/relative
        _,metrics,audit=audit_run(folder,settings,data,outer)
        manifest=json.loads((folder/'run_manifest.json').read_text(encoding='utf-8'))
        require(manifest['configuration']==identifier,'Selected configuration mismatch')
        require(manifest['git_commit']==selection['code_commit'] and manifest['git_dirty'] is False,'Runs need the same clean reviewed commit')
        row={'configuration':identifier,'run_id':manifest['run_id'],'runtime_seconds':sum(f['runtime_seconds'] for f in manifest['folds'])}
        for name in ['macro_f1','balanced_accuracy']:
            row[name+'_mean']=metrics['summary'][name]['mean'];row[name+'_sample_std']=metrics['summary'][name]['sample_std']
        overall.append(row)
        for repeat in metrics['repeats']:
            repeats.append(dict(configuration=identifier,repeat=repeat['repeat'],macro_f1=repeat['macro_f1'],balanced_accuracy=repeat['balanced_accuracy']))
            for label,values in repeat['per_class'].items():classes.append(dict(configuration=identifier,repeat=repeat['repeat'],subtype=label,**values))
            for i,true in enumerate(settings['labels']):
                for j,predicted in enumerate(settings['labels']):confusions.append(dict(configuration=identifier,repeat=repeat['repeat'],true_subtype=true,predicted_subtype=predicted,count=repeat['confusion_matrix'][i][j]))
        for fold in manifest['folds']:parameters.append(dict(configuration=identifier,repeat=fold['repeat'],fold=fold['fold'],best_inner_score=fold['best_inner_score'],**fold['best_params']))
        proof.append(dict(run=relative,audit=audit,files={p.name:sha256(p) for p in folder.iterdir() if p.is_file()}))
    destination.mkdir(parents=True)
    for name,rows in [('overall_scores',overall),('repeat_scores',repeats),('subtype_repeat_scores',classes),('confusion_matrices',confusions),('selected_parameters',parameters)]:
        pd.DataFrame(rows).to_csv(destination/(name+'.csv'),index=False)
    subtype=pd.DataFrame(classes).groupby(['configuration','subtype']).agg(support=('support','first'),f1_mean=('f1','mean'),f1_sample_std=('f1','std'),recall_mean=('recall','mean')).reset_index()
    subtype.to_csv(destination/'subtype_summary.csv',index=False)
    write_json(destination/'selection.json',selection)
    write_json(destination/'comparison_manifest.json',dict(protocol_version=settings['protocol_version'],outer_sha256=sha256(ROOT/'results/splits/outer.csv'),inner_sha256=sha256(INNER),accepted=proof))
    lines=['# SVM experiment comparison','','All 24 runs passed independent output checks and use the same clean commit.','',
           'Compare repeat and subtype scores alongside the overall scores. Repeats reuse the same patients; standard deviations are not confidence intervals. Choosing a winner from this comparison does not independently validate it.','',
           '| Configuration | Macro-F1 mean | SD | Balanced accuracy |','| --- | ---: | ---: | ---: |']
    for row in sorted(overall,key=lambda r:r['macro_f1_mean'],reverse=True):lines.append(f"| {row['configuration']} | {row['macro_f1_mean']:.3f} | {row['macro_f1_sample_std']:.3f} | {row['balanced_accuracy_mean']:.3f} |")
    lines+=['','Read [repeat scores](repeat_scores.csv), [subtype scores](subtype_repeat_scores.csv), [confusion matrices](confusion_matrices.csv), [selected parameters](selected_parameters.csv), and [validation evidence](comparison_manifest.json).']
    (destination/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Saved {destination}')

if __name__=='__main__':
    try:main()
    except (ValueError,AssertionError,KeyError,FileNotFoundError) as error:raise SystemExit(f'Comparison stopped: {error}') from error
