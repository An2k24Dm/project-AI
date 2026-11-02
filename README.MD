# Deep Retention

**Sistema de Retención Selectiva de Clientes**

Deep Retention es un proyecto académico de inteligencia artificial orientado a estimar la probabilidad de abandono de clientes bancarios y convertir esa estimación en decisiones de retención económicamente justificadas. La solución combina una red neuronal profunda, un motor de rentabilidad y una aplicación interactiva en Streamlit.

> **Estado actual:** la solución integrada está implementada: inferencia con el MLP exportado, motor de GNE, catálogo de acciones y aplicación Streamlit con buscador, panel de cartera y simulador. El modelo obtuvo ROC-AUC 0,8635 y Brier Score ajustado 0,0995 en prueba. La corrección de probabilidades es aproximada, no una calibración aprendida.

## Objetivos

1. Entrenar un perceptrón multicapa (MLP) que produzca una probabilidad de abandono entre 0 y 1 a partir de características bancarias.
2. Evaluar incentivos mediante su ganancia neta esperada (GNE), no mediante un umbral fijo de probabilidad.
3. Elegir, para cada cliente elegible, la intervención con mayor GNE estrictamente positiva.
4. Presentar resultados individuales, agregados y de simulación en una aplicación Streamlit sencilla.

La regla económica central es:

\[
\text{GNE}=(P_f \times E_i \times M_c)-C_i
\]

donde \(P_f\) es la probabilidad de fuga, \(E_i\) la efectividad estimada del incentivo, \(M_c\) el margen económico del cliente y \(C_i\) el costo del incentivo.

## Alcance funcional

| Capacidad | Estado | Descripción |
|---|---|---|
| Dataset de clientes | Disponible | `data/Deep_Retention_Dataset.csv`, con 10.000 registros y 21 columnas. |
| Documentación técnica | Disponible | Documentos de arquitectura, datos, ML, finanzas, aplicación, desarrollo y hoja de ruta. |
| Catálogo de incentivos | Completado | `data/incentivos.csv`, con cuatro acciones y reglas académicas explícitas de elegibilidad. |
| Análisis exploratorio | Completado | Notebook ejecutado e [informe de resultados](docs/eda-results.md) verificado. |
| Preprocesamiento | Completado | Limpieza, particiones estratificadas, `ColumnTransformer` y artefactos reproducibles verificados en `notebooks/02_preprocesamiento.ipynb`. |
| MLP de abandono | Completado | Modelo evaluado y exportado; inferencia individual y por lotes mediante `PredictorFuga`. |
| Motor financiero | Completado | Elegibilidad comercial, GNE, desempate determinista y agregados de cartera verificados. |
| Aplicación Streamlit | Completada | Buscador individual, panel ejecutivo y simulador temporal. |
| Pruebas automatizadas | Implementadas | 44 pruebas Pytest para datos, predicción, finanzas, analítica, escenarios e inicio de Streamlit. |

## Tecnologías definidas

| Componente | Tecnología |
|---|---|
| Lenguaje | Python |
| Aplicación web | Streamlit |
| Red neuronal | TensorFlow / Keras |
| Preprocesamiento | Scikit-learn |
| Datos | Pandas y NumPy |
| Visualización | Plotly y Matplotlib |
| Persistencia | Archivos CSV |
| Preprocesador exportado | Joblib |
| Modelo exportado | Formato Keras `.keras` |
| Dependencias y ejecución | uv |
| Pruebas | Pytest |
| Versionado | Git y GitHub |

Python 3.11, Scikit-learn 1.9.1 y TensorFlow 2.21.0 están fijados por el entorno reproducible. No se utilizan bases de datos, Docker, microservicios, API REST ni un frontend independiente.

## Arquitectura resumida

La solución es un monolito organizado por responsabilidades funcionales:

- `app.py`: interfaz Streamlit.
- `src/data_processing.py`: lectura, validación y preparación de datos.
- `src/prediction.py`: carga de artefactos e inferencia.
- `src/financial.py`: elegibilidad, incentivos y cálculos económicos.
- `src/analytics.py`: indicadores agregados del dashboard.
- `training/train.py`: entrenamiento reproducible del MLP.
- `training/evaluate.py`: evaluación, calibración y explicabilidad.

Streamlit leerá los datos locales, utilizará el preprocesador y el modelo ya exportados y pasará las probabilidades al motor financiero. El inicio de la aplicación nunca entrenará el modelo.

La explicación completa se encuentra en [Arquitectura](docs/architecture.md).

## Estructura objetivo

La estructura combina los entregables de análisis, entrenamiento, finanzas y aplicación:

```text
project-AI/
├── README.MD
├── docs/
│   ├── architecture.md
│   ├── dataset.md
│   ├── machine-learning.md
│   ├── financial-model.md
│   ├── application.md
│   ├── development.md
│   ├── eda-results.md
│   └── roadmap.md
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocesamiento.ipynb
│   ├── 03_red_neuronal.ipynb
│   └── 04_analisis_financiero.ipynb
├── app.py
├── src/
│   ├── data_processing.py
│   ├── prediction.py
│   ├── financial.py
│   └── analytics.py
├── training/
│   ├── train.py
│   └── evaluate.py
├── data/
│   ├── Deep_Retention_Dataset.csv
│   ├── processed/
│   │   ├── clientes_limpios.csv
│   │   ├── train.npz
│   │   ├── validation.npz
│   │   ├── test.npz
│   │   └── metadata.json
│   └── incentivos.csv
├── models/
│   ├── preprocesador.joblib
│   ├── modelo_churn.keras
│   └── correccion_probabilidades.json
├── tests/
│   ├── test_prediction.py
│   ├── test_financial.py
│   └── test_application.py
├── pyproject.toml
├── uv.lock
├── .python-version
└── .gitignore
```

La aplicación consume únicamente recursos versionados del repositorio y mantiene las simulaciones en memoria.

## Requisitos de ejecución

Cuando la implementación esté terminada, el profesor solo necesitará:

- Git para clonar o descargar el proyecto.
- `uv` instalado.
- Conexión a Internet durante la primera preparación de dependencias, si no están disponibles en la caché local.

No serán necesarias variables de entorno, una base de datos ni ejecutar el entrenamiento para usar la demostración. El repositorio deberá distribuir el dataset, el catálogo, el modelo y el preprocesador, sujetos a la licencia y a los límites de tamaño de GitHub.

### Instalación de uv

Se recomienda seguir la [guía oficial de instalación de uv](https://docs.astral.sh/uv/getting-started/installation/). Una alternativa independiente de la plataforma, para quien ya disponga de `pipx`, es:

```bash
pipx install uv
```

La instalación puede comprobarse con:

```bash
uv --version
```

### Ejecución oficial

Desde la raíz del repositorio:

```bash
uv run streamlit run app.py
```

El comando inicia la aplicación con el dataset depurado, el catálogo, el preprocesador, el MLP y la corrección probabilística ya disponibles. No ejecuta entrenamiento ni modifica los CSV.

## Orden reproducible de los notebooks

1. Ejecutar `notebooks/02_preprocesamiento.ipynb` para cargar y limpiar una copia del CSV, crear las particiones, ajustar el preprocesador solo con entrenamiento y exportar todos los artefactos de datos.
2. Ejecutar `notebooks/03_red_neuronal.ipynb` para cargar exclusivamente `train.npz`, `validation.npz` y `metadata.json`, y entrenar el MLP candidato.
3. Ejecutar `notebooks/04_analisis_financiero.ipynb` para reproducir la inferencia y las decisiones económicas de los 10.000 clientes con los artefactos exportados.

`notebooks/01_eda.ipynb` es un diagnóstico independiente. `test.npz` ya fue utilizado para la evaluación final documentada, pero no se carga en el entrenamiento ni en el análisis financiero de cartera.

Las pruebas automatizadas se ejecutan desde la raíz con:

```bash
uv run pytest -q
```

## Flujo de la aplicación

1. La aplicación carga el dataset, el catálogo de incentivos, el preprocesador y el modelo exportado.
2. El usuario busca un cliente o consulta la cartera.
3. Se seleccionan exclusivamente las nueve características aprobadas para inferencia.
4. El preprocesador aplica exactamente las transformaciones aprendidas durante el entrenamiento.
5. El MLP devuelve una probabilidad de abandono; nunca se presenta `Exited` como predicción.
6. El motor financiero evalúa los incentivos elegibles, descarta GNE menores o iguales a cero y evita intervenir clientes deficitarios.
7. Streamlit muestra la recomendación o permite simular supuestos sin sobrescribir los CSV.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Dataset](docs/dataset.md)
- [Resultados del EDA](docs/eda-results.md)
- [Aprendizaje automático](docs/machine-learning.md)
- [Modelo financiero](docs/financial-model.md)
- [Aplicación](docs/application.md)
- [Desarrollo y pruebas](docs/development.md)
- [Hoja de ruta](docs/roadmap.md)

## Estado y próximo hito

Los objetivos de predicción, rentabilidad, selección de incentivos e interfaz interactiva están completados y verificados. En el escenario base se recomiendan 1.214 intervenciones, con inversión proyectada de USD 66.640,00 y GNE académica de USD 90.099,69; ninguna se asigna a clientes con margen no positivo. Estas cifras son simulaciones, no ganancias realizadas. El siguiente hito documental es elaborar el informe ejecutivo y preparar la demostración académica.
