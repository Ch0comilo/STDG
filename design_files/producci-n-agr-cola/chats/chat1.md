# Aplicación Streamlit

_Started 2026-05-04 02:14 UTC_

---

## User

Este es mi proyecto, asi que quiero hacer un streamlit, entonces haz tu propuesta

## Assistant

_[tool: read_file]_

_[tool: view_image]_

Entendido. Veo el proyecto: **Producción agrícola, clima y predicción regional** — Geoestadística + ML regresivo aplicado a Colombia. El sketch muestra dos pantallas con mapas de Colombia.

Antes de construir el prototipo Streamlit, tengo algunas preguntas clave:

_[tool: questions_v2]_

## User

Questions answered:
- cultivo: Maíz
- paginas: EDA espacial (mapas coropléticos), Análisis de autocorrelación (Moran / LISA), Modelos ML (Random Forest / XGBoost), Kriging de residuos, Comparación de modelos
- datos_reales: Nadie tiene que subir nada, yo tengo los datos en el backend, es solo mostrarlos y hacer comparaciones
- mapa_tipo: Mapa coroplético de rendimiento (ton/ha), Mapa de predicción del modelo, Mapa de residuos espaciales, Mapa LISA (clusters espaciales)
- ml_models: Random Forest, XGBoost, Lasso / Ridge, GWR (regresión geográficamente ponderada), Kriging de residuos
- interactividad: Alta — filtros, sliders, selección de variables, el usuario puede cambiar parámetros del modelo
- sidebar: Sidebar clásico de Streamlit (navegación vertical izquierda)
- tema_visual: Verde agrícola (tonos verdes y tierra)
- graficos: Variograma empírico de residuos, Importancia de variables (SHAP / feature importance), Gráficos de dependencia parcial (PDP), Tabla comparativa de modelos (RMSE / MAE), Scatter observado vs predicho
- formato_final: Entrega de proyecto (compartir enlace)
- variaciones: No — una propuesta sólida está bien

## Assistant

Perfecto. Tengo todo lo que necesito. Voy a construir un prototipo Streamlit de alta fidelidad con:

- **Sidebar** con navegación entre 5 secciones
- **Datos simulados realistas** de maíz por municipio en Colombia
- **4 tipos de mapas** interactivos + gráficos estadísticos completos
- **Paleta verde agrícola / tierra**
- **Alta interactividad**: filtros de año, región, sliders de hiperparámetros

_[tool: update_todos]_

Voy a construir esto ahora. El sistema visual: **verde bosque** (`oklch(35% 0.12 145)`) + **tierra ámbar** (`oklch(65% 0.14 75)`) + fondo crema oscuro tipo dashboard. Tipografía **IBM Plex Sans** + **IBM Plex Mono** para métricas.

_[tool: write_file]_

_[tool: done]_

Carga limpio. Aquí está tu prototipo 🌽

_[tool: fork_verifier_agent]_

_[tool: update_todos]_

El prototipo está listo. Aquí un resumen de lo que incluye:

**5 secciones navegables (sidebar izquierdo):**
- **EDA Espacial** — mapa coroplético de rendimiento, histograma de distribución, scatters vs. precipitación/temperatura/altitud, promedios por región
- **Autocorrelación** — Moran I global, diagrama de Moran, mapa LISA con clusters HH/LL/HL/LH
- **Modelos ML** — SHAP importance, scatter observado vs predicho, PDP por variable; alertas si hay autocorrelación residual
- **Kriging de Residuos** — variograma empírico + teórico (nugget/sill/range), mapa de residuos divergente, tabla de reducción de RMSE
- **Comparación** — tabla completa con CV aleatoria vs espacial, gráfico de barras dobles, Moran I en residuos, conclusión de 3 paneles

**Filtros interactivos en sidebar:** año (2018–2023), región, modelo, sliders de hiperparámetros (n° árboles, max depth, alpha)

**Siguientes pasos posibles:**
- Conectar datos reales (EVA/AGRONET) sustituyendo `ALL_DATA`
- Agregar selector de cultivo (café, arroz, papa)
- Exportar tabla comparativa como CSV

## User

esta super, pero me gustarian mas graficos geoespaciales, como con el mapa de colombia, que sea interactivo, ademas unos graficos historicos no vendrian mal

## Assistant

Perfecto. Voy a enriquecer el prototipo con:

1. **Mapas coroplético interactivos** — hover con tooltip rico, click para seleccionar municipio, zoom por región
2. **Mapa de calor de tendencia temporal** por municipio (tipo heatmap)
3. **Gráficos históricos** — serie de tiempo por región, ranking anual, tendencia nacional
4. **Panel de detalle** al hacer click en un municipio del mapa

_[tool: update_todos]_

Voy a reescribir el archivo con todos los elementos nuevos. Dado el tamaño, lo voy a dividir en componentes separados.

_[tool: write_file]_

Ahora el archivo de componentes de mapas y gráficos:

_[tool: write_file]_

Ahora el archivo principal con las páginas y la app:

_[tool: write_file]_

Ahora el HTML principal que ensambla todo:

_[tool: write_file]_

_[tool: done]_

Limpio. Aquí está la versión 2 mejorada 🌽

_[tool: fork_verifier_agent]_

_[tool: update_todos]_

Lo nuevo en esta versión:

**Mapas geoespaciales mejorados:**
- 🗺️ **Hover interactivo** — tooltip flotante con rendimiento, precipitación, altitud, región al pasar el cursor
- 🔘 **Click para seleccionar** un municipio — se resalta en todos los mapas simultáneamente
- 🎨 **Mapa LISA** con colores por cluster (HH/LL/HL/LH/NS)
- 🔴🟢 **Mapa de residuos** con escala divergente (subestimado ↔ sobreestimado)
- 🗺️ **Mapa de predicción** del modelo seleccionado

**Gráficos históricos nuevos:**
- 📈 **Serie temporal** nacional + 5 regiones + municipio seleccionado (2018–2023)
- 🔥 **Heatmap** Top 22 municipios × año — clic en fila para seleccionar
- 📊 **Ranking** Top 8 municipios por año
- 📊 **Barras Moran I** por año (tendencia histórica)
- 📊 **Comparativa RMSE** histórico: RF puro vs RF+Kriging

**Panel de detalle del municipio** (sidebar + inline):
- Mini sparkline de rendimiento 2018–2023
- Tendencia % vs 2018, temperatura, altitud, NBI

