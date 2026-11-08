import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import DIR_RESPALDOS


@dataclass
class ResultadoRespaldo:
    ruta_zip: Path
    tamano_original: int    # lo que suman los archivos sin comprimir
    tamano_comprimido: int  # lo que pesa el .zip
    detalle: list           # (nombre, original, comprimido) de cada archivo

    @property
    def porcentaje_ahorro(self):
        if self.tamano_original == 0:
            return 0.0
        return 100 * (1 - self.tamano_comprimido / self.tamano_original)


def crear_respaldo(archivos, carpeta_destino=DIR_RESPALDOS):
    carpeta_destino = Path(carpeta_destino)
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    # con fecha y hora en el nombre para que no se pisen los respaldos
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_zip = carpeta_destino / f"respaldo_{fecha}.zip"

    with zipfile.ZipFile(ruta_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for ruta in archivos:
            ruta = Path(ruta)
            if not ruta.exists():
                raise FileNotFoundError(f"No existe {ruta.name}, no se puede respaldar.")
            z.write(ruta, arcname=ruta.name)

    # se abre otra vez el zip para ver cuánto quedó pesando cada archivo adentro
    with zipfile.ZipFile(ruta_zip, "r") as z:
        detalle = [(info.filename, info.file_size, info.compress_size) for info in z.infolist()]

    original = sum(d[1] for d in detalle)
    return ResultadoRespaldo(ruta_zip, original, ruta_zip.stat().st_size, detalle)