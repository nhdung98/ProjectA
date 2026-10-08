# TCGA SARC machine learning

This repository prepares TCGA SARC gene expression and clinical labels for a reproducible comparison of sarcoma subtype classification pipelines. The current stage audits and merges data; it does not train models.

## Setup

From the repository root, create a Python 3.12 virtual environment and install the pinned direct dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The pins record the pandas and NumPy versions used for the verified merge. This is not a complete transitive environment lock. Jupyter is optional and is not required for the command-line workflow.

## Data and configuration

The repository is configured to include these two unchanged input files in Git:

- `data/raw/sarc_tcga_clinical_data.tsv`
- `data/raw/data_mrna_seq_v2_rsem.txt`

Once these files are committed and pushed, cloning or downloading the repository supplies both inputs. No separate data download or archive extraction is needed for the normal workflow. Run the preparation commands below to generate `data/processed/` locally.

Other raw files, including archives, and generated processed files are excluded by `.gitignore`. The two input files were copied unchanged from local working copies. `DATA_SOURCES.md` records their provenance and exact SHA-256 checksums; `DATA_LICENSE.txt` preserves the license notice supplied with the downloaded study. The audit and preparation runs also record source hashes. Preserve the original downloaded archive and acquisition records separately when available.

configs/data.yaml defines input paths, output directory, label mapping, and expected class counts. It uses JSON syntax, which is valid YAML, so the current loader needs only Python's standard library. Keep this format when editing it. Relative paths resolve from the repository root, rather than the current shell directory. --config accepts an alternate config file.

## Reproduce the data preparation

```powershell
python -m src.data.audit
python -m src.data.prepare
```

audit.py checks identifiers, unmatched samples, expression validity, missing values, duplicate gene identifiers, patient repetition, and class counts without writing data. prepare.py runs the audit, refuses unexpected class counts, transposes expression measurements, joins by exact Sample ID, and writes datasets and audit records. Re-running prepare regenerates processed files.

The six-subtype output contains 254 samples from 254 patients and 20,531 genes. Expected labels are LMS 104, DDLPS 57, UPS 49, MFS 25, SS 10, and MPNST 9. Labels come from Cancer Type Detailed to match the research report. Histologic text is retained in the full merge without being used to reassign classes.

The full output preserves 263 matched samples and all clinical columns. Two clinical records lack expression measurements; nine matched samples are outside the target classes. Separate files record exclusions, unmatched clinical records, repeated-patient samples, and gene column mappings. Duplicate gene identifiers remain separate features identified by symbol, Entrez ID, and source row.

Only columns beginning gene__ are expression model inputs. subtype is the target and Patient ID is the split group. No normalization, imputation, scaling, gene filtering, feature selection, or resampling is performed here. These learned steps belong inside model training folds in later pipeline modules.

## Optional acquisition utilities

Skip these utilities when using the bundled input files. They are for acquiring another copy or preparing a deliberately configured alternative dataset. Use a separate destination or configuration rather than overwriting the bundled inputs.

download.py accepts an explicit HTTPS URL and filename; it does not automatically download or choose a clinical export. It refuses existing destination files and can verify an expected SHA-256. extract.py extracts only the configured expression file from a tar archive and refuses existing output.

```powershell
python -m src.data.download --url <public-https-url> --filename sarc_tcga.tar.gz --sha256 <expected-hash>
python -m src.data.extract --archive data/raw/sarc_tcga.tar.gz
```

The expression archive alone does not reproduce the separate clinical export. The bundled clinical TSV preserves the exact export used here; document the provenance separately if replacing it.

## Exploration and verification

notebooks/01_data_exploration.ipynb calls the shared audit code and inspects the prepared dataset. It contains no separate preparation implementation. Open it from the repository root or notebooks directory with a Python environment containing the pinned dependencies.

Preparation verifies saved sample order, feature order, and every expression value after a TSV round trip. data/processed/merge_validation.json records source hashes, configuration, counts, exclusions, package versions, and verification results. The current code has no randomness; later experiments should record seeds and split assignments.
