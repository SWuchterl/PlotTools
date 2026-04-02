#!/bin/sh

# Run toys
combine -M HybridNew Vcb_SL_2024.txt \
    --LHCmode LHC-significance  \
    --saveToys \
    --fullBToys \
    --saveHybridResult \
    -T 100 \
    -i 5 \
    -s 23456 \
    --expectSignal 1 \
    --cminDefaultMinimizerStrategy 0 \
    --cminDefaultMinimizerTolerance 0.1 

# Read the result and exctract the significance. --expectedFromGrid=0.5 is needed to get the median expected significance, otherwise the observed significance will be returned
combine -M HybridNew Vcb_SL_2024.txt \
    --LHCmode LHC-significance \
    --readHybridResult \
    --toysFile=higgsCombineTest.HybridNew.mH120.23456.root \
    --expectedFromGrid=0.5