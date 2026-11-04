# Dataset

[Volver al README](../README.MD) · [Resultados del EDA](eda-results.md) · [Aprendizaje automático](machine-learning.md) · [Modelo financiero](financial-model.md)

## Inventario vigente

| Recurso | Dimensiones | Propósito |
|---|---:|---|
| `data/Customer-Churn-Records.csv` | 10.000 × 18 | Dataset original y fuente de los notebooks 01, 02 y 04. |
| `data/processed/clientes_limpios.csv` | 10.000 × 18 | Copia limpia generada por el notebook 02 para trazabilidad del flujo de ML. |
| `data/processed/clientes_financieros_simulados.csv` | 10.000 × 26 | Dieciocho columnas originales más ocho simuladas; fuente principal de Streamlit. |
| `data/processed/metadata.json` | — | Contrato de preprocesamiento, particiones, esquema y `artifact_id`. |
| `data/incentivos.csv` | 4 filas | Catálogo académico de campañas. |

## Origen y alcance

El dataset representa 10.000 clientes bancarios. El repositorio no incluye una ficha completa de procedencia, licencia, fecha de extracción ni diccionario oficial; estos aspectos deben verificarse antes de redistribuirlo o citarlo formalmente.

Una fila corresponde a un cliente y `CustomerId` es único. No existe una fecha de observación ni una dimensión temporal.

## Convención monetaria

Para garantizar la consistencia monetaria del análisis, se adopta el dólar estadounidense (USD) como moneda de referencia del proyecto. Los saldos bancarios (`Balance`) y los ingresos estimados (`EstimatedSalary`) del dataset original se interpretan en USD como supuesto académico, ya que la fuente no documenta expresamente su moneda. No se aplican conversiones cambiarias y los valores numéricos permanecen inalterados. Los ingresos, costos, márgenes e incentivos financieros se expresan igualmente en USD. El período al que corresponde `EstimatedSalary` tampoco está documentado.

## Dieciocho columnas originales

| Columna | Tipo observado | Significado y uso |
|---|---|---|
| `RowNumber` | `int64` | Número de fila; trazabilidad, no entrada del MLP. |
| `CustomerId` | `int64` | Identificador único; búsqueda y unión, no entrada del MLP. |
| `Surname` | texto | Apellido; presentación, no entrada del MLP. |
| `CreditScore` | `int64` | Puntuación crediticia; predictora. |
| `Geography` | texto | `France`, `Germany` o `Spain`; predictora nominal. |
| `Gender` | texto | `Female` o `Male`; excluida por decisión del proyecto. |
| `Age` | `int64` | Edad en años; predictora. |
| `Tenure` | `int64` | Antigüedad registrada; predictora. |
| `Balance` | `float64` | Saldo interpretado en USD sin conversión; predictora y criterio percentil financiero. |
| `NumOfProducts` | `int64` | Número de productos; predictora. |
| `HasCrCard` | `int64` binaria | Posesión de tarjeta; predictora. |
| `IsActiveMember` | `int64` binaria | Condición de cliente activo; predictora. |
| `EstimatedSalary` | `float64` | Salario estimado interpretado en USD, con período no documentado; predictora. |
| `Exited` | `int64` binaria | Objetivo histórico: `0` permaneció, `1` abandonó. |
| `Complain` | `int64` binaria | Queja; excluida por riesgo de fuga de información. |
| `Satisfaction Score` | `int64` | Puntuación 1–5; diagnóstico, no entrada inicial. |
| `Card Type` | texto | `DIAMOND`, `GOLD`, `PLATINUM` o `SILVER`; diagnóstico. |
| `Point Earned` | `int64` | Puntos acumulados; diagnóstico. |

## Calidad y objetivo

La verificación directa del CSV original y el notebook 01 muestran:

| Control | Resultado |
|---|---:|
| Filas / columnas | 10.000 / 18 |
| Celdas faltantes | 0 |
| Filas duplicadas | 0 |
| `CustomerId` únicos / duplicados | 10.000 / 0 |
| Apellidos con `?` | 92 |
| `Exited = 0` | 7.962 (79,62 %) |
| `Exited = 1` | 2.038 (20,38 %) |
| Coincidencia `Complain = Exited` | 9.986 (99,86 %) |

La coincidencia casi determinista entre `Complain` y `Exited` podría reflejar una variable registrada después o como consecuencia del abandono. Para evitar métricas artificialmente altas, `Complain` no entra al MLP.

## Dataset limpio

El notebook 02 carga el CSV original y trabaja sobre una copia:

- elimina espacios exteriores en columnas de texto;
- sustituye por `pd.NA` el apellido completo de los 92 registros que contienen `?`;
- no reconstruye nombres, no elimina clientes y no altera identificadores;
- conserva 10.000 filas y produce 92 faltantes solo en `Surname`;
- mantiene las nueve predictoras completas, por lo que no requiere imputación.

`clientes_limpios.csv` conserva las 18 columnas originales. Las particiones `.npz` contienen las matrices transformadas, etiquetas, índices originales, `CustomerId` y el identificador común de artefacto.

## Características del MLP

Las nueve características originales autorizadas son:

1. `CreditScore`
2. `Geography`
3. `Age`
4. `Tenure`
5. `Balance`
6. `NumOfProducts`
7. `HasCrCard`
8. `IsActiveMember`
9. `EstimatedSalary`

Quedan fuera `RowNumber`, `CustomerId`, `Surname`, `Gender`, `Exited`, `Complain`, `Satisfaction Score`, `Card Type`, `Point Earned` y las variables financieras simuladas. `Exited` se usa solo como etiqueta durante desarrollo y evaluación.

## Ocho variables financieras simuladas

El notebook 04 conserva las 18 columnas originales sin cambios y añade:

| Columna | Descripción | Unidad simulada |
|---|---|---|
| `MonthlyTransactions_Sim` | Transacciones mensuales estimadas. | transacciones/mes |
| `MonthlyTransactionVolume_USD_Sim` | Volumen mensual estimado. | USD/mes |
| `AvgTransactionFee_USD_Sim` | Comisión promedio. | USD/transacción |
| `AnnualCommissionIncome_USD_Sim` | Ingreso anual por comisiones. | USD/año |
| `AnnualFinancialMargin_USD_Sim` | Contribución financiera anual. | USD/año |
| `AnnualOperatingCosts_USD_Sim` | Costos operativos anuales. | USD/año |
| `AnnualNetMargin_USD_Sim` | Comisiones + contribución − costos. | USD/año |
| `ProfitabilitySegment_Sim` | `Rentable` si el margen es positivo; en otro caso `Deficitario`. | categoría |

Las reglas son deterministas y reproducibles. Se basan en productos, actividad, antigüedad y segmentos percentiles de `Balance`; no usan `Exited` ni `Complain`. No representan ingresos ni costos observados de una entidad real.

### Distinciones financieras

- **Saldo:** `Balance`, interpretado en USD por convención académica y sin conversión cambiaria.
- **Margen neto:** `AnnualNetMargin_USD_Sim`, supuesto académico expresado en USD/año.
- **Beneficio bruto esperado:** suma de `P_f × E_i × M_c` solo para intervenciones recomendadas.
- **Ganancia Neta Esperada (GNE):** beneficio bruto esperado menos costo del incentivo.

El saldo no equivale al margen ni al beneficio recuperable. En la aplicación, el saldo en riesgo se muestra en USD y corresponde a una exposición patrimonial ponderada por la probabilidad de fuga.

## Catálogo de incentivos

`data/incentivos.csv` contiene cuatro incentivos, sus costos, efectividades hipotéticas, márgenes mínimos y requisitos percentiles sobre transacciones, comisiones, saldo y volumen. Estos parámetros son supuestos académicos y no proceden de campañas reales ni del entrenamiento del MLP.

## Limitaciones

- La licencia y procedencia primaria requieren verificación.
- La fuente no documenta formalmente la moneda de `Balance` y `EstimatedSalary`; su interpretación en USD es una convención académica, no una conversión validada contra la fuente.
- No existe información temporal para estudiar deriva o causalidad.
- El objetivo y las variables observadas pueden reflejar sesgos del conjunto de origen.
- Las ocho variables financieras y los incentivos son adecuados para experimentación académica, no para afirmar rentabilidad bancaria real.
