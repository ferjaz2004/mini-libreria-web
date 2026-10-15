from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

def consultar_tramites_por_dpi(dpi):
    # Usamos ruta absoluta para asegurar que encuentre la base de datos en cualquier servidor
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

@app.route("/", methods=["GET", "POST"])
def index():
    tramites = None
    dpi_buscado = ""
    if request.method == "POST":
        dpi_buscado = request.form.get("dpi", "").strip()
        if dpi_buscado:
            tramites = consultar_tramites_por_dpi(dpi_buscado)
    return render_template("index.html", tramites=tramites, dpi=dpi_buscado)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)