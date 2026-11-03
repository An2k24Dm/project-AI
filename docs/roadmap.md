# Hoja de ruta

[Volver al README](../README.MD) · [Arquitectura](architecture.md) · [Dataset](dataset.md) · [Desarrollo](development.md)

## Criterios de estado

| Estado | Significado |
|---|---|
| Completada | Existen entregables implementados y evidencia verificable. |
| Pendiente | Falta el entregable o su verificación final. |

## Resumen

| Fase | Estado | Evidencia principal |
|---|---|---|
| 1. Documentación técnica | Completada | `README.MD` y documentos de `docs/`. |
| 2. Análisis exploratorio | Completada | Notebook 01 ejecutado, 7 celdas de código y 4 figuras. |
| 3. Limpieza y preprocesamiento | Completada | Notebook 02, particiones y preprocesador exportados. |
| 4. Entrenamiento del MLP | Completada | Notebook 03 y modelo Keras exportado. |
| 5. Evaluación y corrección | Completada | Métricas finales y corrección analítica guardadas. |
| 6. Simulación financiera y GNE | Completada | Notebook 04, CSV 10.000×26 y motor financiero. |
| 7. Aplicación Streamlit | Completada | Buscador, panel y simulador integrados. |
| 8. Pruebas de integración | Completada | Suite Pytest y verificación de arranque/interfaz. |
| 9. Informe ejecutivo final | Pendiente | Documento final no creado. |
| 10. Presentación académica | Pendiente | Material de presentación no preparado en esta fase. |

## 1. Documentación técnica

**Objetivo:** mantener una referencia coherente y verificable de datos, ML, finanzas, arquitectura, aplicación y desarrollo.

**Estado:** completada. La documentación utiliza `Customer-Churn-Records.csv`, las métricas actuales del MLP, el escenario financiero vigente y la estructura real de Streamlit.

**Mantenimiento pendiente:** actualizar cifras y contratos si se regeneran datos o artefactos; confirmar procedencia y licencia antes de la entrega externa.

## 2. Análisis exploratorio

**Objetivo:** diagnosticar calidad, desbalance, distribuciones, valores atípicos, correlaciones y posibles fugas de información.

**Entregables:** [`01_eda.ipynb`](../notebooks/01_eda.ipynb) y [resultados del EDA](eda-results.md).

**Evidencia:** 10.000×18, cero faltantes y duplicados, 92 apellidos con `?`, distribución 7.962/2.038 y coincidencia `Complain = Exited` del 99,86 %. El notebook no modifica datos.

## 3. Limpieza y preprocesamiento

**Objetivo:** preparar entradas reproducibles sin fuga de información.

**Entregables:** [`02_preprocesamiento.ipynb`](../notebooks/02_preprocesamiento.ipynb), `clientes_limpios.csv`, `train.npz`, `validation.npz`, `test.npz`, `metadata.json` y `preprocesador.joblib`.

**Evidencia:** 10.000 clientes conservados; 92 apellidos desconocidos representados mediante `pd.NA`; particiones estratificadas 7.000/1.500/1.500; transformadores ajustados solo con entrenamiento; nueve entradas originales convertidas en 11 valores.

## 4. Entrenamiento del MLP

**Objetivo:** estimar probabilidades de abandono mediante una arquitectura reproducible.

**Entregables:** [`03_red_neuronal.ipynb`](../notebooks/03_red_neuronal.ipynb) y `models/modelo_churn.keras`.

**Evidencia:** arquitectura 128–64–1 con Batch Normalization y Dropout, Adam, Binary Crossentropy, pesos de clase y Early Stopping. La ejecución guardada completó 22 épocas y restauró la mejor, la 10.

## 5. Evaluación y corrección probabilística

**Objetivo:** medir discriminación y calidad probabilística sin usar prueba para seleccionar el método.

**Entregable:** `models/correccion_probabilidades.json` y evaluación final guardada.

**Evidencia:** la corrección analítica mejoró Brier Score y Log Loss en validación. En prueba: ROC-AUC `0,886851`, PR-AUC `0,732324`, Brier `0,095979`, Log Loss `0,315112` y F1@0.5 `0,606426`.

**Limitación:** no es una calibración aprendida ni perfecta. El umbral `0,5` es diagnóstico y no interviene en la GNE.

## 6. Simulación financiera y motor GNE

**Objetivo:** construir un escenario de rentabilidad cuando no existen datos bancarios contables y seleccionar intervenciones con GNE positiva.

**Entregables:** [`04_analisis_financiero.ipynb`](../notebooks/04_analisis_financiero.ipynb), `clientes_financieros_simulados.csv`, `data/incentivos.csv` y `src/financial.py`.

**Evidencia:** 10.000×26, ocho columnas simuladas deterministas, 7.880 rentables, 2.120 deficitarios, 793 retenciones, USD 35.600,00 de inversión, USD 42.180,78 de Ganancia Neta Esperada y ROI proyectado de 118,49 %.

**Limitación:** los importes, costos y efectividades son supuestos académicos, no resultados observados.

## 7. Aplicación Streamlit

**Objetivo:** presentar inferencia y decisiones mediante tres vistas.

**Entregables:** `app.py`, `ui/`, servicios y configuración de Streamlit.

**Evidencia:**

- buscador individual con perfil, MLP, finanzas y alternativas;
- panel con KPI, filtros, visualizaciones de riesgo, decisiones y economía, y tabla ejecutiva;
- simulador temporal de costos y efectividades, comparación y restablecimiento;
- caché por versión y reutilización de probabilidades;
- ausencia de escritura sobre CSV o catálogo.

## 8. Pruebas de integración

**Objetivo:** verificar contratos de datos, predicción, finanzas y UI.

**Entregables:** archivos existentes en `tests/` y comando reproducible `uv run pytest -q`. La verificación actual completó 56 pruebas aprobadas.

**Criterios:** probabilidades válidas y alineadas, ningún incentivo para margen no positivo, GNE positiva en toda retención, filtros sin recálculo de decisiones, simulación sin mutación y navegación funcional.

## 9. Informe ejecutivo final

**Estado:** pendiente.

Debe sintetizar problema, arquitectura, calidad del modelo, escenario financiero, matriz de decisiones, limitaciones y uso de la aplicación. Toda cifra debe distinguir datos observados, probabilidades estimadas y resultados simulados. Este documento no se crea como parte de la actualización técnica actual.

## 10. Presentación académica

**Estado:** pendiente.

Debe preparar la demostración del buscador, el dashboard y el simulador, y explicar las limitaciones del modelo y de la simulación sin presentar GNE o ROI como beneficios realizados.

## Próximo paso

El siguiente hito es elaborar el informe ejecutivo y preparar la presentación. No se requiere continuar desarrollando el MLP o el motor financiero para completar esta fase documental.
