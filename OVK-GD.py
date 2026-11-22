#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVK-GD | Dr. Gerardo Diaz

Escribir LaTeX en tu computadora y trabajar en equipo con Git,
sin necesidad de saber programar.

Que hace:
  1. Instala todo lo necesario (LaTeX, Git, Visual Studio Code) y lo mantiene al dia.
  2. Configura proyectos (descargar uno existente, crear uno nuevo o usar una carpeta).
  3. Sincroniza con un solo paso: guarda tus cambios, descarga los de los demas y los sube.
  4. Compila el PDF.

Solo usa la biblioteca estandar de Python (3.8 o superior). No hay que instalar nada mas.

Uso:
  python OVK-GD.py                 -> menu interactivo (recomendado)
  python OVK-GD.py instalar        -> instalar herramientas
  python OVK-GD.py actualizar      -> actualizar herramientas
  python OVK-GD.py abrir RUTA      -> abrir un proyecto local con su URL guardada
  python OVK-GD.py proyecto        -> crear o descargar un proyecto por primera vez
  python OVK-GD.py sincronizar     -> guardar, descargar y subir cambios
  python OVK-GD.py compilar        -> generar el PDF
  python OVK-GD.py auto            -> sincronizar cada cierto tiempo
  python OVK-GD.py diagnostico     -> revisar que todo este instalado
  python OVK-GD.py historial       -> ver commits y compilar versiones anteriores
  python OVK-GD.py compilar-version COMMIT -> generar el PDF de un commit
  python OVK-GD.py descargar-version COMMIT --principal -> guardar y compilar esa copia
  python OVK-GD.py principal       -> elegir proyecto y archivo principal
  Agrega --simular para ver los comandos de instalacion sin ejecutarlos.
"""
import argparse
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, urlunsplit

APP_NAME = "OVK-GD"
AUTHOR = "Dr. Gerardo Diaz"
SYSTEM = platform.system()  # "Windows", "Darwin" (Mac) o "Linux"
APP_DIR = Path.home() / ".ovk-gd"
CONFIG_FILE = APP_DIR / "proyectos.json"
PROJECT_FILE_NAME = "OVK-GD.proyecto.json"
BASE_PROYECTOS = Path.home() / "Proyectos_OVK-GD"
SIMULAR = False  # si es True, no se ejecutan instalaciones (solo se muestran)

LIMITE_ARCHIVO_MB = 90  # GitHub rechaza archivos de mas de 100 MB

# ---------------------------------------------------------------------------
# Herramientas por sistema operativo
# ---------------------------------------------------------------------------
# (nombre visible, comando que se busca, id de winget)
WIN_HERRAMIENTAS = [
    ("Git", "git", "Git.Git"),
    ("MiKTeX (LaTeX)", "pdflatex", "MiKTeX.MiKTeX"),
    ("Perl (lo necesita latexmk)", "perl", "StrawberryPerl.StrawberryPerl"),
    ("Visual Studio Code", "code", "Microsoft.VisualStudioCode"),
]

MAC_TLMGR_PAQUETES = [
    "collection-latexrecommended", "collection-latexextra",
    "collection-fontsrecommended", "collection-langspanish",
    "latexmk", "biber",
]

LINUX_APT = ["git", "latexmk", "texlive-latex-extra", "texlive-fonts-recommended",
             "texlive-lang-spanish", "texlive-bibtex-extra", "biber"]
LINUX_DNF = ["git", "latexmk", "texlive-scheme-medium", "texlive-biber",
             "texlive-babel-spanish"]

EXTENSION_VSCODE = "James-Yu.latex-workshop"

# ---------------------------------------------------------------------------
# Plantillas de archivos
# ---------------------------------------------------------------------------
PLANTILLA_TEX = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage{graphicx}
\usepackage{hyperref}

\title{Título del documento}
\author{Autor}
\date{\today}

\begin{document}
\maketitle

\section{Introducción}
Escribe aquí tu texto.

\end{document}
"""

GITIGNORE = """# Archivos temporales de LaTeX (se generan solos al compilar)
*.aux
*.log
*.out
*.toc
*.lof
*.lot
*.fls
*.fdb_latexmk
*.synctex.gz
*.bbl
*.blg
*.bcf
*.run.xml
*.nav
*.snm
*.vrb
_minted*/
build/

# El PDF de la raiz no se sube (cada quien lo genera; evita conflictos).
# Si quieres compartir un PDF final, guardalo en una subcarpeta (por ejemplo entrega/).
/*.pdf

# Archivos del sistema
.DS_Store
Thumbs.db
"""

GITATTRIBUTES = "* text=auto\n*.pdf binary\n*.png binary\n*.jpg binary\n*.jpeg binary\n"

VSCODE_SETTINGS = """{
  "latex-workshop.latex.autoBuild.run": "onSave",
  "latex-workshop.view.pdf.viewer": "tab",
  "files.autoSave": "afterDelay"
}
"""


# ---------------------------------------------------------------------------
# Utilidades de pantalla
# ---------------------------------------------------------------------------
def say(msg=""):
    print(msg)


def ok(msg):
    print("  [OK] " + msg)


def aviso(msg):
    print("  [!]  " + msg)


def fallo(msg):
    print("  [X]  " + msg)


def titulo(msg):
    print()
    print("=" * 68)
    print("{} | {}".format(APP_NAME, AUTHOR))
    print(msg)
    print("=" * 68)


def ask(prompt, default=""):
    sufijo = " [{}]".format(default) if default else ""
    try:
        valor = input("{}{}: ".format(prompt, sufijo)).strip()
    except EOFError:
        valor = ""
    return valor or default


def yes(prompt, default=True):
    d = "S/n" if default else "s/N"
    valor = ask("{} ({})".format(prompt, d)).lower()
    if not valor:
        return default
    return valor.startswith(("s", "y"))


def pausa():
    try:
        input("\nPresiona Enter para continuar...")
    except EOFError:
        pass


# ---------------------------------------------------------------------------
# Ejecucion de comandos
# ---------------------------------------------------------------------------
def run(cmd, cwd=None, env=None):
    """Ejecuta un comando y devuelve (codigo, salida)."""
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "No se encontro el programa: {}".format(cmd[0])
    except OSError as e:
        return 126, str(e)


def run_live(cmd, cwd=None, env=None):
    """Ejecuta un comando mostrando su salida en pantalla (y permitiendo que pida datos)."""
    try:
        return subprocess.call(cmd, cwd=cwd, env=env)
    except FileNotFoundError:
        fallo("No se encontro el programa: {}".format(cmd[0]))
        return 127
    except OSError as e:
        fallo(str(e))
        return 126


def run_install(cmd):
    """Como run_live, pero respeta el modo --simular."""
    say("  $ " + " ".join(cmd))
    if SIMULAR:
        say("    [simulacion] no se ejecuto")
        return 0
    return run_live(cmd)


def git(args, cwd=None):
    return run(["git", "-c", "core.quotepath=off"] + list(args), cwd=cwd)


def refresh_path():
    """Actualiza el PATH del proceso para ver programas recien instalados."""
    if SYSTEM == "Windows":
        try:
            import winreg
            rutas = []
            for raiz, sub in (
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                (winreg.HKEY_CURRENT_USER, "Environment"),
            ):
                try:
                    with winreg.OpenKey(raiz, sub) as k:
                        valor, _ = winreg.QueryValueEx(k, "Path")
                        rutas.append(os.path.expandvars(valor))
                except OSError:
                    pass
            if rutas:
                os.environ["PATH"] = os.pathsep.join(rutas + [os.environ.get("PATH", "")])
        except ImportError:
            pass
    else:
        extras = ["/Library/TeX/texbin", "/opt/homebrew/bin", "/usr/local/bin"]
        actuales = os.environ.get("PATH", "").split(os.pathsep)
        for e in extras:
            if os.path.isdir(e) and e not in actuales:
                actuales.append(e)
        os.environ["PATH"] = os.pathsep.join(actuales)


# ---------------------------------------------------------------------------
# Instalacion y actualizacion de herramientas
# ---------------------------------------------------------------------------
def instalar_extension_vscode():
    code = shutil.which("code")
    if not code:
        aviso("No encontre Visual Studio Code; omito la extension de LaTeX.")
        return
    say("Instalando/actualizando la extension LaTeX Workshop de VS Code...")
    run_install([code, "--install-extension", EXTENSION_VSCODE, "--force"])


def _windows(actualizar):
    if not shutil.which("winget"):
        fallo("No encontre 'winget'. Abre Microsoft Store, busca 'Instalador de aplicacion' "
              "y actualizalo. Luego vuelve a ejecutar este programa.")
        return
    for nombre, comando, wid in WIN_HERRAMIENTAS:
        presente = shutil.which(comando) is not None
        if presente and not actualizar:
            ok("{} ya esta instalado.".format(nombre))
            continue
        accion = "upgrade" if presente else "install"
        say("\n{} {}...".format("Actualizando" if presente else "Instalando", nombre))
        run_install(["winget", accion, "--id", wid, "-e", "--silent",
                     "--accept-package-agreements", "--accept-source-agreements"])
    refresh_path()
    initexmf = shutil.which("initexmf")
    if initexmf:
        say("\nConfigurando MiKTeX para que descargue solo los paquetes que falten...")
        run_install([initexmf, "--set-config-value=[MPM]AutoInstall=1"])
    miktex = shutil.which("miktex")
    if miktex:
        say("\nActualizando paquetes de LaTeX (MiKTeX)...")
        run_install([miktex, "packages", "update-package-database"])
        run_install([miktex, "packages", "update"])
    instalar_extension_vscode()


def _mac(actualizar):
    brew = shutil.which("brew")
    for candidato in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if not brew and os.path.exists(candidato):
            brew = candidato
    if not brew:
        fallo("Falta Homebrew (el instalador de programas de Mac).")
        say("  Abre la app 'Terminal' y pega la linea que aparece en https://brew.sh")
        say("  Cuando termine, vuelve a ejecutar este programa.")
        return
    if actualizar:
        say("\nActualizando programas con Homebrew...")
        run_install([brew, "update"])
        run_install([brew, "upgrade"])
    else:
        faltan = []
        if run([brew, "list", "--formula", "git"])[0] != 0:
            faltan.append(["install", "git"])
        if run([brew, "list", "--cask", "basictex"])[0] != 0:
            faltan.append(["install", "--cask", "basictex"])
        if run([brew, "list", "--cask", "visual-studio-code"])[0] != 0:
            faltan.append(["install", "--cask", "visual-studio-code"])
        if not faltan:
            ok("Git, LaTeX (BasicTeX) y VS Code ya estan instalados.")
        for args in faltan:
            say("\nInstalando {}...".format(args[-1]))
            run_install([brew] + args)
    refresh_path()
    tlmgr = shutil.which("tlmgr")
    if not tlmgr:
        aviso("No encontre 'tlmgr'. Cierra la Terminal, abrela de nuevo y repite este paso.")
        return
    say("\nInstalando paquetes de LaTeX (te pedira tu contrasena de Mac)...")
    run_install(["sudo", tlmgr, "update", "--self"])
    run_install(["sudo", tlmgr, "install"] + MAC_TLMGR_PAQUETES)
    if actualizar:
        run_install(["sudo", tlmgr, "update", "--all"])
    instalar_extension_vscode()


def _linux(actualizar):
    prefijo = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else ["sudo"]
    if shutil.which("apt-get"):
        run_install(prefijo + ["apt-get", "update"])
        run_install(prefijo + ["apt-get", "install", "-y"] + LINUX_APT)
    elif shutil.which("dnf"):
        run_install(prefijo + ["dnf", "install", "-y"] + LINUX_DNF)
    else:
        fallo("Solo se automatiza apt (Ubuntu/Debian) y dnf (Fedora). "
              "Instala 'git', 'latexmk' y una distribucion TeX Live completa a mano.")
        return
    if shutil.which("code"):
        instalar_extension_vscode()
    else:
        aviso("Visual Studio Code no esta instalado. Descargalo de https://code.visualstudio.com")


def instalar(actualizar=False):
    titulo("Actualizar herramientas" if actualizar else "Instalar herramientas")
    if SIMULAR:
        aviso("MODO SIMULACION: solo se muestran los comandos.")
    refresh_path()
    if SYSTEM == "Windows":
        _windows(actualizar)
    elif SYSTEM == "Darwin":
        _mac(actualizar)
    else:
        _linux(actualizar)
    say()
    say("Terminado. Si algun programa recien instalado no aparece en el diagnostico,")
    say("cierra esta ventana y vuelve a abrirla (para que el sistema lo reconozca).")


def diagnostico():
    titulo("Diagnostico")
    refresh_path()
    say("Sistema: {} | Python {}".format(platform.platform(), platform.python_version()))
    say()
    revisar = [("Git", "git", ["--version"]),
               ("latexmk (compila el PDF)", "latexmk", ["-v"]),
               ("pdflatex (motor de LaTeX)", "pdflatex", ["--version"]),
               ("biber (bibliografia)", "biber", ["--version"]),
               ("Visual Studio Code", "code", ["--version"])]
    if SYSTEM == "Windows":
        revisar.insert(2, ("Perl (lo necesita latexmk)", "perl", ["--version"]))
    todo_bien = True
    for nombre, cmd, args in revisar:
        ruta = shutil.which(cmd)
        if not ruta:
            fallo("{}: NO instalado".format(nombre))
            todo_bien = False
            continue
        _, out = run([ruta] + args)
        primera = out.splitlines()[0] if out else ""
        ok("{}: {}".format(nombre, primera[:70]))
    code = shutil.which("code")
    if code:
        _, exts = run([code, "--list-extensions"])
        if EXTENSION_VSCODE.lower() in exts.lower():
            ok("Extension LaTeX Workshop de VS Code: instalada")
        else:
            fallo("Extension LaTeX Workshop de VS Code: NO instalada")
            todo_bien = False
    say()
    if todo_bien:
        ok("Todo listo.")
    else:
        aviso("Faltan cosas. Ejecuta la opcion 'Instalar herramientas'.")


# ---------------------------------------------------------------------------
# Proyectos
# ---------------------------------------------------------------------------
def cargar_proyectos():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def guardar_proyectos(lista):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)


def registrar_proyecto(nombre, ruta):
    lista = [p for p in cargar_proyectos() if p["path"] != str(ruta)]
    lista.append({"name": nombre, "path": str(ruta)})
    guardar_proyectos(lista)


def leer_datos_proyecto(ruta):
    archivo = Path(ruta) / PROJECT_FILE_NAME
    if not archivo.exists():
        return {}
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError("No se pudo leer {}: {}".format(archivo, e))
    if not isinstance(datos, dict) or any(
            clave in datos and not isinstance(datos[clave], str)
            for clave in ("name", "url", "remote", "main")):
        raise ValueError("{} debe contener nombre, URL y archivo principal como texto.".format(archivo))
    if datos.get("main"):
        datos["main"] = datos["main"].replace("\\", "/")
    return datos


def conexion_git(ruta, preferido="origin"):
    """Lee la conexion del repositorio exacto, sin acceder a la red."""
    ruta = Path(ruta).resolve()
    codigo, raiz = git(["rev-parse", "--show-toplevel"], ruta)
    if codigo != 0 or Path(raiz).resolve() != ruta:
        return None, ""
    codigo, salida = git(["remote"], ruta)
    remotos = salida.split() if codigo == 0 else []
    if not remotos:
        return None, ""
    remoto = preferido if preferido in remotos else ("origin" if "origin" in remotos else remotos[0])
    codigo, url = git(["remote", "get-url", remoto], ruta)
    return (remoto, url.strip()) if codigo == 0 else (None, "")


def url_para_guardar(url):
    """Guarda el enlace del proyecto sin credenciales HTTP incrustadas."""
    if url.startswith(("https://", "http://")):
        partes = urlsplit(url)
        return urlunsplit((partes.scheme, partes.netloc.rsplit("@", 1)[-1], partes.path, partes.query, partes.fragment))
    return url


def guardar_datos_proyecto(proyecto, principal=None):
    ruta = Path(proyecto["path"]).resolve()
    anteriores = leer_datos_proyecto(ruta)
    remoto, url = conexion_git(ruta, anteriores.get("remote", "origin"))
    datos = {"name": proyecto["name"],
             "url": url_para_guardar(url or proyecto.get("url") or anteriores.get("url", "")),
             "remote": remoto or anteriores.get("remote", "origin"),
             "main": (principal or proyecto.get("main") or anteriores.get("main", "")).replace("\\", "/")}
    (ruta / PROJECT_FILE_NAME).write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    return datos


def restaurar_conexion_guardada(ruta, datos):
    """Reutiliza el enlace guardado si Git no tiene ningun remoto. No descarga archivos."""
    url = datos.get("url", "")
    if not url:
        return
    codigo, raiz = git(["rev-parse", "--show-toplevel"], ruta)
    if codigo != 0 or Path(raiz).resolve() != Path(ruta).resolve():
        return
    codigo, remotos = git(["remote"], ruta)
    if codigo != 0 or remotos.strip():
        return
    remoto = datos.get("remote") or "origin"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", remoto):
        remoto = "origin"
    codigo, salida = git(["remote", "add", "--", remoto, url], ruta)
    if codigo != 0:
        raise ValueError("No se pudo reutilizar la URL guardada:\n" + salida)


def obtener_proyecto_principal():
    try:
        datos = json.loads((APP_DIR / "principal.json").read_text(encoding="utf-8"))
        if (isinstance(datos, dict) and isinstance(datos.get("path"), str)
                and isinstance(datos.get("main"), str) and Path(datos["path"]).is_dir()):
            return datos
    except (OSError, ValueError):
        pass
    return None


def elegir_proyecto(usar_principal=True):
    if usar_principal:
        principal = obtener_proyecto_principal()
        if principal:
            return principal
    lista = [p for p in cargar_proyectos() if Path(p["path"]).exists()]
    if not lista:
        aviso("Todavia no hay proyectos. Usa la opcion 3 para abrir una carpeta o la 11 para crear un proyecto.")
        return None
    if len(lista) == 1:
        return lista[0]
    say("Proyectos disponibles:")
    for i, p in enumerate(lista, 1):
        say("  {}) {}  ({})".format(i, p["name"], p["path"]))
    say("  0) Cancelar")
    while True:
        n = ask("Elige el numero del proyecto", "1")
        if n == "0":
            return None
        if n.isdigit() and 1 <= int(n) <= len(lista):
            return lista[int(n) - 1]
        say("  Numero no valido.")


def nombre_seguro(texto):
    limpio = re.sub(r"[^\w\-.]+", "_", texto.strip(), flags=re.UNICODE).strip("._")
    return limpio or "proyecto"


def ensure_identity(cwd=None, auto=False):
    """Git necesita nombre y correo para firmar los cambios."""
    for clave, etiqueta in (("user.name", "tu nombre"), ("user.email", "tu correo")):
        codigo, valor = git(["config", "--get", clave], cwd)
        if codigo != 0 or not valor.strip():
            if auto:
                fallo("Git no tiene configurado {}. Ejecuta una vez la sincronizacion normal.".format(etiqueta))
                return False
            v = ""
            while not v:
                v = ask("Git necesita {} (aparecera junto a los cambios que guardes)".format(etiqueta))
            git(["config", "--global", clave, v], cwd)
    # Guardar la contrasena/token para no escribirla cada vez
    codigo, valor = git(["config", "--get", "credential.helper"], cwd)
    if codigo != 0 or not valor.strip():
        if SYSTEM == "Darwin":
            git(["config", "--global", "credential.helper", "osxkeychain"], cwd)
        elif SYSTEM == "Linux":
            git(["config", "--global", "credential.helper", "cache --timeout=28800"], cwd)
    return True


def crear_archivos_base(ruta):
    """Crea .gitignore, .gitattributes y ajustes de VS Code si no existen."""
    ruta = Path(ruta)
    for nombre, contenido in ((".gitignore", GITIGNORE), (".gitattributes", GITATTRIBUTES)):
        destino = ruta / nombre
        if not destino.exists():
            destino.write_text(contenido, encoding="utf-8")
            ok("Creado {}".format(nombre))
    vs = ruta / ".vscode" / "settings.json"
    if not vs.exists():
        vs.parent.mkdir(exist_ok=True)
        vs.write_text(VSCODE_SETTINGS, encoding="utf-8")
        ok("Creado .vscode/settings.json (compila el PDF al guardar)")


def detectar_principal(ruta, elegir=False):
    """Busca el .tex principal (el que contiene \\documentclass)."""
    ruta = Path(ruta)
    candidatos = []
    for f in sorted(ruta.rglob("*.tex")):
        if any(parte.startswith(".") for parte in f.relative_to(ruta).parts):
            continue
        try:
            if "\\documentclass" in f.read_text(encoding="utf-8", errors="ignore"):
                candidatos.append(f.relative_to(ruta))
        except OSError:
            pass
    if not candidatos:
        return None
    if not elegir:
        for c in candidatos:
            if c.name.lower() == "main.tex":
                return str(c)
    if len(candidatos) == 1:
        return str(candidatos[0])
    say("Encontre varios archivos principales:")
    for i, c in enumerate(candidatos, 1):
        say("  {}) {}".format(i, c))
    if elegir:
        say("  0) Cancelar")
    while True:
        n = ask("Cual quieres compilar", "1")
        if elegir and n == "0":
            return None
        if n.isdigit() and 1 <= int(n) <= len(candidatos):
            return str(candidatos[int(n) - 1])


def establecer_proyecto_principal(proyecto, principal=None):
    ruta = Path(proyecto["path"]).resolve()
    try:
        configuracion = leer_datos_proyecto(ruta)
    except ValueError as e:
        fallo(str(e))
        return False
    if principal is None:
        preferido = proyecto.get("main") or configuracion.get("main")
        if preferido:
            try:
                archivo_guardado = (ruta / preferido).resolve()
                archivo_guardado.relative_to(ruta)
                if archivo_guardado.is_file() and archivo_guardado.suffix.lower() == ".tex":
                    principal = preferido
            except (OSError, ValueError):
                pass
        principal = principal or detectar_principal(ruta, elegir=True)
    if not principal:
        aviso("No se selecciono un archivo principal. La seleccion actual se conserva.")
        return False
    try:
        archivo = (ruta / principal).resolve()
        relativo = archivo.relative_to(ruta)
        if archivo.suffix.lower() != ".tex" or not archivo.is_file():
            raise ValueError("El archivo principal debe ser un .tex existente.")
        datos = {"name": proyecto["name"], "path": str(ruta), "main": str(relativo)}
        configuracion = guardar_datos_proyecto(datos, str(relativo))
        datos["url"] = configuracion["url"]
        APP_DIR.mkdir(parents=True, exist_ok=True)
        registrar_proyecto(datos["name"], ruta)
        (APP_DIR / "principal.json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    except (OSError, ValueError) as e:
        fallo("No se pudo seleccionar el proyecto principal: {}".format(e))
        return False
    ok("Proyecto principal: {}".format(datos["name"]))
    say("  Archivo: {}".format(archivo))
    say("  La opcion 5 compilara este archivo. Usa la opcion 10 para cambiar de proyecto.")
    return True


def explorar_carpeta():
    ventana = None
    try:
        import tkinter as tk
        from tkinter import filedialog
        ventana = tk.Tk()
        ventana.withdraw()
        return filedialog.askdirectory(title="OVK-GD - Abrir carpeta del proyecto", parent=ventana)
    except Exception:
        aviso("No se pudo abrir el selector. Pega la ruta de la carpeta en la terminal.")
        return ""
    finally:
        if ventana is not None:
            ventana.destroy()


def ruta_local(texto):
    texto = str(texto).strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in ("\"", "'"):
        texto = texto[1:-1]
    return Path(os.path.expandvars(texto)).expanduser().resolve()


def abrir_proyecto_local(ruta=None):
    titulo("Abrir proyecto desde la PC")
    if ruta is None:
        ruta = ask("Carpeta, archivo .tex o {} (E para explorar, 0 para cancelar)".format(PROJECT_FILE_NAME))
        if ruta.lower() == "e":
            ruta = explorar_carpeta()
        if not ruta or ruta == "0":
            return None
    try:
        seleccion = ruta_local(ruta)
        principal = None
        if seleccion.is_file():
            if seleccion.suffix.lower() == ".tex":
                principal = seleccion
                carpeta = seleccion.parent
                for candidata in (carpeta,) + tuple(carpeta.parents):
                    if (candidata / PROJECT_FILE_NAME).is_file() or (candidata / ".git").exists():
                        carpeta = candidata
                        break
            elif seleccion.name == PROJECT_FILE_NAME:
                carpeta = seleccion.parent
            else:
                raise ValueError("Selecciona una carpeta, un archivo .tex o {}.".format(PROJECT_FILE_NAME))
        elif seleccion.is_dir():
            carpeta = seleccion
        else:
            raise ValueError("La ubicacion no existe. Elige la carpeta donde ya estan tus archivos.")
        datos = leer_datos_proyecto(carpeta)
        restaurar_conexion_guardada(carpeta, datos)
        proyecto = {"name": datos.get("name") or carpeta.name, "path": str(carpeta)}
        if principal is not None:
            principal = str(principal.relative_to(carpeta))
        if not establecer_proyecto_principal(proyecto, principal):
            return None
        proyecto = obtener_proyecto_principal()
        ok("Proyecto abierto desde su carpeta local.")
        if proyecto.get("url"):
            say("  URL del proyecto: {}".format(proyecto["url"]))
        say("  Configuracion: {}".format(carpeta / PROJECT_FILE_NAME))
        return proyecto
    except (OSError, ValueError) as e:
        fallo("No se pudo abrir el proyecto: {}".format(e))
        return None


def seleccionar_principal():
    titulo("Elegir proyecto y archivo principal")
    proyecto = elegir_proyecto(usar_principal=False)
    if proyecto:
        principal = detectar_principal(proyecto["path"], elegir=True)
        return establecer_proyecto_principal(proyecto, principal) if principal else False
    return False


def _iniciar_repo(ruta):
    for args in (["init"], ["symbolic-ref", "HEAD", "refs/heads/main"]):
        codigo, salida = git(args, ruta)
        if codigo != 0:
            fallo("No se pudo preparar Git en la carpeta seleccionada:\n" + salida)
            return False
    return True


def configurar_proyecto():
    titulo("Crear o descargar un proyecto")
    say("1) Descargar de GitHub/GitLab por primera vez")
    say("2) Crear un proyecto nuevo")
    say("3) Abrir una carpeta que ya tengo en mi computadora")
    say("4) Conectar una carpeta local a GitHub/GitLab")
    say("0) Volver")
    opcion = ask("Elige una opcion", "0")
    if opcion == "3":
        return abrir_proyecto_local()
    if opcion not in ("1", "2", "4"):
        return None
    if not shutil.which("git"):
        fallo("Git no esta instalado. Ejecuta primero 'Instalar herramientas'.")
        return None

    if opcion == "1":
        url = ""
        while not url:
            url = ask("Pega el enlace del repositorio (termina en .git o es la direccion de la pagina)")
        sugerido = nombre_seguro(url.rstrip("/").split("/")[-1].replace(".git", ""))
        destino = ruta_local(ask("Carpeta donde guardarlo", str(BASE_PROYECTOS / sugerido)))
        if destino.exists() and (not destino.is_dir() or any(destino.iterdir())):
            fallo("Esa ubicacion ya tiene contenido. Usa la opcion 3 para abrirla o elige otra para descargar.")
            return None
        if not ensure_identity():
            return None
        destino.parent.mkdir(parents=True, exist_ok=True)
        say("\nDescargando (si te pide usuario y contrasena, mira el manual: se usa un 'token')...")
        if run_live(["git", "clone", url, str(destino)]) != 0:
            fallo("No se pudo descargar. Revisa el enlace y tus permisos.")
            return None
        nombre = destino.name

    elif opcion == "2":
        nombre = nombre_seguro(ask("Nombre del proyecto (sin espacios, por ejemplo tesis)", "mi_documento"))
        destino = ruta_local(ask("Carpeta donde crearlo", str(BASE_PROYECTOS / nombre)))
        if destino.exists() and (not destino.is_dir() or any(destino.iterdir())):
            fallo("Esa ubicacion ya tiene contenido. Usa la opcion 3 para abrirla o elige otra para crear.")
            return None
        destino.mkdir(parents=True, exist_ok=True)
        if not (destino / ".git").exists():
            if not _iniciar_repo(destino):
                return None
        if not (destino / "main.tex").exists():
            (destino / "main.tex").write_text(PLANTILLA_TEX, encoding="utf-8")
            ok("Creado main.tex de ejemplo")
        url = ask("Enlace del repositorio vacio donde se compartira (Enter para omitir)")
        if url:
            codigo, salida = git(["remote", "add", "--", "origin", url], destino)
            if codigo != 0:
                fallo("No se pudo guardar la conexion del proyecto:\n" + salida)
                return None

    elif opcion == "4":
        seleccion = ask("Carpeta que deseas conectar (0 para cancelar)")
        if not seleccion or seleccion == "0":
            return None
        destino = ruta_local(seleccion)
        if not destino.is_dir():
            fallo("Esa carpeta no existe.")
            return None
        try:
            datos = leer_datos_proyecto(destino)
        except ValueError as e:
            fallo(str(e))
            return None
        nombre = datos.get("name") or destino.name
        if not (destino / ".git").exists() and not _iniciar_repo(destino):
            return None
        remoto, url = conexion_git(destino, datos.get("remote", "origin"))
        if not url:
            url = datos.get("url") or ask("Enlace del repositorio donde se compartira (Enter para omitir)")
            if url:
                codigo, salida = git(["remote", "add", "--", "origin", url], destino)
                if codigo != 0:
                    fallo("No se pudo guardar la conexion:\n" + salida)
                    return None

    if not ensure_identity(destino):
        return None
    crear_archivos_base(destino)
    registrar_proyecto(nombre, destino)
    ok("Proyecto '{}' registrado en {}".format(nombre, destino))
    proyecto = {"name": nombre, "path": str(destino)}
    try:
        guardar_datos_proyecto(proyecto)
    except (OSError, ValueError) as e:
        fallo("No se pudo guardar la configuracion del proyecto: {}".format(e))
        return None
    establecer_proyecto_principal(proyecto)
    if yes("¿Sincronizar ahora (guardar y subir lo que hay)?", True):
        sincronizar(proyecto)
    return proyecto


# ---------------------------------------------------------------------------
# Sincronizacion con Git
# ---------------------------------------------------------------------------
def tiene_commits(ruta):
    return git(["rev-parse", "--verify", "HEAD"], ruta)[0] == 0


def cabeza(ruta):
    return git(["rev-parse", "HEAD"], ruta)[1].strip()


def guardar_cambios(ruta, mensaje=None, auto=False):
    """Devuelve True al guardar, False sin cambios y None ante un error."""
    codigo, salida = git(["add", "-A"], ruta)
    if codigo != 0:
        fallo("No se pudieron preparar los cambios:\n" + salida)
        return None
    codigo, archivos = git(["diff", "--cached", "--name-only"], ruta)
    if codigo != 0:
        fallo("No se pudieron revisar los cambios:\n" + archivos)
        return None
    lista = [a for a in archivos.splitlines() if a.strip()]

    # Proteccion: GitHub rechaza archivos enormes y eso atasca todo el historial.
    for a in list(lista):
        p = Path(ruta) / a
        if p.exists() and p.stat().st_size > LIMITE_ARCHIVO_MB * 1024 * 1024:
            git(["reset", "-q", "--", a], ruta)
            lista.remove(a)
            aviso("'{}' pesa mas de {} MB: NO se subira (GitHub no lo acepta). "
                  "Muevelo fuera del proyecto o comprimelo.".format(a, LIMITE_ARCHIVO_MB))
    if not lista:
        say("  Sin cambios nuevos que guardar.")
        return False

    nombres = [Path(a).name for a in lista]
    resumen = ", ".join(nombres[:3]) + (" (+{} mas)".format(len(nombres) - 3) if len(nombres) > 3 else "")
    if not mensaje and not auto:
        mensaje = ask("Describe brevemente tus cambios (Enter = mensaje automatico)")
    if not mensaje:
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        mensaje = "Actualizacion {} - {}".format(fecha, resumen)
    codigo, salida = git(["commit", "-m", mensaje], ruta)
    if codigo != 0:
        fallo("No se pudieron guardar los cambios:\n" + salida)
        return None
    ok("Cambios guardados ({} archivo(s)): {}".format(len(lista), resumen))
    return True


def _cancelar_merge(ruta):
    git(["merge", "--abort"], ruta)
    aviso("Se cancelo la mezcla. Tus cambios estan a salvo y nada se perdio.")


def resolver_conflictos(ruta, auto):
    _, salida = git(["diff", "--name-only", "--diff-filter=U"], ruta)
    archivos = [l for l in salida.splitlines() if l.strip()]
    if not archivos:
        fallo("No se pudieron descargar los cambios del servidor "
              "(¿sin internet o sin permiso?). Tus cambios locales siguen guardados.")
        return False
    aviso("CONFLICTO: tu y otra persona editaron las mismas lineas de:")
    for a in archivos:
        say("       - " + a)
    if auto:
        _cancelar_merge(ruta)
        aviso("Modo automatico: sincroniza a mano (opcion 4 del menu) para elegir que version conservar.")
        return False
    say()
    say("  Elige que version conservar de cada archivo. La otra version no se pierde:")
    say("  queda en el historial de Git y se puede recuperar.")
    for a in archivos:
        say()
        op = ask("  {}\n   [1] MI version   [2] La version de la OTRA persona   [3] Cancelar".format(a), "3")
        if op not in ("1", "2"):
            _cancelar_merge(ruta)
            return False
        bandera = "--ours" if op == "1" else "--theirs"
        codigo, out = git(["checkout", bandera, "--", a], ruta)
        if codigo == 0:
            codigo, out = git(["add", "--", a], ruta)
        if codigo != 0:
            fallo("No pude resolver '{}' automaticamente:\n{}".format(a, out))
            _cancelar_merge(ruta)
            return False
    codigo, out = git(["commit", "--no-edit"], ruta)
    if codigo != 0:
        fallo("No se pudo terminar la mezcla:\n" + out)
        _cancelar_merge(ruta)
        return False
    ok("Conflictos resueltos.")
    return True


def sincronizar(proyecto, auto=False, mensaje=None):
    """Guarda cambios, descarga los de otras personas y sube los tuyos."""
    ruta = proyecto["path"]
    titulo("Sincronizando: {}".format(proyecto["name"]))
    if not shutil.which("git"):
        fallo("Git no esta instalado. Ejecuta primero 'Instalar herramientas'.")
        return False
    if not (Path(ruta) / ".git").exists():
        fallo("La carpeta {} no es un proyecto Git.".format(ruta))
        return False
    if not ensure_identity(ruta, auto):
        return False
    crear_archivos_base(ruta)

    say("\n1) Guardando tus cambios...")
    if guardar_cambios(ruta, mensaje, auto) is None:
        return False

    _, remotos_txt = git(["remote"], ruta)
    remotos = remotos_txt.split()
    if not remotos:
        aviso("Este proyecto no tiene servidor remoto, asi que los cambios solo estan en tu computadora.")
        say("  Para compartirlo, crea un repositorio vacio en GitHub y agrega su enlace:")
        say("  git remote add origin <enlace>   (el enlace quedara guardado al abrir la carpeta con la opcion 3)")
        return True
    remoto = "origin" if "origin" in remotos else remotos[0]

    if not tiene_commits(ruta):
        aviso("Aun no hay nada guardado en el proyecto; agrega archivos y vuelve a sincronizar.")
        return True
    codigo, rama = git(["symbolic-ref", "--short", "HEAD"], ruta)
    rama = rama.strip()
    if codigo != 0 or not rama:
        fallo("Git esta en un estado raro (sin rama). Pide ayuda a alguien con experiencia.")
        return False

    env = dict(os.environ, GIT_TERMINAL_PROMPT="0") if auto else None
    tiene_upstream = git(["rev-parse", "--abbrev-ref", "{}@{{u}}".format(rama)], ruta)[0] == 0

    for intento in (1, 2):
        say("\n2) Revisando cambios de otras personas...")
        codigo, salida = run(["git", "ls-remote", "--exit-code", "--heads", remoto, rama], cwd=ruta, env=env)
        if codigo == 0:
            existe = True
        elif codigo == 2:
            existe = False
        else:
            fallo("No pude conectarme al servidor. Revisa tu internet, el enlace y tus permisos.")
            if salida:
                say("     " + salida.splitlines()[-1])
            return False

        if existe:
            antes = cabeza(ruta)
            args = ["git", "pull", "--no-rebase", "--no-edit"]
            if not tiene_upstream:
                args.append("--allow-unrelated-histories")
            args += [remoto, rama]
            if run_live(args, cwd=ruta, env=env) != 0:
                if not resolver_conflictos(ruta, auto):
                    return False
            despues = cabeza(ruta)
            if antes != despues:
                _, cambiados = git(["diff", "--name-only", antes, despues], ruta)
                nombres = [c for c in cambiados.splitlines() if c.strip()]
                if nombres:
                    ok("Se actualizaron {} archivo(s) con cambios de otras personas.".format(len(nombres)))
                    for n in nombres[:8]:
                        say("       - " + n)
                else:
                    say("  Se descargo historial nuevo, pero tus archivos no cambiaron.")
            else:
                say("  Nadie mas habia hecho cambios nuevos.")
        else:
            say("  El servidor aun no tiene esta rama; se creara al subir.")

        say("\n3) Subiendo tus cambios...")
        if run_live(["git", "push", "-u", remoto, rama], cwd=ruta, env=env) == 0:
            ok("Listo: todo esta sincronizado.")
            return True
        if intento == 1:
            aviso("El servidor recibio cambios nuevos mientras tanto; reintentando una vez...")
            tiene_upstream = True

    fallo("No se pudieron subir los cambios. Causas comunes:")
    say("     - Te falta permiso: pide que te agreguen como colaborador del repositorio.")
    say("     - Credenciales: GitHub pide un 'token', no tu contrasena (ver manual).")
    say("     - Algun archivo pesa mas de 100 MB.")
    return False


def sincronizacion_automatica(proyecto):
    titulo("Sincronizacion automatica")
    minutos = ask("Cada cuantos minutos sincronizar (minimo 1)", "10")
    minutos = max(1, int(minutos)) if minutos.isdigit() else 10
    say("Se sincronizara '{}' cada {} minuto(s). Para detener: Ctrl+C.".format(proyecto["name"], minutos))
    say("Si hay un conflicto, se cancela esa ronda y se te avisa aqui.")
    try:
        while True:
            sincronizar(proyecto, auto=True)
            say("\nProxima sincronizacion en {} minuto(s)...".format(minutos))
            time.sleep(minutos * 60)
    except KeyboardInterrupt:
        say("\nSincronizacion automatica detenida.")


# ---------------------------------------------------------------------------
# Compilacion y apertura
# ---------------------------------------------------------------------------
def abrir_archivo(ruta):
    try:
        if SYSTEM == "Windows":
            os.startfile(str(ruta))  # noqa
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", str(ruta)])
        else:
            subprocess.Popen(["xdg-open", str(ruta)])
    except Exception:
        aviso("No pude abrir el PDF automaticamente: {}".format(ruta))


def compilar(proyecto, abrir=True, principal=None):
    titulo("Compilar PDF: {}".format(proyecto["name"]))
    ruta = Path(proyecto["path"])
    refresh_path()
    latexmk = shutil.which("latexmk")
    if not latexmk:
        fallo("No encontre 'latexmk'. Ejecuta 'Instalar herramientas' (o cierra y abre esta ventana "
              "si acabas de instalarlo).")
        return False
    principal = principal or proyecto.get("main") or detectar_principal(ruta)
    if not principal:
        fallo("No encontre ningun archivo .tex con \\documentclass en el proyecto.")
        return False
    try:
        archivo = (ruta / principal).resolve()
        archivo.relative_to(ruta.resolve())
        if not archivo.is_file() or archivo.suffix.lower() != ".tex":
            raise ValueError("El archivo ya no existe o no es un .tex.")
    except (OSError, ValueError) as e:
        fallo("Archivo principal no valido: {}. Usa la opcion 10 para elegirlo.".format(e))
        return False
    say("Compilando {} ...\n".format(principal))
    codigo = run_live([latexmk, "-cd", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                       "-file-line-error", principal], cwd=str(ruta))
    pdf = (ruta / principal).with_suffix(".pdf")
    if codigo == 0 and pdf.exists():
        ok("PDF generado: {}".format(pdf))
        if abrir:
            abrir_archivo(pdf)
        return True
    fallo("La compilacion fallo. Errores encontrados en el registro:")
    log = (ruta / principal).with_suffix(".log")
    try:
        lineas = log.read_text(encoding="utf-8", errors="replace").splitlines()
        errores = [l for l in lineas if l.startswith("!") or re.match(r"^.+:\d+: ", l)]
        for l in errores[:10]:
            say("     " + l)
        if not errores:
            say("     (revisa el archivo {})".format(log.name))
    except OSError:
        say("     (no se encontro el archivo de registro)")
    say("  Pista: el numero despues del nombre del archivo es la linea con el problema.")
    return False


def abrir_vscode(proyecto):
    code = shutil.which("code")
    if not code:
        fallo("Visual Studio Code no esta instalado. Usa 'Instalar herramientas'.")
        return
    subprocess.Popen([code, proyecto["path"]])
    ok("Abriendo VS Code. Guarda con Ctrl+S (Cmd+S en Mac) y el PDF se actualiza solo.")


# ---------------------------------------------------------------------------
# Historial Git: consultar y compilar sin cambiar el proyecto activo
# ---------------------------------------------------------------------------
def texto_terminal(texto):
    """Evita interpretar caracteres de control presentes en metadatos de Git."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", texto)


def listar_versiones(proyecto, cantidad=10, referencia="HEAD"):
    """Devuelve commits alcanzables desde la referencia seleccionada."""
    formato = "%H%x00%h%x00%an%x00%ai%x00%s"
    codigo, salida = git(["log", "--no-color", "--date-order", "-n", str(max(6, cantidad)),
                          "--format=" + formato, referencia, "--"], proyecto["path"])
    if codigo != 0:
        aviso("No hay historial disponible en {}. Guarda al menos un commit o descarga el proyecto.".format(
            texto_terminal(referencia)))
        return []
    versiones = []
    for linea in salida.splitlines():
        campos = linea.split("\x00", 4)
        if len(campos) == 5:
            versiones.append(dict(zip(("commit", "corto", "autor", "fecha", "mensaje"), campos)))
    return versiones


def actualizar_historial(proyecto):
    """Fetch: actualiza referencias remotas, sin pull, checkout ni commits."""
    ruta = proyecto["path"]
    codigo, salida = git(["remote"], ruta)
    remotos = salida.split() if codigo == 0 else []
    if not remotos:
        aviso("Este proyecto no tiene un remoto configurado. Puedes consultar su historial local.")
        return None
    remoto = "origin" if "origin" in remotos else remotos[0]
    args = ["git", "fetch", "--no-tags"]
    if git(["rev-parse", "--is-shallow-repository"], ruta)[1].strip() == "true":
        args.append("--deepen=50")
    say("Descargando historial de {} (sin mezclar archivos)...".format(texto_terminal(remoto)))
    if run_live(args + [remoto], cwd=ruta) != 0:
        aviso("No se pudo actualizar. El historial ya descargado sigue disponible.")
        return None
    codigo, seguimiento = git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], ruta)
    if codigo == 0 and seguimiento.startswith(remoto + "/"):
        return seguimiento.strip()
    codigo, rama = git(["symbolic-ref", "--quiet", "--short", "HEAD"], ruta)
    if codigo == 0:
        referencia = "refs/remotes/{}/{}".format(remoto, rama.strip())
        if git(["rev-parse", "--verify", referencia + "^{commit}"], ruta)[0] == 0:
            return referencia
    aviso("La rama actual no tiene una version remota equivalente; se conserva la vista local.")
    return None


def exportar_version(proyecto, revision):
    """Exporta un commit a una carpeta nueva fuera del arbol de trabajo."""
    ruta = Path(proyecto["path"]).resolve()
    codigo, commit = git(["rev-parse", "--verify", "--end-of-options", revision + "^{commit}"], ruta)
    commit = commit.strip()
    if codigo != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        fallo("No se encontro ese commit. Actualiza el historial o revisa el identificador.")
        return None
    base = APP_DIR / "versiones"
    try:
        base.resolve().relative_to(ruta)
    except ValueError:
        pass
    else:
        base = Path(tempfile.gettempdir()) / "OVK-GD-versiones"
    try:
        # Rechaza una ubicacion de copias que pudiera quedar dentro del proyecto.
        try:
            base.resolve().relative_to(ruta)
        except ValueError:
            pass
        else:
            fallo("No es posible crear una copia historica fuera de esta carpeta. Elige un proyecto mas especifico.")
            return None
        base.mkdir(parents=True, exist_ok=True)
        prefijo = "{}-{}-".format(nombre_seguro(proyecto["name"])[:40], commit[:10])
        destino = Path(tempfile.mkdtemp(prefix=prefijo, dir=str(base)))
        archivo = destino / "fuente.zip"
        codigo, salida = git(["archive", "--format=zip", "--output=" + str(archivo), commit], ruta)
        if codigo != 0:
            fallo("No se pudo exportar el commit:\n" + salida)
            return None
        fuente = destino / "fuente"
        fuente.mkdir()
        with zipfile.ZipFile(archivo) as paquete:
            for item in paquete.infolist():
                partes = PurePosixPath(item.filename).parts
                if (PurePosixPath(item.filename).is_absolute() or ".." in partes
                        or "\\" in item.filename or any(":" in p for p in partes)):
                    raise ValueError("Ruta no compatible en el commit: " + repr(item.filename))
                (fuente / item.filename).resolve().relative_to(fuente.resolve())
            paquete.extractall(fuente)
        archivo.unlink()
        version = listar_versiones(proyecto, referencia=commit)[0]
        version["proyecto"] = proyecto["name"]
        version["exportado"] = datetime.datetime.now().astimezone().isoformat()
        (destino / "version.json").write_text(json.dumps(version, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"path": str(fuente), "name": "{} @ {}".format(proyecto["name"], commit[:10]),
                "commit": commit, "destino": str(destino)}
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        fallo("No se pudo preparar la copia historica: {}".format(e))
        return None


def descargar_version(proyecto, revision, destino=None, usar_principal=False):
    """Crea una copia Git independiente en el commit elegido, en una rama propia."""
    ruta = Path(proyecto["path"]).resolve()
    codigo, commit = git(["rev-parse", "--verify", "--end-of-options", revision + "^{commit}"], ruta)
    commit = commit.strip()
    if codigo != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        fallo("No se encontro ese commit. Actualiza el historial y vuelve a intentarlo.")
        return None
    if destino is None:
        sugerido = BASE_PROYECTOS / (nombre_seguro(proyecto["name"])[:60] + "-" + commit[:10])
        destino = ask("Carpeta NUEVA donde guardar la version (0 para cancelar)", str(sugerido))
        if destino == "0":
            return None
    try:
        destino = Path(destino).expanduser().resolve()
        if destino.exists():
            fallo("La carpeta de destino ya existe. Elige otra para conservar su contenido.")
            return None
        try:
            destino.relative_to(ruta)
        except ValueError:
            pass
        else:
            fallo("Elige una carpeta fuera del proyecto de origen.")
            return None
        destino.parent.mkdir(parents=True, exist_ok=True)
        say("Guardando una copia independiente de {} en {}...".format(commit[:10], destino))
        if run_live(["git", "clone", "--no-hardlinks", "--no-checkout", "--", str(ruta), str(destino)]) != 0:
            fallo("No se pudo crear la copia. Revisa el mensaje y la carpeta de destino.")
            return None

        def preparar(args):
            codigo, salida = git(args, destino)
            if codigo != 0:
                raise ValueError("Git no pudo preparar la copia:\n" + salida)

        # El clon local no debe conservar un remoto que apunte al proyecto de origen.
        preparar(["remote", "remove", "origin"])
        codigo, nombres = git(["remote"], ruta)
        remotos = nombres.split() if codigo == 0 else []
        if remotos:
            remoto = "origin" if "origin" in remotos else remotos[0]
            codigo, url = git(["remote", "get-url", remoto], ruta)
            if codigo != 0:
                raise ValueError("No se pudo leer el remoto del proyecto de origen.")

            def resolver_url(valor):
                valor = valor.strip()
                if "://" not in valor and not re.match(r"^[^/\\]+:", valor):
                    local = Path(valor).expanduser()
                    if not local.is_absolute():
                        local = ruta / local
                    if local.exists():
                        return str(local.resolve())
                return valor

            preparar(["remote", "add", "origin", resolver_url(url)])
            codigo, push_url = git(["remote", "get-url", "--push", remoto], ruta)
            if codigo == 0 and push_url.strip() != url.strip():
                preparar(["remote", "set-url", "--push", "origin", resolver_url(push_url)])
        if git(["cat-file", "-e", commit + "^{commit}"], destino)[0] != 0:
            preparar(["fetch", "--no-tags", str(ruta), commit])
        rama = "ovk-version-{}-{}".format(commit[:10], uuid.uuid4().hex[:8])
        preparar(["checkout", "-b", rama, commit])
        copia = {"name": "{} @ {}".format(proyecto["name"], commit[:10]),
                 "path": str(destino), "commit": commit, "rama": rama}
        guardar_datos_proyecto(copia)
        registrar_proyecto(copia["name"], destino)
        ok("Version guardada en: {}".format(destino))
        say("  Puedes editarla y compilarla. Se conserva su historial Git.")
        say("  La sincronizacion de esta copia utiliza la rama {}.".format(rama))
        copia["principal_establecido"] = False
        if usar_principal:
            copia["principal_establecido"] = establecer_proyecto_principal(copia)
        else:
            say("  Usa la opcion 10 para elegir esta copia como proyecto principal.")
        return copia
    except (OSError, ValueError) as e:
        fallo("No se pudo terminar la descarga: {}".format(e))
        if "destino" in locals():
            say("  Destino solicitado: {}".format(destino))
        return None


def acciones_version(proyecto, version):
    while True:
        titulo("Version del documento: {}".format(version["corto"]))
        say("{} | {}".format(texto_terminal(version["autor"]), version["fecha"]))
        say(texto_terminal(version["mensaje"]))
        say("\n 1) Compilar y ver su PDF")
        say(" 2) Descargar esta version a una carpeta local")
        say(" 3) Descargar y usar como proyecto principal de compilacion")
        say(" 0) Volver al historial")
        opcion = ask("Elige una opcion", "0")
        if opcion == "0":
            return False
        if opcion == "1":
            compilar_version(proyecto, version["commit"])
            pausa()
        elif opcion in ("2", "3"):
            copia = descargar_version(proyecto, version["commit"], usar_principal=opcion == "3")
            if copia and copia.get("principal_establecido"):
                return True
            pausa()
        else:
            aviso("Opcion no valida.")


def compilar_version(proyecto, revision):
    """Genera un PDF identificado por commit; no modifica HEAD, indice ni archivos actuales."""
    refresh_path()
    if not shutil.which("latexmk"):
        fallo("Falta latexmk. Instala las herramientas antes de compilar una version anterior.")
        return False
    copia = exportar_version(proyecto, revision)
    if not copia:
        return False
    principal = detectar_principal(copia["path"])
    if not principal:
        fallo("Este commit no contiene un archivo principal LaTeX con \\documentclass.")
        say("Copia conservada en: " + copia["destino"])
        return False
    say("Version: {} | Fuentes: {}".format(copia["commit"][:10], copia["path"]))
    if not compilar(copia, abrir=False, principal=principal):
        aviso("Revisa los errores de esa version. Las fuentes y registros quedan en: " + copia["destino"])
        return False
    try:
        pdf_origen = (Path(copia["path"]) / principal).with_suffix(".pdf")
        nombre = "OVK-GD_{}_{}.pdf".format(nombre_seguro(proyecto["name"])[:60], copia["commit"][:10])
        pdf = Path(copia["destino"]) / nombre
        shutil.copy2(pdf_origen, pdf)
        ok("PDF historico generado: {}".format(pdf))
        abrir_archivo(pdf)
        return True
    except OSError as e:
        fallo("No se pudo copiar el PDF historico: {}".format(e))
        return False


def historial(proyecto, cantidad=10, actualizar=False):
    if not shutil.which("git"):
        fallo("Git no esta instalado. Ejecuta primero 'Instalar herramientas'.")
        return
    referencia = actualizar_historial(proyecto) if actualizar else None
    referencia = referencia or "HEAD"
    cantidad = max(6, cantidad)
    while True:
        titulo("Versiones y PDF: {}".format(proyecto["name"]))
        say("Historial de: {} | Maximo {} commits".format(texto_terminal(referencia), cantidad))
        versiones = listar_versiones(proyecto, cantidad, referencia)
        actual = cabeza(proyecto["path"])
        for i, version in enumerate(versiones, 1):
            marca = " [HEAD local]" if version["commit"] == actual else ""
            say("\n  {}) {}{}  {}".format(i, version["corto"], marca, texto_terminal(version["mensaje"])))
            say("     Autor: {} | Fecha: {}".format(texto_terminal(version["autor"]), version["fecha"]))
        if len(versiones) < 6:
            aviso("Hay menos de 6 commits disponibles. Se muestran todos los encontrados.")
        say("\nEscribe el NUMERO del commit para ver su PDF, descargarlo o usarlo como principal.")
        say(" M) Mostrar 10 commits mas")
        say(" R) Actualizar desde GitHub/GitLab y ver la rama remota")
        say(" L) Ver el historial de la rama local")
        say(" 0) Volver")
        opcion = ask("Elige una opcion", "0").lower()
        if opcion == "0":
            return
        if opcion == "m":
            cantidad += 10
        elif opcion == "r":
            nueva = actualizar_historial(proyecto)
            if nueva:
                referencia = nueva
        elif opcion == "l":
            referencia = "HEAD"
        elif opcion.isdigit() and 1 <= int(opcion) <= len(versiones):
            if acciones_version(proyecto, versiones[int(opcion) - 1]):
                return
        else:
            aviso("Opcion no valida.")


# ---------------------------------------------------------------------------
# Menu y linea de comandos
# ---------------------------------------------------------------------------
def con_proyecto(funcion):
    proyecto = elegir_proyecto()
    if proyecto:
        funcion(proyecto)


def menu():
    refresh_path()
    acciones = {
        "1": lambda: instalar(False),
        "2": lambda: instalar(True),
        "3": abrir_proyecto_local,
        "4": lambda: con_proyecto(sincronizar),
        "5": lambda: con_proyecto(compilar),
        "6": lambda: con_proyecto(abrir_vscode),
        "7": lambda: con_proyecto(sincronizacion_automatica),
        "8": diagnostico,
        "9": lambda: con_proyecto(historial),
        "10": seleccionar_principal,
        "11": configurar_proyecto,
    }
    while True:
        titulo("LaTeX en equipo")
        principal = obtener_proyecto_principal()
        if principal:
            say(" Principal: {} | {}".format(principal["name"], principal["main"]))
            say(" Carpeta: {}\n".format(principal["path"]))
            if principal.get("url"):
                say(" URL: {}\n".format(principal["url"]))
        else:
            say(" Proyecto principal: sin seleccionar (opcion 10).\n")
        say(" 1) Instalar herramientas (primera vez)")
        say(" 2) Actualizar herramientas")
        say(" 3) Abrir un proyecto desde una carpeta de la PC")
        say(" 4) Sincronizar proyecto (guardar, descargar y subir cambios)")
        say(" 5) Compilar PDF")
        say(" 6) Abrir proyecto en VS Code")
        say(" 7) Sincronizacion automatica cada cierto tiempo")
        say(" 8) Diagnostico (¿esta todo instalado?)")
        say(" 9) Historial: PDF, descargar versiones y elegir principal")
        say("10) Elegir proyecto y archivo principal de compilacion")
        say("11) Crear un proyecto nuevo o descargar de GitHub")
        say(" 0) Salir")
        eleccion = ask("\nElige una opcion", "").strip()
        if eleccion == "0":
            say("Hasta luego.")
            return
        accion = acciones.get(eleccion)
        if not accion:
            say("Opcion no valida.")
            continue
        try:
            accion()
        except KeyboardInterrupt:
            say("\nCancelado.")
        pausa()


def main():
    global SIMULAR
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    if SYSTEM == "Windows":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("{} - {}".format(APP_NAME, AUTHOR))
        except (AttributeError, OSError):
            pass
    elif sys.stdout.isatty():
        print("\033]0;{} - {}\007".format(APP_NAME, AUTHOR), end="", flush=True)

    parser = argparse.ArgumentParser(description="{} | {}. Compilacion LaTeX local y colaboracion con Git.".format(APP_NAME, AUTHOR))
    parser.add_argument("--simular", action="store_true",
                        help="muestra los comandos de instalacion sin ejecutarlos")
    sub = parser.add_subparsers(dest="comando")
    sub.add_parser("instalar")
    sub.add_parser("actualizar")
    sub.add_parser("proyecto")
    a = sub.add_parser("abrir", help="abrir una carpeta o un archivo de proyecto local")
    a.add_argument("ruta", nargs="?", help="carpeta, archivo .tex o archivo de proyecto")
    s = sub.add_parser("sincronizar")
    s.add_argument("--mensaje", "-m", help="descripcion de tus cambios")
    s.add_argument("--auto", action="store_true", help="sin preguntas (para tareas automaticas)")
    sub.add_parser("compilar")
    sub.add_parser("auto")
    sub.add_parser("diagnostico")
    h = sub.add_parser("historial", help="consultar commits y compilar versiones anteriores")
    h.add_argument("--cantidad", type=int, default=10, help="commits a mostrar (minimo 6)")
    h.add_argument("--actualizar", action="store_true", help="descargar referencias remotas sin mezclar archivos")
    c = sub.add_parser("compilar-version", help="compilar un commit en una copia independiente")
    c.add_argument("commit", help="identificador del commit guardado en Git")
    d = sub.add_parser("descargar-version", help="guardar un commit como proyecto local independiente")
    d.add_argument("commit", help="identificador del commit")
    d.add_argument("--destino", help="carpeta nueva donde guardar la copia")
    d.add_argument("--principal", action="store_true", help="usar la copia para las compilaciones habituales")
    sub.add_parser("principal", help="elegir proyecto y archivo principal de compilacion")
    args = parser.parse_args()
    SIMULAR = args.simular

    if not args.comando:
        menu()
        return 0

    refresh_path()
    if args.comando == "instalar":
        instalar(False)
    elif args.comando == "actualizar":
        instalar(True)
    elif args.comando == "proyecto":
        configurar_proyecto()
    elif args.comando == "abrir":
        return 0 if abrir_proyecto_local(args.ruta) else 1
    elif args.comando == "diagnostico":
        diagnostico()
    elif args.comando == "principal":
        return 0 if seleccionar_principal() else 1
    else:
        proyecto = elegir_proyecto()
        if not proyecto:
            return 1
        if args.comando == "sincronizar":
            return 0 if sincronizar(proyecto, auto=args.auto, mensaje=args.mensaje) else 1
        if args.comando == "compilar":
            return 0 if compilar(proyecto) else 1
        if args.comando == "historial":
            historial(proyecto, args.cantidad, args.actualizar)
        if args.comando == "compilar-version":
            return 0 if compilar_version(proyecto, args.commit) else 1
        if args.comando == "descargar-version":
            copia = descargar_version(proyecto, args.commit, args.destino, args.principal)
            return 0 if copia and (not args.principal or copia.get("principal_establecido")) else 1
        if args.comando == "auto":
            sincronizacion_automatica(proyecto)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(130)
