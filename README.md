# Optimizador de enrutamiento costero - Guardianes de la costera

Código en Python (sin dependencias externas) de las historias HU-01 a HU-14.

| Historia | Módulo |
|---|---|
| HU-01 Asignar ruta a cuadrilla | `guardianes/hu01_asignar_cuadrilla.py` |
| HU-02 Ingresar coordenadas y calcular ruta | `guardianes/hu02_coordenadas.py` |
| HU-03 Panel de control y PDF | `guardianes/hu03_panel.py` |
| HU-04 Ahorro frente al recorrido empírico | `guardianes/hu04_ahorro.py` |
| HU-05 Omitir punto por clima | `guardianes/hu05_omitir_punto.py` |
| HU-06 Tipo de embarcación y consumo | `guardianes/hu06_embarcacion.py` |
| HU-07 Registro de kg | `guardianes/hu07_registro_kg.py` |
| HU-08 Validación de datos de entrada | `guardianes/hu08_validacion.py` |
| HU-09 Alerta de combustible | `guardianes/hu09_alerta_combustible.py` |
| HU-10 Tipo de residuo | `guardianes/hu10_tipo_residuo.py` |
| HU-11 Historial de rutas | `guardianes/hu11_historial.py` |
| HU-12 Exportar resumen en texto | `guardianes/hu12_exportar.py` |
| HU-13 Registro de auditoría | `guardianes/hu13_auditoria.py` |
| HU-14 Múltiples muelles | `guardianes/hu14_muelles.py` |

El núcleo compartido (distancias, algoritmo de ruta, modelos) está en `guardianes/nucleo.py`.

## Uso

```
py simulador.py     # ventana con las 14 historias y sus 42 criterios
python main.py
python -m unittest discover -s tests -v
```

Los límites navegables (`LIMITES_NAVEGABLES`) y las lanchas del catálogo (`BASE` en `hu06_embarcacion.py`) son valores de ejemplo.

`simulador.py` abre una ventana (Tkinter, incluido con Python) con una pestaña por historia. Cada criterio de aceptación tiene un botón que lo ejecuta y muestra si cumple. La pestaña «Escenario» permite cambiar la base y los puntos, y «Resumen» ejecuta los 42 criterios de una vez. Los escenarios están en `guardianes/escenarios.py`. Los archivos que genera (PDF, texto) quedan en la carpeta `salidas/`.

## Simulador en la web (GitHub Pages)

`index.html` es una página que ejecuta este mismo código Python dentro del navegador (con Pyodide), sin servidor. Tiene una pestaña por historia, un escenario editable con mapa, y un resumen que ejecuta los 42 criterios. Para verla en local:

```
py -m http.server 8000
```

y abrir http://localhost:8000. En GitHub se publica activando Pages (Settings > Pages > rama `main`, carpeta `/ (root)`). La página necesita internet para descargar Pyodide la primera vez.
