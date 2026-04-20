#!/bin/bash
INPUT_DIR="/afs/cern.ch/work/r/rselvati/private/Vcb/CMSSW_15_0_10/src/PhysicsTools/PlotTools/datacards_14032026_v4"
WORKSPACE="workspace_Vcb_SL_2024.root"
OUTPUT="pre_post_fit.root"
CATS="Vcb_catWcb_SR Vcb_catBB_CR Vcb_catBJ_CR Vcb_cat2B_CR Vcb_catCC_CR Vcb_catCJ_CR Vcb_cat2C_CR Vcb_catLF_CR"

python3 postFitShapesCondor.py \
    -i $INPUT_DIR \
    -w $WORKSPACE \
    -o $OUTPUT \
    -c $CATS \
    --skip-proc-errs

#    --postfit \