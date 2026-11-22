"""Pruebas locales: no usan GitHub ni instalan herramientas."""
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("ovk_gd", Path(__file__).resolve().parents[1] / "OVK-GD.py")
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)


class TemporaryProject(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ovk_gd test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        config_patch = mock.patch.multiple(
            kit, APP_DIR=self.root / "config",
            CONFIG_FILE=self.root / "config" / "proyectos.json",
            BASE_PROYECTOS=self.root / "proyectos predeterminados",
        )
        config_patch.start()
        self.addCleanup(config_patch.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)


class ProjectTests(TemporaryProject):
    def test_registration_updates_existing_path(self):
        kit.registrar_proyecto("primero", self.root)
        kit.registrar_proyecto("renombrado", self.root)
        projects = kit.cargar_proyectos()
        self.assertEqual(projects, [{"name": "renombrado", "path": str(self.root)}])
        self.assertEqual(json.loads(kit.CONFIG_FILE.read_text(encoding="utf-8")), projects)

    def test_existing_settings_are_preserved(self):
        settings = self.root / ".vscode" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"editor.fontSize": 18}', encoding="utf-8")
        kit.crear_archivos_base(self.root)
        self.assertEqual(settings.read_text(encoding="utf-8"), '{"editor.fontSize": 18}')
        self.assertTrue((self.root / ".gitignore").exists())

    def test_detects_nested_main_and_ignores_hidden_directories(self):
        hidden = self.root / ".cache"
        hidden.mkdir()
        (hidden / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        document = self.root / "documento"
        document.mkdir()
        (document / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        self.assertEqual(Path(kit.detectar_principal(self.root)), Path("documento/main.tex"))

    def test_principal_selection_is_persistent_and_uses_selected_tex(self):
        project = self.root / "documento"
        project.mkdir()
        (project / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        alternate = project / "articulo.tex"
        alternate.write_text(kit.PLANTILLA_TEX.replace("Título del documento", "Articulo seleccionado"), encoding="utf-8")
        self.assertTrue(kit.establecer_proyecto_principal({"name": "documento", "path": str(project)}, "articulo.tex"))
        saved = json.loads((kit.APP_DIR / "principal.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["main"], "articulo.tex")
        with mock.patch.object(kit, "ask", side_effect=AssertionError("No debe volver a preguntar el proyecto")):
            selected = kit.elegir_proyecto()
        self.assertEqual(selected, saved)

        def fake_latexmk(cmd, cwd=None, env=None):
            source = Path(cwd) / cmd[-1]
            source.with_suffix(".pdf").write_bytes(b"%PDF-1.4\n" + source.read_bytes())
            return 0

        with mock.patch.object(kit.shutil, "which", return_value="latexmk"), \
                mock.patch.object(kit, "run_live", side_effect=fake_latexmk), \
                mock.patch.object(kit, "abrir_archivo"):
            self.assertTrue(kit.compilar(kit.obtener_proyecto_principal()))
        self.assertIn(b"Articulo seleccionado", alternate.with_suffix(".pdf").read_bytes())
        self.assertFalse((project / "main.pdf").exists())

    def test_principal_cannot_be_selected_outside_project(self):
        project = self.root / "documento"
        project.mkdir()
        (self.root / "externo.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        self.assertFalse(kit.establecer_proyecto_principal({"name": "documento", "path": str(project)}, "../externo.tex"))
        self.assertIsNone(kit.obtener_proyecto_principal())

    def test_open_local_folder_does_not_clone_or_ask_for_url(self):
        project = self.root / "mi documento local"
        project.mkdir()
        (project / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        with mock.patch.object(kit, "ask", side_effect=AssertionError("No debe pedir URL")), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe clonar")):
            opened = kit.abrir_proyecto_local('"{}"'.format(project))
        self.assertEqual(opened["path"], str(project))
        self.assertEqual(opened["main"], "main.tex")
        self.assertFalse((project / ".git").exists())
        self.assertFalse(kit.BASE_PROYECTOS.exists())
        saved = json.loads((project / kit.PROJECT_FILE_NAME).read_text(encoding="utf-8"))
        self.assertEqual(saved["url"], "")

    def test_open_manifest_reuses_saved_url_and_tex_after_restart(self):
        project = self.root / "carpeta elegida"
        project.mkdir()
        for filename in ("main.tex", "principal.tex"):
            (project / filename).write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        config = {"name": "tesis", "url": "https://github.com/equipo/tesis.git",
                  "remote": "origin", "main": "principal.tex"}
        manifest = project / kit.PROJECT_FILE_NAME
        manifest.write_text(json.dumps(config), encoding="utf-8")
        elsewhere = self.root / "lanzador en otra carpeta"
        elsewhere.mkdir()
        previous_cwd = Path.cwd()
        try:
            os.chdir(elsewhere)
            with mock.patch.object(kit, "ask", side_effect=AssertionError("La URL y el tex ya estan guardados")), \
                    mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe descargar")):
                opened = kit.abrir_proyecto_local(manifest)
                reopened = kit.abrir_proyecto_local(project)
        finally:
            os.chdir(previous_cwd)
        self.assertEqual(opened, reopened)
        self.assertEqual(reopened["url"], config["url"])
        self.assertEqual(reopened["main"], "principal.tex")
        self.assertEqual(reopened["path"], str(project))

    def test_open_missing_folder_does_not_create_it(self):
        missing = self.root / "ubicacion inexistente"
        with mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe descargar")):
            self.assertIsNone(kit.abrir_proyecto_local(missing))
        self.assertFalse(missing.exists())
        self.assertFalse(kit.BASE_PROYECTOS.exists())

    def test_open_invalid_manifest_preserves_file_and_current_selection(self):
        valid = self.root / "seleccion actual"
        valid.mkdir()
        (valid / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        self.assertTrue(kit.establecer_proyecto_principal({"name": "actual", "path": str(valid)}))
        before = kit.obtener_proyecto_principal()
        invalid = self.root / "configuracion rota"
        invalid.mkdir()
        (invalid / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        manifest = invalid / kit.PROJECT_FILE_NAME
        manifest.write_text('{"url":', encoding="utf-8")
        self.assertIsNone(kit.abrir_proyecto_local(invalid))
        self.assertEqual(manifest.read_text(encoding="utf-8"), '{"url":')
        self.assertEqual(kit.obtener_proyecto_principal(), before)

    def test_menu_option_three_opens_local_folder(self):
        project = self.root / "documento del menu"
        project.mkdir()
        (project / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        with mock.patch.object(kit, "ask", side_effect=["3", str(project), "0"]), \
                mock.patch.object(kit, "pausa"), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("La opcion 3 no descarga")):
            kit.menu()
        self.assertEqual(kit.obtener_proyecto_principal()["path"], str(project))

    def test_saved_tex_path_can_be_shared_between_platforms(self):
        project = self.root / "proyecto compartido"
        nested = project / "capitulos"
        nested.mkdir(parents=True)
        (nested / "principal.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        (project / kit.PROJECT_FILE_NAME).write_text(json.dumps({
            "name": "tesis", "url": "", "remote": "origin", "main": "capitulos\\principal.tex"
        }), encoding="utf-8")
        with mock.patch.object(kit, "ask", side_effect=AssertionError("El principal ya esta guardado")):
            opened = kit.abrir_proyecto_local(project)
        self.assertEqual(Path(opened["main"]), Path("capitulos/principal.tex"))
        self.assertEqual(kit.leer_datos_proyecto(project)["main"], "capitulos/principal.tex")


@unittest.skipUnless(shutil.which("git"), "Git no esta disponible")
class GitTests(TemporaryProject):
    def setUp(self):
        super().setUp()
        self.env_patch = mock.patch.dict(os.environ, {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.root / "empty.gitconfig"),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_MERGE_AUTOEDIT": "no",
            "GIT_AUTHOR_NAME": "Prueba OVK-GD",
            "GIT_AUTHOR_EMAIL": "prueba@example.invalid",
            "GIT_COMMITTER_NAME": "Prueba OVK-GD",
            "GIT_COMMITTER_EMAIL": "prueba@example.invalid",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.remote = self.root / "remoto.git"
        self.command(["git", "init", "--bare", "--initial-branch=main", str(self.remote)])
        self.a = self.root / "persona a"
        self.clone(self.a)

    def command(self, args, cwd=None):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def clone(self, destination):
        self.command(["git", "clone", str(self.remote), str(destination)])
        for key, value in (("user.name", "Prueba OVK-GD"),
                           ("user.email", "prueba@example.invalid"),
                           ("core.autocrlf", "false"),
                           ("commit.gpgsign", "false")):
            self.command(["git", "config", key, value], cwd=destination)

    def sync(self, folder):
        return kit.sincronizar({"name": folder.name, "path": str(folder)},
                               auto=True, mensaje="Prueba local")

    def seed(self):
        (self.a / "capitulo.tex").write_text("Texto inicial\n", encoding="utf-8")
        self.assertTrue(self.sync(self.a))

    def test_first_push_and_second_clone(self):
        self.seed()
        second = self.root / "persona b"
        self.clone(second)
        self.assertEqual((second / "capitulo.tex").read_text(encoding="utf-8"), "Texto inicial\n")
        self.assertEqual(self.command(["git", "status", "--porcelain"], self.a), "")

    def test_two_people_merge_different_files(self):
        self.seed()
        second = self.root / "persona b"
        self.clone(second)
        (self.a / "introduccion.tex").write_text("Introduccion\n", encoding="utf-8")
        (second / "metodologia.tex").write_text("Metodologia\n", encoding="utf-8")
        self.assertTrue(self.sync(self.a))
        self.assertTrue(self.sync(second))
        self.assertTrue(self.sync(self.a))
        self.assertTrue((self.a / "metodologia.tex").exists())
        self.assertTrue((second / "introduccion.tex").exists())
        self.assertEqual(kit.cabeza(self.a), kit.cabeza(second))

    def test_auto_conflict_aborts_merge_and_keeps_both_histories(self):
        self.seed()
        second = self.root / "persona b"
        self.clone(second)
        (self.a / "capitulo.tex").write_text("Cambio de A\n", encoding="utf-8")
        self.assertTrue(self.sync(self.a))
        (second / "capitulo.tex").write_text("Cambio de B\n", encoding="utf-8")
        self.assertFalse(self.sync(second))
        self.assertFalse((second / ".git" / "MERGE_HEAD").exists())
        self.assertEqual((second / "capitulo.tex").read_text(encoding="utf-8"), "Cambio de B\n")
        self.assertEqual(self.command(["git", "show", "origin/main:capitulo.tex"], second), "Cambio de A")
        self.assertEqual(self.command(["git", "status", "--porcelain"], second), "")

    def test_manual_conflict_can_choose_other_version(self):
        self.seed()
        second = self.root / "persona b"
        self.clone(second)
        (self.a / "capitulo.tex").write_text("Cambio de A\n", encoding="utf-8")
        self.assertTrue(self.sync(self.a))
        (second / "capitulo.tex").write_text("Cambio de B\n", encoding="utf-8")
        with mock.patch.object(kit, "ask", return_value="2"):
            self.assertTrue(kit.sincronizar({"name": "B", "path": str(second)}, mensaje="Cambio de B"))
        self.assertEqual((second / "capitulo.tex").read_text(encoding="utf-8"), "Cambio de A\n")

    def test_failed_commit_stops_before_network(self):
        self.seed()
        original_head = kit.cabeza(self.a)
        (self.a / "capitulo.tex").write_text("No confirmado\n", encoding="utf-8")
        hook = self.a / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        with mock.patch.object(kit, "run_live") as live:
            self.assertFalse(self.sync(self.a))
            live.assert_not_called()
        self.assertEqual(kit.cabeza(self.a), original_head)
        self.assertEqual((self.a / "capitulo.tex").read_text(encoding="utf-8"), "No confirmado\n")

    def test_unreachable_remote_keeps_local_commit(self):
        (self.a / "capitulo.tex").write_text("Disponible sin conexion\n", encoding="utf-8")
        self.command(["git", "remote", "set-url", "origin", str(self.root / "inexistente.git")], self.a)
        self.assertFalse(self.sync(self.a))
        self.assertTrue(kit.tiene_commits(self.a))
        self.assertEqual(self.command(["git", "status", "--porcelain"], self.a), "")

    def test_large_file_is_excluded_from_first_commit(self):
        (self.a / "capitulo.tex").write_text("Texto\n", encoding="utf-8")
        (self.a / "grande.bin").write_bytes(b"x" * (1024 * 1024 + 1))
        with mock.patch.object(kit, "LIMITE_ARCHIVO_MB", 1):
            self.assertTrue(self.sync(self.a))
        tracked = self.command(["git", "ls-files"], self.a).splitlines()
        self.assertIn("capitulo.tex", tracked)
        self.assertNotIn("grande.bin", tracked)
        self.assertTrue((self.a / "grande.bin").exists())

    def make_history(self, count=8):
        revisions = []
        for i in range(count):
            content = ("\\documentclass{article}\n\\begin{document}\n"
                       "Version %d.\\input{seccion}\n\\end{document}\n") % i
            (self.a / "main.tex").write_text(content, encoding="utf-8")
            (self.a / "seccion.tex").write_text("Seccion %d.\n" % i, encoding="utf-8")
            self.command(["git", "add", "."], self.a)
            author = "Ana Perez <ana@example.invalid>" if i % 2 else "Gerardo Diaz <gd@example.invalid>"
            self.command(["git", "commit", "--author", author, "-m", "Revision %d" % i], self.a)
            revisions.append(kit.cabeza(self.a))
        return revisions

    def state(self, folder):
        return (kit.cabeza(folder),
                self.command(["git", "symbolic-ref", "HEAD"], folder),
                self.command(["git", "status", "--porcelain=v1", "--untracked-files=all"], folder),
                self.command(["git", "show", ":main.tex"], folder))

    def test_history_shows_current_plus_at_least_five_previous_with_authors(self):
        commits = self.make_history()
        versions = kit.listar_versiones({"path": str(self.a)})
        self.assertEqual([v["commit"] for v in versions], list(reversed(commits)))
        self.assertEqual(versions[0]["autor"], "Ana Perez")
        self.assertEqual(versions[1]["autor"], "Gerardo Diaz")
        self.assertEqual(versions[0]["mensaje"], "Revision 7")
        self.assertTrue(versions[0]["fecha"])
        self.assertEqual(len(kit.listar_versiones({"path": str(self.a)}, cantidad=1)), 6)

    def test_export_old_revision_preserves_staged_dirty_and_untracked_files(self):
        commits = self.make_history()
        original = (self.a / "main.tex").read_bytes()
        (self.a / "main.tex").write_text("Cambio preparado\n", encoding="utf-8")
        self.command(["git", "add", "main.tex"], self.a)
        (self.a / "main.tex").write_text("Cambio aun no preparado\n", encoding="utf-8")
        (self.a / "privado.txt").write_text("No versionado\n", encoding="utf-8")
        before = self.state(self.a)
        copy = kit.exportar_version({"name": "tesis", "path": str(self.a)}, commits[1])
        self.assertIsNotNone(copy)
        self.assertIn("Version 1.", (Path(copy["path"]) / "main.tex").read_text())
        self.assertFalse((Path(copy["path"]) / "privado.txt").exists())
        self.assertNotEqual((Path(copy["path"]) / "main.tex").read_bytes(), original)
        metadata = json.loads((Path(copy["destino"]) / "version.json").read_text())
        self.assertEqual(metadata["commit"], commits[1])
        self.assertEqual(metadata["autor"], "Ana Perez")
        self.assertEqual(self.state(self.a), before)
        self.assertEqual((self.a / "main.tex").read_text(), "Cambio aun no preparado\n")

    def test_historical_pdf_keeps_commit_in_name_and_uses_old_sources(self):
        commits = self.make_history()
        before = self.state(self.a)

        def fake_compile(project, abrir=True, principal=None):
            source = Path(project["path"]) / principal
            self.assertIn("Version 2.", source.read_text())
            self.assertFalse(abrir)
            source.with_suffix(".pdf").write_bytes(b"%PDF-1.4\nTest double for historical compilation\n")
            return True

        with mock.patch.object(kit.shutil, "which", return_value="latexmk"), \
                mock.patch.object(kit, "compilar", side_effect=fake_compile), \
                mock.patch.object(kit, "abrir_archivo") as viewer:
            self.assertTrue(kit.compilar_version({"name": "tesis", "path": str(self.a)}, commits[2]))
        pdf = viewer.call_args[0][0]
        self.assertTrue(pdf.exists())
        self.assertIn(commits[2][:10], pdf.name)
        self.assertEqual(pdf.parent.parent, kit.APP_DIR / "versiones")
        self.assertEqual(self.state(self.a), before)

    def test_historical_compile_failure_keeps_sources_and_current_branch(self):
        commits = self.make_history()
        before = self.state(self.a)
        with mock.patch.object(kit.shutil, "which", return_value="latexmk"), \
                mock.patch.object(kit, "compilar", return_value=False), \
                mock.patch.object(kit, "abrir_archivo") as viewer:
            self.assertFalse(kit.compilar_version({"name": "tesis", "path": str(self.a)}, commits[0]))
        viewer.assert_not_called()
        self.assertEqual(self.state(self.a), before)
        self.assertEqual(len(list((kit.APP_DIR / "versiones").glob("*/version.json"))), 1)

    def test_invalid_commit_is_rejected_without_touching_current_project(self):
        self.make_history(2)
        before = self.state(self.a)
        self.assertIsNone(kit.exportar_version({"name": "tesis", "path": str(self.a)}, "--help"))
        self.assertEqual(self.state(self.a), before)

    def test_remote_history_fetch_keeps_local_branch_and_work_in_progress(self):
        self.make_history(6)
        self.command(["git", "push", "-u", "origin", "main"], self.a)
        second = self.root / "persona b"
        self.clone(second)
        (second / "main.tex").write_text("Trabajo sin guardar en Git\n", encoding="utf-8")
        before = self.state(second)
        (self.a / "main.tex").write_text("Version remota mas reciente\n", encoding="utf-8")
        self.command(["git", "add", "."], self.a)
        self.command(["git", "commit", "-m", "Cambio de la otra persona"], self.a)
        self.command(["git", "push"], self.a)
        project = {"name": "tesis", "path": str(second)}
        reference = kit.actualizar_historial(project)
        self.assertTrue(reference)
        versions = kit.listar_versiones(project, referencia=reference)
        self.assertEqual(versions[0]["mensaje"], "Cambio de la otra persona")
        self.assertEqual(self.state(second), before)
        self.assertEqual((second / "main.tex").read_text(), "Trabajo sin guardar en Git\n")

    def test_shallow_clone_fetch_recovers_at_least_five_previous_versions(self):
        self.make_history(8)
        self.command(["git", "push", "-u", "origin", "main"], self.a)
        second = self.root / "copia superficial"
        self.command(["git", "clone", "--depth=1", self.remote.as_uri(), str(second)])
        project = {"name": "tesis", "path": str(second)}
        self.assertEqual(len(kit.listar_versiones(project)), 1)
        head = kit.cabeza(second)
        reference = kit.actualizar_historial(project)
        self.assertTrue(reference)
        self.assertGreaterEqual(len(kit.listar_versiones(project, referencia=reference)), 6)
        self.assertEqual(kit.cabeza(second), head)

    def test_history_menu_selects_a_commit_and_can_return(self):
        commits = self.make_history()
        with mock.patch.object(kit, "ask", side_effect=["2", "1", "0", "0"]), \
                mock.patch.object(kit, "pausa"), mock.patch.object(kit, "compilar_version") as compile_old:
            kit.historial({"name": "tesis", "path": str(self.a)})
        self.assertEqual(compile_old.call_args[0][1], commits[-2])

    def test_download_preserves_dirty_source_and_creates_independent_history(self):
        commits = self.make_history()
        (self.a / "main.tex").write_text("Preparado\n", encoding="utf-8")
        self.command(["git", "add", "main.tex"], self.a)
        (self.a / "main.tex").write_text("Trabajo sin commit\n", encoding="utf-8")
        (self.a / "privado.txt").write_text("Solo en el original\n", encoding="utf-8")
        before = self.state(self.a)
        destination = self.root / "version descargada"
        project = {"name": "tesis", "path": str(self.a)}
        with mock.patch.object(kit, "compilar") as compile_pdf:
            copy = kit.descargar_version(project, commits[2], destination)
        self.assertIsNotNone(copy)
        compile_pdf.assert_not_called()
        self.assertEqual(kit.cabeza(destination), commits[2])
        self.assertIn("Version 2.", (destination / "main.tex").read_text())
        self.assertEqual((destination / "seccion.tex").read_text(), "Seccion 2.\n")
        self.assertFalse((destination / "privado.txt").exists())
        self.assertEqual(self.state(self.a), before)
        self.assertEqual((self.a / "main.tex").read_text(), "Trabajo sin commit\n")
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], destination), str(self.remote))
        self.assertTrue(self.command(["git", "branch", "--show-current"], destination).startswith("ovk-version-"))
        self.a.rename(self.root / "origen movido")
        self.assertEqual(kit.cabeza(destination), commits[2])
        self.assertEqual(len(kit.listar_versiones(copy)), 3)

    def test_download_can_be_main_and_switch_back_to_original(self):
        commits = self.make_history()
        original = {"name": "tesis", "path": str(self.a)}
        kit.registrar_proyecto(original["name"], self.a)
        self.assertTrue(kit.establecer_proyecto_principal(original))
        destination = self.root / "version principal"
        copy = kit.descargar_version(original, commits[1], destination, usar_principal=True)
        self.assertTrue(copy["principal_establecido"])
        self.assertEqual(kit.elegir_proyecto()["path"], str(destination))
        self.assertEqual(kit.obtener_proyecto_principal()["main"], "main.tex")
        self.assertTrue((kit.APP_DIR / "principal.json").exists())
        with mock.patch.object(kit, "ask", return_value="1"):
            self.assertTrue(kit.seleccionar_principal())
        self.assertEqual(kit.elegir_proyecto()["path"], str(self.a))
        self.assertEqual(kit.cabeza(self.a), commits[-1])

    def test_download_does_not_replace_existing_destination(self):
        commits = self.make_history(2)
        destination = self.root / "ya existe"
        destination.mkdir()
        marker = destination / "importante.txt"
        marker.write_text("Conservar\n", encoding="utf-8")
        before = self.state(self.a)
        self.assertIsNone(kit.descargar_version({"name": "tesis", "path": str(self.a)}, commits[0], destination))
        self.assertEqual(marker.read_text(), "Conservar\n")
        self.assertEqual(self.state(self.a), before)

    def test_download_rejects_destination_inside_source(self):
        commits = self.make_history(2)
        destination = self.a / "copia"
        self.assertIsNone(kit.descargar_version({"name": "tesis", "path": str(self.a)}, commits[0], destination))
        self.assertFalse(destination.exists())

    def test_download_invalid_commit_keeps_main_selection(self):
        self.make_history(2)
        project = {"name": "tesis", "path": str(self.a)}
        self.assertTrue(kit.establecer_proyecto_principal(project))
        selected = kit.obtener_proyecto_principal()
        destination = self.root / "fallida"
        self.assertIsNone(kit.descargar_version(project, "--help", destination, usar_principal=True))
        self.assertFalse(destination.exists())
        self.assertEqual(kit.obtener_proyecto_principal(), selected)

    def test_download_copy_sync_publishes_own_branch_without_changing_main(self):
        commits = self.make_history()
        self.command(["git", "push", "-u", "origin", "main"], self.a)
        destination = self.root / "version para editar"
        copy = kit.descargar_version({"name": "tesis", "path": str(self.a)}, commits[1], destination)
        self.assertIsNotNone(copy)
        self.command(["git", "config", "user.name", "Prueba OVK-GD"], destination)
        self.command(["git", "config", "user.email", "prueba@example.invalid"], destination)
        (destination / "main.tex").write_text("Continuacion de la version elegida\n", encoding="utf-8")
        self.assertTrue(self.sync(destination))
        remote_main = self.command(["git", "rev-parse", "refs/heads/main"], self.remote)
        self.assertEqual(remote_main, commits[-1])
        remote_copy = self.command(["git", "rev-parse", "refs/heads/" + copy["rama"]], self.remote)
        self.assertEqual(remote_copy, kit.cabeza(destination))
        self.assertEqual(kit.cabeza(self.a), commits[-1])

    def test_download_fetched_commit_that_is_not_in_local_head(self):
        self.make_history(3)
        self.command(["git", "push", "-u", "origin", "main"], self.a)
        second = self.root / "otra persona"
        self.clone(second)
        (second / "main.tex").write_text("Commit remoto\n", encoding="utf-8")
        self.command(["git", "add", "."], second)
        self.command(["git", "commit", "-m", "Documento remoto"], second)
        self.command(["git", "push"], second)
        project = {"name": "tesis", "path": str(self.a)}
        reference = kit.actualizar_historial(project)
        revision = kit.listar_versiones(project, referencia=reference)[0]["commit"]
        before = self.state(self.a)
        destination = self.root / "descarga remota"
        self.assertIsNotNone(kit.descargar_version(project, revision, destination))
        self.assertEqual((destination / "main.tex").read_text(), "Commit remoto\n")
        self.assertEqual(self.state(self.a), before)

    def test_history_menu_downloads_and_activates_selected_commit(self):
        commits = self.make_history()
        destination = self.root / "seleccion del menu"
        with mock.patch.object(kit, "ask", side_effect=["2", "3", str(destination)]):
            kit.historial({"name": "tesis", "path": str(self.a)})
        self.assertEqual(kit.obtener_proyecto_principal()["path"], str(destination))
        self.assertEqual(kit.cabeza(destination), commits[-2])

    def test_new_project_saves_url_and_last_folder_for_reopening(self):
        destination = self.root / "nuevo proyecto"
        url = "https://github.com/equipo/tesis.git"
        with mock.patch.object(kit, "ask", side_effect=["2", "tesis", str(destination), url]), \
                mock.patch.object(kit, "ensure_identity", return_value=True), \
                mock.patch.object(kit, "yes", return_value=False), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("Crear no necesita clonar")):
            created = kit.configurar_proyecto()
        self.assertIsNotNone(created)
        saved = kit.leer_datos_proyecto(destination)
        self.assertEqual(saved["url"], url)
        self.assertEqual(saved["main"], "main.tex")
        self.assertEqual(kit.obtener_proyecto_principal()["path"], str(destination))
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], destination), url)
        with mock.patch.object(kit, "ask", side_effect=AssertionError("No debe volver a pedir URL")), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("Abrir no clona")):
            reopened = kit.abrir_proyecto_local(destination)
        self.assertEqual(reopened["url"], url)

    def test_reopening_git_folder_reuses_connection_and_does_not_clone(self):
        commits = self.make_history(3)
        with mock.patch.object(kit, "ask", side_effect=AssertionError("No debe pedir URL")), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe clonar ni hacer pull")):
            opened = kit.abrir_proyecto_local(self.a)
            reopened = kit.abrir_proyecto_local(self.a)
        self.assertEqual(opened["path"], str(self.a))
        self.assertEqual(reopened["url"], str(self.remote))
        self.assertEqual(kit.cabeza(self.a), commits[-1])
        self.assertFalse(kit.BASE_PROYECTOS.exists())
        self.assertEqual(kit.leer_datos_proyecto(self.a)["url"], str(self.remote))

    def test_saved_url_restores_missing_remote_without_network(self):
        self.make_history(3)
        self.assertIsNotNone(kit.abrir_proyecto_local(self.a))
        self.command(["git", "remote", "remove", "origin"], self.a)
        before = self.state(self.a)
        with mock.patch.object(kit, "ask", side_effect=AssertionError("El enlace ya esta guardado")), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe descargar archivos")):
            self.assertIsNotNone(kit.abrir_proyecto_local(self.a))
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], self.a), str(self.remote))
        self.assertEqual(self.state(self.a), before)

    def test_open_moved_folder_uses_selected_location_and_relative_main(self):
        self.make_history(3)
        self.assertIsNotNone(kit.abrir_proyecto_local(self.a))
        moved = self.root / "documentos movidos"
        self.a.rename(moved)
        (kit.APP_DIR / "principal.json").unlink()
        kit.CONFIG_FILE.unlink()
        with mock.patch.object(kit, "ask", side_effect=AssertionError("No debe pedir URL")), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe clonar")):
            opened = kit.abrir_proyecto_local(moved)
        self.assertEqual(opened["path"], str(moved))
        self.assertEqual(opened["main"], "main.tex")
        self.assertEqual(opened["url"], str(self.remote))
        saved = kit.leer_datos_proyecto(moved)
        self.assertFalse(Path(saved["main"]).is_absolute())
        self.assertNotIn("path", saved)
        self.assertFalse(self.a.exists())

    def test_open_tex_file_finds_project_and_uses_that_main(self):
        self.make_history(2)
        nested = self.a / "documento"
        nested.mkdir()
        tex = nested / "principal.tex"
        tex.write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        opened = kit.abrir_proyecto_local(tex)
        self.assertEqual(opened["path"], str(self.a))
        self.assertEqual(Path(opened["main"]), Path("documento/principal.tex"))
        self.assertEqual(kit.leer_datos_proyecto(self.a)["url"], str(self.remote))

    def test_open_does_not_replace_existing_git_remote_with_stale_manifest(self):
        self.make_history(2)
        manifest = self.a / kit.PROJECT_FILE_NAME
        manifest.write_text(json.dumps({"name": "tesis", "url": "https://github.com/otro/incorrecto.git",
                                        "main": "main.tex", "remote": "origin"}), encoding="utf-8")
        self.assertIsNotNone(kit.abrir_proyecto_local(self.a))
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], self.a), str(self.remote))
        self.assertEqual(kit.leer_datos_proyecto(self.a)["url"], str(self.remote))

    def test_manifest_does_not_store_http_credentials(self):
        self.make_history(2)
        url = "https://usuario:token_de_prueba@github.com/equipo/tesis.git"
        self.command(["git", "remote", "set-url", "origin", url], self.a)
        opened = kit.abrir_proyecto_local(self.a)
        self.assertEqual(opened["url"], "https://github.com/equipo/tesis.git")
        self.assertNotIn("token_de_prueba", (self.a / kit.PROJECT_FILE_NAME).read_text())
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], self.a), url)

    def test_connect_existing_local_folder_reuses_manifest_url_without_clone(self):
        project = self.root / "documento sin Git"
        project.mkdir()
        (project / "main.tex").write_text(kit.PLANTILLA_TEX, encoding="utf-8")
        url = "https://github.com/equipo/tesis.git"
        (project / kit.PROJECT_FILE_NAME).write_text(json.dumps({
            "name": "tesis", "url": url, "main": "main.tex", "remote": "origin"
        }), encoding="utf-8")
        with mock.patch.object(kit, "ask", side_effect=["4", str(project)]), \
                mock.patch.object(kit, "ensure_identity", return_value=True), \
                mock.patch.object(kit, "yes", return_value=False), \
                mock.patch.object(kit, "run_live", side_effect=AssertionError("No debe clonar")):
            self.assertIsNotNone(kit.configurar_proyecto())
        self.assertEqual(self.command(["git", "remote", "get-url", "origin"], project), url)
        self.assertFalse(kit.BASE_PROYECTOS.exists())
        self.assertEqual(kit.obtener_proyecto_principal()["path"], str(project))

    def test_first_clone_saves_url_and_uses_chosen_folder(self):
        self.make_history(2)
        self.command(["git", "push", "-u", "origin", "main"], self.a)
        project = self.root / "ubicacion elegida" / "documento"
        with mock.patch.object(kit, "ask", side_effect=["1", str(self.remote), str(project)]), \
                mock.patch.object(kit, "ensure_identity", return_value=True), \
                mock.patch.object(kit, "yes", return_value=False):
            self.assertIsNotNone(kit.configurar_proyecto())
        self.assertEqual(kit.obtener_proyecto_principal()["path"], str(project))
        self.assertEqual(kit.leer_datos_proyecto(project)["url"], str(self.remote))
        self.assertFalse(kit.BASE_PROYECTOS.exists())


class CompilationTests(TemporaryProject):
    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("pdflatex"),
                         "Se necesitan latexmk y pdflatex para esta prueba")
    def test_compile_nested_main_with_relative_input_and_spaces(self):
        # Algunas imagenes incluyen el ejecutable, pero no los formatos de LaTeX.
        if shutil.which("kpsewhich"):
            probe = subprocess.run(["kpsewhich", "pdflatex.fmt"], capture_output=True)
            if probe.returncode != 0:
                self.skipTest("La instalacion TeX no tiene el formato pdflatex.fmt")
        folder = self.root / "documento con espacios"
        folder.mkdir()
        (folder / "seccion.tex").write_text("Texto de prueba.\n", encoding="utf-8")
        (folder / "main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{seccion}\n\\end{document}\n", encoding="utf-8")
        with mock.patch.object(kit, "abrir_archivo") as viewer:
            self.assertTrue(kit.compilar({"name": "prueba", "path": str(self.root)}))
        pdf = folder / "main.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
        viewer.assert_called_once_with(pdf)


if __name__ == "__main__":
    unittest.main()
