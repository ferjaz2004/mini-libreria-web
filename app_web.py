import os
import sqlite3
import urllib.parse
from flask import Flask, render_template, request

app = Flask(__name__)


def consultar_tramites_por_dpi(dpi):
  database_url = os.environ.get("DATABASE_URL")

  if database_url:
    # Conexión a Supabase usando pg8000 (Python puro, sin errores de compilación)
    import pg8000.dbapi

    url = urllib.parse.urlparse(database_url)
    password = urllib.parse.unquote(url.password) if url.password else None

    conexion = pg8000.dbapi.connect(
        database=url.path[1:],
        user=url.username,
        password=password,
        host=url.hostname,
        port=url.port or 5432,
    )
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
    # Conexión local con SQLite para tu PC
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