# Guía de desarrollo

[Volver al README](../README.MD) · [Arquitectura](architecture.md) · [Aprendizaje automático](machine-learning.md) · [Aplicación](application.md) · [Hoja de ruta](roadmap.md)

## Entorno

El proyecto requiere Python `3.11.*`. `pyproject.toml` declara Jupyter, Pandas, NumPy, Matplotlib, Plotly, Scikit-learn, Joblib, TensorFlow `2.21.0`, Streamlit y Pytest. `uv.lock` fija la resolución reproducible y `requirements.txt` es una exportación para herramientas que lo requieran.

Desde la raíz:

```bash
uv sync --locked
uv run pytest -q
uv run streamlit run app.py
```

Para regenerar `requirements.txt` desde el lock:

```bash
uv export --format requirements-txt --no-hashes --locked --output-file requirements.txt
```

`requirements.txt` no debe editarse manualmente.

## Principios

1. Mantener una solución monolítica y reproducible.
2. Separar presentación, coordinación, datos, predicción, finanzas y analítica.
3. Reutilizar una sola implementación de cada transformación y fórmula.
4. Validar esquema y dominios en los límites del sistema.
5. Preservar identificadores y orden de filas.
6. Distinguir datos observados, predicciones, simulaciones y proyecciones.
7. Mantener cálculos con precisión completa y redondear solo al presentar.
8. No persistir cambios del simulador.

## Organización del código

| Archivo | Responsabilidad | Evitar |
|---|---|---|
| `app.py` | Inicialización, navegación y límite de errores. | Reglas financieras o gráficos. |
| `src/constants.py` | Rutas y características compartidas. | Cargas pesadas o estado mutable. |
| `src/data_processing.py` | Lectura, validación, consulta y catálogos temporales. | Widgets o inferencia. |
| `src/prediction.py` | Carga de artefactos y predicción. | Entrenamiento o reglas de incentivos. |
| `src/financial.py` | Catálogo, percentiles, elegibilidad, GNE y decisiones. | Streamlit o acceso directo al MLP. |
| `src/analytics.py` | Enriquecimiento, KPI, filtros y comparación. | Escritura en datos fuente. |
| `ui/services.py` | Firma de recursos, caché y coordinación. | Duplicar fórmulas. |
| `ui/pages/*.py` | Presentación de las tres vistas. | Entrenamiento o transformaciones. |
| `ui/components.py` | Formatos, KPI y avisos compartidos. | Acceso a archivos. |
| `ui/styles.py` | Colores y estilos visuales. | Lógica de negocio. |

## Flujo reproducible de notebooks

1. `01_eda.ipynb` diagnostica `Customer-Churn-Records.csv` sin modificarlo.
2. `02_preprocesamiento.ipynb` limpia una copia, divide 70/15/15, ajusta el `ColumnTransformer` solo con entrenamiento y exporta datos y preprocesador.
3. `03_red_neuronal.ipynb` carga los artefactos del notebook 02, entrena una arquitectura, decide la corrección con validación y evalúa prueba una sola vez.
4. `04_analisis_financiero.ipynb` carga el CSV original, genera ocho variables deterministas, aplica el predictor y el motor financiero, y exporta `clientes_financieros_simulados.csv`.

Ejecutar un notebook con exportación puede sobrescribir artefactos versionados. Antes de regenerarlos se debe confirmar que esa acción es intencional, conservar la trazabilidad y volver a ejecutar las verificaciones dependientes.

## Datos y artefactos

| Recurso | Productor | Consumidor principal |
|---|---|---|
| `Customer-Churn-Records.csv` | Fuente | Notebooks 01, 02 y 04. |
| `clientes_limpios.csv` | Notebook 02 | Trazabilidad del preprocesamiento. |
| `train.npz`, `validation.npz`, `test.npz` | Notebook 02 | Notebook 03. |
| `metadata.json` | Notebook 02 | Notebook 03 y verificación. |
| `preprocesador.joblib` | Notebook 02 | Notebook 03 y `PredictorFuga`. |
| `modelo_churn.keras` | Notebook 03 | `PredictorFuga`. |
| `correccion_probabilidades.json` | Notebook 03 | `PredictorFuga`. |
| `clientes_financieros_simulados.csv` | Notebook 04 | Streamlit. |
| `incentivos.csv` | Catálogo versionado | Notebook 04 y Streamlit. |

El preprocesador, los NPZ, los metadatos, el modelo y la corrección deben compartir un `artifact_id` compatible. No se reemplaza un artefacto aislado sin verificar los demás.

## Convenciones

- Seguir PEP 8, nombres descriptivos y type hints en contratos públicos.
- Usar `pathlib.Path` y rutas relativas a la raíz del proyecto.
- Preferir funciones deterministas con entradas y salidas explícitas.
- Preservar DataFrames originales o trabajar sobre copias documentadas.
- No capturar excepciones genéricas salvo en el límite de interfaz, donde se registran y se convierten en mensajes seguros.
- No registrar filas completas ni información personal en errores.
- No añadir dependencias o capas arquitectónicas sin necesidad comprobada.

## Pruebas

La suite se ejecuta con:

```bash
uv run pytest -q
```

En la revisión documental actual, el comando completó **56 pruebas aprobadas**.

### Cobertura funcional

| Área | Comprobaciones |
|---|---|
| Datos | Archivos presentes, esquema financiero completo, tipos, finitud, identificadores únicos y rentabilidad coherente. |
| Características | Selección exacta de nueve columnas; `Exited`, `Complain`, identificadores y variables financieras no entran al MLP. |
| Artefactos | `artifact_id`, dimensión 11 y orden de características compatibles. |
| Predicción | Probabilidades finitas en `[0, 1]` y equivalencia individual/lote. |
| Finanzas | GNE negativa, cero y positiva; bloqueo de margen no positivo; elegibilidad; máximo y desempates. |
| Agregados | Decisiones, inversión, beneficio bruto, GNE, ROI, saldo expuesto y efectividad. |
| Filtros | Actúan sobre decisiones existentes y manejan subconjuntos vacíos. |
| Simulación | Cambia resultados sin mutar catálogo, probabilidades ni CSV. |
| Interfaz | Navegación, búsqueda, filtros, formulario y restablecimiento con `AppTest`. |

Las métricas finales del MLP no se usan como comparaciones exactas frágiles en cada prueba; se verifican contratos, rangos y compatibilidad. Las cifras de referencia se documentan desde las salidas guardadas de los notebooks.

## Manejo de errores

Los módulos internos producen errores con contexto técnico; la interfaz muestra mensajes seguros. Se distinguen al menos:

- recurso ausente o sin permisos;
- CSV mal formado o incompleto;
- `CustomerId` ausente o duplicado;
- categoría o dominio no soportado;
- artefactos incompatibles;
- predicción no finita o fuera de `[0, 1]`;
- costo, efectividad o margen fuera de dominio;
- ROI sin inversión.

No se sustituyen silenciosamente valores desconocidos ni se presentan resultados parciales como válidos.

## Actualización del modelo

Ante nuevos datos o cambios de esquema:

1. conservar la versión anterior y su huella;
2. repetir EDA y revisar fuga de información;
3. generar particiones y ajustar un preprocesador nuevo solo con entrenamiento;
4. entrenar y seleccionar con validación;
5. usar prueba una vez para evaluación final;
6. exportar juntos preprocesador, modelo y corrección;
7. regenerar el escenario financiero solo si corresponde;
8. ejecutar pruebas y arrancar Streamlit;
9. actualizar metadatos y documentación.

## Git y entrega

- Mantener cambios pequeños y coherentes.
- Revisar `git status`, `git diff --check` y el alcance antes de cada commit.
- No versionar entornos, cachés, secretos ni archivos temporales.
- No reescribir artefactos grandes sin una razón trazable.
- Confirmar licencia y tamaño antes de redistribuir dataset y modelo.
- Una entrega válida debe abrir con `uv run streamlit run app.py` sin reentrenamiento, base de datos ni descargas manuales de datos.
