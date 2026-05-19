"""Interactive Colombia choropleth using the real DANE municipios shapefile.

Uses a light base layer (cartodbpositron) so the bright yellow→green palette
actually pops against the surrounding UI — the previous dark base swallowed
half the color range.
"""
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

# Bright palette — visible on light cartodbpositron base
CHORO_HEX = ["#fff5b8", "#ffd166", "#ff9f1c", "#3dab5a", "#0b6e3a"]
DIVERG_HEX = ["#c0392b", "#e67e22", "#f7f3d3", "#5ee08a", "#117a3d"]


_TOOLTIP_STYLE = ("background-color: #1d251f; color: #f0f6f1; "
                  "font-family: 'IBM Plex Sans', sans-serif; font-size: 13px; "
                  "padding: 8px 11px; border-radius: 8px; "
                  "border: 1px solid #5ee08a; "
                  "box-shadow: 0 4px 12px rgba(0,0,0,0.35); font-weight: 500;")


def _build_value_map(df: pd.DataFrame, key: str) -> dict[str, float]:
    if df.empty or key not in df.columns:
        return {}
    g = df.groupby("dane_code")[key].mean()
    return g.to_dict()


@st.cache_data(show_spinner=False)
def _simplified_geojson() -> dict:
    gdf = load_municipios()[["dane_code", "MPIO_CNMBR", "DEPTO", "geometry"]].copy()
    proj = gdf.to_crs(epsg=3116)
    proj["geometry"] = proj.geometry.simplify(tolerance=400, preserve_topology=True)
    gdf = proj.to_crs(epsg=4326)
    return json.loads(gdf.to_json())


def _base_map(light: bool = True) -> folium.Map:
    m = folium.Map(
        location=COLOMBIA_CENTER, zoom_start=5, tiles=None,
        control_scale=True, prefer_canvas=True,
    )
    tile = "cartodbpositron" if light else "cartodbdark_matter"
    folium.TileLayer(tiles=tile, name="Base", control=False).add_to(m)
    return m


def choropleth(df: pd.DataFrame, value_key: str = "rendimiento",
               year: int | None = None, height: int = 460,
               key: str = "map", caption: str | None = None,
               value_map_override: dict | None = None,
               unit: str = "ton/ha") -> dict | None:
    """Render an interactive choropleth of Colombia (light base, bright palette).

    `value_map_override` lets the caller pass a {dane_code: value} dict directly,
    bypassing df aggregation — handy when the values were produced by kriging.
    """
    if value_map_override is not None:
        value_map = value_map_override
    else:
        if year is not None:
            df = df[df["anio"] == year]
        value_map = _build_value_map(df, value_key)

    m = _base_map(light=True)

    if value_map:
        finite = [v for v in value_map.values()
                  if v is not None and not (isinstance(v, float) and np.isnan(v))]
        if finite:
            vmin = float(np.nanmin(finite))
            vmax = float(np.nanmax(finite))
            if vmax - vmin < 1e-9:
                vmax = vmin + 1.0
        else:
            vmin, vmax = 0.0, 1.0
    else:
        vmin, vmax = 0.0, 1.0

    colormap = cm.LinearColormap(colors=CHORO_HEX, vmin=vmin, vmax=vmax,
                                  caption=caption or f"{value_key} ({unit})")
    colormap.add_to(m)

    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        v = value_map.get(code)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return {"fillColor": "#d6dcd4", "fillOpacity": 0.35,
                    "color": "#a8b0a8", "weight": 0.4}
        return {"fillColor": colormap(v), "fillOpacity": 0.92,
                "color": "#2d3a30", "weight": 0.5}

    folium.GeoJson(
        geo,
        name="Municipios",
        style_function=_style,
        highlight_function=lambda f: {"weight": 2.0, "color": "#0b6e3a"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            labels=True, sticky=False,
            style=_TOOLTIP_STYLE,
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


def lisa_map(df: pd.DataFrame, lisa_col: str = "lisa", height: int = 460,
             key: str = "lisa_map") -> dict | None:
    LISA_FILL = {"HH": "#2dca5f", "LL": "#ef4444", "HL": "#60a5fa",
                  "LH": "#f0b34a", "NS": "#b8c4bb"}
    cluster_map = df.groupby("dane_code")[lisa_col].first().to_dict()

    m = _base_map(light=True)
    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        c = cluster_map.get(code)
        if c is None:
            return {"fillColor": "#e3e8e4", "fillOpacity": 0.35,
                    "color": "#9aa49d", "weight": 0.4}
        return {"fillColor": LISA_FILL.get(c, "#b8c4bb"), "fillOpacity": 0.90,
                "color": "#2d3a30", "weight": 0.5}

    folium.GeoJson(
        geo, style_function=_style,
        highlight_function=lambda f: {"weight": 1.8, "color": "#1a1a1a"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            sticky=False, style=_TOOLTIP_STYLE,
        ),
    ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 20px; left: 60px; z-index: 9999;
                background: #1d251f; padding: 12px 16px; border-radius: 10px;
                border: 1px solid #5ee08a55; color: #f0f6f1;
                font-family: 'IBM Plex Sans'; font-size: 13px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.5);">
      <div style="font-weight:700; margin-bottom:8px; font-size:13px;
                  color:#5ee08a; letter-spacing:0.05em;">CLUSTERS LISA</div>
      <div style="margin:4px 0"><span style="display:inline-block;width:12px;height:12px;background:#2dca5f;border-radius:50%;margin-right:8px"></span>HH · Alto-Alto</div>
      <div style="margin:4px 0"><span style="display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:50%;margin-right:8px"></span>LL · Bajo-Bajo</div>
      <div style="margin:4px 0"><span style="display:inline-block;width:12px;height:12px;background:#60a5fa;border-radius:50%;margin-right:8px"></span>HL · Alto rodeado de Bajo</div>
      <div style="margin:4px 0"><span style="display:inline-block;width:12px;height:12px;background:#f0b34a;border-radius:50%;margin-right:8px"></span>LH · Bajo rodeado de Alto</div>
      <div style="margin:4px 0"><span style="display:inline-block;width:12px;height:12px;background:#b8c4bb;border-radius:50%;margin-right:8px"></span>NS · No significativo</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    return st_folium(m, height=height, use_container_width=True,
                      returned_objects=["last_object_clicked"], key=key)


def residual_map(df: pd.DataFrame, residual_col: str = "residual",
                  height: int = 460, key: str = "resid_map",
                  caption: str = "Residuo (pred − obs) ton/ha") -> dict | None:
    res_map = df.groupby("dane_code")[residual_col].mean().to_dict()
    if not res_map:
        return None
    vals = np.array([v for v in res_map.values() if not np.isnan(v)])
    bound = float(np.nanpercentile(np.abs(vals), 95)) or 1.0

    colormap = cm.LinearColormap(colors=DIVERG_HEX, vmin=-bound, vmax=bound,
                                  caption=caption)

    m = _base_map(light=True)
    colormap.add_to(m)
    geo = _simplified_geojson()

    def _style(feat):
        code = feat["properties"]["dane_code"]
        v = res_map.get(code)
        if v is None or np.isnan(v):
            return {"fillColor": "#e3e8e4", "fillOpacity": 0.30,
                    "color": "#9aa49d", "weight": 0.4}
        return {"fillColor": colormap(np.clip(v, -bound, bound)),
                "fillOpacity": 0.90, "color": "#2d3a30", "weight": 0.5}

    folium.GeoJson(
        geo, style_function=_style,
        highlight_function=lambda f: {"weight": 1.8, "color": "#0b6e3a"},
        tooltip=folium.GeoJsonTooltip(
            fields=["MPIO_CNMBR", "DEPTO"],
            aliases=["Municipio", "Departamento"],
            sticky=False, style=_TOOLTIP_STYLE,
        ),
    ).add_to(m)
    return st_folium(m, height=height, use_container_width=True,
                      returned_objects=["last_object_clicked"], key=key)
