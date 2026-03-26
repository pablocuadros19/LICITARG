"""
Sincroniza los parquets procesados de LICITARG hacia NyPer y AgroBip.
Correr después de reprocesar los datos.

Uso:
    python scripts/sync_repos.py
"""

import shutil
import subprocess
from pathlib import Path
from datetime import datetime

LICITARG = Path(__file__).parent.parent

FUENTES = {
    "proveedores.parquet": LICITARG / "data/processed/proveedores.parquet",
    "agro-proveedores-estado.parquet": LICITARG / "data/processed/agro-proveedores-estado.parquet",
}

DESTINOS = {
    "NyPer": {
        "path": Path(r"C:\PRUEBA 101\data\licitarg"),
        "archivos": ["proveedores.parquet"],
    },
    "AgroBip": {
        "path": Path(r"C:\AgroBip\data\licitarg"),
        "archivos": ["proveedores.parquet", "agro-proveedores-estado.parquet"],
    },
}


def copiar():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sincronizando parquets LICITARG -> repos\n")

    for nombre_repo, config in DESTINOS.items():
        dest_dir = config["path"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"  {nombre_repo}:")
        for archivo in config["archivos"]:
            origen = FUENTES.get(archivo)
            if not origen or not origen.exists():
                print(f"    {archivo} — FALTA en processed/, correr el pipeline primero")
                continue
            destino = dest_dir / archivo
            shutil.copy2(origen, destino)
            kb = destino.stat().st_size // 1024
            print(f"    {archivo} -> {destino} ({kb} KB)")

    print()


def git_status():
    for nombre_repo, config in DESTINOS.items():
        repo = config["path"].parent.parent
        if not (repo / ".git").exists():
            continue
        result = subprocess.run(
            ["git", "status", "--short", "data/licitarg/"],
            cwd=repo, capture_output=True, text=True
        )
        if result.stdout.strip():
            print(f"  {nombre_repo} — cambios listos para commit:")
            for linea in result.stdout.strip().splitlines():
                print(f"    {linea}")
        else:
            print(f"  {nombre_repo} — sin cambios nuevos")


if __name__ == "__main__":
    copiar()
    print("Estado git:")
    git_status()
    print()
    print("Proximos pasos:")
    print("  cd 'C:\\PRUEBA 101' && git add data/licitarg/ && git commit -m 'datos: actualizar proveedores LICITARG' && git push")
    print("  cd C:\\AgroBip    && git add data/licitarg/ && git commit -m 'datos: actualizar proveedores LICITARG' && git push")
