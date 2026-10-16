import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

def obtener_productos_db():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'mini_libreria.db')
    try:
        with sqlite3.connect(db_path) as conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventario'")
            if cursor.fetchone():
                # Verificamos si la columna visible_web existe para evitar errores
                cursor.execute("PRAGMA table_info(inventario)")
                columnas = [info[1] for info in cursor.fetchall()]

                if 'visible_web' in columnas:
                    cursor.execute("SELECT id, nombre, precio_venta, stock FROM inventario WHERE visible_web = 1")
                else:
                    cursor.execute("SELECT id, nombre, precio_venta, stock FROM inventario")

                productos = cursor.fetchall()
                if productos:
                    return productos
    except Exception as e:
        print("Error leyendo inventario local:", e)
    
    return [
        (1, "Cuaderno Universitario 100 Hojas", 15.00, 50),
        (2, "Caja de Lápices BIC (12 unid.)", 25.00, 30),
        (3, "Set de Geometría Completo", 18.50, 20),
        (4, "Resma de Papel Bond Tamaño Carta", 42.00, 15)
    ]

def consultar_tramites_por_dpi(dpi):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'mini_libreria.db')
    with sqlite3.connect(db_path) as conexion:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, dpi, nombre_cliente, tipo_tramite, costo, fecha_registro, estado 
            FROM tramites 
            WHERE dpi = ?
        """, (dpi,))
        return cursor.fetchall()

@app.route("/")
def index():
    productos = obtener_productos_db()
    return render_template("index.html", productos=productos)

@app.route("/tramites-en-linea")
def tramites_en_linea():
    servicios = [
        {"nombre": "Antecedentes Penales", "costo": 5.00, "desc": "Solicitud y gestión rápida con opción de pago."},
        {"nombre": "Antecedentes Policiacos", "costo": 35.00, "desc": "Gestión digital inmediata."},
        {"nombre": "Tarjeta de Salud", "costo": 50.00, "desc": "Asesoría y requisitos completos."},
        {"nombre": "Trámite de NIT", "costo": 30.00, "desc": "Inscripción y actualización en la SAT."},
        {"nombre": "Certificado de Nacimiento", "costo": 25.00, "desc": "Impresión oficial de RENAP."},
        {"nombre": "Pagos de RENAP", "costo": 20.00, "desc": "Gestión de boletas y certificaciones."}
    ]
    return render_template("tramites.html", servicios=servicios)

@app.route("/rastreo", methods=["GET", "POST"])
def rastreo():
    tramites = None
    dpi_buscado = ""
    if request.method == "POST":
        dpi_buscado = request.form.get("dpi", "").strip()
        if dpi_buscado:
            tramites = consultar_tramites_por_dpi(dpi_buscado)
    return render_template("rastreo.html", tramites=tramites, dpi=dpi_buscado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)