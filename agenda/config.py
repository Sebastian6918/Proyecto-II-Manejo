from pathlib import Path

# la carpeta del proyecto, o sea donde está main.py
BASE_DIR = Path(__file__).resolve().parent.parent

DIR_DATOS = BASE_DIR / "datos"
DIR_EXPORTADOS = BASE_DIR / "exportados"
DIR_RESPALDOS = BASE_DIR / "respaldos"

ARCHIVO_CONTACTOS = DIR_DATOS / "contactos.dat"
ARCHIVO_INDICE = DIR_DATOS / "indice.json"
ARCHIVO_HASH = DIR_DATOS / "contactos.sha256"
ARCHIVO_EXPORT_JSON = DIR_EXPORTADOS / "contactos.json"
ARCHIVO_REPORTE_PDF = DIR_EXPORTADOS / "reporte_contactos.pdf"

CODIFICACION = "utf-8"

# cada campo con lo que mide en bytes
# se cuenta en bytes y no en letras porque en utf-8 una á o una ñ ocupan 2 bytes
CAMPOS = (
    ("id", 5),
    ("nombre", 30),
    ("telefono", 14),
    ("correo", 32),
    ("ciudad", 18),
)

# cada registro termina en salto de línea para que se pueda leer en el bloc de notas
FIN_REGISTRO = b"\n"

# 5 + 30 + 14 + 32 + 18 + 1 = 100
TAMANO_REGISTRO = sum(largo for _, largo in CAMPOS) + len(FIN_REGISTRO)

# el id tiene 5 espacios, entonces lo máximo es 99999
ID_MAXIMO = 99999


def crear_carpetas():
    for carpeta in (DIR_DATOS, DIR_EXPORTADOS, DIR_RESPALDOS):
        carpeta.mkdir(parents=True, exist_ok=True)
