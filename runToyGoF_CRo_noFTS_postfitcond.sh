#!/bin/bash
# Toy-calibrated saturated GoF for CRo, orig shapes, our pipeline, lowess,
# --no-flavtag-mirror -- the PROPERLY conditioned version.
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   ./runToyGoF_CRo_noFTS_postfitcond.sh
#
# runToyGoF_CRo_noFTS.sh (the first attempt) fluctuated toys around the raw
# observed data_obs itself, which adds a SECOND independent layer of Poisson
# noise on top of what the one real dataset already has -- inflating the toy
# q-distribution (measured: toy mean 108.8 vs asymptotic chi2(54) mean 54,
# q_obs=53.37 below all 512 toys). Not a statement about GoF, an artifact of
# the naive conditioning point.
#
# Fix: build a COPY of ourCRnoFTS.hdf5 whose hdata_obs is overwritten with the
# real fit's own POSTFIT model expectation (from B_CRo_noFTS.hdf5's saved
# mappings/BaseMapping/channels/<ch>/hist_postfit_inclusive, per channel,
# placed at indata.channel_info[<ch>]['start':'stop'] -- verified bit-for-bit
# against the raw data_obs order using hist_data_obs before trusting this for
# hist_postfit_inclusive too). Toys now fluctuate around a single, smooth,
# postfit-conditioned mean -- one layer of Poisson noise, matching what the
# real data experienced. q_obs itself is UNCHANGED (still read from the real
# B_CRo_noFTS.hdf5 fit, 53.37) -- only the toy-generation tensor differs.
#
# Tensor build: see the inline python block below (also runnable standalone).

set -e

OUT=${OUT:-Comparison_250826_preUnblinding}
O=${OUT}/rabbit
JOBS=${JOBS:-16}
TOYS_PER_JOB=${TOYS_PER_JOB:-32}
SEED_BASE=${SEED_BASE:-30001}   # distinct from the naive run's 20001-20016

PM="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"

if [ ! -f ${O}/ourCRnoFTS_postfitmean.hdf5 ]; then
    echo "ERROR: ${O}/ourCRnoFTS_postfitmean.hdf5 missing -- build it first (see comment header)" >&2
    exit 1
fi

for k in $(seq 1 ${JOBS}); do
    N=toyGoF_CRo_noFTS_postfitcond_batch${k}
    [ -f ${O}/${N}.hdf5 ] && { echo "  ${N} already there, skipping"; continue; }
    ( rabbit_fit.py ${O}/ourCRnoFTS_postfitmean.hdf5 -o ${O} --outname ${N} \
        -t ${TOYS_PER_JOB} --toysDataMode observed --seed $((SEED_BASE + k)) \
        ${PM} --freezeParameters tt-vcb --unblind 'xsec_.*' \
        > ${O}/log_${N}.log 2>&1 ) &
done
wait
echo "### done: $((JOBS * TOYS_PER_JOB)) properly-conditioned toys across ${JOBS} files"
