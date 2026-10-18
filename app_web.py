from datetime import datetime
import json
import os
import random
import re
import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# --- CREDENCIALES DE SUPABASE (Nube) ---
SUPABASE_URL = "https://hvqtvrlgvbesirifaija.supabase.co"
SUPABASE_KEY = "sb_publishable_-_9y5B7SDdLkZY_wu0sQGQ_yUflKTWW"
BUCKET_CLIENTES = "tramites-clientes"  # <--- Bucket exclusivo para los archivos del cliente


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
    return render_template("index.html", productos=productos)
  except Exception as e:
    return f"Error al cargar la tienda: {e}"


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
            "Content-Type": "application/octet-stream",
            "x-upsert": "true",
        }
        contenido_bytes = archivo.read()
        resp_doc = requests.post(
            url_storage, data=contenido_bytes, headers=headers_storage
        )
        if resp_doc.status_code in [200, 201]:
          archivo_cliente_url_final = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_CLIENTES}/{nombre_arc}"
      except Exception as e:
        print("Error al subir boleta del cliente desde la web:", e)

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
    requests.post(f"{SUPABASE_URL}/rest/v1/tramites", json=payload, headers=headers)

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
    return f"Error al procesar la solicitud de trámite: {e}"


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