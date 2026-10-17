# Guía de desarrollo

[Volver al README](../README.MD) · [Arquitectura](architecture.md) · [Aprendizaje automático](machine-learning.md) · [Aplicación](application.md) · [Hoja de ruta](roadmap.md)

## Estado

Esta guía establece las reglas para la implementación futura. El EDA, el preprocesamiento y el primer entrenamiento disponen de un entorno bloqueado con Python 3.11, Jupyter, Pandas, NumPy, Matplotlib, Scikit-learn y TensorFlow/Keras. Todavía no hay código de aplicación, pruebas automatizadas ni artefactos exportados; Streamlit se añadirá en su fase correspondiente.

## Principios

1. Mantener una solución monolítica y fácil de ejecutar.
2. Separar interfaz, preparación de datos, predicción, finanzas y analítica.
3. Hacer explícitas las entradas, salidas, unidades y supuestos.
4. Evitar duplicar transformaciones o fórmulas.
5. Favorecer funciones pequeñas, deterministas y comprobables.
6. No introducir bases de datos, contenedores, servicios ni patrones fuera del alcance.
7. Distinguir datos reales del conjunto base, variables simuladas, predicciones y proyecciones.

## Organización del código

| Archivo previsto | Contenido permitido | Contenido que debe evitarse |
|---|---|---|
| `app.py` | Controles y presentación de Streamlit; coordinación de casos de uso. | Entrenamiento, transformaciones manuales o fórmulas financieras duplicadas. |
| `src/data_processing.py` | Lectura de CSV, validación de esquema, selección de columnas. | Widgets o dependencias de presentación. |
| `src/prediction.py` | Carga de artefactos, transformación e inferencia. | Reglas de incentivos o entrenamiento. |
| `src/financial.py` | GNE, elegibilidad, comparación y decisión. | Código de Streamlit o acceso al modelo neuronal. |
| `src/analytics.py` | Agregaciones y datos para gráficos/KPI. | Mutación de archivos fuente. |
| `training/train.py` | División, ajuste del preprocesador y entrenamiento. | Inicio de Streamlit. |
| `training/evaluate.py` | Evaluación, calibración y explicabilidad. | Reglas de interfaz. |

La separación es funcional, no una invitación a crear capas, interfaces o abstracciones ceremoniales.

## Convenciones de Python

- Seguir PEP 8 y utilizar nombres descriptivos en inglés para módulos, funciones, variables y columnas ya establecidas.
- Escribir docstrings breves en funciones públicas cuando el contrato no resulte obvio.
- Usar type hints en parámetros y retornos, especialmente en cálculos financieros y carga de artefactos.
- Preferir `pathlib.Path` para construir rutas relativas a la raíz del proyecto.
- Evitar estado global mutable.
- Usar constantes con nombre para columnas, rutas y parámetros base; no dispersar cadenas o números mágicos.
- Validar datos en los límites del sistema y lanzar errores específicos con contexto útil.
- Mantener cálculos internos con precisión suficiente; redondear solo al presentar.
- No capturar excepciones genéricas salvo en el límite de interfaz, donde deberán registrarse y convertirse en mensajes seguros.

## Diseño de funciones

Las funciones reutilizables deberán:

- recibir dependencias y datos de forma explícita;
- retornar resultados sin escribir archivos de manera implícita;
- no mezclar validación, cálculo y visualización cuando puedan probarse por separado;
- preservar los DataFrames originales o documentar con claridad cualquier copia;
- devolver estructuras con nombres inequívocos y unidades consistentes;
- ser deterministas dadas las mismas entradas, salvo operaciones de ML con aleatoriedad controlada.

Ejemplos de contratos a implementar posteriormente incluyen leer y validar clientes, preparar las nueve características, predecir probabilidades por lote, calcular una GNE, seleccionar una intervención y agregar indicadores.

## Gestión de dependencias con uv

Los archivos disponibles son:

- `pyproject.toml`: metadatos, Python 3.11 y dependencias directas del EDA, el preprocesamiento y el entrenamiento inicial;
- `uv.lock`: resolución exacta y reproducible;
- `.python-version`: versión de Python elegida para el proyecto.

Proceso para ampliar el entorno en fases futuras:

1. comprobar matrices de compatibilidad oficiales;
2. elegir una versión de Python soportada por TensorFlow y las demás bibliotecas;
3. añadir solo dependencias directas necesarias;
4. regenerar y versionar `uv.lock`;
5. probar la instalación en un clon limpio;
6. registrar cambios de dependencias en el historial del proyecto.

No se utilizarán rangos abiertos sin justificación para dependencias sensibles al formato de los artefactos. Actualizar una dependencia que serializa o carga modelos exige volver a verificar los artefactos.

Comandos disponibles o previstos según la fase:

```bash
uv sync --locked
uv run python training/train.py
uv run python training/evaluate.py
uv run pytest
uv run streamlit run app.py
```

El profesor solo necesitará el último comando para la demostración; entrenamiento y evaluación forman parte del mantenimiento del proyecto.

## Datos y rutas

- Los CSV y artefactos necesarios para la demostración deberán estar dentro del repositorio si licencia y tamaño lo permiten.
- Las rutas se resolverán desde la raíz, no desde el directorio de trabajo accidental del usuario.
- La aplicación leerá datos y artefactos; las simulaciones no los modificarán.
- El esquema esperado se validará antes de inferir.
- Nunca se registrarán filas completas con datos personales en mensajes de error.
- La procedencia, licencia y huella del dataset utilizado para entrenar deberán conservarse.

## Pruebas con Pytest

No se implementan pruebas en esta fase. La estrategia prevista incluye pruebas unitarias para lógica pura y pruebas de integración para los límites entre módulos.

### Matriz mínima

| Área | Comprobaciones |
|---|---|
| Lectura | El CSV se carga con el número y nombres de columnas esperados; errores claros ante ausencia o esquema inválido. |
| Clientes | `CustomerId` identifica una sola fila; IDs ausentes o duplicados se manejan explícitamente. |
| Características | Se seleccionan exactamente las nueve predictoras, en orden consistente. |
| Fuga de datos | `Exited`, identificadores, `Gender`, `Surname` y columnas `_Sim` no entran al modelo. |
| Preprocesamiento | El objeto se ajusta solo con entrenamiento y transforma de forma consistente datos individuales y lotes. |
| Artefactos | Modelo y preprocesador exportados se cargan y son compatibles con el esquema. |
| Predicción | Salida finita dentro de `[0, 1]`; misma fila produce resultado coherente individual y por lote. |
| GNE | Fórmula, unidades, límites y casos de margen negativo son correctos. |
| Incentivos | Se rechazan alternativas con `GNE <= 0` y se selecciona la mayor GNE positiva elegible. |
| Agregados | Inversión, valor rescatable, GNE total y ROI siguen sus definiciones. |
| Simulación | Los cambios son temporales y no alteran archivos ni DataFrames base. |
| Aplicación | Streamlit inicia con los recursos distribuidos y muestra errores controlados cuando falta alguno. |

### Pruebas unitarias

Se centrarán en validadores, selección de características, fórmulas financieras, elegibilidad, desempates y agregaciones. Utilizarán datos mínimos creados para la prueba, sin depender del dataset completo cuando no sea necesario.

### Pruebas de integración

Cubrirán:

- CSV → validación → preprocesador → modelo → probabilidad;
- probabilidad + cliente + catálogo → recomendación;
- predicciones por lote → métricas del dashboard;
- carga de los artefactos reales distribuidos;
- inicio básico de la aplicación en un entorno creado desde `uv.lock`.

Los resultados del conjunto de prueba del modelo no deben convertirse en asserts frágiles de igualdad exacta; se validarán contratos y tolerancias justificadas.

## Manejo de errores

Los módulos internos deberán producir excepciones con contexto técnico y la interfaz transformarlas en mensajes comprensibles. Como mínimo se distinguirán:

- recurso ausente o sin permisos;
- CSV mal formado;
- columnas faltantes, adicionales críticas o tipos inválidos;
- identificador inexistente o duplicado;
- categoría desconocida no soportada;
- artefactos incompatibles;
- predicción inválida;
- costo, efectividad o margen fuera de dominio;
- división de ROI con inversión cero.

No se sustituirán silenciosamente valores inválidos ni se continuará con resultados parciales como si fueran válidos.

## Reproducibilidad

Cada entrenamiento candidato deberá registrar:

- commit o versión del código;
- huella y procedencia del dataset;
- lista de características;
- semilla y estrategia de partición;
- parámetros del preprocesamiento;
- arquitectura e hiperparámetros;
- versiones del entorno bloqueado;
- métricas de validación y prueba;
- decisión y método de calibración;
- fecha y criterio de selección del modelo.

El modelo y el preprocesador forman una pareja indivisible. No se reemplazará uno sin volver a comprobar el otro.

## Versionado y actualización del modelo

Procedimiento previsto:

1. incorporar y validar el nuevo dataset sin sobrescribir evidencia del anterior;
2. ejecutar el EDA y comparar cambios de esquema y distribución;
3. decidir si la definición del objetivo o las características cambió;
4. crear particiones reproducibles y ajustar un preprocesador nuevo solo con entrenamiento;
5. entrenar, evaluar, calibrar si corresponde y analizar explicabilidad;
6. comparar con el modelo vigente mediante criterios registrados;
7. exportar juntos el nuevo `.keras` y `.joblib`;
8. ejecutar todas las pruebas e iniciar Streamlit con los nuevos artefactos;
9. actualizar documentación, métricas y metadatos;
10. reemplazar la versión distribuida solo después de aprobar los criterios.

Si el tamaño de los artefactos excede los límites de GitHub, se deberá definir un mecanismo de distribución reproducible antes de la entrega; la aplicación no debe depender de una descarga improvisada al iniciar.

## Buenas prácticas de Git

- Crear cambios pequeños y coherentes por fase.
- Usar ramas con nombres descriptivos y commits que expliquen la intención.
- No versionar cachés, entornos virtuales, secretos, resultados temporales ni datos sin permiso de distribución.
- Revisar `git status` y el diff antes de cada commit.
- No mezclar cambios de documentación, datos y modelo sin una razón trazable.
- No reescribir artefactos grandes innecesariamente.
- Integrar cambios solo cuando pruebas y documentación estén actualizadas.
- Mantener `main` utilizable y seguir el flujo de ramas acordado por el equipo.

## Ejecución de la aplicación

Una entrega válida deberá funcionar desde un clon limpio con `uv` instalado:

```bash
uv run streamlit run app.py
```

La verificación de entrega comprobará que no sea necesario entrenar, descargar datos manualmente, configurar variables de entorno, instalar una base de datos ni ejecutar otros comandos para abrir la demostración.
