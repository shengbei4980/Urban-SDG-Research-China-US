'Run a source-panel renderer using an environment with its dependencies installed.\nThis does not overwrite the approved full composites in figure_s*/outputs.\n'
from pathlib import Path
import argparse, runpy, sys, os
ROOT=Path(__file__).resolve().parent
ENTRIES={'2': 'figure_s2/plotting_project/code/plot_supplementary_fig_2.py', '4': 'figure_s4/plotting_project/legend/code/build_Supplementary_Fig_4_exact_legend.py', '5a': 'figure_s5/figure_s5a/code/plot_Supplementary_Fig_5a_institution_city_similarity.py', '5b': 'figure_s5/figure_s5b/code/plot_Supplementary_Fig_5b_circular_matrix_and_city_clustering_tree.py', '6a': 'figure_s6/figure_s6a/code/plot_Supplementary_Fig_6a_four_column_vertical_alignment.py', '6b': 'figure_s6/figure_s6b/code/plot_Supplementary_Fig_6b_knowledge_task_differences_in_six_domains.py', '7': 'figure_s7/plotting_project/code/plot_Supplementary_Fig_7_unified_frame_and_Figure1a_palette.py', '8a': 'figure_s8/figure_s8a/code/plot_lorenz.py', '8b': 'figure_s8/figure_s8b/code/plot_supplementary_fig_8b.py', '9a': 'figure_s9/figure_s9a/code/Supplementary_Fig_9a_light_palette_sankey_and_terminal_stage_groups.py', '9b': 'figure_s9/figure_s9b/code/Supplementary_Fig_9b_discrete_mirrored_ridgelines_reconstructed.py', '3': 'figure_s3/plotting_project/code/plot_source_unified_palette.py'}
parser=argparse.ArgumentParser()
parser.add_argument('--figure',choices=list(ENTRIES))
parser.add_argument('--list',action='store_true')
args=parser.parse_args()
if args.list or args.figure is None:
    for k,v in ENTRIES.items():print(k,v)
else:
    script=ROOT/ENTRIES[args.figure]
    os.environ.setdefault('MPLBACKEND','Agg')
    sys.argv=[str(script)]
    runpy.run_path(str(script),run_name='__main__')
