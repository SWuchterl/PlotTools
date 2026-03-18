#!/bin/sh
PROD_VERSION=14032026
EXTRA_NAME=fscores_ttLFm0p1_rebinned
INPUT_DIR=histos_$PROD_VERSION/$EXTRA_NAME/
OUTPUT_DIR=plots_$PROD_VERSION/$EXTRA_NAME/
EXTRA_PATH=fscores_ttLFm0p1_rebinned
SIG_NORM=5
CONFIG_FILE=configs/hconfig_fscores.csv

python3 plotUnrolled.py --input_dir $INPUT_DIR --output_dir $OUTPUT_DIR --sig-norm $SIG_NORM --log --blind

# Copy the plot to the appropriate web area
cp $OUTPUT_DIR/log/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH/log/