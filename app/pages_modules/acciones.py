"""Acciones Concretas — identificación de oportunidades de mejora y casos de éxito."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from theme import card_header, PALETTE, metric
from data_loader import filter_data
from models import train_model
from charts import styled

def render(df, year: int, region: str) -> None:
    st.markdown(
        f"<h2 style='margin-top:0; font-size:20px;'>Acciones Concretas e Insights</h2>"
        f"<p style='font-size:12px; color:{PALETTE['text_dim']}; margin-bottom:14px;'>"
        f"Identificación de municipios con rendimiento anómalo respecto al modelo predictivo (XGBoost) "
        f"· año {year} · región {region}</p>",
        unsafe_allow_html=True,
    )

    base = df if region == "Todas" else df[df["region"] == region]
    
    with st.spinner("Analizando desviaciones del modelo…"):
        # Use XGBoost as it's usually the most sensitive/best
        res = train_model(base, year, "XGBoost")

    df_res = res.df_pred.copy()
    # Residual = Obs - Pred. 
    # Positive residual: Municipiio produced MORE than expected (Success case)
    # Negative residual: Municipio produced LESS than expected (Opportunity for improvement)
    
    success = df_res.sort_values("residual", ascending=False).head(10)
    improvement = df_res.sort_values("residual", ascending=True).head(10)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="agro-card" style="border-left:4px solid #4ade80">' + card_header(
            "CASOS DE ÉXITO — Rendimiento superior al esperado"), unsafe_allow_html=True)
        st.markdown("<p style='font-size:11px; color:#9ca3af; margin-bottom:10px;'>"
                    "Municipios que superan las predicciones del modelo. Candidatos para estudio de buenas prácticas.</p>", 
                    unsafe_allow_html=True)
        
        for _, row in success.iterrows():
            st.markdown(f"""
                <div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);'>
                    <div style='font-size:12px;'>
                        <strong>{row['municipio']}</strong> <span style='color:#6b7280; font-size:10px;'>({row['departamento'][:10]})</span>
                    </div>
                    <div style='font-family:IBM Plex Mono; font-size:12px; color:#4ade80;'>
                        +{row['residual']:.2f} ton/ha
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="agro-card" style="border-left:4px solid #ef4444">' + card_header(
            "OPORTUNIDADES — Rendimiento inferior al esperado"), unsafe_allow_html=True)
        st.markdown("<p style='font-size:11px; color:#9ca3af; margin-bottom:10px;'>"
                    "Municipios que rinden menos de lo que sus condiciones sugieren. Prioridad para asistencia técnica.</p>", 
                    unsafe_allow_html=True)
        
        for _, row in improvement.iterrows():
            st.markdown(f"""
                <div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);'>
                    <div style='font-size:12px;'>
                        <strong>{row['municipio']}</strong> <span style='color:#6b7280; font-size:10px;'>({row['departamento'][:10]})</span>
                    </div>
                    <div style='font-family:IBM Plex Mono; font-size:12px; color:#ef4444;'>
                        {row['residual']:.2f} ton/ha
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="agro-card">' + card_header(
        "RESUMEN ESTRATÉGICO"), unsafe_allow_html=True)
    
    avg_yield = df_res["obs"].mean()
    potential_gain = -improvement["residual"].mean()
    
    cols = st.columns(3)
    cols[0].markdown(metric("Rendimiento Promedio", f"{avg_yield:.2f}", "ton/ha"), unsafe_allow_html=True)
    cols[1].markdown(metric("Brecha en Oportunidades", f"{potential_gain:.2f}", "ton/ha", color="#ef4444"), unsafe_allow_html=True)
    cols[2].markdown(metric("Municipios Analizados", f"{len(df_res)}", "muns", color=PALETTE["accent"]), unsafe_allow_html=True)

    st.markdown(f"""
        <div style='margin-top:15px; font-size:12px; line-height:1.6; color:{PALETTE["text_dim"]}'>
            <p><strong>Acción 1:</strong> Focalizar programas de fertilización y riego en los 10 municipios de la columna derecha, 
            donde la brecha respecto al potencial es de <strong>{potential_gain:.2f} ton/ha</strong>.</p>
            <p><strong>Acción 2:</strong> Realizar misiones de campo en <strong>{success.iloc[0]['municipio']}</strong> para documentar 
            factores locales (semillas, clima, técnicas) que explican el sobre-rendimiento de <strong>{success.iloc[0]['residual']:.2f} ton/ha</strong>.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
