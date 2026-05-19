"""Panorama — business view. KPIs, kriging-filled map, regional pies.

This page used to be technical EDA. We now lead with the question every
stakeholder asks: ¿quién produce maíz, dónde rinde mejor, y dónde estamos
volando a ciegas? The kriging fill answers the last one — instead of leaving
600+ municipios en negro, mostramos un estimado con varianza.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import filter_data, REGIONES, REGION_COLORS
from colombia_map import choropleth
from kriging_engine import krige_yield_full
import charts as ch


def render(df, year: int, region: str) -> None:
    sub = filter_data(df, year=year, region=region)

    st.markdown(
        f"<h2 style='margin-top:0;'>Panorama de producción · {year}</h2>"
        f"<p style='font-size:14px; color:{PALETTE['text_dim']}; margin-bottom:18px;'>"
        f"Vista de negocio del rendimiento de maíz en Colombia · "
        f"{len(sub):,} observaciones · región <strong>{region}</strong></p>",
        unsafe_allow_html=True,
    )

    if sub.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    # ── KPIs business-first ──────────────────────────────────────────────
    avg = sub["rendimiento"].mean()
    total_prod = sub["produccion"].sum()
    total_area = sub["area_sembrada"].sum()
    n = sub["dane_code"].nunique()
    # Year-over-year delta
    prev = df[df["anio"] == year - 1]
    if region != "Todas":
        prev = prev[prev["region"] == region]
    delta_avg = avg - prev["rendimiento"].mean() if not prev.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    delta_sub = (f"{delta_avg:+.2f} vs {year-1}"
                 if not prev.empty else "—")
    c1.markdown(metric("Rendimiento promedio", f"{avg:.2f}", "ton/ha",
                        color=PALETTE["accent_hi"], sub=delta_sub),
                 unsafe_allow_html=True)
    c2.markdown(metric("Producción total", f"{total_prod/1000:,.0f}", "×10³ ton",
                        color=PALETTE["amber"],
                        sub=f"{total_area/1000:,.0f} ×10³ ha sembradas"),
                 unsafe_allow_html=True)
    top_row = sub.sort_values("rendimiento", ascending=False).iloc[0]
    c3.markdown(metric("Municipio líder", f"{top_row['rendimiento']:.2f}", "ton/ha",
                        color=PALETTE["accent_hi"],
                        sub=f"{top_row['municipio'][:24]}"),
                 unsafe_allow_html=True)
    c4.markdown(metric("Municipios con dato", f"{n:,}", "muns",
                        color=PALETTE["info"],
                        sub=f"de 1 120 total · {n/11.2:.0f}% cobertura"),
                 unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Map: observado + kriging para los faltantes ──────────────────────
    base_for_krig = df if region == "Todas" else df[df["region"] == region]
    with st.spinner("Krigeando rendimiento para municipios sin observación…"):
        krig = krige_yield_full(base_for_krig, year)

    if not krig["df_filled"].empty:
        # Build a {dane_code: value} dict for the choropleth
        df_filled = krig["df_filled"]
        value_map = dict(zip(df_filled["dane_code"], df_filled["rendimiento_krig"]))
        n_obs = krig["n_obs"]
        n_filled = krig["n_filled"]
        rmse_loo = krig["rmse_loo"]

        st.markdown('<div class="agro-card">' + card_header(
            f"MAPA NACIONAL · RENDIMIENTO COMPLETADO POR KRIGING · {year}"),
            unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:13px; color:{PALETTE['text_dim']}; margin-bottom:10px;'>"
            f"<strong style='color:{PALETTE['accent_hi']}'>{n_obs:,}</strong> "
            f"municipios con dato observado · "
            f"<strong style='color:{PALETTE['amber']}'>{n_filled:,}</strong> "
            f"interpolados con kriging ordinario "
            f"(RMSE leave-one-out = <strong>{rmse_loo:.3f}</strong> ton/ha)</p>",
            unsafe_allow_html=True,
        )
        choropleth(sub, value_key="rendimiento", year=year,
                    height=520, key=f"pano_map_{year}_{region}",
                    value_map_override=value_map,
                    caption=f"Rendimiento {year} (ton/ha) · kriging fill",
                    unit="ton/ha")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="agro-card">' + card_header(
            f"MAPA NACIONAL · RENDIMIENTO ton/ha · {year}"),
            unsafe_allow_html=True)
        choropleth(sub, value_key="rendimiento", year=year,
                    height=520, key=f"pano_map_basic_{year}_{region}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Pies + ranking ───────────────────────────────────────────────────
    left, mid, right = st.columns([1, 1, 1.1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"Participación de producción por región · {year}"),
            unsafe_allow_html=True)
        st.plotly_chart(ch.region_pie(sub, REGION_COLORS, value_col="produccion"),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with mid:
        st.markdown('<div class="agro-card">' + card_header(
            f"Rendimiento promedio por región · {year}"),
            unsafe_allow_html=True)
        st.plotly_chart(ch.region_bars(sub, REGION_COLORS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(f"TOP 10 municipios · {year}"),
                     unsafe_allow_html=True)
        st.plotly_chart(ch.ranking(sub, year, top=10, mode="top"),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Treemap + time series ─────────────────────────────────────────────
    left, right = st.columns([1, 1.2])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"Treemap de producción · top departamentos · {year}"),
            unsafe_allow_html=True)
        st.plotly_chart(ch.depto_treemap(sub, value_col="produccion", top=18),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Serie histórica · rendimiento nacional y por región"),
            unsafe_allow_html=True)
        base = df if region == "Todas" else df[df.region == region]
        st.plotly_chart(ch.time_series(base, REGIONES, REGION_COLORS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Insight callout ───────────────────────────────────────────────────
    best_region = (sub.groupby("region")["rendimiento"].mean()
                       .sort_values(ascending=False))
    if len(best_region) >= 2:
        top_r = best_region.index[0]; top_v = best_region.iloc[0]
        bot_r = best_region.index[-1]; bot_v = best_region.iloc[-1]
        gap = (top_v - bot_v) / max(bot_v, 1e-6) * 100
        st.markdown(alert(
            f"<strong style='color:{PALETTE['accent_hi']}'>Brecha territorial · {gap:.0f}%</strong>"
            f" — la región <strong>{top_r}</strong> rinde "
            f"<strong>{top_v:.2f} ton/ha</strong> en promedio, "
            f"vs <strong>{bot_v:.2f} ton/ha</strong> en <strong>{bot_r}</strong>. "
            f"Ese delta es el punto de partida para priorizar asistencia técnica "
            f"y entender qué prácticas funcionan en la cabeza del ranking.",
        ), unsafe_allow_html=True)
