#!/bin/sh

# First, run MultiDimFit. --algo singles is needed to get the post-fit uncertainties on the POI.
combine -M MultiDimFit workspace_Vcb_SL_2024.root \
    --algo singles \
    -m 125.38 \
    --saveFitResult \
    --saveWorkspace \
    -t -1 \
    --expectSignal 1 \
    --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 \
    --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --cminPreScan \
    --cminPreFit 1 \
    --X-rtd FAST_VERTICAL_MORPH \
    --robustFit 1

# Now run a combineTool command
PostFitShapesFromWorkspace \
    --workspace higgsCombineTest.MultiDimFit.mH125.38.root \
    --fitresult multidimfitTest.root:fit_mdf \
    --postfit \
    --output pre_and_post_fit.root