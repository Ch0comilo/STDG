"""Kriging de Residuos page — variograma + corrección espacial."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import REGION_COLORS
from models import train_model
from kriging_engine import krige_residuals
from charts import variogram, styled
from colombia_map import residual_map


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]
    model_name = st.session_state.get("model", "Random Forest")

    st.markdown(
        f"<h2 style='margin-top:0; font-size:20px;'>Kriging de Residuos</h2>"
        f"<p style='font-size:12px; color:{PALETTE['text_dim']}; margin-bottom:14px;'>"
        f"Variograma exponencial empírico + ordinary kriging sobre los residuos del modelo "
        f"<strong>{model_name}</strong> entrenado en {year}</p>",
        unsafe_allow_html=True,
    )

    with st.spinner(f"Entrenando {model_name} y krigeando residuos…"):
        res = train_model(base, year, model_name)
        krig = krige_residuals(res.df_pred)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Nugget", f"{krig['nugget']:.3f}", "(ton/ha)²",
                        color=PALETTE["text_dim"]), unsafe_allow_html=True)
    c2.markdown(metric("Sill", f"{krig['sill']:.3f}", "(ton/ha)²",
                        color=PALETTE["accent"]), unsafe_allow_html=True)
    c3.markdown(metric("Range", f"{krig['range_km']:.0f}", "km",
                        color=PALETTE["amber"]), unsafe_allow_html=True)
    c4.markdown(metric("Modelo", "Exp.", color=PALETTE["accent_hi"]),
                 unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "VARIOGRAMA EMPÍRICO + AJUSTE EXPONENCIAL"), unsafe_allow_html=True)
        st.plotly_chart(variogram(krig["h"], krig["gamma_emp"], krig["gamma_theo"],
                                    sill=krig["sill"], range_=krig["range_km"]),
                         use_container_width=True, config={"displayModeBar": False})
        dimmer = PALETTE["text_dimmer"]
        rng = krig["range_km"]; sill = krig["sill"]; nug = krig["nugget"]
        st.markdown(f"<div style='font-size:11px; color:{dimmer}; "
                    f"line-height:1.7'>Dependencia espacial detectada hasta ~{rng:.0f} km. "
                    f"Sill = {sill:.3f} representa la varianza total de los residuos. "
                    f"Nugget = {nug:.3f}.</div></div>",
                    unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            f"MAPA DE RESIDUOS POST-KRIGING — {model_name} · {year}"),
            unsafe_allow_html=True)
        post = krig["df_per_mun"].copy()
        post["residual"] = post["pred_corregido"] - post["obs"]
        residual_map(post, residual_col="residual", height=420,
                      key=f"krig_resid_map_{model_name}_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)

    # RMSE reduction across multiple base models
    st.markdown('<div class="agro-card">' + card_header(
        "REDUCCIÓN DE RMSE — ML puro vs ML + kriging de residuos"),
        unsafe_allow_html=True)

    cols = st.columns(3)
    for i, m in enumerate(["Random Forest", "XGBoost", "Lasso/Ridge"]):
        with cols[i]:
            with st.spinner(f"{m}…"):
                rm = train_model(base, year, m)
                kk = krige_residuals(rm.df_pred)
            delta_pct = kk["delta_pct"]
            st.markdown(f"""
            <div style='background:{PALETTE["card"]}; border:1px solid {PALETTE["border"]};
                        border-radius:8px; padding:14px; min-height:170px;'>
              <div style='font-weight:600; font-size:12px; margin-bottom:10px;'>{m}</div>
              <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                <span style='font-size:11px; color:{PALETTE["text_dim"]}'>RMSE base</span>
                <span style='font-family:IBM Plex Mono; font-size:12px;
                              color:{PALETTE["amber"]}'>{kk["rmse_base"]:.3f}</span>
              </div>
              <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:11px; color:{PALETTE["text_dim"]}'>RMSE + kriging</span>
                <span style='font-family:IBM Plex Mono; font-size:12px;
                              color:{PALETTE["accent"]}'>{kk["rmse_krig"]:.3f}</span>
              </div>
              <div style='background:rgba(74,222,128,0.14); border-radius:6px;
                          padding:8px 10px; text-align:center;'>
                <span style='font-family:IBM Plex Mono; color:{PALETTE["accent_hi"]};
                              font-size:18px; font-weight:700;'>
                  {('-' + f'{delta_pct:.1f}') if delta_pct >= 0 else f'+{-delta_pct:.1f}'}% RMSE
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
