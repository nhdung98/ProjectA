"""Shared nested validation for 24 SVM configurations."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import tempfile
from joblib import Memory
import uuid
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV, ParameterGrid
from threadpoolctl import threadpool_limits

from .common import ROOT, sha256, write_json, load_dataset, verify_environment, shared_splits
from .validation import fold_indices
from .pipeline import build_pipeline, feature_details
from .metrics import summarize

INNER = ROOT / 'results/splits/inner.csv'
INNER_MANIFEST = ROOT / 'results/splits/inner_manifest.json'

def load_settings():
    return json.loads((ROOT/'configs/svm.json').read_text(encoding='utf-8'))

def candidates(configuration, settings):
    grid = {'model__C': settings['search']['C']}
    if configuration['kernel'] == 'rbf':
        grid['model__gamma'] = settings['search']['gamma']
    return list(ParameterGrid(grid))

def generate_inner(data, outer, settings):
    rows=[]
    for repeat,fold,train,test in fold_indices(outer,data):
        development=data.iloc[train].reset_index(drop=True)
        splitter=StratifiedKFold(**settings['inner_validation'])
        for inner_fold,(fit,validation) in enumerate(splitter.split(np.zeros(len(train)),development.subtype),1):
            if set(development.iloc[fit].subtype)!=set(settings['labels']) or set(development.iloc[validation].subtype)!=set(settings['labels']):
                raise ValueError('An inner fold does not contain all classes')
            if len(fit)<=max(c['k'] for c in settings['configurations'] if c['reduction']=='pca'):
                raise ValueError('Inner training set is too small for informative PCA components')
            block=development.iloc[validation][['Sample ID','Patient ID','subtype']].copy()
            block.insert(0,'inner_fold',inner_fold)
            block.insert(0,'outer_fold',fold)
            block.insert(0,'repeat',repeat)
            rows.append(block)
    return pd.concat(rows,ignore_index=True)

def shared_inner(data,outer,settings,create=False):
    expected=generate_inner(data,outer,settings)
    metadata={'dataset_sha256':sha256(ROOT/settings['dataset']),
              'outer_sha256':sha256(ROOT/'results/splits/outer.csv'),
              'inner_validation':settings['inner_validation']}
    if not INNER.exists():
        if not create or INNER_MANIFEST.exists():
            raise ValueError('Inner assignments missing; leader must prepare-splits')
        expected.to_csv(INNER,index=False,lineterminator='\n')
        write_json(INNER_MANIFEST,{**metadata,'inner_sha256':sha256(INNER)})
    stored=json.loads(INNER_MANIFEST.read_text(encoding='utf-8'))
    if stored!={**metadata,'inner_sha256':sha256(INNER)}:
        raise ValueError('Inner splits or source data changed')
    actual=pd.read_csv(INNER)
    if not actual.equals(expected):
        raise ValueError('Inner assignments differ from agreed seeds, labels, or patient IDs')
    return actual

def inner_indices(development,inner,repeat,fold):
    block=inner[(inner['repeat']==repeat)&(inner.outer_fold==fold)]
    pairs=[]
    for _,group in block.groupby('inner_fold',sort=True):
        mask=development['Sample ID'].isin(group['Sample ID']).to_numpy()
        pairs.append((np.flatnonzero(~mask),np.flatnonzero(mask)))
    return pairs

def provenance(settings,packages):
    # Use the installed Git rather than a bundled helper when available.
    git=Path(r'C:\Program Files\Git\cmd\git.exe')
    executable=str(git) if git.exists() else 'git'
    def query(*args):
        result=subprocess.run([executable,*args],cwd=ROOT,capture_output=True,text=True)
        return result.stdout.strip() if result.returncode==0 else None
    commit,status=query('rev-parse','HEAD'),query('status','--porcelain')
    paths=['src/experiments/'+n for n in ['__init__.py','common.py','validation.py','pipeline.py','metrics.py','svm.py']]
    paths+=['configs/svm.json','requirements-experiments.txt']
    return dict(git_commit=commit,git_dirty=bool(status) if status is not None else None,
                packages=packages,source_sha256=settings['source_sha256'],
                dataset_sha256=sha256(ROOT/settings['dataset']),split_sha256=sha256(ROOT/'results/splits/outer.csv'),
                inner_split_sha256=sha256(INNER),code_sha256={p:sha256(ROOT/p) for p in paths})

def fit_search(configuration,settings,x,y,cv):
    # GridSearch clones the full pipeline, so each inner fit learns its own preprocessing.
    search=GridSearchCV(build_pipeline(configuration,settings),candidates(configuration,settings),
                        scoring=settings['search']['scoring'],cv=cv,refit=True,n_jobs=1,
                        error_score='raise',return_train_score=False)
    # ParameterGrid values must be lists for GridSearchCV's list-of-dicts API.
    search.param_grid=[{key:[value] for key,value in p.items()} for p in candidates(configuration,settings)]
    # Reuse identical training-fold preprocessing across C/gamma candidates.
    # Cache keys include training values, labels, and transformer settings;
    # different folds therefore cannot share a fitted transformation.
    # Temporary caches are local to this search and removed before returning.
    with tempfile.TemporaryDirectory(prefix='sarc-inner-') as cache:
        search.estimator.memory = Memory(cache, verbose=0)
        search.fit(x,y)
    search.best_estimator_.memory = None
    return search

def run_configuration(configuration,settings,data,features,values,outer,inner,packages,smoke=False):
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    destination=ROOT/'results/svm'/configuration['id']/run_id
    destination.mkdir(parents=True,exist_ok=False)
    write_json(destination/'config.json',dict(shared=settings,configuration=configuration,smoke=smoke))
    manifest=dict(**provenance(settings,packages),run_id=run_id,configuration=configuration['id'],
                  status='running',smoke=smoke,folds=[])
    predictions=[]; details=[]; tuning=[]; messages=[]; failed=False
    for repeat,fold,train,test in fold_indices(outer,data):
        start=time.perf_counter(); caught=[]
        record=dict(repeat=repeat,fold=fold,train_samples=len(train),test_samples=len(test))
        try:
            cv=inner_indices(data.iloc[train],inner,repeat,fold)
            with threadpool_limits(limits=settings['blas_threads']), warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                search=fit_search(configuration,settings,values[train],data.iloc[train].subtype,cv)
                labels=search.predict(values[test])
            if caught:
                raise ValueError('A search/refit emitted warnings; review before acceptance')
            record.update(status='complete',best_params=search.best_params_,best_inner_score=float(search.best_score_),
                          search_candidates=len(search.cv_results_['params']),inner_folds=len(cv))
            details.append(dict(repeat=repeat,fold=fold,**feature_details(search.best_estimator_,features)))
            for candidate,params in enumerate(search.cv_results_['params']):
                tuning.append(dict(repeat=repeat,fold=fold,candidate=candidate,params=params,
                                   scores=[float(search.cv_results_[f'split{i}_test_score'][candidate]) for i in range(len(cv))],
                                   mean_score=float(search.cv_results_['mean_test_score'][candidate])))
            for index,label in zip(test,labels):
                predictions.append({'configuration':configuration['id'],'repeat':repeat,'fold':fold,
                                    'Sample ID':data.iloc[index]['Sample ID'],'Patient ID':data.iloc[index]['Patient ID'],
                                    'true_subtype':data.iloc[index].subtype,'predicted_subtype':label})
        except Exception as error:
            failed=True;record.update(status='failed',error=f'{type(error).__name__}: {error}')
            messages.append(f'repeat={repeat} fold={fold} {record["error"]}')
        messages.extend(f'repeat={repeat} fold={fold} {w.category.__name__}: {w.message}' for w in caught)
        record['runtime_seconds']=time.perf_counter()-start
        manifest['folds'].append(record)
        write_json(destination/'run_manifest.json',manifest)
        write_json(destination/'feature_details.json',details)
        write_json(destination/'search_results.json',tuning)
        pd.DataFrame(predictions,columns=['configuration','repeat','fold','Sample ID','Patient ID','true_subtype','predicted_subtype']).to_csv(destination/'predictions.csv',index=False)
        (destination/'warnings.log').write_text('\n'.join(messages),encoding='utf-8')
        print(f'{configuration["id"]} repeat={repeat} fold={fold}: {record["status"]}',flush=True)
        if failed or smoke: break
    manifest['status']='incomplete' if failed else 'smoke_only' if smoke else 'complete'
    write_json(destination/'metrics.json',summarize(pd.DataFrame(predictions),settings['labels'],data['Sample ID'],settings['validation']['n_repeats'])
               if manifest['status']=='complete' else {'status':manifest['status']})
    write_json(destination/'run_manifest.json',manifest)
    print(f'Saved {destination}',flush=True)
    return not failed

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list');commands.add_parser('prepare-splits');commands.add_parser('check')
    run=commands.add_parser('run')
    choice=run.add_mutually_exclusive_group(required=True)
    choice.add_argument('--member',type=int,choices=[1,2,3,4]);choice.add_argument('--configuration',action='append');choice.add_argument('--all',action='store_true')
    run.add_argument('--smoke',action='store_true');run.add_argument('--development',action='store_true',help='Allow dirty/uncommitted source for checks only')
    args=parser.parse_args();settings=load_settings()
    if args.command=='list':
        for c in settings['configurations']: print(c['owner'],c['id'])
        return
    chosen=[]
    if args.command=='run':
        lookup={c['id']:c for c in settings['configurations']}
        if args.configuration:
            if any(i not in lookup for i in args.configuration): parser.error('Unknown configuration ID')
            chosen=[lookup[i] for i in dict.fromkeys(args.configuration)]
        else: chosen=[c for c in settings['configurations'] if args.all or c['owner']==f'Member {args.member}']
    packages=verify_environment(settings)
    print('Checking raw files and prepared expression values...',flush=True)
    data,features,values=load_dataset(settings)
    outer=shared_splits(data,settings,create=args.command=='prepare-splits')
    inner=shared_inner(data,outer,settings,create=args.command=='prepare-splits')
    print(f'Verified {len(data)} patients; {len(outer)} outer and {len(inner)} inner assignments.',flush=True)
    if args.command!='run':return
    proof=provenance(settings,packages)
    if not args.development and not args.smoke and (not proof['git_commit'] or proof['git_dirty'] is not False):
        raise ValueError('Official runs require a clean committed checkout. Use --development only for local checks.')
    for configuration in chosen:
        if not run_configuration(configuration,settings,data,features,values,outer,inner,packages,args.smoke):
            raise SystemExit(1)

if __name__=='__main__':
    try: main()
    except (ValueError,FileNotFoundError) as error: raise SystemExit(f'Experiment stopped: {error}') from error
