<p align="center">
  <img src="docs/assets/OVK-GD-banner.svg" alt="OVK-GD. Tu documento, tu equipo, tu computadora." width="100%">
</p>

<p align="center">
  <strong>Dr. Gerardo Diaz</strong><br>
  Compila LaTeX en tu computadora y trabaja en equipo con Git.<br>
  Windows · macOS · Linux · Python 3.8+ · Interfaz en español
</p>

<p align="center">
  <a href="#empezar">Empezar</a> ·
  <a href="MANUAL_OVK-GD.md">Manual completo</a> ·
  <a href="docs/PUBLICAR_EN_GITHUB.md">Publicar en GitHub</a> ·
  <a href="CONTRIBUTING.md">Contribuir</a>
</p>

---

## Escribe aquí. Comparte con tu equipo.

OVK-GD reúne la instalación de herramientas, la compilación de PDF y la sincronización de proyectos LaTeX en un menú de terminal. Está pensado para tesis, artículos, reportes y materiales de clase que se escriben entre varias personas.

La compilación se ejecuta localmente mediante `latexmk` y tu distribución de LaTeX. Puedes seguir escribiendo y compilando sin conexión una vez instalados los paquetes necesarios. Git conserva el historial; GitHub o GitLab permiten compartirlo.

> **Colaboración por sincronización.** Cada persona edita una copia local y después comparte sus cambios. La edición simultánea en tiempo real no está incluida. Repartir capítulos o secciones entre archivos facilita el trabajo.

## Qué puedes hacer

| Función | Para qué sirve |
|---|---|
| Instalar y actualizar | Preparar Git, LaTeX y, donde se automatiza, Visual Studio Code. |
| Configurar proyectos | Descargar un repositorio, crear un documento o registrar una carpeta existente. |
| Sincronizar | Guardar cambios en Git, incorporar los del equipo y subir los tuyos. |
| Compilar PDF | Ejecutar `latexmk` con `pdflatex` y mostrar el resultado. |
| Abrir en VS Code | Editar con LaTeX Workshop y compilar al guardar. |
| Sincronizar periódicamente | Repetir la sincronización mientras la aplicación permanece abierta. |
| Diagnosticar | Verificar las herramientas y la extensión de VS Code. |
| Consultar versiones y PDF | Ver commits con su autor y compilar versiones anteriores del documento sin cambiar el trabajo actual. |

El programa usa únicamente la biblioteca estándar de Python: **no necesitas ejecutar `pip install`**. LaTeX, Git y VS Code son aplicaciones externas.

## Empezar

### 1. Descarga y extrae

En la página de este repositorio, selecciona **Code → Download ZIP** y extrae todo su contenido. Conserva `OVK-GD.py` y los lanzadores en la misma carpeta.

Si ya usas Git, también puedes clonar el enlace que aparece en **Code**.

### 2. Abre el lanzador

| Sistema | Cómo abrir OVK-GD | Herramientas de compilación |
|---|---|---|
| Windows 10/11 | Doble clic en `OVK-GD_windows.bat`. | MiKTeX + Perl + latexmk. |
| macOS | En Terminal: `bash OVK-GD_mac_linux.command`. | BasicTeX + paquetes de TeX Live. |
| Ubuntu / Debian | En Terminal: `bash OVK-GD_mac_linux.command`. | TeX Live + latexmk. |
| Fedora | En Terminal: `bash OVK-GD_mac_linux.command`. | TeX Live + latexmk. |

Ejecuta los comandos desde la carpeta extraída. Se necesita **Python 3.8 o superior**. El lanzador de Windows ofrece instalar Python 3.12 si falta y encuentra `winget`. En macOS/Linux, instala Python previamente si no está disponible.

En macOS se requiere [Homebrew](https://brew.sh/) para la instalación automática. En Linux, VS Code se instala por separado. Consulta los detalles y las alternativas en el [manual](MANUAL_OVK-GD.md#2-instalar-en-tu-sistema).

### 3. Prepara tu entorno

Al abrir el menú por primera vez:

1. Elige **1 — Instalar herramientas**. Revisa los mensajes; algunas instalaciones requieren permisos de administrador.
2. Cierra y vuelve a abrir el lanzador.
3. Elige **8 — Diagnóstico** para comprobar qué herramientas están disponibles.
4. Elige **3 — Configurar un proyecto** para descargar, crear o registrar tu documento.

La descarga de herramientas y paquetes requiere internet y puede ocupar varios GB. La duración depende del equipo y de los paquetes seleccionados.

## Tu rutina de trabajo

1. **Antes de escribir:** opción **4**, sincronizar.
2. **Para editar:** opción **6**, abrir el proyecto en VS Code.
3. **Para generar el PDF:** guarda en VS Code o usa la opción **5**.
4. **Al terminar:** opción **4**, sincronizar y describir los cambios.

Al sincronizar, OVK-GD guarda los cambios locales, incorpora los del remoto mediante una mezcla de Git y después intenta subir el resultado. Si falta conexión, puedes conservar commits locales para enviarlos después. Si aparece un conflicto, consulta el [procedimiento del manual](MANUAL_OVK-GD.md#6-resolver-conflictos).

## Versiones anteriores: elige un commit y genera su PDF

La opción **9 — Historial: versiones anteriores y compilar su PDF** abre un submenú del proyecto seleccionado.

- Muestra inicialmente hasta **10 commits**, con identificador, descripción, autor y fecha. Incluye al menos cinco versiones anteriores si hay seis o más commits disponibles.
- Escribe el **número del commit** para compilar esa versión en una carpeta independiente.
- Usa **M** para mostrar diez commits más, **R** para consultar la rama remota tras descargar su historial y **L** para volver al historial local.
- El PDF se conserva con el identificador del commit en el nombre, junto con sus fuentes y un archivo `version.json`.

Tus archivos actuales, los cambios sin commit, la rama y el índice de Git se conservan. La actualización del historial usa `git fetch`; la compilación histórica exporta el commit sin cambiar la revisión activa.

Los resultados se guardan normalmente en `~/.ovk-gd/versiones/`. La aplicación muestra la ubicación exacta y abre el PDF cuando la compilación termina correctamente. Consulta el [manual del historial](MANUAL_OVK-GD.md#11-versiones-anteriores-y-pdf) para los requisitos y detalles.

## Un documento, varios archivos

El ejemplo incluido separa la introducción y la metodología para que dos personas puedan trabajar en archivos diferentes:

| Archivo | Contenido |
|---|---|
| `ejemplos/documento/main.tex` | Estructura general y llamadas a las secciones. |
| `ejemplos/documento/secciones/introduccion.tex` | Contexto y objetivo del documento. |
| `ejemplos/documento/secciones/metodologia.tex` | Desarrollo y ecuación de ejemplo. |

Copia **el contenido de `ejemplos/documento/` a una carpeta nueva**, fuera de este repositorio, y regístrala con la opción 3. Así mantienes separados el código de OVK-GD y los documentos de tu equipo.

## Uso desde terminal

```bash
python OVK-GD.py --help
python OVK-GD.py instalar
python OVK-GD.py diagnostico
python OVK-GD.py proyecto
python OVK-GD.py sincronizar -m "Actualiza la introducción"
python OVK-GD.py compilar
python OVK-GD.py historial
python OVK-GD.py historial --cantidad 20 --actualizar
python OVK-GD.py compilar-version IDENTIFICADOR_DEL_COMMIT
python OVK-GD.py auto
python OVK-GD.py --simular instalar
```

En macOS/Linux, usa `python3` si `python` no corresponde a Python 3. En Windows también puedes usar `py -3`.

`--simular` permite inspeccionar la instalación o actualización sin ejecutarla. Se escribe **antes** del subcomando. Los comandos de proyecto, compilación y sincronización usan los proyectos registrados por la opción 3.

## Qué incluye este repositorio

| Ruta | Descripción |
|---|---|
| [`OVK-GD.py`](OVK-GD.py) | Programa y menú de terminal. |
| [`MANUAL_OVK-GD.md`](MANUAL_OVK-GD.md) | Instalación, uso, autenticación y solución de problemas. |
| [`docs/PUBLICAR_EN_GITHUB.md`](docs/PUBLICAR_EN_GITHUB.md) | Cómo cargar y presentar este proyecto en tu cuenta. |
| [`ejemplos/documento/`](ejemplos/documento/) | Documento breve dividido en secciones. |
| [`tests/`](tests/) | Pruebas de sincronización y compilación. |
| [`.github/`](.github/) | Comprobaciones automáticas y plantillas de colaboración. |

## Alcance y estado

- La interfaz es un menú de terminal en español.
- El comando de compilación utiliza `pdflatex`; otros motores se configuran por separado en el editor o mediante herramientas LaTeX.
- La compilación local depende de la memoria, el disco y los paquetes de tu equipo.
- Los instaladores automatizan comandos de los gestores de cada sistema. Su disponibilidad depende del entorno.
- El proyecto incluye un flujo de GitHub Actions para comprobar Python y Git en Windows, macOS y Linux. Los resultados aparecen después de publicar y ejecutar el flujo; esto no valida los instaladores completos.

La validación realizada para esta entrega se describe en [`docs/VALIDACION.md`](docs/VALIDACION.md).

## Contribuir y licencia

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) para proponer mejoras o reportar un problema. Usa la pestaña **Issues** del repositorio donde se publique el proyecto.

**Licencia pendiente de elección por el titular.** Este paquete no añade una licencia de redistribución. La guía de publicación explica dónde agregarla cuando se decida.
