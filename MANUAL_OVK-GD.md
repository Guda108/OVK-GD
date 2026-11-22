# Manual de OVK-GD

**Dr. Gerardo Diaz · Interfaz en español · Windows, macOS y Linux**

[Volver a la presentación](README.md) · [Publicar la herramienta en GitHub](docs/PUBLICAR_EN_GITHUB.md)

## Contenido

1. [Qué necesitas](#1-qué-necesitas)
2. [Instalar en tu sistema](#2-instalar-en-tu-sistema)
3. [Preparar GitHub y el acceso](#3-preparar-github-y-el-acceso)
4. [Configurar un documento](#4-configurar-un-documento)
5. [Escribir, compilar y sincronizar](#5-escribir-compilar-y-sincronizar)
6. [Resolver conflictos](#6-resolver-conflictos)
7. [Actualizar y respaldar](#7-actualizar-y-respaldar)
8. [Problemas frecuentes](#8-problemas-frecuentes)
9. [Instalación manual](#9-instalación-manual)
10. [Referencia de comandos](#10-referencia-de-comandos)
11. [Versiones anteriores y PDF](#11-versiones-anteriores-y-pdf)

## 1. Qué necesitas

OVK-GD compila documentos en tu computadora y comparte sus archivos mediante Git. Cada persona conserva una copia local. La colaboración se realiza al sincronizar; no hay edición compartida en tiempo real.

| Requisito | Detalle |
|---|---|
| Python | 3.8 o superior para ejecutar el programa. |
| Git | Para guardar historial y sincronizar. |
| LaTeX | MiKTeX en Windows o TeX Live/BasicTeX en macOS/Linux. |
| latexmk | Organiza las pasadas de compilación y bibliografía. Necesita Perl. |
| VS Code + LaTeX Workshop | Recomendados para editar y visualizar el PDF. |
| Internet | Necesario para instalar, descargar paquetes y sincronizar con GitHub. |
| Disco | Reserva varios GB; el tamaño cambia según la distribución y sus paquetes. |
| Cuenta de GitHub o GitLab | Necesaria para escribir en un repositorio remoto del equipo. |

No hay dependencias de Python que instalar con `pip`. Python puede no estar instalado de fábrica, incluso en macOS y Linux.

**Dos repositorios distintos:** uno contiene la herramienta OVK-GD; cada tesis, artículo o reporte debe tener su propio repositorio de documentos. Descargar OVK-GD no crea automáticamente el repositorio de una tesis.

## 2. Instalar en tu sistema

Descarga el ZIP y **extrae todos sus archivos**. No ejecutes el lanzador desde la vista interna del ZIP.

### Windows

1. Abre `OVK-GD_windows.bat` con doble clic.
2. Si falta Python y está disponible `winget`, el lanzador ofrece instalar Python 3.12. Después, cierra y vuelve a abrir el lanzador.
3. En el menú, elige **1 — Instalar herramientas**. Se intenta instalar Git, MiKTeX, Strawberry Perl y VS Code mediante `winget`.
4. Atiende los avisos de instalación y revisa si algún comando falla.
5. Cierra la ventana, abre el lanzador de nuevo y elige **8 — Diagnóstico**.

La instalación configura MiKTeX para descargar los paquetes que falten cuando esa utilidad está disponible. Las primeras compilaciones pueden necesitar internet.

Si no existe `winget`, instala las herramientas desde sus sitios oficiales siguiendo la [sección 9](#9-instalación-manual). Si Python abre Microsoft Store o no inicia, usa el instalador oficial y activa la opción para añadir Python al `PATH`.

### macOS

1. Instala Python 3 si hace falta desde [python.org](https://www.python.org/downloads/macos/).
2. Instala [Homebrew](https://brew.sh/) siguiendo las instrucciones de su sitio.
3. Abre Terminal en la carpeta de OVK-GD y ejecuta:

   ```bash
   bash OVK-GD_mac_linux.command
   ```

4. Elige **1**. Se instalan Git, BasicTeX y VS Code si Homebrew no los registra como instalados. `tlmgr` instala las colecciones LaTeX necesarias, `latexmk` y `biber`.
5. Cuando aparezca `sudo`, escribe tu contraseña de macOS. Es normal que no se vean caracteres al teclearla.
6. Cierra y abre Terminal y ejecuta el diagnóstico.

Para abrir con doble clic desde Finder, primero ejecuta:

```bash
chmod +x OVK-GD_mac_linux.command
```

Si macOS solicita una autorización al abrirlo, revisa el aviso del sistema. También puedes usar directamente el comando `bash` anterior.

Si ya tienes MacTeX u otra instalación de LaTeX funcional, revisa el diagnóstico antes de ejecutar la instalación automática: esta versión busca BasicTeX por su registro en Homebrew y puede intentar instalarlo aunque ya exista otra distribución.

### Ubuntu / Debian / Fedora

Abre Terminal en la carpeta extraída y ejecuta:

```bash
bash OVK-GD_mac_linux.command
```

Elige **1**. OVK-GD usa `apt-get` o `dnf` para instalar Git y herramientas de TeX Live. Puede solicitar la contraseña de `sudo`.

Instala [Visual Studio Code](https://code.visualstudio.com/download) por separado. Después repite la opción **1** para instalar LaTeX Workshop si el comando `code` ya está disponible.

En otras distribuciones, instala manualmente Git, TeX Live, `latexmk`, Perl y, si lo necesitas, `biber`.

### Revisar el diagnóstico

La opción **8** busca las herramientas por su nombre y muestra información de versión. Comprueba los mensajes; que una ruta exista no garantiza que todos los paquetes de tu documento estén instalados. Si acabas de instalar algo, reinicia la terminal antes de repetir.

## 3. Preparar GitHub y el acceso

Una persona crea el repositorio del documento y agrega al resto del equipo.

1. Entra a [github.com/new](https://github.com/new).
2. Escribe un nombre, por ejemplo `tesis-redes-memristivas`.
3. Elige **Private** si el documento solo debe estar disponible para el equipo.
4. Para conectar una carpeta existente, crea el repositorio vacío: no agregues README, `.gitignore` ni licencia desde esa pantalla.
5. En **Settings**, busca **Collaborators** o **Collaborators and teams**, agrega a las personas y espera a que acepten la invitación.
6. Copia el enlace HTTPS desde **Code**.

### Iniciar sesión para sincronizar

La cuenta con la que navegas por GitHub y las credenciales que usa Git en tu computadora se configuran por separado.

- **Windows:** Git for Windows incluye Git Credential Manager. Cuando solicite autenticar una operación, normalmente abre el navegador para iniciar sesión.
- **macOS/Linux:** puedes instalar [GitHub CLI](https://cli.github.com/) y ejecutar `gh auth login`. Elige GitHub.com, HTTPS y acepta autenticar Git. Otra alternativa es Git Credential Manager.
- **Token:** si Git solicita una contraseña en la terminal, utiliza un personal access token autorizado para ese repositorio. La contraseña normal de GitHub no sirve para operaciones Git por HTTPS. Sigue las [instrucciones oficiales](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens); cuando sea posible, limita el acceso a los repositorios necesarios.

OVK-GD no instala GitHub CLI ni crea tokens. Si no detecta un gestor de credenciales, puede configurar el llavero de macOS o una caché de Git de ocho horas en Linux. Respeta un gestor existente.

La primera configuración pide tu nombre y correo si Git aún no los tiene. Estos datos identifican los commits y se guardan en la configuración global de Git. Puedes usar el correo privado `noreply` que GitHub muestra en **Settings → Emails**.

## 4. Configurar un documento

Elige **3 — Configurar un proyecto**.

| Opción | Cuándo usarla | Resultado |
|---|---|---|
| 1. Descargar | El equipo ya tiene un repositorio. | Clona sus archivos en tu computadora. |
| 2. Crear | Comienzas un documento nuevo. | Crea un repositorio local y un `main.tex` de ejemplo. |
| 3. Usar una carpeta | Ya tienes archivos, por ejemplo un ZIP de Overleaf extraído. | Registra la carpeta y crea Git si falta. |

La ubicación propuesta es `Proyectos_OVK-GD` dentro de tu carpeta de usuario. Puedes elegir otra. El registro de proyectos se guarda en `~/.ovk-gd/proyectos.json`.


Para compartir un documento nuevo, pega el enlace del repositorio vacío cuando se solicite y acepta sincronizar. Los demás integrantes usan la opción **1 — Descargar**. Crear un proyecto local no crea por sí mismo el repositorio en GitHub.

Si no existen, OVK-GD añade:

| Archivo | Función |
|---|---|
| `.gitignore` | Omite temporales LaTeX y los PDF de la raíz del documento. |
| `.gitattributes` | Normaliza texto e identifica algunos formatos binarios. |
| `.vscode/settings.json` | Configura LaTeX Workshop para compilar al guardar. |

Los archivos de configuración existentes se conservan: no se combinan ni se reemplazan automáticamente. Para un ejemplo dividido en capítulos, copia el contenido de [`ejemplos/documento/`](ejemplos/documento/) a una nueva carpeta y regístrala.

## 5. Escribir, compilar y sincronizar

### Rutina recomendada

1. Al iniciar, elige **4 — Sincronizar**.
2. Elige **6 — Abrir en VS Code** y edita tu sección.
3. Guarda con `Ctrl+S` o `Cmd+S`. Con LaTeX Workshop configurado, se solicita la compilación al guardar. Si no se abre la vista PDF, utiliza **LaTeX Workshop: View LaTeX PDF file** desde la paleta de comandos de VS Code.
4. Al terminar, vuelve a **4 — Sincronizar** e indica una descripción breve de tus cambios.

### Qué hace sincronizar

Primero prepara los cambios de toda la carpeta y crea un commit si hace falta. Después consulta la rama remota, descarga y mezcla los cambios del equipo, y finalmente intenta subir el resultado.

Se incluyen los archivos nuevos, modificados y eliminados que Git no ignore. Revisa el contenido de la carpeta antes de sincronizar. Los commits registran los cambios, pero un commit local todavía no es una copia en GitHub.

Si no hay remoto, los cambios quedan solo en tu equipo. Si falla la conexión, reintenta cuando vuelva internet. Si falla el guardado local, esta versión detiene la sincronización antes de descargar o subir.

Los archivos de más de 90 MiB se excluyen del commit como margen preventivo para el límite de GitHub. Reduce su tamaño o muévelos fuera del documento; no basta con intentar subirlos de nuevo.

### Compilar desde el menú

La opción **5** busca archivos `.tex` que contengan `\documentclass`. Prefiere uno llamado `main.tex`; si hay varias alternativas sin ese nombre, permite elegir.

Ejecuta `latexmk -cd -pdf` con mensajes de error por archivo y línea. La opción `-cd` permite compilar el principal en su propia subcarpeta y resolver sus entradas relativas. El PDF se genera normalmente junto al archivo principal y se intenta abrir con el visor del sistema.

El comando incluido utiliza `pdflatex`. Si tu documento requiere XeLaTeX o LuaLaTeX, utiliza una receta adecuada en tu editor o compila externamente. Una configuración `.latexmkrc` propia puede cambiar rutas o comportamiento; el programa espera encontrar el PDF junto al principal.

### Sincronización periódica

La opción **7** pregunta el intervalo en minutos. Funciona mientras esa terminal siga abierta y se detiene con `Ctrl+C`. No instala un servicio ni se ejecuta al encender el equipo.

Haz primero una sincronización manual para comprobar las credenciales. El modo automático evita preguntas de Git en la terminal; un gestor de credenciales externo podría mostrar sus propios avisos. Si aparece un conflicto, intenta abortar la mezcla y requiere atención manual.

## 6. Resolver conflictos

Un conflicto aparece cuando Git no puede combinar cambios, por ejemplo cuando dos personas modifican las mismas líneas.

En la sincronización manual, OVK-GD permite elegir **tu versión**, **la otra versión** o **cancelar**. La selección conserva **el archivo completo** de uno de los lados, no solo las líneas en conflicto. Revisa con tu compañero antes de elegir si ambos hicieron cambios importantes.

En conflictos que incluyen eliminaciones u otros casos que Git no pueda resolver mediante esa selección, el programa informa el fallo e intenta cancelar la mezcla. Puedes revisar el repositorio con `git status` y resolverlo con un editor o pedir apoyo.

Los cambios que llegaron a guardarse como commits permanecen en el historial correspondiente. Esto no sustituye una copia de respaldo de archivos sin guardar o ignorados por Git.

Para reducir conflictos:

- Divide el documento con `\input{secciones/introduccion}` y reparte los archivos.
- Sincroniza antes de editar y después de terminar un bloque.
- Coordina los cambios del archivo principal y la bibliografía.
- Antes de reestructurar muchos archivos, avisa al equipo y sincroniza.

## 7. Actualizar y respaldar

La opción **2** intenta actualizar las herramientas mediante el gestor del sistema. En macOS ejecuta también `brew upgrade`, que puede actualizar otros paquetes administrados por Homebrew; en Linux esta versión vuelve a instalar o actualiza los paquetes enumerados de LaTeX y Git. Revisa primero los comandos con `--simular actualizar`.

Para actualizar OVK-GD, descarga una versión nueva y reemplaza sus archivos de programa. No necesitas copiar encima tus documentos: viven en carpetas independientes. Conserva el registro `~/.ovk-gd/proyectos.json` o vuelve a registrar las carpetas existentes.

Los PDF de la raíz se omiten **solo si el proyecto usa el `.gitignore` generado y todavía no estaban registrados en Git**. Para compartir una entrega puedes copiar el PDF a `entrega/`. No es necesario versionar cada compilación.

## 8. Problemas frecuentes

| Problema | Acción |
|---|---|
| El lanzador no encuentra `OVK-GD.py` | Extrae el ZIP completo y conserva juntos el programa y los lanzadores. |
| `winget` no existe | Instala o actualiza App Installer desde Microsoft Store, o usa instalación manual. |
| Una herramienta no aparece después de instalar | Cierra y vuelve a abrir la terminal y ejecuta diagnóstico. |
| Falta `latexmk` en Windows | Revisa MiKTeX y Strawberry Perl. Ejecuta la opción 1 y verifica los mensajes. |
| macOS no encuentra `tlmgr` | Revisa BasicTeX y reinicia Terminal; normalmente está en `/Library/TeX/texbin`. |
| VS Code no se abre | Comprueba `code --version`; en macOS puede ser necesario instalar el comando `code` desde la paleta de VS Code. |
| No se genera el PDF | Revisa el primer error, la línea indicada y el `.log`. Confirma el motor requerido por tu documento. |
| Pide contraseña de GitHub y la rechaza | Usa Git Credential Manager, GitHub CLI o un token autorizado. |
| `Repository not found` o permiso denegado | Revisa enlace, cuenta autenticada, permisos e invitación aceptada. |
| Se rechaza un `push` | Sincroniza otra vez; revisa permisos, tamaño de archivos y reglas de la rama. |
| Archivos grandes o PDF temporales se siguen subiendo | Si ya están registrados en Git, añadirlos a `.gitignore` no los elimina del seguimiento. Revisa qué quieres conservar. |
| La primera compilación tarda | Puede estar descargando paquetes y generando referencias. Revisa su salida. |

Al reportar un problema, incluye sistema, versión de Python, versión de OVK-GD, acción realizada y el error. Evita incluir tokens o documentos privados. Hay una plantilla en **Issues**.

## 9. Instalación manual

### Windows

Instala [Python](https://www.python.org/downloads/windows/), [Git for Windows](https://git-scm.com/downloads/win), [MiKTeX](https://miktex.org/download), [Strawberry Perl](https://strawberryperl.com/) y [VS Code](https://code.visualstudio.com/). En VS Code instala la extensión **LaTeX Workshop** (`James-Yu.latex-workshop`).

Reinicia la terminal. Comprueba `git --version`, `pdflatex --version`, `perl --version` y `latexmk -v`. Si MiKTeX solicita instalar `latexmk` u otros paquetes, revisa su aviso.

### macOS con Homebrew

```bash
brew install git
brew install --cask basictex visual-studio-code
```

Abre una terminal nueva y completa BasicTeX:

```bash
sudo /Library/TeX/texbin/tlmgr update --self
sudo /Library/TeX/texbin/tlmgr install collection-latexrecommended collection-latexextra collection-fontsrecommended collection-langspanish latexmk biber
```

Si `tlmgr` indica incompatibilidad entre años de TeX Live, revisa las instrucciones de esa distribución antes de cambiar de repositorio de paquetes.

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install git latexmk texlive-latex-extra texlive-fonts-recommended texlive-lang-spanish texlive-bibtex-extra biber
```

### Fedora

```bash
sudo dnf install git latexmk texlive-scheme-medium texlive-biber texlive-babel-spanish
```

Los nombres y la disponibilidad de paquetes pueden variar entre versiones del sistema. Usa el diagnóstico y revisa los mensajes del gestor.

## 10. Referencia de comandos

Ejecuta desde la carpeta de OVK-GD. En macOS/Linux puedes necesitar `python3`; en Windows, `py -3`.

| Comando | Función |
|---|---|
| `python OVK-GD.py` | Abrir el menú. |
| `python OVK-GD.py --help` | Consultar los subcomandos. |
| `python OVK-GD.py instalar` | Preparar herramientas. |
| `python OVK-GD.py actualizar` | Intentar actualizarlas. |
| `python OVK-GD.py proyecto` | Descargar, crear o registrar un documento. |
| `python OVK-GD.py sincronizar -m "Descripción"` | Guardar, descargar y subir. |
| `python OVK-GD.py sincronizar --auto` | Una sincronización sin preguntas de OVK-GD. |
| `python OVK-GD.py auto` | Sincronización periódica hasta `Ctrl+C`. |
| `python OVK-GD.py compilar` | Generar el PDF del proyecto registrado. |
| `python OVK-GD.py diagnostico` | Buscar herramientas y mostrar versiones. |
| `python OVK-GD.py historial` | Consultar commits y elegir uno para compilar. |
| `python OVK-GD.py historial --cantidad 20 --actualizar` | Descargar referencias remotas y abrir el historial con hasta 20 commits. |
| `python OVK-GD.py compilar-version IDENTIFICADOR` | Compilar un commit conocido en una carpeta independiente. |
| `python OVK-GD.py --simular instalar` | Mostrar la instalación sin ejecutarla. |
| `python OVK-GD.py --simular actualizar` | Mostrar la actualización sin ejecutarla. |

Si hay varios proyectos registrados, el programa pide cuál utilizar. `--auto` no elimina esa selección, por lo que esta versión requiere adaptación adicional para programar tareas completamente desatendidas con varios proyectos.

## 11. Versiones anteriores y PDF

### Abrir el historial

1. Abre **OVK-GD_windows.bat** en Windows o **OVK-GD_mac_linux.command** en macOS/Linux.
2. Elige **9 — Historial: versiones anteriores y compilar su PDF**.
3. Selecciona el proyecto cuando tengas varios registrados.
4. Revisa la lista y escribe el número de la versión que deseas compilar.

Se muestran hasta **10 commits** de la rama local al abrir el submenú. Cada entrada incluye un identificador corto, la descripción, el nombre del autor registrado en Git y la fecha con su zona horaria. El commit activo tiene la marca `[HEAD local]`.

Si hay al menos seis commits disponibles, podrás consultar el actual y cinco o más anteriores. Cuando hay menos, el programa muestra los existentes y lo indica; no crea versiones artificiales. Cada sincronización con cambios normalmente añade un commit al historial.

El nombre mostrado corresponde al **autor registrado en Git**. Puede diferir del usuario de GitHub y del nombre de quien hizo la subida. Git también conserva fechas de autor originales al incorporar commits de otras personas.

### Opciones del submenú

| Opción | Acción |
|---|---|
| Número de una entrada | Exportar y compilar ese commit. |
| `M` | Aumentar la lista en diez commits. |
| `R` | Descargar el historial del remoto y mostrar la rama remota correspondiente. |
| `L` | Volver a los commits alcanzables desde la revisión local. |
| `0` | Regresar al menú principal. |

`R` utiliza el remoto `origin` o, si no existe, el primero configurado. Ejecuta `git fetch`, que puede pedir autenticación. Actualiza las referencias de Git, sin mezclar archivos ni subir cambios. Si la descarga falla, puedes seguir consultando los commits disponibles localmente.

En una copia superficial de Git, como una creada con `--depth=1`, `R` intenta descargar hasta 50 niveles adicionales. El número final depende del historial del servidor. Si no existe una rama remota correspondiente, se mantiene la vista local.

### Cómo se genera el PDF histórico

OVK-GD resuelve el identificador completo y exporta los archivos del commit a una carpeta nueva. Compila esas fuentes con `latexmk` y `pdflatex`, y copia el PDF a un nombre que incluye el proyecto y los primeros diez caracteres del commit:

```text
OVK-GD_nombre-del-proyecto_IDENTIFICADOR.pdf
```

Cada ejecución usa una carpeta distinta, por lo que no sobrescribe un PDF histórico anterior. Al terminar, muestra su ruta y abre el visor del sistema.

Los resultados quedan normalmente bajo `~/.ovk-gd/versiones/`, con esta organización:

| Elemento | Contenido |
|---|---|
| `fuente/` | Archivos exportados y resultados de la compilación. |
| `version.json` | Commit completo, autor, fecha, descripción y momento de exportación. |
| PDF con identificador | Copia del resultado que puedes compartir. |

Si esa ubicación estuviera dentro del proyecto, el programa utiliza una carpeta del sistema temporal fuera del proyecto e informa la ruta exacta. Cuando falla LaTeX, conserva las fuentes y registros para revisar el error. Puedes borrar las carpetas de resultados cuando dejes de necesitarlas.

### Requisitos de las versiones históricas

- Debes usar un proyecto con historial Git. Un ZIP descargado desde GitHub no incluye la carpeta `.git`; descarga el proyecto mediante la opción 3 → 1 para conservar su historial.
- La compilación necesita las herramientas LaTeX instaladas. Se aplica el mismo motor `pdflatex` que usa la opción 5.
- Solo se exportan archivos presentes en ese commit y permitidos por las reglas de `git archive`. Los archivos ignorados, cambios sin commit y dependencias externas no se incorporan desde tu copia actual.
- Los recursos gestionados mediante Git LFS o submódulos pueden requerir preparación adicional. La exportación no descarga automáticamente esos contenidos.
- Un commit antiguo puede contener errores LaTeX, depender de paquetes que ya no estén disponibles o usar otro motor. Consulta su registro si falla.

### Compilar un commit desde la terminal

```bash
python OVK-GD.py historial
python OVK-GD.py historial --cantidad 20 --actualizar
python OVK-GD.py compilar-version IDENTIFICADOR_DEL_COMMIT
```

Sustituye `IDENTIFICADOR_DEL_COMMIT` por el código corto o completo mostrado en el historial. El programa sigue utilizando el proyecto registrado que selecciones.
