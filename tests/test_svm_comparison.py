"""Check acceptance gates and complete tables for the 24-run comparison."""
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import contextmanager, ExitStack, redirect_stdout
from unittest.mock import patch
import io
import pandas as pd
from src.experiments import compare_svm as compare
from src.experiments.svm import load_settings
from src.experiments.metrics import summarize

class ComparisonChecks(unittest.TestCase):
    @contextmanager
    def fixture(self):
        settings=load_settings()
        data=pd.DataFrame({'Sample ID':[f's{i}' for i in range(60)],'subtype':settings['labels']*10})
        predictions=pd.concat([data.assign(repeat=i) for i in [1,2,3]],ignore_index=True)
        predictions['true_subtype']=predictions.subtype
        predictions['predicted_subtype']=predictions.subtype
        metrics=summarize(predictions,settings['labels'],data['Sample ID'],3)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);runs={}
            for c in settings['configurations']:
                relative='results/'+c['id']+'/run';folder=root/relative;folder.mkdir(parents=True)
                manifest={'configuration':c['id'],'run_id':'run','git_commit':'reviewed','git_dirty':False,
                          'folds':[dict(repeat=r,fold=f,runtime_seconds=1,best_inner_score=.5,best_params={'model__C':1}) for r in [1,2,3] for f in range(1,6)]}
                (folder/'run_manifest.json').write_text(json.dumps(manifest),encoding='utf-8');runs[c['id']]=relative
            selection={'code_commit':'reviewed','runs':runs};path=root/'selection.json'
            path.write_text(json.dumps(selection),encoding='utf-8')
            with ExitStack() as stack:
                for name,value in [('ROOT',root),('load_settings',lambda:settings),('verify_environment',lambda s:{}),
                                   ('load_dataset',lambda s:(data,None,None)),('shared_splits',lambda *args:None),
                                   ('shared_inner',lambda *args:None),('audit_run',lambda *args:(predictions,metrics,{'status':'passed'})),
                                   ('sha256',lambda p:'test')]:stack.enter_context(patch.object(compare,name,value))
                stack.enter_context(patch('sys.argv',['compare','selection.json','--output','results/comparison']))
                stack.enter_context(redirect_stdout(io.StringIO()))
                yield root,selection

    def test_comparison_preserves_all_24_configurations_and_repeat_tables(self):
        with self.fixture() as (root,_):
            compare.main();folder=root/'results/comparison'
            for name,rows in [('overall_scores',24),('repeat_scores',72),('subtype_repeat_scores',432),('confusion_matrices',2592),('selected_parameters',360)]:
                self.assertEqual(len(pd.read_csv(folder/(name+'.csv'))),rows)
            self.assertTrue(pd.read_csv(folder/'subtype_summary.csv').support.eq(10).all())

    def test_comparison_rejects_missing_configuration(self):
        with self.fixture() as (root,selection):
            selection['runs'].pop(next(iter(selection['runs'])))
            (root/'selection.json').write_text(json.dumps(selection),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'24 configurations'):compare.main()
            self.assertFalse((root/'results/comparison').exists())

    def test_comparison_rejects_dirty_or_mixed_commit_runs(self):
        for changes in [{'git_dirty':True},{'git_commit':'different'}]:
            with self.fixture() as (root,selection):
                folder=root/next(iter(selection['runs'].values()))
                manifest=json.loads((folder/'run_manifest.json').read_text(encoding='utf-8'));manifest.update(changes)
                (folder/'run_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'same clean reviewed commit'):compare.main()
                self.assertFalse((root/'results/comparison').exists())

if __name__=='__main__':unittest.main()
