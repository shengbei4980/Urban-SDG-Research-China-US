'Run a source-panel renderer using an environment with its dependencies installed.\nThis does not overwrite the approved full composites in figure_s*/outputs.\n'
from pathlib import Path
import argparse, runpy, sys, os
ROOT=Path(__file__).resolve().parent
ENTRIES={'8': 'figure_s8/plotting_project/code/plot_supplementary_fig_8.py', '1': 'figure_s1/plotting_project/legend/code/build_Supplementary_Fig_1_exact_legend.py', '2a': 'figure_s2/figure_s2a/code/plot_Supplementary_Fig_2a_institution_city_similarity.py', '2b': 'figure_s2/figure_s2b/code/plot_Supplementary_Fig_2b_circular_matrix_and_city_clustering_tree.py', '3a': 'figure_s3/figure_s3a/code/plot_Supplementary_Fig_3a_four_column_vertical_alignment.py', '3b': 'figure_s3/figure_s3b/code/plot_Supplementary_Fig_3b_knowledge_task_differences_in_six_domains.py', '4': 'figure_s4/plotting_project/code/plot_Supplementary_Fig_4_unified_frame_and_Figure1a_palette.py', '5a': 'figure_s5/figure_s5a/code/plot_lorenz.py', '5b': 'figure_s5/figure_s5b/code/plot_supplementary_fig_5b.py', '6a': 'figure_s6/figure_s6a/code/Supplementary_Fig_6a_light_palette_sankey_and_terminal_stage_groups.py', '6b': 'figure_s6/figure_s6b/code/Supplementary_Fig_6b_discrete_mirrored_ridgelines_reconstructed.py', '9': 'figure_s9/plotting_project/code/plot_source_unified_palette.py'}
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
