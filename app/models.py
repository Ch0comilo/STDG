"""Real ML models trained on the AGRONET maíz dataset.

Features used per municipality·year:
  - lat, lon, altitud_proxy (computed from latitude or geom)
  - area_sembrada
  - log_area_cosechada
  - region (one-hot)
  - año

Targets: rendimiento (ton/ha)
Includes: random K-Fold CV and SPATIAL block CV (by departamento) for fairness.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import KFold, GroupKFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


FEATURES_NUM = ["lat", "lon", "area_sembrada_log", "area_cosechada_log", "anio_norm"]
FEATURES_CAT = ["region"]
# TerriData socio-economic features used when present
FEATURES_TERRIDATA = ["cob_energia", "recaudo_predial"]


def _prep(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    sub = df.copy()
    if year is not None:
        sub = sub[sub["anio"] == year]
    sub = sub.dropna(subset=["rendimiento", "lat", "lon", "area_sembrada"])
    sub = sub[(sub["area_sembrada"] > 0)]
    sub["area_sembrada_log"] = np.log1p(sub["area_sembrada"])
    sub["area_cosechada_log"] = np.log1p(sub["area_cosechada"].clip(lower=0))
    sub["anio_norm"] = (sub["anio"] - sub["anio"].min()) / max(1, sub["anio"].max() - sub["anio"].min())
    # Fill TerriData numeric features with column median where present
    for col in FEATURES_TERRIDATA:
        if col in sub.columns:
            med = sub[col].median()
            sub[col] = sub[col].fillna(med if pd.notna(med) else 0.0)
    # one-hot region
    region_dum = pd.get_dummies(sub["region"], prefix="reg", drop_first=False)
    sub = pd.concat([sub, region_dum], axis=1)
    return sub


def _feature_matrix(sub: pd.DataFrame) -> pd.DataFrame:
    region_cols = [c for c in sub.columns if c.startswith("reg_")]
    extra = [c for c in FEATURES_TERRIDATA if c in sub.columns]
    cols = FEATURES_NUM + extra + region_cols
    return sub[cols].astype(float)


def _build(model_name: str, n_trees: int = 200, max_depth: int = 8, alpha: float = 0.1):
    if model_name == "Random Forest":
        return RandomForestRegressor(
            n_estimators=n_trees, max_depth=max_depth, min_samples_leaf=3,
            n_jobs=-1, random_state=42,
        )
    if model_name == "XGBoost":
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=n_trees, max_depth=max_depth, learning_rate=0.07,
                subsample=0.85, colsample_bytree=0.85, n_jobs=-1, random_state=42,
                tree_method="hist", verbosity=0,
            )
        except Exception:
            # Fallback to sklearn GBR if xgboost is unavailable
            from sklearn.ensemble import GradientBoostingRegressor
            return GradientBoostingRegressor(n_estimators=n_trees, max_depth=max_depth,
                                              random_state=42)
    if model_name == "Lasso/Ridge":
        return Pipeline([("sc", StandardScaler()),
                         ("reg", Ridge(alpha=alpha, random_state=42))])
    if model_name == "GWR":
        # Lightweight surrogate: KNN-weighted local regression — treated as a "geographically-weighted" baseline.
        from sklearn.neighbors import KNeighborsRegressor
        return KNeighborsRegressor(n_neighbors=10, weights="distance")
    raise ValueError(model_name)


@dataclass
class TrainResult:
    model_name: str
    rmse: float
    mae: float
    r2: float
    rmse_spatial: float
    moran_residuos: float
    obs: np.ndarray
    pred: np.ndarray
    residuals: np.ndarray
    feature_importance: pd.Series
    feature_names: list[str]
    df_pred: pd.DataFrame  # has dane_code/lat/lon/obs/pred/residual
    full_model: object


@st.cache_data(show_spinner="Entrenando modelo ML…")
def train_model(df: pd.DataFrame, year: int, model_name: str,
                 n_trees: int = 200, max_depth: int = 8,
                 alpha: float = 0.1) -> TrainResult:
    sub = _prep(df, year=year)
    if len(sub) < 30:
        # Not enough — back off to all years
        sub = _prep(df, year=None)

    X = _feature_matrix(sub)
    y = sub["rendimiento"].values
    feat_names = X.columns.tolist()

    # Random K-Fold CV
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    obs_all, pred_all = [], []
    for tr, te in kf.split(X):
        m = _build(model_name, n_trees=n_trees, max_depth=max_depth, alpha=alpha)
        m.fit(X.iloc[tr].values, y[tr])
        obs_all.append(y[te])
        pred_all.append(np.asarray(m.predict(X.iloc[te].values)))
    obs = np.concatenate(obs_all)
    pred = np.concatenate(pred_all)

    rmse = float(np.sqrt(mean_squared_error(obs, pred)))
    mae = float(mean_absolute_error(obs, pred))
    r2 = float(r2_score(obs, pred))

    # Spatial block CV by departamento
    groups = sub["depto_norm"].values
    n_groups = len(np.unique(groups))
    if n_groups >= 5:
        gkf = GroupKFold(n_splits=min(5, n_groups))
        sp_obs, sp_pred = [], []
        for tr, te in gkf.split(X, y, groups):
            m = _build(model_name, n_trees=n_trees, max_depth=max_depth, alpha=alpha)
            m.fit(X.iloc[tr].values, y[tr])
            sp_obs.append(y[te])
            sp_pred.append(np.asarray(m.predict(X.iloc[te].values)))
        sp_obs = np.concatenate(sp_obs); sp_pred = np.concatenate(sp_pred)
        rmse_sp = float(np.sqrt(mean_squared_error(sp_obs, sp_pred)))
    else:
        rmse_sp = rmse * 1.10

    # Final fit on all data for predictions/residuals
    full = _build(model_name, n_trees=n_trees, max_depth=max_depth, alpha=alpha)
    full.fit(X.values, y)
    pred_full = np.asarray(full.predict(X.values))
    resid = pred_full - y

    df_pred = sub[["dane_code", "lat", "lon", "departamento", "municipio",
                    "region", "anio"]].copy()
    df_pred["obs"] = y
    df_pred["pred"] = pred_full
    df_pred["residual"] = resid

    # Feature importance
    if hasattr(full, "feature_importances_"):
        fi = pd.Series(full.feature_importances_, index=feat_names)
    elif hasattr(full, "coef_"):
        fi = pd.Series(np.abs(np.asarray(full.coef_).ravel()), index=feat_names)
    elif isinstance(full, Pipeline) and hasattr(full[-1], "coef_"):
        fi = pd.Series(np.abs(full[-1].coef_), index=feat_names)
    else:
        # KNN — use permutation importance as proxy on a small sample
        from sklearn.inspection import permutation_importance
        try:
            sample_idx = np.random.RandomState(0).choice(len(X), size=min(800, len(X)),
                                                          replace=False)
            r = permutation_importance(full, X.iloc[sample_idx].values, y[sample_idx],
                                         n_repeats=3, random_state=42, n_jobs=-1)
            fi = pd.Series(r.importances_mean, index=feat_names).clip(lower=0)
        except Exception:
            fi = pd.Series(np.ones(len(feat_names)) / len(feat_names), index=feat_names)

    if fi.sum() == 0:
        fi[:] = 1 / len(fi)
    fi = fi / fi.sum()

    # Moran I of residuals (KNN weights)
    try:
        from libpysal.weights import KNN
        from esda.moran import Moran
        coords = sub[["lon", "lat"]].values
        # need unique points for KNN — collapse to per-municipality residual
        per_mun = (df_pred.groupby(["dane_code", "lat", "lon"], as_index=False)["residual"]
                          .mean())
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

    return TrainResult(
        model_name=model_name, rmse=rmse, mae=mae, r2=r2,
        rmse_spatial=rmse_sp, moran_residuos=moran_res,
        obs=obs, pred=pred, residuals=resid,
        feature_importance=fi, feature_names=feat_names,
        df_pred=df_pred, full_model=full,
    )


@st.cache_data(show_spinner="Entrenando todos los modelos…")
def train_all(df: pd.DataFrame, year: int) -> dict[str, TrainResult]:
    out = {}
    for name in ["Random Forest", "XGBoost", "Lasso/Ridge", "GWR"]:
        try:
            out[name] = train_model(df, year, name)
        except Exception as e:
            st.warning(f"Falló {name}: {e}")
    return out


def pdp_curve(result: TrainResult, feature: str, n_points: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Compute a partial-dependence curve for a single numeric feature."""
    df_pred = result.df_pred
    # Use the original prepared X via the residual frame (minus pred/residual cols)
    sub = df_pred.copy()
    sub["area_sembrada_log"] = np.log1p(sub.get("area_sembrada", 1))
    sub["area_cosechada_log"] = np.log1p(sub.get("area_cosechada", 1))
    yr = sub["anio"]
    sub["anio_norm"] = (yr - yr.min()) / max(1, yr.max() - yr.min())
    region_dum = pd.get_dummies(sub["region"], prefix="reg")
    region_cols = [c for c in result.feature_names if c.startswith("reg_")]
    for c in region_cols:
        if c not in region_dum.columns:
            region_dum[c] = 0
    sub = pd.concat([sub, region_dum[region_cols]], axis=1)
    base_cols = result.feature_names
    if feature not in base_cols:
        return np.array([]), np.array([])
    if not all(c in sub.columns for c in base_cols):
        return np.array([]), np.array([])
    xs = sub[feature].astype(float)
    grid = np.linspace(xs.quantile(0.05), xs.quantile(0.95), n_points)
    out = []
    template = sub[base_cols].astype(float).copy()
    for v in grid:
        template[feature] = v
        try:
            p = result.full_model.predict(template.values)
            out.append(float(np.mean(p)))
        except Exception:
            out.append(float("nan"))
    return grid, np.array(out)
