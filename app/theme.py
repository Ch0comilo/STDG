"""Theme constants and CSS injection for the Maíz dashboard.

Dark forest-green shell with high-contrast cards and bright choropleth palette.
Fonts intentionally bumped to feel like a real dashboard, not a slide deck.
"""
import streamlit as st


PALETTE = {
    "bg":          "#161e18",
    "panel":       "#1b251e",
    "panel_alt":   "#1d2820",
    "card":        "#243027",
    "card_light":  "#eef2ee",   # for map containers — high contrast
    "border":      "#2f3d33",
    "border_2":    "#2a3830",
    "text":        "#f0f6f1",
    "text_dim":    "#b4c2b8",
    "text_dimmer": "#94a39a",
    "accent":      "#4dbb58",
    "accent_hi":   "#86e88f",
    "amber":       "#f0b34a",
    "ok":          "#5ee08a",
    "warn":        "#f59e0b",
    "bad":         "#f87171",
    "info":        "#60a5fa",
    "purple":      "#b9a4ff",
}

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font": {"family": "IBM Plex Sans, sans-serif", "color": "#e6efe9", "size": 13},
    "xaxis": {"gridcolor": "rgba(255,255,255,0.09)", "zerolinecolor": "rgba(255,255,255,0.14)",
              "tickfont": {"color": "#cbd5d0", "size": 12},
              "title": {"font": {"color": "#cbd5d0", "size": 13}}},
    "yaxis": {"gridcolor": "rgba(255,255,255,0.09)", "zerolinecolor": "rgba(255,255,255,0.14)",
              "tickfont": {"color": "#cbd5d0", "size": 12},
              "title": {"font": {"color": "#cbd5d0", "size": 13}}},
    "margin": {"l": 56, "r": 24, "t": 36, "b": 46},
    "legend": {"font": {"color": "#e6efe9", "size": 12}, "bgcolor": "rgba(0,0,0,0)"},
    "hoverlabel": {"bgcolor": "#243027", "bordercolor": "#5ee08a",
                    "font": {"color": "#f0f6f1", "size": 13}},
}

# Brighter choropleth scale — visible on a light or dark base. Yellow → orange → green.
CHORO_SCALE = [
    [0.00, "#fff5b8"],
    [0.20, "#ffd166"],
    [0.45, "#ff9f1c"],
    [0.70, "#3dab5a"],
    [1.00, "#0b6e3a"],
]

# Diverging palette for residuals (red ↔ neutral ↔ green)
DIVERGING_SCALE = [
    [0.00, "#c0392b"],
    [0.25, "#e67e22"],
    [0.50, "#f7f3d3"],
    [0.75, "#5ee08a"],
    [1.00, "#117a3d"],
]

# Categorical palette (regions, LISA, etc.)
CAT_PALETTE = ["#5ee08a", "#f0b34a", "#60a5fa", "#b9a4ff", "#34d399", "#f87171"]


def inject_css() -> None:
    """Inject the dark forest-green theme with bigger typography."""
    st.markdown(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

      html, body, [class*="st-"], [class*="css-"] {{
        font-family: 'IBM Plex Sans', sans-serif !important;
      }}

      .stApp {{
        background: {PALETTE['bg']} !important;
        color: {PALETTE['text']} !important;
      }}

      /* Sidebar */
      section[data-testid="stSidebar"] > div {{
        background: {PALETTE['panel']} !important;
        border-right: 1px solid {PALETTE['border_2']};
      }}
      section[data-testid="stSidebar"] * {{ color: {PALETTE['text']}; }}

      /* Bigger, bolder headings */
      h1 {{ font-size: 30px !important; font-weight: 700 !important; color: {PALETTE['text']} !important; }}
      h2 {{ font-size: 22px !important; font-weight: 700 !important; color: {PALETTE['text']} !important; }}
      h3 {{ font-size: 17px !important; font-weight: 600 !important; color: {PALETTE['text']} !important; }}
      h4 {{ font-size: 14px !important; font-weight: 600 !important; color: {PALETTE['text']} !important; }}

      [data-testid="stHeader"] {{ background: transparent !important; }}

      /* Widget labels */
      .stSelectbox label, .stSlider label, .stRadio label, .stMultiSelect label,
      .stCheckbox label {{
        font-size: 12px !important;
        color: {PALETTE['text_dim']} !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600 !important;
      }}
      div[data-baseweb="select"] > div {{
        background: {PALETTE['card']} !important;
        border: 1px solid {PALETTE['border']} !important;
        border-radius: 6px !important;
        font-size: 14px !important;
      }}
      div[data-baseweb="select"] svg {{ color: {PALETTE['accent_hi']}; }}
      .stSlider [data-baseweb="slider"] div[role="slider"] {{
        background-color: {PALETTE['accent']} !important;
        border-color: {PALETTE['accent']} !important;
      }}

      /* Sidebar nav radio */
      .stRadio > div {{ flex-direction: column; gap: 4px; }}
      .stRadio label {{
        background: transparent;
        border-radius: 7px;
        padding: 11px 12px !important;
        border-left: 3px solid transparent;
        transition: all 0.12s ease;
        font-size: 13px !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
      }}
      .stRadio label:hover {{ background: rgba(94, 224, 138, 0.10); }}
      .stRadio [data-checked="true"] {{
        background: rgba(94, 224, 138, 0.16) !important;
        border-left: 3px solid {PALETTE['accent']} !important;
      }}

      /* Tables */
      .stDataFrame, .stTable {{
        background: {PALETTE['panel_alt']};
        border-radius: 10px;
        border: 1px solid {PALETTE['border']};
      }}
      .stDataFrame [role="cell"] {{ font-size: 13px !important; }}

      /* Card container */
      .agro-card {{
        background: {PALETTE['panel_alt']};
        border: 1px solid {PALETTE['border']};
        border-radius: 12px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
      }}
      .agro-card-title {{
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: {PALETTE['accent_hi']};
        margin-bottom: 14px;
        text-transform: uppercase;
      }}

      /* Map card — lighter background to improve contrast with cartodbpositron */
      .agro-card-map {{
        background: {PALETTE['panel_alt']};
        border: 1px solid {PALETTE['border']};
        border-radius: 12px;
        padding: 16px 16px 12px 16px;
        margin-bottom: 18px;
      }}

      /* Metric — visibly bigger */
      .agro-metric {{
        background: {PALETTE['card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 10px;
        padding: 18px 22px;
      }}
      .agro-metric-label {{
        font-size: 13px;
        color: {PALETTE['text_dim']};
        margin-bottom: 6px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      .agro-metric-value {{
        font-size: 32px;
        font-weight: 700;
        font-family: 'IBM Plex Mono', monospace;
        line-height: 1.1;
      }}
      .agro-metric-unit {{
        font-size: 14px;
        margin-left: 6px;
        color: {PALETTE['text_dimmer']};
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
      }}
      .agro-metric-sub {{
        font-size: 12px;
        color: {PALETTE['text_dimmer']};
        margin-top: 6px;
        font-weight: 500;
      }}

      /* Tags */
      .agro-tag {{
        background: rgba(94,224,138,0.18);
        color: {PALETTE['accent_hi']};
        border: 1px solid rgba(94,224,138,0.35);
        border-radius: 4px;
        padding: 2px 10px;
        font-size: 12px;
        font-family: 'IBM Plex Mono', monospace;
        margin-right: 6px;
        font-weight: 600;
      }}
      .agro-tag.amber {{
        background: rgba(240,179,74,0.18);
        color: {PALETTE['amber']};
        border: 1px solid rgba(240,179,74,0.35);
      }}

      /* Alert */
      .agro-alert {{
        background: {PALETTE['panel_alt']};
        border: 1px solid rgba(94,224,138,0.32);
        border-left: 4px solid {PALETTE['accent']};
        border-radius: 10px;
        padding: 14px 18px;
        margin: 14px 0;
        color: {PALETTE['text']};
        line-height: 1.7;
        font-size: 14px;
      }}
      .agro-alert.bad {{
        border-color: rgba(248,113,113,0.45);
        border-left-color: {PALETTE['bad']};
      }}
      .agro-alert.amber {{
        border-color: rgba(240,179,74,0.45);
        border-left-color: {PALETTE['amber']};
      }}
      .agro-alert ul {{ margin: 8px 0 0 18px; padding: 0; }}
      .agro-alert li {{ margin-bottom: 4px; }}

      /* Top bar */
      .agro-topbar {{
        background: {PALETTE['panel']};
        border-bottom: 1px solid {PALETTE['border_2']};
        padding: 14px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -1.2rem -1.2rem 1.4rem -1.2rem;
      }}
      .agro-topbar .left {{ display:flex; align-items:center; gap:12px; }}
      .agro-topbar .pageLabel {{
        font-size: 16px; font-weight:700; color:{PALETTE['text']};
      }}
      .agro-topbar .sep {{ font-size:13px; color:{PALETTE['text_dimmer']}; }}
      .agro-topbar .right {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px; color: {PALETTE['text_dim']};
      }}
      .agro-status-dot {{
        width:8px; height:8px; border-radius:50%;
        background:#5ee08a; box-shadow: 0 0 8px #5ee08a88;
        display:inline-block; margin-left:8px;
      }}

      /* Hide Streamlit chrome */
      #MainMenu, footer {{ visibility: hidden; }}
      header[data-testid="stHeader"] {{
        background: transparent !important;
        height: auto !important;
      }}
      header[data-testid="stHeader"] > * {{ visibility: hidden; }}
      [data-testid="stSidebarCollapsedControl"],
      [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
      }}

      .block-container {{
        padding-top: 1.4rem !important;
        padding-bottom: 1.4rem !important;
        max-width: 100% !important;
      }}

      /* Folium iframe */
      iframe.folium-map {{
        border-radius: 10px;
        border: 1px solid {PALETTE['border']};
      }}

      [data-testid="stMetric"] {{
        background: {PALETTE['card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 10px;
        padding: 14px 18px;
      }}

      /* Streamlit native paragraph and list */
      p, li, span {{ font-size: 14px; }}

      /* Buttons */
      .stButton > button {{
        background: {PALETTE['card']} !important;
        color: {PALETTE['text']} !important;
        border: 1px solid {PALETTE['border']} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 9px 14px !important;
      }}
      .stButton > button:hover {{
        background: {PALETTE['accent']} !important;
        color: #0a1410 !important;
        border-color: {PALETTE['accent']} !important;
      }}

      /* Scrollbar */
      ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
      ::-webkit-scrollbar-track {{ background: {PALETTE['panel']}; }}
      ::-webkit-scrollbar-thumb {{ background: rgba(180,210,190,0.25); border-radius: 4px; }}
    </style>
    """, unsafe_allow_html=True)


def metric(label: str, value: str, unit: str = "", color: str | None = None,
           sub: str | None = None) -> str:
    """Render a big metric tile."""
    color = color or PALETTE["accent_hi"]
    sub_html = (f'<div class="agro-metric-sub">{sub}</div>' if sub else "")
    return f"""
    <div class="agro-metric">
      <div class="agro-metric-label">{label}</div>
      <div class="agro-metric-value" style="color:{color}">{value}<span class="agro-metric-unit">{unit}</span></div>
      {sub_html}
    </div>
    """


def card_header(title: str) -> str:
    return f'<div class="agro-card-title">{title}</div>'


def alert(text: str, kind: str = "ok") -> str:
    cls = "" if kind == "ok" else kind
    return f'<div class="agro-alert {cls}">{text}</div>'


def topbar(page_label: str, year: int, region: str) -> None:
    region_tag = f'<span class="agro-tag amber">{region}</span>' if region != "Todas" else ""
    st.markdown(f"""
    <div class="agro-topbar">
      <div class="left">
        <span class="pageLabel">{page_label}</span>
        <span class="sep">·</span>
        <span style="font-size:13px;color:#94a39a">Maíz</span>
        <span class="agro-tag">{year}</span>
        {region_tag}
      </div>
      <div class="right">
        Estadística Espacial + Modelo Lineal · Maíz Inteligente
        <span class="agro-status-dot"></span>
      </div>
    </div>
    """, unsafe_allow_html=True)
