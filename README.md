# Agenda de contactos

Lab 2 de Manejo de Archivos.

La agenda guarda los contactos en `datos/contactos.dat`, donde cada contacto mide exactamente 100 bytes.
Así se puede ir directo a cualquiera con seek() sin leer todo el archivo. Para buscar por id se usa un
índice en json, y además exporta a json y pdf, revisa con sha256 si alguien modificó el archivo por
fuera y hace respaldos en zip.

## Cómo correrlo

    pip install -r requirements.txt
    python main.py

Si quieres datos de prueba (40 contactos), con la carpeta datos vacía:

    python cargar_datos.py

## Estructura del registro (100 bytes)

| Campo          | Bytes | Posición |
|----------------|-------|----------|
| id             | 5     | 0 - 4    |
| nombre         | 30    | 5 - 34   |
| telefono       | 14    | 35 - 48  |
| correo         | 32    | 49 - 80  |
| ciudad         | 18    | 81 - 98  |
| salto de línea | 1     | 99       |

Se cuenta en bytes y no en letras porque en utf-8 las tildes y la ñ ocupan 2 bytes.

## Archivos que genera

- `datos/contactos.dat`: los contactos
- `datos/indice.json`: id -> número de registro
- `datos/contactos.sha256`: hash para revisar la integridad
- `exportados/contactos.json` y `exportados/reporte_contactos.pdf`
- `respaldos/respaldo_*.zip`

El documento con la explicación completa está en `docs/`.
