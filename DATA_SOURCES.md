# TCGA SARC data sources

The repository includes two unchanged input files for reproducing its data preparation. They are local working copies of the Sarcoma TCGA Firehose Legacy study downloaded from cBioPortal. The research report records October 4, 2026 as the download date; this date comes from that report rather than an independently retained download log.

Study: https://www.cbioportal.org/study/summary?id=sarc_tcga

Original project: https://portal.gdc.cancer.gov/projects/TCGA-SARC

## Included input files

| Repository path | Contents | SHA-256 |
| --- | --- | --- |
| `data/raw/sarc_tcga_clinical_data.tsv` | Clinical export with sample identifiers and subtype labels | `ef96a946f513bad5fac4fcdb8663586286db20b8cd04f5be5bc598c6e348d6b5` |
| `data/raw/data_mrna_seq_v2_rsem.txt` | Gene expression matrix from the downloaded study archive | `e364fba8c62b01e40b17fc7cdf95e4e7487654f1aeeb81a0c055897aa8adceee` |

`data/raw` describes these files' role as unmodified project inputs. The expression file already contains processed RSEM measurements supplied by the source; it is not raw sequencing reads.

The clinical file was copied from the working file in C:/PROJECTA. The expression file was copied from the extracted study in the original local PROJECTA/Data folder. These machine-specific locations are not required to run the repository. The original download request and a permalink to the exact clinical export were not retained in the current repository; the included files and checksums fix the input snapshot used here.

## Attribution and supplied notice

The Cancer Genome Atlas Research Network. Comprehensive and Integrated Genomic Characterization of Adult Soft Tissue Sarcomas. Cell (2017). https://doi.org/10.1016/j.cell.2017.10.014

Cerami et al. The cBio Cancer Genomics Portal An Open Platform for Exploring Multidimensional Cancer Genomics Data. Cancer Discovery (2012). https://doi.org/10.1158/2159-8290.CD-12-0095

Gao et al. Integrative Analysis of Complex Cancer Genomics and Clinical Profiles Using the cBioPortal. Science Signaling (2013). https://doi.org/10.1126/scisignal.2004088

`DATA_LICENSE.txt` reproduces the notice shipped with the expression study archive. That notice names the Broad Institute GDAC TCGA Analysis Pipeline License; it is not a complete copy of those terms. The separate clinical export contained no standalone license notice in the supplied files. cBioPortal's general data licensing guidance is at https://docs.cbioportal.org/user-guide/faq/. Preserve the source attribution and study-specific notice; a software license for this repository does not replace dataset terms.

## Reproduction

Install requirements.txt, run `python -m src.data.audit`, then `python -m src.data.prepare` from the repository root. The audit prints current input hashes, which can be compared with the snapshot above. Processed files are generated locally and excluded from Git. If intentionally replacing either input, review provenance, hashes, label mappings, and expected class counts together.
