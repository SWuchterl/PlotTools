#!/bin/sh

#Run first likelihood scan on the POI Vcb
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root --algo grid -m 125 --setParameterRange Vcb=0.8,1.2:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 --floatOtherPOIs 1 --saveInactivePOI 1 --robustFit 1 --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,Vcb=1 -t -1 -P Vcb -n VcbScan
#Run a second scan freezing all systematics
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root --algo grid -m 125 --setParameterRange Vcb=0.8,1.2:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 --floatOtherPOIs 1 --saveInactivePOI 1 --robustFit 1 --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,Vcb=1 -t -1 -P Vcb -n VcbScan_FrozenSys --freezeNuisanceGroups systematics,autoMCStats 
#Plot the likelihood scan result
python3 ../plot1DScan.py higgsCombineVcbScan.MultiDimFit.mH125.root --POI Vcb --main-label "Total" --others higgsCombineVcbScan_FrozenSys.MultiDimFit.mH125.root:StatOnly:2