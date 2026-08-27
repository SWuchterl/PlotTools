#!/bin/bash
# Toy-calibrated saturated GoF for CRo, orig shapes, our pipeline, lowess,
# --no-flavtag-mirror (the leg-B configuration we settled on as "the right
# one"). Cross-checks the asymptotic chi2(ndf) approximation reported earlier
# against an empirical distribution of q = 2*nllvalreduced from real toys.
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   ./runToyGoF_CRo_noFTS.sh
#
# NOT run for SR-expected (Asimov, q_obs=0 trivially, low information) or
# SR-unblinded (real SR data -- toy generation there needs its own careful
# blinding analysis, not requested, not attempted here).
#
# Toy generation: --toysDataMode observed Poisson-fluctuates around the raw
# observed data_obs counts (verified from rabbit/rabbit/fitter.py:toyassign --
# "expected" mode would use the model evaluated at prefit/default parameters,
# since defaultassign() resets state before every toy in this code path;
# neither mode conditions on the real-data postfit fit within one invocation).
# --toysSystRandomize frequentist (the default) redraws each nuisance's prior
# centre before generating that toy, the standard frequentist-toy recipe.
#
# Parallelism: rabbit_fit.py -t N generates N toys inside ONE process,
# sequentially, sharing tensor-load/graph-trace setup cost. Different
# processes MUST use different --seed (fixed default 123456789 otherwise,
# giving byte-identical "toy 1..N" across jobs -- verified in fitter.py/
# rabbit_fit.py: np.random.seed(args.seed) once at start, consumed by one
# deterministic stream). Measured: ~31 s/toy including per-job overhead.

set -e

OUT=${OUT:-Comparison_250826_preUnblinding}
O=${OUT}/rabbit
JOBS=${JOBS:-16}
TOYS_PER_JOB=${TOYS_PER_JOB:-32}   # 16 x 32 = 512 >= 500 requested
SEED_BASE=${SEED_BASE:-20001}

PM="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"

for k in $(seq 1 ${JOBS}); do
    N=toyGoF_CRo_noFTS_batch${k}
    [ -f ${O}/${N}.hdf5 ] && { echo "  ${N} already there, skipping"; continue; }
    ( rabbit_fit.py ${O}/ourCRnoFTS.hdf5 -o ${O} --outname ${N} \
        -t ${TOYS_PER_JOB} --toysDataMode observed --seed $((SEED_BASE + k)) \
        ${PM} --freezeParameters tt-vcb --unblind 'xsec_.*' \
        > ${O}/log_${N}.log 2>&1 ) &
done
wait
echo "### done: $((JOBS * TOYS_PER_JOB)) toys across ${JOBS} files"
