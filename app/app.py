"""Producción Agrícola de Maíz — Colombia.

Streamlit dashboard implementing the design from
producci-n-agr-cola/project/Producción Agrícola - Streamlit v2.html
with REAL data (AGRONET EVA + DANE municipios shapefile).
"""
from __future__ import annotations

import streamlit as st

from theme import inject_css, topbar, PALETTE
from data_loader import build_master, REGIONES, years_available
from pages_modules.eda import render as render_eda
from pages_modules.moran import render as render_moran
from pages_modules.ml import render as render_ml
from pages_modules.kriging import render as render_kriging
from pages_modules.comparacion import render as render_comp


st.set_page_config(
    page_title="Producción Agrícola de Maíz — Colombia",
    page_icon="🌽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# Persistent floating "Menú" button.
# We inject it into the PARENT document (so it survives Streamlit re-runs that
# unmount this component's iframe) and use a MutationObserver to re-attach it
# if Streamlit ever wipes it out.
import streamlit.components.v1 as components
components.html("""
<script>
(function () {
  const pdoc = window.parent.document;
  const BTN_ID = 'agro-menu-btn';
  const STYLE_ID = 'agro-menu-btn-style';

  function ensureStyle() {
    if (pdoc.getElementById(STYLE_ID)) return;
    const s = pdoc.createElement('style');
    s.id = STYLE_ID;
    s.textContent = `
      #${BTN_ID} {
        position: fixed !important;
        top: 8px; left: 12px;
        z-index: 2147483647;
        background: #3f9b48; color: #fff; border: none;
        border-radius: 8px; padding: 7px 14px;
        font: 600 12px/1 'IBM Plex Sans', system-ui, sans-serif;
        letter-spacing: 0.04em; cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.45);
      }
      #${BTN_ID}:hover { background: #4daf57; }
    `;
    pdoc.head.appendChild(s);
  }

  function findToggle() {
    return pdoc.querySelector('[data-testid="stSidebarCollapsedControl"] button')
        || pdoc.querySelector('[data-testid="stSidebarCollapseButton"] button')
        || pdoc.querySelector('[data-testid="collapsedControl"] button')
        || pdoc.querySelector('button[kind="header"]');
  }

  function ensureButton() {
    ensureStyle();
    if (pdoc.getElementById(BTN_ID)) return;
    const b = pdoc.createElement('button');
    b.id = BTN_ID;
    b.type = 'button';
    b.innerHTML = '&#9776; Menú';
    b.addEventListener('click', (e) => {
      e.preventDefault();
      const t = findToggle();
      if (t) t.click();
    });
    pdoc.body.appendChild(b);
  }

  ensureButton();

  // If Streamlit ever blows away the button (rerun, theme switch, etc.),
  // a single MutationObserver re-creates it. Idempotent.
  if (!window.parent.__agroMenuObserver) {
    const obs = new MutationObserver(() => ensureButton());
    obs.observe(pdoc.body, { childList: true, subtree: false });
    window.parent.__agroMenuObserver = obs;
  }
})();
</script>
""", height=0)

# ── Load data once ────────────────────────────────────────────────────────────
include_terridata = st.session_state.get("include_terridata", False)
df = build_master(include_terridata=include_terridata)
YEARS = years_available(df)


NAV = [
    ("eda",    "◈ EDA Espacial",       "Mapas · históricos · ranking",      render_eda),
    ("moran",  "⬡ Autocorrelación",    "Moran · LISA · clusters",            render_moran),
    ("ml",     "◆ Modelos ML",          "RF · XGBoost · Lasso · GWR",         render_ml),
    ("kriging","◉ Kriging Residuos",    "Variograma · mapa residuos",         render_kriging),
    ("comp",   "▦ Comparación",         "Tabla RMSE/MAE · scatter",           render_comp),
]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px; padding:6px 0 12px 0;
                    border-bottom: 1px solid {PALETTE['border_2']}; margin-bottom:14px;">
          <div style="width:32px; height:32px; border-radius:8px; flex-shrink:0;
                      background:{PALETTE['accent']}; display:flex; align-items:center;
                      justify-content:center; font-size:18px;">🌽</div>
          <div>
            <div style="font-size:13px; font-weight:700; color:{PALETTE['accent_hi']};
                        line-height:1.3;">Producción Agrícola</div>
            <div style="font-size:10px; color:{PALETTE['text_dimmer']};
                        font-family:'IBM Plex Mono', monospace;">Maíz · Colombia · {YEARS[0]}–{YEARS[-1]}</div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown(f"<div style='font-size:9px; color:{PALETTE['text_dimmer']}; "
                f"text-transform:uppercase; letter-spacing:0.10em; margin-bottom:4px;'>"
                f"Secciones</div>", unsafe_allow_html=True)

    page_id = st.radio(
        "Sección",
        options=[n[0] for n in NAV],
        format_func=lambda i: next(n[1] for n in NAV if n[0] == i),
        label_visibility="collapsed",
        key="nav_page",
    )

    st.markdown(f"<div style='border-top:1px solid {PALETTE['border_2']}; "
                f"margin-top:14px; padding-top:14px;'>"
                f"<div style='font-size:9px; color:{PALETTE['text_dimmer']}; "
                f"text-transform:uppercase; letter-spacing:0.10em; margin-bottom:8px;'>Filtros</div>"
                f"</div>", unsafe_allow_html=True)

    year = st.selectbox("Año", YEARS, index=len(YEARS) - 1)
    region = st.selectbox("Región", ["Todas"] + REGIONES, index=0)

    new_terridata = st.checkbox(
        "Incluir indicadores TerriData",
        value=include_terridata,
        help="Suma covariables socio-económicas por municipio (cobertura energía, "
             "recaudo predial). Primer carga puede tardar 2-4 min, luego cachea.",
        key="include_terridata_widget",
    )
    if new_terridata != include_terridata:
        st.session_state["include_terridata"] = new_terridata
        st.rerun()

    # Page-specific controls slot — pages can read these via session_state
    if page_id == "ml":
        st.markdown(f"<div style='border-top:1px solid {PALETTE['border_2']}; "
                    f"margin-top:14px; padding-top:14px;'>"
                    f"<div style='font-size:9px; color:{PALETTE['text_dimmer']}; "
                    f"text-transform:uppercase; letter-spacing:0.10em; margin-bottom:8px;'>"
                    f"Hiper-parámetros</div></div>", unsafe_allow_html=True)
        st.session_state["model"] = st.selectbox(
            "Modelo", ["Random Forest", "XGBoost", "Lasso/Ridge", "KNN espacial"], key="model_sel"
        )
        if st.session_state["model"] == "Random Forest":
            st.session_state["n_trees"] = st.slider("N° árboles", 10, 500, 200, 10)
            st.session_state["max_depth"] = st.slider("Max depth", 2, 20, 8)
        elif st.session_state["model"] == "XGBoost":
            st.session_state["n_trees"] = st.slider("N° árboles", 10, 500, 200, 10)
            st.session_state["max_depth"] = st.slider("Max depth", 2, 12, 5)
        elif st.session_state["model"] == "Lasso/Ridge":
            st.session_state["alpha"] = st.slider("Alpha (λ)", 0.001, 1.0, 0.1, 0.001)


# ── Top bar + Page content ────────────────────────────────────────────────────
page_label = next(n[1] for n in NAV if n[0] == page_id).split(" ", 1)[1]
topbar(page_label, year, region)

renderer = next(n[3] for n in NAV if n[0] == page_id)
renderer(df=df, year=year, region=region)
