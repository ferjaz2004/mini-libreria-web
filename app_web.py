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
  # Recibimos los datos del formulario web o carrito
  nombre_cliente = request.form.get("nombre", "Cliente Web")
  telefono_cliente = request.form.get("telefono", "")

  # Generamos un código de pedido único
  codigo_pedido = f"PED-{random.randint(1000, 9999)}"

  # Aquí puedes procesar los productos del carrito que envía tu HTML
  # Ejemplo simulado de total:
  total_pedido = float(request.form.get("total_pedido", 0.0))

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

  return render_template(
      "pedido_exitoso.html",
      codigo=codigo_pedido,
      nombre=nombre_cliente,
      total=total_pedido,
  )


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