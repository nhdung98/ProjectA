"""No fitting, no prediction generation: orchestration uses predefined synthetic labels.
Run ONLY this module on macOS. Existing PCA-order tests include real training.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from src.experiments import pca_order_csv as e


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(e, 'ROOT', self.root))
        # Fail loudly if ANY production ML path is reached, including synthetic fits.
        for target in ('src.experiments.pca_order_csv.fit_search',
                       'src.experiments.svm.fit_search',
                       'sklearn.model_selection.GridSearchCV.fit',
                       'sklearn.pipeline.Pipeline.fit', 'sklearn.pipeline.Pipeline.predict',
                       'sklearn.svm.SVC.fit', 'sklearn.svm.SVC.predict',
                       'sklearn.decomposition.PCA.fit', 'sklearn.decomposition.PCA.fit_transform'):
            self.stack.enter_context(patch(target, side_effect=AssertionError('ML execution forbidden')))
        self.s = dict(round='pca-order-v1', protocol_version='3.0', labels=['a','b'],
                      validation=dict(n_splits=5,n_repeats=3,random_state=42),
                      search=dict(C=[1],gamma=['scale']), configurations=[])
        for k in (1,2,3):
            for order in ('scale_pca','pca_scale'):
                self.s['configurations'].append(dict(id=f'fixture-{k}-{order}',member=4,scaler='minmax',kernel='rbf',k=k,order=order))
        # Fixed metadata records, NOT generated CV assignments or expression data.
        self.data = pd.DataFrame([{'Sample ID':f's{i}','Patient ID':f'p{i}','subtype':'ab'[i%2]} for i in range(10)])
        for i in range(3): self.data[f'gene__{i}'] = 0
        self.outer = pd.DataFrame([dict(repeat=r,fold=i//2+1,**{'Sample ID':f's{i}','Patient ID':f'p{i}','subtype':'ab'[i%2]}) for r in (1,2,3) for i in range(10)])
        self.inner = pd.DataFrame(columns=['repeat','outer_fold','inner_fold','Sample ID'])
        self.proof = {k:k+'-fixture' for k in e.IDENTITY}
        self.proof['protocol'] = self.s['round']
        self.calls = 0
        self.stop = None

    def callback(self, config, settings, data, features, values, train, test, cv, started):
        if self.stop is not None and self.calls == self.stop: raise KeyboardInterrupt()
        self.calls += 1
        # Already-defined fixture labels; no estimator or prediction method involved.
        return ['a','b'], dict(C=1,gamma='scale',best_inner_macro_f1=.5,train_samples=8,test_samples=2,
                              retained_genes=3,runtime_seconds=1,pca_explained_variance=.5)

    def run_member(self, resume=False, member=4):
        with contextlib.redirect_stdout(io.StringIO()):
            return e.run(member,self.s,self.data,[],None,self.outer,self.inner,self.proof,resume=resume,evaluate=self.callback)

    def interrupted(self, folds):
        self.stop = folds
        with self.assertRaises(KeyboardInterrupt): self.run_member()
        self.stop = None
        return e.result_paths(4)[1]

    def mutate(self, change, rehash=True):
        partial = e.result_paths(4)[1]
        table = change(e.read_csv(partial))
        if rehash: table['payload_sha256'] = e.payload_hash(table)
        table.to_csv(partial,index=False,lineterminator='\n')

    def test_fresh_complete_schema_and_collector(self):
        final=self.run_member()
        table,metrics=e.validate(final,self.s,self.data,self.outer,self.proof,4)
        self.assertEqual(self.calls,90); self.assertEqual(len(table),180)
        self.assertEqual(list(table.columns),e.COLUMNS)
        self.assertEqual(len(metrics['team_summary.csv']),6)
        self.assertFalse(e.result_paths(4)[1].exists())

    def test_four_member_collector_compatibility_without_fitting(self):
        original=copy.deepcopy(self.s['configurations'])
        self.s['configurations']=[dict(c,id=f'member{m}-'+c['id'],member=m) for m in (1,2,3,4) for c in original]
        files=[self.run_member(member=m) for m in (1,2,3,4)]
        with contextlib.redirect_stdout(io.StringIO()):
            outputs=e.collect(files,self.root/'aggregates',self.s,self.data,self.outer,self.proof)
        self.assertEqual({name:len(table) for name,table in outputs.items()},
                         {'team_summary.csv':24,'paired_order_comparison.csv':12,'team_repeat_scores.csv':72,
                          'team_subtypes.csv':144,'team_confusions.csv':288,'sources.csv':4})
        self.assertEqual(self.calls,360)

    def test_resume_one_multiple_folds(self):
        for n in (1,8):
            with self.subTest(n=n):
                with tempfile.TemporaryDirectory() as d,patch.object(e,'ROOT',Path(d)):
                    self.calls=0;self.interrupted(n)
                    self.run_member(resume=True)
                    self.assertEqual(self.calls,90)

    def test_empty_or_header_truncated_checkpoint_requires_review(self):
        partial=self.interrupted(0)
        with self.assertRaisesRegex(ValueError,'Empty checkpoint'):self.run_member(True)
        self.assertEqual(self.calls,0)
        with tempfile.TemporaryDirectory() as d,patch.object(e,'ROOT',Path(d)):
            self.calls=0;partial=self.interrupted(1)
            e.read_csv(partial).iloc[:0].to_csv(partial,index=False)
            with self.assertRaisesRegex(ValueError,'Empty checkpoint'):self.run_member(True)
            self.assertEqual(self.calls,1)

    def test_fsync_failure_preserves_last_committed_bytes(self):
        partial=self.interrupted(1);before=partial.read_bytes()
        with patch.object(e.os,'fsync',side_effect=OSError('injected sync failure')):
            with self.assertRaises(OSError):e.checkpoint(partial,[], 'partial')
        self.assertEqual(partial.read_bytes(),before)

    def test_link_created_before_interruption_is_not_overwritten(self):
        def interrupt_after_link(partial,final):
            e.os.link(partial,final);raise KeyboardInterrupt()
        with patch.object(e,'publish',side_effect=interrupt_after_link):
            with self.assertRaises(KeyboardInterrupt):self.run_member()
        final,partial=e.result_paths(4);self.assertTrue(final.exists());self.assertTrue(partial.exists())
        before=final.read_bytes()
        with self.assertRaisesRegex(ValueError,'Result exists'):self.run_member(True)
        e.validate(final,self.s,self.data,self.outer,self.proof,4)
        self.assertEqual(before,final.read_bytes());self.assertEqual(self.calls,90)

    def test_repeated_resume_preserves_rows_and_identity(self):
        partial=self.interrupted(3); original=e.read_csv(partial).copy()
        self.stop=7
        with self.assertRaises(KeyboardInterrupt):self.run_member(resume=True)
        self.stop=None;final=self.run_member(resume=True);table=e.read_csv(final)
        self.assertEqual(self.calls,90)
        self.assertFalse(table.duplicated(e.PREDICTIONS[:5]).any())
        for column in e.COLUMNS:
            if column not in ('run_state','payload_sha256'):
                self.assertEqual(table[column].iloc[:len(original)].tolist(),original[column].tolist())
        events=[json.loads(line)['event'] for line in final.with_suffix('.activity.jsonl').read_text().splitlines()]
        self.assertEqual(events,['start','resume','resume','validated_for_publication'])

    def test_duplicate_and_incomplete_fold_rejected_even_rehashed(self):
        for change in (lambda t:pd.concat([t,t.iloc[:1]]),lambda t:t.iloc[:-1]):
            with tempfile.TemporaryDirectory() as d,patch.object(e,'ROOT',Path(d)):
                self.calls=0;self.interrupted(2);self.mutate(change)
                with self.assertRaises((ValueError,AssertionError)):self.run_member(resume=True)
                self.assertEqual(self.calls,2)

    def test_corrupt_payload_rejected(self):
        self.interrupted(1)
        def change(t):t.loc[0,'predicted_subtype']='b';return t
        self.mutate(change,False)
        with self.assertRaisesRegex(ValueError,'checksum'):self.run_member(resume=True)

    def test_context_mismatches_rejected(self):
        self.interrupted(1)
        for key in ('dataset_sha256','outer_sha256','inner_sha256','code_sha256','git_commit','packages','protocol'):
            original=self.proof[key];self.proof[key]='different'
            with self.assertRaisesRegex(ValueError,'context differs'):self.run_member(resume=True)
            self.proof[key]=original
        for key,value in [('protocol_version','other'),('round','other'),('search',dict(C=[2],gamma=['scale'])),('validation',dict(n_splits=5,n_repeats=3,random_state=99))]:
            original=self.s[key];self.s[key]=value
            with self.assertRaisesRegex(ValueError,'context differs'):self.run_member(resume=True)
            self.s[key]=original
        with patch.object(e.platform,'python_version',return_value='other'):
            with self.assertRaisesRegex(ValueError,'context differs'):self.run_member(resume=True)

    def test_unexpected_records_and_mixed_fold_evidence_rejected(self):
        for key,value in [('configuration','other'),('repeat','99'),('fold','99'),('Patient ID','wrong'),('member','1'),('run_id','wrong'),('C','2'),('runtime_seconds','2')]:
            with tempfile.TemporaryDirectory() as d,patch.object(e,'ROOT',Path(d)):
                self.calls=0;self.interrupted(1)
                def change(t):t.loc[0,key]=value;return t
                self.mutate(change)
                with self.assertRaises((ValueError,AssertionError)):self.run_member(resume=True)

    def test_existing_final_refused_for_fresh_and_resume(self):
        final=self.run_member();before=final.read_bytes()
        for resume in (False,True):
            with self.assertRaisesRegex(ValueError,'Result exists'):self.run_member(resume)
        self.assertEqual(final.read_bytes(),before)

    def test_resume_is_explicit_and_missing_context_refused(self):
        partial=self.interrupted(1)
        with self.assertRaisesRegex(ValueError,'use --resume'):self.run_member()
        e.result_paths(4)[0].with_suffix('.context.json').unlink()
        with self.assertRaisesRegex(ValueError,'original partial CSV and context'):self.run_member(True)

    def test_interrupted_atomic_write_preserves_checkpoint(self):
        partial=self.interrupted(1);before=partial.read_bytes()
        with patch.object(e.os,'replace',side_effect=OSError('injected replacement failure')):
            with self.assertRaises(OSError):self.run_member(True)
        self.assertEqual(before,partial.read_bytes())
        calls=self.calls;self.run_member(True)
        self.assertEqual(self.calls-calls,89)

    def test_crash_after_replacement_skips_durable_fold(self):
        self.interrupted(1); real=e.os.replace
        def replace_then_interrupt(a,b):real(a,b);raise KeyboardInterrupt()
        with patch.object(e.os,'replace',side_effect=replace_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):self.run_member(True)
        self.run_member(True);self.assertEqual(self.calls,90)

    def test_stale_temp_is_not_evidence(self):
        partial=self.interrupted(1); stale=partial.with_name(partial.name+'.orphan.tmp');stale.write_text('broken')
        self.run_member(True);self.assertEqual(self.calls,90);self.assertEqual(stale.read_text(),'broken')

    def test_final_validation_failure_does_not_publish(self):
        real=e.validate
        def reject(*a,**kw):
            if not kw.get('checkpoint_mode'):raise ValueError('injected final validation failure')
            return real(*a,**kw)
        with patch.object(e,'validate',side_effect=reject):
            with self.assertRaisesRegex(ValueError,'final validation'):self.run_member()
        self.assertFalse(e.result_paths(4)[0].exists())
        self.run_member(True);self.assertEqual(self.calls,90)

    def test_publication_failure_can_retry_without_evaluations(self):
        with patch.object(e.os,'link',side_effect=OSError('injected link failure')):
            with self.assertRaises(OSError):self.run_member()
        self.run_member(True);self.assertEqual(self.calls,90)

    def test_existing_destination_not_overwritten_by_publish(self):
        a=self.root/'partial';b=self.root/'final';a.write_bytes(b'new');b.write_bytes(b'original')
        with self.assertRaises(FileExistsError):e.publish(a,b)
        self.assertEqual(b.read_bytes(),b'original')

    def test_active_lock_rejected(self):
        final,_=e.result_paths(4);final.parent.mkdir(parents=True)
        with e.member_lock(final):
            with self.assertRaisesRegex(ValueError,'Another process'):self.run_member()


if __name__ == '__main__': unittest.main()
