from flask import Flask, render_template, request, send_file
import os
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Ruta principal para subir el archivo CSV
@app.route('/')
def index():
    return render_template('index.html')

# Procesar el archivo y mostrar resultados
@app.route('/procesar', methods=['POST'])
def procesar():
    if 'archivo' not in request.files:
        return "No se subió ningún archivo", 400

    archivo = request.files['archivo']
    if archivo.filename == '':
        return "Archivo no válido", 400

    # Verificar la extensión del archivo
    extension = archivo.filename.split('.')[-1].lower()
    ruta_archivo = os.path.join('static', f'archivo.{extension}')
    archivo.save(ruta_archivo)

    # Leer el archivo según su extensión
    try:
        if extension == 'csv':
            datos = pd.read_csv(ruta_archivo)
        elif extension in ['xls', 'xlsx']:
            datos = pd.read_excel(ruta_archivo, engine='openpyxl')
        else:
            return "Formato de archivo no soportado. Use CSV o Excel.", 400

        # Leer la columna A completa (sin saltar ninguna fila)
        codigos = datos.iloc[:, 0].dropna().astype(str).tolist()  # Lee toda la columna A, desde la fila 1

        # Verificar la cantidad de códigos leídos
        print(f"Se han leído {len(codigos)} códigos.")  # Esto te mostrará cuántos códigos se han cargado

    except Exception as e:
        return f"Error procesando el archivo: {e}", 400

    # Generar PDF con los códigos
    ruta_pdf = generar_pdf(codigos)

    # Eliminar archivo temporal
    os.remove(ruta_archivo)

    return send_file(ruta_pdf, as_attachment=True)


# Función para generar el PDF
def generar_pdf(codigos):
    ruta_pdf = os.path.join('static', 'codigos_barras.pdf')
    c = canvas.Canvas(ruta_pdf, pagesize=A4)
    ancho, alto = A4

    x_inicial = 50
    y_inicial = alto - 100
    y_offset = 60  # Ajustar el espaciado vertical entre códigos
    codigos_por_pagina = 13 # Ajuste: más códigos por página

    for i, codigo in enumerate(codigos):
        if i > 0 and i % codigos_por_pagina == 0:
            c.showPage()  # Nueva página
            y_inicial = alto - 100

        # Generar código de barras como imagen
        codigo_barra = Code128(codigo, writer=ImageWriter())
        ruta_imagen = os.path.join('static', f'{codigo}')  # Sin la extensión .png aquí
        codigo_barra.save(ruta_imagen, {
            'module_width': 0.3,  # Ajusta el ancho de las barras del código de barras
            'font_size': 8  # Ajusta el tamaño de la fuente si es necesario
        })

        # Dibujar el código en el PDF
        c.drawImage(ruta_imagen + '.png', x_inicial, y_inicial - (i % codigos_por_pagina) * y_offset, width=300, height=50)

        # Eliminar imagen temporal
        os.remove(ruta_imagen + '.png')

    c.save()
    return ruta_pdf

if __name__ == '__main__':
    app.run(debug=True)
