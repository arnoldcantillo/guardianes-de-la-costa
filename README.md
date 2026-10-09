# Optimizador de enrutamiento costero

**Equipo:** Guardianes de la costera · Taller Scrum · Ingeniería de Sistemas

Herramienta para planificar la ruta más corta con la que una lancha recolecta residuos acuáticos acumulados en dársenas, muelles y desembocaduras.

> **Simulador en vivo:** https://arnoldcantillo.github.io/guardianes-de-la-costa/
> Ejecuta las 14 historias de usuario y sus 42 criterios de aceptación directamente en el navegador.

## El producto

**Problema.** Las autoridades portuarias y los operadores de canales fluviales recorren hoy las zonas de acumulación de residuos de manera empírica, sin una ruta planificada.

**Product Goal.** Que puedan planificar de forma automatizada y eficiente las rutas de navegación para la recolección de residuos acuáticos, reduciendo los tiempos operativos, los costos logísticos y el consumo de combustible en cada jornada de saneamiento.

**Usuarios.** Entidades de saneamiento ambiental, autoridades gubernamentales de gestión marina y cuadrillas de limpieza.

**Sprint Goal.** Al finalizar el Sprint, planificar de forma automatizada las rutas de navegación para la recolección de residuos, optimizando el tiempo y reduciendo el consumo de combustible.

## Scrum Team

| Rol | Integrante |
|---|---|
| Product Owner | Johan Viviescas |
| Scrum Master | Jaider Lozano |
| Developers | Arnold Cantillo, Jaider Lozano, Kemmell Cabana, Sebastián Murcia, Johan Viviescas |

## Product Backlog

El backlog está priorizado y estimado. Cada historia es un Issue de este repositorio, con sus criterios de aceptación y la Definition of Done.

| # | Historia | Prioridad | Puntos | Código |
|---|---|---|---|---|
| HU-01 | Asignar una ruta generada a una cuadrilla | Alta | 8 | `guardianes/hu01_asignar_cuadrilla.py` |
| HU-02 | Ingresar coordenadas y calcular la ruta más corta | Alta | 5 | `guardianes/hu02_coordenadas.py` |
| HU-03 | Panel de control mensual (combustible ahorrado y plástico retirado) | Media | 8 | `guardianes/hu03_panel.py` |
| HU-04 | Ahorro estimado frente al recorrido empírico | Media | 5 | `guardianes/hu04_ahorro.py` |
| HU-05 | Omitir un punto de recolección por clima | Media | 5 | `guardianes/hu05_omitir_punto.py` |
| HU-06 | Seleccionar tipo de embarcación y consumo | Media | 3 | `guardianes/hu06_embarcacion.py` |
| HU-07 | Registrar los kilogramos recolectados | Media | 3 | `guardianes/hu07_registro_kg.py` |
| HU-08 | Validar los datos de entrada | Media | 3 | `guardianes/hu08_validacion.py` |
| HU-09 | Alerta de combustible insuficiente | Media | 2 | `guardianes/hu09_alerta_combustible.py` |
| HU-10 | Etiquetar el tipo de residuo predominante | Baja | 8 | `guardianes/hu10_tipo_residuo.py` |
| HU-11 | Historial de rutas | Baja | 5 | `guardianes/hu11_historial.py` |
| HU-12 | Exportar un resumen en texto de la ruta | Baja | 3 | `guardianes/hu12_exportar.py` |
| HU-13 | Registro de auditoría de cambios manuales | Baja | 3 | `guardianes/hu13_auditoria.py` |
| HU-14 | Registrar múltiples muelles de salida | Baja | 2 | `guardianes/hu14_muelles.py` |

## Definition of Done

- Criterios de aceptación verificados.
- Revisión de código aprobada.
- Documentación necesaria actualizada.

## Simulador

La página `index.html` ejecuta el mismo código Python del repositorio dentro del navegador (con [Pyodide](https://pyodide.org)), sin servidor.

- **Datos de la jornada:** base y puntos de acumulación editables, con un mapa de la ruta óptima.
- **HU-01 a HU-14:** una pestaña por historia, con un botón por criterio de aceptación que muestra si **cumple** y el resultado (alertas, tablas, gráfico de barras, archivos descargables).
- **Resumen:** ejecuta los 42 criterios de una vez.

Necesita internet la primera vez, para descargar Pyodide. Para abrirla en local:

```
py -m http.server 8000
```

y entrar a http://localhost:8000.

## Cómo ejecutar el código

Requiere Python 3.10 o superior. No usa librerías externas.

```
py -m unittest discover -s tests -v    # pruebas de las 14 historias y sus 42 criterios
py main.py                             # demostración del flujo completo en consola
py simulador.py                        # versión de escritorio del simulador (Tkinter)
```

## Estructura del repositorio

```
index.html            Simulador web (GitHub Pages)
simulador.py          Simulador de escritorio (opcional)
main.py               Demostración en consola
guardianes/
  nucleo.py           Grafo de navegación, Dijkstra, algoritmo de ruta y modelos compartidos
  hu01_... a hu14_... Una historia de usuario por módulo
  escenarios.py       Un escenario ejecutable por cada criterio de aceptación
  web_api.py          Capa que conecta el código Python con la página web
tests/                Pruebas unitarias
```

## Cómo funciona la ruta

La base del cálculo de rutas es el **algoritmo de Dijkstra**. Los puntos de acumulación y la base forman un grafo no dirigido: cada nodo se conecta con sus 2 vecinos más cercanos y el peso de cada arista es la distancia Haversine (km); si quedan zonas aisladas, se unen por la arista más corta. Dijkstra calcula el camino mínimo entre cada par de nodos y esas distancias se usan para ordenar la visita (vecino más cercano, mejorado con 2-opt). La ruta siempre parte y termina en la base. En la página, el mapa dibuja el grafo y el camino de Dijkstra, y una tabla muestra por dónde pasa cada tramo. El ahorro se mide frente al recorrido en el orden en que se ingresaron los puntos (el recorrido empírico).

## Notas

- Los límites del área navegable (`LIMITES_NAVEGABLES` en `nucleo.py`) y las lanchas del catálogo (`BASE` en `hu06_embarcacion.py`) son valores de ejemplo y se ajustan a la jurisdicción y a la flota reales.
- Los archivos que genera el simulador de escritorio (PDF y texto) se guardan en la carpeta `salidas/`.
