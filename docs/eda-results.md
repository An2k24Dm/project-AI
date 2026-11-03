# Resultados del análisis exploratorio de datos

[Volver al README](../README.MD) · [Dataset](dataset.md) · [Aprendizaje automático](machine-learning.md) · [Abrir notebook](../notebooks/01_eda.ipynb)

## Estado y alcance

`01_eda.ipynb` analiza `data/Customer-Churn-Records.csv` sin modificarlo. El archivo guardado contiene 21 celdas: 14 Markdown y 7 de código, todas estas con conteos de ejecución `1–7`, sin salidas de error y con cuatro figuras.

El EDA cubre calidad, desbalance, descripción de predictoras, valores atípicos, variables adicionales, riesgo de fuga y correlaciones. No limpia datos, ajusta transformadores, entrena modelos ni estudia las variables financieras simuladas, que se crean posteriormente en el notebook 04.

## Dimensiones y tipos

El dataset contiene 10.000 filas y 18 columnas:

- 12 columnas `int64`;
- 2 columnas `float64` (`Balance` y `EstimatedSalary`);
- 4 columnas de texto (`Surname`, `Geography`, `Gender` y `Card Type`).

Las nueve predictoras iniciales son `CreditScore`, `Geography`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `HasCrCard`, `IsActiveMember` y `EstimatedSalary`. `Exited` es la variable objetivo. `RowNumber`, `CustomerId` y `Surname` se reservan para trazabilidad; las variables adicionales se revisan sin incorporarlas automáticamente al MLP.

## Calidad de los datos

| Control | Resultado |
|---|---:|
| Valores faltantes | 0 en las 18 columnas |
| Filas duplicadas | 0 |
| `CustomerId` duplicados / únicos | 0 / 10.000 |
| `RowNumber` duplicados | 0 |
| Apellidos con `?` | 92 |

`head()`, `info()`, `isna().sum()` y `duplicated()` sustentan la inspección. Los dominios de `HasCrCard`, `IsActiveMember`, `Exited` y `Complain` contienen exclusivamente `0` y `1`.

Los rangos observados son coherentes con el esquema: `CreditScore` 350–850, `Age` 18–92, `Tenure` 0–10, `Balance` 0–250.898,09, `NumOfProducts` 1–4, `EstimatedSalary` 11,58–199.992,48, `Satisfaction Score` 1–5 y `Point Earned` 119–1.000.

Los 92 apellidos con `?` se informan, pero no se modifican en el EDA. El notebook 02 representa esos apellidos como desconocidos sobre una copia, sin eliminar clientes ni alterar `CustomerId`.

## Distribución de `Exited`

| Clase | Clientes | Porcentaje |
|---|---:|---:|
| Permaneció (`0`) | 7.962 | 79,62 % |
| Abandonó (`1`) | 2.038 | 20,38 % |

La relación cercana a 4:1 justifica particiones estratificadas, ponderación de clases y métricas sensibles a la clase minoritaria. La exactitud aislada no describe adecuadamente el rendimiento.

## Análisis descriptivo y valores atípicos

El notebook utiliza `describe().T` para las ocho predictoras numéricas y diagramas de caja horizontales para `CreditScore`, `Age`, `Tenure`, `Balance` y `EstimatedSalary`. Los boxplots se usan como diagnóstico visual: no se genera una regla automática de eliminación ni se asume que un punto fuera de los bigotes sea erróneo.

Los valores extremos se observan principalmente en `Age` y `CreditScore`. Las escalas de las variables difieren ampliamente, lo que respalda aplicar escalado después de separar los conjuntos y ajustarlo solo con entrenamiento.

### Saldos cero

| Condición | Clientes | Porcentaje |
|---|---:|---:|
| `Balance = 0` | 3.617 | 36,17 % |
| `Balance > 0` | 6.383 | 63,83 % |

El saldo cero es frecuente y válido; no se interpreta como faltante ni se elimina.

## Variables adicionales y fuga de información

La tabla cruzada de `Complain` y `Exited` muestra 9.986 coincidencias de 10.000 (`99,86 %`): solo 14 filas difieren. La relación casi determinista puede indicar que la queja se registró después o como consecuencia del abandono. Incorporarla produciría fuga de información y resultados artificialmente altos, por lo que se excluye de las entradas del MLP.

`Gender`, `Card Type`, `Satisfaction Score` y `Point Earned` se exploran como contexto. Como el archivo no documenta el momento exacto de captura, el modelo inicial conserva las nueve características aprobadas. Cualquier ampliación requeriría comprobar disponibilidad previa al abandono y posibles implicaciones de equidad.

## Correlación de Pearson

El notebook presenta tanto las correlaciones individuales con `Exited` como una matriz anotada de las ocho predictoras numéricas y la etiqueta. Excluye identificadores, texto, `Gender`, variables adicionales y `Geography`, porque esta última es nominal.

| Predictora | Correlación con `Exited` |
|---|---:|
| `Age` | 0,285296 |
| `Balance` | 0,118577 |
| `EstimatedSalary` | 0,012490 |
| `HasCrCard` | -0,006976 |
| `Tenure` | -0,013656 |
| `CreditScore` | -0,026771 |
| `NumOfProducts` | -0,047611 |
| `IsActiveMember` | -0,156356 |

`Age` presenta la asociación lineal positiva más alta y `IsActiveMember` la negativa de mayor magnitud. Las correlaciones bajas no vuelven inútil una variable: Pearson solo mide asociación lineal por pares y una red neuronal puede aprender interacciones y relaciones no lineales. No se elimina ninguna característica solo por esta matriz.

## Figuras guardadas

1. Distribución de `Exited`.
2. Diagramas de caja horizontales de cinco predictoras numéricas.
3. Barras de correlación de las predictoras numéricas con `Exited`.
4. Matriz de correlación de Pearson anotada.

## Conclusiones para el preprocesamiento

1. Conservar los 10.000 clientes y los saldos cero.
2. Tratar los 92 apellidos desconocidos sobre una copia; `Surname` no entra al MLP.
3. Excluir `Complain` por riesgo de fuga de información.
4. Dividir entrenamiento, validación y prueba de forma estratificada antes de ajustar transformadores.
5. Ajustar `StandardScaler` y `OneHotEncoder` exclusivamente con entrenamiento.
6. Mantener `HasCrCard` e `IsActiveMember` como indicadores binarios.
7. Conservar posibles valores atípicos salvo evidencia de error.
8. Tratar el desbalance mediante ponderación de clases y evaluar ROC-AUC, PR-AUC, Brier Score, Log Loss, precisión, recall y F1.

Estas decisiones se implementan en `02_preprocesamiento.ipynb`; el EDA permanece exclusivamente descriptivo.
