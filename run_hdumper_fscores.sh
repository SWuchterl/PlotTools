#!/bin/sh
# This script is used to run the hdumper to make histograms with fscores (i.e., those to fit)
PROD_VERSION=14032026_promptID
CONFIG_FILE=configs/hconfig_fscores.csv
EXTRA_NAME=fscores_ttLFm0p1_rebinned
OUTPUT_DIR=histos_$PROD_VERSION/$EXTRA_NAME/
YEAR=2024

# Select ttLF < 0.1
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_18122025_promptMVA_2024_1L_Wcb/mc/ --output_dir histos_18122025_promptMVA/ttLFm0p1/score_tt_Wcb/4FS/  --tree_name Events --input_csv configs/hconfig_minimal.csv --year 2024 --add_selection "score_ttLF < 0.1"
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_18122025_promptMVA_2024_1L_Wcb/mc/ --output_dir histos_18122025_promptMVA/ttLFm0p1/score_tt_Wcb/5FS/  --tree_name Events --input_csv configs/hconfig_minimal.csv --year 2024 --add_selection "score_ttLF < 0.1" --use5FS

# Plotting of the scores in the CR (no fscores defined) or in SR
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/scores/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2024
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/scores/ttLFm0p1/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2024 --add_selection "score_ttLF < 0.1"
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/CR/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2024 --add_selection "score_ttLF < 0.1 && score_tt_Wcb < 0.8"
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/SR/  --tree_name Events --input_csv configs/hconfig_scores.csv --year 2024 --add_selection "score_ttLF < 0.1 && score_tt_Wcb > 0.8"
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/CRfscores/  --tree_name Events --input_csv configs/hconfig_fscores.csv --year 2024 --eventClassification

# Plotting of the 4FS and 5FS (f)scores
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/4FS/  --tree_name Events --input_csv configs/hconfig_fscores.csv --year 2024 --eventClassification
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/5FS/  --tree_name Events --input_csv configs/hconfig_fscores.csv --year 2024 --eventClassification --use5FS
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/score_tt_Wcb/4FS/  --tree_name Events --input_csv configs/hconfig_minimal.csv --year 2024 --add_selection "score_ttLF < 0.1"
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir histos_07012026/ttLFm0p1/score_tt_Wcb/5FS/  --tree_name Events --input_csv configs/hconfig_minimal.csv --year 2024 --add_selection "score_ttLF < 0.1" --use5FS