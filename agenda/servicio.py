from dataclasses import dataclass, field

from . import config, integridad, exportador, respaldo, metadatos
from .archivo_contactos import ArchivoContactos
from .indice import Indice, IndiceCorruptoError

# aquí se juntan todas las piezas. la ventana solo llama a estos métodos
# y nunca toca los archivos directamente


class AgendaError(Exception):
    pass


class IdNoEncontradoError(AgendaError):
    pass


class IdDuplicadoError(AgendaError):
    pass


@dataclass
class EstadoInicio:
    # lo que pasó al abrir la app, para avisarle al usuario
    advertencias: list = field(default_factory=list)
    resultado_integridad: integridad.ResultadoIntegridad = None


class Agenda:
    def __init__(self):
        self.archivo = ArchivoContactos(config.ARCHIVO_CONTACTOS)
        self.indice = Indice(config.ARCHIVO_INDICE)
        self.ruta_hash = config.ARCHIVO_HASH

    def iniciar(self):
        estado = EstadoInicio()
        config.crear_carpetas()
        self.archivo.asegurar_existe()

        if not self.archivo.es_consistente():
            estado.advertencias.append(
                f"contactos.dat mide {self.archivo.tamano()} bytes y eso no es múltiplo de "
                f"{config.TAMANO_REGISTRO}, parece dañado. Se van a leer solo los registros "
                f"completos y no se va a poder agregar."
            )

        # si el índice no está, está dañado o no cuadra con el .dat, se arma de nuevo
        motivo = None
        try:
            self.indice.cargar()
            if not self.indice.ruta.exists():
                if self.archivo.total_registros() == 0:
                    self.indice.guardar()  # primera vez que se abre la app
                else:
                    motivo = "no existía indice.json"
            elif len(self.indice) != self.archivo.total_registros():
                motivo = (f"el índice tenía {len(self.indice)} entradas y el archivo "
                          f"{self.archivo.total_registros()} registros")
        except IndiceCorruptoError as e:
            motivo = str(e)

        if motivo:
            total, errores = self.indice.reconstruir(self.archivo)
            estado.advertencias.append(f"Se reconstruyó el índice ({motivo}). Quedó con {total} contactos.")
            estado.advertencias.extend(errores)

        # la primera vez no hay hash guardado, entonces se crea
        estado.resultado_integridad = integridad.verificar(self.archivo.ruta, self.ruta_hash)
        if estado.resultado_integridad.estado == integridad.SIN_HASH:
            integridad.guardar_hash(self.archivo.ruta, self.ruta_hash)

        return estado

    def guardar_hash(self):
        # se llama después de cada cambio al .dat
        integridad.guardar_hash(self.archivo.ruta, self.ruta_hash)

    # ---- contactos ----

    def agregar(self, contacto):
        contacto.validar()
        if self.indice.existe(contacto.id):
            raise IdDuplicadoError(f"Ya hay un contacto con el id {contacto.id}.")
        resultado = self.archivo.agregar(contacto)
        self.indice.agregar(contacto.id, resultado.numero_registro)
        self.guardar_hash()
        return resultado

    def buscar(self, id_contacto):
        # primero el índice, luego seek directo al registro
        numero = self.indice.buscar(id_contacto)
        if numero is None:
            raise IdNoEncontradoError(f"No existe ningún contacto con el id {id_contacto}.")
        return self.archivo.leer(numero)

    def modificar(self, contacto):
        contacto.validar()
        numero = self.indice.buscar(contacto.id)
        if numero is None:
            raise IdNoEncontradoError(f"No existe ningún contacto con el id {contacto.id}.")
        resultado = self.archivo.modificar(numero, contacto)
        self.guardar_hash()
        return resultado

    def listar(self):
        return self.archivo.leer_todos()

    def siguiente_id(self):
        return self.indice.siguiente_id()

    # ---- exportar ----

    def exportar_json(self):
        contactos, _ = self.listar()
        return exportador.exportar_json([r.contacto for r in contactos])

    def generar_pdf(self):
        # siempre se exporta el json primero para que el pdf salga con lo último
        self.exportar_json()
        return exportador.generar_pdf_desde_json()

    # ---- herramientas ----

    def verificar_integridad(self):
        return integridad.verificar(self.archivo.ruta, self.ruta_hash)

    def aceptar_archivo_actual(self):
        # el usuario dice que el cambio de afuera está bien: nuevo hash y se rehace el índice
        self.guardar_hash()
        return self.indice.reconstruir(self.archivo)

    def reconstruir_indice(self):
        return self.indice.reconstruir(self.archivo)

    def crear_respaldo(self):
        return respaldo.crear_respaldo([self.archivo.ruta, self.indice.ruta])

    def info_archivos(self):
        rutas = (self.archivo.ruta, self.indice.ruta, self.ruta_hash)
        return [metadatos.obtener_info(r) for r in rutas]
