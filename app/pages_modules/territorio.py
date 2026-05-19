"""Territorio — análisis socio-económico con datos TerriData.

Cinco visualizaciones de negocio que conectan los indicadores territoriales
(energía rural, banda ancha, uso del suelo, recaudo predial, ingresos fiscales)
con el rendimiento del maíz. Pensadas para responder preguntas accionables:

  · ¿La electrificación rural ayuda al rendimiento?
  · ¿Qué municipios producen mucho y aún no tienen banda ancha? → candidatos AgTech
  · ¿En qué regiones el suelo está sobreutilizado vs bien usado?
  · ¿Qué indicador correlaciona más con productividad?
  · ¿Cómo se compara cada región en su 'huella territorial'?
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import filter_data, REGION_COLORS
from colombia_map import choropleth
import charts as ch


TERRIDATA_LABELS = {
    "cob_energia_rural": "Cobertura energía rural (%)",
    "banda_ancha":       "Penetración banda ancha (%)",
    "ingresos_totales":  "Ingresos totales (COP)",
    "uso_adecuado_pct":  "Uso adecuado del suelo (%)",
    "sobreutil_pct":     "Sobreutilización del suelo (%)",
    "recaudo_predial":   "Recaudo predial (%)",
}


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]
    # For municipality-level analysis use the latest observed year per muni
    latest = (base.sort_values("anio")
                   .drop_duplicates("dane_code", keep="last")
                   .copy())

    st.markdown(
        f"<h2 style='margin-top:0;'>Territorio · Análisis Socio-Económico</h2>"
        f"<p style='font-size:14px; color:{PALETTE['text_dim']}; margin-bottom:18px;'>"
        f"Indicadores de DNP-TerriData: electrificación rural, conectividad, uso del "
        f"suelo, fiscalidad municipal. Conectamos cada variable con el rendimiento "
        f"para detectar oportunidades y brechas territoriales.</p>",
        unsafe_allow_html=True,
    )

    # ── KPI strip — promedios nacionales ─────────────────────────────────
    avg_en = latest["cob_energia_rural"].mean()
    avg_ba = latest["banda_ancha"].mean()
    avg_uso = latest["uso_adecuado_pct"].mean()
    avg_sob = latest["sobreutil_pct"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric("Energía rural promedio", f"{avg_en:.0f}", "%",
                        color=PALETTE["amber"],
                        sub="cobertura municipal"),
                 unsafe_allow_html=True)
    c2.markdown(metric("Banda ancha promedio", f"{avg_ba:.1f}", "%",
                        color=PALETTE["info"],
                        sub="penetración hogares"),
                 unsafe_allow_html=True)
    c3.markdown(metric("Uso adecuado del suelo", f"{avg_uso:.0f}", "%",
                        color=PALETTE["accent_hi"],
                        sub="área en uso compatible"),
                 unsafe_allow_html=True)
    c4.markdown(metric("Sobreutilización", f"{avg_sob:.0f}", "%",
                        color=PALETTE["bad"],
                        sub="área sobreexplotada"),
                 unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Decile bars: ¿la electrificación rural mueve el rendimiento? ─────
    st.markdown('<div class="agro-card">' + card_header(
        "¿La cobertura eléctrica rural mueve el rendimiento del maíz?"),
        unsafe_allow_html=True)
    st.plotly_chart(
        ch.decile_bars(latest, "cob_energia_rural",
                        "cobertura energía rural"),
        use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"<div style='font-size:13px; color:{PALETTE['text_dim']}; "
        f"line-height:1.6; margin-top:6px;'>"
        f"Cada barra es el promedio de rendimiento de los municipios agrupados "
        f"en deciles según su cobertura de energía rural. Si la línea sube "
        f"de izquierda a derecha, la electrificación se asocia con mayor "
        f"productividad — un dato que sirve para priorizar inversión rural.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Strategic quadrant: banda ancha × rendimiento ─────────────────────
    st.markdown('<div class="agro-card">' + card_header(
        "Cuadrante estratégico · banda ancha × rendimiento"),
        unsafe_allow_html=True)
    st.plotly_chart(
        ch.strategic_quadrant(latest,
                               x_col="banda_ancha", y_col="rendimiento",
                               x_label="Penetración banda ancha (%)",
                               y_label="Rendimiento (ton/ha)"),
        use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"<div style='font-size:13px; color:{PALETTE['text_dim']}; "
        f"line-height:1.6; margin-top:6px;'>"
        f"Los <strong style='color:{PALETTE['amber']}'>amarillos</strong> son "
        f"<strong>candidatos AgTech</strong>: producen alto sin conectividad. "
        f"Los <strong style='color:{PALETTE['accent_hi']}'>verdes</strong> son "
        f"los ganadores. Los <strong style='color:{PALETTE['bad']}'>rojos</strong> "
        f"son la brecha estructural — bajos en ambos ejes. Los "
        f"<strong style='color:{PALETTE['info']}'>azules</strong> tienen recursos "
        f"pero no rinden — vale la pena entender por qué.</div></div>",
        unsafe_allow_html=True,
    )

    # ── Opportunity table: high yield + low connectivity ──────────────────
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Oportunidad AgTech · top productores SIN banda ancha"),
            unsafe_allow_html=True)
        st.plotly_chart(
            ch.opportunity_lollipop(latest,
                                     x_col="banda_ancha",
                                     y_col="rendimiento",
                                     x_label="Banda ancha (%)",
                                     y_label="Rend. (ton/ha)",
                                     top=12),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:13px; color:{PALETTE['text_dim']}; "
            f"line-height:1.6;'>"
            f"Municipios en el cuartil superior de rendimiento Y en el cuartil "
            f"inferior de banda ancha. Si una entidad va a invertir en "
            f"conectividad rural, estos rinden y aún no tienen el insumo.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Radar territorial por región"), unsafe_allow_html=True)
        radar_cols = ["cob_energia_rural", "banda_ancha", "uso_adecuado_pct",
                       "recaudo_predial", "rendimiento"]
        st.plotly_chart(
            ch.territorial_radar(latest, radar_cols, {**TERRIDATA_LABELS,
                                  "rendimiento": "Rendimiento"},
                                  group_col="region",
                                  region_colors=REGION_COLORS),
            use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
            f"Cada eje normalizado 0-1. Un polígono más amplio = región más "
            f"fuerte en esa combinación de dimensiones.</div></div>",
            unsafe_allow_html=True,
        )

    # ── Land-use maps ────────────────────────────────────────────────────
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Mapa · % del suelo en USO ADECUADO"),
            unsafe_allow_html=True)
        choropleth(latest, value_key="uso_adecuado_pct", year=None,
                    height=420, key=f"terri_uso_map_{year}_{region}",
                    caption="Uso adecuado (%)", unit="%")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Mapa · % del suelo SOBREUTILIZADO"),
            unsafe_allow_html=True)
        choropleth(latest, value_key="sobreutil_pct", year=None,
                    height=420, key=f"terri_sobre_map_{year}_{region}",
                    caption="Sobreutilización (%)", unit="%")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Correlation heatmap ─────────────────────────────────────────────
    st.markdown('<div class="agro-card">' + card_header(
        "Matriz de correlación · TerriData × rendimiento"),
        unsafe_allow_html=True)
    corr_cols = list(TERRIDATA_LABELS.keys())
    st.plotly_chart(
        ch.correlation_heatmap(latest, corr_cols, TERRIDATA_LABELS,
                                target="rendimiento"),
        use_container_width=True, config={"displayModeBar": False})

    # Pull the strongest correlation for the insight
    use = latest[corr_cols + ["rendimiento"]].dropna()
    if not use.empty:
        corr = use.corr()["rendimiento"].drop("rendimiento").sort_values(
            key=lambda s: s.abs(), ascending=False)
        if len(corr) > 0:
            best_var = corr.index[0]
            best_r = corr.iloc[0]
            best_lbl = TERRIDATA_LABELS.get(best_var, best_var)
            direction = "positivamente" if best_r > 0 else "negativamente"
            st.markdown(alert(
                f"<strong style='color:{PALETTE['accent_hi']}'>Lectura de negocio</strong>"
                f" — el indicador TerriData más correlacionado con el rendimiento "
                f"del maíz es <strong>{best_lbl}</strong> "
                f"(r = <strong>{best_r:+.2f}</strong>, correlación {direction}). "
                f"Esto justifica incluirlo en el modelo lineal y vigilarlo como "
                f"palanca de política pública.",
                kind="ok" if abs(best_r) > 0.15 else "amber",
            ), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
