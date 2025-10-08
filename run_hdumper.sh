#!/bin/sh
# This script is used to run the hdumper to make histograms

#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_17092025_2024_1L_Wcb/mc/ --output_dir histos_01102025/  --tree_name Events --input_csv configs/hconfig.csv --year 2024 --use5FS
#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_17092025_2024_1L_Wcb/data/ --output_dir histos_01102025/  --tree_name Events --input_csv configs/hconfig.csv --year 2024 --use5FS

# Select ttLF < 0.1
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_17092025_2024_1L_Wcb/mc/ --output_dir histos_01102025/scores_ttLFm0p1/ --tree_name Events --input_csv configs/hconfig_scores.csv --year 2024 --add_selection "score_ttLF < 0.1"

# Plotting of the scores in the CR (no fscores defined) or in SR
#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/mc/ --output_dir histos_07072025/ttLFm0p1/CR/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2018 --add_selection "score_ttLF < 0.1 && score_tt_Wcb > 0.6 && score_tt_Wcb < 0.85"
#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/mc/ --output_dir histos_07072025/ttLFm0p1/SR/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2018 --add_selection "score_ttLF < 0.1 && score_tt_Wcb > 0.85"

# Use 5FS and select ttLF < 0.1
#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/mc/ --output_dir histos_07072025/scores_ttLFm0p1_5FS/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2018 --add_selection "score_ttLF < 0.1" --use5FS
#python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/data/ --output_dir histos_07072025/scores_ttLFm0p1_5FS/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2018 --add_selection "score_ttLF < 0.1" --use5FS