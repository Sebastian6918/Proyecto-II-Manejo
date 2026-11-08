import json
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from .config import ARCHIVO_EXPORT_JSON, ARCHIVO_REPORTE_PDF, CODIFICACION

# columnas de la tabla del pdf: titulo, campo y ancho en mm (suman 190, lo que cabe en una hoja A4)
COLUMNAS = (
    ("ID", "id", 14),
    ("Nombre", "nombre", 50),
    ("Teléfono", "telefono", 32),
    ("Correo", "correo", 58),
    ("Ciudad", "ciudad", 36),
)


def exportar_json(contactos, ruta=ARCHIVO_EXPORT_JSON):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "total": len(contactos),
        "contactos": [c.a_dict() for c in contactos],
    }
    with open(ruta, "w", encoding=CODIFICACION) as f:
        # ensure_ascii=False para que las tildes se vean normales y no como \u00e9
        json.dump(datos, f, indent=2, ensure_ascii=False)
    return ruta


def texto_pdf(valor):
    # las fuentes que trae fpdf solo aguantan latin-1 (tildes y ñ sí entran),
    # si viene algún caracter raro se cambia por ? para que no truene
    return str(valor).encode("latin-1", errors="replace").decode("latin-1")


class Reporte(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def generar_pdf_desde_json(ruta_json=ARCHIVO_EXPORT_JSON, ruta_pdf=ARCHIVO_REPORTE_PDF):
    # el pdf se arma leyendo el json, no el .dat (así lo pide el lab)
    with open(ruta_json, "r", encoding=CODIFICACION) as f:
        datos = json.load(f)
    contactos = datos.get("contactos", [])

    pdf = Reporte(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Reporte de Contactos", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 6, texto_pdf(f"Fecha de generación: {fecha}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Total de contactos: {len(contactos)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def encabezado():
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(41, 98, 155)
        pdf.set_text_color(255, 255, 255)
        for titulo, _, ancho in COLUMNAS:
            pdf.cell(ancho, 8, texto_pdf(titulo), border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)

    encabezado()
    for i, contacto in enumerate(contactos):
        # si ya no cabe la fila, hoja nueva y se repite el encabezado
        if pdf.will_page_break(7):
            pdf.add_page()
            encabezado()
        pdf.set_fill_color(235, 241, 248)
        for _, campo, ancho in COLUMNAS:
            pdf.cell(ancho, 7, texto_pdf(contacto.get(campo, "")), border=1, fill=(i % 2 == 1))
        pdf.ln()

    if not contactos:
        pdf.cell(0, 8, "No hay contactos registrados.", border=1, align="C")

    ruta_pdf = Path(ruta_pdf)
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(ruta_pdf))
    return ruta_pdf
