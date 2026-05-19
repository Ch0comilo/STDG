"""Producción Agrícola de Maíz — Colombia.

Streamlit dashboard implementing the design from
producci-n-agr-cola/project/Producción Agrícola - Streamlit v2.html
with REAL data (AGRONET EVA + DANE municipios shapefile).
"""
from __future__ import annotations

import streamlit as st

from theme import inject_css, topbar, PALETTE
from data_loader import build_master, REGIONES, years_available
from pages_modules.landing import render as render_landing
from pages_modules.panorama import render as render_panorama
from pages_modules.clima import render as render_clima
from pages_modules.territorio import render as render_territorio
from pages_modules.modelo import render as render_modelo
from pages_modules.tecnico import render as render_tecnico


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
df = build_master()

# If expected columns are missing (stale cache from a previous schema),
# clear all caches and rerun once so build_master executes fresh.
required_cols = {"prcp_anual", "cob_energia_rural", "uso_adecuado_pct"}
if not required_cols.issubset(df.columns) and not st.session_state.get("_cache_cleared"):
    st.session_state["_cache_cleared"] = True
    st.cache_data.clear()
    st.rerun()
YEARS = years_available(df)


NAV = [
    ("landing",   "★ Maíz Inteligente",  "Presentación · propuesta de valor",          render_landing),
    ("panorama",  "◈ Panorama",           "Mapa kriging · KPIs · pies regionales",     render_panorama),
    ("clima",     "🌡 Clima",              "Precipitación · temperatura · ENSO",         render_clima),
    ("territorio","⬢ Territorio",          "TerriData · infraestructura · uso suelo",    render_territorio),
    ("modelo",    "◆ Modelo Lineal",      "OLS+Ridge · supuestos · VIF · diagnóstico",  render_modelo),
    ("tecnico",   "⬡ Detalle Técnico",    "Moran · LISA · variograma · kriging",        render_tecnico),
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

    # Sidebar info — the single model lives here
    if page_id == "modelo":
        st.markdown(f"<div style='border-top:1px solid {PALETTE['border_2']}; "
                    f"margin-top:14px; padding-top:14px;'>"
                    f"<div style='font-size:10px; color:{PALETTE['text_dim']}; "
                    f"text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;'>"
                    f"Modelo</div>"
                    f"<div style='font-size:12px; color:{PALETTE['text']};'>"
                    f"Regresión lineal · OLS + Ridge<br>"
                    f"<span style='color:{PALETTE['text_dimmer']}; font-size:11px;'>"
                    f"α tunado via CV 5-fold</span></div></div>",
                    unsafe_allow_html=True)


# ── Top bar + Page content ────────────────────────────────────────────────────
renderer = next(n[3] for n in NAV if n[0] == page_id)

if page_id == "landing":
    renderer()
else:
    page_label = next(n[1] for n in NAV if n[0] == page_id).split(" ", 1)[1]
    topbar(page_label, year, region)
    renderer(df=df, year=year, region=region)
