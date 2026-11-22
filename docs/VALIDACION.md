# Validación de OVK-GD

**Fecha:** 21 de noviembre de 2026

La entrega se comprobó en Linux con Python 3.12.14 y Git 2.56.1.

## Resultado

| Comprobación | Resultado |
|---|---|
| Suite `unittest` | 19 pruebas descubiertas: 18 correctas y 1 omitida por falta del formato de LaTeX. |
| Sintaxis y compatibilidad de Python | Verificadas para la sintaxis de Python 3.8. |
| Menú y ayuda de los comandos | Verificados. |
| Lanzador Bash | Sintaxis y ejecución de `--help` verificadas. |
| Lanzador Windows | Referencias y nombre revisados; ejecución pendiente en Windows. |
| Recursos visuales | Banner y tarjeta social revisados. |

## Historial y copias independientes

Las pruebas utilizan repositorios Git locales con ocho commits y dos autores:

- Se muestran los identificadores, autores, fechas y descripciones, incluyendo el actual y cinco o más anteriores.
- El submenú permite seleccionar un commit y regresar al menú.
- La exportación utiliza las fuentes del commit elegido y conserva los archivos actuales, los archivos sin seguimiento, el índice y la rama.
- Una prueba del flujo de PDF usa un compilador simulado para comprobar las fuentes seleccionadas, el nombre del resultado y su ubicación fuera del proyecto.
- Una compilación simulada fallida conserva las fuentes exportadas y no cambia el proyecto activo.
- Los identificadores inválidos se rechazan sin modificar el proyecto.
- Un `fetch` real entre repositorios temporales incorpora nuevos commits remotos sin mezclar los archivos locales.
- Un clon con profundidad 1 recupera al menos cinco revisiones anteriores al ampliar el historial.

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
