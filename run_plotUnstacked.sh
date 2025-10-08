#!/bin/sh

# Unstacked scores for signal, ttLF, total background
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process ttLF --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process ttbb --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process tt2b --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process ttbj --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process ttcc --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process tt2c --log
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --input_csv configs/hconfig_scores.csv --output_dir plots_01102025/unstacked/ --process ttcj --log

# Plot significance
python3 plotUnstacked.py --input_dir histos_01102025/scores/ --hist_name h_score_ttLF --output_dir plots_01102025/unstacked/ --significance --log

# Purity/evt number plots for CRs and SR
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/CRSR/ --purity --multiRegion
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/CRSR/ --purity --multiRegion --raw_evt_number

# Purity/evt number plots for 4FS vs 5FS, ttbb and ttbj
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/FS/ --plot_4F5F --process ttbb
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/FS/ --plot_4F5F --process ttbb --raw_evt_number
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/FS/ --plot_4F5F --process ttbj
#python3 plotUnstacked.py --input_dir histos_07072025/ttLFm0p1/ --output_dir purity_plots/ttLFm0p1/FS/ --plot_4F5F --process ttbj --raw_evt_number

# 4FS vs 5FS comparison of ttbb+ttbj in the ttWcb score
#python3 plotUnstacked.py --input_dir histos_07072025/ --output_dir purity_plots/FS_vs_score/ --plot_4F5F_vs_score