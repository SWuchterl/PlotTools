import CombineHarvester.CombineTools.ch as ch
import ROOT
import os
import subprocess
import argparse
from fixNegativeBins import fixNegativeBins

parser = argparse.ArgumentParser(description='Prepare datacards for Vcb analysis')
parser.add_argument('--year', type=str, default='2024', help='Data taking year')
parser.add_argument('--inputdir', type=str, required=True, help='Input directory for the analysis')
parser.add_argument('--outdir', type=str, required=True, help='Output directory for the datacards')
parser.add_argument('--doAutoMCStats', nargs="?", const=1, type=bool, default=False, required=False, help='Use AutoMCStats')
parser.add_argument('--optimizeWSforFits', nargs="?", const=1, type=bool, default=False, required=False, help='Add workspace optimization options for fits. Not suitable for pre/postfit plots')
args = parser.parse_args()

year = args.year
inputdir = args.inputdir
outdir = args.outdir

if not os.path.exists(outdir):
    os.makedirs(outdir)

channel = "SL"
bkgs = ["singletop", "ttbb", "ttbj", "tt2b", "ttcc", "ttcj", "tt2c", "ttLF", "wjets", "ttZ", "diboson", "ttHbb", "ttHcc"] #"ttbb-dps" and "ttW" whenever ready
signal = ["tt-vcb"]
tt_components = ['tt-vcb','ttbb', 'ttbj', 'tt2b' ,'ttcc', 'ttcj', 'ttLF'] #'ttbb-dps' whenever ready
tt_components_nobb = ['ttcc', 'ttcj', 'tt2c','ttLF']
tt_components_nodps = ['ttbb', 'ttbj', 'tt2b', 'ttcc', 'ttcj',  'tt2c', 'ttLF']
tt_components_nodpsnoLF = ['ttbb', 'ttbj', 'tt2b', 'ttcc', 'ttcj', 'tt2c']
ttH_modes = ['ttHbb', 'ttHcc']
all_procs = bkgs + signal


cb = ch.CombineHarvester()
#cb.SetFlag("filters-use-regex", True)
cb.SetVerbosity(1)

datacard_dict = {"Vcb_catWcb_SR" : {
                "distribution" : "score_tt_Wcb",
                },
                "Vcb_catBB_CR" : {
                "distribution" : "fscore_ttbb",
                },
                "Vcb_catBJ_CR" : {
                "distribution" : "fscore_ttbj",
                },
                "Vcb_cat2B_CR" : {
                "distribution" : "fscore_tt2b",
                },
                "Vcb_catCC_CR" : {
                "distribution" : "fscore_ttcc",
                },
                "Vcb_catCJ_CR" : {
                "distribution" : "fscore_ttcj",
                },
                "Vcb_cat2C_CR" : {
                "distribution" : "fscore_tt2c",
                },
                "Vcb_catLF_CR" : {
                "distribution" : "fscore_ttLF",
                },
}


catNames = [(idx, cat) for idx, cat in enumerate(datacard_dict.keys())]
outputCardName = outdir+ '/Vcb_%s_%s.txt' % (channel, year)
#print (catNames)
cb.AddObservations(['*'], ['Vcb'], [year], [channel], catNames)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], bkgs, catNames, False)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], signal, catNames, True)
bins = cb.bin_set()
#print(bins)

# MC stats yes or no 
if args.doAutoMCStats:
    cb.SetAutoMCStats(cb, 0)
else:
    cb.SetAutoMCStats(cb, -1)

###############################
# Normalization uncertainties #
###############################

# PDF/Scale uncertainties on xsec
if year == '2024':
    cb.cp().AddSyst(cb, 'CMS_lumi_13p6TeV_2024', 'lnN', ch.SystMap()(1.016)),
    cb.cp().process(['singletop']).AddSyst(cb, 'QCDscale_singletop', 'lnN', ch.SystMap()((1.031, 1 - 0.021)))

    cb.cp().process(tt_components).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.024, 1 - 0.035)))
    cb.cp().process(tt_components).AddSyst(cb, 'BFWqq', 'lnN', ch.SystMap()((1.003)))
    cb.cp().process(tt_components).AddSyst(cb, 'BFWlnu', 'lnN', ch.SystMap()((1.002)))
    cb.cp().process(signal).AddSyst(cb, 'effi', 'lnN', ch.SystMap()((1.002)))
    cb.cp().process(['ttW']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.255, 1 - 0.164)))
    cb.cp().process(['ttZ']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093)))
    cb.cp().process(ttH_modes).AddSyst(cb, 'QCDscale_ttH', 'lnN', ch.SystMap()((1.058, 1 - 0.092)))
    cb.cp().process(signal).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093))) # Fix this number
    cb.cp().process(['w-fxfx']).AddSyst(cb, 'QCDscale_V', 'lnN', ch.SystMap()(1.038))
    cb.cp().process(ttH_modes).AddSyst(cb, 'pdf_Higgs_ttH', 'lnN', ch.SystMap()(1.036))
    cb.cp().process(['w-fxfx']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()((1.008, 1 - 0.004)))
    cb.cp().process(['singletop']).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028))
    cb.cp().process(tt_components).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.042))
    cb.cp().process(['ttW']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()(1.036))
    cb.cp().process(['ttZ']).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.035))
    cb.cp().process(signal).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028)) # Fix this number

    #cb.cp().AddSyst(cb, 'CMS_trigEff%s', 'lnN', ch.SystMap()(1.015)),


#############################
#      Rate parameters      #
#############################
fractions = {
    'ttbb': 0.0039195607,
    'ttbj': 0.018511502,
    'ttcc': 0.0088098647,
    'ttcj': 0.067400737,
    'ttLF': 1-(0.0039195607+0.018511502+0.0088098647+0.067400737)
    }

f_ttbb = fractions['ttbb']
f_ttbj = fractions['ttbj']
f_ttcc = fractions['ttcc']
f_ttcj = fractions['ttcj']
f_ttLF = fractions['ttLF']

for proc in tt_components_nodps:
    cb.cp().process([proc]).AddSyst(cb, f"xsec_{proc}", 'rateParam', ch.SystMap()(1.0))
#cb.cp().bin(["Vcb_catWcb_SR"]).process([signal]).AddSyst(cb, "Vcb2", 'rateParam', ch.SystMap()(0.0016))




#############################
#    Shape uncertainties    #
#############################

# Input files to extract shapes from
inputfiles = {bin: "" for bin in bins}
print(f"INPUTDIR: {inputdir}")
for dp, dn, filenames in os.walk(inputdir): # Careful: this will look into all subdirectories, make sure there are no other undesired root file is around

    for f in filenames:
        if f.endswith(".root"):
            bin = f.replace(".root", "")
            if bin in bins:
                fullpath = os.path.join(dp, f)
                inputfiles[bin] = fullpath

print(f"Input files {inputfiles}")

# Output shapes file (will collect all the histograms with shape variations)
outputShapesName = outputCardName.replace(".txt", "_shapes.root")
print("Output file name: " + outputShapesName)

shapeSysts = {
    'CMS_pileup_%s' % year: all_procs,
    #'CMS_flavTag_PS_isr_ttbar_%s' % year: all_procs,
    #'CMS_flavTag_PS_fsr_ttbar_%s' % year: all_procs,
    #'CMS_flavTag_PS_isr_wjets_%s' % year: all_procs,
    #'CMS_flavTag_PS_fsr_wjets_%s' % year: all_procs,
    #'CMS_flavTag_xsec_wjets_c_%s' % year: all_procs,
    #'CMS_flavTag_xsec_wjets_b_%s' % year: all_procs,
    #'CMS_flavTag_JER%s' % year: all_procs,
    #'CMS_flavTag_JES%s' % year: all_procs,
    #'CMS_flavTag_PU_%s' % year: all_procs,
    #'CMS_flavTag_LHE_muF_ttbar_%s' % year: all_procs,
    #'CMS_flavTag_LHE_muR_ttbar_%s' % year: all_procs,
    #'CMS_flavTag_LHE_muF_wjets_%s' % year: all_procs,
    #'CMS_flavTag_LHE_muR_wjets_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_C0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_C1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_C2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_C3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_C4_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_B0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_B1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_B2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_B3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavB_B4_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_C0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_C1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_C2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_C3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_C4_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_B0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_B1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_B2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_B3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavC_B4_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_C0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_C1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_C2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_C3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_C4_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_B0_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_B1_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_B2_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_B3_%s' % year: all_procs,
    #'CMS_flavTag_Stat_flavL_B4_%s' % year: all_procs,
    'CMS_trigEff%s' % year: all_procs,
    'CMS_muEff%s' % year: all_procs,
    'CMS_elEff%s' % year: all_procs,
    #'CMS_topHdampWeight%s' % year: tt_components_nobb,
}

shapeSysts = {}

for syst in shapeSysts:
    print(f"Adding systematic: {syst} for processes: {shapeSysts[syst]}")
    cb.cp().process(shapeSysts[syst]).AddSyst(cb, syst, 'shape', ch.SystMap()(1.0))
            


for bin in bins:
    print(f"Extracting shapes for bin {bin} from file {inputfiles[bin]}")
    cb.cp().bin([bin]).ExtractShapes(inputfiles[bin], "$PROCESS", "$PROCESS_$SYSTEMATIC")



cb.WriteDatacard(outputCardName, outputShapesName)

#Fix negative bins in the shape file. Negative bin contents are set to zero. Uncertainties larger than the bin content are set to the bin content.
fixNegativeBins(outputShapesName, False)

# Now produce a new datacard with the negative bins fixed
cb_fixed = ch.CombineHarvester()
cb_fixed.ParseDatacard(outputCardName)


systematics_nuisances = sorted(
    s for s in cb_fixed.syst_name_set()
    if not s.startswith('rate_')
)
if len(systematics_nuisances) > 0:
    cb_fixed.AddDatacardLineAtEnd('systematics group = ' + ' '.join(systematics_nuisances))

cb_fixed.WriteDatacard(outputCardName, outputShapesName)

# Create workspace with specific model and POI definitions
print ("Test datacards and create workspace for " + year + "!")
# Note that 0.00085 is the ratio of Br(W->cb)/Br(W->qq' - cb) using the PDG values. BR(W->cb) = 0.00085 and BR(W->qq') = 0.6741
workspace_name = outputCardName.replace(".txt", ".root")
print("Workspace name: " + workspace_name)
workspace_name = workspace_name.replace("/Vcb","/workspace_Vcb")
print("Workspace name: " + workspace_name)


if args.optimizeWSforFits:
    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
    " -m 125.38 -v 0" + \
    " --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
    " --optimize-simpdf-constraints=cms --channel-masks"
else:
    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
    " -m 125.38 -v 0 --channel-masks"

#command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
#    " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel" + \
#    " --PO verbose --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
#    " --optimize-simpdf-constraints=cms --channel-masks" + \
#    " --PO 'map=.*/tt-vcb:rate_ttWcb=expr;;rate_ttWcb(\"@0*@0\",Vcb[1,-1.,3.])'"+ \
#    " --PO 'map=.*/tt2b:xsec_tt2b[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttbb:xsec_ttbb[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttbj:xsec_ttbj[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttcc:xsec_ttcc[1,-1.,2.]'" + \
#    " --PO 'map=.*/tt2c:xsec_tt2c[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttcj:xsec_ttcj[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttLF:xsec_ttLF[1,-1.,2.]'"
    
#if args.doValidation:
#    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
#        " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel" + \
#        " --PO verbose --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
#        " --optimize-simpdf-constraints=cms --channel-masks" + \
#        " --PO 'map=.*/tt2b:xsec_tt2b[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttbb:xsec_ttbb[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttbj:xsec_ttbj[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttcc:xsec_ttcc[1,-1.,2.]'" + \
#        " --PO 'map=.*/tt2c:xsec_tt2c[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttcj:xsec_ttcj[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttLF:xsec_ttLF[1,-1.,2.]'"+ \
#        " --PO 'map=.*/tt-vcb:xsec_ttWcb[1,-1.,2.]'"   


#command = "text2workspace.py " + outputCardName + " -o " + workspace_name + " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose --channel-masks --PO 'map=.*/ttbb:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttbj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcc:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttLF:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttWcb:rate_ttWcb=expr;;rate_ttWcb(\"@0*@1*@1*1./(0.00085*(1.-@1*@1)+1.)\",rate_tt,rate_ratio[1,-1.,2.])'"


print(command)
subprocess.call(command, shell=True)