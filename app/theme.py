"""Theme constants and CSS injection for the Maíz dashboard.

Mirrors the dark forest-green aesthetic from the design handoff
(Producción Agrícola - Streamlit v2.html).
"""
import streamlit as st


# Hex palette — used everywhere (Plotly does not accept oklch).
PALETTE = {
    "bg":          "#161e18",   # ~oklch(14% 0.03 145)
    "panel":       "#1b251e",   # ~oklch(17% 0.03 145)
    "panel_alt":   "#1d2820",   # ~oklch(18% 0.03 145)
    "card":        "#243027",   # ~oklch(22% 0.03 145)
    "border":      "#2f3d33",   # ~oklch(28% 0.04 145)
    "border_2":    "#2a3830",   # ~oklch(25% 0.04 145)
    "text":        "#e6efe9",   # ~oklch(92% 0.02 145)
    "text_dim":    "#9aa89e",   # ~oklch(60% 0.04 145)
    "text_dimmer": "#7d8a82",   # ~oklch(50% 0.04 145)
    "accent":      "#3f9b48",   # ~oklch(52% 0.18 148)
    "accent_hi":   "#6cd676",   # ~oklch(72% 0.16 145)
    "amber":       "#d99e30",   # ~oklch(68% 0.16 72)
    "ok":          "#4ade80",
    "warn":        "#f59e0b",
    "bad":         "#f87171",
    "info":        "#3b82f6",
    "purple":      "#a78bfa",
}

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font": {"family": "IBM Plex Sans, sans-serif", "color": "#cfd8d2", "size": 11},
    "xaxis": {"gridcolor": "rgba(255,255,255,0.06)", "zerolinecolor": "rgba(255,255,255,0.10)",
              "tickfont": {"color": "#9aa89e"}, "title": {"font": {"color": "#9aa89e"}}},
    "yaxis": {"gridcolor": "rgba(255,255,255,0.06)", "zerolinecolor": "rgba(255,255,255,0.10)",
              "tickfont": {"color": "#9aa89e"}, "title": {"font": {"color": "#9aa89e"}}},
    "margin": {"l": 50, "r": 20, "t": 30, "b": 40},
    "legend": {"font": {"color": "#cfd8d2"}, "bgcolor": "rgba(0,0,0,0)"},
    "hoverlabel": {"bgcolor": "#1d251f", "bordercolor": "#3b4d40",
                    "font": {"color": "#e6efe9"}},
}

# Choropleth scale: cream → yellow-green → forest
CHORO_SCALE = [
    [0.00, "#f7f3d3"],
    [0.20, "#dceb9a"],
    [0.45, "#a3d36a"],
    [0.70, "#3f9b48"],
    [1.00, "#0f4d2a"],
]


def inject_css() -> None:
    """Inject the dark forest-green theme into the Streamlit document."""
    st.markdown(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

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
      section[data-testid="stSidebar"] * {{
        color: {PALETTE['text']};
      }}

      /* Headings */
      h1, h2, h3, h4 {{
        color: {PALETTE['text']} !important;
        font-weight: 600 !important;
        letter-spacing: -0.005em;
      }}

      /* Headers in main */
      [data-testid="stHeader"] {{ background: transparent !important; }}

      /* Native widget look */
      .stSelectbox label, .stSlider label, .stRadio label, .stMultiSelect label {{
        font-size: 10px !important;
        color: {PALETTE['text_dimmer']} !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      div[data-baseweb="select"] > div {{
        background: {PALETTE['card']} !important;
        border: 1px solid {PALETTE['border']} !important;
        border-radius: 6px !important;
      }}
      div[data-baseweb="select"] svg {{ color: {PALETTE['accent_hi']}; }}
      .stSlider [data-baseweb="slider"] div[role="slider"] {{
        background-color: {PALETTE['accent']} !important;
        border-color: {PALETTE['accent']} !important;
      }}

      /* Buttons (radio nav) */
      .stRadio > div {{ flex-direction: column; gap: 4px; }}
      .stRadio label {{
        background: transparent;
        border-radius: 7px;
        padding: 9px 10px !important;
        border-left: 3px solid transparent;
        transition: all 0.12s ease;
      }}
      .stRadio label:hover {{ background: rgba(72, 159, 88, 0.07); }}
      .stRadio [data-checked="true"] {{
        background: rgba(74, 222, 128, 0.10) !important;
        border-left: 3px solid {PALETTE['accent']} !important;
      }}

      /* Tables */
      .stDataFrame, .stTable {{
        background: {PALETTE['panel_alt']};
        border-radius: 10px;
        border: 1px solid {PALETTE['border']};
      }}

      /* Card container */
      .agro-card {{
        background: {PALETTE['panel_alt']};
        border: 1px solid {PALETTE['border']};
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 14px;
      }}
      .agro-card-title {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.06em;
        color: {PALETTE['text_dim']};
        margin-bottom: 12px;
        text-transform: uppercase;
      }}

      /* Metric */
      .agro-metric {{
        background: {PALETTE['card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 8px;
        padding: 12px 16px;
      }}
      .agro-metric-label {{
        font-size: 11px;
        color: {PALETTE['text_dimmer']};
        margin-bottom: 4px;
      }}
      .agro-metric-value {{
        font-size: 22px;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
      }}
      .agro-metric-unit {{
        font-size: 12px;
        margin-left: 4px;
        color: {PALETTE['text_dimmer']};
        font-family: 'IBM Plex Mono', monospace;
      }}

      /* Tags */
      .agro-tag {{
        background: rgba(74, 222, 128, 0.14);
        color: {PALETTE['accent_hi']};
        border: 1px solid rgba(74, 222, 128, 0.30);
        border-radius: 4px;
        padding: 1px 8px;
        font-size: 11px;
        font-family: 'IBM Plex Mono', monospace;
        margin-right: 6px;
      }}
      .agro-tag.amber {{
        background: rgba(245,158,11,0.14);
        color: {PALETTE['amber']};
        border: 1px solid rgba(245,158,11,0.30);
      }}

      /* Alert */
      .agro-alert {{
        background: {PALETTE['panel_alt']};
        border: 1px solid rgba(74,222,128,0.27);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 14px 0;
        display: flex;
        gap: 12px;
        align-items: flex-start;
        color: {PALETTE['text_dim']};
        line-height: 1.7;
        font-size: 12.5px;
      }}
      .agro-alert.bad {{ border-color: rgba(248,113,113,0.40); }}
      .agro-alert.amber {{ border-color: rgba(245,158,11,0.40); }}
      .agro-alert::before {{
        content: '';
        flex: 0 0 4px;
        background: {PALETTE['accent']};
        border-radius: 3px;
        align-self: stretch;
      }}
      .agro-alert.bad::before {{ background: {PALETTE['bad']}; }}
      .agro-alert.amber::before {{ background: {PALETTE['amber']}; }}

      /* Top bar */
      .agro-topbar {{
        background: {PALETTE['panel']};
        border-bottom: 1px solid {PALETTE['border_2']};
        padding: 10px 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -1.2rem -1.2rem 1.2rem -1.2rem;
      }}
      .agro-topbar .left {{ display:flex; align-items:center; gap:10px; }}
      .agro-topbar .pageLabel {{
        font-size: 13px; font-weight:600; color:{PALETTE['text']};
      }}
      .agro-topbar .sep {{ font-size:12px; color:{PALETTE['text_dimmer']}; }}
      .agro-topbar .right {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px; color: {PALETTE['text_dimmer']};
      }}
      .agro-status-dot {{
        width:7px; height:7px; border-radius:50%;
        background:#4ade80; box-shadow: 0 0 6px #4ade8088;
        display:inline-block; margin-left:8px;
      }}

      /* Hide Streamlit chrome (but KEEP the sidebar expand control) */
      #MainMenu, footer {{ visibility: hidden; }}
      header[data-testid="stHeader"] {{
        background: transparent !important;
        height: auto !important;
      }}
      header[data-testid="stHeader"] > * {{ visibility: hidden; }}
      header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"],
      header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"] * {{
        visibility: visible !important;
      }}

      /* Make the "expand sidebar" control prominent so it's never hidden */
      [data-testid="stSidebarCollapsedControl"] {{
        position: fixed !important;
        top: 12px;
        left: 12px;
        z-index: 9999;
        background: {PALETTE['accent']} !important;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.45);
        padding: 4px 6px;
        display: flex;
        align-items: center;
        gap: 6px;
      }}
      [data-testid="stSidebarCollapsedControl"]::after {{
        content: "Mostrar menú";
        color: #fff;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-right: 4px;
      }}
      [data-testid="stSidebarCollapsedControl"] button,
      [data-testid="stSidebarCollapsedControl"] svg {{
        color: #fff !important;
        fill: #fff !important;
      }}

      .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 1.2rem !important;
        max-width: 100% !important;
      }}

      /* Folium iframe */
      iframe.folium-map {{
        border-radius: 8px;
        border: 1px solid {PALETTE['border']};
      }}

      /* Streamlit metric override (if used) */
      [data-testid="stMetric"] {{
        background: {PALETTE['card']};
        border: 1px solid {PALETTE['border']};
        border-radius: 8px;
        padding: 12px 16px;
      }}

      /* Scrollbar */
      ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
      ::-webkit-scrollbar-track {{ background: {PALETTE['panel']}; }}
      ::-webkit-scrollbar-thumb {{ background: rgba(180,210,190,0.18); border-radius: 3px; }}

    </style>
    """, unsafe_allow_html=True)


def metric(label: str, value: str, unit: str = "", color: str | None = None) -> str:
    """Render a metric tile. Returns HTML string for st.markdown."""
    color = color or PALETTE["accent"]
    return f"""
    <div class="agro-metric">
      <div class="agro-metric-label">{label}</div>
      <div class="agro-metric-value" style="color:{color}">{value}<span class="agro-metric-unit">{unit}</span></div>
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
        <span style="font-size:11px;color:#7a8c81">Maíz</span>
        <span class="agro-tag">{year}</span>
        {region_tag}
      </div>
      <div class="right">
        Estadística Espacial + ML · Proyecto 04
        <span class="agro-status-dot"></span>
      </div>
    </div>
    """, unsafe_allow_html=True)
