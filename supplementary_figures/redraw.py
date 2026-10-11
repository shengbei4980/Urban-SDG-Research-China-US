'Run a source-panel renderer using an environment with its dependencies installed.\nThis does not overwrite the approved full composites in figure_s*/outputs.\n'
from pathlib import Path
import argparse, runpy, sys, os
ROOT=Path(__file__).resolve().parent
ENTRIES={'1': 'figure_s1/plotting_project/code/plot_supplementary_fig_1.py', '2': 'figure_s2/plotting_project/legend/code/build_Supplementary_Fig_2_exact_legend.py', '3a': 'figure_s3/figure_s3a/code/plot_Supplementary_Fig_3a_institution_city_similarity.py', '3b': 'figure_s3/figure_s3b/code/plot_Supplementary_Fig_3b_circular_matrix_and_city_clustering_tree.py', '4a': 'figure_s4/figure_s4a/code/plot_Supplementary_Fig_4a_four_column_vertical_alignment.py', '4b': 'figure_s4/figure_s4b/code/plot_Supplementary_Fig_4b_knowledge_task_differences_in_six_domains.py', '5': 'figure_s5/plotting_project/code/plot_Supplementary_Fig_5_unified_frame_and_Figure1a_palette.py', '6a': 'figure_s6/figure_s6a/code/plot_lorenz.py', '6b': 'figure_s6/figure_s6b/code/plot_supplementary_fig_6b.py', '7a': 'figure_s7/figure_s7a/code/Supplementary_Fig_7a_light_palette_sankey_and_terminal_stage_groups.py', '7b': 'figure_s7/figure_s7b/code/Supplementary_Fig_7b_discrete_mirrored_ridgelines_reconstructed.py', '8': 'figure_s8/plotting_project/code/plot_source_unified_palette.py'}
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
