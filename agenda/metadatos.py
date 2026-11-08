import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class InfoArchivo:
    ruta: Path
    existe: bool
    tamano: int = 0
    modificado: datetime = None
    creado: datetime = None
    lectura: bool = False
    escritura: bool = False


def obtener_info(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        return InfoArchivo(ruta, existe=False)

    datos = os.stat(ruta)
    return InfoArchivo(
        ruta=ruta,
        existe=True,
        tamano=datos.st_size,
        modificado=datetime.fromtimestamp(datos.st_mtime),
        creado=datetime.fromtimestamp(datos.st_ctime),  # en windows es la fecha de creación
        lectura=os.access(ruta, os.R_OK),
        escritura=os.access(ruta, os.W_OK),
    )


def formatear_tamano(num_bytes):
    # 1536 -> "1.50 KB"
    if num_bytes < 1024:
        return f"{num_bytes} bytes"
    if num_bytes < 1024 ** 2:
        return f"{num_bytes / 1024:.2f} KB"
    return f"{num_bytes / 1024 ** 2:.2f} MB"
