import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# --- CREDENCIALES DE SUPABASE (Nube) ---
SUPABASE_URL = "https://hvqtvrlgvbesirifaija.supabase.co"
SUPABASE_KEY = "sb_publishable_-_9y5B7SDdLkZY_wu0sQGQ_yUflKTWW"

def obtener_productos_db():
    url = f"{SUPABASE_URL}/rest/v1/inventario?select=id,nombre,precio_venta,stock,visible_web"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Filtramos solo los productos visibles en la web (visible_web == 1 o True)
            productos_visibles = []
            for p in data:
                # Comprobamos si visible_web es True / 1 / None (por defecto visibles)
                vis = p.get("visible_web", 1)
                if vis == 1 or vis is True:
                    # Formato: (id, nombre, precio_venta, stock)
                    productos_visibles.append((
                        p.get("id"),
                        p.get("nombre"),
                        float(p.get("precio_venta", 0.0)),
                        p.get("stock", 0)
                    ))
            if productos_visibles:
                return productos_visibles
    except Exception as e:
        print("Error conectando con Supabase para inventario:", e)
    
    # Respaldo por si falla el internet en la nube
    return [
        (1, "Cuaderno Universitario 100 Hojas", 15.00, 50),
        (2, "Caja de Lápices BIC (12 unid.)", 25.00, 30),
        (3, "Set de Geometría Completo", 18.50, 20),
        (4, "Resma de Papel Bond Tamaño Carta", 42.00, 15)
    ]

def consultar_tramites_por_dpi(dpi):
    url = f"{SUPABASE_URL}/rest/v1/tramites?dpi=eq.{dpi}&select=id,dpi,nombre_cliente,tipo_tramite,costo,fecha_registro,estado"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Convertimos al formato de tuplas que espera la plantilla
            return [
                (t.get("id"), t.get("dpi"), t.get("nombre_cliente"), t.get("tipo_tramite"), t.get("costo"), t.get("fecha_registro"), t.get("estado"))
                for t in data
            ]
    except Exception as e:
        print("Error consultando trámites en Supabase:", e)
    return []

@app.route("/")
def index():
    productos = obtener_productos_db()
    return render_template("index.html", productos=productos)

@app.route("/tramites-en-linea")
def tramites_en_linea():
    servicios = [
        {"nombre": "Antecedentes Penales", "costo": 5.00, "desc": "Solicitud y gestión rápida con opción de pago."},
        {"nombre": "Antecedentes Policiacos", "costo": 35.00, "desc": "Gestión digital inmediata."},
        {"nombre": "Tarjeta de Salud", "costo": 50.00, "desc": "Asesoría y requisitos completos."},
        {"nombre": "Trámite de NIT", "costo": 30.00, "desc": "Inscripción y actualización en la SAT."},
        {"nombre": "Certificado de Nacimiento", "costo": 25.00, "desc": "Impresión oficial de RENAP."},
        {"nombre": "Pagos de RENAP", "costo": 20.00, "desc": "Gestión de boletas y certificaciones."}
    ]
    return render_template("tramites.html", servicios=servicios)

@app.route("/rastreo", methods=["GET", "POST"])
def rastreo():
    tramites = None
    dpi_buscado = ""
    if request.method == "POST":
        dpi_buscado = request.form.get("dpi", "").strip()
        if dpi_buscado:
            tramites = consultar_tramites_por_dpi(dpi_buscado)
    return render_template("rastreo.html", tramites=tramites, dpi=dpi_buscado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)