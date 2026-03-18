import ROOT
import argparse
import glob
import math
import csv
import os
import cmsstyle as CMS

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)

HIST_ORDER = [
    "h_score_tt_Wcb",
    "h_fscore_ttLF",
    "h_fscore_ttbb",
    "h_fscore_tt2b",
    "h_fscore_ttbj",
    "h_fscore_ttcc",
    "h_fscore_tt2c",
    "h_fscore_ttcj",
]

HIST_LABELS = {
    "h_score_tt_Wcb": "Wcb",
    "h_fscore_ttLF": "ttLF",
    "h_fscore_ttbb": "ttbb",
    "h_fscore_tt2b": "tt2b",
    "h_fscore_ttbj": "ttbj",
    "h_fscore_ttcc": "ttcc",
    "h_fscore_tt2c": "tt2c",
    "h_fscore_ttcj": "ttcj",
}


def _load_histograms(root_path, hist_names):
    root_file = ROOT.TFile.Open(root_path)
    if not root_file or root_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {root_path}")

    hists = {}
    for name in hist_names:
        hist = root_file.Get(name)
        if not hist or not isinstance(hist, ROOT.TH1):
            root_file.Close()
            raise ValueError(f"Histogram '{name}' not found in file '{root_path}'.")
        hist_clone = hist.Clone()
        hist_clone.SetDirectory(0)
        hists[name] = hist_clone

    root_file.Close()
    return hists


def _infer_process_name(root_path):
    base = os.path.splitext(os.path.basename(root_path))[0]
    if base.startswith("h_"):
        base = base[2:]
    if base.startswith("ttbar-powheg_"):
        base = base.split("_")[-1]
    return base


def _is_data(process_name):
    return "data" in process_name.lower()


def _is_signal(process_name):
    return "vcb" in process_name.lower()


def _total_bins(histograms):
    total = 0
    for name in HIST_ORDER:
        total += histograms[name].GetNbinsX()
    return total


def _block_edges(histograms):
    edges = [0]
    running = 0
    for name in HIST_ORDER:
        running += histograms[name].GetNbinsX()
        edges.append(running)
    return edges


def _block_centers(edges):
    centers = []
    for i in range(1, len(edges)):
        centers.append((edges[i - 1] + edges[i]) / 2.0)
    return centers


def _validate_binning(ref_histograms, test_histograms, root_path):
    for name in HIST_ORDER:
        ref_bins = ref_histograms[name].GetNbinsX()
        test_bins = test_histograms[name].GetNbinsX()
        if ref_bins != test_bins:
            raise ValueError(
                f"Histogram '{name}' has {test_bins} bins in '{root_path}', expected {ref_bins}."
            )


def _make_unrolled_hist(histograms, total_bins, name):
    unrolled = ROOT.TH1D(name, name, total_bins, 0, total_bins)
    unrolled.Sumw2()

    offset = 0
    for hist_name in HIST_ORDER:
        hist = histograms[hist_name]
        nbins = hist.GetNbinsX()
        for i in range(1, nbins + 1):
            out_bin = offset + i
            unrolled.SetBinContent(out_bin, hist.GetBinContent(i))
            unrolled.SetBinError(out_bin, hist.GetBinError(i))
        offset += nbins

    return unrolled


def plot_unrolled(input_files, output_dir, sig_norm=1.0, log=False, blind=False, show_blocks=True):
    stack = ROOT.THStack("stack", "Unrolled stack")
    phys_process = {}

    ref_hists = None
    total_bins = None
    block_edges = None
    data_hist = None
    sig_line = None
    block_guides = []

    for infile in input_files:
        print(f"Reading file: {infile}")

        file_hists = _load_histograms(infile, HIST_ORDER)
        if ref_hists is None:
            ref_hists = file_hists
            total_bins = _total_bins(ref_hists)
            block_edges = _block_edges(ref_hists)
        else:
            _validate_binning(ref_hists, file_hists, infile)

        process_name = _infer_process_name(infile)
        unrolled = _make_unrolled_hist(file_hists, total_bins, f"{process_name}_unrolled")

        is_data = _is_data(process_name)
        is_signal = _is_signal(process_name)

        if is_data:
            if blind:
                blind_bins = file_hists[HIST_ORDER[0]].GetNbinsX()
                for i in range(1, blind_bins + 1):
                    unrolled.SetBinContent(i, 0.0)
                    unrolled.SetBinError(i, 0.0)
            if data_hist is None:
                data_hist = unrolled.Clone("data_unrolled")
                data_hist.SetDirectory(0)
            else:
                data_hist.Add(unrolled)
            continue

        if is_signal:
            unrolled.Scale(sig_norm)
            sig_line = unrolled.Clone("sig_line")
            sig_line.SetDirectory(0)
            sig_line.SetLineStyle(ROOT.kDashed)
            sig_line.SetLineWidth(2)

        phys_process[process_name] = unrolled

    if total_bins is None:
        raise ValueError("No input histograms found.")

    x_low, x_high = 0, total_bins

    print(f"Saving stacked histograms as: {output_dir}unrolled.pdf/.png")
    canvas = CMS.cmsDiCanvas("canvas", x_low, x_high, 0, 1, 0.7, 1.3, "Scores", "Events", "Data/MC", square=CMS.kRectangular, extraSpace=0.01, iPos=11)
    canvas.cd(1)
    legend = CMS.cmsLeg(0.55, 0.5, 0.85, 0.87, textSize=0.04, columns=2)
    if data_hist is not None:
        legend.AddEntry(data_hist, "Data", "pe")
    if sig_line is not None:
        legend.AddEntry(sig_line, f"W#rightarrow cb #times {sig_norm:.0f}", "l")

    CMS.cmsDrawStack(stack, legend, phys_process)

    if sig_line is not None:
        CMS.cmsDraw(sig_line, "same", msize=0, lstyle = 2, lcolor=ROOT.kRed, lwidth=3)
    if data_hist is not None:
        CMS.cmsDraw(data_hist, "E1X0", mcolor=ROOT.kBlack)

    hist_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(1))
    stack_max = stack.GetHistogram().GetMaximum() if stack.GetHistogram() else 0
    data_max = data_hist.GetMaximum() if data_hist else 0
    y_max = max(stack_max, data_max) * 2.0 if max(stack_max, data_max) > 0 else 1.0
    hist_from_canvas.GetYaxis().SetRangeUser(0.01, y_max)
    hist_from_canvas.GetYaxis().SetMaxDigits(3)
    if log:
        ROOT.gPad.SetLogy()
        max_val = max(stack_max, data_max) if max(stack_max, data_max) > 0 else 1.0
        hist_from_canvas.GetYaxis().SetRangeUser(0.1, max_val * 100000)

    if show_blocks and block_edges is not None:
        y_top = hist_from_canvas.GetYaxis().GetXmax()
        y_text = y_top * 0.75
        centers = _block_centers(block_edges)
        for edge in block_edges[1:-1]:
            line = ROOT.TLine(edge, 0, edge, y_top)
            line.SetLineStyle(ROOT.kDashed)
            line.SetLineColor(ROOT.kBlue + 2)
            line.Draw("same")
            block_guides.append(line)

        latex = ROOT.TLatex()
        latex.SetTextAlign(22)
        latex.SetTextSize(0.03)
        for center, name in zip(centers, HIST_ORDER):
            label = HIST_LABELS.get(name, name.replace("h_", ""))
            latex.DrawLatex(center, y_text, label)
        block_guides.append(latex)

    if data_hist is not None:
        bkg_hist = stack.GetStack().Last()
        err_hist = bkg_hist.Clone()
        CMS.cmsDraw(err_hist, "e2same0", lcolor=335, lwidth=1, msize=0, fcolor=ROOT.kBlack, fstyle=3004)
        legend.AddEntry(err_hist, "Stat. Unc.", "f")

        canvas.cd(2)
        ratio = data_hist.Clone("ratio")
        ratio.Divide(bkg_hist)

        for i in range(1, ratio.GetNbinsX() + 1):
            if ratio.GetBinContent(i):
                ratio.SetBinError(i, math.sqrt(data_hist.GetBinContent(i)) / bkg_hist.GetBinContent(i))
            else:
                ratio.SetBinError(i, 10 ** (-99))

        yerr = ROOT.TGraphAsymmErrors()
        yerr.Divide(data_hist, bkg_hist, "pois")
        for i in range(0, yerr.GetN() + 1):
            yerr.SetPointY(i, 1)
        CMS.cmsDraw(yerr, "e2same0", lwidth=100, msize=0, fcolor=ROOT.kBlack, fstyle=3004)
        CMS.cmsDraw(ratio, "E1X0", mcolor=ROOT.kBlack)
        ref_line = ROOT.TLine(x_low, 1, x_high, 1)
        CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)
        ratio_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(2))
        ratio_from_canvas.GetYaxis().SetRangeUser(0.5, 1.5)

    plot_name = f"{output_dir}unrolled" if not log else f"{output_dir}/log/unrolled"
    CMS.SaveCanvas(canvas, f"{plot_name}.png", False)
    CMS.SaveCanvas(canvas, f"{plot_name}.pdf", False)
    print()


def _expand_inputs(input_files, input_pattern):
    if input_files:
        return input_files
    if input_pattern:
        return sorted(glob.glob(input_pattern))
    return []


def main():
    parser = argparse.ArgumentParser(description="Make unrolled plots from ROOT files.")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory, where ROOT files are located.")
    #parser.add_argument("--input-files", nargs="+", help="Input ROOT files (e.g. h_tt-vcb.root h_ttbb.root)")
    parser.add_argument("--input-pattern", help="Glob pattern for input ROOT files (e.g. 'h_*.root')")
    parser.add_argument("--output_dir", required=True, help="Output directory for plots")
    parser.add_argument("--sig-norm", type=float, default=1.0, help="Signal normalization factor")
    parser.add_argument("--log", action="store_true", help="Use log scale on Y axis")
    parser.add_argument("--blind", action="store_true", help="Blind data histogram")
    parser.add_argument("--no-blocks", action="store_true", help="Disable block separators/labels")
    args = parser.parse_args()

    # Set plotting details
    CMS.SetExtraText("Work in progress")
    CMS.SetLumi("110")
    #CMS.SetLumi("220")
    CMS.SetEnergy("13.6")
    
    # Get input files from the input_dir
    input_files = sorted(glob.glob(f"{args.input_dir}/*.root"))

    os.makedirs(args.output_dir, exist_ok=True)
    if args.log:
        os.makedirs(os.path.join(args.output_dir, "log"), exist_ok=True)

    plot_unrolled(
        input_files,
        args.output_dir,
        sig_norm=args.sig_norm,
        log=args.log,
        blind=args.blind,
        show_blocks=not args.no_blocks,
    )


if __name__ == "__main__":
    main()