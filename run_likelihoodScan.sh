#!/bin/sh

#Run first likelihood scan on the POI Vcb
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root \
    --algo grid \
    -m 125.38 \
    --setParameterRange r=0.2,1.7:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --floatOtherPOIs 1 \
    --saveInactivePOI 1 \
    --robustFit 1 \
    -t -1 \
    -n VcbScan
#Run a second scan freezing all systematics. --freezeParameters allConstrainedNuisances should be needed to also freeze the shape nuisances.
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root \
    --algo grid -m 125.38 \
    --setParameterRange r=0.2,1.7:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --freezeNuisanceGroups systematics,autoMCStats \
    --freezeParameters allConstrainedNuisances \
    --saveInactivePOI 1 \
    --robustFit 1 \
    -t -1 \
    -n VcbScan_FrozenSys

#Plot the likelihood scan result
python3 ../plot1DScan.py higgsCombineVcbScan.MultiDimFit.mH125.38.root \
    --POI r \
    --main-label "Total" \
    --others higgsCombineVcbScan_FrozenSys.MultiDimFit.mH125.38.root:StatOnly:2