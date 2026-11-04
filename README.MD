# Deep Retention

**Sistema de Retención Selectiva de Clientes**

Deep Retention es un proyecto académico de inteligencia artificial que estima la probabilidad de abandono de clientes bancarios y la combina con un escenario financiero simulado para proponer decisiones de retención trazables. La solución integra un perceptrón multicapa (MLP), un motor de Ganancia Neta Esperada (GNE) y una aplicación Streamlit con buscador, panel ejecutivo y simulador.

> **Estado actual:** el EDA, el preprocesamiento, el entrenamiento, la evaluación, la simulación financiera y las tres vistas de Streamlit están implementados. El informe ejecutivo final continúa pendiente.

## Problema y objetivos

El abandono de clientes no justifica por sí solo una campaña: una intervención también debe ser comercialmente elegible y producir un beneficio esperado superior a su costo. El proyecto persigue cuatro objetivos:

1. Estimar `P(Exited = 1)` mediante un MLP entrenado con nueve características bancarias.
2. Construir un escenario académico de rentabilidad cuando el dataset no contiene ingresos y costos bancarios observados.
3. Evaluar cuatro incentivos con la regla de Ganancia Neta Esperada (GNE), sin usar un umbral fijo de probabilidad para autorizar acciones.
4. Presentar resultados individuales, agregados y de simulación en Streamlit.

La regla económica central es:

\[
\text{GNE}=(P_f \times E_i \times M_c)-C_i
\]

donde `P_f` es la probabilidad ajustada de abandono, `E_i` la efectividad hipotética del incentivo, `M_c` el margen neto anual simulado del cliente y `C_i` el costo anual supuesto.

## Arquitectura general

La solución es un monolito Python modular:

- `app.py` inicializa Streamlit y controla la navegación.
- `ui/pages/` implementa buscador, panel y simulador.
- `ui/services.py` coordina datos, caché, inferencia y escenarios.
- `src/data_processing.py` carga y valida clientes y catálogo.
- `src/prediction.py` aplica el preprocesador, el MLP y la corrección probabilística.
- `src/financial.py` implementa elegibilidad, GNE y decisiones.
- `src/analytics.py` calcula indicadores, filtros y comparaciones.

Streamlit consume artefactos ya exportados; no entrena el modelo ni regenera los datos financieros. La descripción completa está en [Arquitectura](docs/architecture.md).

## Dataset

El dataset original vigente es [`data/Customer-Churn-Records.csv`](data/Customer-Churn-Records.csv):

- 10.000 clientes y 18 columnas observadas;
- objetivo `Exited`;
- 7.962 permanencias (`79,62 %`) y 2.038 abandonos (`20,38 %`);
- sin valores faltantes, filas duplicadas ni `CustomerId` repetidos;
- `Complain` coincide con `Exited` en el `99,86 %` y se excluye por riesgo de fuga de información.

Los tres archivos de clientes cumplen funciones distintas:

| Archivo | Función |
|---|---|
| `data/Customer-Churn-Records.csv` | Fuente original de 18 columnas observadas. |
| `data/processed/clientes_limpios.csv` | Copia limpia de 10.000 filas generada por el notebook 02. |
| `data/processed/clientes_financieros_simulados.csv` | Fuente de Streamlit: 18 columnas originales y ocho financieras simuladas. |

### Convención monetaria

Para garantizar la consistencia monetaria del análisis, se adopta el dólar estadounidense (USD) como moneda de referencia del proyecto. Los saldos bancarios (`Balance`) y los ingresos estimados (`EstimatedSalary`) del dataset original se interpretan en USD como supuesto académico, ya que la fuente no documenta expresamente su moneda. No se aplican conversiones cambiarias y los valores numéricos permanecen inalterados. Los ingresos, costos, márgenes e incentivos financieros se expresan igualmente en USD. Véase [Dataset](docs/dataset.md).

## Flujo de los notebooks

1. [`01_eda.ipynb`](notebooks/01_eda.ipynb): inspecciona calidad, desbalance, distribuciones, valores atípicos, variables adicionales y correlaciones; no modifica datos.
2. [`02_preprocesamiento.ipynb`](notebooks/02_preprocesamiento.ipynb): limpia una copia, conserva los 10.000 clientes, divide 70/15/15 de forma estratificada y ajusta el preprocesador solo con entrenamiento.
3. [`03_red_neuronal.ipynb`](notebooks/03_red_neuronal.ipynb): entrena y evalúa el MLP, decide la corrección probabilística con validación y usa prueba una sola vez al final.
4. [`04_analisis_financiero.ipynb`](notebooks/04_analisis_financiero.ipynb): genera de forma determinista ocho variables financieras, integra probabilidades y evalúa los incentivos y la GNE.

## Preprocesamiento y modelo neuronal

Las nueve entradas originales son `CreditScore`, `Geography`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `HasCrCard`, `IsActiveMember` y `EstimatedSalary`. `StandardScaler` transforma seis numéricas, `OneHotEncoder` genera tres indicadores de `Geography` y las dos binarias pasan sin transformación; el MLP recibe 11 valores.

Las particiones son 7.000 registros de entrenamiento, 1.500 de validación y 1.500 de prueba. El MLP utiliza capas densas de 128 y 64 neuronas con ReLU, Batch Normalization, Dropout de 0,25 y 0,15, salida Sigmoid, Adam, Binary Crossentropy, ponderación de clases y Early Stopping. La ejecución guardada completó 22 épocas; la mejor fue la 10 según `val_loss`.

Resultados finales guardados en prueba:

| Métrica | Resultado |
|---|---:|
| ROC-AUC | 0,886851 |
| PR-AUC | 0,732324 |
| Brier Score | 0,095979 |
| Log Loss | 0,315112 |
| Precision@0.5 | 0,782383 |
| Recall@0.5 | 0,495082 |
| F1@0.5 | 0,606426 |

La corrección posterior al entrenamiento revierte analíticamente el cambio de prior inducido por los pesos de clase. Mejoró Brier Score y Log Loss en validación, pero no es una calibración aprendida ni perfecta. El umbral `0,5` solo se usa para diagnósticos de clasificación; no decide incentivos. Detalles en [Aprendizaje automático](docs/machine-learning.md).

## Modelo financiero simulado

El dataset original no contiene transacciones, comisiones, costos operativos ni margen bancario. El notebook 04 añade ocho variables `_Sim` mediante reglas deterministas basadas en productos, actividad, antigüedad y segmentos relativos de `Balance`. La identidad central es:

\[
\text{Margen neto}=\text{Ingresos por comisiones}+\text{Contribución financiera}-\text{Costos operativos}
\]

Estos valores son supuestos académicos reproducibles, no datos contables observados. El saldo, interpretado en USD sin alterar su valor, solo interviene mediante percentiles; no se convierte directamente en ganancias.

## Catálogo y decisiones

| Incentivo | Costo anual | Efectividad supuesta | Margen mínimo |
|---|---:|---:|---:|
| Bonificación transaccional | USD 20 | 20 % | USD 0 |
| Exoneración de comisiones | USD 50 | 40 % | USD 150 |
| Tasa preferencial | USD 100 | 55 % | USD 400 |
| Gestor personalizado | USD 200 | 75 % | USD 800 |

El motor distingue:

- **Retener:** cliente rentable con una alternativa comercialmente elegible y GNE estrictamente positiva; se elige la mayor.
- **No intervención:** cliente rentable sin alternativa elegible y económicamente conveniente.
- **Salida permitida:** margen neto anual menor o igual a cero; no se autoriza gasto.

Los costos, efectividades y reglas de elegibilidad son supuestos del ejercicio, no fueron aprendidos por el MLP. Véase [Modelo financiero](docs/financial-model.md).

## Aplicación Streamlit

- **Buscador de clientes:** perfil, probabilidad ajustada, indicador de riesgo, datos financieros simulados, alternativa recomendada, beneficio bruto, GNE y auditoría de las cuatro opciones.
- **Panel ejecutivo:** KPI, filtros, gráficos de riesgo, decisiones y economía, y tabla de oportunidades ordenada por GNE.
- **Simulador:** modifica temporalmente costos y efectividades, recalcula decisiones sin repetir la inferencia del MLP, compara escenarios y restablece el catálogo original.

## Resultados principales del escenario base

| Indicador | Resultado |
|---|---:|
| Clientes evaluados | 10.000 |
| Rentables / deficitarios | 7.880 / 2.120 |
| Retener / no intervención / salida permitida | 793 / 7.087 / 2.120 |
| Inversión proyectada | USD 35.600,00 |
| Beneficio bruto esperado | USD 77.780,78 |
| Ganancia Neta Esperada total | USD 42.180,78 |
| ROI proyectado | 118,49 % |

Como indicadores patrimoniales complementarios del notebook 04, 804 clientes cumplen el umbral exploratorio de riesgo crítico (`P_f ≥ 0,65`), con un saldo de USD 68.285.654,02; los 793 clientes seleccionados para retención reúnen un saldo de USD 108.030.424,28. Estos saldos describen exposición patrimonial y no representan beneficio recuperable.

Se recomiendan 350 exoneraciones de comisiones, 335 bonificaciones transaccionales, 102 tasas preferenciales y 6 gestores personalizados. Todas las cifras son proyecciones del escenario simulado, no beneficios realizados.

## Requisitos y ejecución

El proyecto requiere Python 3.11 y [`uv`](https://docs.astral.sh/uv/getting-started/installation/). Desde la raíz:

```bash
uv sync --locked
uv run pytest -q
uv run streamlit run app.py
```

No se requieren base de datos, variables de entorno, Docker ni reentrenamiento para abrir la demostración.

## Pruebas

La suite Pytest cubre carga y validación de datos, compatibilidad de artefactos, predicción individual y por lotes, GNE, elegibilidad, agregados, filtros, simulación e interacciones de Streamlit. La verificación documental actual ejecutó 56 casos correctamente. El procedimiento y la matriz de verificación están en [Desarrollo](docs/development.md).

## Limitaciones

- La procedencia y licencia del dataset deben confirmarse antes de redistribuirlo o citarlo formalmente.
- No existe dimensión temporal ni evidencia de deriva.
- La corrección probabilística es analítica y depende del dataset utilizado.
- Las variables financieras, costos y efectividades son simulados.
- GNE, ROI y abandonos esperados evitados no son resultados de campañas reales.
- El modelo no constituye una validación para uso bancario productivo.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Dataset](docs/dataset.md)
- [Resultados del EDA](docs/eda-results.md)
- [Aprendizaje automático](docs/machine-learning.md)
- [Modelo financiero](docs/financial-model.md)
- [Aplicación](docs/application.md)
- [Desarrollo y pruebas](docs/development.md)
- [Hoja de ruta](docs/roadmap.md)

## Pendiente de entrega

La solución técnica está integrada. Continúan pendientes el informe ejecutivo final y la preparación de la presentación académica; no forman parte de esta actualización documental.
