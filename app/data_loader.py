"""Real data loading and preparation for Maíz dashboard."""
from __future__ import annotations

import os
import unicodedata
import re
from functools import lru_cache

import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Region grouping by department (Colombian standard 5-region split)
REGIONES_BY_DEPTO = {
    "Andina":    ["ANTIOQUIA", "BOYACA", "CALDAS", "CUNDINAMARCA", "HUILA", "NORTE DE SANTANDER",
                   "QUINDIO", "RISARALDA", "SANTANDER", "TOLIMA", "BOGOTA", "BOGOTA, D.C."],
    "Caribe":    ["ATLANTICO", "BOLIVAR", "CESAR", "CORDOBA", "LA GUAJIRA", "MAGDALENA",
                   "SAN ANDRES Y PROVIDENCIA", "SAN ANDRES", "SUCRE"],
    "Pacifica":  ["CAUCA", "CHOCO", "NARINO", "VALLE DEL CAUCA"],
    "Orinoquia": ["ARAUCA", "CASANARE", "META", "VICHADA"],
    "Amazonia":  ["AMAZONAS", "CAQUETA", "GUAINIA", "GUAVIARE", "PUTUMAYO", "VAUPES"],
}
REGIONES = list(REGIONES_BY_DEPTO.keys())
REGION_COLORS = {
    "Andina":    "#4ade80",
    "Caribe":    "#f59e0b",
    "Pacifica":  "#3b82f6",
    "Orinoquia": "#a78bfa",
    "Amazonia":  "#34d399",
}


def _norm(s: str) -> str:
    """Normalize a name for fuzzy matching: uppercase, remove accents, collapse spaces."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().upper()
    # Strip leading articles common in Spanish toponyms when matching is loose
    return s


def depto_to_region(depto: str) -> str:
    d = _norm(depto)
    for r, ds in REGIONES_BY_DEPTO.items():
        if d in [_norm(x) for x in ds]:
            return r
    return "Otra"


@st.cache_data(show_spinner="Cargando shapefile de municipios…")
def load_municipios() -> gpd.GeoDataFrame:
    """Load municipalities shapefile, project, compute centroids and a canonical key."""
    path = os.path.join(DATA_DIR, "municipios", "Municipios.shp")
    gdf = gpd.read_file(path)
    # Try multiple encodings — the .cpg sometimes lies; force a re-decode of the bad chars
    if gdf["MPIO_CNMBR"].astype(str).str.contains(r"�|�", regex=True).any():
        # Re-read forcing latin-1
        gdf = gpd.read_file(path, encoding="latin-1")

    gdf = gdf.to_crs(epsg=4326)

    # Compute centroids in a projected CRS to avoid warnings
    proj = gdf.to_crs(epsg=3116)  # MAGNA-SIRGAS / Colombia Bogota zone
    cent = proj.geometry.centroid.to_crs(epsg=4326)
    gdf["lon"] = cent.x.values
    gdf["lat"] = cent.y.values

    gdf["mpio_norm"] = gdf["MPIO_CNMBR"].apply(_norm)
    gdf["depto_norm"] = gdf["DEPTO"].apply(_norm)
    gdf["region"] = gdf["DEPTO"].apply(depto_to_region)
    gdf["dane_code"] = gdf["DPTO_CCDGO"].astype(str).str.zfill(2) + gdf["MPIO_CCDGO"].astype(str).str.zfill(3)
    return gdf


@st.cache_data(show_spinner="Cargando datos AGRONET (maíz)…")
def load_eva_maiz() -> pd.DataFrame:
    """Load the consolidated AGRONET EVA dataset filtered to maíz."""
    path = os.path.join(DATA_DIR, "agronet_eva_completo.csv")
    df = pd.read_csv(path)
    df = df[df["producto"].str.contains("MAIZ", na=False)].copy()
    df["mpio_norm"] = df["municipio"].apply(_norm)
    df["depto_norm"] = df["departamento"].apply(_norm)
    df["region"] = df["departamento"].apply(depto_to_region)
    df["anio"] = df["anio"].astype(int)
    # Group different maíz subtypes per (muni, year) — sum production/area, weighted yield
    agg = (
        df.groupby(["depto_norm", "mpio_norm", "departamento", "municipio", "region", "anio"], as_index=False)
        .agg(
            area_sembrada=("area_sembrada", "sum"),
            area_cosechada=("area_cosechada", "sum"),
            produccion=("produccion", "sum"),
        )
    )
    agg["rendimiento"] = np.where(agg["area_cosechada"] > 0,
                                   agg["produccion"] / agg["area_cosechada"], np.nan)
    # Robust outlier removal: remove zeros and very extreme yield (e.g. > 99th percentile or > 15)
    agg = agg[agg["rendimiento"] > 0]
    upper_limit = min(agg["rendimiento"].quantile(0.995), 15)
    agg = agg[agg["rendimiento"] <= upper_limit]
    return agg


@st.cache_data(show_spinner="Cargando ENSO Niño 3.4…")
def load_enso() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "enso_nino34.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


@st.cache_data(show_spinner="Cargando indicadores TerriData…")
def load_terridata_features() -> pd.DataFrame:
    """Load TerriData socio-economic indicators by municipality (latest year per indicator).
    Cached to parquet after first build for speed."""
    cache = os.path.join(DATA_DIR, "_terridata_features_cache.parquet")
    if os.path.exists(cache):
        try:
            return pd.read_parquet(cache)
        except Exception:
            pass

    out = []
    # Use exact-as-it-appears-in-the-file substrings (the .xlsx has Latin-1 mojibake
    # in column headers and indicator names but substring matches still work).
    targets = {
        # file: (indicator substring, output column)
        "TerriData_Dim3.xlsx":  ("Cobertura de energ", "cob_energia"),
        "TerriData_Dim15.xlsx": ("Recaudo efectivo por impuesto predial", "recaudo_predial"),
    }
    for fname, (needle, col) in targets.items():
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            continue
        try:
            df = pd.read_excel(fpath)
        except Exception:
            continue
        # Find columns by position, not by name (mojibake in headers)
        cod_col = df.columns[2]   # Código Entidad
        ind_col = df.columns[6]   # Indicador
        val_col = df.columns[7]   # Dato Numérico
        anio_col = df.columns[9]  # Año
        df = df[df[ind_col].astype(str).str.contains(needle, na=False)].copy()
        if df.empty:
            continue
        df = df.dropna(subset=[cod_col])
        df = df.sort_values(anio_col).drop_duplicates([cod_col], keep="last")
        df = df[[cod_col, val_col]].rename(columns={cod_col: "dane_code", val_col: col})
        # Codes come in as floats — convert to int then zero-pad to 5 chars
        df["dane_code"] = (df["dane_code"].astype(float).astype("Int64").astype(str)
                                          .str.zfill(5))
        # TerriData stores values as text with comma decimal separator ("95,79").
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(".", "", regex=False)
                              .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        out.append(df.set_index("dane_code")[[col]])
    if not out:
        return pd.DataFrame()
    feat = pd.concat(out, axis=1).reset_index()
    try:
        feat.to_parquet(cache)
    except Exception:
        pass
    return feat


@st.cache_data(show_spinner="Construyendo dataset maestro…")
def build_master(include_terridata: bool = False) -> pd.DataFrame:
    """Join EVA maíz + shapefile centroids + region. Optionally TerriData features."""
    gdf = load_municipios()
    eva = load_eva_maiz()

    geo = gdf[["dane_code", "MPIO_CNMBR", "DEPTO", "lat", "lon", "region",
                "mpio_norm", "depto_norm"]].copy()
    geo = geo.rename(columns={"MPIO_CNMBR": "muni_shape", "DEPTO": "depto_shape"})

    # Merge on (depto_norm, mpio_norm)
    merged = eva.merge(
        geo[["dane_code", "lat", "lon", "depto_norm", "mpio_norm"]],
        on=["depto_norm", "mpio_norm"], how="inner"
    )

    if include_terridata:
        feats = load_terridata_features()
        if not feats.empty:
            merged = merged.merge(feats, on="dane_code", how="left")

    # Clean and bound
    merged = merged.dropna(subset=["lat", "lon", "rendimiento"])
    merged["rendimiento"] = merged["rendimiento"].clip(0, 15)
    return merged


@st.cache_data
def years_available(df: pd.DataFrame) -> list[int]:
    return sorted(df["anio"].unique().tolist())


def filter_data(df: pd.DataFrame, year: int | None = None,
                region: str | None = None) -> pd.DataFrame:
    out = df
    if year is not None:
        out = out[out["anio"] == year]
    if region and region != "Todas":
        out = out[out["region"] == region]
    return out
