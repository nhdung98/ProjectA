"""Check nested split isolation, complete search, and leakage protection."""
import unittest
import json
import tempfile
from pathlib import Path
from contextlib import contextmanager
from src.experiments.metrics import summarize
from src.experiments.common import write_json
from src.experiments.validate_svm import audit_run
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold
from unittest.mock import patch
from src.experiments import svm as svm
from src.experiments.validation import generate_splits, fold_indices

class TrackingTransform(TransformerMixin,BaseEstimator):
    seen=[]
    def fit(self,x,y=None):
        self.seen.append(set(x[:,0].astype(int)));return self
    def transform(self,x):return x

class SVMChecks(unittest.TestCase):
    def test_assignment_grid_and_workload(self):
        settings=svm.load_settings()
        self.assertEqual(len(settings['configurations']),24)
        self.assertEqual(len({c['id'] for c in settings['configurations']}),24)
        for member in range(1,5):
            configs=[c for c in settings['configurations'] if c['owner']==f'Member {member}']
            self.assertEqual(len(configs),6)
            self.assertEqual(sum((len(svm.candidates(c,settings))*4+1)*15 for c in configs),4590)

    def test_inner_assignments_exclude_outer_test_and_cover_development(self):
        settings=svm.load_settings()
        labels=sum(([label]*count for label,count in settings['class_counts'].items()),[])
        data=pd.DataFrame({'Sample ID':[f's{i}' for i in range(254)],'Patient ID':[f'p{i}' for i in range(254)],'subtype':labels})
        outer=generate_splits(data,settings['validation'])
        inner=svm.generate_inner(data,outer,settings)
        pd.testing.assert_frame_equal(inner,svm.generate_inner(data,outer,settings))
        for repeat,fold,train,test in fold_indices(outer,data):
            development=data.iloc[train]
            block=inner[(inner['repeat']==repeat)&(inner.outer_fold==fold)]
            self.assertEqual(set(block['Sample ID']),set(development['Sample ID']))
            self.assertFalse(set(block['Sample ID'])&set(data.iloc[test]['Sample ID']))
            self.assertFalse(block['Sample ID'].duplicated().any())
            for fit,validation in svm.inner_indices(development,inner,repeat,fold):
                self.assertGreater(len(fit),150)
                self.assertFalse(set(fit)&set(validation))
                self.assertEqual(set(development.iloc[fit].subtype),set(settings['labels']))
                self.assertEqual(set(development.iloc[validation].subtype),set(settings['labels']))

    def test_gridsearch_refits_preprocessing_inside_each_inner_fold(self):
        settings=svm.load_settings();configuration=settings['configurations'][0]
        settings['search']['C']=[0.1,1]
        x=np.column_stack([np.arange(24),np.sin(np.arange(24))]);y=np.array(['a','b']*12)
        cv=list(StratifiedKFold(4,shuffle=True,random_state=42).split(x,y))
        TrackingTransform.seen=[]
        with patch.object(svm,'build_pipeline',return_value=Pipeline([('track',TrackingTransform()),('model',SVC(kernel='linear'))])):
            search=svm.fit_search(configuration,settings,x,y,cv)
        self.assertEqual(len(TrackingTransform.seen),5)
        for i,seen in enumerate(TrackingTransform.seen[:-1]):
            self.assertEqual(seen,set(cv[i%4][0]))
        self.assertEqual(TrackingTransform.seen[-1],set(range(24)))
        self.assertEqual(len(search.cv_results_['params']),2)


    def test_rewritten_inner_manifest_cannot_hide_changed_patients(self):
        settings=svm.load_settings()
        settings['dataset']='dataset.csv'
        labels=sum(([label]*count for label,count in settings['class_counts'].items()),[])
        data=pd.DataFrame({'Sample ID':[f's{i}' for i in range(254)],'Patient ID':[f'p{i}' for i in range(254)],'subtype':labels})
        outer=generate_splits(data,settings['validation'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'results/splits').mkdir(parents=True)
            data.to_csv(root/'dataset.csv',index=False)
            outer.to_csv(root/'results/splits/outer.csv',index=False)
            path=root/'results/splits/inner.csv';manifest_path=root/'results/splits/inner.json'
            with patch.object(svm,'ROOT',root),patch.object(svm,'INNER',path),patch.object(svm,'INNER_MANIFEST',manifest_path):
                original=svm.shared_inner(data,outer,settings,create=True)
                changed=original.copy();changed.loc[0,'Patient ID']='wrong-patient'
                changed.to_csv(path,index=False)
                manifest=json.loads(manifest_path.read_text());manifest['inner_sha256']=svm.sha256(path)
                write_json(manifest_path,manifest)
                with self.assertRaisesRegex(ValueError,'patient IDs'):
                    svm.shared_inner(data,outer,settings)

    def test_cached_search_matches_uncached_scores_and_predictions(self):
        from sklearn.model_selection import GridSearchCV
        settings=svm.load_settings()
        settings['search']['C']=[0.1,1]
        settings['search']['gamma']=['scale',0.01]
        rng=np.random.default_rng(42)
        x=rng.uniform(0,20,size=(36,10));y=np.array(['a','b','c']*12)
        cv=list(StratifiedKFold(4,shuffle=True,random_state=42).split(x,y))
        for reduction in ['anova','pca']:
            for kernel in ['linear','rbf']:
                configuration=dict(settings['configurations'][0],reduction=reduction,k=2,kernel=kernel)
                cached=svm.fit_search(configuration,settings,x,y,cv)
                grid=[{key:[value] for key,value in params.items()} for params in svm.candidates(configuration,settings)]
                uncached=GridSearchCV(svm.build_pipeline(configuration,settings),grid,scoring='f1_macro',cv=cv,error_score='raise').fit(x,y)
                self.assertEqual(cached.best_params_,uncached.best_params_)
                np.testing.assert_allclose(cached.cv_results_['mean_test_score'],uncached.cv_results_['mean_test_score'],rtol=0,atol=1e-12)
                np.testing.assert_array_equal(cached.predict(x),uncached.predict(x))

    @contextmanager
    def fixture(self):
        settings=svm.load_settings()
        settings['search']['C']=[0.1,1]
        configuration=dict(settings['configurations'][0],k=2)
        settings['configurations']=[configuration,dict(configuration,id='TEST-PCA',reduction='pca')]
        labels=sum(([label]*count for label,count in settings['class_counts'].items()),[])
        data=pd.DataFrame({'Sample ID':[f's{i}' for i in range(254)],'Patient ID':[f'p{i}' for i in range(254)],'subtype':labels})
        for i in range(3):data[f'gene__{i}']=np.arange(254)+i
        outer=generate_splits(data,settings['validation'])
        inner=svm.generate_inner(data,outer,settings)
        predictions=outer.rename(columns={'subtype':'true_subtype'}).copy()
        predictions['configuration']=configuration['id']
        predictions['predicted_subtype']=predictions['true_subtype']
        files=['__init__.py','common.py','pipeline.py','validation.py','metrics.py','svm.py']
        manifest=dict(status='complete',smoke=False,configuration=configuration['id'],source_sha256=settings['source_sha256'],
                      packages=settings['packages'],dataset_sha256='test',split_sha256='test',inner_split_sha256='test',
                      code_sha256={f'src/experiments/{f}':'test' for f in files},folds=[])
        manifest['code_sha256']['configs/svm.json']='test'
        details=[];tuning=[];grid=svm.candidates(configuration,settings)
        for repeat,fold,train,test in fold_indices(outer,data):
            manifest['folds'].append(dict(repeat=repeat,fold=fold,status='complete',train_samples=len(train),test_samples=len(test),runtime_seconds=1,
                                          best_params=grid[1],best_inner_score=.6,search_candidates=2,inner_folds=4))
            details.append(dict(repeat=repeat,fold=fold,retained_after_variance=[f'gene__{i}' for i in range(3)],selected_genes=['gene__0','gene__1']))
            for i,params in enumerate(grid):tuning.append(dict(repeat=repeat,fold=fold,candidate=i,params=params,scores=[.5+i*.1]*4,mean_score=.5+i*.1))
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            for name,value in [('config',dict(shared=settings,configuration=configuration,smoke=False)),('run_manifest',manifest),
                               ('feature_details',details),('search_results',tuning),('metrics',summarize(predictions,settings['labels'],data['Sample ID'],3))]:
                write_json(folder/(name+'.json'),value)
            predictions.to_csv(folder/'predictions.csv',index=False)
            (folder/'warnings.log').write_text('')
            with patch('src.experiments.validate_svm.sha256',return_value='test'),patch('src.experiments.validate_svm.shared_inner',return_value=inner):
                yield folder,settings,data,outer

    def test_nested_audit_accepts_full_evidence(self):
        with self.fixture() as args:
            _,_,report=audit_run(*args)
            self.assertEqual(report['predictions'],762)

    def test_nested_audit_rejects_wrong_search_winner(self):
        with self.fixture() as args:
            folder=args[0]
            manifest=json.loads((folder/'run_manifest.json').read_text())
            manifest['folds'][0]['best_params']['model__C']=.1
            write_json(folder/'run_manifest.json',manifest)
            with self.assertRaisesRegex(ValueError,'search winner'):audit_run(*args)

    def test_nested_audit_rejects_missing_candidate(self):
        with self.fixture() as args:
            folder=args[0]
            tuning=json.loads((folder/'search_results.json').read_text())[:-1]
            write_json(folder/'search_results.json',tuning)
            with self.assertRaisesRegex(ValueError,'Incomplete inner'):audit_run(*args)

    def test_nested_audit_rejects_changed_outer_prediction(self):
        with self.fixture() as args:
            folder=args[0]
            predictions=pd.read_csv(folder/'predictions.csv')
            predictions.loc[0,'predicted_subtype']='MPNST'
            predictions.to_csv(folder/'predictions.csv',index=False)
            with self.assertRaises(AssertionError):audit_run(*args)

if __name__=='__main__':unittest.main()
