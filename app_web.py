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
  productos = obtener_productos_db()
  return render_template("index.html", productos=productos)


@app.route("/crear-pedido", methods=["POST"])
def crear_pedido():
  nombre_cliente = request.form.get("nombre", "Cliente Web")
  telefono_cliente = request.form.get("telefono", "")
  total_pedido = float(request.form.get("total_pedido", 0.0))

  # Generamos un código de pedido único
  codigo_pedido = f"PED-{random.randint(1000, 9999)}"

  # Guardamos el pedido en Supabase con estado PENDIENTE DE PAGO
  url_pedidos = f"{SUPABASE_URL}/rest/v1/pedidos"
  headers = {
      "apikey": SUPABASE_KEY,
      "Authorization": f"Bearer {SUPABASE_KEY}",
      "Content-Type": "application/json",
      "Prefer": "return=minimal",
  }

  payload = {
      "codigo_pedido": codigo_pedido,
      "cliente_nombre": nombre_cliente,
      "cliente_telefono": telefono_cliente,
      "total": total_pedido,
      "estado": "PENDIENTE DE PAGO",
  }

  try:
    requests.post(url_pedidos, json=payload, headers=headers)
  except Exception as e:
    print("Error al registrar pedido en Supabase:", e)

  # Enlace directo a WhatsApp con el mensaje prearmado para el negocio
  mensaje_wa = (
      f"Hola, quiero completar mi pago. Mi código de pedido es"
      f" {codigo_pedido} a nombre de {nombre_cliente} por un total de"
      f" Q{total_pedido:.2f}"
  )
  link_whatsapp = f"https://wa.me/50242001925?text={requests.utils.quote(mensaje_wa)}"

  return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Pedido Generado</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light text-center py-5">
        <div class="container card p-5 shadow" style="max-width: 600px;">
            <h2 class="text-success mb-3">¡Pedido generado con éxito!</h2>
            <p class="lead">Tu código de orden es: <strong>{codigo_pedido}</strong></p>
            <p>Cliente: <strong>{nombre_cliente}</strong></p>
            <p class="mb-4">Total a pagar: <strong class="text-primary">Q{total_pedido:.2f}</strong></p>
            
            <div class="alert alert-warning">
                Para finalizar y validar tu compra, haz clic en el botón de abajo para contactarnos vía WhatsApp con los detalles de tu pedido.
            </div>
            
            <a href="{link_whatsapp}" target="_blank" class="btn btn-success btn-lg w-100 mb-3">
                💬 Contactar por WhatsApp para completar el pago
            </a>
            <br>
            <a href="/" class="btn btn-secondary">Regresar a la Tienda</a>
        </div>
    </body>
    </html>
    """


@app.route("/tramites-en-linea")
def tramites_en_linea():
  return render_template("tramites.html")


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)