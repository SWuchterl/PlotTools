Plotting and fitting tools for the |Vcb| measurement. In the following, an example workflow.
Note that, for what concerns the Combine fitting (and datacard production) part, Combine and CombineHarvester are needed.
You can install them within a CMSSW_15_0_10 release. It works.
Concerning the CombineHarvester version to use, please read `Plot pre- and post-fit uncertainties on the fit templates` section.

# Create preselection plots

Create histograms:
```
python3 hdumper.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR 
python3 hdumper.py --input_dirs $INPUT_DIR/data/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR
```
The input csv file is a file containing the name of the branch(es) that we want to plot and the chosen binning. There are some example csv files under `/configs`.
One can also add extra selection strings via argparse, doing `--add_selection ...&&...`.
Then, for plotting:
```
python3 plotter.py --input_dir $INPUT_DIR --output_dir $OUTPUT_DIR --sig_norm $SIG_NORM --input_csv $CONFIG_FILE
```
Where the input_dir must be the output directory of the previous histogramming step. Consider to add the options `--blind` to blind the tt_Wcb score and the option `--log` to plot in log scale.
This two steps can be taken care of by the bash scripts:
```
run_hdumper.sh
run_plotter.sh
```
Check them out to modify/add options.


# Create plots of the fit templates

The workflow is essentially the same as the above. The list of plots to be made in that case is in
```
configs/hconfig_fscores.csv
```
There is an option `--eventClassification` that should be added to the hdumper. When this is done, the script will read the binning from 
```
configs/weights_and_constants.py
```
and will use the weights in the above class to assign events to either of the (fractional) score distributions.
To facilitate all this, an example hdumper command has been added to
```
run_hdumper_fscores.sh
```
The plotting follows (still using `plotter.py`). Another option, if you want to collect all the score plots into a single canvas, is to launch `plotUnrolled.py`, e.g. with the options specified in
```
run_plotUnrolled.sh
```


# Create purity plots

That is, plotting the purity and the difference in event numbers in the various scores depending on how such scores are defined (fractional or not, with weights or not, using 4FS or 5FS for ttbb, etc.).
This currently requires `hdumper.py` to run multiple times with different options. To simplify that, they are all summarized in
```
run_hdumper_purity.py
```
Therefore, it should be sufficient to run the above once (taking care of setting up the directory names first, of course). Then, for the plotting one can run the commands in
```
run_plotUnstacked.py
```
that runs one or more of the various funcions of the script `plotUnstacked.py`. Again, take care of modifying input/output directories.


# Create histograms for fitting (i.e., shapes)

The creation of the histograms to be used to create fit templates and shape variations is handled by the script `prepareHistosForCards.py`. Within that script, one can define the set
of systematic uncertainties that will create shape histograms. Given the format of the input rootfiles (namely the output of the NanoTTH ntuplizer) and that of the desired output rootfiles
(namely one file per template/score, containing the corresponding histograms for all the processes and their shape variations), it is better to run it with the `--nproc 1` option, which
avoids I/O parallelization. It makes the script slower, but ensures that all rootfiles are filled in properly. An example is provided in
```
run_prepareHistosForCards.sh
```

# Create datacards

The obvious step following the creation of templates and shape variations is the Combine datacard preparation. That is handled by `prepareDatacards.py`. The script uses CombineHarvester
to prepare the datacard and the workspace for fitting, adding lnN nuisances, rate parameters, shapes and all that is needed to fit.
Important note: an option called `--optimizeWSforFits` lets you select between creating a workspace optimized for actual fit results (and should therefore *really* be used for likelihood scans,
impacts, significance, etc.) and creating a workspace optimized for plotting e.g. uncertainties using the `PostFitShapesFromWorkspace` method of combineTool. Unfortunately, the set of options that
we need to specify for serious fitting clashes with the more plotting-oriented scripts.
As usual, a bash script is available to simplify the datacard preparation:
```
run_prepareDatacards.sh
```


# Fit
There are several things that one might want to do with their freshly-produced datacard and workspace.

## Likelihood scan
The bash script
```
run_likelihoodScan.sh
```
collects the Combine commands that are necessary to obtain a likelihood scan of *r* (i.e., |Vcb|^2) with stat. only and with stat.+syst. uncertainties. The script is meant to be copied in the 
directory that contains the datacard and workspace to be run. It calls a `plot1Dscan.py` for plotting, which is located in the main directory.

## Impacts
The bash script
```
run_impacts.sh
```
does what you need. As for the above, it is meant to be copied over to the datacard and workspace directory before running.

## Plot pre- and post-fit uncertainties on the fit templates
This procedure makes use of the `PostFitShapesFromWorkspace` method of combineTool. This will produce a rootfile with 8 or 16 directories, depending on whether we choose to have only pre-fit
uncertainties or also post-fit ones. Each directory corresponds to a fit category (read template or score). Inside are histograms for each process and their pre- or post-fit uncertainties, including
for TotalProcs, which is what we need for plotting total MC uncertainties. It is extremely slow. A good option is to run it on Condor. A script is available to prepare condor jobs:
```
run_postFitShapesCondor.sh
```
and follow the instructions to submit jobs. In the script, one can specify the categories for which we want ucertainties to be computed. Each category will generate a job, to speed up the computation.
To speed it up further, one can use the option `--skip-proc-errs` to only have uncertainties computed for Total* and not for every single process. If you don't need post-fit uncertainties, remove the
`--postfit` flag.
**IMPORTANT** The fact of splitting the uncertainty computation per category requires a patch to `CombineHarvester/CombineTools`. You can get the patch diretly doing:
```
git clone git@github.com:RSalvatico/CombineHarvester.git -b VcbAnalysis
scram b -j8
```
This was built on top of the official CombineHarvester release tagged v3.0.0-pre1.
A script is then available to draw pre- or post-fit template plots using the total uncertainties: `plotUnrolledPostFit.py`.

## Run toys for significance estimation
Similarly to the above, a script exists to run toys (e.g., starting from a fit model where the parameters are fixed to the initial value). These toys can then be used for instance to estimate the significance
for the W->cb decay to be above the expected background.
The scrip is:
```
run_significanceToysCondor.sh
```
and then follow the submission instructions. The number of seeds chosen in the script defines the number of condor jobs that will be prepared. The number of toys per job is the product of the `-T` (toy number) and
`-i` (iterations) parameters.

