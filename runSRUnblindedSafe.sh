#!/bin/bash
# GoF + impacts for CRo / SR-expected / SR-unblinded, orig templates,
# --no-flavtag-mirror pipeline, WITHOUT ever exposing the tt-vcb central value.
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   ./runSRUnblindedSafe.sh
#
# Requires the tensors from runPreUnblindingComparison.sh:
#   Comparison_250826_preUnblinding/rabbit/{ourSRnoFTS,ourCRnoFTS}.hdf5
#
# ============================================================================
# BLINDING MECHANISM -- read before changing anything in this file
# ============================================================================
# rabbit blinds a POI on any REAL-data fit (-t 0) unless it is named in
# --unblind. Blinding multiplies the physical POI value by a DETERMINISTIC
# offset exp(N(0,5)) seeded from the parameter's own name (SHA256 hash,
# rabbit/rabbit/fitter.py:612-627). It is reproducible (same file, same
# scramble, every run) and not recoverable without the source's hash of the
# parameter name.
#
# What is provably safe to compute on a blinded fit (verified by reading
# rabbit/rabbit/fitter.py and rabbit/bin/rabbit_fit.py directly, not inferred):
#   - GoF (nllvalreduced / saturated chi2): computed inside fit() from the NLL
#     VALUE at the converged minimum. The blinding offset cancels through the
#     minimisation (get_poi(x*) = mu(x*)*offset = mu_hat_true regardless of
#     offset), so the NLL value -- and hence GoF -- reflects the true fit
#     quality. Always available, no extra flag; COMBINE_FIXES.md and
#     runRabbitFits.sh already treat it as freely reportable.
#   - --doImpacts / --globalImpacts: Hessian/curvature-based. The plotting
#     script (analysis/rabbitPlotImpacts.py:57-59) scales impacts by the
#     STORED (already-scrambled) parms value, never by a fresh get_poi() call,
#     so impact magnitudes stay scrambled and their RANKING is offset-invariant
#     (multiplying every impact by the same unknown positive scalar preserves
#     order). This is the intended use of --unblind: review impacts before
#     revealing the value.
#
# What is NOT safe and is deliberately EXCLUDED from the SR-unblinded fit:
#   --saveHists / --saveHistsPerProcess / --computeHistErrors / --computeHistImpacts
#   These compute postfit yields via get_poi() AFTER fit() returns, with the
#   blinding offset still active (rabbit_fit.py:994-1012, no reset in between).
#   Because the offset cancels through the same fit, this path returns the
#   TRUE, unscrambled best-fit SR yield -- i.e. the true postfit SR shape would
#   be written to disk. Confirmed by direct code reading, not assumption.
#
# Operational rule for whoever reads B_SR_noFTS_unblinded.hdf5 later:
#   NEVER read/print the "tt-vcb" entry from this file. Every other parameter
#   (xsec_*, nuisances, GoF) is safe. The impacts_..._tt-vcb_SR_UNBLINDED_*.png
#   plot IS safe to open (built from the scrambled stored value only) but its
#   "total" annotation is a scrambled number, not the true uncertainty --
#   do not quote it as if it were.
# ============================================================================

set -e

OUT=${OUT:-Comparison_250826_preUnblinding}
O=${OUT}/rabbit
D=${OUT}/plots/impacts_noFTS
mkdir -p "${D}"

PM="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
FULL="--doImpacts --globalImpacts --saveHists --saveHistsPerProcess --computeHistErrors"

echo "### CRo (observed, SR masked, tt-vcb frozen -- not sensitive, full output)"
rabbit_fit.py "${O}/ourCRnoFTS.hdf5" -o "${O}" --outname B_CRo_noFTS -t 0 ${PM} \
    --freezeParameters tt-vcb --unblind 'xsec_.*' ${FULL} \
    > "${O}/log_B_CRo_noFTS.log" 2>&1

echo "### SR expected (Asimov -- never blinded by construction, full output)"
rabbit_fit.py "${O}/ourSRnoFTS.hdf5" -o "${O}" --outname B_SR_noFTS -t -1 ${PM} \
    ${FULL} \
    > "${O}/log_B_SR_noFTS.log" 2>&1

echo "### SR UNBLINDED (real data, SR unmasked) -- tt-vcb stays blinded"
rabbit_fit.py "${O}/ourSRnoFTS.hdf5" -o "${O}" --outname B_SR_noFTS_unblinded -t 0 ${PM} \
    --unblind 'xsec_.*' --doImpacts --globalImpacts \
    > "${O}/log_B_SR_noFTS_unblinded.log" 2>&1
grep -q "Unblinding 7 parameters:.*xsec_tt2b.*xsec_ttLF" "${O}/log_B_SR_noFTS_unblinded.log" \
    || { echo "ABORT: unblind audit line missing/unexpected, refusing to trust this fit" >&2; exit 1; }
grep -qi "tt-vcb" <(grep -i "^INFO:fitter.py: Unblinding" "${O}/log_B_SR_noFTS_unblinded.log") \
    && { echo "ABORT: tt-vcb appears unblinded, this must never happen" >&2; exit 1; }

echo "### impact plots (traditional, ungrouped)"
python3 analysis/rabbitPlotImpacts.py "${O}/B_CRo_noFTS.hdf5" --poi xsec_ttLF \
    -o "${D}" --postfix CRo_noFTS --impact-type traditional
python3 analysis/rabbitPlotImpacts.py "${O}/B_SR_noFTS.hdf5" --poi tt-vcb \
    -o "${D}" --postfix SR_expected_noFTS --impact-type traditional --asimov
python3 analysis/rabbitPlotImpacts.py "${O}/B_SR_noFTS_unblinded.hdf5" --poi tt-vcb \
    -o "${D}" --postfix SR_UNBLINDED_noFTS --impact-type traditional

echo "### done -> ${O}, ${D}"
