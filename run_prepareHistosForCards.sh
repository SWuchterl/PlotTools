#!/bin/sh

INPUT_DIR=/eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07042026_2024_1L_Wcb
PROD_VERSION=07042026
EXTRA_NAME=
OUTPUT_DIR=datacard_preparation_07042026/
YEAR=2024


python3 prepareHistosForCards.py --input_dirs $INPUT_DIR/data/ --output_dir $OUTPUT_DIR --tree_name Events --year $YEAR --nproc 1
python3 prepareHistosForCards.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --year $YEAR --nproc 1