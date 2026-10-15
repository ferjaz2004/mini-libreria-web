import os
import sqlite3
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def consultar_tramites_por_dpi(dpi):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        url = f"{supabase_url}/rest/v1/tramites?dpi=eq.{dpi}"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                resultados = []
                for item in data:
                    resultados.append((
                        item.get('id'),
                        item.get('dpi'),
                        item.get('nombre_cliente'),
                        item.get('tipo_tramite'),
                        item.get('costo'),
                        item.get('fecha_registro'),
                        item.get('estado')
                    ))
                return resultados
        except Exception as e:
            print("Error en API de Supabase:", e)
        return []
    else:
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