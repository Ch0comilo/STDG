"""Kriging on observed yield (to fill missing municipios) and on model residuals.

Two entry points:
  - `krige_yield_full(df, year)`     → interpolates rendimiento everywhere
  - `krige_residuals(df_pred)`       → kriges the residuals of a fitted model
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from data_loader import load_municipios


# ─── variogram primitives ────────────────────────────────────────────────────

def empirical_variogram(coords: np.ndarray, values: np.ndarray,
                         n_lags: int = 12, max_dist_km: float | None = None
                         ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    coords_km = coords * 111.0
    n = len(coords_km)
    if n < 10:
        return np.array([]), np.array([]), np.array([])
    idx_i, idx_j = np.triu_indices(n, k=1)
    d = np.sqrt(((coords_km[idx_i] - coords_km[idx_j]) ** 2).sum(axis=1))
    diff2 = (values[idx_i] - values[idx_j]) ** 2 / 2.0
    if max_dist_km is None:
        max_dist_km = float(np.percentile(d, 60))
    bins = np.linspace(0, max_dist_km, n_lags + 1)
    centers = (bins[:-1] + bins[1:]) / 2.0
    gamma, counts = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (d >= lo) & (d < hi)
        if m.sum() > 5:
            gamma.append(diff2[m].mean())
            counts.append(int(m.sum()))
        else:
            gamma.append(np.nan)
            counts.append(0)
    return centers, np.array(gamma), np.array(counts)


def fit_exponential(h: np.ndarray, gamma: np.ndarray
                     ) -> tuple[float, float, float]:
    from scipy.optimize import curve_fit
    mask = ~np.isnan(gamma) & (h > 0)
    if mask.sum() < 4:
        return 0.0, float(np.nanmean(gamma)) if mask.any() else 1.0, max(50.0, float(h.max())/3 if len(h) else 50.0)
    h_use, g_use = h[mask], gamma[mask]

    def model(h, nugget, sill, range_):
        return nugget + (sill - nugget) * (1.0 - np.exp(-h / max(range_, 1e-3)))
    p0 = [g_use.min(), g_use.max(), h_use[len(h_use) // 2]]
    bounds = ([0, p0[1] * 0.5, 5.0], [p0[1], p0[1] * 3 + 1, 1000.0])
    try:
        popt, _ = curve_fit(model, h_use, g_use, p0=p0, bounds=bounds, maxfev=2000)
        return float(popt[0]), float(popt[1]), float(popt[2])
    except Exception:
        return float(p0[0]), float(p0[1]), float(p0[2])


# ─── yield kriging (fills missing municipios) ────────────────────────────────

@st.cache_data(show_spinner="Krigeando rendimiento por municipio…")
def krige_yield_full(df: pd.DataFrame, year: int, n_lags: int = 12) -> dict:
    """Ordinary kriging of `rendimiento` for the given year.

    Returns a dict with:
      - df_filled: per-municipio frame with columns
            dane_code, lat, lon, rendimiento_obs, rendimiento_krig,
            is_observed (bool), variance
      - h, gamma_emp, gamma_theo, nugget, sill, range_km
      - n_obs, n_filled, rmse_loo
    """
    yd = df[df["anio"] == year].copy()
    yd = yd.dropna(subset=["lat", "lon", "rendimiento"])
    yd = yd[yd["rendimiento"] > 0]
    per_mun_obs = (yd.groupby(["dane_code"], as_index=False)
                      .agg(lat=("lat", "first"), lon=("lon", "first"),
                            rendimiento=("rendimiento", "mean")))

    if len(per_mun_obs) < 10:
        return {"df_filled": pd.DataFrame(), "h": np.array([]),
                "gamma_emp": np.array([]), "gamma_theo": np.array([]),
                "nugget": 0.0, "sill": 0.0, "range_km": 0.0,
                "n_obs": len(per_mun_obs), "n_filled": 0, "rmse_loo": np.nan}

    coords = per_mun_obs[["lon", "lat"]].values
    z = per_mun_obs["rendimiento"].values

    h, gamma_emp, _ = empirical_variogram(coords, z, n_lags=n_lags)
    nugget, sill, range_km = fit_exponential(h, gamma_emp)
    gamma_theo = nugget + (sill - nugget) * (1 - np.exp(-h / max(range_km, 1e-3)))

    # All municipios from the shapefile — predict for those not observed
    muni = load_municipios()[["dane_code", "lat", "lon"]].drop_duplicates("dane_code")
    obs_codes = set(per_mun_obs["dane_code"])
    missing = muni[~muni["dane_code"].isin(obs_codes)].copy()

    krig_pred = np.full(len(missing), np.nan)
    variance = np.full(len(missing), np.nan)
    loo = z.copy()

    try:
        from pykrige.ok import OrdinaryKriging
        OK = OrdinaryKriging(
            coords[:, 0], coords[:, 1], z,
            variogram_model="exponential",
            variogram_parameters={"sill": sill, "range": range_km / 111.0,
                                   "nugget": nugget},
            verbose=False, enable_plotting=False, coordinates_type="geographic",
        )
        if len(missing) > 0:
            zp, ss = OK.execute("points",
                                  missing["lon"].values,
                                  missing["lat"].values)
            krig_pred = np.asarray(zp)
            variance = np.asarray(ss)

        # Leave-one-out (10-fold for speed) on observations
        from sklearn.model_selection import KFold
        n = len(coords)
        kf = KFold(n_splits=min(10, n), shuffle=True, random_state=42)
        for tr, te in kf.split(coords):
            try:
                OKt = OrdinaryKriging(
                    coords[tr, 0], coords[tr, 1], z[tr],
                    variogram_model="exponential",
                    variogram_parameters={"sill": sill, "range": range_km / 111.0,
                                            "nugget": nugget},
                    verbose=False, enable_plotting=False,
                    coordinates_type="geographic",
                )
                zte, _ = OKt.execute("points", coords[te, 0], coords[te, 1])
                loo[te] = np.asarray(zte)
            except Exception:
                loo[te] = z[te].mean()
    except Exception:
        pass

    rmse_loo = float(np.sqrt(np.mean((loo - z) ** 2))) if len(loo) else float("nan")

    # Combined frame
    obs_frame = per_mun_obs.copy()
    obs_frame = obs_frame.rename(columns={"rendimiento": "rendimiento_krig"})
    obs_frame["rendimiento_obs"] = obs_frame["rendimiento_krig"]
    obs_frame["is_observed"] = True
    obs_frame["variance"] = 0.0

    miss_frame = missing.copy()
    miss_frame["rendimiento_krig"] = krig_pred
    miss_frame["rendimiento_obs"] = np.nan
    miss_frame["is_observed"] = False
    miss_frame["variance"] = variance

    df_filled = pd.concat([obs_frame[["dane_code", "lat", "lon",
                                         "rendimiento_obs",
                                         "rendimiento_krig",
                                         "is_observed", "variance"]],
                              miss_frame[["dane_code", "lat", "lon",
                                          "rendimiento_obs",
                                          "rendimiento_krig",
                                          "is_observed", "variance"]]],
                             ignore_index=True)
    # Bound to plausible range
    df_filled["rendimiento_krig"] = df_filled["rendimiento_krig"].clip(lower=0, upper=15)

    return {
        "df_filled": df_filled,
        "h": h, "gamma_emp": gamma_emp, "gamma_theo": gamma_theo,
        "nugget": nugget, "sill": sill, "range_km": range_km,
        "n_obs": int(len(per_mun_obs)),
        "n_filled": int((~df_filled["is_observed"]).sum()),
        "rmse_loo": rmse_loo,
    }


# ─── residual kriging ────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Krigeando residuos…")
def krige_residuals(df_pred: pd.DataFrame, n_lags: int = 12) -> dict:
    per_mun = (df_pred.groupby(["dane_code", "lat", "lon"], as_index=False)
                       .agg(obs=("obs", "mean"), pred=("pred", "mean"),
                             residual=("residual", "mean")))
    coords = per_mun[["lon", "lat"]].values
    res = per_mun["residual"].values

    h, gamma_emp, _ = empirical_variogram(coords, res, n_lags=n_lags)
    nugget, sill, range_km = fit_exponential(h, gamma_emp)
    gamma_theo = nugget + (sill - nugget) * (1 - np.exp(-h / max(range_km, 1e-3)))

    krig_pred_loo = res.copy()
    krig_pred_smooth = res.copy()
    try:
        from pykrige.ok import OrdinaryKriging
        OK = OrdinaryKriging(
            coords[:, 0], coords[:, 1], res,
            variogram_model="exponential",
            variogram_parameters={"sill": sill, "range": range_km / 111.0,
                                   "nugget": nugget},
            verbose=False, enable_plotting=False, coordinates_type="geographic",
        )
        z_smooth, _ = OK.execute("points", coords[:, 0], coords[:, 1])
        krig_pred_smooth = np.asarray(z_smooth)

        from sklearn.model_selection import KFold
        n = len(coords)
        kf = KFold(n_splits=min(10, n), shuffle=True, random_state=42)
        loo = np.zeros(n)
        for tr, te in kf.split(coords):
            try:
                OKt = OrdinaryKriging(
                    coords[tr, 0], coords[tr, 1], res[tr],
                    variogram_model="exponential",
                    variogram_parameters={"sill": sill, "range": range_km / 111.0,
                                            "nugget": nugget},
                    verbose=False, enable_plotting=False,
                    coordinates_type="geographic",
                )
                zte, _ = OKt.execute("points", coords[te, 0], coords[te, 1])
                loo[te] = np.asarray(zte)
            except Exception:
                loo[te] = res[te].mean()
        krig_pred_loo = loo
    except Exception:
        pass

    per_mun["residual_krig_smooth"] = krig_pred_smooth
    per_mun["residual_krig_loo"] = krig_pred_loo
    per_mun["pred_corregido"] = per_mun["pred"] - per_mun["residual_krig_loo"]
    rmse_base = float(np.sqrt(np.mean((per_mun["pred"] - per_mun["obs"]) ** 2)))
    rmse_krig = float(np.sqrt(np.mean((per_mun["pred_corregido"] - per_mun["obs"]) ** 2)))
    delta = (rmse_base - rmse_krig) / max(rmse_base, 1e-6) * 100

    return {
        "h": h, "gamma_emp": gamma_emp, "gamma_theo": gamma_theo,
        "nugget": nugget, "sill": sill, "range_km": range_km,
        "rmse_base": rmse_base, "rmse_krig": rmse_krig, "delta_pct": delta,
        "df_per_mun": per_mun,
    }
