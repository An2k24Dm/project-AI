# Aprendizaje automático

[Volver al README](../README.MD) · [Dataset](dataset.md) · [Arquitectura](architecture.md) · [Modelo financiero](financial-model.md) · [Desarrollo](development.md)

## Estado y objetivo

El preprocesamiento, entrenamiento, evaluación y exportación están implementados en los notebooks 02 y 03. `src/prediction.py` consume los artefactos resultantes para inferencia individual y por lotes; Streamlit no limpia datos, ajusta transformadores ni reentrena el modelo.

El MLP estima:

\[
P(\texttt{Exited}=1 \mid X)
\]

`Exited` es la etiqueta histórica durante desarrollo y evaluación, nunca una entrada del modelo ni un sustituto de su predicción.

## Limpieza y selección de variables

`02_preprocesamiento.ipynb` carga `data/Customer-Churn-Records.csv` de forma independiente y crea una copia `df_clean`. Sobre esa copia:

- elimina espacios exteriores de las columnas de texto;
- sustituye por `pd.NA` el apellido completo de 92 registros con `?`;
- no reconstruye nombres ni elimina filas;
- conserva 10.000 clientes y sus identificadores;
- obtiene 92 faltantes solo en `Surname`, columna excluida del modelo;
- valida dominios binarios, rangos y valores finitos.

Las nueve características originales son:

| Tratamiento | Características |
|---|---|
| `StandardScaler` | `CreditScore`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `EstimatedSalary` |
| `OneHotEncoder` | `Geography` |
| Passthrough | `HasCrCard`, `IsActiveMember` |

Quedan fuera `Exited`, `Complain`, identificadores, `Surname`, `Gender`, las variables adicionales y las financieras simuladas. `Complain` se excluye expresamente por su coincidencia del 99,86 % con `Exited`.

## Particiones estratificadas

La separación usa `train_test_split`, `stratify` y `random_state=42`:

| Conjunto | Registros | `Exited = 1` | Tasa de abandono |
|---|---:|---:|---:|
| Entrenamiento | 7.000 | 1.427 | 20,3857 % |
| Validación | 1.500 | 306 | 20,4000 % |
| Prueba | 1.500 | 305 | 20,3333 % |

Los conjuntos no se solapan y cubren las 10.000 filas. La prueba se reserva para la evaluación final: antes del entrenamiento, el notebook 03 solo consulta sus identificadores para comprobar compatibilidad y ausencia de solapamiento; carga `X_test` e `y_test` una vez cerradas la arquitectura y la corrección probabilística.

## Preprocesador

El `ColumnTransformer` se ajusta mediante `fit_transform` exclusivamente sobre entrenamiento. Validación y prueba reciben solo `transform`:

- seis variables numéricas estandarizadas;
- `Geography_France`, `Geography_Germany` y `Geography_Spain`;
- dos variables binarias sin transformación.

Las nueve entradas originales producen 11 valores numéricos `float32`:

| Matriz | Dimensiones |
|---|---:|
| Entrenamiento | 7.000 × 11 |
| Validación | 1.500 × 11 |
| Prueba | 1.500 × 11 |

No se implementa imputación porque las predictoras no presentan faltantes. `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` evita fallar ante una categoría geográfica no vista, aunque su significado debería revisarse antes de un uso real.

## Artefactos de preprocesamiento

El notebook 02 exporta y verifica:

| Archivo | Función |
|---|---|
| `data/processed/clientes_limpios.csv` | Copia limpia de 10.000×18. |
| `data/processed/train.npz` | `X`, `y`, índices, `CustomerId` y `artifact_id` de entrenamiento. |
| `data/processed/validation.npz` | Partición de validación con el mismo contrato. |
| `data/processed/test.npz` | Partición de prueba reservada. |
| `data/processed/metadata.json` | Fuente, SHA-256, semilla, esquema, formas y orden de características. |
| `models/preprocesador.joblib` | `ColumnTransformer` ajustado solo con entrenamiento. |

El identificador actual es `9d8ff84b7ef5921f` y aparece en metadatos, NPZ, preprocesador y configuración de corrección. La versión guardada del notebook tiene habilitada la exportación y muestra controles de recarga satisfactorios.

## Arquitectura del MLP

| Etapa | Configuración implementada |
|---|---|
| Entrada | 11 características. |
| Capa oculta 1 | 128 neuronas, ReLU. |
| Regularización | Batch Normalization y Dropout `0,25`. |
| Capa oculta 2 | 64 neuronas, ReLU. |
| Regularización | Dropout `0,15`. |
| Salida | 1 neurona, Sigmoid. |
| Parámetros | 10.369 totales: 10.113 entrenables y 256 no entrenables. |
| Optimizador | Adam. |
| Pérdida | Binary Crossentropy. |
| Seguimiento | Binary Accuracy, ROC-AUC y PR-AUC. |

El entrenamiento fija semilla 42, determinismo de TensorFlow, un máximo de 100 épocas y `batch_size=64`. Early Stopping vigila `val_loss`, usa paciencia 12 y restaura los mejores pesos.

## Desbalance y entrenamiento

`compute_class_weight(class_weight="balanced")` calcula los pesos solo sobre `y_train`:

| Clase | Registros | Peso |
|---|---:|---:|
| `0` | 5.573 | 0,628028 |
| `1` | 1.427 | 2,452698 |

No se aplica SMOTE ni se duplican o eliminan observaciones. La ejecución guardada completó 22 épocas; la menor `val_loss` apareció en la época 10 (`0,466119`), cuyos pesos fueron restaurados.

## Corrección probabilística

La ponderación de clases cambia el prior efectivo del entrenamiento. Por ello se evalúa en validación una corrección analítica:

\[
p_{ajustada}=\frac{p}{p+(w_1/w_0)(1-p)}
\]

| Métrica de validación | Original | Corregida |
|---|---:|---:|
| ROC-AUC | 0,854542 | 0,854542 |
| PR-AUC | 0,691390 | 0,691390 |
| Brier Score | 0,153208 | 0,105419 |
| Log Loss | 0,466119 | 0,343671 |

La transformación es monótona: conserva ROC-AUC y PR-AUC, y fue seleccionada porque mejoró simultáneamente Brier Score y Log Loss. Es una corrección algebraica por pesos de clase, no una calibración aprendida mediante un modelo independiente ni una garantía de calibración perfecta.

Con umbral diagnóstico `0,5`, validación obtuvo precisión `0,732673`, recall `0,483660` y F1 `0,582677`. Ese umbral solo sirve para la matriz de confusión y métricas descriptivas; no autoriza incentivos.

## Interpretabilidad mediante importancia por permutación

El notebook 03 evalúa el MLP realmente entrenado mediante importancia por permutación. Las 1.500 filas originales de validación se recuperan en el orden de los `customer_ids` guardados en `validation.npz`; antes del cálculo se comprueba la coincidencia de identificadores, etiquetas, `artifact_id` y matriz transformada. El conjunto de prueba no participa.

Cada una de las nueve variables originales se permuta por separado cinco veces con semillas fijas. `Geography` se trata como una única característica categórica. La importancia es la disminución media del ROC-AUC ajustado frente al valor de referencia de **0,854542**:

| Variable | Importancia media | Desviación estándar |
|---|---:|---:|
| `NumOfProducts` | 0,144935 | 0,006642 |
| `Age` | 0,098243 | 0,010874 |
| `IsActiveMember` | 0,032636 | 0,008111 |
| `Balance` | 0,027758 | 0,003775 |
| `Geography` | 0,020826 | 0,003795 |
| `CreditScore` | 0,001710 | 0,001782 |
| `HasCrCard` | 0,001007 | 0,000374 |
| `EstimatedSalary` | -0,000910 | 0,003360 |
| `Tenure` | -0,005239 | 0,002992 |

Los tres factores con mayor importancia positiva son `NumOfProducts`, `Age` e `IsActiveMember`. Las importancias negativas o cercanas a cero reflejan variabilidad de esta medición sobre validación y no justifican eliminar características. Esta técnica describe la sensibilidad predictiva del MLP; no sustituye las correlaciones de Pearson del EDA ni demuestra causalidad.

## Evaluación final en prueba

| Métrica | Resultado |
|---|---:|
| ROC-AUC | 0,886851 |
| PR-AUC | 0,732324 |
| Brier Score | 0,095979 |
| Log Loss | 0,315112 |
| Precision@0.5 | 0,782383 |
| Recall@0.5 | 0,495082 |
| F1@0.5 | 0,606426 |

Estas cifras corresponden a las salidas guardadas del notebook 03. No constituyen validación para producción bancaria y el conjunto de prueba no participa en la inferencia de cartera ni en las reglas financieras.

## Exportación e inferencia

| Artefacto | Contenido |
|---|---|
| `models/preprocesador.joblib` | Transformaciones aprendidas con entrenamiento. |
| `models/modelo_churn.keras` | Arquitectura y pesos restaurados del MLP. |
| `models/correccion_probabilidades.json` | Método, pesos de clase, métricas de validación, orden de entradas y `artifact_id`. |

`PredictorFuga` valida los tres artefactos, selecciona exactamente las nueve características, transforma 9→11, ejecuta Keras y aplica la corrección. Las probabilidades deben ser finitas y pertenecer a `[0, 1]`; la predicción por lotes preserva el orden de los clientes.

Las columnas adicionales, incluidas `Exited`, `Complain` y las ocho financieras, se ignoran como entradas. Streamlit reutiliza las probabilidades en el dashboard y el simulador; cambiar costos o efectividades no vuelve a ejecutar el MLP.

## Decisión financiera y limitaciones

La clasificación visual de riesgo y el umbral `0,5` están separados de la decisión económica. El motor evalúa la elegibilidad y la Ganancia Neta Esperada (GNE) de cada incentivo y selecciona solo alternativas con GNE positiva.

Limitaciones principales:

- datos históricos sin dimensión temporal ni prueba causal;
- tres geografías observadas;
- corrección probabilística analítica dependiente del dataset;
- falta de evaluación formal por subgrupos y necesidad de confirmar la estabilidad de la importancia por permutación ante datos nuevos;
- necesidad de reevaluar el modelo ante cambios de datos, esquema o dependencias.
