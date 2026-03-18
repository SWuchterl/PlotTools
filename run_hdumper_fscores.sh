#!/bin/sh
# This script is used to run the hdumper to make histograms with fscores (i.e., those to fit)
PROD_VERSION=14032026
CONFIG_FILE=configs/hconfig_fscores.csv
EXTRA_NAME=fscores_ttLFm0p1_rebinned
OUTPUT_DIR=histos_$PROD_VERSION/$EXTRA_NAME/
YEAR=2024

python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_14032026_2024_1L_Wcb/mc/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_14032026_2024_1L_Wcb/data/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification 