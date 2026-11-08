import functools
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, simpledialog

from . import config, integridad
from .archivo_contactos import ArchivoCorruptoError
from .metadatos import formatear_tamano
from .registro import Contacto, ContactoInvalidoError, RegistroInvalidoError, LARGOS
from .servicio import Agenda, AgendaError

TITULO = "Agenda de Contactos"

ETIQUETAS = (
    ("id", "ID"),
    ("nombre", "Nombre"),
    ("telefono", "Teléfono"),
    ("correo", "Correo"),
    ("ciudad", "Ciudad"),
)


def manejar_errores(metodo):
    # se le pone @manejar_errores a cada acción para no repetir el mismo try/except
    # en todos los botones. si algo falla sale un mensaje y la app sigue abierta
    @functools.wraps(metodo)
    def envoltura(self, *args, **kwargs):
        try:
            return metodo(self, *args, **kwargs)
        except ContactoInvalidoError as e:
            messagebox.showwarning("Datos inválidos", str(e), parent=self)
        except AgendaError as e:
            self.log(f"AVISO: {e}")
            messagebox.showwarning("Aviso", str(e), parent=self)
        except (ArchivoCorruptoError, RegistroInvalidoError, IndexError) as e:
            self.log(f"ERROR: {e}")
            messagebox.showerror("Archivo dañado", str(e), parent=self)
        except PermissionError as e:
            self.log(f"ERROR de permisos: {e}")
            messagebox.showerror("Sin permisos",
                                 f"No hay permiso para usar:\n{e.filename}\n\n"
                                 "Revisa que no esté abierto en otro programa o que no sea de solo lectura.",
                                 parent=self)
        except FileNotFoundError as e:
            self.log(f"ERROR: no se encontró {e.filename}")
            messagebox.showerror("Archivo no encontrado", str(e), parent=self)
        except OSError as e:
            self.log(f"ERROR de archivo: {e}")
            messagebox.showerror("Error de archivo", str(e), parent=self)
        except Exception as e:
            # por si pasa algo que no esperábamos, igual no se cierra
            self.log(f"ERROR inesperado: {e!r}")
            messagebox.showerror("Error inesperado", repr(e), parent=self)
    return envoltura


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO)
        self.geometry("980x680")
        self.minsize(860, 560)

        self.agenda = Agenda()
        self.campos = {}  # campo -> StringVar del Entry
        self.acceso = {}  # labels del panel de seek/tell

        self.crear_menu()
        self.crear_formulario()
        self.crear_tabla()
        self.crear_bitacora()
        self.crear_barra_estado()

        # se espera un poquito para que los avisos salgan encima de la ventana ya dibujada
        self.after(100, self.iniciar_agenda)

    # ---- armado de la ventana ----

    def crear_menu(self):
        barra = tk.Menu(self)

        contactos = tk.Menu(barra, tearoff=False)
        contactos.add_command(label="Agregar contacto", command=self.agregar)
        contactos.add_command(label="Buscar por ID...", command=self.buscar_desde_menu)
        contactos.add_command(label="Modificar contacto", command=self.modificar)
        contactos.add_command(label="Limpiar formulario", command=self.limpiar)
        contactos.add_separator()
        contactos.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Contactos", menu=contactos)

        exportar = tk.Menu(barra, tearoff=False)
        exportar.add_command(label="Exportar a JSON", command=self.exportar_json)
        exportar.add_command(label="Generar reporte PDF", command=self.generar_pdf)
        barra.add_cascade(label="Exportar", menu=exportar)

        herramientas = tk.Menu(barra, tearoff=False)
        herramientas.add_command(label="Verificar integridad", command=self.verificar_integridad)
        herramientas.add_command(label="Crear respaldo ZIP", command=self.crear_respaldo)
        herramientas.add_command(label="Información del archivo", command=self.mostrar_info_archivo)
        herramientas.add_separator()
        herramientas.add_command(label="Reconstruir índice", command=self.reconstruir_indice)
        barra.add_cascade(label="Herramientas", menu=herramientas)

        ayuda = tk.Menu(barra, tearoff=False)
        ayuda.add_command(label="Manual de usuario", command=self.ayuda_simulada)
        ayuda.add_command(label="Acerca de", command=self.acerca_de)
        barra.add_cascade(label="Ayuda", menu=ayuda)

        self.config(menu=barra)

    def crear_formulario(self):
        arriba = ttk.Frame(self, padding=(10, 10, 10, 0))
        arriba.pack(fill="x")

        marco = ttk.LabelFrame(arriba, text="Datos del contacto", padding=10)
        marco.pack(side="left", fill="both", expand=True)

        for fila, (campo, etiqueta) in enumerate(ETIQUETAS):
            ttk.Label(marco, text=f"{etiqueta}:").grid(row=fila, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            ancho = 10 if campo == "id" else 38
            ttk.Entry(marco, textvariable=var, width=ancho).grid(row=fila, column=1, sticky="w", padx=6, pady=3)
            ttk.Label(marco, text=f"máx. {LARGOS[campo]} bytes", foreground="gray").grid(row=fila, column=2, sticky="w")
            self.campos[campo] = var

        ttk.Button(marco, text="Siguiente ID", command=self.sugerir_id).grid(row=0, column=1, sticky="e", padx=6)

        botones = ttk.Frame(marco)
        botones.grid(row=len(ETIQUETAS), column=0, columnspan=3, pady=(10, 0), sticky="w")
        ttk.Button(botones, text="Agregar", command=self.agregar).pack(side="left", padx=3)
        ttk.Button(botones, text="Buscar por ID", command=self.buscar).pack(side="left", padx=3)
        ttk.Button(botones, text="Modificar", command=self.modificar).pack(side="left", padx=3)
        ttk.Button(botones, text="Limpiar", command=self.limpiar).pack(side="left", padx=3)

        # panel de la derecha para ver el seek y el tell de cada operación
        panel = ttk.LabelFrame(arriba, text="Acceso al archivo (seek / tell)", padding=10)
        panel.pack(side="left", fill="y", padx=(10, 0))
        filas = (
            ("operacion", "Última operación:"),
            ("indice", "Índice (id → registro):"),
            ("seek", "seek(registro × tamaño):"),
            ("tell", "tell() devolvió:"),
            ("tamano", "Tamaño de registro:"),
            ("total", "Total de registros:"),
        )
        for fila, (clave, texto) in enumerate(filas):
            ttk.Label(panel, text=texto).grid(row=fila, column=0, sticky="w", pady=2)
            valor = ttk.Label(panel, text="-", font=("Consolas", 10, "bold"))
            valor.grid(row=fila, column=1, sticky="w", padx=8)
            self.acceso[clave] = valor
        self.acceso["tamano"].config(text=f"{config.TAMANO_REGISTRO} bytes")

    def crear_tabla(self):
        marco = ttk.LabelFrame(self, text="Contactos guardados (doble clic para cargar uno)", padding=5)
        marco.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("registro", "byte", "id", "nombre", "telefono", "correo", "ciudad")
        titulos = ("Reg. #", "Byte", "ID", "Nombre", "Teléfono", "Correo", "Ciudad")
        anchos = (60, 60, 60, 210, 120, 220, 140)

        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=8)
        for col, titulo, ancho in zip(columnas, titulos, anchos):
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="w")

        scroll = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-1>", self.al_doble_clic)

    def crear_bitacora(self):
        marco = ttk.LabelFrame(self, text="Bitácora", padding=5)
        marco.pack(fill="x", padx=10)
        self.bitacora = tk.Text(marco, height=7, state="disabled", font=("Consolas", 9))
        self.bitacora.pack(fill="x")

    def crear_barra_estado(self):
        self.estado = ttk.Label(self, text="Listo", relief="sunken", anchor="w", padding=3)
        self.estado.pack(fill="x", side="bottom", pady=(8, 0))

    # ---- cositas que se usan en varios lados ----

    def log(self, mensaje):
        hora = datetime.now().strftime("%H:%M:%S")
        self.bitacora.config(state="normal")
        self.bitacora.insert("end", f"[{hora}] {mensaje}\n")
        self.bitacora.see("end")
        self.bitacora.config(state="disabled")

    def mostrar_acceso(self, operacion, resultado, id_contacto=None):
        n = resultado.numero_registro
        self.acceso["operacion"].config(text=operacion)
        if id_contacto is None:
            self.acceso["indice"].config(text=f"(nuevo) → #{n}")
        else:
            self.acceso["indice"].config(text=f"{id_contacto} → #{n}")
        self.acceso["seek"].config(text=f"{n} × {config.TAMANO_REGISTRO} = {n * config.TAMANO_REGISTRO}")
        self.acceso["tell"].config(text=f"{resultado.posicion} bytes")

    def leer_id(self):
        texto = self.campos["id"].get().strip()
        if not texto:
            raise ContactoInvalidoError("Escribe un ID.")
        if not texto.isdigit():
            raise ContactoInvalidoError("El ID tiene que ser un número entero positivo.")
        return int(texto)

    def leer_formulario(self):
        return Contacto(
            id=self.leer_id(),
            nombre=self.campos["nombre"].get().strip(),
            telefono=self.campos["telefono"].get().strip(),
            correo=self.campos["correo"].get().strip(),
            ciudad=self.campos["ciudad"].get().strip(),
        )

    def llenar_formulario(self, contacto):
        for campo, var in self.campos.items():
            var.set(str(getattr(contacto, campo)))

    def refrescar_tabla(self):
        # esto lee todo el archivo de corrido, pero es solo para mostrar la lista.
        # las búsquedas van por el índice
        self.tabla.delete(*self.tabla.get_children())
        contactos, errores = self.agenda.listar()
        for r in contactos:
            c = r.contacto
            self.tabla.insert("", "end", values=(r.numero_registro, r.posicion, c.id,
                                                 c.nombre, c.telefono, c.correo, c.ciudad))
        for error in errores:
            self.log(f"AVISO: {error}")
        total = self.agenda.archivo.total_registros()
        self.acceso["total"].config(text=str(total))
        self.estado.config(text=f"{total} contacto(s)  |  {self.agenda.archivo.ruta}")

    # ---- al abrir ----

    @manejar_errores
    def iniciar_agenda(self):
        estado = self.agenda.iniciar()
        self.log(f"Archivo: {self.agenda.archivo.ruta}")
        self.log(f"Registros: {self.agenda.archivo.total_registros()}  |  en el índice: {len(self.agenda.indice)}")

        for aviso in estado.advertencias:
            self.log(f"AVISO: {aviso}")
        if estado.advertencias:
            messagebox.showwarning("Avisos al abrir", "\n\n".join(estado.advertencias), parent=self)

        resultado = estado.resultado_integridad
        if resultado.estado == integridad.SIN_HASH:
            self.log("Integridad: no había hash guardado, se creó contactos.sha256")
        elif resultado.estado == integridad.OK:
            self.log("Integridad: OK, el hash coincide")
        else:
            self.log("Integridad: ALERTA, el archivo se modificó fuera de la app")
            self.alerta_integridad(resultado)

        self.refrescar_tabla()
        self.sugerir_id()

    def alerta_integridad(self, resultado):
        aceptar = messagebox.askyesno(
            "Archivo modificado",
            "contactos.dat se modificó FUERA de la aplicación.\n\n"
            f"Hash guardado:\n{resultado.hash_guardado}\n\n"
            f"Hash actual:\n{resultado.hash_actual}\n\n"
            "¿Quieres aceptar el archivo como está ahora?\n"
            "(Sí = se guarda el hash nuevo y se rehace el índice)",
            icon="warning", parent=self,
        )
        if aceptar:
            total, _ = self.agenda.aceptar_archivo_actual()
            self.log(f"Integridad: se aceptaron los cambios, índice rehecho con {total} contactos")
        else:
            self.log("Integridad: no se aceptaron los cambios, el aviso va a seguir saliendo")

    # ---- contactos ----

    @manejar_errores
    def agregar(self):
        contacto = self.leer_formulario()
        resultado = self.agenda.agregar(contacto)
        self.mostrar_acceso("AGREGAR", resultado)
        self.log(f"AGREGAR id={contacto.id} → registro #{resultado.numero_registro}, "
                 f"se escribió en el byte {resultado.posicion} (tell)")
        self.refrescar_tabla()
        messagebox.showinfo("Listo", f"Contacto {contacto.id} guardado en el registro #{resultado.numero_registro}.",
                            parent=self)
        self.limpiar()

    @manejar_errores
    def buscar(self, id_contacto=None):
        if id_contacto is None:
            id_contacto = self.leer_id()
        resultado = self.agenda.buscar(id_contacto)
        self.llenar_formulario(resultado.contacto)
        self.mostrar_acceso("BUSCAR", resultado, id_contacto)
        self.log(f"BUSCAR id={id_contacto} → el índice dice registro #{resultado.numero_registro} "
                 f"→ seek({resultado.numero_registro * config.TAMANO_REGISTRO}) → tell()={resultado.posicion}")

    def buscar_desde_menu(self):
        id_contacto = simpledialog.askinteger("Buscar", "ID del contacto:", parent=self,
                                              minvalue=1, maxvalue=config.ID_MAXIMO)
        if id_contacto is not None:
            self.buscar(id_contacto)

    @manejar_errores
    def modificar(self):
        contacto = self.leer_formulario()
        if not messagebox.askyesno("Confirmar", f"¿Guardar los cambios del contacto {contacto.id}?", parent=self):
            return
        resultado = self.agenda.modificar(contacto)
        self.mostrar_acceso("MODIFICAR", resultado, contacto.id)
        self.log(f"MODIFICAR id={contacto.id} → se sobrescribieron solo {config.TAMANO_REGISTRO} bytes "
                 f"desde el byte {resultado.posicion}")
        self.refrescar_tabla()
        messagebox.showinfo("Listo", "Cambios guardados.", parent=self)

    def limpiar(self):
        for var in self.campos.values():
            var.set("")
        self.sugerir_id()

    def sugerir_id(self):
        self.campos["id"].set(str(self.agenda.siguiente_id()))

    def al_doble_clic(self, evento):
        seleccion = self.tabla.selection()
        if seleccion:
            id_contacto = int(self.tabla.item(seleccion[0], "values")[2])
            self.buscar(id_contacto)

    # ---- exportar ----

    @manejar_errores
    def exportar_json(self):
        ruta = self.agenda.exportar_json()
        self.log(f"EXPORTAR JSON → {ruta}")
        messagebox.showinfo("Exportar JSON", f"Contactos exportados en:\n{ruta}", parent=self)

    @manejar_errores
    def generar_pdf(self):
        ruta = self.agenda.generar_pdf()
        self.log(f"REPORTE PDF (hecho desde contactos.json) → {ruta}")
        messagebox.showinfo("Reporte PDF", f"Reporte generado en:\n{ruta}", parent=self)

    # ---- herramientas ----

    @manejar_errores
    def verificar_integridad(self):
        resultado = self.agenda.verificar_integridad()
        if resultado.estado == integridad.OK:
            self.log("VERIFICAR: OK")
            messagebox.showinfo("Integridad", f"El archivo está bien, no lo han tocado.\n\n"
                                              f"SHA-256:\n{resultado.hash_actual}", parent=self)
        elif resultado.estado == integridad.SIN_HASH:
            self.log("VERIFICAR: no hay hash guardado")
            messagebox.showwarning("Integridad", "No existe contactos.sha256 para comparar.", parent=self)
        else:
            self.log("VERIFICAR: el archivo fue ALTERADO")
            self.alerta_integridad(resultado)
            self.refrescar_tabla()

    @manejar_errores
    def crear_respaldo(self):
        r = self.agenda.crear_respaldo()
        lineas = [f"{nombre}: {formatear_tamano(orig)} → {formatear_tamano(comp)}"
                  for nombre, orig, comp in r.detalle]
        mensaje = (f"Respaldo creado:\n{r.ruta_zip}\n\n" + "\n".join(lineas) +
                   f"\n\nTamaño original: {formatear_tamano(r.tamano_original)}"
                   f"\nTamaño del ZIP: {formatear_tamano(r.tamano_comprimido)}"
                   f"\nAhorro: {r.porcentaje_ahorro:.1f} %")
        self.log(f"RESPALDO {r.ruta_zip.name}: {r.tamano_original} → {r.tamano_comprimido} bytes "
                 f"({r.porcentaje_ahorro:.1f} % de ahorro)")
        messagebox.showinfo("Respaldo ZIP", mensaje, parent=self)

    @manejar_errores
    def mostrar_info_archivo(self):
        infos = self.agenda.info_archivos()

        ventana = tk.Toplevel(self)
        ventana.title("Información del archivo")
        ventana.transient(self)
        ventana.resizable(False, False)

        columnas = ["propiedad"] + [i.ruta.name for i in infos]
        tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=7)
        for col in columnas:
            tabla.heading(col, text="Propiedad" if col == "propiedad" else col)
            tabla.column(col, width=170 if col == "propiedad" else 200, anchor="w")

        def si_no(valor):
            return "Sí" if valor else "No"

        def fecha(valor):
            return valor.strftime("%d/%m/%Y %H:%M:%S") if valor else "-"

        filas = [
            ("Existe", [si_no(i.existe) for i in infos]),
            ("Tamaño", [formatear_tamano(i.tamano) for i in infos]),
            ("Tamaño en bytes", [str(i.tamano) for i in infos]),
            ("Última modificación", [fecha(i.modificado) for i in infos]),
            ("Fecha de creación", [fecha(i.creado) for i in infos]),
            ("Permiso de lectura", [si_no(i.lectura) for i in infos]),
            ("Permiso de escritura", [si_no(i.escritura) for i in infos]),
        ]
        for propiedad, valores in filas:
            tabla.insert("", "end", values=[propiedad] + valores)
        tabla.pack(padx=10, pady=10)

        archivo = self.agenda.archivo
        ttk.Label(ventana, text=f"Carpeta: {archivo.ruta.parent}\n"
                                f"Registros en contactos.dat: {archivo.total_registros()} × "
                                f"{config.TAMANO_REGISTRO} bytes").pack(padx=10, anchor="w")
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=10)
        self.log("INFO del archivo (os.stat y os.access)")

    @manejar_errores
    def reconstruir_indice(self):
        total, errores = self.agenda.reconstruir_indice()
        for error in errores:
            self.log(f"AVISO: {error}")
        self.log(f"ÍNDICE rehecho con {total} contactos")
        messagebox.showinfo("Índice", f"Índice reconstruido con {total} contactos.", parent=self)

    # ---- ayuda (simulado) ----

    def ayuda_simulada(self):
        messagebox.showinfo("Manual de usuario", "Esta opción todavía no está disponible.", parent=self)

    def acerca_de(self):
        messagebox.showinfo("Acerca de",
                            f"{TITULO} v1.0\n\nLaboratorio 2 - Manejo de archivos\n"
                            "Ingeniería en Informática y Sistemas\n"
                            "Campus San Alberto Hurtado, S.J. - Quetzaltenango",
                            parent=self)
