# Resultados del análisis exploratorio de datos

[Volver al README](../README.MD) · [Dataset](dataset.md) · [Aprendizaje automático](machine-learning.md) · [Abrir notebook](../notebooks/01_eda.ipynb)

## Estado y alcance

El EDA fue ejecutado completamente sobre `data/Deep_Retention_Dataset.csv` mediante el entorno reproducible definido en `uv.lock`.

```text
SHA-256: 92269A89D774DFD9065F9B8D04A05E7EA647DA289C1A4A83A7893EA50A1ADC3E
```

El notebook contiene 9 celdas de código ejecutadas sin errores y tres figuras. Se limita al diagnóstico exploratorio: calidad, desbalance, estadísticas descriptivas, frecuencias predictoras, revisión visual de valores atípicos, correlaciones y recomendaciones.

No limpia ni transforma el DataFrame, no entrena modelos, no modifica el CSV y no valida la lógica financiera. Las asociaciones observadas no implican causalidad.

La carga utiliza `pathlib` y rutas relativas compatibles tanto con la raíz del proyecto como con la carpeta `notebooks/`.

## Calidad del dataset

| Control | Resultado |
|---|---:|
| Filas | 10.000 |
| Columnas | 21 |
| Celdas faltantes | 0 |
| Filas duplicadas | 0 |
| `CustomerId` duplicados | 0 |
| `CustomerId` únicos | 10.000 |
| Apellidos con `?` | 92 |

El archivo no presenta problemas de calidad que bloqueen el diseño del preprocesamiento. El notebook utiliza `head()`, `info()`, `isna().sum()` y `duplicated()` para mostrar la muestra, los tipos, el conteo de nulos de las 21 columnas y los duplicados.

El EDA detecta 92 apellidos que contienen `?`, pero no los modifica ni crea un DataFrame depurado. Su tratamiento se realiza en [`02_preprocesamiento.ipynb`](../notebooks/02_preprocesamiento.ipynb), sobre una copia independiente del CSV original.

Las columnas numéricas tienen tipos adecuados. Los rangos revisados de crédito, edad, antigüedad, saldo, productos y salario no presentan inconsistencias. `HasCrCard`, `IsActiveMember` y `Exited` contienen exclusivamente los valores binarios `0` y `1`.

Las variables financieras simuladas permanecen en el CSV, pero se excluyen del análisis predictivo. Su validación detallada corresponde a la fase financiera.

## Distribución de `Exited`

| Clase | Clientes | Porcentaje |
|---|---:|---:|
| Permaneció (`0`) | 7.963 | 79,63 % |
| Abandonó (`1`) | 2.037 | 20,37 % |

Existe un desbalance aproximado de 3,91 permanencias por cada abandono. La división posterior se implementó de forma estratificada en el notebook 2; durante el entrenamiento se deberá valorar la ponderación de clases. La exactitud no será suficiente como métrica principal.

## Distribuciones de las predictoras

El notebook conserva:

- estadísticas descriptivas mediante `describe().T` para `CreditScore`, `Age`, `Tenure`, `Balance` y `EstimatedSalary`;
- frecuencias tabulares de `Geography`, `NumOfProducts`, `HasCrCard` e `IsActiveMember`;
- diagramas de caja horizontales de `CreditScore`, `Age`, `Tenure`, `Balance` y `EstimatedSalary`.

Los histogramas permanecen fuera para evitar resultados redundantes. La tabla resume tendencia central y dispersión, mientras que los boxplots permiten revisar visualmente posibles valores atípicos. Las diferencias de escala se tratan en el notebook de preprocesamiento.

### Balance y saldos cero

| Grupo | Clientes | Porcentaje |
|---|---:|---:|
| Saldo cero | 3.617 | 36,17 % |
| Saldo positivo | 6.383 | 63,83 % |

El saldo cero es frecuente y debe conservarse como valor válido, no tratarse como faltante. La distribución de `Balance` ya aparece junto con las demás predictoras numéricas; no se requieren análisis financieros adicionales en esta fase.

### Revisión visual de valores atípicos

Los diagramas de caja horizontales muestran puntos extremos principalmente en `CreditScore` y `Age`. No se genera una tabla adicional ni se eliminan observaciones automáticamente: los boxplots se utilizan únicamente como diagnóstico visual y los casos requieren contexto antes de considerarse errores.

## Matriz de correlación

La matriz de Pearson incluye las ocho predictoras numéricas y `Exited`. Se excluyen `CustomerId`, `Surname`, `Gender`, las variables financieras simuladas y `Geography`; esta última es nominal y se codifica en el notebook de preprocesamiento.

| Predictora | Correlación con `Exited` |
|---|---:|
| `Age` | 0,285 |
| `IsActiveMember` | -0,156 |
| `Balance` | 0,119 |
| `NumOfProducts` | -0,048 |
| `CreditScore` | -0,027 |
| `Tenure` | -0,014 |
| `EstimatedSalary` | 0,012 |
| `HasCrCard` | -0,007 |

Una correlación positiva indica que dos variables tienden a aumentar juntas y una negativa que una tiende a disminuir cuando la otra aumenta. `Age` presenta la mayor asociación lineal positiva con `Exited` (`0,285`), seguida por `Balance` (`0,119`). `IsActiveMember` tiene la asociación negativa de mayor magnitud (`-0,156`).

Las asociaciones restantes son débiles. Esto no determina que una variable sea inútil: Pearson mide relaciones lineales por pares y no captura relaciones no lineales ni interacciones que una red neuronal puede aprender. No se elimina ninguna característica basándose solo en la matriz.

## Decisiones para el preprocesamiento

1. Dividir entrenamiento, validación y prueba de forma estratificada antes de ajustar transformadores; esta decisión se aplica en el notebook 2.
2. Elegir y ajustar el escalador exclusivamente con el conjunto de entrenamiento. Esta decisión se implementa fuera del EDA en `02_preprocesamiento.ipynb` mediante `StandardScaler`.
3. Codificar `Geography` después de la división. Esta decisión se implementa en `02_preprocesamiento.ipynb` con `OneHotEncoder(handle_unknown="ignore")`.
4. Mantener `HasCrCard` e `IsActiveMember` como indicadores binarios validados.
5. Representar en el notebook 2 los 92 apellidos desconocidos mediante `pd.NA`, sin inventar valores; `Surname` no se utiliza como entrada del modelo.
6. No eliminar automáticamente saldos cero ni observaciones señaladas visualmente por los boxplots.
7. Considerar ponderación de clases durante el entrenamiento y métricas adecuadas al desbalance.
8. Ajustar todos los transformadores exclusivamente con el conjunto de entrenamiento.
9. Excluir `CustomerId`, `Surname`, `Gender`, `Exited` y todas las variables financieras simuladas de la matriz de entrada.

## Decisión de fase

El dataset fue diagnosticado sin modificaciones. La limpieza y el pipeline se implementan de manera independiente en `02_preprocesamiento.ipynb`. No se ha avanzado al entrenamiento.
