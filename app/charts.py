"""Plotly chart helpers — bigger fonts, more variety, business-focused."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as sps

from theme import PALETTE, PLOTLY_LAYOUT, CHORO_SCALE, DIVERGING_SCALE, CAT_PALETTE


def styled(fig: go.Figure, height: int | None = None) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    if height:
        fig.update_layout(height=height)
    return fig


# ─── exploration ─────────────────────────────────────────────────────────────

def time_series(df: pd.DataFrame, regions: list[str], region_colors: dict) -> go.Figure:
    nat = df.groupby("anio", as_index=False)["rendimiento"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nat["anio"], y=nat["rendimiento"], name="Nacional",
        mode="lines+markers",
        line=dict(color=PALETTE["accent_hi"], width=3),
        marker=dict(size=9, color=PALETTE["accent_hi"],
                    line=dict(color=PALETTE["bg"], width=1.5)),
        fill="tozeroy", fillcolor="rgba(94,224,138,0.12)",
    ))
    for r in regions:
        rdf = df[df["region"] == r].groupby("anio", as_index=False)["rendimiento"].mean()
        if rdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=rdf["anio"], y=rdf["rendimiento"], name=r,
            mode="lines",
            line=dict(color=region_colors.get(r, "#888"), width=2, dash="dot"),
            opacity=0.85,
        ))
    fig.update_layout(
        height=300, xaxis_title=None, yaxis_title="Rendimiento (ton/ha)",
        legend=dict(orientation="h", y=-0.18, x=0),
    )
    return styled(fig)


def ranking(df: pd.DataFrame, year: int, top: int = 10, mode: str = "top") -> go.Figure:
    yd = df[df["anio"] == year]
    sorted_ = yd.sort_values("rendimiento", ascending=(mode != "top")).head(top)
    sorted_ = sorted_.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=sorted_["rendimiento"],
        y=sorted_["municipio"] + " · " + sorted_["departamento"].str[:12],
        orientation="h",
        marker=dict(color=sorted_["rendimiento"],
                    colorscale=CHORO_SCALE, showscale=False),
        text=[f"{v:.2f}" for v in sorted_["rendimiento"]],
        textposition="outside",
        textfont=dict(size=12),
        hovertemplate="<b>%{y}</b><br>%{x:.3f} ton/ha<extra></extra>",
    ))
    fig.update_layout(
        height=28 * top + 50,
        xaxis_title="ton/ha", yaxis_title=None,
        margin={"l": 10, "r": 30, "t": 10, "b": 30},
    )
    return styled(fig)


def heatmap_top(df: pd.DataFrame, top: int = 20) -> go.Figure:
    avg = (df.groupby(["dane_code", "municipio"], as_index=False)["rendimiento"].mean()
             .sort_values("rendimiento", ascending=False).head(top))
    sub = df[df["dane_code"].isin(avg["dane_code"])]
    pivot = sub.pivot_table(index="municipio", columns="anio",
                             values="rendimiento", aggfunc="mean")
    pivot = pivot.loc[avg["municipio"].values]
    z = pivot.values
    text = [[f"{v:.1f}" if not np.isnan(v) else "" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=pivot.columns.astype(str), y=pivot.index,
        colorscale=CHORO_SCALE, showscale=True,
        text=text, texttemplate="%{text}",
        textfont=dict(size=11, family="IBM Plex Mono, monospace"),
        hovertemplate="<b>%{y}</b><br>Año %{x}<br>%{z:.2f} ton/ha<extra></extra>",
        colorbar=dict(thickness=12, len=0.7, x=1.01,
                       tickfont=dict(color="#cbd5d0", size=11)),
    ))
    fig.update_layout(
        height=26 * top + 90, xaxis_title=None, yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        margin={"l": 0, "r": 40, "t": 24, "b": 36},
    )
    return styled(fig)


def region_bars(df: pd.DataFrame, region_colors: dict) -> go.Figure:
    avg = (df.groupby("region", as_index=False)["rendimiento"].mean()
             .sort_values("rendimiento"))
    fig = go.Figure(go.Bar(
        x=avg["rendimiento"], y=avg["region"], orientation="h",
        marker=dict(color=[region_colors.get(r, "#888") for r in avg["region"]],
                    opacity=0.92),
        text=[f"{v:.2f}" for v in avg["rendimiento"]], textposition="outside",
        textfont=dict(size=13),
    ))
    fig.update_layout(height=220, xaxis_title="ton/ha", yaxis_title=None,
                      margin={"l": 10, "r": 40, "t": 14, "b": 30})
    return styled(fig)


# ─── pie & treemap ───────────────────────────────────────────────────────────

def region_pie(df: pd.DataFrame, region_colors: dict,
                value_col: str = "produccion") -> go.Figure:
    """Pie of regional share of production (or any column)."""
    agg = df.groupby("region", as_index=False)[value_col].sum()
    fig = go.Figure(go.Pie(
        labels=agg["region"], values=agg[value_col],
        hole=0.45,
        marker=dict(colors=[region_colors.get(r, "#888") for r in agg["region"]],
                    line=dict(color=PALETTE["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=13, color=PALETTE["text"]),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} ton<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=320,
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        annotations=[dict(
            text=f"<b>{agg[value_col].sum():,.0f}</b><br><span style='font-size:11px;color:{PALETTE['text_dim']}'>ton totales</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=15, color=PALETTE["accent_hi"], family="IBM Plex Mono"),
        )],
    )
    return styled(fig)


def lisa_pie(counts: dict) -> go.Figure:
    """Pie of LISA cluster distribution."""
    order = [("HH", "#2dca5f", "Alto-Alto"),
             ("LL", "#ef4444", "Bajo-Bajo"),
             ("HL", "#60a5fa", "Alto-Bajo"),
             ("LH", "#f0b34a", "Bajo-Alto"),
             ("NS", "#b8c4bb", "No significativo")]
    labels, values, colors = [], [], []
    for code, color, lbl in order:
        v = counts.get(code, 0)
        if v > 0:
            labels.append(f"{code} · {lbl}")
            values.append(v); colors.append(color)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.50,
        marker=dict(colors=colors, line=dict(color=PALETTE["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color=PALETTE["text"]),
        hovertemplate="<b>%{label}</b><br>%{value} muns<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(height=320, showlegend=False,
                       margin={"l": 10, "r": 10, "t": 10, "b": 10})
    return styled(fig)


def depto_treemap(df: pd.DataFrame, value_col: str = "produccion", top: int = 18) -> go.Figure:
    """Treemap of top departments by production / rendimiento share.

    Plotly requires every parent to also appear as a label (or be ""),
    so we emit two layers: regions (parent = "") and departments (parent = region).
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(height=340, margin={"l": 5, "r": 5, "t": 5, "b": 5})
        return styled(fig)

    if value_col == "rendimiento":
        depto = df.groupby(["region", "departamento"], as_index=False)["rendimiento"].mean()
    else:
        depto = df.groupby(["region", "departamento"], as_index=False)[value_col].sum()
    depto = depto.dropna(subset=[value_col])
    depto = depto[depto[value_col] > 0]
    depto = depto.sort_values(value_col, ascending=False).head(top)
    if depto.empty:
        fig = go.Figure()
        fig.update_layout(height=340, margin={"l": 5, "r": 5, "t": 5, "b": 5})
        return styled(fig)

    region_totals = depto.groupby("region", as_index=False)[value_col].sum()
    labels = list(region_totals["region"]) + list(depto["departamento"])
    parents = [""] * len(region_totals) + list(depto["region"])
    values = list(region_totals[value_col]) + list(depto[value_col])

    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        branchvalues="total",
        marker=dict(colorscale=CHORO_SCALE, colors=values,
                    line=dict(color=PALETTE["bg"], width=2)),
        textfont=dict(size=14, color="#0f1814", family="IBM Plex Sans"),
        texttemplate="<b>%{label}</b><br>%{value:,.0f}",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(height=340, margin={"l": 5, "r": 5, "t": 5, "b": 5})
    return styled(fig)


# ─── climate ─────────────────────────────────────────────────────────────────

def climate_scatter(df: pd.DataFrame, x_col: str, x_label: str,
                     region_colors: dict, with_trend: bool = True,
                     max_points: int = 2500) -> go.Figure:
    """Scatter of climate variable vs rendimiento with OLS trend line.

    Trend line uses ALL data, but the marker layer is downsampled to
    `max_points` (stratified by region) so the page stays snappy.
    """
    fig = go.Figure()
    use = df.dropna(subset=[x_col, "rendimiento"])
    sample = use
    if len(use) > max_points:
        rng = np.random.default_rng(42)
        frac = max_points / len(use)
        sample = (use.groupby("region", group_keys=False)
                     .apply(lambda g: g.sample(max(1, int(len(g) * frac)),
                                                random_state=rng.integers(1e9))))
    for r, grp in sample.groupby("region"):
        fig.add_trace(go.Scatter(
            x=grp[x_col], y=grp["rendimiento"],
            mode="markers", name=r,
            marker=dict(color=region_colors.get(r, "#888"), size=7, opacity=0.62,
                        line=dict(color=PALETTE["bg"], width=0.5)),
            hovertemplate=f"<b>{r}</b><br>%{{x:.2f}} · %{{y:.2f}} ton/ha<extra></extra>",
        ))
    if with_trend and len(use) > 10:
        x_full = use[x_col].values; y_full = use["rendimiento"].values
        slope, intercept_, r_val, p_val, _ = sps.linregress(x_full, y_full)
        xs = np.linspace(np.percentile(x_full, 1), np.percentile(x_full, 99), 60)
        n_total = len(use); n_shown = len(sample)
        trend_name = (f"Tendencia · r={r_val:.2f}, p={p_val:.3g}"
                       + (f" · muestra {n_shown:,}/{n_total:,}"
                          if n_shown < n_total else ""))
        fig.add_trace(go.Scatter(
            x=xs, y=intercept_ + slope * xs, mode="lines",
            line=dict(color=PALETTE["amber"], width=2.6, dash="dash"),
            name=trend_name,
        ))
    fig.update_layout(
        height=320,
        xaxis_title=x_label, yaxis_title="Rendimiento (ton/ha)",
        legend=dict(orientation="h", y=-0.22, x=0),
    )
    return styled(fig)


def _hex_to_rgba(hex_color: str, alpha: float = 0.18) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return f"rgba(94,224,138,{alpha})"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def climate_timeseries(df: pd.DataFrame, col: str, label: str,
                        color: str) -> go.Figure:
    """National annual time series for a climate variable."""
    use = df.dropna(subset=[col])
    nat = use.groupby("anio", as_index=False)[col].mean()
    fig = go.Figure(go.Scatter(
        x=nat["anio"], y=nat[col],
        mode="lines+markers",
        line=dict(color=color, width=3),
        marker=dict(size=9, color=color, line=dict(color=PALETTE["bg"], width=1.5)),
        fill="tozeroy", fillcolor=_hex_to_rgba(color, 0.18),
    ))
    fig.update_layout(height=240, xaxis_title=None, yaxis_title=label,
                       showlegend=False)
    return styled(fig)


# ─── linear-model diagnostics ────────────────────────────────────────────────

def scatter_obs_pred(obs, pred, name: str = "") -> go.Figure:
    obs = np.asarray(obs); pred = np.asarray(pred)
    mx = float(max(obs.max(), pred.max())) + 0.5
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines",
                              line=dict(color=PALETTE["amber"], dash="dash", width=1.6),
                              showlegend=False, hoverinfo="skip", name="y = x"))
    fig.add_trace(go.Scatter(x=obs, y=pred, mode="markers",
                              marker=dict(color=PALETTE["accent"], size=6, opacity=0.55,
                                          line=dict(color=PALETTE["bg"], width=0.3)),
                              showlegend=False,
                              hovertemplate="Obs %{x:.2f} · Pred %{y:.2f}<extra></extra>"))
    fig.update_layout(
        height=340,
        xaxis_title="Observado (ton/ha)", yaxis_title="Predicho",
        title=dict(text=name, x=0.02, font=dict(size=13, color=PALETTE["text_dim"])),
    )
    return styled(fig)


def coef_chart(coef_df: pd.DataFrame, labels: dict) -> go.Figure:
    """Bar of standardized betas with CI as error bars. Excludes intercept."""
    sub = coef_df[coef_df["term"] != "const"].copy()
    sub["abs_beta"] = sub["beta_std"].abs()
    sub = sub.sort_values("abs_beta")
    label_col = [labels.get(t, t.replace("reg_", "Región ")) for t in sub["term"]]
    colors = [PALETTE["accent"] if b > 0 else PALETTE["bad"] for b in sub["beta_std"]]
    fig = go.Figure(go.Bar(
        x=sub["beta_std"], y=label_col, orientation="h",
        marker=dict(color=colors, opacity=0.88),
        error_x=dict(type="data",
                     array=(sub["ci_hi"] - sub["beta_std"]).values,
                     arrayminus=(sub["beta_std"] - sub["ci_lo"]).values,
                     color="rgba(255,255,255,0.35)", thickness=1.5, width=4),
        text=[f"{b:+.2f}" for b in sub["beta_std"]], textposition="outside",
        textfont=dict(size=12),
        hovertemplate="<b>%{y}</b><br>β = %{x:.3f}<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.30)", width=1))
    fig.update_layout(
        height=32 * len(sub) + 80,
        xaxis_title="Coeficiente estandarizado (β)", yaxis_title=None,
        margin={"l": 10, "r": 40, "t": 10, "b": 30},
    )
    return styled(fig)


def vif_chart(vif: pd.Series, labels: dict) -> go.Figure:
    s = vif.sort_values()
    cat = [labels.get(t, t.replace("reg_", "Región ")) for t in s.index]
    colors = [PALETTE["bad"] if v > 10 else (PALETTE["amber"] if v > 5 else PALETTE["ok"])
              for v in s.values]
    fig = go.Figure(go.Bar(
        x=s.values, y=cat, orientation="h",
        marker=dict(color=colors, opacity=0.88),
        text=[f"{v:.1f}" for v in s.values], textposition="outside",
        textfont=dict(size=12),
    ))
    fig.add_vline(x=5, line=dict(color=PALETTE["amber"], dash="dot", width=1),
                  annotation_text="VIF=5", annotation_position="top",
                  annotation_font=dict(color=PALETTE["amber"], size=10))
    fig.add_vline(x=10, line=dict(color=PALETTE["bad"], dash="dot", width=1),
                  annotation_text="VIF=10", annotation_position="top",
                  annotation_font=dict(color=PALETTE["bad"], size=10))
    fig.update_layout(
        height=32 * len(s) + 80,
        xaxis_title="VIF", yaxis_title=None,
        margin={"l": 10, "r": 40, "t": 30, "b": 30},
    )
    return styled(fig)


def residuals_vs_fitted(fitted: np.ndarray, resid: np.ndarray) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fitted, y=resid, mode="markers",
        marker=dict(color=PALETTE["accent"], size=5, opacity=0.45,
                    line=dict(color=PALETTE["bg"], width=0.3)),
        showlegend=False,
        hovertemplate="ŷ %{x:.2f} · r %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=PALETTE["amber"], dash="dash", width=1.5))
    # Lowess-ish: simple binned mean to visualize curvature
    try:
        bins = np.linspace(fitted.min(), fitted.max(), 14)
        cents, means = [], []
        for i in range(len(bins) - 1):
            m = (fitted >= bins[i]) & (fitted < bins[i + 1])
            if m.sum() > 3:
                cents.append((bins[i] + bins[i + 1]) / 2)
                means.append(resid[m].mean())
        fig.add_trace(go.Scatter(x=cents, y=means, mode="lines",
                                   line=dict(color=PALETTE["accent_hi"], width=2.5),
                                   showlegend=False))
    except Exception:
        pass
    fig.update_layout(height=300, xaxis_title="Valores ajustados (ŷ)",
                       yaxis_title="Residuos")
    return styled(fig)


def qq_plot(std_resid: np.ndarray) -> go.Figure:
    sample = np.sort(std_resid)
    n = len(sample)
    quantiles = sps.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
    fig = go.Figure()
    mn, mx = float(quantiles.min()), float(quantiles.max())
    fig.add_trace(go.Scatter(x=[mn, mx], y=[mn, mx], mode="lines",
                              line=dict(color=PALETTE["amber"], dash="dash", width=1.6),
                              showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=quantiles, y=sample, mode="markers",
                              marker=dict(color=PALETTE["accent"], size=5, opacity=0.6,
                                          line=dict(color=PALETTE["bg"], width=0.3)),
                              showlegend=False,
                              hovertemplate="Teórico %{x:.2f}<br>Empírico %{y:.2f}<extra></extra>"))
    fig.update_layout(height=300,
                       xaxis_title="Cuantiles teóricos N(0,1)",
                       yaxis_title="Residuos estandarizados")
    return styled(fig)


def alpha_curve(curve: pd.DataFrame, best: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=curve["alpha"], y=curve["rmse_cv"],
        mode="lines+markers",
        line=dict(color=PALETTE["accent_hi"], width=2.5),
        marker=dict(size=10, color=PALETTE["accent_hi"]),
        showlegend=False,
        hovertemplate="α=%{x}<br>RMSE=%{y:.3f}<extra></extra>",
    ))
    fig.add_vline(x=best, line=dict(color=PALETTE["amber"], dash="dash", width=2),
                  annotation_text=f"α* = {best:g}",
                  annotation_position="top right",
                  annotation_font=dict(color=PALETTE["amber"], size=12))
    fig.update_layout(height=240, xaxis_type="log",
                       xaxis_title="Ridge α (escala log)",
                       yaxis_title="RMSE (CV 5-fold)")
    return styled(fig)


# ─── kept legacy helpers (still used elsewhere) ──────────────────────────────

def bar_horizontal(features, values, color=None) -> go.Figure:
    color = color or PALETTE["accent"]
    fig = go.Figure(go.Bar(
        x=values, y=features, orientation="h",
        marker=dict(color=color, opacity=0.88),
        text=[f"{v*100:.0f}%" for v in values], textposition="outside",
        textfont=dict(size=12),
    ))
    fig.update_layout(
        height=34 * len(features) + 70,
        xaxis_title=None, yaxis_title=None,
        margin={"l": 10, "r": 30, "t": 10, "b": 20},
    )
    return styled(fig)


# ─── TerriData business charts ───────────────────────────────────────────────

def decile_bars(df: pd.DataFrame, feature: str, feat_label: str,
                 target: str = "rendimiento", n_bins: int = 10) -> go.Figure:
    """Average yield per decile of a TerriData indicator.

    Telling because it forces a monotonic-or-not story: does yield rise as
    electrification / connectivity / land-use-adequacy goes up?
    """
    use = df.dropna(subset=[feature, target])
    if use.empty:
        return styled(go.Figure())
    try:
        use = use.copy()
        use["bin"] = pd.qcut(use[feature], q=n_bins, duplicates="drop",
                              labels=False)
    except Exception:
        return styled(go.Figure())
    agg = (use.groupby("bin").agg(
              mean_yield=(target, "mean"),
              center=(feature, "median"),
              n=(target, "size"),
          ).reset_index().dropna())
    if agg.empty:
        return styled(go.Figure())
    # Color by yield with the bright palette
    fig = go.Figure(go.Bar(
        x=[f"D{int(b)+1}" for b in agg["bin"]],
        y=agg["mean_yield"],
        marker=dict(color=agg["mean_yield"], colorscale=CHORO_SCALE,
                    showscale=False, line=dict(color=PALETTE["bg"], width=1)),
        text=[f"{v:.2f}" for v in agg["mean_yield"]],
        textposition="outside", textfont=dict(size=12, color=PALETTE["text"]),
        customdata=np.stack([agg["center"].values, agg["n"].values], axis=-1),
        hovertemplate=(f"<b>Decil %{{x}}</b><br>{feat_label} mediana: %{{customdata[0]:.2f}}"
                       f"<br>Rendimiento: %{{y:.2f}} ton/ha"
                       f"<br>n = %{{customdata[1]}}<extra></extra>"),
    ))
    # Connecting line emphasizes the gradient
    fig.add_trace(go.Scatter(
        x=[f"D{int(b)+1}" for b in agg["bin"]],
        y=agg["mean_yield"], mode="lines",
        line=dict(color=PALETTE["accent_hi"], width=2, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        height=320,
        xaxis_title=f"Decil de {feat_label} (D1 = bajo, D10 = alto)",
        yaxis_title="Rendimiento promedio (ton/ha)",
        showlegend=False, margin={"l": 50, "r": 30, "t": 30, "b": 50},
    )
    return styled(fig)


def strategic_quadrant(df: pd.DataFrame, x_col: str, y_col: str,
                        x_label: str, y_label: str,
                        label_col: str = "municipio",
                        max_points: int = 1500) -> go.Figure:
    """Four-quadrant scatter split at medians.

    Q2 (alto-y, bajo-x) = oportunidades (e.g. alto rendimiento sin banda ancha
                                          → candidatos a inversión AgTech)
    Q1 (alto-y, alto-x) = ganadores
    Q4 (bajo-y, bajo-x) = brecha estructural
    Q3 (bajo-y, alto-x) = casos curiosos (recursos sin resultado)
    """
    use = df.dropna(subset=[x_col, y_col, label_col]).copy()
    if use.empty:
        return styled(go.Figure())
    if len(use) > max_points:
        use = use.sample(max_points, random_state=42)
    mx, my = use[x_col].median(), use[y_col].median()

    def _quad(row):
        if row[y_col] >= my and row[x_col] >= mx: return "Ganadores"
        if row[y_col] >= my and row[x_col] <  mx: return "Oportunidad AgTech"
        if row[y_col] <  my and row[x_col] <  mx: return "Brecha estructural"
        return "Recursos sin resultado"

    use["quad"] = use.apply(_quad, axis=1)

    quad_color = {
        "Ganadores":              PALETTE["accent_hi"],
        "Oportunidad AgTech":     PALETTE["amber"],
        "Brecha estructural":     PALETTE["bad"],
        "Recursos sin resultado": PALETTE["info"],
    }
    fig = go.Figure()
    for q, color in quad_color.items():
        grp = use[use["quad"] == q]
        fig.add_trace(go.Scatter(
            x=grp[x_col], y=grp[y_col], mode="markers", name=q,
            marker=dict(color=color, size=8, opacity=0.62,
                        line=dict(color=PALETTE["bg"], width=0.5)),
            text=grp[label_col],
            hovertemplate=(f"<b>%{{text}}</b><br>{x_label}: %{{x:.2f}}"
                            f"<br>{y_label}: %{{y:.2f}}<br>"
                            f"<i>{q}</i><extra></extra>"),
        ))
    fig.add_hline(y=my, line=dict(color="rgba(255,255,255,0.35)", dash="dash", width=1),
                   annotation_text=f"mediana y = {my:.2f}",
                   annotation_position="top right",
                   annotation_font=dict(size=10, color=PALETTE["text_dim"]))
    fig.add_vline(x=mx, line=dict(color="rgba(255,255,255,0.35)", dash="dash", width=1),
                   annotation_text=f"mediana x = {mx:.2f}",
                   annotation_position="top right",
                   annotation_font=dict(size=10, color=PALETTE["text_dim"]))
    fig.update_layout(
        height=440, xaxis_title=x_label, yaxis_title=y_label,
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=11)),
    )
    return styled(fig)


def correlation_heatmap(df: pd.DataFrame, cols: list, labels: dict,
                         target: str = "rendimiento") -> go.Figure:
    """Heatmap of Pearson correlations between target and a list of features."""
    use = df[cols + [target]].dropna()
    if use.empty:
        return styled(go.Figure())
    corr = use.corr().loc[cols, [target] + cols]
    z = corr.values
    x_lbl = [labels.get(c, c) for c in corr.columns]
    y_lbl = [labels.get(c, c) for c in corr.index]
    text = [[f"{v:+.2f}" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=x_lbl, y=y_lbl,
        colorscale=[[0, "#c0392b"], [0.5, "#f7f3d3"], [1, "#117a3d"]],
        zmid=0, zmin=-1, zmax=1,
        text=text, texttemplate="%{text}",
        textfont=dict(size=12, family="IBM Plex Mono", color="#0f1814"),
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>r = %{z:+.3f}<extra></extra>",
        colorbar=dict(thickness=12, len=0.7, x=1.02,
                       tickfont=dict(color="#cbd5d0", size=11)),
    ))
    fig.update_layout(
        height=max(280, 36 * len(cols) + 80),
        xaxis=dict(tickangle=-25), yaxis=dict(autorange="reversed"),
        margin={"l": 10, "r": 40, "t": 20, "b": 60},
    )
    return styled(fig)


def territorial_radar(df: pd.DataFrame, cols: list, labels: dict,
                       group_col: str = "region",
                       region_colors: dict | None = None) -> go.Figure:
    """Per-region radar chart on min-max normalized TerriData indicators.

    Strong visual for 'which region is strong / weak across socio-economic axes'.
    """
    use = df.dropna(subset=cols + [group_col])
    if use.empty:
        return styled(go.Figure())
    agg = use.groupby(group_col)[cols].mean()
    # Min-max normalize each axis to [0, 1] for comparability
    norm = (agg - agg.min()) / (agg.max() - agg.min() + 1e-12)
    fig = go.Figure()
    axis_labels = [labels.get(c, c) for c in cols]
    for region, row in norm.iterrows():
        color = (region_colors or {}).get(region, PALETTE["accent"])
        vals = list(row.values) + [row.values[0]]  # close the polygon
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=axis_labels + [axis_labels[0]],
            fill="toself", name=region,
            line=dict(color=color, width=2.2),
            fillcolor=_hex_to_rgba(color, 0.15),
            hovertemplate=f"<b>{region}</b><br>%{{theta}}: %{{r:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        polar=dict(
            bgcolor=PALETTE["panel_alt"],
            radialaxis=dict(visible=True, range=[0, 1.05],
                             tickfont=dict(color=PALETTE["text_dim"], size=10),
                             gridcolor="rgba(255,255,255,0.10)"),
            angularaxis=dict(tickfont=dict(color=PALETTE["text"], size=12),
                              gridcolor="rgba(255,255,255,0.10)"),
        ),
        height=460,
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0, font=dict(size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "IBM Plex Sans, sans-serif",
               "color": PALETTE["text"], "size": 13},
    )
    return fig


def opportunity_lollipop(df: pd.DataFrame, x_col: str, y_col: str,
                          x_label: str, y_label: str,
                          label_col: str = "municipio",
                          top: int = 12) -> go.Figure:
    """Lollipop of top 'high yield · low infrastructure' opportunities.

    Selects municipios in the top quartile of y and the bottom quartile of x
    — i.e. they produce a lot but score low on infrastructure. Each row is
    one municipio: a horizontal line from its `x` value, dot colored by `y`.
    """
    use = df.dropna(subset=[x_col, y_col]).copy()
    if use.empty:
        return styled(go.Figure())
    y_q3 = use[y_col].quantile(0.75)
    x_q1 = use[x_col].quantile(0.25)
    cand = use[(use[y_col] >= y_q3) & (use[x_col] <= x_q1)].copy()
    cand = cand.sort_values(y_col, ascending=False).head(top)
    if cand.empty:
        return styled(go.Figure())
    cand = cand.iloc[::-1]  # for horizontal bar visual order
    fig = go.Figure()
    # Stems
    for _, row in cand.iterrows():
        fig.add_trace(go.Scatter(
            x=[0, row[x_col]], y=[row[label_col], row[label_col]],
            mode="lines",
            line=dict(color=PALETTE["text_dimmer"], width=2),
            hoverinfo="skip", showlegend=False,
        ))
    # Dots colored by yield
    fig.add_trace(go.Scatter(
        x=cand[x_col], y=cand[label_col], mode="markers+text",
        marker=dict(size=14, color=cand[y_col], colorscale=CHORO_SCALE,
                    showscale=True, cmin=cand[y_col].min(), cmax=cand[y_col].max(),
                    line=dict(color=PALETTE["bg"], width=1.5),
                    colorbar=dict(title=dict(text=y_label, font=dict(size=11,
                                              color=PALETTE["text_dim"])),
                                    thickness=10, len=0.7,
                                    tickfont=dict(color="#cbd5d0", size=10))),
        text=[f" {v:.1f}" for v in cand[y_col]], textposition="middle right",
        textfont=dict(size=11, color=PALETTE["text"]),
        hovertemplate=(f"<b>%{{y}}</b><br>{x_label}: %{{x:.2f}}"
                       f"<br>{y_label}: %{{marker.color:.2f}}<extra></extra>"),
        showlegend=False,
    ))
    fig.update_layout(
        height=30 * len(cand) + 90,
        xaxis_title=x_label, yaxis_title=None,
        margin={"l": 10, "r": 60, "t": 10, "b": 40},
    )
    return styled(fig)


def variogram(h, gamma_emp, gamma_theo, sill, range_) -> go.Figure:
    fig = go.Figure()
    fig.add_hline(y=sill, line=dict(color=PALETTE["amber"], dash="dash", width=1.4),
                  annotation_text=f"Sill ≈ {sill:.2f}",
                  annotation_position="top left",
                  annotation_font=dict(color=PALETTE["amber"], size=11))
    fig.add_vline(x=range_, line=dict(color=PALETTE["amber"], dash="dash", width=1.4),
                  annotation_text=f"Range ≈ {range_:.0f} km",
                  annotation_position="top right",
                  annotation_font=dict(color=PALETTE["amber"], size=11))
    fig.add_trace(go.Scatter(x=h, y=gamma_theo, mode="lines",
                              line=dict(color=PALETTE["accent_hi"], width=2.6),
                              name="Modelo exponencial"))
    fig.add_trace(go.Scatter(x=h, y=gamma_emp, mode="markers",
                              marker=dict(size=10, color=PALETTE["accent"],
                                           line=dict(color=PALETTE["bg"], width=1.5)),
                              name="Empírico"))
    fig.update_layout(
        height=300, xaxis_title="Distancia (km)", yaxis_title="γ(h)",
        legend=dict(orientation="h", y=-0.22, x=0),
    )
    return styled(fig)
