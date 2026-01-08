import ROOT
import argparse
import glob
import csv
import os
from colorama import Fore, Style
import multiprocessing as mp
from functools import partial

ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)
ROOT.TTreeCache.SetLearnEntries(100)
ROOT.gEnv.SetValue("TFile.AsyncPrefetching", 1)

def process_tree(infile, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning, systematics):
    """
    Processes a TTree, converts it to multiple TH1Ds for specified branches, and saves them to ROOT files.

    Parameters:
    - input_file: Input ROOT file.
    - output_files: List of output ROOT files.
    - tree_name: Name of the TTree to process.
    - year: Data taking year.
    - selections: Dictionary containing event selections.
    - adhoc_selection: Dictionary containing an ad-hoc event selection to fill the scores.
    - adhoc_binning: Dictionary containing ad-hoc binning for the scores.
    - systematics: Dictionary containing systematic variations.
    """

    print(f"{Fore.RED}Processing file: {infile}{Style.RESET_ALL}")

    # Open input file
    input_file = ROOT.TFile.Open(infile)
    if not input_file or input_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {infile}")

    # Access the TTree
    tree = input_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")
    
    # Optimize TTree reading
    tree.SetCacheSize(50000000)  # 50MB cache
    tree.AddBranchToCache("*", True)

    # Create RDataFrame from TTree
    df = ROOT.RDataFrame(tree)

    # Apply base selection everywhere (and early, to speed things up)
    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0" # Remove from the electron channel the events that fired the muon trigger. Could choose to do vice versa as well.
    df = df.Filter(base_filter)

    # Define the fractional scores
    df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
        .Define("fscore_ttbb", "score_ttbb / denominator") \
        .Define("fscore_tt2b", "score_tt2b / denominator") \
        .Define("fscore_ttbj", "score_ttbj / denominator") \
        .Define("fscore_ttcc", "score_ttcc / denominator") \
        .Define("fscore_tt2c", "score_tt2c / denominator") \
        .Define("fscore_ttcj", "score_ttcj / denominator") \
        .Define("fscore_ttLF", "score_ttLF / denominator")

    tt_file_names = ["ttbb-4f", "ttbar-powheg"]
    tt4f_strings = ["ttbb", "ttbj", "tt2b"]
    tt_strings   = ["ttcc", "ttcj", "tt2c", "ttLF"]


    histograms = {}
    # Process each selection-output combinations
    for selection_name in selections:

        # Apply the ttbar-specific selection to the right 4f and powheg samples
        if not "base" in selection_name and not any(x in infile for x in tt_file_names): 
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt4f_strings) and not "4f" in infile:
            continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue

        # Add event selection for ttbar samples
        print(f"Events after base selection: {df.Count().GetValue()}")
        if not "base" in selection_name:
            print(f"Applying additional selection for {infile}: {selection_name}")
            ttbar_event_selection = f"{selections[selection_name]}"
            df_selected = df.Filter(ttbar_event_selection)

            # Check the number of events after ttbar selection
            print(f"Events passing additional ttbar selection: {df_selected.Count().GetValue()}")
        else:
            df_selected = df


        # Assign event weight based on data taking year and process type
        for syst in systematics.keys():
            if syst == "None":
                weight = assign_event_weight(year, infile)
            else:
                weight = assign_event_weight(year, infile, systematics[syst])

            # If weight is a complex expression, define it as a new column
            weight_column = f"weight_{syst}"
            if "data" not in infile and "Data" not in infile:
                #print(f"Event weight: {Fore.GREEN}{weight}{Style.RESET_ALL}")
                df_selected = df_selected.Define(weight_column, weight)
            else: # Keep the weight == 1 for collision data
                df_selected = df_selected.Define(weight_column, "1")

            final_df = dict()
            for (score, adhoc_sel), outfile in zip(adhoc_selection.items(), output_files):


                hist_name = infile.split('/')[-1].replace('_tree.root','')
                if any(x in infile for x in tt_file_names):
                    hist_name = selection_name
                if "Data" in infile or "data" in infile:
                    hist_name = "data_obs"
                if not syst == "None":
                    hist_name = f"{hist_name}_{syst}"

                final_df[score] = df_selected.Filter(adhoc_sel)

                hist_key = (selection_name, outfile, hist_name, score)
                histograms[hist_key] = final_df[score].Histo1D(
                    (hist_name, f"Histogram of {score} for process {hist_name}", 
                     len(adhoc_binning[score])-1, adhoc_binning[score]), 
                    score, weight_column
                )

            if "Data" in infile: break # Do not continue with the systematic variations for collision data

    # Write all histograms to their respective output files
    print(f"Materializing {len(histograms)} histograms...")
    materialized_hists = {}
    for key, hist_lazy in histograms.items():
        materialized_hists[key] = hist_lazy.GetPtr()   

    output_file_handles = {}
    for key, hist in materialized_hists.items():
        selection_name, outfile, hist_name, score = key
        
        if outfile not in output_file_handles:
            output_file_handles[outfile] = ROOT.TFile(outfile, "UPDATE")
        
        output_file_handles[outfile].cd()
        hist.Write()
    
    # Chiudi tutti i file
    for f in output_file_handles.values():
        f.Close()
    
    input_file.Close()
    print(f"{Fore.GREEN}Completed processing {infile}{Style.RESET_ALL}")



def process_trees_parallel(input_files, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning, systematics):

    process_func = partial(
        process_tree, 
        output_files=output_files,
        tree_name=tree_name, 
        year=year,
        selections=selections,
        adhoc_selection=adhoc_selection,
        adhoc_binning=adhoc_binning,
        systematics=systematics
    )

    with mp.Pool(processes=min(len(input_files), mp.cpu_count())) as pool:
        pool.map(process_func, input_files)



def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be histogrammed. 
    Fill in a list of dictionaries containing branch (i.e., variable name), nbins, xmin, and xmax information.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode='r') as f:
        csv_reader = csv.reader(f) 
        dict_list = [
            {'branch': line[0], 'nbins': line[1], 'xmin': line[2], 'xmax': line[3]}
            for line in csv_reader if not line[0] == 'Variable'
        ]

    return dict_list


def prepare_output(output_dir, year, categories, prepend, append):
    """
    Prepare the output files that will contain the histograms used to create combine datacards.

    Parameters:
    - output_dir: Output directory for the new ROOT files.
    - categories: The name of the categories.
    - prepend: String to prepend to the file name.
    - append: String to append to the file name.
    """
    os.makedirs(output_dir + str(year), exist_ok=True)

    name_list = [prepend + cat for cat in categories]
    name_list = [name + append[1] if 'Wcb' in name else name + append[0] for name in name_list]

    return [
        f"{output_dir}{year}/{name}.root"
        for name in name_list
    ]



def assign_event_weight(year, infile, syst=""):
    """
    Define the MC event weight according to the year. Collision data should be handled separately.

    Parameters:
    - year: Data taking year.
    - infile: Input file.
    - syst: Systematic uncertainty string.
    """
    weight = "1"
    if year == 2024:
        weight = "lumiwgt*genWeight*xsecWeight*l1PreFiringWeight*puWeight*muEffWeight*elEffWeight*flavTagWeight*(((abs(lep1_pdgId)==11 && passTrigEl && ((year!=2018) || (year==2018 && !(lep1_phi>-1.57 && lep1_phi<-0.87 && lep1_eta<-1.3)))) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    if "ttbar" in infile:
        weight = f"{weight}*topptWeight"
    if "4f" in infile:
        weight = f"{weight}*topptWeight"#*0.7559" # 5FS / 4FS for tt+B component
    
    if not syst == "":
        weight = f"{weight}*{syst}"
    
    return weight


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms.")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")

    args = parser.parse_args()

    # Categories for combine datacards
    prepended_ = "Vcb_"
    categories = ["catWcb", "catBB", "cat2B", "catBJ", "catCC", "cat2C", "catCJ", "catLF"]
    appended_ = ["_CR", "_SR"]

    # Get input files from the input_dirs list
    input_files = []
    for input_dir in args.input_dirs:
        input_files += glob.glob(f"{input_dir}*.root")

    # Prepare list of output files based on the name of the input files
    output_files = prepare_output(args.output_dir, args.year, categories, prepended_, appended_)
    print(f"Output files: {output_files}")

    # Define event selections. Some are process-specific.
    selections = {"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1",
                 "ttbb" : "genEventClassifier==9",
                 "ttbj" : "genEventClassifier==7",
                 "tt2b" : "genEventClassifier==8",
                 "ttcc" : "genEventClassifier==6",
                 "ttcj" : "genEventClassifier==4",
                 "tt2c" : "genEventClassifier==5",
                 "ttLF" : "tt_category==0"
    }

    from configs.weights_and_constants import adhoc_selection, adhoc_binning
    adhoc_selection = adhoc_selection.copy()
    adhoc_binning = adhoc_binning.copy()
    
    # Apply trigger selection to separate channels if requested
    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    year = args.year
    # Define list of systematic variations to include
    systematics = {"None" : "", 
                   "CMS_pileup_%sUp" % year : "puWeightUp/puWeight", 
                   "CMS_pileup_%sDown" % year : "puWeightDown/puWeight",
                   "CMS_trigEff%sUp" % year : "trigEffWeightUp/trigEffWeight",
                   "CMS_trigEff%sDown" % year : "trigEffWeightDown/trigEffWeight",
                   "CMS_muEff%sUp" % year : "muEffWeight_UP/muEffWeight",
                   "CMS_muEff%sDown" % year : "muEffWeight_DOWN/muEffWeight",
                   "CMS_elEff%sUp" % year : "elEffWeight_UP/elEffWeight",
                   "CMS_elEff%sDown" % year : "elEffWeight_DOWN/elEffWeight",
                   #"CMS_topHdampWeight%sUp" % year : "topHdampWeightUp",
                   #"CMS_topHdampWeight%sDown" % year : "topHdampWeightDown"
                   #"CMS_flavTag_PS_isr_ttbar_%sUp" % year : "flavTagWeight_PSWeightISR_ttbar_UP/flavTagWeight",
                   #"CMS_flavTag_PS_isr_ttbar_%sDown" % year : "flavTagWeight_PSWeightISR_ttbar_DOWN/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_ttbar_%sUp" % year : "flavTagWeight_PSWeightFSR_ttbar_UP/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_ttbar_%sDown" % year : "flavTagWeight_PSWeightFSR_ttbar_DOWN/flavTagWeight",
                   #"CMS_flavTag_PS_isr_wjets_%sUp" % year : "flavTagWeight_PSWeightISR_wjets_UP/flavTagWeight",
                   #"CMS_flavTag_PS_isr_wjets_%sDown" % year : "flavTagWeight_PSWeightISR_wjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_wjets_%sUp" % year : "flavTagWeight_PSWeightFSR_wjets_UP/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_wjets_%sDown" % year : "flavTagWeight_PSWeightFSR_wjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_PS_isr_zjets_%sUp" % year : "flavTagWeight_PSWeightISR_zjets_UP/flavTagWeight",
                   #"CMS_flavTag_PS_isr_zjets_%sDown" % year : "flavTagWeight_PSWeightISR_zjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_zjets_%sUp" % year : "flavTagWeight_PSWeightFSR_zjets_UP/flavTagWeight",
                   #"CMS_flavTag_PS_fsr_zjets_%sDown" % year : "flavTagWeight_PSWeightFSR_zjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_xsec_wjets_c_%sUp" % year : "flavTagWeight_XSec_WJets_c_UP/flavTagWeight",
                   #"CMS_flavTag_xsec_wjets_c_%sDown" % year : "flavTagWeight_XSec_WJets_c_DOWN/flavTagWeight",
                   #"CMS_flavTag_xsec_wjets_b_%sUp" % year : "flavTagWeight_XSec_WJets_b_UP/flavTagWeight",
                   #"CMS_flavTag_xsec_wjets_b_%sDown" % year : "flavTagWeight_XSec_WJets_b_DOWN/flavTagWeight",
                   #"CMS_flavTag_xsec_zjets_c_%sUp" % year : "flavTagWeight_XSec_ZJets_c_UP/flavTagWeight",
                   #"CMS_flavTag_xsec_zjets_c_%sDown" % year : "flavTagWeight_XSec_ZJets_c_DOWN/flavTagWeight",
                   #"CMS_flavTag_xsec_zjets_b_%sUp" % year : "flavTagWeight_XSec_ZJets_b_UP/flavTagWeight",
                   #"CMS_flavTag_xsec_zjets_b_%sDown" % year : "flavTagWeight_XSec_ZJets_b_DOWN/flavTagWeight",
                   #"CMS_flavTag_JER%sUp" % year : "flavTagWeight_JER_UP/flavTagWeight",
                   #"CMS_flavTag_JER%sDown" % year : "flavTagWeight_JER_DOWN/flavTagWeight",
                   #"CMS_flavTag_JES%sUp" % year : "flavTagWeight_JES_UP/flavTagWeight",
                   #"CMS_flavTag_JES%sDown" % year : "flavTagWeight_JES_DOWN/flavTagWeight",
                   #"CMS_flavTag_PU_%sUp" % year : "flavTagWeight_PUWeight_UP/flavTagWeight",
                   #"CMS_flavTag_PU_%sDown" % year : "flavTagWeight_PUWeight_DOWN/flavTagWeight",
                   #"CMS_flavTag_stat_%sUp" % year : "flavTagWeight_Stat_UP/flavTagWeight",
                   #"CMS_flavTag_stat_%sDown" % year : "flavTagWeight_Stat_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_ttbar_%sUp" % year : "flavTagWeight_LHEScaleWeight_muF_ttbar_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_ttbar_%sDown" % year : "flavTagWeight_LHEScaleWeight_muF_ttbar_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_ttbar_%sUp" % year : "flavTagWeight_LHEScaleWeight_muR_ttbar_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_ttbar_%sDown" % year : "flavTagWeight_LHEScaleWeight_muR_ttbar_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_wjets_%sUp" % year : "flavTagWeight_LHEScaleWeight_muF_wjets_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_wjets_%sDown" % year : "flavTagWeight_LHEScaleWeight_muF_wjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_wjets_%sUp" % year : "flavTagWeight_LHEScaleWeight_muR_wjets_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_wjets_%sDown" % year : "flavTagWeight_LHEScaleWeight_muR_wjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_zjets_%sUp" % year : "flavTagWeight_LHEScaleWeight_muF_zjets_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muF_zjets_%sDown" % year : "flavTagWeight_LHEScaleWeight_muF_zjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_zjets_%sUp" % year : "flavTagWeight_LHEScaleWeight_muR_zjets_UP/flavTagWeight",
                   #"CMS_flavTag_LHE_muR_zjets_%sDown" % year : "flavTagWeight_LHEScaleWeight_muR_zjets_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C0_%sUp" % year : "flavTagWeight_Stat_flavB_C0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C0_%sDown" % year : "flavTagWeight_Stat_flavB_C0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C1_%sUp" % year : "flavTagWeight_Stat_flavB_C1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C1_%sDown" % year : "flavTagWeight_Stat_flavB_C1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C2_%sUp" % year : "flavTagWeight_Stat_flavB_C2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C2_%sDown" % year : "flavTagWeight_Stat_flavB_C2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C3_%sUp" % year : "flavTagWeight_Stat_flavB_C3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C3_%sDown" % year : "flavTagWeight_Stat_flavB_C3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C4_%sUp" % year : "flavTagWeight_Stat_flavB_C4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_C4_%sDown" % year : "flavTagWeight_Stat_flavB_C4_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B0_%sUp" % year : "flavTagWeight_Stat_flavB_B0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B0_%sDown" % year : "flavTagWeight_Stat_flavB_B0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B1_%sUp" % year : "flavTagWeight_Stat_flavB_B1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B1_%sDown" % year : "flavTagWeight_Stat_flavB_B1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B2_%sUp" % year : "flavTagWeight_Stat_flavB_B2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B2_%sDown" % year : "flavTagWeight_Stat_flavB_B2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B3_%sUp" % year : "flavTagWeight_Stat_flavB_B3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B3_%sDown" % year : "flavTagWeight_Stat_flavB_B3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B4_%sUp" % year : "flavTagWeight_Stat_flavB_B4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavB_B4_%sDown" % year : "flavTagWeight_Stat_flavB_B4_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C0_%sUp" % year : "flavTagWeight_Stat_flavC_C0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C0_%sDown" % year : "flavTagWeight_Stat_flavC_C0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C1_%sUp" % year : "flavTagWeight_Stat_flavC_C1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C1_%sDown" % year : "flavTagWeight_Stat_flavC_C1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C2_%sUp" % year : "flavTagWeight_Stat_flavC_C2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C2_%sDown" % year : "flavTagWeight_Stat_flavC_C2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C3_%sUp" % year : "flavTagWeight_Stat_flavC_C3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C3_%sDown" % year : "flavTagWeight_Stat_flavC_C3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C4_%sUp" % year : "flavTagWeight_Stat_flavC_C4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_C4_%sDown" % year : "flavTagWeight_Stat_flavC_C4_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B0_%sUp" % year : "flavTagWeight_Stat_flavC_B0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B0_%sDown" % year : "flavTagWeight_Stat_flavC_B0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B1_%sUp" % year : "flavTagWeight_Stat_flavC_B1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B1_%sDown" % year : "flavTagWeight_Stat_flavC_B1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B2_%sUp" % year : "flavTagWeight_Stat_flavC_B2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B2_%sDown" % year : "flavTagWeight_Stat_flavC_B2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B3_%sUp" % year : "flavTagWeight_Stat_flavC_B3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B3_%sDown" % year : "flavTagWeight_Stat_flavC_B3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B4_%sUp" % year : "flavTagWeight_Stat_flavC_B4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavC_B4_%sDown" % year : "flavTagWeight_Stat_flavC_B4_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C0_%sUp" % year : "flavTagWeight_Stat_flavL_C0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C0_%sDown" % year : "flavTagWeight_Stat_flavL_C0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C1_%sUp" % year : "flavTagWeight_Stat_flavL_C1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C1_%sDown" % year : "flavTagWeight_Stat_flavL_C1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C2_%sUp" % year : "flavTagWeight_Stat_flavL_C2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C2_%sDown" % year : "flavTagWeight_Stat_flavL_C2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C3_%sUp" % year : "flavTagWeight_Stat_flavL_C3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C3_%sDown" % year : "flavTagWeight_Stat_flavL_C3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C4_%sUp" % year : "flavTagWeight_Stat_flavL_C4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_C4_%sDown" % year : "flavTagWeight_Stat_flavL_C4_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B0_%sUp" % year : "flavTagWeight_Stat_flavL_B0_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B0_%sDown" % year : "flavTagWeight_Stat_flavL_B0_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B1_%sUp" % year : "flavTagWeight_Stat_flavL_B1_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B1_%sDown" % year : "flavTagWeight_Stat_flavL_B1_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B2_%sUp" % year : "flavTagWeight_Stat_flavL_B2_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B2_%sDown" % year : "flavTagWeight_Stat_flavL_B2_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B3_%sUp" % year : "flavTagWeight_Stat_flavL_B3_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B3_%sDown" % year : "flavTagWeight_Stat_flavL_B3_DOWN/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B4_%sUp" % year : "flavTagWeight_Stat_flavL_B4_UP/flavTagWeight",
                   #"CMS_flavTag_Stat_flavL_B4_%sDown" % year : "flavTagWeight_Stat_flavL_B4_DOWN/flavTagWeight",
               }

    process_trees_parallel(input_files, output_files, args.tree_name, args.year, selections, adhoc_selection, adhoc_binning, systematics)
