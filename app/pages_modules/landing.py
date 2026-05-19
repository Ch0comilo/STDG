"""Landing page — presentación comercial de Maíz Inteligente."""
from __future__ import annotations

import streamlit as st
from theme import PALETTE


# ── helpers ──────────────────────────────────────────────────────────────────

def _nav(page_id: str) -> None:
    st.session_state["nav_page"] = page_id
    st.rerun()


def _section_title(text: str, subtitle: str = "") -> str:
    sub_html = (
        f"<p style='font-size:13px;color:{PALETTE['text_dim']};margin-top:6px;"
        f"margin-bottom:0;font-weight:400;'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
    <div style='margin-bottom:28px;'>
      <h2 style='font-size:20px;font-weight:700;color:{PALETTE['text']};
                 margin:0;letter-spacing:-0.01em;'>{text}</h2>
      {sub_html}
    </div>
    """


def _card(icon: str, title: str, body: str, accent: str | None = None) -> str:
    border_color = accent or PALETTE["border"]
    return f"""
    <div style='background:{PALETTE['panel_alt']};border:1px solid {border_color};
                border-radius:10px;padding:18px 20px;height:100%;'>
      <div style='font-size:22px;margin-bottom:8px;'>{icon}</div>
      <div style='font-size:13px;font-weight:600;color:{PALETTE['text']};
                  margin-bottom:6px;'>{title}</div>
      <div style='font-size:12px;color:{PALETTE['text_dim']};line-height:1.65;'>{body}</div>
    </div>
    """


def _pill(text: str, color: str) -> str:
    return (
        f"<span style='background:rgba(0,0,0,0.25);border:1px solid {color};"
        f"color:{color};border-radius:20px;padding:3px 12px;font-size:11px;"
        f"font-family:IBM Plex Mono,monospace;margin-right:8px;'>{text}</span>"
    )


# ── render ────────────────────────────────────────────────────────────────────

def render(df=None, year: int = 2024, region: str = "Todas") -> None:

    # ── 1. HERO ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{PALETTE['panel']} 0%,#0f2e14 100%);
                border:1px solid {PALETTE['border_2']};border-radius:14px;
                padding:48px 40px 40px 40px;margin-bottom:28px;position:relative;
                overflow:hidden;'>
      <!-- fondo decorativo -->
      <div style='position:absolute;top:-40px;right:-40px;width:220px;height:220px;
                  border-radius:50%;background:rgba(63,155,72,0.08);'></div>
      <div style='position:absolute;bottom:-60px;right:80px;width:140px;height:140px;
                  border-radius:50%;background:rgba(217,158,48,0.06);'></div>

      <!-- chips -->
      <div style='margin-bottom:18px;'>
        {_pill("Colombia · 2006–2024", PALETTE['accent'])}
        {_pill("AGRONET · IDEAM · DANE", PALETTE['amber'])}
        {_pill("Herramienta de código abierto", PALETTE['text_dim'])}
      </div>

      <!-- título -->
      <h1 style='font-size:38px;font-weight:700;color:{PALETTE['accent_hi']};
                 letter-spacing:-0.02em;margin:0 0 6px 0;line-height:1.1;'>
        🌽 Maíz Inteligente
      </h1>
      <p style='font-size:16px;color:{PALETTE['text']};font-weight:500;
                margin:0 0 14px 0;line-height:1.4;'>
        Datos, mapas y predicción para entender el rendimiento del maíz en Colombia
      </p>
      <p style='font-size:13px;color:{PALETTE['text_dim']};max-width:620px;
                line-height:1.65;margin:0;'>
        Convertimos datos agrícolas y geográficos en una herramienta visual para
        identificar zonas de alto rendimiento, detectar brechas productivas y
        apoyar decisiones agrícolas con evidencia.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    with c1:
        if st.button("📊 Ver panorama nacional", use_container_width=True,
                     key="cta_top_panorama"):
            _nav("panorama")
    with c2:
        if st.button("🤖 Modelo lineal", use_container_width=True,
                     key="cta_top_modelo"):
            _nav("modelo")
    with c3:
        if st.button("⬡ Detalle técnico", use_container_width=True,
                     key="cta_top_tecnico"):
            _nav("tecnico")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 2. EL PROBLEMA ────────────────────────────────────────────────────────
    st.markdown(_section_title(
        "El problema",
        "Los datos existen, pero no siempre están disponibles en una forma útil"
    ), unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4)
    cards_problema = [
        ("📋", "Datos dispersos",
         "La información agrícola vive en tablas grandes, difíciles de leer y comparar entre municipios."),
        ("📉", "Producción ≠ eficiencia",
         "Un municipio puede producir mucho maíz solo porque tiene más hectáreas, no porque rinda mejor."),
        ("🗺️", "El territorio importa",
         "Las diferencias entre regiones no se ven en una tabla. El mapa revela patrones que los números ocultan."),
        ("🤔", "Decisiones sin contexto",
         "Agricultores y entidades toman decisiones sin acceso a comparativos históricos ni proyecciones."),
    ]
    for col, (icon, title, body) in zip([p1, p2, p3, p4], cards_problema):
        col.markdown(_card(icon, title, body, accent=f"rgba(248,113,113,0.25)"),
                     unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 3. LA SOLUCIÓN ────────────────────────────────────────────────────────
    st.markdown(_section_title(
        "La solución",
        "Una sola herramienta que une datos agrícolas, geografía y estadística"
    ), unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    cards_sol = [
        ("🗺️", "Mapas de rendimiento",
         "Visualiza el rendimiento ton/ha en cada municipio de Colombia. Identifica clústeres de alto y bajo rendimiento de un vistazo."),
        ("📈", "Análisis histórico",
         "Compara cómo ha evolucionado el rendimiento entre 2006 y 2024 por región y municipio."),
        ("🤖", "Modelo lineal interpretable",
         "Regresión lineal (OLS + Ridge) que predice rendimiento con coeficientes claros — cada variable con su signo, magnitud e intervalo de confianza."),
    ]
    for col, (icon, title, body) in zip([s1, s2, s3], cards_sol):
        col.markdown(_card(icon, title, body, accent=f"rgba(63,155,72,0.30)"),
                     unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    s4, s5, s6 = st.columns(3)
    cards_sol2 = [
        ("⬡", "Autocorrelación espacial",
         "Detecta si los municipios con bajo rendimiento están agrupados territorialmente, señal de un problema estructural de zona."),
        ("🎯", "Kriging para rellenar huecos",
         "Ordinary kriging interpola el rendimiento donde no hay registros — el mapa nacional ya no queda con municipios en negro."),
        ("📋", "Diagnóstico de supuestos",
         "VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, Moran sobre residuos. Si el modelo no cumple, lo decimos."),
    ]
    for col, (icon, title, body) in zip([s4, s5, s6], cards_sol2):
        col.markdown(_card(icon, title, body, accent=f"rgba(63,155,72,0.30)"),
                     unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 4. DATOS UTILIZADOS ───────────────────────────────────────────────────
    st.markdown(_section_title(
        "Datos utilizados",
        "Tres fuentes integradas para una visión completa del territorio"
    ), unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3)
    datos = [
        ("🌾", "AGRONET / EVA", PALETTE["accent"],
         "Registros municipales de producción (ton), área sembrada (ha), área cosechada (ha) y rendimiento (ton/ha). "
         "Cubre todos los departamentos de Colombia desde 2006."),
        ("🗾", "Shapefile municipal · DANE", PALETTE["amber"],
         "Geometrías de los 1 120 municipios de Colombia. Permite ubicar cada registro agrícola "
         "en el mapa y calcular centroides geográficos para el análisis espacial."),
        ("🌡️", "IDEAM · TerriData", PALETTE["info"],
         "Variables climáticas (precipitación anual, temperatura media, índice ENSO Niño 3.4) "
         "e indicadores territoriales complementarios (cobertura energía, recaudo predial)."),
    ]
    for col, (icon, title, color, body) in zip([d1, d2, d3], datos):
        col.markdown(f"""
        <div style='background:{PALETTE['panel_alt']};border:1px solid {color}33;
                    border-top:3px solid {color};border-radius:10px;padding:18px 20px;'>
          <div style='font-size:22px;margin-bottom:8px;'>{icon}</div>
          <div style='font-size:13px;font-weight:700;color:{color};margin-bottom:8px;'>{title}</div>
          <div style='font-size:12px;color:{PALETTE['text_dim']};line-height:1.65;'>{body}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 5. QUÉ ES RENDIMIENTO ─────────────────────────────────────────────────
    st.markdown(_section_title(
        "¿Qué es el rendimiento agrícola?",
        "La variable central del proyecto — y por qué es mejor que la producción total"
    ), unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown(f"""
        <div style='background:{PALETTE['panel_alt']};border:1px solid {PALETTE['border']};
                    border-radius:10px;padding:24px 28px;'>
          <p style='font-size:12px;color:{PALETTE['text_dim']};margin:0 0 16px 0;'>
            La producción total puede engañar: un municipio produce mucho maíz simplemente
            porque tiene muchas hectáreas sembradas, no porque sea más eficiente.
            El rendimiento corrige eso.
          </p>

          <!-- fórmula -->
          <div style='background:{PALETTE['card']};border:1px solid {PALETTE['border']};
                      border-radius:8px;padding:16px 20px;text-align:center;margin-bottom:16px;'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:20px;
                        color:{PALETTE['accent_hi']};font-weight:600;'>
              rendimiento = producción ÷ área cosechada
            </div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:13px;
                        color:{PALETTE['text_dim']};margin-top:8px;'>
              toneladas de maíz &nbsp;/&nbsp; hectáreas cosechadas
            </div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:18px;
                        color:{PALETTE['amber']};margin-top:8px;font-weight:600;'>
              → ton / ha
            </div>
          </div>

          <p style='font-size:12px;color:{PALETTE['text_dim']};margin:0;line-height:1.65;'>
            <strong style='color:{PALETTE['text']};'>Ejemplo:</strong>
            si un municipio tiene <strong style='color:{PALETTE['accent_hi']};'>2 ton/ha</strong>,
            significa que produce 2 toneladas de maíz por cada hectárea cosechada.
            Ese indicador permite comparar municipios grandes y pequeños en igualdad de condiciones.
          </p>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div style='background:{PALETTE['panel_alt']};border:1px solid {PALETTE['border']};
                    border-radius:10px;padding:24px 28px;height:100%;'>
          <div style='font-size:12px;font-weight:600;color:{PALETTE['text_dim']};
                      text-transform:uppercase;letter-spacing:0.07em;margin-bottom:16px;'>
            ¿Por qué no usar producción total?
          </div>

          <div style='display:flex;flex-direction:column;gap:12px;'>
            <div style='background:{PALETTE['card']};border-radius:8px;padding:12px 14px;
                        border-left:3px solid {PALETTE['bad']};'>
              <div style='font-size:12px;font-weight:600;color:{PALETTE['bad']};
                          margin-bottom:4px;'>❌ Producción total</div>
              <div style='font-size:11px;color:{PALETTE['text_dim']};line-height:1.5;'>
                Municipio A: 10 000 ton &nbsp;|&nbsp; Municipio B: 2 000 ton<br>
                <em>¿Municipio A es más eficiente? No necesariamente.</em>
              </div>
            </div>
            <div style='background:{PALETTE['card']};border-radius:8px;padding:12px 14px;
                        border-left:3px solid {PALETTE['ok']};'>
              <div style='font-size:12px;font-weight:600;color:{PALETTE['ok']};
                          margin-bottom:4px;'>✓ Rendimiento ton/ha</div>
              <div style='font-size:11px;color:{PALETTE['text_dim']};line-height:1.5;'>
                Municipio A: 1.8 ton/ha &nbsp;|&nbsp; Municipio B: 4.2 ton/ha<br>
                <em>Municipio B produce más por hectárea: es más eficiente.</em>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 6. QUÉ PUEDE VER EL USUARIO ──────────────────────────────────────────
    st.markdown(_section_title(
        "¿Qué puede explorar en la app?",
        "Seis módulos de análisis integrados"
    ), unsafe_allow_html=True)

    modulos = [
        ("panorama",   "📍", "Panorama",
         "Mapa nacional completado con kriging, KPIs de producción, pies de participación regional y ranking municipal."),
        ("clima",      "🌡️", "Clima",
         "Precipitación, temperatura y ENSO vs rendimiento. Correlaciones, mapas climáticos y series anuales."),
        ("territorio", "⬢",  "Territorio",
         "TerriData: energía rural, banda ancha, uso del suelo. Cuadrante AgTech, radar regional, mapas y oportunidades."),
        ("modelo",     "🤖", "Modelo Lineal",
         "Regresión lineal interpretable con diagnóstico completo: coeficientes, VIF, supuestos, mapas de predicción y residuos."),
        ("tecnico",    "⬡",  "Detalle Técnico",
         "Moran I, clusters LISA, variograma y kriging del rendimiento y de los residuos. Para profundizar en lo espacial."),
    ]

    row1 = st.columns(5)
    for i, (page_id, icon, title, body) in enumerate(modulos):
        col = row1[i]
        with col:
            st.markdown(f"""
            <div style='background:{PALETTE['panel_alt']};border:1px solid {PALETTE['border']};
                        border-radius:10px;padding:18px 20px;margin-bottom:4px;'>
              <div style='font-size:20px;margin-bottom:6px;'>{icon}</div>
              <div style='font-size:13px;font-weight:600;color:{PALETTE['accent_hi']};
                          margin-bottom:6px;'>{title}</div>
              <div style='font-size:12px;color:{PALETTE['text_dim']};line-height:1.6;'>{body}</div>
            </div>
            """, unsafe_allow_html=True)
            if page_id:
                if st.button(f"Ir a {title}", key=f"btn_mod_{page_id}",
                             use_container_width=True):
                    _nav(page_id)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 7. VALOR PARA AGRICULTORES ────────────────────────────────────────────
    st.markdown(_section_title(
        "¿Para quién es útil?",
        "La app no reemplaza el conocimiento del campo — lo fortalece con evidencia"
    ), unsafe_allow_html=True)

    v1, v2 = st.columns(2)

    perfiles = [
        ("👨‍🌾", "Agricultor / productor",
         ["Compara tu municipio con los de mejor rendimiento del país",
          "Detecta si tu zona tiene un problema estructural de baja productividad",
          "Evalúa el impacto de años Niño/Niña en tu región",
          "Identifica si vale la pena cambiar variedad o práctica agronómica"]),
        ("🏛️", "Entidad territorial / gremio",
         ["Prioriza municipios que necesitan asistencia técnica urgente",
          "Justifica inversiones con evidencia espacial y modelos validados",
          "Monitorea el cambio histórico en la productividad regional",
          "Detecta clústeres de bajo rendimiento persistente en el territorio"]),
    ]

    for col, (icon, perfil, items) in zip([v1, v2], perfiles):
        items_html = "".join(
            f"<li style='margin-bottom:6px;color:{PALETTE['text_dim']};'>{it}</li>"
            for it in items
        )
        col.markdown(f"""
        <div style='background:{PALETTE['panel_alt']};border:1px solid {PALETTE['border']};
                    border-radius:10px;padding:22px 24px;'>
          <div style='font-size:24px;margin-bottom:8px;'>{icon}</div>
          <div style='font-size:14px;font-weight:700;color:{PALETTE['text']};
                      margin-bottom:14px;'>{perfil}</div>
          <ul style='margin:0;padding-left:18px;font-size:12px;line-height:1.7;'>
            {items_html}
          </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── 8. NOTA TÉCNICA ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:{PALETTE['panel_alt']};border:1px solid {PALETTE['border_2']};
                border-left:4px solid {PALETTE['info']};border-radius:10px;
                padding:20px 24px;margin-bottom:28px;'>
      <div style='font-size:11px;font-weight:600;color:{PALETTE['info']};
                  text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>
        Metodología
      </div>
      <p style='font-size:13px;color:{PALETTE['text']};margin:0;line-height:1.7;'>
        <strong>Maíz Inteligente</strong> usa <strong>un solo modelo</strong> — regresión
        lineal (OLS + Ridge regularizado) — porque es el más interpretable: cada
        coeficiente tiene signo, magnitud e intervalo de confianza. Se valida con
        CV aleatoria y CV espacial por departamento, y se verifican los supuestos
        del modelo (VIF, normalidad, homocedasticidad, independencia, autocorrelación
        residual). Para rellenar municipios sin observación usamos <strong>kriging
        ordinario</strong> del rendimiento; para corregir patrones espaciales no
        capturados por el modelo, kriging sobre los residuos.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 9. CIERRE COMERCIAL ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0d2710 0%,{PALETTE['panel']} 100%);
                border:1px solid {PALETTE['accent']}44;border-radius:14px;
                padding:40px;text-align:center;position:relative;overflow:hidden;'>
      <div style='position:absolute;top:-30px;left:-30px;width:160px;height:160px;
                  border-radius:50%;background:rgba(63,155,72,0.07);'></div>
      <div style='position:absolute;bottom:-40px;right:-20px;width:200px;height:200px;
                  border-radius:50%;background:rgba(217,158,48,0.05);'></div>
      <div style='font-size:28px;margin-bottom:12px;'>🌽</div>
      <h2 style='font-size:22px;font-weight:700;color:{PALETTE['accent_hi']};
                 margin:0 0 10px 0;letter-spacing:-0.01em;'>
        Maíz Inteligente transforma datos agrícolas en decisiones territoriales.
      </h2>
      <p style='font-size:14px;color:{PALETTE['text_dim']};max-width:560px;
                margin:0 auto 28px auto;line-height:1.65;'>
        No reemplaza el conocimiento del campo: lo fortalece con evidencia,
        mapas y predicción.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    ca, cb, cc, _ = st.columns([1, 1, 1, 1.5])
    with ca:
        if st.button("📊 Analizar mi municipio", use_container_width=True,
                     key="cta_bot_panorama"):
            _nav("panorama")
    with cb:
        if st.button("🤖 Explorar el modelo", use_container_width=True,
                     key="cta_bot_modelo"):
            _nav("modelo")
    with cc:
        if st.button("🌡️ Clima & territorio", use_container_width=True,
                     key="cta_bot_clima"):
            _nav("clima")
