"""Real data loading and preparation for Maíz dashboard."""
from __future__ import annotations

import glob
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
    agg = agg[(agg["area_cosechada"] > 0) & (agg["rendimiento"] > 0) & (agg["rendimiento"] < 20)]
    return agg


@st.cache_data(show_spinner="Cargando ENSO Niño 3.4…")
def load_enso() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "enso_nino34.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


@st.cache_data(show_spinner="Extrayendo variables climáticas por municipio…")
def load_climate_by_muni() -> pd.DataFrame:
    """Build (dane_code, anio, prcp_anual, tmed_anual, enso_anual) from gridded NetCDF + ENSO.

    Samples each municipality centroid from ndpr_anio/ (annual precip) and
    tmed_mes_prom/ (monthly temperature, averaged to annual). Caches to parquet.
    """
    cache = os.path.join(DATA_DIR, "_climate_features_cache.parquet")
    if os.path.exists(cache):
        try:
            return pd.read_parquet(cache)
        except Exception:
            pass

    try:
        import xarray as xr
    except ImportError:
        return pd.DataFrame()

    gdf = load_municipios()
    muni_pts = gdf[["dane_code", "lat", "lon"]].drop_duplicates("dane_code").reset_index(drop=True)
    lat_arr = muni_pts["lat"].values
    lon_arr = muni_pts["lon"].values

    # ENSO annual mean
    enso_df = load_enso()
    enso_annual: pd.DataFrame = pd.DataFrame()
    if not enso_df.empty:
        seas_cols = [c for c in enso_df.columns if c != "year"]
        enso_annual = enso_df[["year"]].copy()
        enso_annual["enso_anual"] = enso_df[seas_cols].mean(axis=1)
        enso_annual = enso_annual.rename(columns={"year": "anio"})

    prcp_dir = os.path.join(DATA_DIR, "ndpr_anio")
    tmed_dir = os.path.join(DATA_DIR, "tmed_mes_prom")
    prcp_files = sorted(glob.glob(os.path.join(prcp_dir, "ndpr_*.nc")))
    if not prcp_files:
        return pd.DataFrame()

    # Read coordinate arrays once
    with xr.open_dataset(prcp_files[0]) as ds0:
        lats = ds0["Lat"].values
        lons = ds0["Lon"].values

    # Vectorised nearest-grid-cell lookup for all municipalities
    lat_idx = np.argmin(np.abs(lats[:, None] - lat_arr[None, :]), axis=0)
    lon_idx = np.argmin(np.abs(lons[:, None] - lon_arr[None, :]), axis=0)

    records = []
    for fpath in prcp_files:
        year_str = os.path.basename(fpath).replace("ndpr_", "").replace(".nc", "")
        try:
            year = int(year_str)
        except ValueError:
            continue

        with xr.open_dataset(fpath) as ds:
            prcp_grid = ds["ndpr"].values.astype(float)
        prcp_vals = prcp_grid[lat_idx, lon_idx]
        prcp_vals[prcp_vals < 0] = np.nan  # sentinel fill values

        # Annual temperature: mean of available monthly files
        monthly = []
        for month in range(1, 13):
            tfile = os.path.join(tmed_dir, f"tmed_{year}{month:02d}.nc")
            if os.path.exists(tfile):
                try:
                    with xr.open_dataset(tfile) as ds_t:
                        tgrid = ds_t["tmpr"].values.astype(float)
                    tgrid[tgrid < -100] = np.nan
                    monthly.append(tgrid[lat_idx, lon_idx])
                except Exception:
                    pass
        tmpr_vals = np.nanmean(monthly, axis=0) if monthly else np.full(len(muni_pts), np.nan)

        for i in range(len(muni_pts)):
            records.append({
                "dane_code": muni_pts.at[i, "dane_code"],
                "anio": year,
                "prcp_anual": float(prcp_vals[i]),
                "tmed_anual": float(tmpr_vals[i]),
            })

    if not records:
        return pd.DataFrame()

    feat = pd.DataFrame(records)
    if not enso_annual.empty:
        feat = feat.merge(enso_annual, on="anio", how="left")

    try:
        feat.to_parquet(cache)
    except Exception:
        pass
    return feat


@st.cache_data(show_spinner="Cargando indicadores TerriData…")
def load_terridata_features() -> pd.DataFrame:
    """Load TerriData socio-economic indicators per municipality.

    Now pulls SIX indicators that have a defensible link to maíz yield:

      cob_energia_rural  · Dim3  · electrification → mechanization access
      banda_ancha        · Dim3  · connectivity   → AgTech adoption
      ingresos_totales   · Dim7  · fiscal capacity → can the muni invest?
      uso_adecuado_pct   · Dim15 · % land in 'uso adecuado'
      sobreutil_pct      · Dim15 · % land overused → soil degradation
      recaudo_predial    · Dim15 · property tax efficiency → governance

    Indicator substrings are matched on the raw cell text (the .xlsx headers
    arrive Latin-1 mojibaked but substring matching is fine). Cached to parquet
    so re-loads are instant.
    """
    cache = os.path.join(DATA_DIR, "_terridata_features_cache.parquet")
    if os.path.exists(cache):
        try:
            cached = pd.read_parquet(cache)
            # Bust the cache if the schema doesn't include the new columns
            required = {"cob_energia_rural", "banda_ancha", "ingresos_totales",
                        "uso_adecuado_pct", "sobreutil_pct", "recaudo_predial"}
            if required.issubset(set(cached.columns)):
                return cached
        except Exception:
            pass

    # (file, indicator substring, output column).
    # NB: substrings must be specific enough to avoid matching neighbouring
    # rows (e.g. "Uso adecuado" alone would also catch the percentage row).
    targets = [
        ("TerriData_Dim3.xlsx",  "Cobertura de energ",                  "cob_energia_rural"),
        ("TerriData_Dim3.xlsx",  "Penetraci",                            "banda_ancha"),
        ("TerriData_Dim7.xlsx",  "Ingresos totales",                     "ingresos_totales"),
        ("TerriData_Dim15.xlsx", "Porcentaje - Uso adecuado",            "uso_adecuado_pct"),
        ("TerriData_Dim15.xlsx", "Porcentaje conflicto - Sobreutilizaci", "sobreutil_pct"),
        ("TerriData_Dim15.xlsx", "Recaudo efectivo por impuesto predial", "recaudo_predial"),
    ]
    # Read each file at most once
    file_cache: dict[str, pd.DataFrame] = {}
    out = []
    for fname, needle, col in targets:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            continue
        if fname not in file_cache:
            try:
                file_cache[fname] = pd.read_excel(fpath)
            except Exception:
                continue
        df = file_cache[fname]
        cod_col = df.columns[2]
        ind_col = df.columns[6]
        val_col = df.columns[7]
        anio_col = df.columns[9]
        m = df[df[ind_col].astype(str).str.contains(needle, na=False, regex=False)].copy()
        if m.empty:
            continue
        m = m.dropna(subset=[cod_col])
        m = m.sort_values(anio_col).drop_duplicates([cod_col], keep="last")
        m = m[[cod_col, val_col]].rename(columns={cod_col: "dane_code", val_col: col})
        m["dane_code"] = (m["dane_code"].astype(float).astype("Int64").astype(str)
                                          .str.zfill(5))
        m[col] = pd.to_numeric(
            m[col].astype(str).str.replace(".", "", regex=False)
                              .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        out.append(m.set_index("dane_code")[[col]])
    if not out:
        return pd.DataFrame()
    feat = pd.concat(out, axis=1).reset_index()
    try:
        feat.to_parquet(cache)
    except Exception:
        pass
    return feat


@st.cache_data(show_spinner="Construyendo dataset maestro…")
def build_master() -> pd.DataFrame:
    """Join EVA maíz + shapefile centroids + climate + TerriData socio-economics.

    TerriData is no longer optional — it carries real signal (energía rural,
    banda ancha, uso del suelo, recaudo predial) that we want in the model
    and on its own dashboard page.
    """
    gdf = load_municipios()
    eva = load_eva_maiz()

    geo = gdf[["dane_code", "MPIO_CNMBR", "DEPTO", "lat", "lon", "region",
                "mpio_norm", "depto_norm"]].copy()
    geo = geo.rename(columns={"MPIO_CNMBR": "muni_shape", "DEPTO": "depto_shape"})

    merged = eva.merge(
        geo[["dane_code", "lat", "lon", "depto_norm", "mpio_norm"]],
        on=["depto_norm", "mpio_norm"], how="inner"
    )

    climate = load_climate_by_muni()
    if not climate.empty:
        merged = merged.merge(climate, on=["dane_code", "anio"], how="left")

    # TerriData — always included (NOT optional anymore)
    feats = load_terridata_features()
    if not feats.empty:
        merged = merged.merge(feats, on="dane_code", how="left")

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
