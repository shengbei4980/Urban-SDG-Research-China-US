# Distinct research responses to shared urban sustainability goals in China and the US

This repository provides the analysis code, research data, and figure-generation scripts accompanying the study “Distinct research responses to shared urban sustainability goals in China and the US”.

## Folder structure

```text
Urban-SDG-Research-China-US/
├── README.md
├── main_figures/
│   ├── figure1/
│   │   ├── figure1a/          # Code, data, outputs, and notes kept together
│   │   ├── figure1b/
│   │   └── figure1c/
│   ├── figure2/
│   ├── figure3/
│   ├── figure4/
│   └── figure5/
├── supplementary_figures/
│   ├── figure_s1/          # Current Supplementary Fig. 1
│   ├── figure_s2/          # Current Supplementary Fig. 2
│   ├── figure_s3/          # Current Supplementary Fig. 3
│   ├── figure_s4/          # Current Supplementary Fig. 4
│   ├── figure_s5/          # Current Supplementary Fig. 5
│   ├── figure_s6/          # Current Supplementary Fig. 6
│   ├── figure_s7/          # Current Supplementary Fig. 7
│   ├── figure_s8/          # Current Supplementary Fig. 8
│   └── figure_s9/          # Current Supplementary Fig. 9
└── coding_data/               # Raw retrieval tables and coding exports
```

Each figure folder follows the author's original folder hierarchy. Its code, datasets, exported figures, notes, reviews, and historical versions remain together. A figure without subpanels remains a single folder. Existing flat layouts and intermediate subdirectories are retained. English directory names include `code`, `data`, `outputs`, `figures`, `notes`, `review`, and `checks`; no common internal layout is imposed on every figure. Empty source directories are retained locally but are not tracked by Git.

Main-figure folders retain the source archive's numbering. For example, current Figure 1b uses original Figure 1e materials; current Figures 4b, 4c, and 4d use original Figures 4d, 4b, and 4c. Supplementary-figure folders follow the current manuscript order, S1–S9. The screening and coding workflow is [Supplementary Fig. 7](supplementary_figures/figure_s7/outputs/Supplementary_Fig_7.png), and annual changes are Supplementary Fig. 8. See the [supplementary figure index and reproduction guide](supplementary_figures/README.md).

## Coding and raw retrieval data

| File in `coding_data/` | Data level | Rows |
|---|---|---:|
| `nsf_awards_results.csv` | Original NSF award-retrieval table | 25,782 |
| `nsfc_results_requests_no_images.csv` | Original NSFC project-retrieval table | 9,982 |
| `NSF_coding_results.csv` | NSF project-level coding export | 6,207 |
| `NSFC_coding_results.csv` | NSFC project-level coding export | 5,546 |
| `NSF_coding_evidence.csv` | NSF field-level coding evidence export | 122,314 |
| `NSFC_coding_evidence.csv` | NSFC field-level coding evidence export | 108,263 |

Raw retrieval records and the coded study sample represent different stages of processing and need not match one-to-one. Evidence exports contain multiple rows per project and must not be counted as independent projects. Original values, column names, bilingual labels, and evidence quotations are preserved. Read CSV files as UTF-8 with an optional byte-order mark. For definitions and units, consult the corresponding figure's data and source notes.

## Code and provenance

Scientific scripts remain within their original figure folders. Filename, local-module, and directory references affected by English renaming were updated where identifiable. The supplementary-figure archive was synchronized with the revised source folders on 11 October 2026. Its scientific data tables were preserved byte for byte. The later graphical update to Figure 3a-c and Supplementary Fig. 2a preserves the supplied panel exports and scientific inputs; the earlier complete map/network composition is retained as a source reference under S2. English renaming changes path references and documentation only. Current Figure 3b/c exports stay in their existing `figures/` directories; duplicate source output folders and local revision backups are not uploaded. Some legacy scripts still depend on original machine-specific paths, upstream modules, or software that were not supplied; the archive is not represented as a validated single-command workflow. Consult the relevant script and its original notes before rerunning it.

The detailed filename mapping, restructuring tools, and upload-verification reports are maintained locally by the author, outside this repository. Earlier repository organization remains recoverable from Git history.

## Downloading large files

This repository uses Git Large File Storage for five files larger than 50 MiB. With Git LFS installed:

```bash
git clone https://github.com/shengbei4980/Urban-SDG-Research-China-US.git
cd Urban-SDG-Research-China-US
git lfs pull
```

This public repository can be cloned without a GitHub account. A downloaded LFS pointer is not the actual CSV or TIFF file. The `.gitattributes` file also preserves original line endings.

## Access and citation

Repository: [shengbei4980/Urban-SDG-Research-China-US](https://github.com/shengbei4980/Urban-SDG-Research-China-US), made **public** at the author's request. No new license is assigned by this restructuring step. Original notices and third-party rights remain applicable. Final article citation and author-approved licensing can be added when available.

The supplementary figures were renumbered on 14 October 2026 to match the supplied manuscript and supplementary document. All nine complete PNGs now match the embedded document images. The complete S2 and S5 layouts were refreshed from that document; scientific inputs were preserved.
