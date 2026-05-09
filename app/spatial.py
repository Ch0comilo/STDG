"""Real spatial statistics — Moran I, LISA — computed with libpysal/esda."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local


@st.cache_data(show_spinner="Calculando Moran I y LISA…")
def compute_moran(df: pd.DataFrame, value_col: str = "rendimiento",
                   k: int = 8, year: int | None = None) -> dict:
    """Compute global Moran I and local LISA on a per-year aggregate by municipality.

    Returns a dict with: I, p_sim, lag, lisa (per-row HH/LL/HL/LH/NS), df.
    """
    if year is not None:
        sub = df[df["anio"] == year].copy()
    else:
        sub = df.copy()

    # One row per municipality (mean if multiple)
    agg = (sub.groupby(["dane_code", "lat", "lon", "departamento", "municipio", "region"],
                        as_index=False)[value_col].mean())
    if len(agg) < k + 1:
        return {"I": np.nan, "p_sim": np.nan, "lag": [], "lisa": [], "df": agg}

    coords = agg[["lon", "lat"]].values
    w = KNN.from_array(coords, k=k)
    w.transform = "r"
    y = agg[value_col].values

    moran = Moran(y, w, permutations=199)
    local = Moran_Local(y, w, permutations=199, seed=42)

    # Quadrants from local Moran (1=HH, 2=LH, 3=LL, 4=HL); flag NS where p_sim > 0.05
    q = local.q
    p_sim = local.p_sim
    sig = p_sim < 0.05
    lisa_labels = []
    for qi, s in zip(q, sig):
        if not s:
            lisa_labels.append("NS")
        else:
            lisa_labels.append({1: "HH", 2: "LH", 3: "LL", 4: "HL"}[int(qi)])
    lag = (w.sparse @ y) / max(1, w.n)  # not really needed; lag values from KNN
    # Better: use lag computed by libpysal
    from libpysal.weights.spatial_lag import lag_spatial
    lag_vals = lag_spatial(w, y)

    agg["lisa"] = lisa_labels
    agg["lag"] = lag_vals
    agg["z"] = (y - y.mean()) / y.std(ddof=0)
    agg["lag_z"] = (lag_vals - lag_vals.mean()) / lag_vals.std(ddof=0)

    return {
        "I": float(moran.I),
        "p_sim": float(moran.p_sim),
        "EI": float(moran.EI),
        "lag": lag_vals,
        "lisa": lisa_labels,
        "df": agg,
    }


@st.cache_data(show_spinner=False)
def moran_history(df: pd.DataFrame, value_col: str = "rendimiento",
                   k: int = 8) -> pd.DataFrame:
    """Compute Moran's I for every available year. Cached."""
    rows = []
    for y in sorted(df["anio"].unique()):
        try:
            r = compute_moran(df, value_col=value_col, k=k, year=int(y))
            rows.append({"anio": int(y), "I": r["I"], "p_sim": r["p_sim"]})
        except Exception:
            rows.append({"anio": int(y), "I": np.nan, "p_sim": np.nan})
    return pd.DataFrame(rows)
