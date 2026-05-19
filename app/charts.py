"""Plotly chart helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from theme import PALETTE, PLOTLY_LAYOUT, CHORO_SCALE


def styled(fig: go.Figure, height: int | None = None) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT)
    if height:
        fig.update_layout(height=height)
    return fig


def time_series(df: pd.DataFrame, regions: list[str], region_colors: dict) -> go.Figure:
    """National + per-region average rendimiento over years."""
    nat = df.groupby("anio", as_index=False)["rendimiento"].mean()
    fig = go.Figure()

    # Filled area for national
    fig.add_trace(go.Scatter(
        x=nat["anio"], y=nat["rendimiento"], name="Nacional",
        mode="lines+markers",
        line=dict(color=PALETTE["accent_hi"], width=2.5),
        marker=dict(size=7, color=PALETTE["accent_hi"], line=dict(color=PALETTE["bg"], width=1.5)),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.10)",
    ))
    for r in regions:
        rdf = df[df["region"] == r].groupby("anio", as_index=False)["rendimiento"].mean()
        if rdf.empty:
            continue
        fig.add_trace(go.Scatter(
            x=rdf["anio"], y=rdf["rendimiento"], name=r,
            mode="lines",
            line=dict(color=region_colors.get(r, "#888"), width=1.5, dash="dot"),
            opacity=0.75,
        ))

    fig.update_layout(
        height=260,
        xaxis_title=None, yaxis_title="ton/ha",
        legend=dict(orientation="h", y=-0.18, x=0),
    )
    return styled(fig)


def ranking(df: pd.DataFrame, year: int, top: int = 10, mode: str = "top") -> go.Figure:
    yd = df[df["anio"] == year]
    sorted_ = yd.sort_values("rendimiento", ascending=(mode != "top")).head(top)
    sorted_ = sorted_.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=sorted_["rendimiento"], y=sorted_["municipio"] + " · " + sorted_["departamento"].str[:10],
        orientation="h",
        marker=dict(color=sorted_["rendimiento"],
                    colorscale=CHORO_SCALE, showscale=False),
        text=[f"{v:.2f}" for v in sorted_["rendimiento"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.3f} ton/ha<extra></extra>",
    ))
    fig.update_layout(
        height=22 * top + 40,
        xaxis_title="ton/ha", yaxis_title=None,
        margin={"l": 10, "r": 30, "t": 10, "b": 30},
    )
    return styled(fig)


def heatmap_top(df: pd.DataFrame, top: int = 22) -> go.Figure:
    avg = (df.groupby(["dane_code", "municipio"], as_index=False)["rendimiento"].mean()
             .sort_values("rendimiento", ascending=False).head(top))
    sub = df[df["dane_code"].isin(avg["dane_code"])]
    pivot = sub.pivot_table(index="municipio", columns="anio",
                             values="rendimiento", aggfunc="mean")
    # order rows by average desc
    pivot = pivot.loc[avg["municipio"].values]
    z = pivot.values
    text = [[f"{v:.1f}" if not np.isnan(v) else "" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=pivot.columns.astype(str), y=pivot.index,
        colorscale=CHORO_SCALE, showscale=True,
        text=text, texttemplate="%{text}",
        textfont=dict(size=10, family="IBM Plex Mono, monospace"),
        hovertemplate="<b>%{y}</b><br>Año %{x}<br>%{z:.2f} ton/ha<extra></extra>",
        colorbar=dict(thickness=10, len=0.7, x=1.01, tickfont=dict(color="#9aa89e")),
    ))
    fig.update_layout(
        height=22 * top + 80,
        xaxis_title=None, yaxis_title=None,
        yaxis=dict(autorange="reversed"),
        margin={"l": 0, "r": 30, "t": 20, "b": 30},
    )
    return styled(fig)


def scatter_obs_pred(obs, pred, name: str = "") -> go.Figure:
    obs = np.asarray(obs); pred = np.asarray(pred)
    mx = float(max(obs.max(), pred.max())) + 0.5
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines",
                              line=dict(color=PALETTE["amber"], dash="dash", width=1.4),
                              showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=obs, y=pred, mode="markers",
                              marker=dict(color=PALETTE["accent"], size=6, opacity=0.55),
                              showlegend=False,
                              hovertemplate="Obs %{x:.2f} · Pred %{y:.2f}<extra></extra>"))
    fig.update_layout(
        height=300,
        xaxis_title="Observado (ton/ha)",
        yaxis_title="Predicho",
        title=dict(text=name, x=0.02, font=dict(size=12, color=PALETTE["text_dim"])),
    )
    return styled(fig)


def bar_horizontal(features, values, color=None) -> go.Figure:
    color = color or PALETTE["accent"]
    fig = go.Figure(go.Bar(
        x=values, y=features, orientation="h",
        marker=dict(color=color, opacity=0.85),
        text=[f"{v*100:.0f}%" for v in values], textposition="outside",
    ))
    fig.update_layout(
        height=32 * len(features) + 60,
        xaxis_title=None, yaxis_title=None,
        margin={"l": 10, "r": 30, "t": 10, "b": 20},
    )
    return styled(fig)


def variogram(h, gamma_emp, gamma_theo, sill, range_) -> go.Figure:
    fig = go.Figure()
    fig.add_hline(y=sill, line=dict(color=PALETTE["amber"], dash="dash", width=1),
                  annotation_text=f"Sill ≈ {sill:.2f}",
                  annotation_position="top left",
                  annotation_font=dict(color=PALETTE["amber"], size=9))
    fig.add_vline(x=range_, line=dict(color=PALETTE["amber"], dash="dash", width=1),
                  annotation_text=f"Range ≈ {range_:.0f} km",
                  annotation_position="top right",
                  annotation_font=dict(color=PALETTE["amber"], size=9))
    fig.add_trace(go.Scatter(x=h, y=gamma_theo, mode="lines",
                              line=dict(color=PALETTE["accent_hi"], width=2.2),
                              name="Teórico"))
    fig.add_trace(go.Scatter(x=h, y=gamma_emp, mode="markers",
                              marker=dict(size=8, color=PALETTE["accent"],
                                           line=dict(color=PALETTE["bg"], width=1.5)),
                              name="Empírico"))
    fig.update_layout(
        height=260,
        xaxis_title="Distancia (km)", yaxis_title="γ(h)",
        legend=dict(orientation="h", y=-0.22, x=0),
    )
    return styled(fig)


def pdp_chart(x, y, label) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                              line=dict(color=PALETTE["amber"], width=2.5),
                              fill="tozeroy", fillcolor="rgba(245,158,11,0.10)",
                              showlegend=False))
    fig.update_layout(height=180, xaxis_title=label, yaxis_title="ŷ",
                      margin={"l": 40, "r": 10, "t": 10, "b": 36})
    return styled(fig)


def efficiency_scatter(df: pd.DataFrame, region_colors: dict) -> go.Figure:
    """Yield vs Area Cosechada to look for scale trends."""
    fig = go.Figure()
    for r, grp in df.groupby("region"):
        fig.add_trace(go.Scatter(
            x=grp["area_cosechada"], y=grp["rendimiento"],
            mode="markers", name=r,
            marker=dict(color=region_colors.get(r, "#888"), size=5, opacity=0.55),
            hovertemplate=f"<b>{r}</b><br>Área: %{{x:.0f}} ha<br>Rendimiento: %{{y:.2f}} ton/ha<extra></extra>",
        ))
    fig.update_layout(
        height=240,
        xaxis_title="Área Cosechada (ha)", yaxis_title="Rendimiento (ton/ha)",
        xaxis_type="log",
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return styled(fig)


def yield_distribution(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["rendimiento"], nbinsx=40, name="Frecuencia",
        marker=dict(color=PALETTE["accent"], opacity=0.7),
        hovertemplate="Rendimiento: %{x}<br>Count: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Box(
        x=df["rendimiento"], name="Distribución",
        marker=dict(color=PALETTE["amber"]),
        yaxis="y2"
    ))
    fig.update_layout(
        height=280,
        xaxis_title="Rendimiento (ton/ha)",
        yaxis_title="Frecuencia",
        yaxis2=dict(title="", overlaying="y", side="right", showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        margin={"l": 40, "r": 10, "t": 10, "b": 40},
    )
    return styled(fig)


def region_bars(df: pd.DataFrame, region_colors: dict) -> go.Figure:
    avg = df.groupby("region", as_index=False)["rendimiento"].mean().sort_values("rendimiento")
    fig = go.Figure(go.Bar(
        x=avg["rendimiento"], y=avg["region"], orientation="h",
        marker=dict(color=[region_colors.get(r, "#888") for r in avg["region"]], opacity=0.88),
        text=[f"{v:.2f}" for v in avg["rendimiento"]], textposition="outside",
    ))
    fig.update_layout(height=180, xaxis_title="ton/ha", yaxis_title=None,
                      margin={"l": 10, "r": 30, "t": 10, "b": 30})
    return styled(fig)


def precip_vs_rendim(df: pd.DataFrame, region_colors: dict) -> go.Figure:
    """Until we have real climate joined, use altitude proxy. Returns scatter."""
    if "precipitacion" in df.columns:
        x = df["precipitacion"]; xlabel = "Precipitación (mm)"
    else:
        # Use latitude as a basic proxy (hides correlation but keeps the slot real-ish)
        x = df["lat"]; xlabel = "Latitud (°)"
    fig = go.Figure()
    for r, grp in df.groupby("region"):
        fig.add_trace(go.Scatter(
            x=x.loc[grp.index], y=grp["rendimiento"],
            mode="markers", name=r,
            marker=dict(color=region_colors.get(r, "#888"), size=5, opacity=0.55),
            hovertemplate=f"<b>{r}</b><br>%{{x:.2f}} · %{{y:.2f}} ton/ha<extra></extra>",
        ))
    fig.update_layout(
        height=240,
        xaxis_title=xlabel, yaxis_title="Rendimiento (ton/ha)",
        legend=dict(orientation="h", y=-0.25, x=0),
    )
    return styled(fig)
