#!/bin/bash
# Clean-session GoF study: orig shapes, our pipeline (prepareTensor.py),
# lowess smoothing, --no-flavtag-mirror. CR expected/observed, SR expected.
# SR observed (blinded tt-vcb) is handled separately -- see run_sr_observed.sh,
# gated on a resolved blinding-safety question, not run by this script.
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   cd GoFStudy_orig_noFTS_lowess && ./run_bulk.sh
#
# GoF toy conditioning (established in the prior Comparison_250826_preUnblinding
# session -- see its runToyGoF_CRo_noFTS_postfitcond.sh):
#   - Asimov configs (CR_expected, SR_expected): --toysDataMode expected uses
#     the model's own prior/default state as the toy mean, which for an Asimov
#     check already IS the correct null-hypothesis conditioning point (nobs was
#     never anything but that same expectation) -- no patched tensor needed.
#   - CR_observed (real data): --toysDataMode observed on the RAW tensor
#     double-counts Poisson noise (verified: toy mean ~2x asymptotic mean).
#     Fixed by patching a copy of the tensor's hdata_obs with CR_observed's
#     own postfit expectation (per-channel, from mappings/BaseMapping, at the
#     indata.channel_info start:stop indices -- verified bit-identical
#     reconstruction of data_obs before trusting it for the postfit array).

set -e

BASE=$(cd "$(dirname "$0")" && pwd)
cd "${BASE}"
O=rabbit
mkdir -p ${O} plots/prepostfit plots/impacts

SHAPES=../Datacards_250826_preUnblinding/orig/Vcb_SL_2024_shapes.root
PM="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
FULL="--doImpacts --globalImpacts --saveHists --saveHistsPerProcess --computeHistErrors"
POIS="tt-vcb xsec_ttbb xsec_ttbj xsec_tt2b xsec_ttcc xsec_ttcj xsec_tt2c xsec_ttLF"
JOBS=${JOBS:-16}
TOYS=${TOYS:-5000}
TOYS_PER_JOB=$(( (TOYS + JOBS - 1) / JOBS ))

# ------------------------------------------------------------------ tensors
echo "### [1/6] tensors"
# prepareTensor.py now defaults to lowess smoothing + flavTag mirror-up OFF,
# exactly this study's configuration -- no flags needed.
[ -f ${O}/ourSR.hdf5 ] || python3 ../analysis/prepareTensor.py ${SHAPES} \
    -o ${O} --outname ourSR \
    > ${O}/log_tensor_ourSR.log 2>&1 &
[ -f ${O}/ourCR.hdf5 ] || python3 ../analysis/prepareTensor.py ${SHAPES} \
    -o ${O} --outname ourCR --mask '_SR$' \
    > ${O}/log_tensor_ourCR.log 2>&1 &
wait
echo "  tensors done"

# ---------------------------------------------------------------------- fits
echo "### [2/6] fits (CR_expected, CR_observed, SR_expected + tt-vcb scan)"
[ -f ${O}/CR_expected.hdf5 ] || rabbit_fit.py ${O}/ourCR.hdf5 -o ${O} --outname CR_expected \
    -t -1 ${PM} --freezeParameters tt-vcb ${FULL} \
    > ${O}/log_CR_expected.log 2>&1
[ -f ${O}/CR_observed.hdf5 ] || rabbit_fit.py ${O}/ourCR.hdf5 -o ${O} --outname CR_observed \
    -t 0 ${PM} --freezeParameters tt-vcb --unblind 'xsec_.*' ${FULL} \
    > ${O}/log_CR_observed.log 2>&1
[ -f ${O}/SR_expected.hdf5 ] || rabbit_fit.py ${O}/ourSR.hdf5 -o ${O} --outname SR_expected \
    -t -1 ${PM} ${FULL} --scan tt-vcb --scanPoints 31 \
    > ${O}/log_SR_expected.log 2>&1
echo "  fits done"

# ------------------------------------------------------------------ prepostfit
echo "### [3/6] prepostfit"
python3 ../analysis/rabbitPlotStack.py ${O}/CR_expected.hdf5 -o plots/prepostfit \
    --postfix CR_expected --logy --asimov > /dev/null 2>&1
python3 ../analysis/rabbitPlotStack.py ${O}/CR_observed.hdf5 -o plots/prepostfit \
    --postfix CR_observed --logy > /dev/null 2>&1
python3 ../analysis/rabbitPlotStack.py ${O}/SR_expected.hdf5 -o plots/prepostfit \
    --postfix SR_expected --logy --asimov > /dev/null 2>&1
echo "  prepostfit done"

# --------------------------------------------------------------------- impacts
echo "### [4/6] impacts (traditional + global, 8 POIs x 3 configs = 48 plots)"
for CFG in CR_expected CR_observed SR_expected; do
    ASIMOV=""; [ "${CFG}" != "CR_observed" ] && ASIMOV="--asimov"
    for POI in ${POIS}; do
        for IT in traditional global; do
            python3 ../analysis/rabbitPlotImpacts.py ${O}/${CFG}.hdf5 --poi ${POI} \
                -o plots/impacts --postfix ${CFG} --impact-type ${IT} ${ASIMOV} \
                > /dev/null 2>&1
        done
    done
    echo "  ${CFG} impacts done"
done

# --------------------------------------------------- CR_observed postfit-mean
echo "### [5/6] CR_observed postfit-conditioned tensor for GoF toys"
if [ ! -f ${O}/ourCR_postfitmean.hdf5 ]; then
    python3 - <<'PY'
import shutil, h5py
import numpy as np
from rabbit import io_tools, inputdata

O = 'rabbit'
indata = inputdata.FitInputData(f'{O}/ourCR.hdf5')
raw = np.asarray(indata.data_obs)

fr, meta = io_tools.get_fitresult(f'{O}/CR_observed.hdf5', meta=True)
chans = fr['mappings']['BaseMapping']['channels']

# verify ordering against the OBSERVED data histogram before trusting it for postfit
check = np.zeros_like(raw)
postfit = np.zeros_like(raw)
for ch, info in indata.channel_info.items():
    if info['masked']:
        continue
    s, e = info['start'], info['stop']
    check[s:e] = chans[ch]['hist_data_obs'].get().values().flatten()
    postfit[s:e] = chans[ch]['hist_postfit_inclusive'].get().values().flatten()
assert np.allclose(raw, check, rtol=0, atol=1e-6), "channel ordering mismatch, refusing to patch"
assert np.all(postfit > 0), "non-positive postfit bin, unsafe for Poisson toys"

dst = f'{O}/ourCR_postfitmean.hdf5'
shutil.copyfile(f'{O}/ourCR.hdf5', dst)
with h5py.File(dst, 'r+') as f:
    f['hdata_obs'][...] = postfit.astype(f['hdata_obs'].dtype)
print(f'wrote {dst}: raw sum={raw.sum():.1f} postfit sum={postfit.sum():.1f}')
PY
fi
echo "  postfit-mean tensor ready"

# ------------------------------------------------------------------ GoF toys
echo "### [6/6] GoF toys (${TOYS} each, ${JOBS} jobs x ${TOYS_PER_JOB})"

run_toy_batch() {  # <name> <tensor> <mode> <extra fit flags...>
    local NAME=$1 TENSOR=$2 MODE=$3; shift 3
    echo "  --- ${NAME}"
    for k in $(seq 1 ${JOBS}); do
        local N=toyGoF_${NAME}_batch${k}
        [ -f ${O}/${N}.hdf5 ] && continue
        ( rabbit_fit.py ${O}/${TENSOR} -o ${O} --outname ${N} \
            -t ${TOYS_PER_JOB} --toysDataMode ${MODE} --seed $((40000 + k)) \
            "$@" > ${O}/log_${N}.log 2>&1 ) &
    done
    wait
    echo "  --- ${NAME} done"
}

run_toy_batch CR_expected ourCR.hdf5 expected ${PM} --freezeParameters tt-vcb
run_toy_batch CR_observed ourCR_postfitmean.hdf5 observed ${PM} --freezeParameters tt-vcb --unblind 'xsec_.*'
run_toy_batch SR_expected ourSR.hdf5 expected ${PM}

echo "### ALL DONE"
