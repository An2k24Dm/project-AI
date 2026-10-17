# Aprendizaje automático

[Volver al README](../README.MD) · [Dataset](dataset.md) · [Arquitectura](architecture.md) · [Desarrollo](development.md) · [Hoja de ruta](roadmap.md)

## Estado y objetivo

El [EDA](eda-results.md) y el preprocesamiento reproducible de datos ya están implementados como notebooks independientes. El EDA solo diagnostica el CSV; [`02_preprocesamiento.ipynb`](../notebooks/02_preprocesamiento.ipynb) vuelve a cargarlo, limpia una copia, crea las particiones y transforma las nueve características sin fuga de información. Todavía no se ha entrenado ningún modelo; por tanto, no existen métricas predictivas, curvas, hiperparámetros definitivos ni conclusiones de rendimiento.

El objetivo es aprender, mediante clasificación supervisada, una función que estime:

\[
P(\texttt{Exited}=1 \mid X)
\]

para cada cliente. La salida será una probabilidad entre 0 y 1 y alimentará el motor financiero. El valor histórico `Exited` se utilizará únicamente como etiqueta durante el desarrollo y la evaluación; nunca se mostrará como si fuera la predicción del modelo.

## Datos de entrada

Las nueve características autorizadas son:

| Tipo | Características |
|---|---|
| Numéricas para escalado | `CreditScore`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `EstimatedSalary` |
| Categórica nominal | `Geography` |
| Binarias en passthrough | `HasCrCard`, `IsActiveMember` |

`HasCrCard` e `IsActiveMember` son indicadores binarios y se validan como `0` o `1`. `CustomerId`, `Surname`, `Gender`, todas las columnas `_Sim` y `Exited` quedan fuera de la matriz predictora. Véase el [diccionario del dataset](dataset.md).

## Proceso experimental

```mermaid
flowchart TD
    A[CSV validado] --> B[EDA y controles de calidad]
    B --> L[Limpieza en una copia dentro del notebook 2]
    L --> C[Separación estratificada]
    C --> D[Conjunto de entrenamiento]
    C --> V[Conjunto de validación]
    C --> T[Conjunto de prueba aislado]
    D --> P[Ajustar preprocesador solo con entrenamiento]
    P --> M[Entrenar MLP con class_weight]
    V --> H[Selección y Early Stopping]
    M --> H
    H --> E[Evaluación única en prueba]
    E --> K{¿Calibración necesaria?}
    K -->|Sí| C2[Calibrar sin usar prueba para ajustar]
    K -->|No| X[Exportar artefactos]
    C2 --> X
    X --> O[Inferencia en Streamlit]
```

## Análisis exploratorio implementado

El análisis reproducible ejecutado antes del entrenamiento cubre:

- dimensiones, esquema y tipos inferidos;
- estadística descriptiva adecuada a cada tipo;
- faltantes y registros duplicados;
- rangos inválidos y valores atípicos, sin eliminarlos automáticamente;
- distribución de `Exited` y cuantificación del desbalance;
- distribuciones por clase y relaciones bivariadas relevantes;
- asociaciones entre características, redundancias y posibles proxies;
- visualizaciones con títulos, unidades y población claramente identificados.

El EDA versionado confirmó 10.000 filas, ninguna celda vacía, 92 apellidos con `?` y una tasa histórica de abandono de 20,37 %. Solo informa estos resultados; no modifica los apellidos ni crea un DataFrame depurado.

## Limpieza previa al preprocesamiento

`02_preprocesamiento.ipynb` carga el CSV original de forma independiente y crea `df_clean` como copia en memoria. En esa copia:

- elimina espacios exteriores de las columnas de texto mediante `str.strip()`;
- reemplaza completos por `pd.NA` los 92 apellidos que contienen `?`, sin intentar reconstruirlos;
- conserva las 10.000 filas y todos los `CustomerId`;
- obtiene 92 valores faltantes únicamente en `Surname` y cero faltantes en las nueve predictoras;
- no escribe cambios en el CSV original.

Después de esta limpieza se seleccionan `X` e `y` y se realizan las particiones. Como `Surname` está excluido de `X`, no se incorpora imputación al `ColumnTransformer`.

## División de conjuntos implementada

La separación se realiza en dos etapas con `train_test_split`, `stratify` y `random_state=42`. Produce conjuntos independientes con las siguientes dimensiones:

| Conjunto | Registros | Proporción | Abandonos | Tasa de abandono |
|---|---:|---:|---:|---:|
| Entrenamiento | 7.000 | 70 % | 1.426 | 20,37 % |
| Validación | 1.500 | 15 % | 306 | 20,40 % |
| Prueba | 1.500 | 15 % | 305 | 20,33 % |

Las intersecciones entre los índices de los tres conjuntos son vacías y sus tamaños suman los 10.000 registros originales.

Reglas contra fuga de información:

1. Separar los registros antes de ajustar imputadores, escaladores o codificadores.
2. Ajustar todos los transformadores exclusivamente con entrenamiento.
3. Usar validación para selección de arquitectura, hiperparámetros, época y umbral descriptivo.
4. Mantener prueba aislada hasta elegir el pipeline final.
5. No utilizar variables financieras simuladas para predecir `Exited`.
6. No utilizar el conjunto de prueba para calibrar probabilidades.

Si en el futuro se incorporan observaciones temporales o múltiples filas por cliente, la estrategia de partición deberá cambiar para impedir solapamiento o anticipación temporal.

## Pipeline de preprocesamiento implementado

El `ColumnTransformer` implementado preserva nombres y orden de características:

- **Validación:** comprueba las nueve columnas requeridas, faltantes, valores finitos, dominios binarios y ausencia de solapamiento entre particiones.
- **Numéricas:** `StandardScaler` transforma las seis variables usando exclusivamente medias y desviaciones del entrenamiento.
- **Categórica:** `OneHotEncoder(handle_unknown="ignore")` transforma `Geography` en `Geography_France`, `Geography_Germany` y `Geography_Spain`.
- **Binarias:** `HasCrCard` e `IsActiveMember` se conservan mediante passthrough.
- **Imputación:** no se incorpora porque las nueve predictoras no presentan valores faltantes.

El preprocesador solo recibe `fit_transform` sobre `X_train`; validación y prueba reciben únicamente `transform`. Las matrices resultantes son:

| Matriz | Dimensiones | Tipo |
|---|---:|---|
| `X_train_processed` | 7.000 × 11 | `float32` |
| `X_val_processed` | 1.500 × 11 | `float32` |
| `X_test_processed` | 1.500 × 11 | `float32` |

Las 11 columnas finales corresponden a seis numéricas estandarizadas, tres indicadores geográficos y dos variables binarias. No contienen valores `NaN` ni infinitos y son compatibles con la futura entrada de Keras.

La exportación a `models/preprocesador.joblib` sigue pendiente. Se realizará junto con el entrenamiento para guardar exactamente el transformador utilizado por el modelo aprobado; Streamlit no reconstruirá las transformaciones manualmente.

## Arquitectura inicial del MLP

La arquitectura de partida, sujeta a evaluación, será:

| Etapa | Configuración inicial |
|---|---|
| Entrada | Dimensión producida por el preprocesador. |
| Capa oculta 1 | 64–128 unidades, ReLU, Batch Normalization y Dropout de 0,2–0,3. |
| Capa oculta 2 | 32–64 unidades, ReLU y Dropout de 0,1–0,2. |
| Salida | 1 unidad con Sigmoid. |
| Optimizador | Adam. |
| Pérdida | Binary Crossentropy. |

ReLU aporta no linealidad en las capas ocultas; Sigmoid permite interpretar la salida como una probabilidad. El número exacto de unidades, tasas de Dropout, tasa de aprendizaje, tamaño de lote y número máximo de épocas serán decisiones experimentales, no valores asumidos por esta documentación.

## Entrenamiento y desbalance

El entrenamiento deberá:

- fijar semillas cuando las bibliotecas lo permitan;
- calcular ponderaciones de clase a partir del conjunto de entrenamiento;
- usar el conjunto de validación durante el ajuste;
- aplicar Early Stopping con paciencia dentro del rango de 10 a 15 épocas;
- restaurar los mejores pesos según una métrica de validación elegida explícitamente;
- registrar curvas de pérdida y métricas para diagnosticar sobreajuste;
- conservar configuración, versiones y resultados del experimento seleccionado.

La ponderación de clases busca evitar que la clase mayoritaria domine el aprendizaje. Su efecto deberá evaluarse también sobre la calibración: mejorar el recall no garantiza probabilidades bien calibradas.

## Evaluación

El conjunto de prueba deberá producir, como mínimo:

| Métrica o artefacto | Propósito |
|---|---|
| ROC-AUC | Capacidad de ordenamiento a través de distintos umbrales. |
| PR-AUC | Rendimiento sobre la clase positiva bajo desbalance. |
| Brier Score | Error cuadrático de las probabilidades. |
| Curva de calibración | Correspondencia entre probabilidad estimada y frecuencia observada. |
| Matriz de confusión | Errores para un umbral de análisis declarado. |
| Precision | Proporción de positivos predichos que abandonaron. |
| Recall | Proporción de abandonos históricos detectados. |
| F1-score | Balance armónico entre precision y recall. |

La exactitud podrá reportarse como contexto, pero no será el criterio principal. Los intervalos de confianza o la variabilidad entre semillas son deseables si el calendario lo permite.

### Calibración

Las decisiones económicas multiplican directamente la probabilidad por un margen, por lo que la calibración es crítica. Se comparará la curva de calibración y el Brier Score antes y después de cualquier técnica adicional. Si se aplica calibración, el método se ajustará con datos separados de la prueba final y se exportará como parte inequívoca del flujo de inferencia.

No se añadirá calibración si no mejora evidencia relevante o si introduce fuga de información.

### Umbrales y decisión económica

Un umbral de clasificación puede utilizarse para matrices de confusión, segmentos informativos o análisis de sensibilidad. No reemplaza la regla financiera: la decisión final se obtiene evaluando la GNE de cada incentivo elegible, según se describe en el [modelo financiero](financial-model.md).

## Explicabilidad

Se seleccionará una técnica apropiada para redes neuronales y datos tabulares, por ejemplo importancia por permutación o SHAP, después de verificar compatibilidad y costo computacional. El análisis deberá:

- diferenciar explicaciones globales e individuales;
- operar sobre el pipeline real y documentar el espacio de características interpretado;
- evitar presentar asociación como causalidad;
- comprobar estabilidad y coherencia de los resultados;
- reconocer los límites de interpretar variables codificadas y correlacionadas.

La técnica definitiva y sus resultados quedan pendientes.

## Exportación e inferencia

Los artefactos objetivo son:

```text
models/modelo_churn.keras
models/preprocesador.joblib
```

Antes de exportar se registrarán:

- versión del dataset o huella verificable;
- lista y orden de características;
- partición y semilla;
- versiones de Python, TensorFlow/Keras, Scikit-learn y Joblib;
- arquitectura e hiperparámetros;
- métricas finales y decisión de calibración.

En Streamlit, la inferencia seguirá siempre el orden: validar registro → seleccionar nueve características → transformar con el objeto exportado → ejecutar `predict` con el modelo exportado → validar que la salida sea finita y pertenezca a `[0, 1]` → entregar la probabilidad al motor financiero.

## Limitaciones predictivas

- Los datos son históricos y no prueban causalidad.
- No existe información temporal para medir deriva o cambios de comportamiento.
- El conjunto cubre solo tres geografías observadas.
- Se excluye `Gender` por decisión del proyecto, pero se deberá revisar el rendimiento por subgrupos para detectar disparidades.
- La probabilidad estimada depende de la representatividad, calidad y definición de `Exited`.
- Los resultados académicos no deben presentarse como validación para producción bancaria.
- El rendimiento deberá reevaluarse si cambia el dataset, el preprocesamiento o una dependencia relevante.
