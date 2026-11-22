# Contribuir a OVK-GD

Gracias por ayudar a que sea más fácil escribir LaTeX en equipo.

## Reportar un problema

Abre un **Issue** con la plantilla de error e incluye el sistema operativo, las versiones de Python y OVK-GD, la opción del menú que utilizaste y el mensaje observado. Si se trata de un documento, comparte un ejemplo mínimo que reproduzca el problema.

## Proponer cambios

1. Crea una rama desde `main` o trabaja en un fork.
2. Mantén los cambios centrados en un problema concreto.
3. Conserva la compatibilidad con Python 3.8 y la biblioteca estándar, salvo que el proyecto decida cambiar esos requisitos.
4. Actualiza el manual cuando cambie el comportamiento para el usuario.
5. Ejecuta las comprobaciones y abre un pull request con una explicación breve.

```bash
python -m py_compile OVK-GD.py
python -m unittest discover -s tests -v
python OVK-GD.py --help
```

En macOS/Linux puede ser necesario utilizar `python3`. Para verificar el lanzador de shell, ejecuta `bash -n OVK-GD_mac_linux.command`.

Las pruebas de Git usan repositorios temporales locales y no necesitan una cuenta. La prueba de compilación real se omite si faltan `latexmk` o `pdflatex`. Los instaladores requieren una comprobación aparte en cada sistema; primero puedes consultar sus órdenes con `--simular instalar`.

Las pruebas del historial crean varias revisiones y autores, exportan commits, simulan la frontera de compilación para comprobar el nombre del PDF y verifican que se conservan los cambios locales. También comprueban un `fetch` real entre repositorios locales y la ampliación de un clon superficial.

Evita añadir dependencias solo para pequeñas utilidades y no incluyas archivos generados por las pruebas. Consulta [`docs/VALIDACION.md`](docs/VALIDACION.md) para conocer el alcance de la validación de esta entrega.

Las pruebas de descarga comprueban las fuentes del commit, la independencia de la copia, la conservación del trabajo local y la sincronización en una rama propia. Las de selección principal comprueban su persistencia y el archivo `.tex` utilizado al compilar.

Las pruebas de apertura comprueban que no se clona ni se pide la URL al reabrir. También verifican la persistencia del enlace, el cambio de ubicación de la carpeta y la conservación de la conexión Git existente.
