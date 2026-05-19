# Reporte de cambios al modelo

Versión: 2026-05-19 · proyecto Maíz Inteligente

## Contexto

El profesor pidió simplificar la modelación: un solo modelo (el más
interpretable), validar supuestos, controlar colinealidad y reportar
resultados. Este documento resume los cambios hechos sobre la versión anterior
del proyecto, que tenía cuatro modelos (Random Forest, XGBoost, Ridge/Lasso,
KNN espacial) y un dashboard que ocultaba el problema de colinealidad detrás
de una alerta.

## 1. De cuatro modelos a uno solo

| Antes | Ahora |
|---|---|
| Random Forest, XGBoost, Ridge/Lasso, KNN espacial | **Regresión lineal** |
| Selector de modelo en el sidebar | Modelo fijo |
| Comparación RMSE entre modelos (tabla larga) | Un único conjunto de métricas |

**Por qué regresión lineal.** Es el modelo que permite leer cada variable de
forma directa: cada coeficiente tiene un signo, una magnitud y un intervalo
de confianza. Para un proyecto de estadística espacial cuya audiencia incluye
gente de negocio, la pregunta no es "¿qué modelo predice mejor?" sino "¿qué
variables explican el rendimiento del maíz y cuánto pesa cada una?".

**Implementación.** Usamos dos motores en paralelo sobre la **misma matriz**:

- `statsmodels.OLS` → tabla de coeficientes con `β`, `SE`, `t`, `p-valor`,
  `CI 95%`, `R²`, `R² ajustado`, `F`, `AIC`, `BIC`.
- `sklearn.linear_model.Ridge` → regularización para la predicción, con `α`
  elegido por `GridSearchCV` 5-fold sobre `{0.001, 0.01, 0.1, 1, 10, 100}`.

Las features se **estandarizan** antes del ajuste, de modo que los `β` son
directamente comparables y se interpretan como la importancia de cada variable
en unidades de desviación estándar.

## 2. Reducción iterativa de VIF (cambio principal)

El problema que aparecía en pantalla casi todos los años:

```
Área sembrada (log ha)    VIF = 38.7   ← colinealidad grave
Área cosechada (log ha)   VIF = 37.6   ← idem (son casi la misma variable)
Región Caribe             VIF = 12.5
Región Andina             VIF = 11.0
```

Es esperable: `area_sembrada` y `area_cosechada` son casi idénticas (la segunda
es la primera menos las hectáreas perdidas), y los dummies de región son
combinación lineal de `lat/lon`. Con eso adentro, los coeficientes individuales
no son interpretables.

**Solución.** Antes de entrenar, se aplica reducción iterativa de VIF:

```
mientras alguna variable tenga VIF > 10:
    eliminar la variable con VIF más alto
    recalcular VIF sobre el resto
```

Esto se hace en `_iterative_vif_reduction()` en `app/models.py`. El umbral
de 10 es el estándar (Hair, Anderson, Tatham, Black) — algunos autores usan
5 si quieren ser estrictos.

**Resultado para todos los años 2007–2024** (df: 17,211 filas):

| Año  | n     | k final | Variables eliminadas               |
|------|-------|---------|------------------------------------|
| 2007 | 938   | 8       | Área sembrada (log), Región Caribe |
| 2010 | 959   | 8       | Área sembrada (log), Región Caribe |
| 2015 | 950   | 8       | Área sembrada (log), Región Caribe |
| 2020 | 940   | 8       | Área sembrada (log), Región Caribe |
| 2024 | 963   | 6       | Área sembrada (log), Región Caribe |

El patrón es consistente: cada año se eliminan dos variables, *siempre las
mismas*. Esto confirma que la colinealidad es estructural del dataset y no un
artefacto del año seleccionado.

**Por qué se queda `Área cosechada` y no `Área sembrada`**: el algoritmo
selecciona la variable con mayor VIF en cada paso. Empíricamente, en este
dataset la sembrada termina con el VIF marginalmente más alto y se elimina
primero. Conceptualmente da igual — son casi idénticas y la cosechada está
incluso más cerca del fenómeno físico (área que efectivamente entregó
toneladas).

## 3. Cambios en el Streamlit

Se eliminó el panel "Recomendación: la regularización Ridge ya está
mitigando el problema en la predicción, pero para inferencia conviene
eliminar la variable más colineal o construir un índice". Era un *workaround*
que decía "el problema existe pero lo dejamos pasar". Ahora el problema se
resuelve antes de mostrar nada.

La página **Modelo Lineal** muestra:

1. **VIF del modelo final** — todas las barras por debajo del umbral. No se
   muestran las variables eliminadas en el gráfico.
2. **Panel "Variables eliminadas por colinealidad"** — al lado del VIF,
   listando cada variable que fue removida con su VIF inicial y explicando
   el proceso iterativo.
3. **Coeficientes (β estandarizados)**, tabla OLS y gráfico de barras — sólo
   variables del modelo final.
4. **Tests de supuestos** sobre el modelo final.
5. **Mapas** (predicción y residuos) generados con el modelo final.

## 4. Otros cambios menores incluidos

- **Kriging de rendimiento** (no sólo de residuos) para rellenar municipios
  sin observación en el mapa nacional.
- Mapas folium ahora sobre base `cartodbpositron` (clara) con paleta brillante
  yellow → orange → green para mejor contraste.
- Reorganización a cinco páginas business-first: Landing · Panorama · Clima &
  Territorio · Modelo Lineal · Detalle Técnico.
- Página **Clima**: scatter precipitación/temperatura/ENSO vs rendimiento con
  línea de tendencia OLS, muestreo estratificado a 2,500 puntos para
  performance.
- Pies de participación regional, treemap de departamentos, Q-Q plot,
  residuos-vs-ajustados y `α`-curve agregados a `charts.py`.

## 5. Cómo verificar

```bash
streamlit run app/app.py
# ir a "◆ Modelo Lineal"
# en el panel "MULTICOLINEALIDAD · VIF DEL MODELO FINAL" todas las barras
# están en verde, ninguna pasa la línea de VIF = 10.
```

Y desde la línea de comandos, para confirmar cuántas variables se eliminan
año por año:

```bash
python -c "import sys; sys.path.insert(0,'app'); \
  from data_loader import build_master; from models import fit_linear; \
  df=build_master(); \
  print([(y, [n for n,_,_ in fit_linear(df,y).dropped_features]) \
         for y in sorted(df['anio'].unique())])"
```
