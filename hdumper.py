import ROOT
import argparse
import glob
import csv
import os
from colorama import Fore, Style 
import numpy as np
import multiprocessing as mp
from functools import partial

ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)
ROOT.TTreeCache.SetLearnEntries(200)
ROOT.gEnv.SetValue("TFile.AsyncPrefetching", 2)
ROOT.TH1.SetDefaultSumw2(True)

def add_overflow_underflow(hist):
    """
    Add underflow (bin 0) to first bin and overflow (bin N+1) to last bin.
    
    Parameters:
    - hist: ROOT.TH1 histogram
    """
    nbins = hist.GetNbinsX()
    
    # Add underflow to first bin
    underflow = hist.GetBinContent(0)
    underflow_err = hist.GetBinError(0)
    first_bin = hist.GetBinContent(1)
    first_bin_err = hist.GetBinError(1)
    
    hist.SetBinContent(1, first_bin + underflow)
    hist.SetBinError(1, np.sqrt(first_bin_err**2 + underflow_err**2))
    hist.SetBinContent(0, 0)
    hist.SetBinError(0, 0)
    
    # Add overflow to last bin
    overflow = hist.GetBinContent(nbins + 1)
    overflow_err = hist.GetBinError(nbins + 1)
    last_bin = hist.GetBinContent(nbins)
    last_bin_err = hist.GetBinError(nbins)
    
    hist.SetBinContent(nbins, last_bin + overflow)
    hist.SetBinError(nbins, np.sqrt(last_bin_err**2 + overflow_err**2))
    hist.SetBinContent(nbins + 1, 0)
    hist.SetBinError(nbins + 1, 0)
    
    return hist

def process_tree(infile, outfile, tree_name, hist_configs, year, selections, eventClassification, use5FS, count_events):
    """
    Processes a TTree, converts it to multiple TH1Ds for specified branches, and saves them to a ROOT file.

    Parameters:
    - input_files: List of input ROOT files.
    - output_files: List of output ROOT files.
    - tree_names: List of TTree names corresponding to input files.
    - hist_configs: List of dictionaries with keys 'branch', 'nbins', 'xmin', 'xmax'.
    - year: Year of data taking.
    - selections: String containing common event preselection.
    - eventClassification: Boolean indicating whether to apply event classification.
    - use5FS: Boolean indicating whether to use 5-flavor scheme MC for ttbb and ttbj processes.
    - count_events: Decide whether to count events for each selection (probably slows things down a bit).
    """
    print("")

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
    tree.SetCacheSize(100000000)  # 100MB cache
    tree.AddBranchToCache("*", True)

    # Create RDataFrame from TTree
    df = ROOT.RDataFrame(tree)

    # Apply base selection everywhere (and early, to speed things up)
    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0" # Remove from the electron channel the events that fired the muon trigger. Could choose to do vice versa as well.
    df = df.Filter(base_filter)

    if eventClassification:
        print(f"{Fore.YELLOW}Running in event classification mode. Will define a series of fractional scores.{Style.RESET_ALL}")
        # Define the fractional scores
        df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
            .Define("fscore_ttbb", "score_ttbb / denominator") \
            .Define("fscore_tt2b", "score_tt2b / denominator") \
            .Define("fscore_ttbj", "score_ttbj / denominator") \
            .Define("fscore_ttcc", "score_ttcc / denominator") \
            .Define("fscore_tt2c", "score_tt2c / denominator") \
            .Define("fscore_ttcj", "score_ttcj / denominator") \
            .Define("fscore_ttLF", "score_ttLF / denominator")
    else:
        df = df.Define("ak4_1_pt", "ak4_pt.size() > 0 ? ak4_pt[0] : 0") \
            .Define("ak4_1_phi",   "ak4_phi.size() > 0 ? ak4_phi[0] : 0") \
            .Define("ak4_1_eta",   "ak4_eta.size() > 0 ? ak4_eta[0] : 0") \
            .Define("ak4_2_pt",    "ak4_pt.size() > 1 ? ak4_pt[1] : 0") \
            .Define("ak4_2_phi",   "ak4_phi.size() > 1 ? ak4_phi[1] : 0") \
            .Define("ak4_2_eta",   "ak4_eta.size() > 1 ? ak4_eta[1] : 0") \
            .Define("ak4_3_pt",    "ak4_pt.size() > 2 ? ak4_pt[2] : 0") \
            .Define("ak4_3_phi",   "ak4_phi.size() > 2 ? ak4_phi[2] : 0") \
            .Define("ak4_3_eta",   "ak4_eta.size() > 2 ? ak4_eta[2] : 0") \
            .Define("ak4_4_pt",    "ak4_pt.size() > 3 ? ak4_pt[3] : 0") \
            .Define("ak4_4_phi",   "ak4_phi.size() > 3 ? ak4_phi[3] : 0") \
            .Define("ak4_4_eta",   "ak4_eta.size() > 3 ? ak4_eta[3] : 0")

    tt_file_names = ["ttbb-4f", "ttbb-dps", "ttbar-powheg"]
    tt4f_strings = ["ttbb", "ttbj", "tt2b"]
    tt_strings   = ["ttcc", "ttcj", "tt2c", "ttLF"]

    # Assign event weight based on data taking year and process type
    weight = assign_event_weight(year, infile)

    # If weight is a complex expression, define it as a new column
    weight_column = "weight_column"
    if not "data" in infile and not "Data" in infile: 
        print(f"Event weight: {weight}")
        df = df.Define(weight_column, weight)
    else: 
        df = df.Define(weight_column, "1") # Set collision data weight to 1

    # Initialize counters for events
    local_total_MC_events = 0
    local_events_in_category = {key: 0 for key in selections.keys() if not key == "base"}

    histograms = {}
    # Process each selection-output combinations
    for selection_name in selections:

        # Apply base selection to every sample; apply the ttbar-specific selection to the right 4F, dps, and 5F powheg samples
        if not "base" in selection_name and not any(x in infile for x in tt_file_names): 
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if use5FS: # "ttbb", "ttbj" -> both powheg and dps samples; "ttcc", "ttcj", "ttLF" --> only powheg
            if any(x in selection_name for x in tt4f_strings) and not ("powheg" in infile or "dps" in infile):
                continue
            if any(x in selection_name for x in tt_strings) and not "powheg" in infile: 
                continue
        else:
            if any(x in selection_name for x in tt4f_strings) and not "bb" in infile:
                continue
            if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
                continue


        if not "base" in selection_name:
            print(f"Applying additional selection for {infile}: {Fore.RED}{selection_name}{Style.RESET_ALL}")
            ttbar_event_selection = f"{selections[selection_name]}"
            df_selected = df.Filter(ttbar_event_selection)
            if count_events:
                print(f"Events passing additional ttbar selection: {df_selected.Count().GetValue()}")
        else:
            df_selected = df

        if not "Data" in infile and not "data" in infile and not "base" in selection_name:
            n_events = df_selected.Sum(weight_column).GetValue()
            local_total_MC_events += n_events
            local_events_in_category[selection_name] += n_events

        print(f"Applying selection: {Fore.GREEN}{selection_name}{Style.RESET_ALL}")

        # Define event classification for the dedicated mode
        if eventClassification:
            from configs.weights_and_constants import adhoc_selection, adhoc_binning
            adhoc_selection = adhoc_selection.copy()
            adhoc_binning = adhoc_binning.copy()

        # Create histograms for each branch
        final_df = dict()
        for hist_config in hist_configs:
            branch_name = hist_config['branch']
            nbins = int(hist_config['nbins'])
            xmin = float(hist_config['xmin'])
            xmax = float(hist_config['xmax'])
            print(f"Creating histogram for branch: {branch_name}")
                
            final_df[branch_name] = df_selected.Filter(adhoc_selection[branch_name]) if eventClassification else df_selected

            hist_key = (branch_name, selection_name)
            # Create histogram
            if eventClassification:
                #n_bins = 20 # Make many bins for these histograms. We will adjust them later.
                histograms[hist_key] = final_df[branch_name].Histo1D((f"h_{branch_name}", f"Histogram of {branch_name}", len(adhoc_binning[branch_name])-1, adhoc_binning[branch_name]), branch_name, weight_column)
                #histograms[hist_key] = final_df[branch_name].Histo1D((f"h_{branch_name}", f"Histogram of {branch_name}", nbins, xmin, xmax), branch_name, weight_column)
            else:
                histograms[hist_key] = final_df[branch_name].Histo1D((f"h_{branch_name}", f"Histogram of {branch_name}", nbins, xmin, xmax), branch_name, weight_column)



    # Materialising histograms
    print(f"Materializing {len(histograms)} histograms...")
    materialized_hists = {}
    for key, hist_lazy in histograms.items():
        materialized_hists[key] = hist_lazy.GetPtr() 
        materialized_hists[key] = add_overflow_underflow(materialized_hists[key]) 

    output_file_handles = {}
    for key, hist in materialized_hists.items():
        branch_name, selection_name = key
        tt_outfile_name = outfile.replace('.root','_'+selection_name+'.root')
        output_file = tt_outfile_name if not "base" in selection_name else outfile

        if output_file not in output_file_handles:
            output_file_handles[output_file] = ROOT.TFile(output_file, "RECREATE")

        output_file_handles[output_file].cd()
        hist.Write()
    
    # Close all files
    for fOut in output_file_handles.values():
        fOut.Close()

    input_file.Close()
    print(f"{Fore.GREEN}Completed processing {infile}{Style.RESET_ALL}")

    return (local_total_MC_events, local_events_in_category)


def process_trees_parallel(input_files, output_files, tree_name, hist_configs, year, selections, eventClassification, use5FS, count_events):
    """
    Basically a wrapper of process_tree to process multiple TTrees in parallel.
    """

    process_func = partial(
        process_tree,
        tree_name=tree_name,
        hist_configs=hist_configs,
        year=year,
        selections=selections,
        eventClassification=eventClassification,
        use5FS=use5FS,
        count_events=count_events
    )

    with mp.Pool(processes=min(len(input_files), mp.cpu_count())) as pool:
        results = pool.starmap(process_func, zip(input_files, output_files))

    # Aggregate results from all processes
    total_MC_events = 0
    events_in_category = {key: 0 for key in selections.keys() if not key == "base"}
    
    for local_total, local_category in results:
        total_MC_events += local_total
        for category, count in local_category.items():
            events_in_category[category] += count
    
    return (total_MC_events, events_in_category)

def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be plotted. 
    Fill in a list of dictionaries containing branch (i.e., variable name), nbins, xmin, and xmax information.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode = 'r') as f:
        csv_reader = csv.reader(f) 
        dict_list = [
            {'branch': line[0], 'nbins': line[1], 'xmin': line[2], 'xmax': line[3]}
            for line in csv_reader if not line[0] == 'Variable'
        ]
    # Note: the csv file must NOT contain empty lines.

    return dict_list

def assign_event_weight(year, infile):
    """
    Define the MC event weight according to the year. Collision data should be handled separately.

    Parameters:
    - year: Data taking year.
    - infile: Input file.
    """
    weight = "1"
    if year == 2018 or year == 2024:
        weight = "lumiwgt*genWeight*xsecWeight*l1PreFiringWeight*puWeight*muEffWeight*elEffWeight*flavTagWeight*(((abs(lep1_pdgId)==11 && passTrigEl && ((year!=2018) || (year==2018 && !(lep1_phi>-1.57 && lep1_phi<-0.87 && lep1_eta<-1.3)))) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
        #weight = "0.93*(!jetVetoMapEventVeto)*lumiwgt*genWeight*xsecWeight*l1PreFiringWeight*puWeight*muEffWeight*elEffWeight*flavTagWeight*(((abs(lep1_pdgId)==11 && passTrigEl && ((year!=2018) || (year==2018 && !(lep1_phi>-1.57 && lep1_phi<-0.87 && lep1_eta<-1.3)))) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
        #weight = "2.013*0.93*(!jetVetoMapEventVeto)*lumiwgt*genWeight*xsecWeight*l1PreFiringWeight*puWeight*muEffWeight*elEffWeight*flavTagWeight*(((abs(lep1_pdgId)==11 && passTrigEl && ((year!=2018) || (year==2018 && !(lep1_phi>-1.57 && lep1_phi<-0.87 && lep1_eta<-1.3)))) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    if "ttbar" in infile:
        weight = f"{weight}*topptWeight*renormWeight_topPt_nom"
    if "4f" in infile:
        weight = f"{weight}*topptWeight*renormWeight_topPt_nom"#*0.7559" # 5FS / 4FS for tt+B component
    
    return weight

def prepare_output(output_dir, input_files):
    """
    Prepare the output file names based on the input file names.

    Parameters:
    - output_dir: Output directory for the new ROOT files.
    - input_files: List of input ROOT files.
    """
    os.makedirs(output_dir, exist_ok=True)
    return [
        f"{output_dir}h_{input_file.split('/')[-1].replace('_tree.root','.root')}"
        for input_file in input_files
    ]

def merge_files(directory, input_files, output_file):
    """
    Merges multiple ROOT files into a single ROOT file.

    Parameters:
    - directory: Directory where the ROOT files are located.
    - input_files: List of input ROOT files.
    - output_file: Output ROOT file.
    """
    if not all([os.path.exists(directory+'/'+infile) for infile in input_files]):
        print(f"Input files {input_files} not found in directory: {directory}")
        return
    
    hadd_command = f"hadd -f {directory}/{output_file} {' '.join([directory+'/'+infile for infile in input_files])}"
    os.system(hadd_command)
    rm_command = f"rm {' '.join([directory+'/'+infile for infile in input_files])}"
    os.system(rm_command)


    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms.")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--nbins", type=int, required=False, help="Number of bins for the histograms.")
    parser.add_argument("--xmin", type=float, required=False, help="Minimum value for the histograms.")
    parser.add_argument("--xmax", type=float, required=False, help="Maximum value for the histograms.")
    parser.add_argument("--input_csv", type=str, required=True, help="The csv file to read variables and ranges from.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")
    parser.add_argument("--add_selection", type=str, required=False, help="Additional selection to apply to all processes.")
    parser.add_argument("--count_events", nargs="?", const=1, type=bool, default=False, required=False, help="Count events for each selection.")
    parser.add_argument("--eventClassification", nargs="?", const=1, type=bool, default=False, required=False, help="Apply event classification selection.")
    parser.add_argument("--use5FS", nargs="?", const=1, type=bool, default=False, required=False, help="Use 5-flavor scheme.")

    args = parser.parse_args()

    # Get input files from the input_dirs list
    input_files = []
    for input_dir in args.input_dirs:
        input_files.extend(glob.glob(f"{input_dir}*.root"))
    input_files = sorted(set(input_files))

    # Prepare list of output files based on the name of the input files
    output_files = prepare_output(args.output_dir, input_files)

    # Prepare histogram configurations for each branch
    hist_configs = read_csv(args.input_csv)

    selections = {"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1", #"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1 && n_ctagT>=1"
                 "ttbb" : "genEventClassifier==9",
                 "ttbj" : "genEventClassifier==7",
                 "tt2b" : "genEventClassifier==8",
                 "ttcc" : "genEventClassifier==6",
                 "ttcj" : "genEventClassifier==4",
                 "tt2c" : "genEventClassifier==5",
                 "ttLF" : "tt_category==0"
    }

    # Apply trigger selection to separate channels if requested
    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    use5FS = False
    if args.use5FS:
        use5FS = True
        print(f"{Fore.GREEN}Using 5-flavor scheme for ttbb, tt2b, and ttbj processes.{Style.RESET_ALL}")

    # Apply additional selections if specified
    if args.add_selection:
        for key in selections.keys():
            selections[key] += f" && ({args.add_selection})"

    print(f"{Fore.YELLOW}Final selections to be applied:{Style.RESET_ALL}")
    for key, value in selections.items():
        print(f"{Fore.YELLOW} - {key}: {value}{Style.RESET_ALL}")

    # Process the trees and get event counts
    total_MC_events, events_in_category = process_trees_parallel(input_files, output_files, args.tree_name, hist_configs, args.year, selections, args.eventClassification, use5FS, args.count_events)

    # Make sure the previous step is completed before merging files
    ROOT.gSystem.Exec("sync")

    # Merge some of the output files

    # We do not have ttV samples for 2024 yet
    #ttV_list = ["h_ttW.root", "h_ttZ.root"]
    #merge_files(args.output_dir, ttV_list, "h_ttV.root")

    # We do not have ttH samples for 2024 yet
    ttH_list = ["h_ttHbb.root", "h_ttHcc.root", "h_ttZ.root", "h_ttW.root", "h_diboson.root", "h_singletop.root", "h_wjets.root"]
    merge_files(args.output_dir, ttH_list, "h_others.root")

    merge_files(args.output_dir, ["h_ttbb-4f_ttbb.root"], "h_ttbb.root")
    merge_files(args.output_dir, ["h_ttbb-4f_tt2b.root"], "h_tt2b.root")
    merge_files(args.output_dir, ["h_ttbb-4f_ttbj.root"], "h_ttbj.root")

    #merge_files(args.output_dir, ["h_ttbar-vcb.root"], "h_tt-vcb.root")

    # We do not have dps samples for 2024 yet
    #if use5FS:
    #    ttbb_list = ["h_ttbar-powheg_ttbb.root", "h_ttbb-dps_ttbb.root"]
    #    merge_files(args.output_dir, ttbb_list, "h_ttbb-withDPS.root")
    #    ttbj_list = ["h_ttbar-powheg_ttbj.root", "h_ttbb-dps_ttbj.root"]
    #    merge_files(args.output_dir, ttbj_list, "h_ttbj-withDPS.root")
    #else:
    #    ttbb_list = ["h_ttbb-4f_ttbb.root", "h_ttbb-dps_ttbb.root"]
    #    merge_files(args.output_dir, ttbb_list, "h_ttbb-withDPS.root")
    #    ttbj_list = ["h_ttbb-4f_ttbj.root", "h_ttbb-dps_ttbj.root"]
    #    merge_files(args.output_dir, ttbj_list, "h_ttbj-withDPS.root")

    # We do not have TWZ for 2024 yet
    #diboson_list = ["h_TWZ.root", "h_diboson.root"]
    #merge_files(args.output_dir, diboson_list, "h_diboson-tWZ.root")
    data_list = ["h_singlee.root", "h_singlemu.root"]
    merge_files(args.output_dir, data_list, "h_Data.root")

    if args.count_events:
        print(f"{Fore.YELLOW}Total MC events after preselection: {total_MC_events}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Event counts in each category:{Style.RESET_ALL}")
        for category, count in events_in_category.items():
            print(f"{Fore.YELLOW} - {category}: {count}{Style.RESET_ALL}")
            print(f"  --> Fraction: {count/total_MC_events:.4f}\n")