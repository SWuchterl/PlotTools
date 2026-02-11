#!/bin/sh
# Preselection scores
python3 plotter.py --input_dir histos_07012026/fscores_ttLFm0p1/ --output_dir plots_07012026/fscores_ttLFm0p1/ --sig_norm 5 --input_csv configs/hconfig_fscores.csv --blind
python3 plotter.py --input_dir histos_07012026/fscores_ttLFm0p1/ --output_dir plots_07012026/fscores_ttLFm0p1/ --sig_norm 5 --input_csv configs/hconfig_fscores.csv --blind --log

#python3 plotter.py --input_dir histos_centralVcb_njets4/ --output_dir plots_centralVcb_njets4/ --sig_norm 100 --input_csv configs/hconfig_scores.csv --log
#python3 plotter.py --input_dir histos_centralVcb_njets5/ --output_dir plots_centralVcb_njets5/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_njets6/ --output_dir plots_centralVcb_njets6/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_njetsM6/ --output_dir plots_centralVcb_njetsM6/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nbtag3/ --output_dir plots_centralVcb_nbtag3/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nbtag4/ --output_dir plots_centralVcb_nbtag4/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nbtag5/ --output_dir plots_centralVcb_nbtag5/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nbtagM5/ --output_dir plots_centralVcb_nbtagM5/ --sig_norm 100 --input_csv configs/hconfig_scores.csv --log
#python3 plotter.py --input_dir histos_centralVcb_nctag1/ --output_dir plots_centralVcb_nctag1/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nctag2/ --output_dir plots_centralVcb_nctag2/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nctag3/ --output_dir plots_centralVcb_nctag3/ --sig_norm 100 --input_csv configs/hconfig_scores.csv  --log
#python3 plotter.py --input_dir histos_centralVcb_nctagM3/ --output_dir plots_centralVcb_nctagM3/ --sig_norm 100 --input_csv configs/hconfig_scores.csv --log

# Scores
#python3 plotter.py --input_dir histos_centralVcb/fscores_ttLFm0p1_rebinned/ --output_dir plots_centralVcb/fscores_ttLFm0p1_rebinned/ --sig_norm 5 --input_csv configs/hconfig_fscores.csv --blind
#python3 plotter.py --input_dir histos_centralVcb/fscores_ttLFm0p1_rebinned/ --output_dir plots_centralVcb/fscores_ttLFm0p1_rebinned/ --sig_norm 5 --input_csv configs/hconfig_fscores.csv --blind --log