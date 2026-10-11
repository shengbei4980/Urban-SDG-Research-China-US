# Supplementary figures: code, data and figure files

Directories `figure_s1` through `figure_s9` follow the current supplementary-material numbering. Each retains the revised source folder hierarchy with English filenames and directory names.

| Figure | Content | Approved complete figure |
|---|---|---|
| [S1](figure_s1/) | Annual changes in research content and SDG Target coverage | [PNG](figure_s1/outputs/Supplementary_Fig_1.png) |
| [S2](figure_s2/) | SDG Target co-occurrence networks | [PNG](figure_s2/outputs/Supplementary_Fig_2.png) |
| [S3](figure_s3/) | City similarity and coverage of stable Target combinations | [PNG](figure_s3/outputs/Supplementary_Fig_3.png) |
| [S4](figure_s4/) | Urban-need content links and knowledge-task differences | [PNG](figure_s4/outputs/Supplementary_Fig_4.png) |
| [S5](figure_s5/) | Intervention types and research-action stages by knowledge task | [PNG](figure_s5/outputs/Supplementary_Fig_5.png) |
| [S6](figure_s6/) | Geographic supply concentration and support-threshold sensitivity | [PNG](figure_s6/outputs/Supplementary_Fig_6.png) |
| [S7](figure_s7/) | Research content and action stages across supply positions | [PNG](figure_s7/outputs/Supplementary_Fig_7.png) |
| [S8](figure_s8/) | City-level research supply and alignment contributions | [PNG](figure_s8/outputs/Supplementary_Fig_8.png) |
| [S9](figure_s9/) | Project screening and research-content coding workflow | [PNG](figure_s9/outputs/Supplementary_Fig_9.png) |

## Reproduce source panels

```bash
python -m pip install -r requirements.txt
python redraw.py --list
python redraw.py --figure 6b
```

The available entries are `1`, `2` (legend), `3a`, `3b`, `4a`, `4b`, `5`, `6a`, `6b`, `7a`, `7b` and `8`. Map panel 3a requires the geospatial dependencies listed in `requirements.txt`. Supplementary Fig. 2 uses the retained Gephi layout. Supplementary Fig. 9 is edited in its PowerPoint source.

The nine approved complete PNGs are copied byte for byte from the revised source archive and match its approved supplementary-document image hashes. Original CSV contents, column names and scientific labels are preserved. Source-panel regeneration is separate from assembling the complete publication layout. File locations, renderer entries and approved-image SHA-256 values are listed in [`figure_index.csv`](figure_index.csv).

## Numbering update

The previous source folders S2-S9 are now S1-S8. The screening and coding workflow previously uploaded under S1 is now S9, with its editable PowerPoint source. S6b uses administrative-location sensitivity results; S7a uses the revised Sankey diagrams. S8 retains the institution-city definition.

Source audit notes are retained in `notes/`; some historical notes and data labels are bilingual. Local upload backups and synchronization records are kept outside this repository.
