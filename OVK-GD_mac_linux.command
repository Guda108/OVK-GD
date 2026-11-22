#!/usr/bin/env bash
# Conserva las rutas con espacios y permite abrir el lanzador desde Finder.
cd -- "$(dirname -- "$0")" || exit 1

for interprete in python3 python; do
    if command -v "$interprete" >/dev/null 2>&1 &&
       "$interprete" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
        "$interprete" OVK-GD.py "$@"
        estado=$?
        if [ "$#" -eq 0 ] && [ -t 0 ]; then
            printf '\nPresiona Enter para cerrar...'
            read -r respuesta
        fi
        exit "$estado"
    fi
done

printf '%s\n' 'OVK-GD necesita Python 3.8 o superior.'
printf '%s\n' 'Instalalo desde https://www.python.org/downloads/ o con el gestor de tu sistema.'
if [ -t 0 ]; then
    printf '\nPresiona Enter para cerrar...'
    read -r respuesta
fi
exit 1
