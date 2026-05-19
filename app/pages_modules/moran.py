"""Autocorrelación Espacial — Moran I, LISA."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import metric, card_header, alert, PALETTE, PLOTLY_LAYOUT
from data_loader import filter_data, REGION_COLORS
from spatial import compute_moran, moran_history, compute_variogram
from colombia_map import lisa_map
from charts import styled, variogram


def _moran_scatter(df_with_z: pd.DataFrame, I: float) -> go.Figure:
    fig = go.Figure()
    quads = {"HH": "#22c55e", "LL": "#ef4444", "HL": "#3b82f6",
             "LH": "#f59e0b", "NS": "#475569"}
    for k, c in quads.items():
        sub = df_with_z[df_with_z["lisa"] == k]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub["z"], y=sub["lag_z"], mode="markers", name=k,
                marker=dict(color=c, size=6, opacity=0.75),
                hovertemplate="<b>%{customdata[0]}</b><br>"
                              "z=%{x:.2f} · lag z=%{y:.2f}<extra></extra>",
                customdata=sub[["municipio"]].values,
            ))
    # Reference line y = I*x (slope of OLS)
    xs = np.linspace(df_with_z["z"].min(), df_with_z["z"].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=I * xs, mode="lines",
                              line=dict(color=PALETTE["amber"], dash="dash", width=1.4),
                              name=f"slope = I = {I:.3f}", showlegend=True))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.18)", width=0.7))
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.18)", width=0.7))
    fig.update_layout(
        height=320,
        xaxis_title="Rendimiento estandarizado (z)",
        yaxis_title="Lag espacial estandarizado",
        legend=dict(orientation="h", y=-0.20, x=0),
    )
    return styled(fig)


def _moran_history_bars(hist: pd.DataFrame, current_year: int) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=hist["anio"], y=hist["I"],
        marker=dict(color=[PALETTE["accent"] if y == current_year else "rgba(74,222,128,0.40)"
                            for y in hist["anio"]]),
        text=[f"{v:.2f}" for v in hist["I"]],
        textposition="outside",
        hovertemplate="Año %{x}<br>I = %{y:.3f}<extra></extra>",
    ))
    fig.update_layout(height=240, xaxis_title=None, yaxis_title="I de Moran")
    return styled(fig)


def render(df, year: int, region: str) -> None:
    st.markdown(
        f"<h2 style='margin-top:0; font-size:20px;'>Autocorrelación Espacial</h2>"
        f"<p style='font-size:12px; color:{PALETTE['text_dim']}; margin-bottom:14px;'>"
        f"Índice de Moran global e indicadores locales de asociación espacial (LISA) "
        f"sobre rendimiento de maíz por municipio · KNN k=8</p>",
        unsafe_allow_html=True,
    )

    base = df if region == "Todas" else df[df["region"] == region]
    res = compute_moran(base, value_col="rendimiento", k=8, year=year)
    if not res["df"].shape[0]:
        st.warning("No hay datos suficientes para calcular Moran I.")
        return
    I = res["I"]; p = res["p_sim"]
    lisa_df = res["df"]
    counts = lisa_df["lisa"].value_counts().to_dict()

    p_str = "< 0.001" if p < 0.001 else f"{p:.3f}"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Moran I global", f"{I:.3f}",
                        color=PALETTE["accent"]), unsafe_allow_html=True)
    c2.markdown(metric("p-valor", p_str, color=PALETTE["amber"]), unsafe_allow_html=True)
    c3.markdown(metric("Clusters HH", f"{counts.get('HH', 0)}", "muns",
                        color=PALETTE["ok"]), unsafe_allow_html=True)
    c4.markdown(metric("Clusters LL", f"{counts.get('LL', 0)}", "muns",
                        color=PALETTE["bad"]), unsafe_allow_html=True)

    if I > 0 and p < 0.05:
        msg = (f"<strong style='color:{PALETTE['accent_hi']}'>"
               f"Autocorrelación positiva significativa</strong> "
               f"(I = {I:.3f}, p = {p_str}): municipios con alto rendimiento tienden a estar "
               f"rodeados de municipios similares. La estructura espacial explica parte importante "
               f"de la varianza.")
    elif I < 0 and p < 0.05:
        msg = (f"<strong style='color:{PALETTE['amber']}'>Autocorrelación negativa</strong> "
               f"(I = {I:.3f}, p = {p_str}): patrón en damero — alto-rendimiento rodeado de bajo.")
    else:
        msg = (f"Sin evidencia robusta de autocorrelación global (I = {I:.3f}, p = {p_str}).")
    st.markdown(alert(msg), unsafe_allow_html=True)

    # LISA map + Moran scatter
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"MAPA LISA — clusters espaciales · {year}"), unsafe_allow_html=True)
        lisa_map(lisa_df, lisa_col="lisa", height=460,
                  key=f"lisa_map_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "DIAGRAMA DE MORAN — z vs lag espacial z"), unsafe_allow_html=True)
        st.plotly_chart(_moran_scatter(lisa_df, I),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # History bars + Variogram
    hist = moran_history(base, value_col="rendimiento", k=8)
    vario = compute_variogram(base, value_col="rendimiento", year=year)

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "TENDENCIA HISTÓRICA — I de Moran por año"), unsafe_allow_html=True)
        st.plotly_chart(_moran_history_bars(hist, year),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "VARIOGRAMA — Dependencia espacial vs Distancia"), unsafe_allow_html=True)
        if len(vario["h"]) > 0:
            st.plotly_chart(variogram(vario["h"], vario["gamma_emp"], vario["gamma_theo"],
                                      vario["sill"], vario["range"]),
                             use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("No hay datos suficientes para el variograma.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Cluster distribution
    st.markdown('<div class="agro-card">' + card_header("DISTRIBUCIÓN LISA"),
                 unsafe_allow_html=True)
    total = sum(counts.values()) or 1
    rows = []
    for k, c in [("HH", "#4ade80"), ("LL", "#ef4444"),
                  ("HL", "#3b82f6"), ("LH", "#f59e0b"), ("NS", "#475569")]:
        n = counts.get(k, 0)
        pct = n / total * 100
        rows.append(f"""
          <div style='margin-bottom:6px;'>
            <div style='display:flex; justify-content:space-between; font-size:11px;'>
              <span style='color:{c}'>{k}</span>
              <span style='font-family:IBM Plex Mono; color:{PALETTE["text_dim"]}'>
                {n} ({pct:.0f}%)</span>
            </div>
            <div style='height:7px; background:{PALETTE["card"]}; border-radius:4px;'>
              <div style='height:100%; width:{pct}%; background:{c};
                          border-radius:4px; opacity:0.85;'></div>
            </div>
          </div>
        """)
    st.markdown("".join(rows) + "</div>", unsafe_allow_html=True)
