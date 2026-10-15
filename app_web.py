import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


def consultar_tramites_por_dpi(dpi):
  # Verificamos si estamos en Render (si existe la variable de entorno DATABASE_URL)
  database_url = os.environ.get("DATABASE_URL")

  if database_url:
    # Conexión a PostgreSQL en Supabase (para la nube)
    import psycopg2

    conexion = psycopg2.connect(database_url)
    cursor = conexion.cursor()
    cursor.execute(
        """
            SELECT id, dpi, nombre_cliente, tipo_tramite, costo, fecha_registro, estado 
            FROM tramites 
            WHERE dpi = %s
        """,
        (dpi,),
    )
    resultados = cursor.fetchall()
    conexion.close()
    return resultados
  else:
    # Conexión local con SQLite (para cuando lo pruebes en tu computadora)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "mini_libreria.db")
    with sqlite3.connect(db_path) as conexion:
      cursor = conexion.cursor()
      cursor.execute(
          """
                SELECT id, dpi, nombre_cliente, tipo_tramite, costo, fecha_registro, estado 
                FROM tramites 
                WHERE dpi = ?
            """,
          (dpi,),
      )
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