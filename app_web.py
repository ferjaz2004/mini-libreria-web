def consultar_tramites_por_dpi(dpi):
  database_url = os.environ.get("DATABASE_URL")

  if database_url:
    # Conexión a PostgreSQL en Supabase usando psycopg (v3)
    import psycopg

    with psycopg.connect(database_url) as conexion:
      with conexion.cursor() as cursor:
        cursor.execute(
            """
                SELECT id, dpi, nombre_cliente, tipo_tramite, costo, fecha_registro, estado 
                FROM tramites 
                WHERE dpi = %s
            """,
            (dpi,),
        )
        return cursor.fetchall()
  else:
    # Conexión local con SQLite
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