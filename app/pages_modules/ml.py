"""Modelos ML — RF / XGBoost / Lasso / GWR — entrenados sobre datos reales."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import filter_data, REGION_COLORS
from models import train_model, pdp_curve
from charts import scatter_obs_pred, bar_horizontal, pdp_chart, styled
from colombia_map import residual_map, choropleth


FEATURE_LABELS = {
    "lat": "Latitud",
    "lon": "Longitud",
    "area_sembrada_log": "Área sembrada (log)",
    "area_cosechada_log": "Área cosechada (log)",
    "anio_norm": "Año (norm.)",
    "cob_energia": "Cobertura energía (%)",
    "recaudo_predial": "Recaudo predial (%)",
}


def _shap_proxy(result, top_n: int = 8) -> tuple[list[str], list[float]]:
    fi = result.feature_importance.sort_values(ascending=False).head(top_n)
    labels = [FEATURE_LABELS.get(k, k.replace("reg_", "Región ")) for k in fi.index]
    return labels[::-1], fi.values.tolist()[::-1]


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]
    model_name = st.session_state.get("model", "Random Forest")
    n_trees = st.session_state.get("n_trees", 200)
    max_depth = st.session_state.get("max_depth", 8)
    alpha = st.session_state.get("alpha", 0.1)

    st.markdown(
        f"<h2 style='margin-top:0; font-size:20px;'>Modelos de Machine Learning</h2>"
        f"<p style='font-size:12px; color:{PALETTE['text_dim']}; margin-bottom:14px;'>"
        f"Entrenado sobre datos reales AGRONET-EVA · año = {year} · región = {region}"
        f" · CV aleatoria 5-fold + CV espacial por departamento</p>",
        unsafe_allow_html=True,
    )

    with st.spinner(f"Entrenando {model_name}…"):
        res = train_model(base, year, model_name,
                           n_trees=n_trees, max_depth=max_depth, alpha=alpha)

    moran_color = PALETTE["bad"] if (not np.isnan(res.moran_residuos) and res.moran_residuos > 0.1) else PALETTE["ok"]
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("RMSE (CV aleat.)", f"{res.rmse:.3f}", "ton/ha",
                        color=PALETTE["amber"]), unsafe_allow_html=True)
    c2.markdown(metric("MAE", f"{res.mae:.3f}", "ton/ha",
                        color=PALETTE["amber"]), unsafe_allow_html=True)
    c3.markdown(metric("R²", f"{res.r2:.3f}", color=PALETTE["accent"]),
                 unsafe_allow_html=True)
    moran_str = f"{res.moran_residuos:.3f}" if not np.isnan(res.moran_residuos) else "n/d"
    c4.markdown(metric("Moran I residuos", moran_str, color=moran_color),
                 unsafe_allow_html=True)

    # Importance + scatter
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"IMPORTANCIA DE VARIABLES — {model_name}"), unsafe_allow_html=True)
        labels, vals = _shap_proxy(res, top_n=8)
        st.plotly_chart(bar_horizontal(labels, vals),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            f"OBSERVADO vs PREDICHO — {model_name}"), unsafe_allow_html=True)
        st.plotly_chart(scatter_obs_pred(res.obs, res.pred),
                         use_container_width=True, config={"displayModeBar": False})
        dimmer = PALETTE["text_dimmer"]
        st.markdown(f"<div style='font-size:11px; color:{dimmer};'>"
                    f"Línea punteada = predicción perfecta · RMSE = {res.rmse:.3f} ton/ha</div></div>",
                    unsafe_allow_html=True)

    # PDP
    st.markdown('<div class="agro-card">' + card_header(
        "DEPENDENCIA PARCIAL — efecto marginal por variable"), unsafe_allow_html=True)
    top_feats = res.feature_importance.sort_values(ascending=False).index.tolist()
    pdp_feats = [f for f in top_feats if f in res.feature_names and not f.startswith("reg_")][:3]
    cols = st.columns(3)
    for i, feat in enumerate(pdp_feats):
        with cols[i]:
            xs, ys = pdp_curve(res, feat)
            label = FEATURE_LABELS.get(feat, feat)
            if len(xs) > 0:
                dim = PALETTE["text_dim"]
                st.markdown(f"<div style='font-size:11px; color:{dim}; "
                            f"margin-bottom:6px'>{label}</div>", unsafe_allow_html=True)
                st.plotly_chart(pdp_chart(xs, ys, label),
                                 use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Residual map + prediction map
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"MAPA DE RESIDUOS ESPACIALES — {model_name}"), unsafe_allow_html=True)
        # Build a per-municipality mean residual frame
        residual_map(res.df_pred, residual_col="residual",
                      height=420, key=f"resid_map_{model_name}_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            f"PREDICCIÓN MUNICIPAL — {model_name} · {year}"), unsafe_allow_html=True)
        pred_df = res.df_pred.copy()
        pred_df["rendimiento"] = pred_df["pred"]
        pred_df["anio"] = year
        choropleth(pred_df, value_key="rendimiento", year=year,
                    height=420, key=f"pred_map_{model_name}_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)

    if not np.isnan(res.moran_residuos) and res.moran_residuos > 0.1:
        st.markdown(alert(
            f"<strong style='color:#fca5a5'>Autocorrelación residual detectada</strong> "
            f"(I = {res.moran_residuos:.3f}): el modelo {model_name} no captura completamente "
            f"la estructura espacial. Ve a <em>Kriging de Residuos</em> para corregirla.",
            kind="bad"
        ), unsafe_allow_html=True)
