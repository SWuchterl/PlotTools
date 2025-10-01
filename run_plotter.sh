#!/bin/sh
# Preselection scores
python3 plotter.py --input_dir histos_07072025/scores/ --output_dir plots_07072025/preselection_scores/ --sig_norm 100 --input_csv hconfig_scores.csv --blind --log

# Scores
#python3 plotter.py --input_dir histos_07072025/ttLFm0p1/evtClassification_ttLFm0p1/ --output_dir plots_07072025/evtClassification_ttLFm0p1/ --sig_norm 5 --input_csv hconfig_fscores.csv --blind