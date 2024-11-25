from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import qrcode
import os

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"

# Asegurarse de que la carpeta de destino exista
save_path = 'static/QR_Visitas'
if not os.path.exists(save_path):
    os.makedirs(save_path)

def obtener_nombre_archivo(usuario):
    """Genera un nombre único para el archivo QR."""
    base_nombre = f"{save_path}/qr_visita_{usuario}"
    contador = 1
    nombre_archivo = f"{base_nombre}.png"

    while os.path.exists(nombre_archivo):
        nombre_archivo = f"{base_nombre}_{contador}.png"
        contador += 1

    return nombre_archivo

@app.route('/')
def index():
    """Página principal con el formulario."""
    return render_template('index.html')

@app.route('/generar_qr2', methods=['POST'])
def generar_qr2():
    """Genera el QR y lo guarda en la ruta especificada."""
    tarjeta = request.form.get('tarjeta', '').strip()
    usuario = request.form.get('usuario', '').strip()

    if not tarjeta or not usuario:
        flash("Por favor, complete todos los campos.", "error")
        return redirect(url_for('index'))

    qr_data = f"{tarjeta},{usuario}"
    nombre_archivo = obtener_nombre_archivo(usuario)

    # Crear el código QR
    qr = qrcode.make(qr_data)
    qr.save(nombre_archivo)

    flash(f"Código QR generado correctamente.", "success")
    return render_template('qr_visitas.html', qr_file=qr_file)

@app.route('/download/<filename>')
def download_qr(filename):
    """Permite descargar un código QR generado."""
    return send_from_directory(save_path, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

