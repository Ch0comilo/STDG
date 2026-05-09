"""EDA Espacial — choropleth, ranking, time series, heatmap."""
from __future__ import annotations

import streamlit as st

from theme import metric, card_header, PALETTE
from data_loader import filter_data, REGIONES, REGION_COLORS, years_available
from colombia_map import choropleth
import charts as ch


def render(df, year: int, region: str) -> None:
    sub = filter_data(df, year=year, region=region)

    st.markdown(
        f"<h2 style='margin-top:0; font-size:20px;'>EDA Espacial</h2>"
        f"<p style='font-size:12px; color:{PALETTE['text_dim']}; margin-bottom:16px;'>"
        f"Exploración geoespacial del rendimiento municipal de maíz · "
        f"datos AGRONET-EVA · {len(sub):,} observaciones para {year}</p>",
        unsafe_allow_html=True,
    )

    # KPIs
    if sub.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return
    avg = sub["rendimiento"].mean()
    total_prod = sub["produccion"].sum() / 1000
    top = sub.sort_values("rendimiento", ascending=False).iloc[0]
    n = sub["dane_code"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Rendimiento promedio", f"{avg:.2f}", "ton/ha"), unsafe_allow_html=True)
    c2.markdown(metric("Producción total", f"{total_prod:,.0f}", "×10³ ton",
                        color=PALETTE["amber"]), unsafe_allow_html=True)
    c3.markdown(metric("Municipio top", f"{top['rendimiento']:.2f}", "ton/ha",
                        color=PALETTE["accent_hi"]), unsafe_allow_html=True)
    c4.markdown(metric("Municipios", f"{n}", "muns",
                        color=PALETTE["text_dim"]), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Map + region bars / scatter row
    left, right = st.columns([1.2, 1])
    with left:
        with st.container(border=False):
            st.markdown('<div class="agro-card">' + card_header(
                f"MAPA COROPLÉTICO — Rendimiento ton/ha · {year}"), unsafe_allow_html=True)
            event = choropleth(sub, value_key="rendimiento", year=None,
                                height=460, key=f"eda_map_{year}_{region}")
            st.markdown('</div>', unsafe_allow_html=True)
            if event and event.get("last_object_clicked"):
                clicked = event["last_object_clicked"]
                st.session_state["last_click"] = clicked

    with right:
        st.markdown('<div class="agro-card">' + card_header(
            f"Rendimiento promedio por región · {year}"), unsafe_allow_html=True)
        st.plotly_chart(ch.region_bars(sub, REGION_COLORS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="agro-card">' + card_header(
            "Rendimiento vs Latitud (proxy climático)"), unsafe_allow_html=True)
        st.plotly_chart(ch.precip_vs_rendim(sub, REGION_COLORS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Time series + ranking
    left, right = st.columns([1.6, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"SERIE HISTÓRICA — rendimiento nacional y por región"), unsafe_allow_html=True)
        st.plotly_chart(ch.time_series(df if region == "Todas" else df[df.region == region],
                                         REGIONES, REGION_COLORS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(f"TOP 10 · {year}"),
                     unsafe_allow_html=True)
        st.plotly_chart(ch.ranking(sub, year, top=10, mode="top"),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Heatmap
    st.markdown('<div class="agro-card">' + card_header(
        "HEATMAP — rendimiento por municipio y año (Top 22 nacional)"),
        unsafe_allow_html=True)
    base = df if region == "Todas" else df[df.region == region]
    st.plotly_chart(ch.heatmap_top(base, top=22),
                     use_container_width=True, config={"displayModeBar": False})
    dimmer = PALETTE["text_dimmer"]
    st.markdown(f"<div style='font-size:11px; color:{dimmer}; margin-top:6px;'>"
                f"Pasa el cursor sobre cualquier celda para ver el dato exacto.</div></div>",
                unsafe_allow_html=True)
