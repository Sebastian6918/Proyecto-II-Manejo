import json
import os
from pathlib import Path

from .config import ARCHIVO_INDICE, CODIFICACION

# el índice guarda qué id está en qué número de registro, por ejemplo:
# {"101": 0, "102": 1, "250": 2}
# buscar en un diccionario es casi instantáneo, y con el número de registro
# se hace un solo seek() en vez de leer el archivo completo


class IndiceCorruptoError(Exception):
    pass


class Indice:
    def __init__(self, ruta=ARCHIVO_INDICE):
        self.ruta = Path(ruta)
        self.entradas = {}  # id -> numero de registro

    def cargar(self):
        if not self.ruta.exists():
            self.entradas = {}
            return
        try:
            with open(self.ruta, "r", encoding=CODIFICACION) as f:
                datos = json.load(f)
            if not isinstance(datos, dict):
                raise ValueError("no tiene forma de diccionario")
            # en json las llaves siempre son texto, por eso se pasan a int
            self.entradas = {int(k): int(v) for k, v in datos.items()}
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self.entradas = {}
            raise IndiceCorruptoError(f"indice.json está dañado: {e}")

    def guardar(self):
        # primero se escribe en un .tmp y luego se reemplaza,
        # así si algo falla a medio guardar no se pierde el índice que ya había
        temporal = self.ruta.with_suffix(".tmp")
        datos = {str(k): v for k, v in sorted(self.entradas.items())}
        with open(temporal, "w", encoding=CODIFICACION) as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        os.replace(temporal, self.ruta)

    def buscar(self, id_contacto):
        # devuelve el número de registro, o None si no está
        return self.entradas.get(id_contacto)

    def existe(self, id_contacto):
        return id_contacto in self.entradas

    def agregar(self, id_contacto, numero_registro):
        self.entradas[id_contacto] = numero_registro
        self.guardar()

    def siguiente_id(self):
        return max(self.entradas, default=0) + 1

    def reconstruir(self, archivo_contactos):
        # por si el índice se pierde o se daña: se arma de nuevo leyendo el .dat
        contactos, errores = archivo_contactos.leer_todos()
        self.entradas = {r.contacto.id: r.numero_registro for r in contactos}
        self.guardar()
        return len(self.entradas), errores

    def __len__(self):
        return len(self.entradas)
