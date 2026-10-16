from datetime import datetime
import json
import os
import random
import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# --- CREDENCIALES DE SUPABASE (Nube) ---
SUPABASE_URL = "https://hvqtvrlgvbesirifaija.supabase.co"
SUPABASE_KEY = "sb_publishable_-_9y5B7SDdLkZY_wu0sQGQ_yUflKTWW"


def obtener_productos_db():
  url = (
      f"{SUPABASE_URL}/rest/v1/inventario?select=id,nombre,precio_venta,stock,visible_web"
  )
  headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      productos_visibles = []
      for p in data:
        vis = p.get("visible_web", 1)
        if vis == 1 or vis is True:
          productos_visibles.append((
              p.get("id"),
              p.get("nombre"),
              float(p.get("precio_venta", 0.0)),
              p.get("stock", 0),
          ))
      if productos_visibles:
        return productos_visibles
  except Exception as e:
    print("Error conectando con Supabase para inventario:", e)

  return [
      (1, "Cuaderno Universitario 100 Hojas", 15.00, 50),
      (2, "Caja de Lápices BIC (12 unid.)", 25.00, 30),
  ]


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

    # Recibimos el carrito enviado desde el index.html
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

    # 1. Insertar pedido principal en la tabla 'pedidos'
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

    # 2. Insertar cada producto comprado en la tabla 'detalles_pedido'
    if carrito_productos:
      for item in carrito_productos:
        payload_detalle = {
            "codigo_pedido": codigo_pedido,
            "producto_nombre": item.get("nombre", "Producto"),
            "cantidad": int(item.get("cantidad", 1)),
            "subtotal": float(item.get("precio", 0.0))
            * int(item.get("cantidad", 1)),
        }
        requests.post(
            f"{SUPABASE_URL}/rest/v1/detalles_pedido",
            json=payload_detalle,
            headers=headers,
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
                    Pedido y detalles registrados correctamente en el sistema. Haz clic en el botón de abajo para contactarnos vía WhatsApp y completar el pago.
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


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)