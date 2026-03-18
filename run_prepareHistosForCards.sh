#!/bin/sh

python3 prepareHistosForCards.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_14032026_2024_1L_Wcb/data/ --output_dir datacard_preparation_14032026/ --tree_name Events --year 2024 --nproc 1
python3 prepareHistosForCards.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_14032026_2024_1L_Wcb/mc/ --output_dir datacard_preparation_14032026/ --tree_name Events --year 2024