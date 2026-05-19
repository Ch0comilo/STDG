"""Real kriging on ML residuals."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st


def empirical_variogram(coords: np.ndarray, values: np.ndarray,
                         n_lags: int = 12, max_dist_km: float | None = None
                         ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Crude experimental variogram on lat/lon coords (degrees converted to km approx)."""
    # Use approximate degrees → km via 111
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
    gamma = []
    counts = []
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
    """Fit gamma = nugget + (sill - nugget) * (1 - exp(-h/range))."""
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


@st.cache_data(show_spinner="Krigeando residuos…")
def krige_residuals(df_pred: pd.DataFrame, n_lags: int = 12) -> dict:
    """Aggregate residuals per municipio, compute variogram + ordinary kriging predictions
    at the same locations (for visualization / RMSE reduction estimation).
    """
    per_mun = (df_pred.groupby(["dane_code", "lat", "lon"], as_index=False)
                       .agg(obs=("obs", "mean"), pred=("pred", "mean"),
                             residual=("residual", "mean")))
    coords = per_mun[["lon", "lat"]].values
    res = per_mun["residual"].values

    h, gamma_emp, counts = empirical_variogram(coords, res, n_lags=n_lags)
    nugget, sill, range_ = fit_exponential(h, gamma_emp)
    gamma_theo = nugget + (sill - nugget) * (1 - np.exp(-h / max(range_, 1e-3)))

    # Ordinary kriging using pykrige — leave-one-out for honest evaluation
    krig_pred_loo = res.copy()
    krig_pred_smooth = res.copy()
    try:
        from pykrige.ok import OrdinaryKriging
        # Smooth surface (predicting at fit points — useful for visualization)
        OK = OrdinaryKriging(
            coords[:, 0], coords[:, 1], res,
            variogram_model="exponential",
            variogram_parameters={"sill": sill, "range": range_/111.0,
                                   "nugget": nugget},
            verbose=False, enable_plotting=False, coordinates_type="geographic",
        )
        z_smooth, _ = OK.execute("points", coords[:, 0], coords[:, 1])
        krig_pred_smooth = np.asarray(z_smooth)

        # LOO: kriging at each held-out point using K-Fold (10) for speed
        from sklearn.model_selection import KFold
        n = len(coords)
        kf = KFold(n_splits=min(10, n), shuffle=True, random_state=42)
        loo = np.zeros(n)
        for tr, te in kf.split(coords):
            try:
                OKt = OrdinaryKriging(
                    coords[tr, 0], coords[tr, 1], res[tr],
                    variogram_model="exponential",
                    variogram_parameters={"sill": sill, "range": range_/111.0,
                                            "nugget": nugget},
                    verbose=False, enable_plotting=False, coordinates_type="geographic",
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
        "nugget": nugget, "sill": sill, "range_km": range_,
        "rmse_base": rmse_base, "rmse_krig": rmse_krig, "delta_pct": delta,
        "df_per_mun": per_mun,
    }
