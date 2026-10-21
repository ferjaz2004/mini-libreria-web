from datetime import datetime
import json
import os
import random
import re
import requests
from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
# Llave secreta fija para mantener las sesiones activas en Render
app.secret_key = "clave_secreta_super_segura_para_mini_libreria_2026_xyz"

# --- CREDENCIALES DE SUPABASE (Nube) ---
SUPABASE_URL = "https://hvqtvrlgvbesirifaija.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2cXR2cmxndmJlc2lyaWZhaWphIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MjA4MjY3MiwiZXhwIjoyMTA3NjU4NjcyfQ.L-l2ZegBZ84yV_FRkl4RsNSGTMG0QBL7VjpUn0ONwJc"
BUCKET_CLIENTES = "tramites-clientes"


def obtener_productos_db():
  url = f"{SUPABASE_URL}/rest/v1/inventario?select=id,nombre,precio_venta,stock,visible_web,imagen_url&order=id.asc"
  headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      productos_visibles = []
      for p in data:
        vis = p.get("visible_web")
        if vis == 1 or vis is True or vis == "1":
          productos_visibles.append((
              p.get("id"),
              p.get("nombre"),
              float(p.get("precio_venta", 0.0)),
              int(p.get("stock", 0)),
              str(p.get("imagen_url", "") or ""),
          ))
      return productos_visibles
  except Exception as e:
    print("Error conectando con Supabase para inventario:", e)
  return []


@app.route("/")
def index():
  try:
    productos = obtener_productos_db()
    cliente_actual = session.get("cliente_puntos")
    return render_template(
        "index.html", productos=productos, cliente_actual=cliente_actual
    )
  except Exception as e:
    return f"Error al cargar la tienda: {e}"


@app.route("/terminos")
def terminos():
  return render_template("terminos.html")


@app.route("/registro")
def pagina_registro():
  return render_template("registro.html")


@app.route("/login")
def pagina_login():
  return render_template("login.html")


# --- RUTAS DE FIDELIZACIÓN: PUNTOS PEPEL & TINTA ---


@app.route("/registro-puntos", methods=["POST"])
def registro_puntos():
  try:
    nombre_completo = request.form.get("nombre_completo", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    password = request.form.get("password", "").strip()
    fecha_nacimiento_str = request.form.get("fecha_nacimiento", "").strip()
    telefono = request.form.get("telefono", "").strip()
    localidad = request.form.get("localidad", "").strip()

    if not nombre_completo or not correo or not password or not fecha_nacimiento_str:
      return "<h3>Error:</h3><p>Faltan campos obligatorios para el registro.</p><a href='/registro'>Regresar</a>"

    fecha_nac = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d")
    hoy = datetime.now()
    edad = (
        hoy.year
        - fecha_nac.year
        - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    )

    if edad < 15:
      return """
            <!DOCTYPE html>
            <html lang="es">
            <head><meta charset="UTF-8"><title>Registro Denegado</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
            <body class="bg-light text-center py-5">
                <div class="container card p-5 shadow" style="max-width: 500px; border-top: 5px solid #dc3545; margin: auto;">
                    <h3 class="text-danger">Registro no permitido</h3>
                    <p class="mt-3">Lo sentimos, debes tener al menos 15 años cumplidos para registrarte en <strong>Puntos Pepel & Tinta</strong>.</p>
                    <a href="/registro" class="btn btn-secondary mt-3">Regresar</a>
                </div>
            </body>
            </html>
            """

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload_cliente = {
        "serial_tarjeta": None,
        "nombre_completo": nombre_completo,
        "correo": correo,
        "password": password,
        "fecha_nacimiento": fecha_nacimiento_str,
        "telefono": telefono,
        "localidad": localidad,
        "dpi": "",
    }

    resp_insert = requests.post(
        f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion",
        json=payload_cliente,
        headers=headers,
    )
    if resp_insert.status_code not in [200, 201]:
      return f"<h3>Error al registrar cliente:</h3><p>{resp_insert.text}</p><a href='/registro'>Regresar</a>"

    return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Registrado Exitosamente</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <meta http-equiv="refresh" content="5;url=/login">
        </head>
        <body class="bg-light text-center py-5">
            <div class="container card p-5 shadow" style="max-width: 600px; border-top: 5px solid #10b981; margin: auto;">
                <h2 class="text-success mb-3">¡Registrado Exitosamente!</h2>
                <p class="lead">Te has unido a <strong>Puntos Pepel & Tinta</strong>.</p>
                <p>Serás redirigido al inicio de sesión en unos segundos...</p>
                <a href="/login" class="btn btn-primary w-100 mt-3">Ir a Iniciar Sesión Ahora</a>
            </div>
        </body>
        </html>
        """
  except Exception as e:
    return f"Error en el registro de puntos: {e}"


@app.route("/login-puntos", methods=["POST"])
def login_puntos():
  try:
    correo = request.form.get("correo", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not correo or not password:
      return redirect(url_for("pagina_login"))

    # Consulta directa y segura a Supabase
    url = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(correo)}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
      data = resp.json()
      if data and len(data) > 0:
        cliente = data[0]
        pass_en_db = str(cliente.get("password", "")).strip()

        if pass_en_db == password:
          session.permanent = True
          session["cliente_puntos"] = {
              "nombre": cliente.get("nombre_completo"),
              "serial": cliente.get("serial_tarjeta"),
              "correo": correo,
              "telefono": cliente.get("telefono", ""),
              "fecha_nacimiento": cliente.get("fecha_nacimiento", ""),
              "dpi": cliente.get("dpi", ""),
              "localidad": cliente.get("localidad", ""),
          }

          carrito_previo = cliente.get("carrito_guardado")
          if carrito_previo:
            try:
              session["carrito"] = json.loads(carrito_previo)
            except:
              session["carrito"] = []
          else:
            session["carrito"] = []

          return redirect(url_for("index"))
  except Exception as e:
    print("Error en login puntos:", e)

  return redirect(url_for("pagina_login"))


@app.route("/logout-puntos")
def logout_puntos():
  cliente = session.get("cliente_puntos")
  carrito_actual = session.get("carrito", [])
  if cliente:
    try:
      headers = {
          "apikey": SUPABASE_KEY,
          "Authorization": f"Bearer {SUPABASE_KEY}",
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
      }
      url_upd = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(cliente.get('correo'))}"
      requests.patch(
          url_upd,
          json={"carrito_guardado": json.dumps(carrito_actual)},
          headers=headers,
      )
    except Exception as e:
      print("Error al guardar carrito en logout:", e)

  session.pop("cliente_puntos", None)
  session.pop("carrito", None)
  return redirect(url_for("index"))


@app.route("/puntos-pepel-tinta")
def puntos_pepel_tinta():
  cliente = session.get("cliente_puntos")
  if not cliente:
    return redirect(url_for("pagina_login"))
  return render_template("puntos.html", cliente=cliente)


@app.route("/generar-tarjeta-online", methods=["POST"])
def generar_tarjeta_online():
  try:
    cliente = session.get("cliente_puntos")
    if not cliente:
      return redirect(url_for("pagina_login"))

    correo = cliente.get("correo")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    url_serial = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?select=serial_tarjeta&order=serial_tarjeta.desc&limit=1"
    resp_serial = requests.get(url_serial, headers=headers)

    nuevo_serial = "10000000"
    if resp_serial.status_code == 200:
      datos_ult = resp_serial.json()
      if datos_ult:
        ultimo_serial_str = datos_ult[0].get("serial_tarjeta")
        if ultimo_serial_str:
          try:
            nuevo_serial = str(int(ultimo_serial_str) + 1).zfill(8)
          except:
            pass

    url_upd = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(correo)}"
    resp_upd = requests.patch(
        url_upd, json={"serial_tarjeta": nuevo_serial}, headers=headers
    )

    if resp_upd.status_code in [200, 204]:
      cliente["serial"] = nuevo_serial
      session["cliente_puntos"] = cliente

    return redirect(url_for("puntos_pepel_tinta"))
  except Exception as e:
    print("Error al generar tarjeta online:", e)
    return redirect(url_for("puntos_pepel_tinta"))


@app.route("/actualizar-cuenta", methods=["POST"])
def actualizar_cuenta():
  try:
    cliente = session.get("cliente_puntos")
    if not cliente:
      return redirect(url_for("index"))

    correo = cliente.get("correo")
    nombre_completo = request.form.get("nombre_completo", "").strip()
    telefono = request.form.get("telefono", "").strip()
    fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
    localidad = request.form.get("localidad", "").strip()
    dpi = request.form.get("dpi", "").strip()

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload = {
        "nombre_completo": nombre_completo,
        "telefono": telefono,
        "fecha_nacimiento": fecha_nacimiento,
        "localidad": localidad,
        "dpi": dpi,
    }

    url_update = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(correo)}"
    resp = requests.patch(url_update, json=payload, headers=headers)

    if resp.status_code in [200, 204]:
      cliente["nombre"] = nombre_completo
      cliente["telefono"] = telefono
      cliente["fecha_nacimiento"] = fecha_nacimiento
      cliente["localidad"] = localidad
      cliente["dpi"] = dpi
      session["cliente_puntos"] = cliente
  except Exception as e:
    print("Error al actualizar cuenta:", e)

  return redirect(url_for("index"))


@app.route("/enlazar-tarjeta", methods=["POST"])
def enlazar_tarjeta():
  try:
    cliente = session.get("cliente_puntos")
    if not cliente:
      return redirect(url_for("index"))

    serial_existente = request.form.get("serial_existente", "").strip()
    correo = cliente.get("correo")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    url_check = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?serial_tarjeta=eq.{requests.utils.quote(serial_existente)}&select=correo"
    resp_check = requests.get(url_check, headers=headers)

    if resp_check.status_code == 200:
      data_tarj = resp_check.json()
      if data_tarj:
        propietario_actual = data_tarj[0].get("correo")
        if propietario_actual and propietario_actual != correo:
          return """
                    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Error</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
                    <body class="bg-light text-center py-5"><div class="container card p-5 shadow" style="max-width: 500px; border-top: 5px solid #dc3545; margin: auto;">
                    <h3 class="text-danger">Tarjeta no disponible</h3><p class="mt-3">Esta tarjeta ya se encuentra enlazada a otra cuenta.</p><a href='/puntos-pepel-tinta' class="btn btn-secondary mt-3">Regresar</a></div></body></html>
                    """
        else:
          url_upd = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(correo)}"
          requests.patch(
              url_upd, json={"serial_tarjeta": serial_existente}, headers=headers
          )
          cliente["serial"] = serial_existente
          session["cliente_puntos"] = cliente
      else:
        return """
                <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Error</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
                <body class="bg-light text-center py-5"><div class="container card p-5 shadow" style="max-width: 500px; border-top: 5px solid #dc3545; margin: auto;">
                <h3 class="text-danger">Tarjeta no encontrada</h3><p class="mt-3">El número de tarjeta no existe en el sistema.</p><a href='/puntos-pepel-tinta' class="btn btn-secondary mt-3">Regresar</a></div></body></html>
                """
  except Exception as e:
    print("Error al enlazar tarjeta:", e)

  return redirect(url_for("puntos_pepel_tinta"))


@app.route("/eliminar-cuenta-puntos", methods=["POST"])
def eliminar_cuenta_puntos():
  try:
    cliente = session.get("cliente_puntos")
    if not cliente:
      return redirect(url_for("index"))

    correo = cliente.get("correo")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    url_delete = f"{SUPABASE_URL}/rest/v1/clientes_fidelizacion?correo=eq.{requests.utils.quote(correo)}"
    resp = requests.delete(url_delete, headers=headers)

    if resp.status_code in [200, 204]:
      session.pop("cliente_puntos", None)
      return """
            <!DOCTYPE html>
            <html lang="es">
            <head><meta charset="UTF-8"><title>Cuenta Eliminada</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
            <body class="bg-light text-center py-5">
                <div class="container card p-5 shadow" style="max-width: 500px; border-top: 5px solid #ffc107; margin: auto;">
                    <h3 class="text-warning">Cuenta Eliminada</h3>
                    <p class="mt-3">Tu cuenta de <strong>Puntos Pepel & Tinta</strong> ha sido eliminada correctamente.</p>
                    <a href="/" class="btn btn-secondary mt-3">Regresar a la Tienda</a>
                </div>
            </body>
            </html>
            """
  except Exception as e:
    print("Excepción al eliminar cuenta:", e)

  return redirect(url_for("index"))


@app.route("/crear-pedido", methods=["POST"])
def crear_pedido():
  try:
    nombre_cliente = request.form.get("nombre", "Cliente Web")
    telefono_cliente = request.form.get("telefono", "Sin teléfono")
    total_pedido = float(request.form.get("total_pedido", 0.0))

    carrito_json = request.form.get("carrito_productos", "[]")
    try:
      carrito_productos = json.loads(carrito_json)
    except Exception:
      carrito_productos = []

    codigo_pedido = f"PED-{random.randint(1000, 9999)}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload_pedido = {
        "codigo_pedido": codigo_pedido,
        "cliente_nombre": nombre_cliente,
        "cliente_telefono": telefono_cliente,
        "total": total_pedido,
        "estado": "PENDIENTE DE PAGO",
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/pedidos", json=payload_pedido, headers=headers
    )

    if carrito_productos:
      for item in carrito_productos:
        nombre_prod = item.get("nombre", "Producto")
        cantidad_comprada = int(item.get("cantidad", 1))

        payload_detalle = {
            "codigo_pedido": codigo_pedido,
            "producto_nombre": nombre_prod,
            "cantidad": cantidad_comprada,
            "subtotal": float(item.get("precio", 0.0)) * cantidad_comprada,
        }
        requests.post(
            f"{SUPABASE_URL}/rest/v1/detalles_pedido",
            json=payload_detalle,
            headers=headers,
        )

        url_inv = f"{SUPABASE_URL}/rest/v1/inventario?nombre=eq.{requests.utils.quote(nombre_prod)}"
        resp_inv = requests.get(url_inv, headers=headers)
        if resp_inv.status_code == 200:
          inv_data = resp_inv.json()
          if inv_data:
            prod_actual = inv_data[0]
            prod_id = prod_actual.get("id")
            stock_actual = int(prod_actual.get("stock", 0))
            nuevo_stock = max(0, stock_actual - cantidad_comprada)

            url_update = f"{SUPABASE_URL}/rest/v1/inventario?id=eq.{prod_id}"
            requests.patch(
                url_update,
                json={"stock": nuevo_stock},
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                },
            )

    mensaje_wa = (
        f"Hola, mi nombre es {nombre_cliente}. Deseo completar el pago de mi"
        f" pedido con código *{codigo_pedido}*. Total: Q{total_pedido:.2f}"
    )
    link_whatsapp = (
        f"https://wa.me/50242001925?text={requests.utils.quote(mensaje_wa)}"
    )

    return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Pedido Generado</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light text-center py-5">
            <div class="container card p-5 shadow" style="max-width: 600px; border-top: 5px solid #10b981; margin: auto;">
                <h2 class="text-success mb-3">¡Pedido generado con éxito!</h2>
                <p class="lead">Tu código de orden es: <strong>{codigo_pedido}</strong></p>
                <p>Cliente: <strong>{nombre_cliente}</strong></p>
                <p class="mb-4">Total a pagar: <strong class="text-primary">Q{total_pedido:.2f}</strong></p>
                
                <div class="alert alert-warning">
                    Pedido registrado y stock descontado correctamente. Haz clic en el botón de abajo para contactarnos vía WhatsApp y completar el pago.
                </div>
                
                <a href="{link_whatsapp}" target="_blank" class="btn btn-success btn-lg w-100 mb-3" style="background-color: #25d366; border: none;">
                    💬 Contactar por WhatsApp para completar el pago
                </a>
                <br>
                <a href="/" class="btn btn-secondary w-100">Regresar a la Tienda</a>
            </div>
        </body>
        </html>
        """
  except Exception as e:
    return f"Error al procesar el pedido: {e}"


@app.route("/tramites-en-linea")
def tramites_en_linea():
  servicios = [
      {
          "nombre": "Antecedentes Penales",
          "costo": 5.00,
          "desc": "Solicitud y gestión rápida con opción de pago.",
      },
      {
          "nombre": "Antecedentes Policiacos",
          "costo": 35.00,
          "desc": "Gestión digital inmediata.",
      },
  ]
  return render_template("tramites.html", servicios=servicios)


@app.route("/crear-tramite-web", methods=["POST"])
def crear_tramite_web():
  try:
    nombre = request.form.get("nombre", "").strip()
    dpi = request.form.get("dpi", "").strip()
    correo = request.form.get("correo", "").strip()
    telefono = request.form.get("telefono", "").strip()
    nacimiento = request.form.get("nacimiento", "").strip()
    tipo_pago = request.form.get("tipo_pago", "nosotros").strip()

    tipo_tramite = "Antecedentes Penales"
    costo = 40.00 if tipo_pago == "nosotros" else 5.00
    pago_boleta = (
        "Nosotros pagamos la boleta"
        if tipo_pago == "nosotros"
        else "Boleta ya pagada por cliente"
    )
    fecha_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    estado = "Papelería recibida"

    archivo_cliente_url_final = ""
    archivo = request.files.get("archivo")
    if archivo and archivo.filename != "":
      try:
        base_nom = re.sub(
            r"[^a-zA-Z0-9_.-]", "_", os.path.basename(archivo.filename)
        )
        nombre_arc = f"cliente_{dpi}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{base_nom}"
        url_storage = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_CLIENTES}/{requests.utils.quote(nombre_arc)}"
        headers_storage = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": archivo.content_type
            or "application/octet-stream",
            "x-upsert": "true",
        }
        contenido_bytes = archivo.read()
        resp_doc = requests.post(
            url_storage, data=contenido_bytes, headers=headers_storage
        )

        if resp_doc.status_code in [200, 201]:
          archivo_cliente_url_final = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_CLIENTES}/{nombre_arc}"
        else:
          return f"<h3>Error al subir archivo a Storage:</h3><p>Código {resp_doc.status_code}: {resp_doc.text}</p><a href='/tramites-en-linea'>Regresar</a>"
      except Exception as e:
        return f"<h3>Excepción al subir archivo:</h3><p>{e}</p><a href='/tramites-en-linea'>Regresar</a>"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "dpi": dpi,
        "nombre_cliente": nombre,
        "fecha_nacimiento": nacimiento,
        "correo": correo,
        "telefono": telefono,
        "tipo_tramite": tipo_tramite,
        "pago_boleta": pago_boleta,
        "costo": costo,
        "fecha_registro": fecha_reg,
        "estado": estado,
        "archivo_cliente_url": archivo_cliente_url_final,
    }
    resp_db = requests.post(
        f"{SUPABASE_URL}/rest/v1/tramites", json=payload, headers=headers
    )
    if resp_db.status_code not in [200, 201]:
      return f"<h3>Error al guardar en la Base de Datos:</h3><p>{resp_db.text}</p><a href='/tramites-en-linea'>Regresar</a>"

    mensaje_wa = (
        f"Hola, he solicitado el trámite de *Antecedentes Penales* en"
        f" línea.%0A%0A*Nombre:* {nombre}%0A*DPI:* {dpi}%0A*Teléfono:*"
        f" {telefono}%0A*Modalidad:* {pago_boleta}%0A*Costo:* Q{costo:.2f}"
    )
    link_whatsapp = (
        f"https://wa.me/50242001925?text={requests.utils.quote(mensaje_wa)}"
    )

    return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Solicitud Enviada</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light text-center py-5">
            <div class="container card p-5 shadow" style="max-width: 600px; border-top: 5px solid #10b981; margin: auto;">
                <h2 class="text-success mb-3">¡Solicitud Registrada en el Sistema!</h2>
                <p class="lead">Tus datos y comprobante han sido enviados directamente a nuestra central de trámites.</p>
                <p>Cliente: <strong>{nombre}</strong> (DPI: {dpi})</p>
                <p class="mb-4">Costo del servicio: <strong class="text-primary">Q{costo:.2f}</strong></p>
                
                <div class="alert alert-warning">
                    El trámite y tu boleta ya están disponibles en nuestra aplicación de escritorio. Haz clic abajo para notificar por WhatsApp y dar seguimiento.
                </div>
                
                <a href="{link_whatsapp}" target="_blank" class="btn btn-success btn-lg w-100 mb-3" style="background-color: #25d366; border: none;">
                    💬 Notificar Solicitud por WhatsApp
                </a>
                <br>
                <a href="/tramites-en-linea" class="btn btn-secondary w-100">Regresar a Trámites</a>
            </div>
        </body>
        </html>
        """
  except Exception as e:
    return f"Error general al procesar la solicitud: {e}"


@app.route("/rastreo", methods=["GET", "POST"])
def rastreo():
  tramites = None
  dpi_buscado = ""
  if request.method == "POST":
    dpi_buscado = request.form.get("dpi", "").strip()
    if dpi_buscado:
      url = f"{SUPABASE_URL}/rest/v1/tramites?dpi=eq.{dpi_buscado}&select=id,dpi,nombre_cliente,tipo_tramite,costo,fecha_registro,estado,archivo_url"
      headers = {
          "apikey": SUPABASE_KEY,
          "Authorization": f"Bearer {SUPABASE_KEY}",
      }
      try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
          data = resp.json()
          tramites = []
          for t in data:
            cadena_archivos = t.get("archivo_url", "") or ""
            lista_links_descarga = []

            if cadena_archivos:
              urls_individuales = [
                  u.strip() for u in cadena_archivos.split(",") if u.strip()
              ]
              for path_archivo in urls_individuales:
                try:
                  nombre_archivo = path_archivo.split("/")[-1]
                  nombre_limpio = nombre_archivo
                  if "_" in nombre_archivo:
                    partes = nombre_archivo.split("_", 3)
                    if len(partes) > 3:
                      nombre_limpio = partes[3]

                  url_sign = f"{SUPABASE_URL}/storage/v1/object/sign/tramites-privados/{nombre_archivo}"
                  headers_storage = {
                      "apikey": SUPABASE_KEY,
                      "Authorization": f"Bearer {SUPABASE_KEY}",
                      "Content-Type": "application/json",
                  }
                  resp_sign = requests.post(
                      url_sign, json={"expiresIn": 300}, headers=headers_storage
                  )
                  if resp_sign.status_code == 200:
                    token_data = resp_sign.json()
                    signed_url_path = token_data.get("signedURL")
                    if signed_url_path:
                      link_final = f"{SUPABASE_URL}/storage/v1{signed_url_path}"
                      lista_links_descarga.append((nombre_limpio, link_final))
                except Exception as ex:
                  print("Error al generar URL firmada para archivo:", ex)

            tramites.append((
                t.get("id"),
                t.get("dpi"),
                t.get("nombre_cliente"),
                t.get("tipo_tramite"),
                float(t.get("costo", 0.0)),
                t.get("fecha_registro"),
                t.get("estado", "Papelería recibida"),
                lista_links_descarga,
            ))
      except Exception as e:
        print("Error al consultar trámites:", e)
  return render_template("rastreo.html", tramites=tramites, dpi=dpi_buscado)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)