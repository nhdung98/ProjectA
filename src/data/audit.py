"""Read-only input audit and configuration loading."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

def load_config(path=None):
    config_path = Path(path).resolve() if path else ROOT / 'configs/data.yaml'
    # JSON is a YAML subset; keeping this config in that subset avoids another dependency.
    config = json.loads(config_path.read_text(encoding='utf-8'))
    for key in ['raw_dir', 'processed_dir', 'clinical_file', 'expression_file']:
        p = Path(config[key])
        config[key] = p if p.is_absolute() else ROOT / p
    return config

def audit(config):
    cp, ep = config['clinical_file'], config['expression_file']
    with ep.open(encoding='utf-8') as f:
        header = next(csv.reader(f, delimiter='\t'))
    if len(header) != len(set(header)):
        raise ValueError('Duplicate expression sample identifiers')
    c = pd.read_csv(cp, sep='\t', dtype='string', keep_default_na=False)
    e = pd.read_csv(ep, sep='\t', dtype={'Hugo_Symbol': 'string', 'Entrez_Gene_Id': 'string'})
    required = ['Sample ID', 'Patient ID', config['label_column']]
    if not set(required).issubset(c.columns):
        raise ValueError(f'Missing required clinical columns: {required}')
    if not c['Sample ID'].is_unique or c['Sample ID'].eq('').any() or c['Patient ID'].eq('').any():
        raise ValueError('Clinical sample IDs must be unique and patient/sample IDs nonempty')
    if header[:2] != ['Hugo_Symbol', 'Entrez_Gene_Id']:
        raise ValueError('Unexpected expression gene identifier columns')
    v = e.iloc[:, 2:].apply(pd.to_numeric, errors='raise')
    if np.isinf(v.to_numpy()).any() or (v < 0).any().any():
        raise ValueError('Expression contains negative or infinite values')
    ids = set(header[2:])
    matched = c.loc[c['Sample ID'].isin(ids)]
    selected = matched.loc[matched[config['label_column']].isin(config['target_subtypes'])]
    report = {
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [cp, ep]},
        'clinical_samples': len(c), 'expression_samples': len(ids), 'genes': len(e),
        'matched_samples': len(matched), 'target_samples': len(selected),
        'target_unique_patients': int(selected['Patient ID'].nunique()),
        'class_counts': selected[config['label_column']].map(config['target_subtypes']).value_counts().to_dict(),
        'clinical_without_expression': sorted(set(c['Sample ID'])-ids),
        'expression_without_clinical': sorted(ids-set(c['Sample ID'])),
        'excluded_label_counts': matched.loc[~matched[config['label_column']].isin(config['target_subtypes']), config['label_column']].value_counts().to_dict(),
        'missing_expression_cells': int(v.isna().sum().sum()),
        'duplicate_gene_symbols_beyond_first': int(e.Hugo_Symbol.duplicated().sum()),
        'missing_gene_symbols': int(e.Hugo_Symbol.isna().sum()),
        'duplicate_entrez_ids_beyond_first': int(e.Entrez_Gene_Id.duplicated().sum()),
        'repeated_patients_in_full_merge': int(matched.loc[matched['Patient ID'].duplicated(False), 'Patient ID'].nunique()),
        'label_source': config['label_column'],
    }
    report['matches_expected_class_counts'] = report['class_counts'] == config['expected_class_counts']
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    args = parser.parse_args()
    print(json.dumps(audit(load_config(args.config)), indent=2))

if __name__ == '__main__':
    main()
