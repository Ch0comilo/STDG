"""Modelo Lineal — un solo modelo, interpretable, con todos los supuestos.

Decidimos quedarnos con regresión lineal (OLS + Ridge) en vez de árboles porque
es el modelo más interpretable y eso es lo que la audiencia de negocio necesita:
un coeficiente por variable, con su signo, su magnitud y su intervalo de confianza.

La página presenta:
  1. Rendimiento del modelo (métricas + α tuning).
  2. Coeficientes estandarizados → 'feature importance' lineal.
  3. Multicolinealidad (VIF).
  4. Diagnóstico de supuestos (linealidad, normalidad, homocedasticidad,
     independencia, autocorrelación espacial residual).
  5. Mapa de predicciones del modelo lineal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from theme import metric, card_header, alert, PALETTE
from data_loader import REGION_COLORS
from models import fit_linear, FEATURE_LABELS
from colombia_map import choropleth, residual_map
import charts as ch


def _assumption_card(title: str, value: str, ok: bool, msg: str) -> str:
    color = PALETTE["ok"] if ok else PALETTE["bad"]
    badge_text = "✓ CUMPLE" if ok else "✗ NO CUMPLE"
    return f"""
    <div style='background:{PALETTE["card"]}; border-radius:10px; padding:14px 16px;
                border-left:4px solid {color}; height:100%;'>
      <div style='display:flex; justify-content:space-between; align-items:center;
                  margin-bottom:6px;'>
        <span style='font-size:13px; font-weight:600; color:{PALETTE["text"]};'>{title}</span>
        <span style='font-family:IBM Plex Mono; font-size:11px; font-weight:700;
                      color:{color}; background:{color}22; padding:2px 8px;
                      border-radius:4px;'>{badge_text}</span>
      </div>
      <div style='font-family:IBM Plex Mono; font-size:14px; color:{color};
                  margin-bottom:6px; font-weight:600;'>{value}</div>
      <div style='font-size:12px; color:{PALETTE["text_dim"]}; line-height:1.55;'>{msg}</div>
    </div>
    """


def render(df, year: int, region: str) -> None:
    base = df if region == "Todas" else df[df["region"] == region]

    st.markdown(
        f"<h2 style='margin-top:0;'>Modelo Lineal · OLS + Ridge</h2>"
        f"<p style='font-size:14px; color:{PALETTE['text_dim']}; margin-bottom:18px;'>"
        f"Un solo modelo, interpretable. Coeficientes con p-valor e intervalos de "
        f"confianza, validación cruzada (aleatoria + espacial por departamento), "
        f"diagnóstico completo de supuestos.</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("Ajustando regresión lineal y validando supuestos…"):
        res = fit_linear(base, year)

    # ── KPI strip (predictive + inferencial) ─────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(metric("R² (CV)", f"{res.r2:.3f}",
                        color=PALETTE["accent_hi"],
                        sub=f"R² in-sample = {res.r2_in:.3f}"),
                 unsafe_allow_html=True)
    c2.markdown(metric("RMSE (CV aleat.)", f"{res.rmse:.3f}", "ton/ha",
                        color=PALETTE["amber"],
                        sub=f"MAE = {res.mae:.3f}"),
                 unsafe_allow_html=True)
    c3.markdown(metric("RMSE (CV espacial)", f"{res.rmse_spatial:.3f}", "ton/ha",
                        color=PALETTE["amber"],
                        sub="bloques por departamento"),
                 unsafe_allow_html=True)
    c4.markdown(metric("F-statistic", f"{res.f_stat:.1f}",
                        color=PALETTE["info"],
                        sub=f"p = {res.f_pvalue:.2e}"),
                 unsafe_allow_html=True)
    c5.markdown(metric("Ridge α* (CV)", f"{res.ridge_alpha:g}",
                        color=PALETTE["accent_hi"],
                        sub=f"n = {res.n_obs:,} · k = {res.n_features}"),
                 unsafe_allow_html=True)

    # ── Coefficients (feature importance) + observed vs predicted ──────
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Coeficientes estandarizados β · feature importance lineal"),
            unsafe_allow_html=True)
        st.plotly_chart(ch.coef_chart(res.coef_table, FEATURE_LABELS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']}; margin-top:4px;'>"
            f"Las barras muestran el efecto de mover cada variable una desviación "
            f"estándar — comparables entre sí. Las barritas finas son el intervalo "
            f"de confianza al 95%.</div></div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Observado vs predicho"), unsafe_allow_html=True)
        st.plotly_chart(ch.scatter_obs_pred(res.obs, res.pred),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── α-curve + coefficient table ─────────────────────────────────────
    left, right = st.columns([1, 1.4])
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            "Ajuste del hiperparámetro α (Ridge)"), unsafe_allow_html=True)
        st.plotly_chart(ch.alpha_curve(res.alpha_curve, res.ridge_alpha),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
            f"GridSearchCV 5-fold sobre escala logarítmica. α* minimiza el RMSE "
            f"de validación cruzada.</div></div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            "Tabla de coeficientes · OLS"), unsafe_allow_html=True)
        tbl = res.coef_table.copy()
        tbl["term"] = tbl["term"].map(
            lambda t: FEATURE_LABELS.get(t, t.replace("reg_", "Región ")))
        tbl = tbl.rename(columns={
            "term": "Variable", "beta_std": "β std.",
            "std_err": "SE", "t": "t", "p": "p-valor",
            "ci_lo": "CI 2.5%", "ci_hi": "CI 97.5%",
        })

        def _color_p(v):
            if pd.isna(v): return ""
            return ("color:#5ee08a; font-weight:600" if v < 0.05
                    else "color:#f0b34a" if v < 0.1 else "color:#94a39a")

        styled = (tbl.style
                   .format({"β std.": "{:+.3f}", "SE": "{:.3f}",
                             "t": "{:+.2f}", "p-valor": "{:.3g}",
                             "CI 2.5%": "{:+.3f}", "CI 97.5%": "{:+.3f}"})
                   .map(_color_p, subset=["p-valor"])
                   .set_properties(**{
                       "background-color": "transparent",
                       "font-family": "IBM Plex Mono, monospace",
                       "font-size": "13px",
                       "border": "1px solid rgba(255,255,255,0.06)",
                   }))
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
            f"Variables con p < 0.05 (verde) son estadísticamente significativas.</div></div>",
            unsafe_allow_html=True,
        )

    # ── Multicollinearity (VIF) on the FINAL model only ──────────────────
    st.markdown('<div class="agro-card">' + card_header(
        f"MULTICOLINEALIDAD · VIF DEL MODELO FINAL (umbral = {res.vif_threshold:.0f})"),
        unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])
    with left:
        st.plotly_chart(ch.vif_chart(res.vif, FEATURE_LABELS),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']}; margin-top:4px;'>"
            f"Las variables que aparecen aquí ya pasaron la reducción iterativa "
            f"de VIF — todas están por debajo del umbral.</div>",
            unsafe_allow_html=True,
        )
    with right:
        if res.dropped_features:
            c_card  = PALETTE["card"]
            c_text  = PALETTE["text"]
            c_dim   = PALETTE["text_dim"]
            c_bad   = PALETTE["bad"]
            c_amber = PALETTE["amber"]
            rows_html = ""
            for name, vif_drop, reason in res.dropped_features:
                lbl = FEATURE_LABELS.get(name, name.replace("reg_", "Región "))
                rows_html += (
                    f"<div style='display:flex; justify-content:space-between; "
                    f"padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.06);'>"
                    f"<span style='color:{c_text}; font-size:13px;'>"
                    f"<strong>{lbl}</strong></span>"
                    f"<span style='font-family:IBM Plex Mono; color:{c_bad}; "
                    f"font-size:12px;'>VIF inicial = {vif_drop:.1f}</span></div>"
                )
            n_drop = len(res.dropped_features)
            st.markdown(
                f"<div style='background:{c_card}; border-radius:10px; "
                f"padding:14px 16px; border-left:4px solid {c_amber};'>"
                f"<div style='font-size:12px; color:{c_amber}; "
                f"font-weight:700; text-transform:uppercase; letter-spacing:0.07em; "
                f"margin-bottom:8px;'>Variables eliminadas por colinealidad "
                f"({n_drop})</div>"
                f"{rows_html}"
                f"<div style='font-size:12px; color:{c_dim}; "
                f"line-height:1.6; margin-top:10px;'>"
                f"Se aplicó reducción iterativa de VIF: en cada paso se elimina la "
                f"variable con el VIF más alto y se recalcula hasta que ninguna "
                f"queda por encima del umbral.</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(alert(
                "El modelo nunca presentó colinealidad problemática — ninguna "
                f"variable superó VIF = {res.vif_threshold:.0f} en la matriz inicial.",
                kind="ok",
            ), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Assumption diagnostics ──────────────────────────────────────────
    st.markdown('<div class="agro-card">' + card_header(
        "DIAGNÓSTICO DE SUPUESTOS DEL MODELO LINEAL"), unsafe_allow_html=True)

    g1, g2, g3, g4, g5 = st.columns(5)
    # Linearity (Ramsey RESET)
    g1.markdown(_assumption_card(
        "Linealidad", f"RESET p = {res.reset_pvalue:.3g}",
        ok=(np.isnan(res.reset_pvalue) or res.reset_pvalue > 0.05),
        msg=("La relación entre predictores y rendimiento es razonablemente "
              "lineal.") if (np.isnan(res.reset_pvalue) or res.reset_pvalue > 0.05)
        else "Hay no-linealidades. Considera términos cuadráticos o splines.",
    ), unsafe_allow_html=True)
    # Independence (Durbin-Watson)
    dw_ok = 1.5 < res.durbin_watson < 2.5
    g2.markdown(_assumption_card(
        "Independencia", f"DW = {res.durbin_watson:.2f}",
        ok=dw_ok,
        msg=("Sin evidencia de autocorrelación residual de primer orden "
              "(DW cerca de 2).") if dw_ok else
              "Residuos correlacionados — esperable con datos espaciales.",
    ), unsafe_allow_html=True)
    # Homoscedasticity (Breusch-Pagan)
    bp_ok = (np.isnan(res.breusch_pagan_p) or res.breusch_pagan_p > 0.05)
    g3.markdown(_assumption_card(
        "Homocedasticidad", f"BP p = {res.breusch_pagan_p:.3g}",
        ok=bp_ok,
        msg=("Varianza de los residuos estable a lo largo de los valores "
              "predichos.") if bp_ok else
              "Heteroscedasticidad — usar errores robustos al reportar p-valores.",
    ), unsafe_allow_html=True)
    # Normality (Jarque-Bera)
    jb_ok = (np.isnan(res.jarque_bera_p) or res.jarque_bera_p > 0.05)
    g4.markdown(_assumption_card(
        "Normalidad", f"JB p = {res.jarque_bera_p:.3g}",
        ok=jb_ok,
        msg=("Residuos compatibles con distribución normal.") if jb_ok else
              "Cola pesada o asimetría — con n > 500 el TLC nos protege para los IC.",
    ), unsafe_allow_html=True)
    # Spatial autocorrelation
    moran = res.moran_residuos
    moran_ok = (np.isnan(moran) or abs(moran) < 0.10)
    moran_str = "n/d" if np.isnan(moran) else f"I = {moran:+.3f}"
    g5.markdown(_assumption_card(
        "Sin autocorr. espacial residual", moran_str,
        ok=moran_ok,
        msg=("Los errores no muestran patrón geográfico — el modelo captura "
              "la estructura espacial.") if moran_ok else
              "Patrón geográfico en los residuos: kriging residual puede mejorar la predicción.",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Diagnostic plots
    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="agro-card">' + card_header(
            "Residuos vs valores ajustados"), unsafe_allow_html=True)
        st.plotly_chart(ch.residuals_vs_fitted(res.fitted, res.residuals),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
            f"Una banda horizontal alrededor de 0 indica linealidad y "
            f"homocedasticidad. La curva verde es el promedio local.</div></div>",
            unsafe_allow_html=True,
        )
    with p2:
        st.markdown('<div class="agro-card">' + card_header(
            "Q-Q plot · normalidad de residuos"), unsafe_allow_html=True)
        st.plotly_chart(ch.qq_plot(res.standardized_residuals),
                         use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px; color:{PALETTE['text_dimmer']};'>"
            f"Los puntos cerca de la línea ⇒ residuos normales. "
            f"Shapiro p = {res.shapiro_p:.3g}, JB p = {res.jarque_bera_p:.3g}.</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Maps: prediction + residuals ────────────────────────────────────
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="agro-card">' + card_header(
            f"Mapa de PREDICCIÓN del modelo · {year}"), unsafe_allow_html=True)
        pred_df = res.df_pred.copy()
        pred_df["rendimiento"] = pred_df["pred"]
        pred_df["anio"] = year
        choropleth(pred_df, value_key="rendimiento", year=year,
                    height=440, key=f"modelo_pred_map_{year}_{region}",
                    caption="Predicción modelo lineal (ton/ha)")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="agro-card">' + card_header(
            f"Mapa de RESIDUOS · pred − obs · {year}"), unsafe_allow_html=True)
        residual_map(res.df_pred, residual_col="residual",
                      height=440, key=f"modelo_resid_map_{year}_{region}",
                      caption="Residuo (pred − obs) ton/ha")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Closing business insight ──────────────────────────────────────────
    sig_terms = res.coef_table[
        (res.coef_table["term"] != "const") & (res.coef_table["p"] < 0.05)
    ].copy()
    if not sig_terms.empty:
        sig_terms["abs"] = sig_terms["beta_std"].abs()
        sig_terms = sig_terms.sort_values("abs", ascending=False).head(3)
        bullets = []
        for _, row in sig_terms.iterrows():
            lbl = FEATURE_LABELS.get(row["term"], row["term"].replace("reg_", "Región "))
            sign = "↑" if row["beta_std"] > 0 else "↓"
            bullets.append(
                f"<li><strong>{lbl}</strong> {sign} (β = {row['beta_std']:+.2f}, "
                f"p = {row['p']:.3g})</li>"
            )
        st.markdown(alert(
            f"<strong style='color:{PALETTE['accent_hi']}'>Lectura del modelo</strong>"
            f" — las tres variables más influyentes en el rendimiento son:"
            f"<ul style='margin:8px 0 0 18px;'>{''.join(bullets)}</ul>",
        ), unsafe_allow_html=True)
