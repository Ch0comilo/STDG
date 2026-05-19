"""Detalle Técnico — autocorrelación espacial + variogramas.

Va al final del flujo. Es la sección 'para los técnicos': Moran I global,
clusters LISA, variograma del rendimiento y de los residuos del modelo lineal,
mapa de varianza de kriging. Las páginas previas ya entregaron la respuesta
de negocio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import REGION_COLORS
from spatial import compute_moran, moran_history
from colombia_map import lisa_map, residual_map, choropleth
from models import fit_linear
from kriging_engine import krige_yield_full, krige_residuals
import charts as ch


def _moran_scatter(df_with_z: pd.DataFrame, I: float) -> go.Figure:
    fig = go.Figure()
    quads = {"HH": "#2dca5f", "LL": "#ef4444", "HL": "#60a5fa",
             "LH": "#f0b34a", "NS": "#94a39a"}
    for k, c in quads.items():
        sub = df_with_z[df_with_z["lisa"] == k]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub["z"], y=sub["lag_z"], mode="markers", name=k,
                marker=dict(color=c, size=7, opacity=0.78,
                            line=dict(color=PALETTE["bg"], width=0.4)),
                hovertemplate="<b>%{customdata[0]}</b><br>"
                              "z=%{x:.2f} · lag z=%{y:.2f}<extra></extra>",
                customdata=sub[["municipio"]].values,
            ))
    xs = np.linspace(df_with_z["z"].min(), df_with_z["z"].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=I * xs, mode="lines",
                              line=dict(color=PALETTE["amber"], dash="dash", width=1.6),
                              name=f"slope = I = {I:.3f}"))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.20)", width=0.8))
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.20)", width=0.8))
    fig.update_layout(
        height=340,
        xaxis_title="Rendimiento estandarizado (z)",
        yaxis_title="Lag espacial estandarizado",
        legend=dict(orientation="h", y=-0.22, x=0),
    )
    return ch.styled(fig)


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]

    st.markdown(
        f"<h2 style='margin-top:0;'>Detalle Técnico · Análisis Espacial</h2>"
        f"<p style='font-size:14px; color:{PALETTE['text_dim']}; margin-bottom:18px;'>"
        f"Moran I global y local, variograma del rendimiento, kriging ordinario "
        f"y kriging de residuos del modelo lineal. Para validar la estructura "
        f"espacial del fenómeno.</p>",
        unsafe_allow_html=True,
    )

    # ── Section 1: Moran ──────────────────────────────────────────────────
    st.markdown("<h3>1 · Autocorrelación espacial · I de Moran</h3>",
                 unsafe_allow_html=True)
    mres = compute_moran(base, value_col="rendimiento", k=8, year=year)
    if not mres["df"].shape[0]:
        st.warning("No hay datos suficientes para calcular Moran I.")
        return
    I = mres["I"]; p = mres["p_sim"]; lisa_df = mres["df"]
    counts = lisa_df["lisa"].value_counts().to_dict()
    p_str = "< 0.001" if p < 0.001 else f"{p:.3f}"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Moran I global", f"{I:.3f}",
                        color=PALETTE["accent_hi"],
                        sub=f"p-valor = {p_str}"),
                 unsafe_allow_html=True)
    c2.markdown(metric("Clusters HH", f"{counts.get('HH', 0)}", "muns",
                        color=PALETTE["ok"], sub="alto rodeado de alto"),
                 unsafe_allow_html=True)
    c3.markdown(metric("Clusters LL", f"{counts.get('LL', 0)}", "muns",
                        color=PALETTE["bad"], sub="bajo rodeado de bajo"),
                 unsafe_allow_html=True)
    c4.markdown(metric("Outliers HL+LH",
                        f"{counts.get('HL', 0) + counts.get('LH', 0)}", "muns",
                        color=PALETTE["amber"], sub="atípicos espaciales"),
                 unsafe_allow_html=True)

    if I > 0 and p < 0.05:
        msg = (f"<strong style='color:{PALETTE['accent_hi']}'>"
               f"Autocorrelación positiva significativa</strong> "
               f"(I = {I:.3f}, p = {p_str}): municipios con alto rendimiento tienden "
               f"a estar rodeados de municipios similares.")
    elif I < 0 and p < 0.05:
        msg = (f"<strong style='color:{PALETTE['amber']}'>Autocorrelación negativa</strong> "
               f"(I = {I:.3f}, p = {p_str}): patrón en damero.")
    else:
        msg = f"Sin evidencia de autocorrelación global (I = {I:.3f}, p = {p_str})."
    st.markdown(alert(msg), unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"Mapa LISA · clusters espaciales · {year}"),
            unsafe_allow_html=True)
        lisa_map(lisa_df, lisa_col="lisa", height=460,
                  key=f"lisa_map_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Diagrama de Moran"), unsafe_allow_html=True)
        st.plotly_chart(_moran_scatter(lisa_df, I),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="agro-card">' + card_header(
            "Distribución LISA"), unsafe_allow_html=True)
        st.plotly_chart(ch.lisa_pie(counts),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Historical Moran
    st.markdown('<div class="agro-card">' + card_header(
        "Tendencia histórica · I de Moran por año"), unsafe_allow_html=True)
    hist = moran_history(base, value_col="rendimiento", k=8)
    fig_h = go.Figure(go.Bar(
        x=hist["anio"], y=hist["I"],
        marker=dict(color=[PALETTE["accent_hi"] if y == year else "rgba(94,224,138,0.40)"
                            for y in hist["anio"]]),
        text=[f"{v:.2f}" for v in hist["I"]],
        textposition="outside", textfont=dict(size=11),
        hovertemplate="Año %{x}<br>I = %{y:.3f}<extra></extra>",
    ))
    fig_h.update_layout(height=280, xaxis_title=None, yaxis_title="I de Moran")
    st.plotly_chart(ch.styled(fig_h), use_container_width=True,
                     config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 2: Variograma del rendimiento ─────────────────────────────
    st.markdown("<h3>2 · Variograma y kriging ordinario del rendimiento</h3>",
                 unsafe_allow_html=True)
    with st.spinner("Calculando variograma del rendimiento…"):
        krig_y = krige_yield_full(base, year)

    if krig_y["df_filled"].empty:
        st.info("No hay suficientes municipios observados este año para kriging.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric("Nugget", f"{krig_y['nugget']:.3f}", "(ton/ha)²",
                            color=PALETTE["text_dim"],
                            sub="varianza a distancia 0"),
                     unsafe_allow_html=True)
        c2.markdown(metric("Sill", f"{krig_y['sill']:.3f}", "(ton/ha)²",
                            color=PALETTE["accent"],
                            sub="meseta del variograma"),
                     unsafe_allow_html=True)
        c3.markdown(metric("Range", f"{krig_y['range_km']:.0f}", "km",
                            color=PALETTE["amber"],
                            sub="alcance de la dependencia"),
                     unsafe_allow_html=True)
        c4.markdown(metric("RMSE leave-one-out", f"{krig_y['rmse_loo']:.3f}", "ton/ha",
                            color=PALETTE["info"], sub="precisión del kriging"),
                     unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown('<div class="agro-card">' + card_header(
                "Variograma empírico + ajuste exponencial"),
                unsafe_allow_html=True)
            st.plotly_chart(ch.variogram(
                krig_y["h"], krig_y["gamma_emp"], krig_y["gamma_theo"],
                sill=krig_y["sill"], range_=krig_y["range_km"]),
                use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
                f"Dependencia espacial detectada hasta ~{krig_y['range_km']:.0f} km.</div></div>",
                unsafe_allow_html=True,
            )
        with right:
            st.markdown('<div class="agro-card">' + card_header(
                f"Mapa de varianza de kriging · incertidumbre · {year}"),
                unsafe_allow_html=True)
            df_var = krig_y["df_filled"][["dane_code", "variance"]].copy()
            df_var = df_var.rename(columns={"variance": "var_krig"})
            value_map = dict(zip(df_var["dane_code"], df_var["var_krig"]))
            choropleth(pd.DataFrame(), value_key="var_krig", year=None,
                        value_map_override=value_map, height=400,
                        key=f"krig_var_map_{year}_{region}",
                        caption="Varianza de kriging (incertidumbre)",
                        unit="(ton/ha)²")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 3: Kriging de residuos del modelo lineal ──────────────────
    st.markdown("<h3>3 · Kriging de residuos del modelo lineal</h3>",
                 unsafe_allow_html=True)
    with st.spinner("Ajustando modelo lineal y krigeando residuos…"):
        res = fit_linear(base, year)
        krig_r = krige_residuals(res.df_pred)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("RMSE modelo solo", f"{krig_r['rmse_base']:.3f}", "ton/ha",
                        color=PALETTE["amber"]),
                 unsafe_allow_html=True)
    c2.markdown(metric("RMSE + kriging residual", f"{krig_r['rmse_krig']:.3f}", "ton/ha",
                        color=PALETTE["accent_hi"]),
                 unsafe_allow_html=True)
    delta = krig_r["delta_pct"]
    delta_color = PALETTE["ok"] if delta > 0 else PALETTE["bad"]
    c3.markdown(metric("Reducción de error", f"{delta:+.1f}", "%",
                        color=delta_color,
                        sub="ML + kriging vs ML puro"),
                 unsafe_allow_html=True)
    c4.markdown(metric("Range residuos", f"{krig_r['range_km']:.0f}", "km",
                        color=PALETTE["text_dim"]),
                 unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Variograma de residuos del modelo lineal"),
            unsafe_allow_html=True)
        st.plotly_chart(ch.variogram(
            krig_r["h"], krig_r["gamma_emp"], krig_r["gamma_theo"],
            sill=krig_r["sill"], range_=krig_r["range_km"]),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Mapa de residuos post-kriging"), unsafe_allow_html=True)
        post = krig_r["df_per_mun"].copy()
        post["residual"] = post["pred_corregido"] - post["obs"]
        residual_map(post, residual_col="residual", height=400,
                      key=f"krig_resid_map_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(alert(
        f"<strong>Resumen técnico:</strong> el modelo lineal explica una parte "
        f"importante del rendimiento, pero deja estructura espacial sin capturar "
        f"(range ≈ {krig_r['range_km']:.0f} km). Aplicar kriging sobre los "
        f"residuos {'reduce' if delta > 0 else 'no reduce'} el RMSE en "
        f"<strong>{abs(delta):.1f}%</strong>. Esto valida la combinación "
        f"<em>modelo lineal interpretable + corrección espacial explícita</em> "
        f"como mejor estrategia que un modelo más complejo y opaco.",
        kind="ok" if delta > 0 else "amber",
    ), unsafe_allow_html=True)
