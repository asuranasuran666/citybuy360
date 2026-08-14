"""
Consulta la tasa de cambio informal (USD y EUR -> MN) en la API de elToque
y actualiza config/tasasConversion en Firebase, ademas de refrescar los
numeros y la fecha en el texto de la marquesina (solo el tramo "El TOQUE").

Se ejecuta desde GitHub Actions (ver .github/workflows/actualizar-tasa-cambio.yml).
Variables de entorno esperadas:
  ELTOQUE_TOKEN  - token de la API de elToque (guardado como secreto en GitHub)
  FIREBASE_URL   - URL base de la Realtime Database (sin barra final)
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone


def obtener_tasa_eltoque(token):
    req = urllib.request.Request(
        "https://tasas.eltoque.com/v1/trmi",
        headers={"Authorization": "Bearer " + token},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        crudo = resp.read().decode("utf-8")
    print("Respuesta cruda de elToque:")
    print(crudo)
    return json.loads(crudo)


def buscar_moneda(d, codigo):
    """Intenta varias formas comunes en que podria venir el dato de una moneda (USD/EUR)."""
    if isinstance(d, dict):
        if codigo in d:
            v = d[codigo]
            if isinstance(v, (int, float)):
                return v
            if isinstance(v, dict):
                for clave in ("venta", "promedio", "price", "value", "avg"):
                    if clave in v:
                        return v[clave]
        if "tasas" in d and isinstance(d["tasas"], dict) and codigo in d["tasas"]:
            return buscar_moneda({codigo: d["tasas"][codigo]}, codigo)
        if "data" in d:
            return buscar_moneda(d["data"], codigo)
    return None


def leer_ticker(firebase_url):
    req = urllib.request.Request(firebase_url + "/interfaz/ticker.json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def actualizar_ticker(firebase_url, tasa_usd, tasa_eur):
    """Reemplaza (o agrega) la fecha DD.MM.AAAA al inicio del texto de la marquesina
    y refresca los numeros de USD/EUR solo en el tramo 'El TOQUE', sin tocar
    el resto del texto (BANMET, etc.), que sigue siendo manual."""
    actual = leer_ticker(firebase_url)
    if not isinstance(actual, str) or not actual.strip():
        print("La marquesina no tiene texto propio (esta apagada o vacia) — no se toca.")
        return

    nuevo = actual
    hoy = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    patron_fecha = r"^\d{2}\.\d{2}\.\d{4}\s*"
    if re.match(patron_fecha, nuevo):
        nuevo = re.sub(patron_fecha, hoy + " ", nuevo, count=1)
    else:
        nuevo = hoy + " " + nuevo

    if tasa_eur is not None:
        patron_eur = r"(El TOQUE\)\s*-\s*EURO\s*)(\d+(?:\.\d+)?)(\s*MN)"
        if re.search(patron_eur, nuevo):
            nuevo = re.sub(patron_eur, lambda m: m.group(1) + str(round(tasa_eur)) + m.group(3), nuevo, count=1)
        else:
            print("⚠️ No se encontro el patron de EURO (El TOQUE) en la marquesina — no se toco ese numero.")

    if tasa_usd is not None:
        patron_usd = r"(El TOQUE\).*?-\s*USD\s*)(\d+(?:\.\d+)?)(\s*MN)"
        if re.search(patron_usd, nuevo):
            nuevo = re.sub(patron_usd, lambda m: m.group(1) + str(round(tasa_usd)) + m.group(3), nuevo, count=1)
        else:
            print("⚠️ No se encontro el patron de USD (El TOQUE) en la marquesina — no se toco ese numero.")

    if nuevo == actual:
        print("La marquesina ya estaba actualizada, no hubo cambios.")
        return

    body = json.dumps({"ticker": nuevo}).encode("utf-8")
    req = urllib.request.Request(
        firebase_url + "/interfaz.json", data=body, method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("Marquesina actualizada:", resp.read().decode("utf-8"))
        print("Texto nuevo:", nuevo)


def actualizar_firebase(firebase_url, tasa_usd, tasa_eur):
    valores = {"usd": tasa_usd}
    if tasa_eur is not None:
        valores["eur"] = tasa_eur
    body = json.dumps({"tasasConversion": valores}).encode("utf-8")
    req = urllib.request.Request(
        firebase_url + "/config.json", data=body, method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("Respuesta de Firebase:", resp.read().decode("utf-8"))


def main():
    token = os.environ.get("ELTOQUE_TOKEN", "")
    firebase_url = os.environ.get("FIREBASE_URL", "")
    if not token or not firebase_url:
        print("Faltan variables de entorno ELTOQUE_TOKEN o FIREBASE_URL")
        sys.exit(1)

    try:
        datos = obtener_tasa_eltoque(token)
    except Exception as e:
        print("Error consultando elToque:", e)
        sys.exit(1)

    tasa_usd = buscar_moneda(datos, "USD")
    tasa_eur = buscar_moneda(datos, "EUR")

    if tasa_usd is None:
        print("⚠️ No se pudo interpretar el USD de la respuesta de elToque (revisa el JSON de arriba).")
        sys.exit(1)
    if tasa_eur is None:
        print("⚠️ No se pudo interpretar el EUR de la respuesta de elToque — se sigue solo con USD.")

    print("Tasa USD detectada:", tasa_usd)
    print("Tasa EUR detectada:", tasa_eur)
    actualizar_firebase(firebase_url, tasa_usd, tasa_eur)
    print("✅ Listo. tasasConversion actualizado.")

    try:
        actualizar_ticker(firebase_url, tasa_usd, tasa_eur)
    except Exception as e:
        print("⚠️ No se pudo actualizar la marquesina:", e)


if __name__ == "__main__":
    main()
