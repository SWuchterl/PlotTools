#!/bin/sh

# Unstacked scores for signal, ttLF, total background
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process ttLF --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process ttbb --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process tt2b --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process ttbj --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process ttcc --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process tt2c --log
python3 plotUnstacked.py --input_dir histos_07012026/scores/ttLFm0p1/ --input_csv configs/hconfig_scores.csv --output_dir plots_07012026/unstacked/ttLFm0p1/ --process ttcj --log

# Purity/evt number plots for CRs and SR
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/CRSR/ --purity --multiRegion
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/CRSR/ --purity --multiRegion --raw_evt_number

# Purity/evt number plots for 4FS vs 5FS in ttbb, tt2b, and ttbj
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process ttbb
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process ttbb --raw_evt_number
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process tt2b
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process tt2b --raw_evt_number
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process ttbj
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/ --output_dir plots_07012026/purity/ttLFm0p1/FS/ --plot_4F5F --process ttbj --raw_evt_number

# 4FS vs 5FS comparison of ttbb+ttbj+tt2b in the ttWcb score
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/score_tt_Wcb/ --output_dir plots_07012026/FS_vs_score/ --plot_4F5F_vs_score --process ttbx
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/score_tt_Wcb/ --output_dir plots_07012026/FS_vs_score/ --plot_4F5F_vs_score --process ttbb
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/score_tt_Wcb/ --output_dir plots_07012026/FS_vs_score/ --plot_4F5F_vs_score --process ttbj
#python3 plotUnstacked.py --input_dir histos_07012026/ttLFm0p1/score_tt_Wcb/ --output_dir plots_07012026/FS_vs_score/ --plot_4F5F_vs_score --process tt2b

# Plot significance
#python3 plotUnstacked.py --input_dir histos_01102025/scores/ --hist_name h_score_tt_Wcb --output_dir plots_01102025/unstacked/ttLFm0p1/ --significance --log