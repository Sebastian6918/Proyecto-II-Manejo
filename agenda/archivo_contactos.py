import os
from dataclasses import dataclass
from pathlib import Path

from .config import ARCHIVO_CONTACTOS, TAMANO_REGISTRO
from .registro import Contacto

# el archivo se abre en binario (rb, r+b, ab) para que seek() y tell()
# trabajen con bytes exactos. igual lo que se guarda es texto en utf-8


class ArchivoCorruptoError(Exception):
    pass


@dataclass
class ResultadoAcceso:
    numero_registro: int
    posicion: int  # lo que devolvió tell()
    contacto: Contacto


class ArchivoContactos:
    def __init__(self, ruta=ARCHIVO_CONTACTOS):
        self.ruta = Path(ruta)

    def asegurar_existe(self):
        # si no existe lo crea vacío, si ya existe no lo toca
        if not self.ruta.exists():
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta, "ab"):
                pass

    def tamano(self):
        return os.path.getsize(self.ruta)

    def total_registros(self):
        return self.tamano() // TAMANO_REGISTRO

    def es_consistente(self):
        # si no da exacto es que hay un registro a medias
        return self.tamano() % TAMANO_REGISTRO == 0

    @staticmethod
    def posicion_de(numero_registro):
        return numero_registro * TAMANO_REGISTRO

    def agregar(self, contacto):
        datos = contacto.a_bytes()
        with open(self.ruta, "ab") as f:
            f.seek(0, os.SEEK_END)  # al final del archivo
            posicion = f.tell()
            if posicion % TAMANO_REGISTRO != 0:
                raise ArchivoCorruptoError(
                    f"El archivo mide {posicion} bytes y eso no es múltiplo de {TAMANO_REGISTRO}, "
                    f"está dañado. No se agrega nada para no empeorarlo."
                )
            f.write(datos)
        return ResultadoAcceso(posicion // TAMANO_REGISTRO, posicion, contacto)

    def leer(self, numero_registro):
        # aquí está el acceso aleatorio: salta directo al registro sin leer los de antes
        if not 0 <= numero_registro < self.total_registros():
            raise IndexError(f"El registro #{numero_registro} no existe.")
        with open(self.ruta, "rb") as f:
            f.seek(self.posicion_de(numero_registro))
            posicion = f.tell()
            datos = f.read(TAMANO_REGISTRO)
        return ResultadoAcceso(numero_registro, posicion, Contacto.desde_bytes(datos))

    def modificar(self, numero_registro, contacto):
        # solo se sobrescriben esos 100 bytes, el resto del archivo ni se toca
        if not 0 <= numero_registro < self.total_registros():
            raise IndexError(f"El registro #{numero_registro} no existe.")
        datos = contacto.a_bytes()
        with open(self.ruta, "r+b") as f:  # r+b no borra el archivo como haría w
            f.seek(self.posicion_de(numero_registro))
            posicion = f.tell()
            f.write(datos)
        return ResultadoAcceso(numero_registro, posicion, contacto)

    def leer_todos(self):
        # este sí lee todo de corrido, solo se usa para exportar, listar o rehacer el índice
        # si un registro está dañado lo anota y sigue con los demás
        contactos = []
        errores = []
        with open(self.ruta, "rb") as f:
            numero = 0
            while True:
                posicion = f.tell()
                datos = f.read(TAMANO_REGISTRO)
                if not datos:
                    break
                try:
                    contactos.append(ResultadoAcceso(numero, posicion, Contacto.desde_bytes(datos)))
                except ValueError as e:
                    errores.append(f"Registro #{numero} (byte {posicion}): {e}")
                numero += 1
        return contactos, errores
