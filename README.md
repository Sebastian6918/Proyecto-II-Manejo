# Agenda de contactos

Lab 2 de Manejo de Archivos.

La agenda guarda los contactos en un archivo .dat donde todos los registros miden lo mismo,
así se puede ir directo a cualquiera con seek() sin leer todo el archivo.
También tiene un índice en json, exporta a json y pdf, revisa si alguien modificó
el archivo por fuera (sha256) y hace respaldos en zip.

## Cómo correrlo

pip install -r requirements.txt
python main.py
