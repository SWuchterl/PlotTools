# Rabbit backend

TensorFlow-based alternative to the classic Combine workflow described in
`README.md`, sharing the same input: `<card>_shapes.root` from
`prepareDatacards.py`. The model (categories, processes, systematics metadata)
is defined once in `configs/model.py`.

## Setup

```
cmsenv
git submodule update --init rabbit   # first time only, fetches the fitter
./setup_rabbit_env.sh                # builds rabbit_env/, first time only
source setup_rabbit.sh               # activate; `rabbit_off` to leave
```

## Run

```
./runRabbitFits.sh
```
builds tensors from a shapes file (`analysis/prepareTensor.py`), fits them
(`rabbit_fit.py`, from the `rabbit/` submodule), and plots pre/post-fit
stacks, likelihood scans, and impacts (`analysis/rabbitPlot{Stack,Scan,Impacts}.py`,
all CMS-styled, grouped legends, png+pdf). Edit the settings block at the top
of the script to point at a different shapes file.

Cross-check against classic Combine on one datacard:
```
./validateCombineRabbit.sh <carddir> <outdir>
```

## Layout

- `analysis/` -- tensor building, fit glue, and all plotting
  (`rabbitPlot{Stack,Scan,Impacts,Style}.py`, `prepareTensor.py`,
  `smoothing.py`, `validation*.py`, ...).
- `configs/model.py` -- single source of truth for categories, processes, and
  per-systematic statistical metadata (correlation class, symmetrisation).
- `rabbit/` -- the vendored fitter itself: a git submodule with its own
  history and README, not part of this repo's commits.
- `COMBINE_FIXES.md` -- Combine-side bugs found while building this backend.
- `RABBIT_TENSOR_GUIDE.md` -- tensor pipeline internals, decision policy.
