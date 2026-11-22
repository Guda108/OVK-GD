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
        with mock.patch.object(kit, "ask", side_effect=["2", "0"]), \
                mock.patch.object(kit, "pausa"), mock.patch.object(kit, "compilar_version") as compile_old:
            kit.historial({"name": "tesis", "path": str(self.a)})
        self.assertEqual(compile_old.call_args[0][1], commits[-2])


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
