import re
from dataclasses import dataclass, asdict

from .config import CAMPOS, CODIFICACION, FIN_REGISTRO, TAMANO_REGISTRO, ID_MAXIMO

LARGOS = dict(CAMPOS)

PATRON_TELEFONO = re.compile(r"^\+?[0-9][0-9 -]{6,13}$")
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ContactoInvalidoError(ValueError):
    # cuando el usuario escribe algo que no cumple
    pass


class RegistroInvalidoError(ValueError):
    # cuando lo que se leyó del archivo no tiene sentido
    pass


def rellenar(texto, largo):
    # como ljust() pero contando bytes, así el campo siempre mide lo mismo
    datos = texto.encode(CODIFICACION)
    if len(datos) > largo:
        # por si acaso: se corta sin partir una letra con tilde a la mitad
        datos = datos[:largo].decode(CODIFICACION, errors="ignore").encode(CODIFICACION)
    return datos.ljust(largo, b" ")


@dataclass
class Contacto:
    id: int
    nombre: str
    telefono: str
    correo: str
    ciudad: str

    def validar(self):
        errores = []

        if not isinstance(self.id, int) or not 1 <= self.id <= ID_MAXIMO:
            errores.append(f"El id tiene que ser un número entre 1 y {ID_MAXIMO}.")

        for campo in ("nombre", "telefono", "correo", "ciudad"):
            valor = getattr(self, campo)
            if not valor.strip():
                errores.append(f"Falta llenar {campo}.")
            elif "\n" in valor or "\r" in valor:
                errores.append(f"{campo} no puede llevar saltos de línea.")
            elif len(valor.encode(CODIFICACION)) > LARGOS[campo]:
                errores.append(f"{campo} es muy largo, máximo {LARGOS[campo]} bytes "
                               f"(las tildes cuentan doble).")

        if self.telefono.strip() and not PATRON_TELEFONO.match(self.telefono.strip()):
            errores.append("El teléfono no es válido, ej: 5555-1234 o +502 5555-1234")
        if self.correo.strip() and not PATRON_CORREO.match(self.correo.strip()):
            errores.append("El correo no es válido, ej: alguien@gmail.com")

        if errores:
            raise ContactoInvalidoError("\n".join(errores))

    def a_bytes(self):
        # convierte el contacto en un registro de 100 bytes exactos
        self.validar()
        partes = [rellenar(str(getattr(self, campo)).strip(), largo) for campo, largo in CAMPOS]
        registro = b"".join(partes) + FIN_REGISTRO
        assert len(registro) == TAMANO_REGISTRO
        return registro

    @classmethod
    def desde_bytes(cls, datos):
        # lo contrario: de 100 bytes a un contacto
        if len(datos) != TAMANO_REGISTRO or not datos.endswith(FIN_REGISTRO):
            raise RegistroInvalidoError(f"Se esperaban {TAMANO_REGISTRO} bytes y vinieron {len(datos)}.")

        valores = {}
        inicio = 0
        for campo, largo in CAMPOS:
            pedazo = datos[inicio:inicio + largo]
            try:
                valores[campo] = pedazo.decode(CODIFICACION).rstrip(" ")
            except UnicodeDecodeError:
                raise RegistroInvalidoError(f"El campo {campo} está dañado.")
            inicio += largo

        try:
            valores["id"] = int(valores["id"])
        except ValueError:
            raise RegistroInvalidoError(f"El id '{valores['id']}' no es un número.")

        return cls(**valores)

    def a_dict(self):
        return asdict(self)
