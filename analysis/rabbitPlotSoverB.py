#!/usr/bin/env python3
"""Post-fit yields of every bin of every category, regrouped by log10(S/B).

S and B are the post-fit signal and background yields of each bin. The
background uncertainty is propagated by rabbit with the full post-fit
covariance (bins and processes correlated), via the SoverB mapping below
evaluated at the loaded fit result (--externalPostfit --noFit).

    analysis/rabbitPlotSoverB.py fit.hdf5 --tensor tensor.hdf5 -o plots/

The fit's own --paramModel and --unblind are reused, so the loaded parameters
are not shifted by blinding offsets.
"""

import argparse
import os
import subprocess

import hist
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from rabbit import io_tools
from rabbit.mappings.mapping import Mapping

from configs import model as M
from analysis.rabbitPlotStyle import cms_label
from analysis.rabbitResults import read_poi

# 0.25 grid shifted so SR bins 2, 3, 4 each get their own bin; the empty CR/SR
# gap (-2.35..-1.32) is split between its two neighbour bins at -1.85
EDGES = "-3.45,-3.20,-2.95,-2.70,-2.45,-1.85,-1.20,-0.95,-0.70,-0.45"
SIG = M.SIGNAL[0]


def log_sb(channels):
    """{channel: log10(S/B) per bin} from a fit result's post-fit hists."""
    out = {}
    for ch in channels.keys():
        h = channels[ch]["hist_postfit"].get()
        procs = [str(p) for p in h.axes["processes"]]
        v = h.values().reshape(-1, len(procs))
        s = v[:, procs.index(SIG)]
        out[ch] = np.log10(s / (v.sum(axis=1) - s))
    return out


def assign(lsb, edges):
    """Bin index in `edges`; values outside go to the first / last bin."""
    return np.clip(np.digitize(lsb, edges) - 1, 0, len(edges) - 2)


class SoverB(Mapping):
    """Sum all bins into log10(S/B) bins. Inclusive output = background only."""

    need_processes = True
    has_data = False
    skip_prefit = True

    def __init__(self, indata, key, fitresult, edges=EDGES):
        super().__init__(indata, key)
        edges = np.array(edges.strip("[]").split(","), dtype=float)
        lsb = log_sb(io_tools.get_fitresult(fitresult)["mappings"]["BaseMapping"]["channels"])
        nflat = max(info["stop"] for info in indata.channel_info.values())
        A = np.zeros((len(edges) - 1, nflat))
        for ch, info in indata.channel_info.items():
            A[assign(lsb[ch], edges), np.arange(info["start"], info["stop"])] = 1.0
        self.A = tf.constant(A, dtype=indata.dtype)
        procs = indata.procs.astype(str)
        self.bkg = tf.constant(procs != SIG, dtype=indata.dtype)
        self.channel_info = {"SoverB": {
            "axes": [hist.axis.Variable(edges, name="log10SoverB",
                                        underflow=False, overflow=False)],
            "flow": False, "processes": indata.procs}}

    def compute_flat(self, params, observables=None):
        return tf.linalg.matvec(self.A, tf.reduce_sum(observables * self.bkg, axis=1))

    def compute_flat_per_process(self, params, observables=None):
        return self.A @ observables


def run_rabbit(fit, tensor, outdir, outname, edges):
    _, meta = io_tools.get_fitresult(fit, meta=True)
    a = meta["meta_info"]["args"]
    cmd = ["rabbit_fit.py", tensor, "-o", outdir, "--outname", outname, "-t", "0",
           "--externalPostfit", fit, "--noFit", "--saveHists", "--saveHistsPerProcess",
           "--computeHistErrors", "-m", "BaseMapping",
           "-m", "analysis.rabbitPlotSoverB.SoverB", fit, f"[{edges}]"]
    for pm in a["paramModel"]:
        cmd += ["--paramModel", *pm]
    if a["unblind"]:
        cmd += ["--unblind", *a["unblind"]]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def step(ax, edges, y, **kw):
    ax.stairs(y, edges, baseline=None, **kw)


def draw(path, edges, data, bkg, berr, s_fit, mu):
    ok = bkg > 0
    data, berr, s_fit, bkg = [np.where(ok, v, np.nan) for v in (data, berr, s_fit, bkg)]
    s_sm = s_fit / mu
    x = 0.5 * (edges[1:] + edges[:-1])
    red, orange = "#e42536", "#f89c20"
    l_fit = rf"$\mathrm{{t\bar{{t}}}}$ (Vcb) ($\mu_{{fit}} = {mu:.2f}$)"
    l_sm = r"$\mathrm{t\bar{t}}$ (Vcb) ($\mu_{SM} = 1.0$)"

    fig, (a, r) = plt.subplots(2, 1, figsize=(10, 10), sharex=True,
                               gridspec_kw={"height_ratios": [3, 1.3], "hspace": 0.05})
    # larger signal first, so the smaller one stays visible on top of it
    sigs = sorted([(s_fit, red, l_fit), (s_sm, orange, l_sm)], key=lambda t: -np.nansum(t[0]))
    for s, c, l in sigs:
        a.stairs(bkg + s, edges, baseline=bkg, fill=True, color=c, label=l)
    a.stairs(bkg, edges, baseline=None, color="k", lw=1.2, label="Background")
    hatch = dict(fill=False, hatch="////", lw=0, edgecolor="k", alpha=0.7)
    a.stairs(bkg + berr, edges, baseline=bkg - berr, label="Bkg uncertainty", **hatch)
    a.errorbar(x, data, yerr=np.sqrt(data), fmt="ko", ms=8, lw=1.5, label="Data")

    r.stairs(1 + berr / bkg, edges, baseline=1 - berr / bkg, **hatch)
    r.axhline(1, color="k", lw=1)
    for s, c, l in sigs[::-1]:
        step(r, edges, (bkg + s) / bkg, color=c, lw=3, label=l + " + Bkg")
    r.errorbar(x, data / bkg, yerr=np.sqrt(data) / bkg, fmt="ko", ms=8, lw=1.5)

    a.set_yscale("log")
    a.set_ylim(0.5 * np.nanmin([bkg, data]), 300 * np.nanmax([bkg, data]))
    a.set_ylabel("Events")
    a.set_xlim(edges[0], edges[-1])
    h, l = a.get_legend_handles_labels()
    order = [l.index(k) for k in ("Data", "Background", "Bkg uncertainty")]
    left = a.legend([h[i] for i in order], [l[i] for i in order], loc="upper left", fontsize=18)
    a.add_artist(left)
    a.legend([h[l.index(k)] for k in (l_fit, l_sm)], [l_fit, l_sm], loc="upper right",
             fontsize=18)
    r.set_ylabel("Data / Bkg", fontsize=22)
    r.set_xlabel(r"$\log_{10}(S/B)$")
    top = np.nanmax(np.concatenate([(bkg + s_fit) / bkg, (bkg + s_sm) / bkg,
                                    (data + np.sqrt(data)) / bkg]))
    r.set_ylim(0.85, top + 0.4 * (top - 1))
    r.legend(loc="upper left", fontsize=16, frameon=False)
    cms_label(a, data=True, loc=0)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{path}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}.png")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fitresult", help="unblinded rabbit fit (-t 0) with --saveHistsPerProcess")
    p.add_argument("--tensor", required=True, help="input tensor the fit was run on")
    p.add_argument("-o", "--outdir", default="./")
    p.add_argument("--edges", default=EDGES, help="log10(S/B) bin edges, comma separated; use --edges=-3,...")
    args = p.parse_args()

    tag = os.path.splitext(os.path.basename(args.fitresult))[0]
    out = os.path.join(args.outdir, f"{tag}_SoverB.hdf5")
    run_rabbit(args.fitresult, args.tensor, args.outdir, f"{tag}_SoverB", args.edges)

    orig = io_tools.get_fitresult(args.fitresult)["mappings"]["BaseMapping"]["channels"]
    maps = io_tools.get_fitresult(out)["mappings"]
    base = maps["BaseMapping"]["channels"]
    # the re-evaluated fit must reproduce the stored post-fit exactly
    for ch in orig.keys():
        np.testing.assert_allclose(base[ch]["hist_postfit_inclusive"].get().values(),
                                   orig[ch]["hist_postfit_inclusive"].get().values(),
                                   rtol=1e-6, err_msg=ch)

    edges = np.array(args.edges.split(","), dtype=float)
    data = np.zeros(len(edges) - 1)
    for ch, lsb in log_sb(orig).items():
        np.add.at(data, assign(lsb, edges), orig[ch]["hist_data_obs"].get().values().flatten())

    sb = maps[f"SoverB {args.fitresult} [{args.edges}]"]["channels"]["SoverB"]
    b = sb["hist_postfit_inclusive"].get()
    hp = sb["hist_postfit"].get()
    s_fit = hp[{"processes": SIG}].values()
    np.testing.assert_allclose(b.values() + s_fit, hp.values().sum(axis=-1), rtol=1e-6)
    mu = read_poi(args.fitresult, SIG)[0]
    print(f"  mu_fit = {mu:.4f}")
    for i in range(len(data)):
        print(f"  [{edges[i]:6.2f},{edges[i+1]:6.2f}]  data {data[i]:9.0f}  "
              f"B {b.values()[i]:10.1f} +- {np.sqrt(b.variances()[i]):7.1f}  S {s_fit[i]:8.1f}")
    draw(os.path.join(args.outdir, f"{tag}_SoverB"), edges, data, b.values(),
         np.sqrt(b.variances()), s_fit, mu)


if __name__ == "__main__":
    main()
