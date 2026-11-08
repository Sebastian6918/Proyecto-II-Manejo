import hashlib
from dataclasses import dataclass
from pathlib import Path

from .config import ARCHIVO_CONTACTOS, ARCHIVO_HASH, CODIFICACION

# cada vez que la app guarda algo se calcula el sha256 del .dat y se guarda aparte.
# al abrir la app se vuelve a calcular y se compara: si alguien cambió aunque sea
# una letra por fuera, el hash sale totalmente distinto

OK = "ok"
ALTERADO = "alterado"
SIN_HASH = "sin_hash"


@dataclass
class ResultadoIntegridad:
    estado: str
    hash_actual: str
    hash_guardado: str


def calcular_sha256(ruta):
    sha = hashlib.sha256()
    with open(ruta, "rb") as f:
        # se lee por pedazos de 4 KB para no cargar todo el archivo en memoria
        for bloque in iter(lambda: f.read(4096), b""):
            sha.update(bloque)
    return sha.hexdigest()


def guardar_hash(ruta_archivo=ARCHIVO_CONTACTOS, ruta_hash=ARCHIVO_HASH):
    valor = calcular_sha256(ruta_archivo)
    with open(ruta_hash, "w", encoding=CODIFICACION) as f:
        # mismo formato que usa el comando sha256sum
        f.write(f"{valor}  {Path(ruta_archivo).name}\n")
    return valor


def leer_hash_guardado(ruta_hash=ARCHIVO_HASH):
    ruta_hash = Path(ruta_hash)
    if not ruta_hash.exists():
        return None
    with open(ruta_hash, "r", encoding=CODIFICACION) as f:
        contenido = f.read().strip()
    if not contenido:
        return None
    return contenido.split()[0].lower()


def verificar(ruta_archivo=ARCHIVO_CONTACTOS, ruta_hash=ARCHIVO_HASH):
    actual = calcular_sha256(ruta_archivo)
    guardado = leer_hash_guardado(ruta_hash)
    if guardado is None:
        estado = SIN_HASH
    elif guardado == actual:
        estado = OK
    else:
        estado = ALTERADO
    return ResultadoIntegridad(estado, actual, guardado)
