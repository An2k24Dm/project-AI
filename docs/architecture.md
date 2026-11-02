# Arquitectura de la solución

[Volver al README](../README.MD) · [Dataset](dataset.md) · [Aprendizaje automático](machine-learning.md) · [Modelo financiero](financial-model.md) · [Aplicación](application.md)

## Estado del documento

La arquitectura completa está implementada y separa presentación, coordinación y negocio. `app.py` solo configura Streamlit y dirige la navegación; `ui/` contiene páginas, componentes, estilos y servicios; `src/` conserva datos, inferencia, analítica y reglas financieras.

## Estilo arquitectónico

Deep Retention es un monolito Python sencillo, desplegable y ejecutable como una única aplicación Streamlit. La organización es modular por responsabilidad funcional, sin capas ceremoniales ni patrones que no aporten valor al alcance académico.

La solución no utilizará:

- bases de datos relacionales;
- Docker o Docker Compose;
- microservicios o arquitectura distribuida;
- API REST;
- Domain-Driven Design, entidades, objetos de valor o repositorios;
- puertos, adaptadores, Mediator ni un frontend independiente.

Esta decisión reduce la preparación necesaria para la demostración y mantiene explícita la separación entre datos, inferencia, cálculo financiero y presentación.

## Componentes y responsabilidades

| Componente | Responsabilidad | Dependencias principales |
|---|---|---|
| `app.py` | Configuración, navegación, inicialización mínima y errores generales. | Módulos de `ui/`; no contiene gráficos ni negocio. |
| `ui/pages/buscador.py` | Consulta diferida y presentación individual. | Servicios y componentes compartidos. |
| `ui/pages/dashboard.py` | Filtros, KPI, gráficos y tabla de oportunidades. | `src.analytics`; no recalcula decisiones. |
| `ui/pages/simulador.py` | Estado de sesión, formulario y comparación de escenarios. | Servicios y componentes compartidos. |
| `ui/components.py` | Formatos, KPI y avisos reutilizables. | Streamlit. |
| `ui/styles.py` | Paleta y CSS limitado a elementos no cubiertos por el tema. | Streamlit y `.streamlit/config.toml`. |
| `ui/services.py` | Firma de recursos, caché, carga diferida, inferencia y escenarios. | Funciones existentes de `src/`. |
| `src/constants.py` | Rutas y características comunes sin importar TensorFlow. | `pathlib`. |
| `src/data_processing.py` | Lectura de CSV, validación de esquema y preparación de entradas. | Pandas, preprocesador exportado cuando corresponda. |
| `src/prediction.py` | Carga y valida preprocesador, MLP y corrección; predicción individual y por lotes. | TensorFlow/Keras, Joblib. |
| `src/financial.py` | Catálogo, percentiles comerciales, GNE, selección, cartera y agregados. | Pandas, datos financieros y catálogo. |
| `src/analytics.py` | Agregados de cartera, ROI y datos para visualizaciones. | Predicciones y decisiones financieras. |
| Archivos CSV | Fuente local de clientes e incentivos. | Sin servidor de base de datos. |
| Artefactos en `models/` | Modelo, preprocesador y corrección versionados. | Cargados bajo demanda, nunca reentrenados en Streamlit. |

## Diagrama de arquitectura

```mermaid
flowchart LR
    U[Usuario] --> APP[app.py / navegación]

    subgraph MON[Monolito Python]
        APP --> PAGES[ui/pages]
        PAGES --> SVC[ui/services.py]
        PAGES --> CMP[ui/components.py]
        SVC --> DP[src/data_processing.py]
        SVC --> PR[src/prediction.py]
        SVC --> FN[src/financial.py]
        SVC --> AN[src/analytics.py]
        PR --> FN
        FN --> AN
    end

    DC[(CSV de clientes)] --> DP
    IC[(CSV de incentivos)] --> FN
    PP[(preprocesador.joblib)] --> PR
    NN[(modelo_churn.keras)] --> PR
    CP[(correccion_probabilidades.json)] --> PR
    AN --> PAGES

    subgraph OFF[Flujo de entrenamiento fuera de Streamlit]
        PRE[02_preprocesamiento.ipynb] --> PP
        RED[03_red_neuronal.ipynb] --> NN
        RED --> CP
    end
    DC --> PRE
    PRE --> RED
```

Las flechas desde entrenamiento hacia los artefactos representan un proceso separado de la aplicación. La aplicación solo consume artefactos ya generados.

## Flujo de una consulta individual

```mermaid
sequenceDiagram
    actor Usuario
    participant UI as ui/pages/buscador
    participant Servicios as ui/services
    participant Pred as prediction
    participant Prep as preprocesador.joblib
    participant MLP as modelo_churn.keras
    participant Finanzas as financial

    Usuario->>UI: Ingresa CustomerId
    UI->>Servicios: Solicita CustomerId
    Servicios->>Servicios: Recupera datos y percentiles en caché
    Servicios->>Pred: Solicita probabilidad individual
    Pred->>Prep: Transforma 9 características
    Prep-->>Pred: Vector transformado
    Pred->>MLP: Ejecuta inferencia
    MLP-->>Pred: Probabilidad de abandono [0, 1]
    Pred-->>Servicios: Probabilidad con corrección aproximada
    Servicios->>Finanzas: Evalúa incentivos elegibles
    Finanzas-->>Servicios: Mejor GNE positiva o no intervención
    Servicios-->>UI: Perfil y decisión trazable
    UI-->>Usuario: Riesgo, margen y decisión
```

## Contratos entre componentes

### Datos hacia predicción

El módulo de predicción recibirá exactamente estas características, con nombres y tipos validados:

`CreditScore`, `Geography`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `HasCrCard`, `IsActiveMember` y `EstimatedSalary`.

No aceptará `Exited`, identificadores, variables demográficas excluidas ni variables financieras simuladas como entradas del MLP.

### Predicción hacia finanzas

El contrato mínimo es una probabilidad finita dentro de `[0, 1]`, asociada inequívocamente a un `CustomerId`. El motor financiero combina esa probabilidad con el margen del cliente y los parámetros de cada incentivo; no conoce detalles internos de TensorFlow.

### Finanzas hacia presentación

El resultado conserva probabilidad, margen, incentivo, perfil requerido, elegibilidad, costo, efectividad, GNE, motivo y todas las alternativas evaluadas. Un margen no positivo produce «Salida permitida»; un cliente rentable sin alternativa conveniente produce «No intervención».

## Gestión de archivos

La persistencia es exclusivamente local mediante CSV y artefactos serializados:

- El CSV original `data/Deep_Retention_Dataset.csv` se conserva como entrada de solo lectura; la aplicación consume `data/processed/clientes_limpios.csv`.
- `data/incentivos.csv` contiene cuatro acciones y condiciones comerciales académicas verificadas.
- `models/modelo_churn.keras` contiene la red entrenada.
- `models/preprocesador.joblib` contiene el pipeline ajustado con entrenamiento.
- `models/correccion_probabilidades.json` registra la corrección aproximada por pesos de clase y el identificador de artefacto.

La aplicación tratará estos archivos como entradas de solo lectura. Las simulaciones vivirán en el estado de sesión de Streamlit y no sobrescribirán los CSV.

## Inicio y ciclo de vida

Al iniciar, Streamlit valida la presencia y metadatos de clientes, catálogo y artefactos, pero solo carga los CSV. La firma de versión combina nombre, tamaño y fecha de modificación en nanosegundos de los cinco recursos. Un cambio normal en cualquiera de ellos crea una clave de caché nueva.

El predictor se crea con `st.cache_resource` al buscar un cliente o abrir una vista de cartera. Los datos, percentiles, probabilidades, escenario base y escenarios simulados usan `st.cache_data`. El panel ejecuta la inferencia por lotes una sola vez por versión; el simulador reutiliza esas probabilidades y los percentiles originales.

La ejecución oficial es:

```bash
uv run streamlit run app.py
```

La primera ejecución podrá requerir Internet para resolver dependencias. El funcionamiento normal no dependerá de descargas externas de datos o modelos.

## Decisiones y límites

- La separación funcional facilita las pruebas sin introducir una arquitectura distribuida.
- CSV simplifica la demostración, pero no ofrece concurrencia, control transaccional ni escalabilidad de una base de datos.
- Los artefactos deben crearse con versiones compatibles con el entorno de inferencia.
- Los resultados financieros son proyecciones basadas en datos y supuestos simulados, no resultados reales de una campaña.
- La distribución del dataset y de los artefactos queda condicionada a comprobar licencia y tamaño antes de la entrega.
