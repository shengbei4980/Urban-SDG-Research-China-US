# Supplementary figures: code, data and figure files

Directories `figure_s1`–`figure_s9` follow the numbering and order of the current manuscript and supplementary document.

| Figure | Content | Complete figure |
|---|---|---|
| [S1](figure_s1/) | Target co-occurrence in urban SDG research | [PNG](figure_s1/outputs/Supplementary_Fig_1.png) |
| [S2](figure_s2/) | Similarity of target-pair profiles and recurrence across research-hosting cities | [PNG](figure_s2/outputs/Supplementary_Fig_2.png) |
| [S3](figure_s3/) | Content connections of urban needs and balanced knowledge-task differences | [PNG](figure_s3/outputs/Supplementary_Fig_3.png) |
| [S4](figure_s4/) | Intervention modes and text-supported action stages by knowledge task | [PNG](figure_s4/outputs/Supplementary_Fig_4.png) |
| [S5](figure_s5/) | Geographical concentration of supply and sensitivity of city task differences to support thresholds | [PNG](figure_s5/outputs/Supplementary_Fig_5.png) |
| [S6](figure_s6/) | Research content and action stages at different supply positions | [PNG](figure_s6/outputs/Supplementary_Fig_6.png) |
| [S7](figure_s7/) | Screening and content coding of urban research projects | [PNG](figure_s7/outputs/Supplementary_Fig_7.png) |
| [S8](figure_s8/) | Annual changes in research content and target coverage | [PNG](figure_s8/outputs/Supplementary_Fig_8.png) |
| [S9](figure_s9/) | Overall supply and aligned contributions of research-hosting cities | [PNG](figure_s9/outputs/Supplementary_Fig_9.png) |

## Reproduce source panels

```bash
python -m pip install -r requirements.txt
python redraw.py --list
python redraw.py --figure 5b
```

Available entries are `1` (network legend), `2a`, `2b`, `3a`, `3b`, `4`, `5a`, `5b`, `6a`, `6b`, `8` and `9`. Map panel 2a uses the geospatial dependencies in `requirements.txt`. S1 retains its Gephi layout; S7 retains its editable PowerPoint source.

All nine complete PNGs match their actual embedded drawings in the supplied supplementary document byte for byte. Complete-image hashes, captions, source entries and the previous repository numbers are listed in [figure_index.csv](figure_index.csv). The nine figures also follow their first-citation order in the current main manuscript.

Scientific CSV/GPKG data, network exports and source figure payloads were retained without recomputation. File and directory references in code and metadata were updated for the new numbering. Source-panel regeneration remains separate from assembling the approved full publication layouts. Historical audit notes retain their scientific results; local backups and synchronization records remain outside the public repository.
