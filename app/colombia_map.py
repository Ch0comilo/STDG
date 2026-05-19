"""Interactive Colombia choropleth using the real DANE municipios shapefile."""
from __future__ import annotations

import json
import branca.colormap as cm
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from data_loader import load_municipios
from theme import PALETTE


COLOMBIA_CENTER = [4.6, -74.0]


def _build_value_map(df: pd.DataFrame, key: str) -> dict[str, float]:
    """Aggregate (mean) value per dane_code for the supplied dataframe."""
    if df.empty or key not in df.columns:
        return {}
    g = df.groupby("dane_code")[key].mean()
    return g.to_dict()


@st.cache_data(show_spinner=False)
def _simplified_geojson() -> dict:
    """Cache a simplified GeoJSON of Colombia municipios for fast rendering."""
    gdf = load_municipios()[["dane_code", "MPIO_CNMBR", "DEPTO", "geometry"]].copy()
    # Simplify in projected CRS for stability, then back to 4326
    proj = gdf.to_crs(epsg=3116)
    proj["geometry"] = proj.geometry.simplify(tolerance=400, preserve_topology=True)
    gdf = proj.to_crs(epsg=4326)
    return json.loads(gdf.to_json())


def choropleth(df: pd.DataFrame, value_key: str = "rendimiento",
               year: int | None = None, height: int = 420,
               key: str = "map") -> dict | None:
    """Render an interactive choropleth of Colombia.

    Returns the Folium event payload from st_folium so callers can react to
    municipality clicks.
    """
    if year is not None:
        df = df[df["anio"] == year]
    value_map = _build_value_map(df, value_key)

    m = folium.Map(
        location=COLOMBIA_CENTER, zoom_start=5, tiles=None,
        control_scale=True, prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="cartodbdark_matter", name="Base", control=False,
    ).add_to(m)

    if value_map:
        vmin = float(np.nanmin(list(value_map.values())))
        vmax = float(np.nanmax(list(value_map.values())))
    else:
        vmin, vmax = 0, 1

    palette = ["#f7f3d3", "#dceb9a", "#a3d36a", "#3f9b48", "#0f4d2a"]
    colormap = cm.LinearColormap(colors=palette, vmin=vmin, vmax=vmax,
                                  caption=f"{value_key} (ton/ha)")
    colormap.add_to(m)

    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        v = value_map.get(code)
        if v is None or np.isnan(v):
            return {"fillColor": "#1d2520", "fillOpacity": 0.25,
                    "color": "#3a4d3f", "weight": 0.4}
        return {"fillColor": colormap(v), "fillOpacity": 0.85,
                "color": "#1a221d", "weight": 0.4}

    def _popup(feat):
        code = feat["properties"]["dane_code"]
        v = value_map.get(code)
        vstr = f"{v:.2f} ton/ha" if v is not None and not np.isnan(v) else "—"
        return (f"<div style='font-family:IBM Plex Sans;font-size:12px;'>"
                f"<b>{feat['properties']['MPIO_CNMBR']}</b>"
                f"<br><span style='color:#666'>{feat['properties']['DEPTO']}</span>"
                f"<br><span style='color:#0f4d2a;font-weight:600'>{vstr}</span></div>")

    folium.GeoJson(
        geo,
        name="Municipios",
        style_function=_style,
        highlight_function=lambda f: {"weight": 1.6, "color": "#fff"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            labels=True, sticky=False,
            style=("background-color: #1d251f; color: #e6efe9; "
                   "font-family: IBM Plex Sans; font-size: 11px; "
                   "padding: 6px 9px; border-radius: 6px; border: 1px solid #3b4d40;"),
        ),
        popup=folium.GeoJsonPopup(
            fields=["MPIO_CNMBR", "DEPTO", "dane_code"],
            aliases=["Municipio", "Departamento", "DANE"],
        ),
    ).add_to(m)

    return st_folium(
        m, height=height, use_container_width=True,
        returned_objects=["last_object_clicked", "last_active_drawing"],
        key=key,
    )


def lisa_map(df: pd.DataFrame, lisa_col: str = "lisa", height: int = 420,
             key: str = "lisa_map") -> dict | None:
    """LISA cluster choropleth. df must contain 'lisa' per dane_code."""
    LISA_FILL = {"HH": "#22c55e", "LL": "#ef4444", "HL": "#3b82f6",
                  "LH": "#f59e0b", "NS": "#334155"}
    cluster_map = df.groupby("dane_code")[lisa_col].first().to_dict()

    m = folium.Map(location=COLOMBIA_CENTER, zoom_start=5, tiles=None,
                    prefer_canvas=True)
    folium.TileLayer(tiles="cartodbdark_matter", control=False).add_to(m)

    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        c = cluster_map.get(code)
        if c is None:
            return {"fillColor": "#1d2520", "fillOpacity": 0.20,
                    "color": "#3a4d3f", "weight": 0.4}
        return {"fillColor": LISA_FILL.get(c, "#334155"), "fillOpacity": 0.85,
                "color": "#1a221d", "weight": 0.4}

    folium.GeoJson(
        geo, style_function=_style,
        highlight_function=lambda f: {"weight": 1.4, "color": "#fff"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            sticky=False,
            style=("background-color: #1d251f; color: #e6efe9; "
                   "font-family: IBM Plex Sans; font-size: 11px; "
                   "padding: 6px 9px; border-radius: 6px; border: 1px solid #3b4d40;"),
        ),
    ).add_to(m)

    # Manual legend
    legend_html = """
    <div style="position: fixed; bottom: 20px; left: 60px; z-index: 9999;
                background: #1d251f; padding: 8px 12px; border-radius: 8px;
                border: 1px solid #3b4d40; color: #e6efe9; font-family: 'IBM Plex Sans';
                font-size: 11px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
      <div style="font-weight:600; margin-bottom:4px;">LISA Clusters</div>
      <div><span style="display:inline-block;width:10px;height:10px;background:#22c55e;border-radius:50%;margin-right:6px"></span>HH (Alto-Alto)</div>
      <div><span style="display:inline-block;width:10px;height:10px;background:#ef4444;border-radius:50%;margin-right:6px"></span>LL (Bajo-Bajo)</div>
      <div><span style="display:inline-block;width:10px;height:10px;background:#3b82f6;border-radius:50%;margin-right:6px"></span>HL (Atípico)</div>
      <div><span style="display:inline-block;width:10px;height:10px;background:#f59e0b;border-radius:50%;margin-right:6px"></span>LH (Atípico)</div>
      <div><span style="display:inline-block;width:10px;height:10px;background:#334155;border-radius:50%;margin-right:6px"></span>NS</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    return st_folium(m, height=height, use_container_width=True,
                      returned_objects=["last_object_clicked"], key=key)


def residual_map(df: pd.DataFrame, residual_col: str = "residual",
                  height: int = 420, key: str = "resid_map") -> dict | None:
    """Diverging choropleth of residuals (sub-/sobre-estimado)."""
    res_map = df.groupby("dane_code")[residual_col].mean().to_dict()
    if not res_map:
        return None
    vals = np.array([v for v in res_map.values() if not np.isnan(v)])
    bound = float(np.nanpercentile(np.abs(vals), 95)) or 1.0

    palette = ["#dc2626", "#fb923c", "#f3f4f6", "#86efac", "#16a34a"]
    colormap = cm.LinearColormap(colors=palette, vmin=-bound, vmax=bound,
                                  caption="Residuo (pred − obs) ton/ha")

    m = folium.Map(location=COLOMBIA_CENTER, zoom_start=5, tiles=None,
                    prefer_canvas=True)
    folium.TileLayer(tiles="cartodbdark_matter", control=False).add_to(m)
    colormap.add_to(m)

    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        v = res_map.get(code)
        if v is None or np.isnan(v):
            return {"fillColor": "#1d2520", "fillOpacity": 0.20,
                    "color": "#3a4d3f", "weight": 0.4}
        return {"fillColor": colormap(np.clip(v, -bound, bound)),
                "fillOpacity": 0.85, "color": "#1a221d", "weight": 0.4}

    folium.GeoJson(
        geo, style_function=_style,
        highlight_function=lambda f: {"weight": 1.4, "color": "#fff"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            sticky=False,
            style=("background-color: #1d251f; color: #e6efe9; "
                   "font-family: IBM Plex Sans; font-size: 11px; "
                   "padding: 6px 9px; border-radius: 6px; border: 1px solid #3b4d40;"),
        ),
    ).add_to(m)
    return st_folium(m, height=height, use_container_width=True,
                      returned_objects=["last_object_clicked"], key=key)
