"""Opt-in, read-only checks of actual published aggregates; no model code."""
import csv
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import unittest
import zipfile

import numpy as np
import matplotlib.pyplot as plt
from src.reporting.dashboard_inputs import load_batch, LABELS, SCHEMAS
from src.reporting.protocol2_dashboard import configuration_figure, global_figures, results_provenance, subtype_overview, COLORS

SHA = '67ad3e764dadf13827421ab2d6f78f85809b42b3'
PREFIX = 'results/protocol2/windows-official-01/'


@unittest.skipUnless(os.environ.get('PROTOCOL2_OFFICIAL_ZIP'), 'Set PROTOCOL2_OFFICIAL_ZIP to run authentic evidence checks')
class OfficialDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(os.environ['PROTOCOL2_OFFICIAL_ZIP'])
        cls.batch=load_batch(cls.source)
        with zipfile.ZipFile(cls.source) as archive:
            cls.payloads={name:archive.read(name) for name in [*SCHEMAS,'validation_summary.json']}
        cls.rows={name:list(csv.DictReader(io.StringIO(payload.decode()))) for name,payload in cls.payloads.items() if name.endswith('.csv')}

    def test_publication_and_all_pipeline_coverage(self):
        results_provenance(self.source,SHA,PREFIX+'evidence_bundle.zip')
        for name in SCHEMAS:
            blob=subprocess.check_output(['git','show',SHA+':'+PREFIX+name])
            self.assertEqual(blob,self.payloads[name],name)
        b=self.batch
        self.assertEqual(b.batch_id,'windows-official-01')
        self.assertEqual(b.commit,'87f3e6ce1bb3e7fa53e513a22b480abb63998882')
        self.assertFalse(b.synthetic)
        self.assertEqual(len(b.valid),24)
        self.assertEqual(b.tables['summary.csv'].groupby(['scaler','reduction']).size().tolist(),[6,6,6,6])
        audit=json.loads(self.payloads['validation_summary.json'])
        self.assertEqual(sum(a['fits'] for a in audit['runs'].values()),360)

    def test_independent_metric_arithmetic_and_configuration_charts(self):
        for summary in self.rows['summary.csv']:
            identifier=summary['configuration']
            repeats=[r for r in self.rows['reports/repeat_scores.csv'] if r['configuration']==identifier]
            subtype=[r for r in self.rows['reports/subtype_analysis.csv'] if r['configuration']==identifier]
            cells=[r for r in self.rows['reports/confusion_matrices.csv'] if r['configuration']==identifier]
            for metric in ('macro_f1','balanced_accuracy'):
                values=[float(r[metric]) for r in repeats]
                self.assertAlmostEqual(statistics.mean(values),float(summary[metric+'_mean']),places=12)
                self.assertAlmostEqual(statistics.stdev(values),float(summary[metric+'_sd']),places=12)
            pooled=np.zeros((6,6))
            for repeat in range(1,4):
                matrix=[[next(int(r['count']) for r in cells if int(r['repeat'])==repeat and r['true_subtype']==true and r['predicted_subtype']==pred) for pred in LABELS] for true in LABELS]
                pooled+=matrix
                f1s=[]; recalls=[]
                for i,label in enumerate(LABELS):
                    tp=matrix[i][i]; support=sum(matrix[i]); predicted=sum(row[i] for row in matrix)
                    precision=tp/predicted if predicted else 0; recall=tp/support
                    f1=2*tp/(support+predicted)
                    row=next(r for r in subtype if int(r['repeat'])==repeat and r['subtype']==label)
                    for key,value in [('precision',precision),('recall',recall),('f1',f1),('support',support)]:
                        self.assertAlmostEqual(float(row[key]),value,places=12)
                    f1s.append(f1); recalls.append(recall)
                row=next(r for r in repeats if int(r['repeat'])==repeat)
                self.assertAlmostEqual(float(row['macro_f1']),statistics.mean(f1s),places=12)
                self.assertAlmostEqual(float(row['balanced_accuracy']),statistics.mean(recalls),places=12)
            fig=configuration_figure(self.batch,identifier)
            np.testing.assert_array_equal(fig.axes[0].images[0].get_array(),pooled)
            np.testing.assert_allclose(fig.axes[1].images[0].get_array(),pooled/pooled.sum(axis=1,keepdims=True)*100,rtol=0,atol=1e-12)
            plt.close(fig)
            fig=configuration_figure(self.batch,identifier,'subtypes')
            expected=[float(summary['macro_f1_mean'])]+[statistics.mean(float(r['f1']) for r in subtype if r['subtype']==label) for label in LABELS]
            np.testing.assert_allclose([bar.get_height() for bar in fig.axes[0].patches],expected,rtol=0,atol=1e-12)
            plt.close(fig)

    def test_ranking_and_repeat_chart_values(self):
        selected=[c for c in self.batch.valid if '-50-LINEAR' in c]
        for name,fig in global_figures(self.batch,selected):
            if name=='macro-f1-ranking':
                expected=sorted(float(r['macro_f1_mean']) for r in self.rows['summary.csv'])
                np.testing.assert_allclose([bar.get_width() for bar in fig.axes[0].patches],expected,rtol=0,atol=1e-12)
            if name=='repeat-stability':
                for identifier,line in zip(selected,fig.axes[0].lines):
                    expected=[float(r['macro_f1']) for r in self.rows['reports/repeat_scores.csv'] if r['configuration']==identifier]
                    np.testing.assert_allclose(line.get_ydata(),expected,rtol=0,atol=1e-12)
            plt.close(fig)

    def test_redesign_heatmaps_runtime_scales_and_sd(self):
        b=self.batch
        fig=subtype_overview(b)
        expected=[[statistics.mean(float(r['f1']) for r in self.rows['reports/subtype_analysis.csv'] if r['configuration']==c and r['subtype']==label) for label in LABELS] for c in b.valid]
        np.testing.assert_allclose(fig.axes[0].images[0].get_array(),expected,atol=1e-12,rtol=0)
        self.assertEqual(fig.axes[0].images[0].get_clim(),(0,1));plt.close(fig)
        for name,fig in global_figures(b,b.valid[:4]):
            if name=='pipeline-heatmap':
                expected=[[next(float(r['macro_f1_mean']) for r in self.rows['summary.csv'] if r['configuration']==f'SVM-{pipeline}-{k}-{kernel}') for k in (50,100,150) for kernel in ('LINEAR','RBF')] for pipeline in COLORS]
                np.testing.assert_allclose(fig.axes[0].images[0].get_array(),expected,atol=1e-12,rtol=0)
            if name=='runtime-performance':
                for c,points in zip(b.valid,fig.axes[0].collections):
                    row=next(r for r in self.rows['summary.csv'] if r['configuration']==c)
                    np.testing.assert_allclose(points.get_offsets(),[[float(row['runtime_seconds'])/60,float(row['macro_f1_mean'])]],atol=1e-12,rtol=0)
            if name=='validation-status':np.testing.assert_array_equal(fig.axes[0].images[0].get_array(),np.full((4,6),2))
            plt.close(fig)
        for c in b.valid:
            fig=configuration_figure(b,c,'confusion')
            self.assertEqual(fig.axes[0].images[0].get_clim(),(0,312))
            self.assertEqual(fig.axes[1].images[0].get_clim(),(0,100));plt.close(fig)
            fig=configuration_figure(b,c,'stability')
            expected=[float(r['macro_f1']) for r in self.rows['reports/repeat_scores.csv'] if r['configuration']==c]
            np.testing.assert_allclose(fig.axes[0].lines[0].get_ydata(),expected,rtol=0,atol=1e-12);plt.close(fig)
            fig=configuration_figure(b,c,'subtypes')
            row=next(r for r in self.rows['summary.csv'] if r['configuration']==c)
            means=[float(row['macro_f1_mean'])]+[statistics.mean(float(r['f1']) for r in self.rows['reports/subtype_analysis.csv'] if r['configuration']==c and r['subtype']==label) for label in LABELS]
            sd=[float(row['macro_f1_sd'])]+[statistics.stdev(float(r['f1']) for r in self.rows['reports/subtype_analysis.csv'] if r['configuration']==c and r['subtype']==label) for label in LABELS]
            segments=fig.axes[0].collections[0].get_segments()
            np.testing.assert_allclose([[s[0,1],s[1,1]] for s in segments],[[m-d,m+d] for m,d in zip(means,sd)],rtol=0,atol=1e-12)
            self.assertGreaterEqual(fig.axes[0].get_ylim()[1],max(m+d for m,d in zip(means,sd)));plt.close(fig)
