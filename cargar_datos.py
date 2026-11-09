# llena la agenda con contactos de prueba para no meterlos uno por uno.
# se corre una sola vez: python cargar_datos.py
import random
import unicodedata

from agenda.registro import ContactoInvalidoError, Contacto
from agenda.servicio import Agenda

NOMBRES = ["Ana", "José", "María", "Luis", "Carlos", "Lucía", "Fernando", "Sofía", "Diego",
           "Andrea", "Pablo", "Gabriela", "Javier", "Daniela", "Óscar", "Valeria", "Kevin",
           "Mónica", "Edgar", "Paola", "Byron", "Alejandra", "Marvin", "Rocío"]
APELLIDOS = ["López", "Pérez", "García", "Ramírez", "Gómez", "Hernández", "Morales", "Juárez",
             "Castillo", "Méndez", "Ixcot", "Tzul", "Cifuentes", "Barrios", "Quemé", "Orozco",
             "Velásquez", "Coyoy", "Monzón", "Fuentes"]
CIUDADES = ["Quetzaltenango", "Guatemala", "Salcajá", "Totonicapán", "San Marcos", "Huehuetenango",
            "Retalhuleu", "Mazatenango", "Sololá", "Cantel", "Olintepeque", "Antigua Guatemala",
            "Zunil", "Almolonga", "Cobán"]
DOMINIOS = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "url.edu.gt"]


def sin_tildes(texto):
    # para armar el correo: José -> Jose
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def main(cantidad=40):
    random.seed(2026)  # misma semilla = siempre salen los mismos contactos
    agenda = Agenda()
    agenda.iniciar()

    agregados = 0
    while agregados < cantidad:
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        correo = (f"{sin_tildes(nombre).lower()}.{sin_tildes(apellido).lower()}"
                  f"{random.randint(1, 99)}@{random.choice(DOMINIOS)}")
        telefono = f"{random.choice('345')}{random.randint(100, 999)}-{random.randint(1000, 9999)}"

        # los ids van saltados a propósito (no 1, 2, 3...) para que se note que el id
        # no es lo mismo que el número de registro, para eso está el índice
        id_contacto = agenda.siguiente_id() + random.randint(0, 15)

        contacto = Contacto(id_contacto, f"{nombre} {apellido}", telefono, correo, random.choice(CIUDADES))
        try:
            agenda.agregar(contacto)
            agregados += 1
        except ContactoInvalidoError as e:
            # si algún correo salió muy largo se salta y se genera otro
            print(f"saltado ({contacto.nombre}): {e}")

    print(f"Listo, se agregaron {agregados} contactos.")
    print(f"contactos.dat ahora tiene {agenda.archivo.total_registros()} registros "
          f"({agenda.archivo.tamano()} bytes)")


if __name__ == "__main__":
    main()
