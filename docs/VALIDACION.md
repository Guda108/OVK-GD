# Validación de OVK-GD

**Fecha:** 22 de noviembre de 2026

La entrega se comprobó en Linux con Python 3.12.14 y Git 2.56.1.

## Resultado

| Comprobación | Resultado |
|---|---|
| Suite `unittest` | 44 pruebas descubiertas: 43 correctas y 1 omitida por falta del formato de LaTeX. |
| Sintaxis y compatibilidad de Python | Verificadas para la sintaxis de Python 3.8. |
| Menú y ayuda de los comandos | Verificados. |
| Lanzador Bash | Sintaxis y ejecución de `--help` verificadas. |
| Lanzador Windows | Referencias y nombre revisados; ejecución pendiente en Windows. |
| Recursos visuales | Banner y tarjeta social revisados. |

## Historial y copias independientes

Las pruebas utilizan repositorios Git locales con ocho commits y dos autores:

- Se muestran los identificadores, autores, fechas y descripciones, incluyendo el actual y cinco o más anteriores.
- El submenú permite seleccionar un commit y elegir entre consultar su PDF, descargarlo o utilizar la copia como principal.
- La exportación utiliza las fuentes del commit elegido y conserva los archivos actuales, los archivos sin seguimiento, el índice y la rama.
- Una prueba del flujo de PDF usa un compilador simulado para comprobar las fuentes seleccionadas, el nombre del resultado y su ubicación fuera del proyecto.
- Una compilación simulada fallida conserva las fuentes exportadas y no cambia el proyecto activo.
- Los identificadores inválidos se rechazan sin modificar el proyecto.
- Un `fetch` real entre repositorios temporales incorpora nuevos commits remotos sin mezclar los archivos locales.
- Un clon con profundidad 1 recupera al menos cinco revisiones anteriores al ampliar el historial.

## Descarga y proyecto principal

- La descarga crea una copia Git independiente en el commit elegido, con todos los archivos versionados de esa revisión.
- Se conserva el proyecto de origen con archivos modificados, cambios preparados y archivos sin seguimiento.
- La copia continúa funcionando tras mover la carpeta del proyecto de origen.
- Se comprueba el rechazo de carpetas existentes, destinos dentro del origen e identificadores inválidos.
- El proyecto y archivo principal se guardan y vuelven a leerse desde disco; el compilador utiliza el `.tex` seleccionado aunque exista otro `main.tex`.
- Es posible volver a seleccionar el proyecto original mediante la opción 10.
- La sincronización de una copia publica su rama propia en un remoto local de prueba y conserva la rama `main` del origen.
- Se descarga un commit que llegó mediante `fetch` y que aún no pertenece al `HEAD` local.

## Apertura local y configuración del proyecto

- La opción 3 del menú abre la carpeta indicada sin clonar, sin crear una ubicación alternativa y sin pedir la URL.
- Un proyecto nuevo guarda la URL y su archivo principal en `OVK-GD.proyecto.json` y queda seleccionado para continuar al reabrir. También se comprueba la primera clonación en la carpeta elegida y la conexión de una carpeta existente sin clonarla.
- Se comprueba la reapertura desde otra carpeta de ejecución y mediante el archivo de datos del proyecto.
- La carpeta puede moverse y abrirse de nuevo sin perder la URL ni el archivo principal relativo. Las rutas del `.tex` guardadas con separadores de Windows también se pueden leer en otros sistemas.
- Se reutiliza la configuración Git existente; si falta el remoto, se reconstruye usando la URL guardada, sin operaciones de red.
- Una URL antigua del archivo de datos no reemplaza una conexión Git existente.
- Se comprueba la apertura de un `.tex` en una subcarpeta y el rechazo de rutas inexistentes o archivos de datos inválidos.
- Las credenciales HTTP incrustadas no se copian al archivo de datos del proyecto.

## Sincronización

Se comprobaron los casos de primera subida, clonación, mezcla de archivos distintos, conflictos, fallo de commit, remoto inaccesible y exclusión de archivos grandes. Los repositorios de prueba son temporales: no publican contenido ni requieren credenciales de GitHub.

## Compilación real y sistemas operativos

El entorno dispone de ejecutables TeX, pero no del formato `pdflatex.fmt`. Por ello se omitió la prueba que genera un PDF real con `latexmk` y `pdflatex` en una subcarpeta. Las pruebas del flujo histórico usan una dependencia de compilación simulada y no sustituyen esa comprobación real.

Quedan por comprobar en equipos de usuario:

- Generación real de PDF actual e histórico con una distribución LaTeX completa.
- Instaladores, visor PDF y VS Code en Windows, macOS y las distribuciones Linux contempladas.
- Autenticación y descarga del historial desde una cuenta real de GitHub/GitLab.

El flujo [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) está preparado para comprobar Python y Git en Windows, macOS y Linux después de publicarlo. No instala LaTeX: la prueba de compilación se omite cuando faltan sus herramientas o formatos.

## Repetir las comprobaciones

```bash
python -m py_compile OVK-GD.py
python -m unittest discover -s tests -v
python OVK-GD.py --help
```

En macOS/Linux puedes utilizar `python3` y comprobar el lanzador con `bash -n OVK-GD_mac_linux.command`.
