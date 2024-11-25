import os
import pandas as pd
import qrcode
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_mysqldb import MySQL
from io import BytesIO
import os
from datetime import datetime
app = Flask(__name__)
app.secret_key = "tu_clave_secreta"
# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Cambia a tu usuario
app.config['MYSQL_PASSWORD'] = ''  # Cambia a tu contraseña
app.config['MYSQL_DB'] = 'byfa_control'  # Cambia al nombre de tu base de datos

mysql = MySQL(app)

# Configuración de la clave secreta para sesiones
save_path = 'static/QR_Visitas'
if not os.path.exists(save_path):
    os.makedirs(save_path)

# Asegurarse de que la carpeta QR_Asistencia exista
if not os.path.exists('QR_Asistencia'):
    os.makedirs('QR_Asistencia')
def obtener_datos_tabla(fecha=None):
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",  
            password="",  
            database="BYFA_CONTROL"  
        )
        cursor = conexion.cursor()
        if fecha:
            query = "SELECT Nombre, Area, Hora_Entrada, Hora_Salida, Fecha, Observaciones FROM asistencias WHERE Fecha = %s"
            cursor.execute(query, (fecha,))
        else:
            cursor.execute("SELECT Nombre, Area, Hora_Entrada, Hora_Salida, Fecha, Observaciones FROM asistencias")
        
        datos = cursor.fetchall()
        conexion.close()
        return datos
    except mysql.connector.Error as err:
        print("Error al conectar con la base de datos:", err)
        return []
def obtener_datos_tabla(fecha=None):
    try:
        cur = mysql.connection.cursor()  # Usar flask_mysqldb para la conexión
        if fecha:
            query = "SELECT Nombre, Area, Hora_Entrada, Hora_Salida, Fecha, Observaciones FROM asistencias WHERE Fecha = %s"
            cur.execute(query, (fecha,))
        else:
            query = "SELECT Nombre, Area, Hora_Entrada, Hora_Salida, Fecha, Observaciones FROM asistencias"
            cur.execute(query)
        
        datos = cur.fetchall()  # Recuperar los datos
        cur.close()  # Cerrar el cursor
        return datos
    except Exception as err:
        print("Error al conectar con la base de datos:", err)
        return []
    
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
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verificar el usuario y la contraseña en la base de datos
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Usuarios WHERE Usuario = %s AND Contrasena = %s"
        cur.execute(query, (username, password))
        user = cur.fetchone()

        if user:
            # Si el usuario existe y la contraseña es correcta
            session['user_id'] = user[0]  # Asume que el ID del usuario está en la primera columna
            return redirect(url_for('panelRH'))
        else:
            # Si el usuario o la contraseña son incorrectos
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('home'))  # Regresa al inicio de sesión si falla

@app.route('/panelRH')
def panelRH():
    # Validar si el usuario ha iniciado sesión
    if 'user_id' in session:
        return render_template('panelRH.html')  # Cargar el panel de Recursos Humanos
    else:
        flash('Debes iniciar sesión para acceder a esta página.', 'warning')
        return redirect(url_for('home'))  # Redirige al inicio de sesión si no está autenticado



@app.route('/QRAsistencia', methods=['GET', 'POST'])
def QRAsistencia():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Recoger los datos del formulario
        nombre = request.form['nombre']
        area = request.form['area']
        sueldo = request.form['sueldo']

        # Guardar los datos en la base de datos (puedes agregar esto si lo deseas)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET nombre = %s, area = %s, sueldo = %s WHERE id = %s", 
                    (nombre, area, sueldo, session['user_id']))
        mysql.connection.commit()

        flash('Datos actualizados correctamente', 'success')
        return redirect(url_for('QRAsistencia'))

    # Recuperar datos actuales del usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = %s", [session['user_id']])
    user = cur.fetchone()

    return render_template('QRAsistencia.html', user=user)

@app.route('/generate_qr', methods=['GET', 'POST'])
def generate_qr():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    qr_code_url = None  # Inicializar la variable que contiene la URL del QR generado
    qr_filename = None  # Guardará solo el nombre del archivo para la descarga

    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        area = request.form['area']
        sueldo = request.form['sueldo']

        # Generar el código QR con los datos
        qr_data = f"Nombre: {nombre} - Área: {area} - Sueldo: {sueldo}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Crear la imagen del QR
        img = qr.make_image(fill='black', back_color='white')

        # Ruta para guardar el archivo QR en static/QR_Asistencia
        qr_filename = f"{nombre}_{area}_{sueldo}.png"
        qr_file_path = os.path.join('static', 'QR_Asistencia', qr_filename)

        # Guardar la imagen en la carpeta estática
        img.save(qr_file_path)

        # Asignar la URL para mostrar la imagen en el HTML
        qr_code_url = url_for('static', filename=f'QR_Asistencia/{qr_filename}')

        # Mensaje de confirmación
        flash(f'El código QR para {nombre} en el área {area} con sueldo {sueldo} ha sido generado y guardado exitosamente.', 'success')

    return render_template('QRAsistencia.html', qr_code_url=qr_code_url, qr_filename=qr_filename)

@app.route('/generar_qr2', methods=['POST'])
def generar_qr2():
    """Genera el QR y lo guarda en la ruta especificada."""
    tarjeta = request.form.get('tarjeta', '').strip()
    usuario = request.form.get('usuario', '').strip()

    if not tarjeta or not usuario:
        flash("Por favor, complete todos los campos.", "error")
        return redirect(url_for('QRVisitas'))

    qr_data = f"{tarjeta},{usuario}"
    nombre_archivo = obtener_nombre_archivo(usuario)

    # Crear el código QR
    qr = qrcode.make(qr_data)
    qr.save(nombre_archivo)

    flash(f"Código QR generado correctamente.", "success")
    return redirect(url_for('QRVisitas', qr_file=os.path.basename(nombre_archivo)))

@app.route('/download_qr/<path:filename>')
def download_qr(filename):
    file_path = os.path.join('static', 'QR_Asistencia', filename)
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/filtrar', methods=['POST'])
def filtrar_por_fecha():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    fecha_seleccionada = request.form['fecha']
    fecha_formateada = datetime.strptime(fecha_seleccionada, "%Y-%m-%d").strftime("%Y-%m-%d")
    datos = obtener_datos_tabla(fecha_formateada)
    return render_template("panelRH.html", datos=datos)

@app.route('/exportar_excel', methods=['GET'])
def exportar_excel():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    fecha = request.args.get('fecha')
    datos_tabla = obtener_datos_tabla(fecha) if fecha else obtener_datos_tabla()

    columnas = ["Nombre", "Área", "Hora Entrada", "Hora Salida", "Fecha", "Observaciones"]
    df = pd.DataFrame(datos_tabla, columns=columnas)

    nombre_archivo = f"reporte_accesos_{fecha}.xlsx" if fecha else "reporte_accesos.xlsx"
    ruta_archivo = os.path.join('ReportesRH', nombre_archivo)
    df.to_excel(ruta_archivo, index=False)

    return send_file(ruta_archivo, as_attachment=True)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Elimina todos los datos de la sesión
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('home'))  # Redirige al usuario a la página de inicio

if __name__ == '__main__':
     app.run(debug=True) 