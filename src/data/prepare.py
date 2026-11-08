"""Match original TCGA-SARC expression and clinical data without learned preprocessing."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import pandas as pd

from .audit import load_config, audit
import argparse

def prepare(config):
    OUT = config['processed_dir']
    EXPRESSION = config['expression_file']
    CLINICAL = config['clinical_file']
    TARGETS = config['target_subtypes']
    source_audit = audit(config)
    if not source_audit['matches_expected_class_counts']:
        raise ValueError('Class counts differ from the configured cohort; review the audit before preparing')
    OUT.mkdir(exist_ok=True)
    with EXPRESSION.open(encoding='utf-8') as f:
        header = next(csv.reader(f, delimiter='\t'))
    assert len(header) == len(set(header)), 'Duplicate expression sample IDs'
    e = pd.read_csv(EXPRESSION, sep='\t', dtype={'Hugo_Symbol': 'string', 'Entrez_Gene_Id': 'string'})
    c = pd.read_csv(CLINICAL, sep='\t', dtype='string', keep_default_na=False)
    assert c['Sample ID'].ne('').all() and c['Sample ID'].is_unique
    assert c['Patient ID'].ne('').all()
    assert c.columns.is_unique
    ids = header[2:]
    values = e.iloc[:, 2:].apply(pd.to_numeric, errors='raise')
    assert not np.isinf(values.to_numpy()).any(), 'Infinite expression values'
    assert not (values < 0).any().any(), 'Negative RSEM expression values'
    # Source row suffix guarantees uniqueness even when symbols or Entrez IDs repeat.
    names = [f'gene__{s if pd.notna(s) else "UNNAMED"}__{g if pd.notna(g) else "NO_ENTREZ"}__row{i+1}'
             for i, (s, g) in enumerate(zip(e.Hugo_Symbol, e.Entrez_Gene_Id))]
    assert len(names) == len(set(names))
    gene_map = pd.DataFrame({'feature_column': names, 'source_gene_row': range(1, len(e)+1),
                             'Hugo_Symbol': e.Hugo_Symbol, 'Entrez_Gene_Id': e.Entrez_Gene_Id})
    x = values.T
    x.columns = names
    x.index.name = 'Sample ID'
    matched_ids = [s for s in ids if s in set(c['Sample ID'])]
    matched_clinical = c.set_index('Sample ID').loc[matched_ids].reset_index()
    merged = matched_clinical.merge(x.reset_index(), on='Sample ID', how='inner', validate='one_to_one', sort=False)
    assert merged['Sample ID'].tolist() == matched_ids
    assert set(names).isdisjoint(c.columns)
    selected = merged[config['label_column']].isin(TARGETS)
    project = merged.loc[selected, ['Sample ID', 'Patient ID', config['label_column']] + names].copy()
    project.insert(3, 'subtype', project[config['label_column']].map(TARGETS))
    excluded = matched_clinical.loc[~selected.to_numpy()].copy()
    excluded['exclusion_reason'] = 'Cancer Type Detailed is outside the six target subtypes'
    unmatched = c.loc[~c['Sample ID'].isin(ids)].copy()
    unmatched['exclusion_reason'] = 'No matching expression sample'
    repeated = matched_clinical.loc[matched_clinical['Patient ID'].duplicated(keep=False)]
    outputs = {'sarc_merged_all.tsv': merged, 'sarc_merged_six_subtypes.tsv': project,
               'gene_feature_map.tsv': gene_map, 'excluded_subtypes.tsv': excluded,
               'unmatched_clinical.tsv': unmatched, 'repeated_patient_samples.tsv': repeated}
    for filename, frame in outputs.items():
        # Fixed line endings keep the agreed dataset checksum identical on Windows and macOS.
        frame.to_csv(OUT / filename, sep='\t', index=False, na_rep='NA', lineterminator='\r\n')
    # Check saved training matrix preserves IDs, feature order, and every expression value.
    saved = pd.read_csv(OUT / 'sarc_merged_six_subtypes.tsv', sep='\t')
    assert saved.columns.tolist() == project.columns.tolist()
    assert saved['Sample ID'].tolist() == project['Sample ID'].tolist()
    np.testing.assert_allclose(saved[names].to_numpy(), project[names].to_numpy(), rtol=1e-14, atol=0, equal_nan=True)
    counts = project['subtype'].value_counts().to_dict()
    report = {
        'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [CLINICAL, EXPRESSION]},
        'clinical_samples': len(c), 'expression_samples': len(ids), 'gene_features': len(e),
        'matched_samples': len(merged), 'target_samples': len(project),
        'target_unique_patients': int(project['Patient ID'].nunique()), 'class_counts': counts,
        'unmatched_expression_samples': sorted(set(ids)-set(c['Sample ID'])),
        'unmatched_clinical_samples': unmatched['Sample ID'].tolist(),
        'excluded_label_counts': excluded[config['label_column']].value_counts().to_dict(),
        'duplicate_clinical_sample_ids': int(c['Sample ID'].duplicated().sum()),
        'duplicate_gene_symbols_beyond_first': int(e.Hugo_Symbol.duplicated().sum()),
        'missing_gene_symbols': int(e.Hugo_Symbol.isna().sum()),
        'duplicate_entrez_ids_beyond_first': int(e.Entrez_Gene_Id.duplicated().sum()),
        'missing_expression_cells': int(values.isna().sum().sum()),
        'repeated_patients_in_full_merge': int(repeated['Patient ID'].nunique()),
        'repeated_patients_in_target_dataset': int(project.loc[project['Patient ID'].duplicated(False), 'Patient ID'].nunique()),
        'label_source': 'Cancer Type Detailed (matches research report); histologic text not used to relabel samples',
        'expression_transformations': 'Transpose only; no aggregation, filtering, imputation, normalization, scaling or feature selection',
        'verification': 'Saved target matrix IDs, column order and all expression values verified against sources',
        'versions': {'pandas': pd.__version__, 'numpy': np.__version__},
    }
    (OUT / 'merge_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (OUT / 'README.md').write_text(
        '# TCGA SARC merged datasets\n\n'
        'The two source files are included in data/raw when committed with the repository. These processed outputs are generated locally and excluded from Git. See ../../DATA_SOURCES.md for source attribution and checksums.\n\n'
        'sarc_merged_six_subtypes.tsv contains one sample per row, four metadata columns '
        '(Sample ID, Patient ID, Cancer Type Detailed, subtype), and all 20,531 gene features. '
        'Use only columns beginning gene__ as model inputs; subtype is the target and Patient ID is the split group.\n\n'
        'sarc_merged_all.tsv preserves all 97 clinical columns for the 263 matched samples, followed by gene features. '
        'Clinical columns must not be treated as gene-expression model inputs.\n\n'
        'Labels come from Cancer Type Detailed, as used by the research report. '
        'The broader UPS clinical label is mapped to UPS without changing the source text. '
        'Histologic labels differ in some records; they were preserved in the full merge and were not used to reassign classes.\n\n'
        'Gene column names contain the original symbol, Entrez ID, and source data row number '
        '(one-based, excluding the header). gene_feature_map.tsv preserves the exact original identifiers. '
        'Duplicate or missing gene identifiers are retained without collapsing expression measurements.\n\n'
        'Nine matched samples outside the target classes and two unmatched clinical records are logged separately. '
        'Four patients have multiple samples in the full merge; the six-subtype dataset has one sample per patient. '
        'Use patient groups when making validation splits.\n\n'
        'No learned preprocessing has been performed. Fit preprocessing and feature selection inside training folds. '
        'merge_validation.json records counts, checks, source SHA-256 hashes, and package versions. '
        'Regenerate with python -m src.data.prepare from the repository root.\n', encoding='utf-8')
    report['configuration'] = {k: str(v) if isinstance(v, Path) else v for k, v in config.items()}
    (OUT / 'merge_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    args = parser.parse_args()
    print(json.dumps(prepare(load_config(args.config)), indent=2))

if __name__ == '__main__':
    main()
