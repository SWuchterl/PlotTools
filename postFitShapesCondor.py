import argparse
import os

def skip_proc_errs_value(enabled):
    return "1" if enabled else "0"


parser = argparse.ArgumentParser(description="Generate HTCondor submission for post-fit shapes extraction")
parser.add_argument("--input_dir", "-i", type=str, required=True, help="Working directory with combine outputs.")
parser.add_argument("--workspace", "-w", type=str, required=True, help="Input workspace file.")
parser.add_argument("--out-file", "-o", type=str, required=True, help="Base output ROOT file name.")
parser.add_argument("--cmssw-base", type=str, default=os.environ.get("CMSSW_BASE", ""), help="Path to local CMSSW release to initialize on Condor (defaults to $CMSSW_BASE).")
parser.add_argument("--categories", "-c",nargs="+", default=["Vcb_catWcb_SR","Vcb_catBB_CR","Vcb_catBJ_CR","Vcb_cat2B_CR","Vcb_catCC_CR","Vcb_catCJ_CR","Vcb_cat2C_CR","Vcb_catLF_CR"], help="Categories to process, one Condor job per category (e.g. Vcb_catBJ_CR Vcb_catWcb_SR).")
parser.add_argument("--skip-proc-errs", action="store_true", help="Pass --skip-proc-errs to PostFitShapesFromWorkspace.")
parser.add_argument("--postfit", action="store_true", help="Pass --postfit to PostFitShapesFromWorkspace.")


args = parser.parse_args()

if not args.cmssw_base:
    raise RuntimeError("CMSSW base not provided. Use --cmssw-base or run from an initialized CMSSW area.")

cmssw_base = os.path.abspath(args.cmssw_base)
cmssw_src = os.path.join(cmssw_base, "src")
if not os.path.isdir(cmssw_src):
    raise RuntimeError(f"Invalid CMSSW release: '{cmssw_base}'. Missing '{cmssw_src}'.")

input_dir = os.path.abspath(args.input_dir)
log_dir = os.path.join(input_dir, "log")
os.makedirs(log_dir, exist_ok=True)

run_script = os.path.join(input_dir, "run_postfit_shapes.sh")
submit_file = os.path.join(input_dir, "postfit_shapes.sub")
skip_proc_errs = skip_proc_errs_value(args.skip_proc_errs)
postfit = "1" if args.postfit else "0"

run_script_content = """#!/bin/bash
set -euo pipefail

category=\"$1\"

source /cvmfs/cms.cern.ch/cmsset_default.sh
cd \"{cmssw_src}\"
eval \"$(scramv1 runtime -sh)\"

if [[ ! -d \"$CMSSW_BASE/src/CombineHarvester\" ]]; then
    echo "ERROR: local CombineHarvester not found in $CMSSW_BASE/src/CombineHarvester"
    exit 2
fi
if [[ ! -d \"$CMSSW_BASE/src/HiggsAnalysis\" ]]; then
    echo "ERROR: local HiggsAnalysis not found in $CMSSW_BASE/src/HiggsAnalysis"
    exit 2
fi

cd \"{workdir}\"

combine -M MultiDimFit \"{workspace}\" \\
  --algo singles \\
  -m 125.38 \\
  --saveFitResult \\
  --saveWorkspace \\
  -t -1 \\
  --expectSignal 1 \\
  --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 \\
  --cminDefaultMinimizerStrategy 0 \\
  --X-rtd MINIMIZER_MaxCalls=999999999 \\
  --cminDefaultMinimizerTolerance 0.1 \\
  --cminPreScan \\
  --cminPreFit 1 \\
  --X-rtd FAST_VERTICAL_MORPH \\
  --robustFit 1 \\
  -n \"${{category}}\"

out_file=\"{out_base}\"
out_file=\"${{out_file%.root}}_${{category}}.root\"

PostFitShapesFromWorkspace \\
  --workspace higgsCombine\"${{category}}\".MultiDimFit.mH125.38.root \\
  --fitresult multidimfit\"${{category}}\".root:fit_mdf \\
  --postfit {postfit} \\
  --skip-proc-errs {skip_proc_errs} \\
  --selected-bins \"${{category}}\" \\
  --output \"${{out_file}}\"
""".format(
    cmssw_src=cmssw_src,
    workdir=input_dir,
    workspace=os.path.join(input_dir, args.workspace),
    out_base=args.out_file,
    skip_proc_errs=skip_proc_errs,
    postfit=postfit,
)

with open(run_script, "w") as f:
    f.write(run_script_content)
os.chmod(run_script, 0o755)

categories_lines = "\n".join(f"{cat}" for cat in args.categories)
submit_content = """universe = vanilla
requirements = (Arch == \"X86_64\") && ((OpSysAndVer =?= \"AlmaLinux9\") || (OpSysAndVer =?= \"CentOS7\"))
request_memory = 2000
request_disk = 10000000
executable = {executable}
arguments = $(category)
output = {log_dir}/$(category).out
error = {log_dir}/$(category).err
log = {log_dir}/$(category).log
use_x509userproxy = true
should_transfer_files = YES
initialdir = {initialdir}
WhenToTransferOutput  = ON_EXIT
want_graceful_removal = true
on_exit_remove        = (ExitBySignal == False) && (ExitCode == 0)
on_exit_hold          = ( (ExitBySignal == True) || (ExitCode != 0) )
on_exit_hold_reason   = strcat("Job held by ON_EXIT_HOLD due to ", ifThenElse((ExitBySignal == True), "exit by signal", strcat("exit code ",ExitCode)), ".")
periodic_release      = (NumJobStarts < 3) && ((CurrentTime - EnteredCurrentStatus) > 10*60)
transfer_output_files = ""

+MaxRuntime = 48*60*60
+AccountingGroup = "group_u_CMST3.all"

MY.WantOS = "el9"

queue category from (
{categories}
)
""".format(
    executable=run_script,
    log_dir=log_dir,
    initialdir=input_dir,
    categories=categories_lines,
)

with open(submit_file, "w") as f:
    f.write(submit_content)

print(f"Created executable script: {run_script}")
print(f"Created Condor submit file: {submit_file}")
print("Submit with:\n   condor_submit " + submit_file)