# Hoja de ruta

[Volver al README](../README.MD) · [Arquitectura](architecture.md) · [Dataset](dataset.md) · [Desarrollo](development.md)

## Criterio de estados

| Estado | Significado |
|---|---|
| Completada | Los entregables y criterios indicados fueron verificados. |
| Pendiente | La fase todavía no comenzó o no cumple todos sus criterios. |

La documentación inicial, el EDA y el preprocesamiento se marcan como completados. No se atribuyen avances de entrenamiento, evaluación ni resultados financieros que todavía no existen.

## Resumen

| Fase | Estado | Dependencia principal |
|---|---|---|
| 1. Documentación inicial | Completada | Requisitos e inspección del repositorio. |
| 2. Análisis exploratorio | Completada | Fase 1 y dataset disponible. |
| 3. Preprocesamiento | Completada | Hallazgos del EDA. |
| 4. Entrenamiento del MLP | Pendiente | Pipeline y particiones validados. |
| 5. Evaluación y calibración | Pendiente | Modelo candidato entrenado. |
| 6. Exportación del modelo | Pendiente | Modelo y evaluación aprobados. |
| 7. Motor financiero | Pendiente | Catálogo disponible y definiciones financieras aprobadas. |
| 8. Construcción de Streamlit | Pendiente | Contratos de inferencia y finanzas definidos. |
| 9. Integración | Pendiente | Componentes y artefactos disponibles. |
| 10. Pruebas finales | Pendiente | Sistema integrado. |
| 11. Informe ejecutivo | Pendiente | Resultados finales verificados. |

## 1. Documentación inicial

**Objetivo:** establecer una referencia técnica coherente antes de programar.

**Actividades:** inspeccionar el repositorio y los recursos; registrar el esquema real del dataset; definir arquitectura, ML, modelo financiero, aplicación, desarrollo y fases.

**Entregables:** `README.MD` y los siete documentos de `docs/`.

**Criterios de finalización:** documentos enlazados, estado actual diferenciado de la planificación, columnas reales verificadas, ausencia del catálogo registrada y alcance tecnológico consistente.

**Dependencias:** requisitos académicos y acceso al repositorio.

## 2. Análisis exploratorio

**Objetivo:** comprender calidad, distribuciones, desbalance y relaciones relevantes antes de transformar datos.

**Actividades:** validar dimensiones y tipos; analizar faltantes, duplicados y atípicos; estudiar `Exited`; explorar relaciones y sesgos; generar visualizaciones reproducibles; excluir las variables financieras simuladas del análisis predictivo y reservar su validación detallada para la fase financiera.

**Entregables:** [`notebooks/01_eda.ipynb`](../notebooks/01_eda.ipynb) ejecutado e [informe de resultados](eda-results.md), con gráficos, hallazgos y decisiones de tratamiento.

**Criterios de finalización:** cada control requerido está documentado, no hay supuestos silenciosos y las decisiones de preprocesamiento se apoyan en evidencia.

**Dependencias:** fase 1 y versión trazable de `data/Deep_Retention_Dataset.csv`.

## 3. Preprocesamiento

**Objetivo:** construir un pipeline sin fuga de información y reutilizable en inferencia.

**Actividades:** fijar semilla y partición estratificada; seleccionar nueve predictoras; escalar numéricas con entrenamiento; codificar `Geography`; conservar binarias; verificar categorías desconocidas, valores finitos y ausencia de solapamiento.

**Entregables:** [`notebooks/02_preprocesamiento.ipynb`](../notebooks/02_preprocesamiento.ipynb) ejecutado, pipeline de Scikit-learn en memoria, particiones reproducibles y comprobaciones de selección y transformación.

**Criterios de finalización:** transformadores ajustados solo con entrenamiento, objetivo y columnas excluidas ausentes de las entradas, misma transformación para lote e individuo.

**Dependencias:** decisiones del EDA.

## 4. Entrenamiento de la red neuronal

**Objetivo:** obtener un MLP candidato que estime probabilidades de abandono.

**Actividades:** implementar arquitectura inicial; configurar Adam y Binary Crossentropy; aplicar class weights, Dropout y Early Stopping; registrar experimentos y curvas; controlar sobreajuste.

**Entregables:** modelos candidatos, historiales de entrenamiento y configuración reproducible.

**Criterios de finalización:** entrenamiento reproducible, mejor época identificada con validación y ausencia de uso del conjunto de prueba para seleccionar el modelo.

**Dependencias:** fase 3 completada.

## 5. Evaluación y calibración

**Objetivo:** medir discriminación, calidad probabilística y limitaciones del candidato.

**Actividades:** calcular ROC-AUC, PR-AUC, Brier Score, matriz de confusión, precision, recall y F1; trazar calibración; decidir si calibrar; analizar factores influyentes con una técnica apropiada; revisar subgrupos.

**Entregables:** informe de evaluación con métricas reales, gráficos, decisión de calibración y análisis de explicabilidad.

**Criterios de finalización:** conjunto de prueba usado una vez para evaluación final, resultados reproducibles, probabilidades válidas y limitaciones documentadas.

**Dependencias:** fase 4 y protocolo de evaluación fijado.

## 6. Exportación del modelo

**Objetivo:** producir artefactos compatibles y listos para inferencia sin entrenamiento.

**Actividades:** guardar el MLP en `models/modelo_churn.keras`; guardar el pipeline en `models/preprocesador.joblib`; registrar versiones, esquema y huellas; probar recarga y paridad de predicciones.

**Entregables:** pareja de artefactos, metadatos de versión y prueba de carga.

**Criterios de finalización:** recarga exitosa en entorno bloqueado, misma salida dentro de tolerancia y archivos aptos para distribución según licencia/tamaño.

**Dependencias:** evaluación y calibración aprobadas.

## 7. Implementación del motor financiero

**Objetivo:** seleccionar intervenciones elegibles con la mayor GNE positiva.

**Actividades:** recibir e inspeccionar el catálogo; validar unidades y períodos; implementar GNE, rentabilidad y elegibilidad; tratar clientes deficitarios; agregar métricas; preparar simulaciones inmutables.

**Entregables:** módulo financiero, catálogo validado y pruebas unitarias de reglas y agregados.

**Criterios de finalización:** `GNE <= 0` siempre rechazada, clientes deficitarios no intervenidos, mejor alternativa seleccionada y resultados trazables.

**Dependencias:** catálogo real disponible, [definiciones financieras](financial-model.md) aprobadas y probabilidad consumible.

## 8. Construcción de Streamlit

**Objetivo:** ofrecer buscador, dashboard y simulador mediante una interfaz clara.

**Actividades:** implementar navegación; cargar recursos con caché; crear consulta por `CustomerId`; representar indicadores y gráficos; construir controles de simulación; manejar errores y estado de sesión.

**Entregables:** `app.py` y vistas funcionales conectadas a contratos simulados o componentes disponibles.

**Criterios de finalización:** tres secciones utilizables, datos simulados identificados, ningún entrenamiento al iniciar y simulaciones sin escritura en CSV.

**Dependencias:** arquitectura y contratos definidos; idealmente fases 6 y 7 disponibles para integración real.

## 9. Integración

**Objetivo:** conectar datos, artefactos, motor y presentación de extremo a extremo.

**Actividades:** organizar recursos finales; ejecutar inferencia individual y por lotes; conectar decisiones y agregados; verificar rutas relativas; comprobar consistencia entre vistas.

**Entregables:** aplicación integrada y configuración reproducible con `pyproject.toml`, `uv.lock` y `.python-version`.

**Criterios de finalización:** mismo cliente produce igual probabilidad en flujos individual y agregado, indicadores usan definiciones centrales y no hay descarga externa obligatoria al iniciar.

**Dependencias:** fases 6, 7 y 8.

## 10. Pruebas finales

**Objetivo:** verificar calidad funcional, reproducibilidad y facilidad de entrega.

**Actividades:** completar pruebas unitarias e integración; probar errores y límites; ejecutar en clon limpio; validar el comando único; revisar documentación, licencias y tamaño de artefactos.

**Entregables:** suite Pytest, registro de resultados, lista de aceptación y paquete listo para demostración.

**Criterios de finalización:** pruebas aprobadas, inicio mediante `uv run streamlit run app.py`, sin preparación manual adicional y sin defectos críticos conocidos.

**Dependencias:** sistema integrado y entorno bloqueado.

## 11. Elaboración del informe ejecutivo

**Objetivo:** comunicar resultados técnicos, económicos y operativos verificados.

**Actividades:** sintetizar impacto y retorno; presentar arquitectura y diagnóstico; construir matriz de decisión; describir operación en sucursales; formular conclusiones y próximos pasos.

**Entregables:** informe ejecutivo con:

1. resumen de impacto financiero y retorno;
2. arquitectura y diagnóstico de fuga;
3. matriz de decisión comercial y rentabilidad;
4. operación de la aplicación en sucursales;
5. conclusiones y próximos pasos.

**Criterios de finalización:** toda cifra se remonta a resultados reproducibles, se distinguen proyecciones y datos simulados, y no se inventan métricas ni resultados de campañas.

**Dependencias:** pruebas finales, métricas del modelo y resultados financieros verificados.

## Próximo paso

El EDA y el preprocesamiento están completados y pendientes de revisión del equipo. La fase 4, entrenamiento del MLP, permanecerá pendiente hasta recibir aprobación explícita de las particiones y del pipeline.
