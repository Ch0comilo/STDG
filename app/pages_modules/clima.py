"""Clima & Territorio — relación clima ↔ rendimiento.

Mostramos precipitación, temperatura y ENSO contra el rendimiento, para responder
'¿qué tan determinante es la lluvia en el rendimiento del maíz?'. Va antes del
modelo para que la audiencia llegue a la regresión con intuición previa.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import filter_data, REGIONES, REGION_COLORS
from colombia_map import choropleth
import charts as ch


def _corr(x, y):
    """Pearson r ignoring NaNs."""
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 5:
        return float("nan")
    return float(np.corrcoef(x[m], y[m])[0, 1])


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]

    st.markdown(
        f"<h2 style='margin-top:0;'>Clima & Territorio</h2>"
        f"<p style='font-size:14px; color:{PALETTE['text_dim']}; margin-bottom:18px;'>"
        f"¿Cuánto pesan la lluvia, la temperatura y el fenómeno ENSO en el rendimiento "
        f"del maíz? Aquí miramos esas relaciones antes de pasar al modelo.</p>",
        unsafe_allow_html=True,
    )

    has_climate = all(c in base.columns for c in ["prcp_anual", "tmed_anual"])
    if not has_climate:
        st.warning("Las variables climáticas aún no están disponibles. "
                    "Limpia caché de Streamlit y vuelve a abrir la app.")
        return

    sub = filter_data(base, year=year)

    # ── KPI strip ─────────────────────────────────────────────────────────
    avg_prcp = sub["prcp_anual"].mean()
    avg_tmed = sub["tmed_anual"].mean()
    avg_enso = sub.get("enso_anual", pd.Series([np.nan])).mean()
    avg_yield = sub["rendimiento"].mean()

    enso_label = "—" if pd.isna(avg_enso) else f"{avg_enso:+.2f}"
    enso_color = (PALETTE["bad"] if avg_enso > 0.5 else
                   PALETTE["info"] if avg_enso < -0.5 else PALETTE["text_dim"])
    enso_sub = (f"Niño fuerte" if avg_enso > 0.5 else
                f"Niña fuerte" if avg_enso < -0.5 else "Neutro / leve")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Precipitación anual", f"{avg_prcp:,.0f}", "mm",
                        color=PALETTE["info"],
                        sub="promedio municipios con maíz"),
                 unsafe_allow_html=True)
    c2.markdown(metric("Temperatura media", f"{avg_tmed:.1f}", "°C",
                        color=PALETTE["amber"]),
                 unsafe_allow_html=True)
    c3.markdown(metric("ENSO Niño 3.4", enso_label, "",
                        color=enso_color, sub=enso_sub),
                 unsafe_allow_html=True)
    c4.markdown(metric("Rendimiento promedio", f"{avg_yield:.2f}", "ton/ha",
                        color=PALETTE["accent_hi"]),
                 unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Correlation strip ─────────────────────────────────────────────────
    r_prcp = _corr(base["prcp_anual"].values, base["rendimiento"].values)
    r_tmed = _corr(base["tmed_anual"].values, base["rendimiento"].values)
    r_enso = (_corr(base["enso_anual"].values, base["rendimiento"].values)
              if "enso_anual" in base.columns else float("nan"))

    def _r_msg(r, name):
        if np.isnan(r): return f"{name}: sin datos suficientes."
        strength = ("fuerte" if abs(r) > 0.4 else
                    "moderada" if abs(r) > 0.2 else "débil")
        direction = "positiva" if r > 0 else "negativa"
        return (f"<strong style='color:{PALETTE['accent_hi']}'>{name}</strong> · "
                f"r = <strong>{r:+.2f}</strong> · correlación {strength} {direction}")

    st.markdown(alert(
        " · ".join([_r_msg(r_prcp, "Precipitación"),
                     _r_msg(r_tmed, "Temperatura"),
                     _r_msg(r_enso, "ENSO")])
    ), unsafe_allow_html=True)

    # ── Scatter de clima vs rendimiento ──────────────────────────────────
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Precipitación anual vs rendimiento"), unsafe_allow_html=True)
        st.plotly_chart(
            ch.climate_scatter(base, "prcp_anual", "Precipitación anual (mm)",
                                REGION_COLORS),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Temperatura media vs rendimiento"), unsafe_allow_html=True)
        st.plotly_chart(
            ch.climate_scatter(base, "tmed_anual", "Temperatura media (°C)",
                                REGION_COLORS),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── ENSO series & precipitation series ────────────────────────────────
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Precipitación anual · serie nacional"), unsafe_allow_html=True)
        st.plotly_chart(
            ch.climate_timeseries(base, "prcp_anual", "mm/año",
                                    color=PALETTE["info"]),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Índice ENSO Niño 3.4 · serie anual"), unsafe_allow_html=True)
        if "enso_anual" in base.columns:
            st.plotly_chart(
                ch.climate_timeseries(base, "enso_anual", "ENSO 3.4",
                                        color=PALETTE["amber"]),
                use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Serie ENSO no disponible en este dataset.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Mapa de precipitación promedio ────────────────────────────────────
    st.markdown('<div class="agro-card">' + card_header(
        f"Mapa de precipitación promedio anual · {year}"),
        unsafe_allow_html=True)
    choropleth(sub, value_key="prcp_anual", year=year,
                height=460, key=f"prcp_map_{year}_{region}",
                caption="Precipitación (mm/año)", unit="mm")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(alert(
        f"<strong>Lectura de negocio:</strong> el coeficiente de correlación entre "
        f"precipitación y rendimiento es r = {r_prcp:+.2f}. "
        f"{'La lluvia explica una parte importante de las diferencias entre municipios.' if abs(r_prcp) > 0.25 else 'La lluvia sola no alcanza para explicar las diferencias — el modelo combinará clima, ubicación y escala de siembra.'}"
        f" Esto justifica incluir clima en el modelo y revisar resultados ENSO año por año.",
        kind="amber",
    ), unsafe_allow_html=True)
