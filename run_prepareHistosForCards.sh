#!/bin/sh

python3 prepareHistosForCards.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/data/ --output_dir datacard_preparation_07012026/VR/testMergingDataObs/ --tree_name Events --year 2024
python3 prepareHistosForCards.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07012026_2024_1L_Wcb/mc/ --output_dir datacard_preparation_07012026/VR/ --tree_name Events --year 2024