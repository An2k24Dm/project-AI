# Dataset

[Volver al README](../README.MD) · [Arquitectura](architecture.md) · [Aprendizaje automático](machine-learning.md) · [Modelo financiero](financial-model.md)

## Inventario actual

La inspección inicial del repositorio encontró:

| Recurso | Estado | Observación |
|---|---|---|
| `data/Deep_Retention_Dataset.csv` | Disponible | 10.000 filas y 21 columnas; EDA completado. |
| `data/incentivos.csv` | Disponible | Cuatro acciones con costos, efectividades y reglas comerciales académicas. |

La ubicación vigente del dataset es `data/Deep_Retention_Dataset.csv`. La copia limpia para inferencia está en `data/processed/clientes_limpios.csv` y el catálogo vigente en `data/incentivos.csv`.

## Origen y alcance

El dataset principal procede de un conjunto de abandono bancario de aproximadamente 10.000 clientes y fue complementado con variables financieras simuladas para el ejercicio académico. El repositorio actual no incluye una ficha de procedencia, licencia, fecha de extracción ni diccionario oficial del conjunto base; estos datos deberán verificarse antes de redistribuirlo o citarlo en el informe ejecutivo.

Los campos con sufijo `_Sim` son simulados. Sus importes no representan información bancaria real ni resultados observados de una institución.

## Estructura real

La siguiente tabla describe las 21 columnas observadas en el encabezado. Las unidades no declaradas se mantienen como tales para evitar suposiciones.

| Columna | Tipo conceptual | Origen | Significado | Unidad / dominio observado | Uso previsto |
|---|---|---|---|---|---|
| `CustomerId` | Identificador | Base | Identificador único del cliente. | Entero; 10.000 valores únicos. | Búsqueda y unión; no entrenamiento. |
| `Surname` | Categórica | Base | Apellido del cliente. | Texto. | Presentación; no entrenamiento. |
| `Gender` | Categórica | Base | Género consignado en el conjunto. | `Female`, `Male`. | Presentación; no entrenamiento. |
| `Geography` | Categórica | Base | País o mercado geográfico. | `France`, `Germany`, `Spain`. | Predictora. |
| `Age` | Numérica | Base | Edad del cliente. | Años; rango observado 18–92. | Predictora. |
| `Tenure` | Numérica discreta | Base | Antigüedad registrada. | Años; rango observado 0–10. | Predictora. |
| `CreditScore` | Numérica | Base | Puntuación crediticia. | Puntos; rango observado 350–850. | Predictora. |
| `Balance` | Numérica | Base | Saldo bancario. | Unidad monetaria no declarada; rango 0–250.898,09. | Predictora y elegibilidad relativa por percentiles. |
| `NumOfProducts` | Numérica discreta | Base | Cantidad de productos contratados. | Conteo; rango observado 1–4. | Predictora. |
| `HasCrCard` | Binaria | Base | Indica si tiene tarjeta de crédito. | `0` = no, `1` = sí. | Predictora. |
| `IsActiveMember` | Binaria | Base | Indica si es miembro activo. | `0` = no, `1` = sí. | Predictora. |
| `EstimatedSalary` | Numérica | Base | Salario estimado. | Unidad monetaria y período no declarados; rango 11,58–199.992,48. | Predictora. |
| `MonthlyTransactions_Sim` | Numérica discreta | Simulada | Cantidad mensual de transacciones. | Transacciones/mes; rango 1–44. | Cálculo/visualización financiera; no entrenamiento. |
| `MonthlyTransactionVolume_USD_Sim` | Numérica | Simulada | Volumen transaccional mensual. | USD/mes; rango 2,55–19.395,11. | Cálculo/visualización financiera; no entrenamiento. |
| `AvgTransactionFee_USD_Sim` | Numérica | Simulada | Comisión promedio por transacción. | USD/transacción; rango 0,18–0,56. | Cálculo financiero; no entrenamiento. |
| `AnnualCommissionIncome_USD_Sim` | Numérica | Simulada | Ingreso anual por comisiones. | USD/año; rango 20,28–316,08. | Cálculo financiero; no entrenamiento. |
| `AnnualFinancialMargin_USD_Sim` | Numérica | Simulada | Margen financiero anual. | USD/año; rango 0–1.353,18. | Cálculo financiero; no entrenamiento. |
| `AnnualOperatingCosts_USD_Sim` | Numérica | Simulada | Costos operativos anuales. | USD/año; rango 116,99–348,52. | Cálculo financiero; no entrenamiento. |
| `AnnualNetMargin_USD_Sim` | Numérica | Simulada | Margen neto anual derivado. | USD/año; rango -163,62–1.253,97. | Margen del motor financiero; no entrenamiento. |
| `ProfitabilitySegment_Sim` | Categórica | Simulada | Segmento comercial de rentabilidad. | `Rentable`, `No rentable`. | Información/elegibilidad; no entrenamiento. |
| `Exited` | Binaria | Base | Resultado histórico de abandono. | `0` = permaneció, `1` = abandonó. | Objetivo; nunca entrada ni predicción mostrada. |

### Distinciones financieras obligatorias

- **Saldo bancario:** `Balance`; no equivale al margen ni al capital recuperable por sí solo.
- **Cantidad de transacciones:** `MonthlyTransactions_Sim`.
- **Volumen transaccional:** `MonthlyTransactionVolume_USD_Sim`; es un importe agregado, no un conteo.
- **Ingresos por comisiones:** `AnnualCommissionIncome_USD_Sim`.
- **Margen financiero:** `AnnualFinancialMargin_USD_Sim`.
- **Costos operativos:** `AnnualOperatingCosts_USD_Sim`.
- **Margen neto:** `AnnualNetMargin_USD_Sim`; es el valor previsto para evaluar rentabilidad, sujeto a validación de su fórmula de generación.

## Características del modelo

La matriz predictora utilizará exclusivamente:

1. `CreditScore`
2. `Geography`
3. `Age`
4. `Tenure`
5. `Balance`
6. `NumOfProducts`
7. `HasCrCard`
8. `IsActiveMember`
9. `EstimatedSalary`

La variable objetivo es `Exited`.

Quedan excluidas de las entradas:

- `CustomerId`, porque es un identificador;
- `Surname` y `Gender`, por decisión explícita del proyecto;
- todas las variables con sufijo `_Sim`, porque pertenecen al análisis financiero posterior;
- `Exited`, para impedir fuga directa de la respuesta histórica.

## Perfil de calidad observado

La inspección estructural inicial produjo estos resultados reproducibles sobre el archivo actual:

| Comprobación | Resultado |
|---|---|
| Filas | 10.000 |
| Columnas | 21 |
| Celdas vacías por columna | 0 en las 21 columnas |
| Filas completas duplicadas | 0 |
| `CustomerId` duplicados | 0 |
| `Exited = 0` | 7.963 (79,63 %) |
| `Exited = 1` | 2.037 (20,37 %) |
| Segmento `Rentable` | 6.398 |
| Segmento `No rentable` | 3.602 |

El EDA reproducible confirmó estos controles y amplió el análisis de tipos, consistencia, distribuciones, valores atípicos y asociaciones. Véanse los [resultados del EDA](eda-results.md). El desbalance observado en `Exited` justifica evaluar ponderación de clases y métricas distintas de la exactitud.

## Catálogo de incentivos

`data/incentivos.csv` contiene `incentivo_id`, nombre, costo anual en USD, efectividad, margen neto anual mínimo, perfil requerido y cuatro posibles requisitos percentiles. Los percentiles vinculan cada acción con `MonthlyTransactions_Sim`, `AnnualCommissionIncome_USD_Sim`, `Balance` o `MonthlyTransactionVolume_USD_Sim`.

Los costos, efectividades, márgenes mínimos y umbrales son supuestos académicos. `validar_catalogo()` comprueba esquema, faltantes, duplicados, dominios, importes y perfiles antes de cualquier decisión. El catálogo no se presenta como política real de una entidad bancaria.

## Limitaciones

- La fuente primaria y la licencia no están documentadas en el repositorio.
- Las unidades monetarias de `Balance` y `EstimatedSalary` no están declaradas.
- Las variables simuladas son adecuadas para experimentación académica, no para afirmar impacto bancario real.
- El objetivo histórico puede reflejar sesgos o condiciones del conjunto de origen no descritas.
- La cobertura geográfica se limita a tres categorías observadas; categorías nuevas exigirán una política explícita en el codificador.
- Una fila representa un cliente, pero no hay fecha de observación ni dimensión temporal para estudiar cambios o deriva.
- El segmento simulado no reemplaza la decisión financiera: la recomendación final depende de elegibilidad, margen, costo, efectividad y GNE.
