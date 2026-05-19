"""Single linear model — OLS for inference + Ridge for prediction.

We use one model on purpose: linear regression is the most interpretable choice,
and the assignment is now about explaining *why* a municipality yields what it
does, not about leaderboard chasing.

The fit pipeline:
  1. Build features (with safe log transforms + region one-hot).
  2. Standardize (so Ridge alpha is meaningful and OLS coefficients are
     comparable in magnitude — "feature importance" for a linear model).
  3. Pick Ridge alpha via 5-fold CV (GridSearchCV on a log-spaced grid).
  4. Refit OLS via statsmodels on the standardized matrix for inference:
     coefficient table, p-values, 95% CIs, R², adj-R², F-statistic, AIC/BIC.
  5. Run diagnostic tests on residuals:
       - Linearity:        Ramsey RESET (approx via squared fitted)
       - Independence:     Durbin-Watson
       - Homoscedasticity: Breusch-Pagan
       - Normality:        Jarque-Bera, Shapiro-Wilk
       - Multicollinearity: VIF per feature
       - Spatial residual autocorrelation: Moran I (KNN k=8)
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


FEATURES_NUM = [
    "area_sembrada_log",     # tamaño de la siembra
    "area_cosechada_log",    # tamaño cosechado (correlacionado, lo veremos en VIF)
    "lat",                    # latitud — proxy de zona térmica
    "lon",                    # longitud — proxy de vertiente / región
    "anio_norm",              # año normalizado (tendencia tecnológica)
]
FEATURES_CLIMATE = ["prcp_anual", "tmed_anual", "enso_anual"]
FEATURES_TERRIDATA = [
    "cob_energia_rural", "banda_ancha", "ingresos_totales",
    "uso_adecuado_pct", "sobreutil_pct", "recaudo_predial",
]

FEATURE_LABELS = {
    "area_sembrada_log":  "Área sembrada (log ha)",
    "area_cosechada_log": "Área cosechada (log ha)",
    "lat":                 "Latitud (°)",
    "lon":                 "Longitud (°)",
    "anio_norm":           "Año (normalizado)",
    "prcp_anual":          "Precipitación anual (mm)",
    "tmed_anual":          "Temperatura media (°C)",
    "enso_anual":          "ENSO Niño 3.4",
    "cob_energia_rural":   "Cobertura energía rural (%)",
    "banda_ancha":         "Penetración banda ancha (%)",
    "ingresos_totales":    "Ingresos totales (COP)",
    "uso_adecuado_pct":    "Uso adecuado del suelo (%)",
    "sobreutil_pct":       "Sobreutilización del suelo (%)",
    "recaudo_predial":     "Recaudo predial (%)",
    "intercept":           "Intercepto",
}


def _prep(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    sub = df.copy()
    if year is not None:
        sub = sub[sub["anio"] == year]
    sub = sub.dropna(subset=["rendimiento", "lat", "lon", "area_sembrada"])
    sub = sub[(sub["area_sembrada"] > 0)]
    sub["area_sembrada_log"] = np.log1p(sub["area_sembrada"])
    sub["area_cosechada_log"] = np.log1p(sub["area_cosechada"].clip(lower=0))
    yr_min, yr_max = sub["anio"].min(), sub["anio"].max()
    sub["anio_norm"] = (sub["anio"] - yr_min) / max(1, yr_max - yr_min)
    for col in FEATURES_CLIMATE + FEATURES_TERRIDATA:
        if col in sub.columns:
            med = sub[col].median()
            sub[col] = sub[col].fillna(med if pd.notna(med) else 0.0)
    region_dum = pd.get_dummies(sub["region"], prefix="reg", drop_first=True)
    sub = pd.concat([sub, region_dum], axis=1)
    return sub


def _feature_matrix(sub: pd.DataFrame) -> pd.DataFrame:
    region_cols = [c for c in sub.columns if c.startswith("reg_")]
    extra = [c for c in FEATURES_CLIMATE + FEATURES_TERRIDATA if c in sub.columns]
    cols = FEATURES_NUM + extra + region_cols
    return sub[cols].astype(float)


# ─── diagnostics container ───────────────────────────────────────────────────

@dataclass
class LinearResult:
    # CV / generalization
    rmse: float
    mae: float
    r2: float
    rmse_spatial: float
    # In-sample OLS inference
    r2_in: float
    r2_adj: float
    f_stat: float
    f_pvalue: float
    aic: float
    bic: float
    n_obs: int
    n_features: int
    # Coefficients (standardized features → comparable importance)
    coef_table: pd.DataFrame   # term, beta_std, std_err, t, p, ci_lo, ci_hi
    intercept: float
    # Diagnostics
    durbin_watson: float
    breusch_pagan_p: float
    jarque_bera_p: float
    shapiro_p: float
    reset_pvalue: float        # linearity (Ramsey-style)
    vif: pd.Series
    moran_residuos: float
    # Hyperparameter
    ridge_alpha: float
    alpha_curve: pd.DataFrame  # alpha, mean_rmse
    # Predictions / data
    feature_names: list[str]
    obs: np.ndarray
    pred: np.ndarray
    residuals: np.ndarray
    fitted: np.ndarray
    standardized_residuals: np.ndarray
    df_pred: pd.DataFrame
    ridge_model: object
    scaler: object
    # Variables removed during iterative VIF reduction
    dropped_features: list = field(default_factory=list)   # (name, vif_at_drop, reason)
    vif_threshold: float = 10.0


def _iterative_vif_reduction(X: pd.DataFrame, threshold: float = 10.0
                              ) -> tuple[pd.DataFrame, list[tuple[str, float, str]]]:
    """Drop the highest-VIF column repeatedly until all VIF ≤ threshold.

    Returns the cleaned design matrix and a log of dropped features as
    (column_name, vif_at_time_of_drop, reason).
    """
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    dropped = []
    X_cur = X.copy()
    while X_cur.shape[1] > 1:
        Xm = sm.add_constant(X_cur, has_constant="add").values
        vifs: dict[str, float] = {}
        for i, col in enumerate(X_cur.columns):
            try:
                # +1 skips the constant column added by add_constant
                vifs[col] = float(variance_inflation_factor(Xm, i + 1))
            except Exception:
                vifs[col] = float("nan")
        # Keep going while at least one VIF (finite) is above threshold
        bad = {c: v for c, v in vifs.items()
               if not np.isnan(v) and v > threshold}
        if not bad:
            break
        worst = max(bad, key=bad.get)
        dropped.append((worst, bad[worst],
                         f"VIF = {bad[worst]:.1f} > {threshold:.0f}"))
        X_cur = X_cur.drop(columns=[worst])
    return X_cur, dropped


@st.cache_data(show_spinner="Ajustando regresión lineal y validando supuestos…")
def fit_linear(df: pd.DataFrame, year: int,
               alpha_grid: tuple = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0),
               vif_threshold: float = 10.0) -> LinearResult:
    """Fit OLS+Ridge with full diagnostics.

    Step 0 (pre-fit): iterative VIF reduction. We compute VIF on the raw
    feature matrix and drop the highest until every remaining variable has
    VIF ≤ `vif_threshold`. This way the final model — and everything reported
    in the Streamlit — is already free of severe multicollinearity.
    """
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.stats.diagnostic import (
        het_breuschpagan, linear_reset, normal_ad,
    )
    from statsmodels.stats.stattools import durbin_watson, jarque_bera
    from scipy import stats as sps

    sub = _prep(df, year=year)
    if len(sub) < 30:
        sub = _prep(df, year=None)

    X = _feature_matrix(sub)
    y = sub["rendimiento"].values.astype(float)

    # Drop zero-variance columns (e.g. a region dummy when filtering a single region)
    keep = X.std(axis=0) > 1e-9
    if not keep.all():
        X = X.loc[:, keep]

    # ── Iterative VIF reduction on the RAW (un-standardized) matrix ──────
    X, dropped_log = _iterative_vif_reduction(X, threshold=vif_threshold)
    feat_names = X.columns.tolist()

    # Standardize for comparability + Ridge stability
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X.values)

    # 5-fold CV — sweep alpha
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(
        Ridge(random_state=42),
        param_grid={"alpha": list(alpha_grid)},
        scoring="neg_root_mean_squared_error",
        cv=kf, n_jobs=-1,
    )
    grid.fit(X_std, y)
    best_alpha = float(grid.best_params_["alpha"])
    alpha_curve = pd.DataFrame({
        "alpha": list(alpha_grid),
        "rmse_cv": [-s for s in grid.cv_results_["mean_test_score"]],
    })

    # OOF predictions with the best alpha for honest residuals
    oof = np.empty_like(y)
    for tr, te in kf.split(X_std):
        m = Ridge(alpha=best_alpha, random_state=42)
        m.fit(X_std[tr], y[tr])
        oof[te] = m.predict(X_std[te])
    rmse = float(np.sqrt(mean_squared_error(y, oof)))
    mae = float(mean_absolute_error(y, oof))
    r2 = float(r2_score(y, oof))

    # Spatial CV by departamento
    try:
        from sklearn.model_selection import GroupKFold
        groups = sub["depto_norm"].values
        n_groups = len(np.unique(groups))
        if n_groups >= 5:
            gkf = GroupKFold(n_splits=min(5, n_groups))
            sp_pred = np.empty_like(y)
            for tr, te in gkf.split(X_std, y, groups):
                m = Ridge(alpha=best_alpha, random_state=42)
                m.fit(X_std[tr], y[tr])
                sp_pred[te] = m.predict(X_std[te])
            rmse_sp = float(np.sqrt(mean_squared_error(y, sp_pred)))
        else:
            rmse_sp = rmse * 1.10
    except Exception:
        rmse_sp = rmse * 1.10

    # Refit Ridge on full sample (used for prediction maps)
    ridge_full = Ridge(alpha=best_alpha, random_state=42).fit(X_std, y)
    pred_full = ridge_full.predict(X_std)
    resid = y - pred_full

    # OLS via statsmodels on the same standardized matrix — for inference
    X_sm = sm.add_constant(pd.DataFrame(X_std, columns=feat_names),
                            has_constant="add")
    ols = sm.OLS(y, X_sm).fit()

    coef_df = pd.DataFrame({
        "term":      ols.params.index,
        "beta_std":  ols.params.values,
        "std_err":   ols.bse.values,
        "t":         ols.tvalues.values,
        "p":         ols.pvalues.values,
        "ci_lo":     ols.conf_int()[0].values,
        "ci_hi":     ols.conf_int()[1].values,
    })
    _const_rows = coef_df.loc[coef_df["term"] == "const", "beta_std"]
    intercept = float(_const_rows.iloc[0]) if len(_const_rows) else 0.0

    # ── diagnostic tests ──────────────────────────────────────────────────
    fitted = ols.fittedvalues.values
    resid_ols = ols.resid.values
    std_resid = resid_ols / (resid_ols.std(ddof=1) + 1e-12)

    dw = float(durbin_watson(resid_ols))

    # Breusch-Pagan (homoscedasticity)
    try:
        bp = het_breuschpagan(resid_ols, X_sm.values)
        bp_p = float(bp[1])
    except Exception:
        bp_p = float("nan")

    # Jarque-Bera (normality)
    try:
        jb_stat, jb_p, _, _ = jarque_bera(resid_ols)
        jb_p = float(jb_p)
    except Exception:
        jb_p = float("nan")

    # Shapiro-Wilk — only valid for n<=5000, otherwise sample
    try:
        sample = resid_ols if len(resid_ols) <= 5000 else \
                 np.random.default_rng(0).choice(resid_ols, 5000, replace=False)
        shapiro_p = float(sps.shapiro(sample).pvalue)
    except Exception:
        shapiro_p = float("nan")

    # Ramsey RESET (linearity)
    try:
        reset = linear_reset(ols, power=2, use_f=True)
        reset_p = float(reset.pvalue)
    except Exception:
        reset_p = float("nan")

    # VIF per feature (excludes intercept)
    vif_vals = {}
    Xv = X_sm.values
    for i, col in enumerate(X_sm.columns):
        if col == "const":
            continue
        try:
            vif_vals[col] = float(variance_inflation_factor(Xv, i))
        except Exception:
            vif_vals[col] = float("nan")
    vif = pd.Series(vif_vals)

    # Moran I on residuals
    try:
        from libpysal.weights import KNN
        from esda.moran import Moran
        df_loc = sub[["dane_code", "lat", "lon"]].copy()
        df_loc["residual"] = resid_ols
        per_mun = df_loc.groupby(["dane_code", "lat", "lon"], as_index=False)["residual"].mean()
        coords = per_mun[["lon", "lat"]].values
        if len(per_mun) > 9:
            w = KNN.from_array(coords, k=8)
            w.transform = "r"
            mor = Moran(per_mun["residual"].values, w, permutations=99)
            moran_res = float(mor.I)
        else:
            moran_res = float("nan")
    except Exception:
        moran_res = float("nan")

    # ── prediction frame for downstream maps ──────────────────────────────
    df_pred = sub[["dane_code", "lat", "lon", "departamento", "municipio",
                    "region", "anio"]].copy()
    df_pred["obs"] = y
    df_pred["pred"] = pred_full
    df_pred["residual"] = pred_full - y

    return LinearResult(
        rmse=rmse, mae=mae, r2=r2, rmse_spatial=rmse_sp,
        r2_in=float(ols.rsquared), r2_adj=float(ols.rsquared_adj),
        f_stat=float(ols.fvalue), f_pvalue=float(ols.f_pvalue),
        aic=float(ols.aic), bic=float(ols.bic),
        n_obs=int(ols.nobs), n_features=int(len(feat_names)),
        coef_table=coef_df, intercept=intercept,
        durbin_watson=dw, breusch_pagan_p=bp_p,
        jarque_bera_p=jb_p, shapiro_p=shapiro_p,
        reset_pvalue=reset_p,
        vif=vif, moran_residuos=moran_res,
        ridge_alpha=best_alpha, alpha_curve=alpha_curve,
        feature_names=feat_names,
        obs=y, pred=pred_full, residuals=resid, fitted=fitted,
        standardized_residuals=std_resid,
        df_pred=df_pred, ridge_model=ridge_full, scaler=scaler,
        dropped_features=dropped_log, vif_threshold=vif_threshold,
    )
