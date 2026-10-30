# Supplementary figures: code, data and figure files

The S1–S9 numbering follows the SB-10.30 manuscript and supplementary document.

| Figure | Content | Complete figure |
|---|---|---|
| [S1](figure_s1/) | Screening and content coding of urban research projects | [PNG](figure_s1/outputs/Supplementary_Fig_1.png) |
| [S2](figure_s2/) | Annual changes in research content and target coverage | [PNG](figure_s2/outputs/Supplementary_Fig_2.png) |
| [S3](figure_s3/) | Overall supply and aligned contributions of research-hosting cities | [PNG](figure_s3/outputs/Supplementary_Fig_3.png) |
| [S4](figure_s4/) | Target co-occurrence in urban SDG research | [PNG](figure_s4/outputs/Supplementary_Fig_4.png) |
| [S5](figure_s5/) | Similarity of target-pair profiles and recurrence across research-hosting cities | [PNG](figure_s5/outputs/Supplementary_Fig_5.png) |
| [S6](figure_s6/) | Content connections of urban needs and balanced knowledge-task differences | [PNG](figure_s6/outputs/Supplementary_Fig_6.png) |
| [S7](figure_s7/) | Intervention modes and text-supported action stages by knowledge task | [PNG](figure_s7/outputs/Supplementary_Fig_7.png) |
| [S8](figure_s8/) | Geographical concentration of supply and sensitivity of city task differences to support thresholds | [PNG](figure_s8/outputs/Supplementary_Fig_8.png) |
| [S9](figure_s9/) | Research content and action stages at different supply positions | [PNG](figure_s9/outputs/Supplementary_Fig_9.png) |

## Source-panel reproduction

```bash
python -m pip install -r requirements.txt
python redraw.py --list
python redraw.py --figure 8b
```

Source entries are `2`, `3`, `4` (network legend), `5a`, `5b`, `6a`, `6b`, `7`, `8a`, `8b`, `9a` and `9b`. S1 has an editable PowerPoint source. S4 retains the Gephi network layout. Map panel 5a requires the geospatial dependencies.

All nine complete PNGs match both the supplied SB-10.30 figure files and the actual embedded images in its supplementary document. S1 was updated on 30 October 2026 together with its PowerPoint source. The other eight complete images retain their original bytes; only their numbering changed. Scientific CSV/GPKG data and source network/vector payloads were preserved.

See [figure_index.csv](figure_index.csv) for titles, source entries, image SHA-256 values and the previous repository numbers. Code paths and metadata references use the current numbering. Source-panel generation remains separate from approved composite layouts. Backups and upload verification records are retained locally outside this repository.
