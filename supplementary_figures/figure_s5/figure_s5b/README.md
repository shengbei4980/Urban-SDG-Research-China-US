# Supplementary Fig. 5b

This folder contains the administrative-location support-threshold sensitivity panel in the current manuscript. The directory and figure number both identify **Supplementary Fig. 5b**.

## Reproduce

```bash
python -m pip install -r code/requirements.txt
python code/plot_supplementary_fig_5b.py
```

The script uses only the input snapshots in this folder and does not modify the manuscript or main figures.

## Files

- `code/plot_supplementary_fig_5b.py`: calculations, checks and plotting.
- `data/input_snapshots/project_level_target_task_allocations.csv`: project-family-weighted allocations to administrative locations, SDGs and knowledge tasks.
- `data/input_snapshots/Figure3b_full_478_locations.csv`: fixed main-figure reference used to verify the recomputed metrics.
- `data/Supplementary_Fig_5b_location_metrics.csv`: recomputed metrics for all 478 locations.
- `data/Supplementary_Fig_5b_source_data.csv`: the eight plotted agency-by-threshold observations.
- `outputs/Supplementary_Fig_5b.png`, `.pdf`, `.svg`: corrected panel; PDF/SVG retain editable text.

## Analysis

The initial samples contain 352 NSF counties and equivalents and 126 NSFC prefecture-level units and equivalents. Within each SDG, base-2 JSD compares a location with all other domestic locations, excluding itself. Location JSD is weighted by its own SDG supply composition, matching Fig. 3b.

Location metrics are calculated once using the full sample. Minimum project-family thresholds of 0, 10, 20 and 30 then select locations for the unweighted JSD median and excluded supply share. Dashed lines are linear visual guides, not inferential estimates. No confidence intervals are shown.

The obsolete `Figure5a` city-scale scatterplots and their old code/data have been archived outside the active repository folder. They are not the current supplementary panel.
