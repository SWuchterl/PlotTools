import argparse
import os

parser = argparse.ArgumentParser(description="Generate HTCondor submission for post-fit shapes extraction")
parser.add_argument("--input_dir", "-i", type=str, required=True, help="Working directory with combine outputs.")
parser.add_argument("--datacard", "-d", type=str, required=True, help="Input datacard file.")
parser.add_argument("--cmssw-base", type=str, default=os.environ.get("CMSSW_BASE", ""), help="Path to local CMSSW release to initialize on Condor (defaults to $CMSSW_BASE).")
parser.add_argument("--toys", "-T",type=str, required=True, help="Number of toys per job.")
parser.add_argument("--iter",type=str, required=True, help="Number of iterations per job.") #Toy number per job = T * iter
parser.add_argument("--seeds", "-s", type=str, default="-1", help="Random seeds to use for each job, comma-separated (e.g. 12345,23456,34567).")

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

run_script = os.path.join(input_dir, "run_significanceToys.sh")
submit_file = os.path.join(input_dir, "significanceToys.sub")

run_script_content = """#!/bin/bash
set -euo pipefail

seed=\"$1\"

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

combine -M HybridNew \"{workspace}\" \\
  --LHCmode LHC-significance \\
  -m 125.38 \\
  --saveToys \\
  --fullBToys \\
  --saveHybridResult \\
  --expectSignal 1 \\
  -T {toys} \\
  -i {iterations} \\
  -s \"${{seed}}\" \\
  --cminDefaultMinimizerStrategy 0 \\
  --cminDefaultMinimizerTolerance 0.1 \\
""".format(
    cmssw_src=cmssw_src,
    workdir=input_dir,
    workspace=os.path.join(input_dir, args.datacard),
    toys=args.toys,
    iterations=args.iter,
)

with open(run_script, "w") as f:
    f.write(run_script_content)
os.chmod(run_script, 0o755)

seeds_lines = "\n".join(f"{seed}" for seed in args.seeds.split(","))
submit_content = """universe = vanilla
requirements = (Arch == \"X86_64\") && ((OpSysAndVer =?= \"AlmaLinux9\") || (OpSysAndVer =?= \"CentOS7\"))
request_memory = 2000
request_disk = 10000000
executable = {executable}
arguments = $(seed)
output = {log_dir}/$(seed).out
error = {log_dir}/$(seed).err
log = {log_dir}/$(seed).log
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

+MaxRuntime = 24*60*60
+AccountingGroup = "group_u_CMST3.all"

MY.WantOS = "el9"
queue seed from (
{seeds}
)
""".format(
    executable=run_script,
    log_dir=log_dir,
    initialdir=input_dir,
    seeds=seeds_lines,
)

with open(submit_file, "w") as f:
    f.write(submit_content)

print(f"Created executable script: {run_script}")
print(f"Created Condor submit file: {submit_file}")
print("Submit with:\n   condor_submit " + submit_file)