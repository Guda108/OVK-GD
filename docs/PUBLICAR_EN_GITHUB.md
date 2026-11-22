# Publicar OVK-GD en GitHub

[Volver al README](../README.md)

Esta guía publica **el código de la herramienta**. Los documentos LaTeX del equipo deben guardarse en repositorios independientes.

## 1. Preparar los archivos

1. Descarga y extrae el paquete completo.
2. Abre la carpeta `OVK-GD` en VS Code mediante **File → Open Folder**.
3. Abre **Terminal → New Terminal**. Debes estar en la carpeta que contiene `README.md` y `OVK-GD.py`.
4. Comprueba Git:

   ```bash
   git --version
   ```

Si falta, instala [Git](https://git-scm.com/downloads) y reinicia VS Code. No hace falta ejecutar el instalador de todas las herramientas de LaTeX para subir el repositorio.

## 2. Crear el repositorio vacío

Entra a [github.com/new](https://github.com/new) con tu cuenta y usa estos datos:

| Campo | Valor sugerido |
|---|---|
| Repository name | `OVK-GD` |
| Description | `Compila LaTeX localmente y sincroniza documentos en equipo con Git. Windows, macOS y Linux.` |
| Visibility | `Public` para compartir la herramienta; `Private` para acceso limitado. |
| Add README | Desactivado: ya está incluido. |
| Add .gitignore | Ninguno: ya está incluido. |
| Choose a license | Ninguna por ahora; puedes agregarla después de elegirla. |

Presiona **Create repository**. Copia el enlace HTTPS de **Quick setup**; tendrá esta forma:

```text
https://github.com/TU_USUARIO/OVK-GD.git
```

`TU_USUARIO` es un marcador: sustitúyelo por tu usuario o el nombre de la organización propietaria. Si usas otro nombre de repositorio, cambia también `OVK-GD` en el enlace.

## 3. Cargar desde la terminal de VS Code

Ejecuta estos comandos, uno por uno, dentro de la carpeta del proyecto:

```bash
git init -b main
git config user.name "Dr. Gerardo Diaz"
git config user.email "TU_CORREO_DE_GITHUB"
git add .
git update-index --chmod=+x OVK-GD_mac_linux.command
git status
git commit -m "Presenta OVK-GD: compilación local y colaboración con Git"
git remote add origin https://github.com/TU_USUARIO/OVK-GD.git
git push -u origin main
```

Sustituye el nombre, el correo y el enlace antes de ejecutar sus líneas. Puedes utilizar el correo `noreply` de **GitHub → Settings → Emails**. Estos comandos configuran la identidad solo en este repositorio.

`git add .` incluye los archivos de configuración que empiezan con punto. `git status` permite revisar qué se va a publicar. El comando `update-index` registra el permiso ejecutable del lanzador para quienes lo clonen en macOS/Linux, aunque subas desde Windows.

Al autenticar, usa la cuenta de GitHub que es propietaria del repositorio o tiene permisos de escritura. Con Git Credential Manager puede abrirse el navegador. Si solicita una contraseña en la terminal, consulta [autenticación en el manual](../MANUAL_OVK-GD.md#iniciar-sesión-para-sincronizar): no se utiliza la contraseña normal de GitHub.

Al terminar, actualiza la página del repositorio: aparecerán el banner, el README, el manual y las carpetas. En **Actions** podrás revisar las comprobaciones automáticas cuando GitHub las ejecute.

### Alternativa: GitHub Desktop

Si prefieres una interfaz gráfica, instala [GitHub Desktop](https://desktop.github.com/) y sigue la [guía oficial para añadir un proyecto existente](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop). Puedes usar **File → Add Local Repository** y crear el repositorio local si aún no existe, para después publicarlo con **Publish repository**. Si usas esta alternativa para crear y publicar, no necesitas crear antes otro repositorio vacío con el mismo nombre.

No subas solamente el ZIP a la pestaña **Code**: GitHub necesita los archivos extraídos para mostrar la documentación y ejecutar los flujos.

## 4. Darle presentación

En la página principal, edita el apartado **About** mediante su engrane:

| Elemento | Propuesta |
|---|---|
| Description | La descripción del paso 2. |
| Topics | `latex`, `latexmk`, `python`, `collaboration`, `git`, `cross-platform`, `academic-writing`. |
| Website | Puedes dejarlo vacío; no se necesita una web para usar OVK-GD. |

El README ya contiene enlaces relativos: seguirá funcionando si cambias el nombre del repositorio. El banner está incluido en `docs/assets/OVK-GD-banner.svg`.

En **Settings → General → Social preview**, puedes subir `docs/assets/OVK-GD-social.png` para personalizar la tarjeta al compartir el enlace. Es una composición de presentación, no una captura de la aplicación.

## 5. Publicar una versión descargable

Cuando revises el contenido y las comprobaciones:

1. Abre **Releases → Draft a new release**.
2. Crea una etiqueta para identificar la entrega, con destino en `main`.
3. Título: **OVK-GD — LaTeX local en equipo**.
4. Describe las funciones: compilación local, sincronización con Git e historial del documento con generación de PDF.
5. Publica la versión. GitHub ofrece automáticamente un archivo ZIP del código asociado a la etiqueta.

No marques como comprobadas las instalaciones en Windows o macOS hasta haberlas ejecutado en esos sistemas. El flujo incluido comprueba Python y Git, pero no instala una distribución LaTeX completa.

## 6. Colaboradores y licencia

Agrega a quienes mantendrán **la herramienta** desde **Settings → Collaborators** o **Collaborators and teams**. Para colaborar solo en una tesis, invítalos al repositorio de esa tesis.

No se ha impuesto una licencia en este paquete. Cuando el titular decida las condiciones de uso y redistribución, puede añadir un archivo `LICENSE` y actualizar la sección de licencia del README. GitHub explica este proceso en [Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

## 7. Subir cambios posteriores

Edita los archivos locales y ejecuta:

```bash
git pull --no-rebase
git add .
git diff --cached --stat
git commit -m "Describe el cambio realizado"
git push
```

Revisa y resuelve cualquier aviso antes de seguir con el siguiente comando. Si Git solicita guardar o confirmar cambios locales antes de descargar, termina o guarda ese trabajo primero.

### Si algo falla en la primera carga

| Mensaje | Qué revisar |
|---|---|
| `git` no se reconoce | Instala Git y reinicia VS Code. |
| `Author identity unknown` | Configura nombre y correo como en el paso 3. |
| `remote origin already exists` | Revisa `git remote -v`; si apunta a otro destino, usa `git remote set-url origin URL_CORRECTA`. |
| `Repository not found` | Verifica que el repositorio existe, el enlace es correcto y la cuenta tiene acceso. |
| `Authentication failed` | Revisa la autenticación del manual y la cuenta que utiliza Git. |
| `src refspec main does not match any` | Verifica que se creó un commit y que la rama se llama `main`. |
| `rejected` / `non-fast-forward` | Puede existir un commit en GitHub. Descarga y revisa el historial antes de continuar; evita forzar la subida. |

## Documentación oficial

- [Añadir código local a GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
- [Crear un repositorio](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository).
- [Recordar credenciales de GitHub](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git).
- [Personalizar el repositorio](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository).
