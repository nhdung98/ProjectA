"""Aggregate-only tests: no training code or patient datasets are imported."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import numpy as np
import pandas as pd

from dashboard_fixture import make_fixture
from src.reporting.dashboard_inputs import INPUTS, CONFIGS, load_batch
from src.reporting.protocol2_dashboard import generate, configuration_figure, results_provenance
import matplotlib.pyplot as plt


class DashboardTests(unittest.TestCase):
    def test_redesign_selector_panels_downloads_and_provenance(self):
        from src.reporting.dashboard_layout import render_report
        from html.parser import HTMLParser
        b=self.load()
        names=['pipeline-heatmap','macro-f1-ranking','subtype-comparison-heatmap','runtime-performance','validation-status','repeat-stability']
        names += [c+'-'+kind for c in b.valid for kind in ('subtypes','confusion','stability')]
        images={n:f'<img alt="{n}" src="data:image/png;base64,AA==">' for n in names}
        provenance={'results_publication':{'results_commit':'a'*40},'source_commit':b.commit,'input_sha256':b.hashes}
        text=render_report(b,images,provenance,'Descriptive only')
        class Inspect(HTMLParser):
            def __init__(self): super().__init__();self.panels=[];self.options=[];self.images=[];self.downloads=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if a.get('class')=='configuration-panel':self.panels.append(a)
                if tag=='option':self.options.append(a['value'])
                if tag=='img':self.images.append(a['alt'])
                if a.get('class')=='figure-download':self.downloads.append(a['data-figure'])
        parser=Inspect();parser.feed(text)
        self.assertEqual(parser.options,b.valid)
        self.assertEqual(len(parser.panels),24)
        self.assertEqual(sum('hidden' not in p for p in parser.panels),1)
        self.assertEqual(set(parser.images),set(names));self.assertEqual(set(parser.downloads),set(names))
        self.assertIn('panel.hidden=panel.dataset.config!==value',text)
        self.assertIn("selector.addEventListener('change'",text)
        for c in b.valid:
            start=text.index('data-config="'+c+'"');end=text.index('</div>',start)
            for kind in ('subtypes','confusion','stability'): self.assertIn(c+'-'+kind,text[start:end])
        self.assertIn('a'*40,text)
        self.assertIn('SS: only <b>10 patients</b>',text)
        self.assertIn('762 prediction events, not 762 independent patients',text)

    def test_results_provenance_requires_matching_git_blob(self):
        path=self.root/'copy.zip'; path.write_bytes(b'fixture bytes')
        sha='a'*40
        with patch('src.reporting.protocol2_dashboard.subprocess.check_output',side_effect=[sha.encode(),b'fixture bytes']):
            result=results_provenance(path,sha,'results/batch/evidence_bundle.zip')
        self.assertEqual(result['results_commit'],sha)
        with patch('src.reporting.protocol2_dashboard.subprocess.check_output',side_effect=[sha.encode(),b'other bytes']):
            with self.assertRaisesRegex(ValueError,'differs'): results_provenance(path,sha,'results/batch/evidence_bundle.zip')
        with self.assertRaisesRegex(ValueError,'both'): results_provenance(path,sha,None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = make_fixture(self.root/'source')

    def load(self, **kwargs):
        return load_batch(self.source, allow_synthetic=True, **kwargs)

    def rehash(self, name):
        path = self.source/'validation_summary.json'
        validation = json.loads(path.read_text())
        validation['export_files'][name] = hashlib.sha256((self.source/name).read_bytes()).hexdigest()
        path.write_text(json.dumps(validation))

    def test_full_matrix_metric_definitions_and_explicit_demo_gate(self):
        with self.assertRaisesRegex(ValueError, 'Synthetic fixtures'):
            load_batch(self.source)
        batch = self.load()
        self.assertEqual(len(batch.valid), 24)
        self.assertIn('NOT RESEARCH RESULTS', batch.status)
        identifier = batch.valid[0]
        fig = configuration_figure(batch, identifier)
        counts, pct = [np.asarray(ax.images[0].get_array()) for ax in fig.axes[:2]]
        self.assertEqual(counts.sum(), 762)
        np.testing.assert_allclose(pct.sum(axis=1), 100)
        plt.close(fig)

    def test_input_hash_and_extra_private_columns_fail_closed(self):
        path = self.source/'summary.csv'
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.load(allow_partial=True)
        self.rehash('summary.csv')
        table = pd.read_csv(path); table['Patient ID'] = 'DO-NOT-EXPORT'
        table.to_csv(path,index=False); self.rehash('summary.csv')
        with self.assertRaisesRegex(ValueError, 'Unexpected columns'):
            self.load(allow_partial=True)

    def test_corrupt_metrics_are_visible_not_silently_dropped(self):
        path = self.source/'summary.csv'; table = pd.read_csv(path)
        table.loc[0,'macro_f1_mean'] = .123456
        table.to_csv(path,index=False); self.rehash('summary.csv')
        with self.assertRaisesRegex(ValueError, 'not fully validated'):
            self.load()
        batch = self.load(allow_partial=True)
        self.assertIn('INCOMPLETE',batch.status)
        self.assertEqual(len(batch.valid),23)
        self.assertEqual(batch.overview.iloc[0].status,'INVALID')

    def test_missing_failed_unplanned_and_batch_failure_status(self):
        path=self.source/'validation_summary.json'; validation=json.loads(path.read_text())
        validation['status']='failed'; validation['runs'][list(CONFIGS)[0]]['status']='failed'
        path.write_text(json.dumps(validation))
        batch=self.load(allow_partial=True)
        self.assertEqual(batch.overview.iloc[0].status,'INVALID')
        self.assertIn('INCOMPLETE',batch.status)
        (self.source/'reports/repeat_scores.csv').unlink()
        batch=self.load(allow_partial=True)
        self.assertEqual(len(batch.valid),0)
        partial=make_fixture(self.root/'partial',2)
        batch=load_batch(partial,allow_synthetic=True,allow_partial=True)
        self.assertEqual(len(batch.valid),2)
        self.assertEqual(batch.overview.status.eq('INCOMPLETE').sum(),22)

    def test_counts_repeat_duplicates_labels_and_runtime_rejected(self):
        for filename, column, value in [('reports/confusion_matrices.csv','count',-1),
                                         ('reports/subtype_analysis.csv','f1',float('nan')),
                                         ('reports/repeat_scores.csv','repeat',2),
                                         ('summary.csv','runtime_seconds',-1)]:
            with self.subTest(filename=filename):
                path=self.source/filename; original=path.read_bytes()
                table=pd.read_csv(path); table.loc[0,column]=value; table.to_csv(path,index=False); self.rehash(filename)
                self.assertEqual(self.load(allow_partial=True).overview.iloc[0].status,'INVALID')
                path.write_bytes(original); self.rehash(filename)
        path=self.source/'experiment_manifest.json'; manifest=json.loads(path.read_text()); manifest['settings']['labels'].reverse()
        path.write_text(json.dumps(manifest)); self.rehash('experiment_manifest.json')
        with self.assertRaisesRegex(ValueError,'label order'):
            self.load()

    def test_zip_inventory_verification_and_no_extraction(self):
        path=self.root/'evidence.zip'
        payloads={n:(self.source/n).read_bytes() for n in INPUTS}
        inventory={'schema_version':1,'entry_sha256':{n:hashlib.sha256(p).hexdigest() for n,p in payloads.items()}}
        for tamper in (False,True):
            with zipfile.ZipFile(path,'w') as archive:
                for name,payload in payloads.items():
                    archive.writestr(name,payload + b'changed' if tamper and name=='summary.csv' else payload)
                archive.writestr('EXPORT_CHECKSUMS.json',json.dumps(inventory))
            if tamper:
                with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                    load_batch(path,allow_synthetic=True)
            else:
                self.assertEqual(len(load_batch(path,allow_synthetic=True).valid),24)
        self.assertFalse((self.root/'summary.csv').exists())

    def test_sanitized_external_zip_uses_export_specific_hashes(self):
        payloads={n:(self.source/n).read_bytes() for n in INPUTS}
        manifest=json.loads(payloads['experiment_manifest.json'])
        manifest['provenance'].pop('python_executable')
        payloads['experiment_manifest.json']=json.dumps(manifest).encode()
        validation=json.loads(payloads['validation_summary.json'])
        validation['source_artifact_sha256']=validation.pop('export_files')
        payloads['validation_summary.json']=json.dumps(validation).encode()
        inventory={'schema_version':1,'audience':'external',
                   'entry_sha256':{n:hashlib.sha256(p).hexdigest() for n,p in payloads.items()}}
        path=self.root/'sanitized.zip'
        with zipfile.ZipFile(path,'w') as archive:
            for name,payload in payloads.items(): archive.writestr(name,payload)
            archive.writestr('EXPORT_CHECKSUMS.json',json.dumps(inventory))
        self.assertEqual(len(load_batch(path,allow_synthetic=True).valid),24)

    def test_batch_completion_attestation_cannot_be_inferred_from_rows(self):
        path=self.source/'validation_summary.json'; original=path.read_bytes()
        for key,value in [('status','failed'),('full_24_comparison',False),('configurations',23)]:
            validation=json.loads(original); validation[key]=value
            path.write_text(json.dumps(validation))
            with self.assertRaisesRegex(ValueError,'not fully validated'): self.load()
            batch=self.load(allow_partial=True)
            self.assertEqual(len(batch.valid),24)
            self.assertIn('INCOMPLETE',batch.status)
        path.write_bytes(original)

    def test_output_read_only_privacy_self_contained_png_and_no_overwrite(self):
        source=make_fixture(self.root/'two',2)
        before={p.name:p.read_bytes() for p in source.rglob('*') if p.is_file()}
        report=generate(source,self.root/'report',allow_partial=True,allow_synthetic=True)
        contents=report.read_text()
        self.assertIn('SYNTHETIC DEMONSTRATION',contents)
        self.assertIn('INCOMPLETE',contents)
        self.assertIn('data:image/png;base64,',contents)
        self.assertNotIn('PRIVATE_FIXTURE',contents)
        self.assertNotIn('/Users/',contents)
        self.assertNotIn('src="http',contents)
        self.assertIn('configuration-panel',contents)
        self.assertEqual(len(list((report.parent/'figures').glob('*.png'))),12)
        from PIL import Image
        for path in (report.parent/'figures').glob('*.png'):
            with Image.open(path) as im:
                self.assertGreaterEqual(im.width,2400)
                self.assertAlmostEqual(im.info['dpi'][0],300,places=1)
        self.assertEqual(before,{p.name:p.read_bytes() for p in source.rglob('*') if p.is_file()})
        with self.assertRaisesRegex(ValueError,'already exists'):
            generate(source,self.root/'report',allow_partial=True,allow_synthetic=True)
        with self.assertRaisesRegex(ValueError,'separate'):
            generate(source,source/'forbidden',allow_partial=True,allow_synthetic=True)
        self.assertFalse((source/'forbidden').exists())

    def test_source_mutation_during_render_refuses_html(self):
        from src.reporting import protocol2_dashboard as module
        original=module.global_figures
        def changed(batch,selected):
            (self.source/'comparison.csv').write_bytes(b'changed')
            yield from original(batch,selected)
        with patch.object(module,'global_figures',side_effect=changed), patch.object(module,'configuration_figure'):
            # A zero-valid partial snapshot avoids saving mocked configuration figures.
            validation=json.loads((self.source/'validation_summary.json').read_text())
            for audit in validation['runs'].values(): audit['status']='failed'
            (self.source/'validation_summary.json').write_text(json.dumps(validation))
            with self.assertRaisesRegex(ValueError,'Inputs changed'):
                generate(self.source,self.root/'changed-report',allow_partial=True,allow_synthetic=True)
        self.assertFalse((self.root/'changed-report/report.html').exists())


if __name__=='__main__':
    unittest.main()
