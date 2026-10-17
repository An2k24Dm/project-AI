# Deep Retention

**Sistema de Retención Selectiva de Clientes**

Deep Retention es un proyecto académico de inteligencia artificial orientado a estimar la probabilidad de abandono de clientes bancarios y convertir esa estimación en decisiones de retención económicamente justificadas. La solución combinará una red neuronal profunda, un motor de rentabilidad y una aplicación interactiva en Streamlit.

> **Estado actual:** documentación técnica, análisis exploratorio, preprocesamiento y primer entrenamiento del MLP completados. El entorno reproducible incluye Scikit-learn, TensorFlow/Keras y las particiones 70/15/15. La evaluación final sobre prueba, calibración, exportación, motor financiero y aplicación todavía están pendientes.

## Objetivos

1. Entrenar un perceptrón multicapa (MLP) que produzca una probabilidad de abandono entre 0 y 1 a partir de características bancarias.
2. Evaluar incentivos mediante su ganancia neta esperada (GNE), no mediante un umbral fijo de probabilidad.
3. Elegir, para cada cliente elegible, la intervención con mayor GNE estrictamente positiva.
4. Presentar resultados individuales, agregados y de simulación en una aplicación Streamlit sencilla.

La regla económica central será:

\[
\text{GNE}=(P_f \times E_i \times M_c)-C_i
\]

donde \(P_f\) es la probabilidad de fuga, \(E_i\) la efectividad estimada del incentivo, \(M_c\) el margen económico del cliente y \(C_i\) el costo del incentivo.

## Alcance funcional

| Capacidad | Estado | Descripción |
|---|---|---|
| Dataset de clientes | Disponible | `data/Deep_Retention_Dataset.csv`, con 10.000 registros y 21 columnas. |
| Documentación técnica | Disponible | Documentos de arquitectura, datos, ML, finanzas, aplicación, desarrollo y hoja de ruta. |
| Catálogo de incentivos | Pendiente | `Deep_Retention_Catalogo_Incentivos.csv` no está presente todavía. |
| Análisis exploratorio | Completado | Notebook ejecutado e [informe de resultados](docs/eda-results.md) verificado. |
| Preprocesamiento | Completado | Particiones estratificadas y `ColumnTransformer` verificados en `notebooks/02_preprocesamiento.ipynb`. |
| MLP de abandono | Entrenamiento inicial completado | Primer candidato entrenado; métricas disponibles solo en validación. |
| Motor financiero | Planificado | Evaluación de elegibilidad y selección de la mayor GNE positiva. |
| Aplicación Streamlit | Planificado | Buscador, dashboard y simulador. |
| Pruebas automatizadas | Planificado | Pruebas unitarias y de integración con Pytest. |

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

La solución será un monolito organizado por responsabilidades funcionales:

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

La estructura combina los entregables actuales con los componentes previstos para las siguientes fases.

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
│   └── 03_red_neuronal.ipynb
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
│   └── incentivos.csv              # pendiente
├── models/
│   ├── modelo_churn.keras
│   └── preprocesador.joblib
├── tests/
├── pyproject.toml
├── uv.lock
├── .python-version
└── .gitignore
```

No se crearán directorios vacíos ni archivos funcionales antes de que su fase correspondiente lo requiera.

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

### Ejecución oficial prevista

Desde la raíz del repositorio:

```bash
uv run streamlit run app.py
```

En el estado actual este comando todavía no es funcional porque `app.py`, los artefactos del modelo y el catálogo de incentivos aún no han sido creados. `pyproject.toml`, `uv.lock` y `.python-version` ya reproducen el entorno del EDA, el preprocesamiento y el entrenamiento inicial.

## Flujo previsto

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

Las fases de documentación inicial, análisis exploratorio, preprocesamiento y primer entrenamiento están completadas. El conjunto de prueba permanece aislado y el proyecto queda a la espera de aprobación antes de avanzar a evaluación final, calibración o exportación.
