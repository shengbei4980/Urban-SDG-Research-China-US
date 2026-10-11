# Supplementary Fig. 3: City similarity and coverage of stable Target combinations

Current complete figure: [PNG, 600 dpi](outputs/Supplementary_Fig_3.png) · [vector PDF](outputs/Supplementary_Fig_3.pdf).

Panel a was revised on 11 October 2026 to show the Northeast and Yangtze River Delta locator windows and their dashed graphical leaders. The city/edge data and the geographic projections are unchanged. Panel b retains the supplied circular matrices and city-profile clustering.

## Reproduction

From `supplementary_figures/`:

```bash
python redraw.py --figure 3a
python figure_s3/code/assemble_supplementary_fig_3.py
```

The assembly reads the current vector PDF exports for panels a and b, preserves their scientific marks, crops to the publication panels and exports a complete PDF plus a 600 dpi PNG. The complete figure retains the two-row, two-country arrangement. Dense matrix labels can be inspected in the vector PDF or the separate national zoom outputs.

## Source entries

- [Map renderer](figure_s3a/code/plot_Supplementary_Fig_3a_institution_city_similarity.py)
- [Matrix renderer](figure_s3b/code/plot_Supplementary_Fig_3b_circular_matrix_and_city_clustering_tree.py)
- [Complete-figure assembly](code/assemble_supplementary_fig_3.py)
- [Composition parameters and source hashes](review/composition_verification.json)

The revised complete figure supersedes the earlier document-derived composite in this repository. This repository update does not edit manuscript or supplementary Word files. The document-image field for S3 in `figure_index.csv` is therefore blank.
