#!/bin/bash
# SR observed, tt-vcb GENUINELY unblinded in the fit (user directive: compute
# the real GoF, real postfit shapes, real impacts -- the discipline is on
# reporting, not computation. Never print/state the tt-vcb central value or
# its impact magnitude in chat; everything else is fair game).
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   cd GoFStudy_orig_noFTS_lowess && ./run_sr_observed.sh
#
# Needs rabbit/ourSR.hdf5 from run_bulk.sh.

set -e

BASE=$(cd "$(dirname "$0")" && pwd)
cd "${BASE}"
O=rabbit
mkdir -p ${O} plots/prepostfit plots/impacts

PM="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
FULL="--doImpacts --globalImpacts --saveHists --saveHistsPerProcess --computeHistErrors"
POIS="tt-vcb xsec_ttbb xsec_ttbj xsec_tt2b xsec_ttcc xsec_ttcj xsec_tt2c xsec_ttLF"
JOBS=${JOBS:-16}
TOYS=${TOYS:-5000}
TOYS_PER_JOB=$(( (TOYS + JOBS - 1) / JOBS ))

while [ ! -f ${O}/ourSR.hdf5 ]; do echo "waiting for ourSR.hdf5 from run_bulk.sh..."; sleep 20; done

echo "### [1/4] fit -- tt-vcb genuinely unblinded"
[ -f ${O}/SR_observed.hdf5 ] || rabbit_fit.py ${O}/ourSR.hdf5 -o ${O} --outname SR_observed \
    -t 0 ${PM} --unblind 'tt-vcb' 'xsec_.*' ${FULL} \
    > ${O}/log_SR_observed.log 2>&1
grep -q "Unblinding 8 parameters:" ${O}/log_SR_observed.log \
    || { echo "ABORT: expected 8 unblinded parameters (tt-vcb + 7 xsec_*)" >&2; exit 1; }
echo "  fit done"

echo "### [2/4] prepostfit + impacts (8 POIs x 2 types)"
python3 ../analysis/rabbitPlotStack.py ${O}/SR_observed.hdf5 -o plots/prepostfit \
    --postfix SR_observed --logy > /dev/null 2>&1
for POI in ${POIS}; do
    for IT in traditional global; do
        python3 ../analysis/rabbitPlotImpacts.py ${O}/SR_observed.hdf5 --poi ${POI} \
            -o plots/impacts --postfix SR_observed --impact-type ${IT} > /dev/null 2>&1
    done
done
echo "  plots done"

echo "### [3/4] postfit-conditioned tensor for GoF toys (now genuinely correct, no offset to cancel)"
if [ ! -f ${O}/ourSR_postfitmean.hdf5 ]; then
    python3 - <<'PY'
import shutil, h5py
import numpy as np
from rabbit import io_tools, inputdata

O = 'rabbit'
indata = inputdata.FitInputData(f'{O}/ourSR.hdf5')
raw = np.asarray(indata.data_obs)

fr, meta = io_tools.get_fitresult(f'{O}/SR_observed.hdf5', meta=True)
chans = fr['mappings']['BaseMapping']['channels']

check = np.zeros_like(raw)
postfit = np.zeros_like(raw)
for ch, info in indata.channel_info.items():
    s, e = info['start'], info['stop']
    check[s:e] = chans[ch]['hist_data_obs'].get().values().flatten()
    postfit[s:e] = chans[ch]['hist_postfit_inclusive'].get().values().flatten()
assert np.allclose(raw, check, rtol=0, atol=1e-6), "channel ordering mismatch, refusing to patch"
assert np.all(postfit > 0), "non-positive postfit bin, unsafe for Poisson toys"

dst = f'{O}/ourSR_postfitmean.hdf5'
shutil.copyfile(f'{O}/ourSR.hdf5', dst)
with h5py.File(dst, 'r+') as f:
    f['hdata_obs'][...] = postfit.astype(f['hdata_obs'].dtype)
print(f'wrote {dst}: sums raw={raw.sum():.1f} postfit={postfit.sum():.1f}')
PY
fi

echo "### [4/4] GoF toys (${TOYS})"
for k in $(seq 1 ${JOBS}); do
    N=toyGoF_SR_observed_batch${k}
    [ -f ${O}/${N}.hdf5 ] && continue
    ( rabbit_fit.py ${O}/ourSR_postfitmean.hdf5 -o ${O} --outname ${N} \
        -t ${TOYS_PER_JOB} --toysDataMode observed --seed $((50000 + k)) \
        ${PM} --unblind 'tt-vcb' 'xsec_.*' \
        > ${O}/log_${N}.log 2>&1 ) &
done
wait
echo "### ALL DONE"
