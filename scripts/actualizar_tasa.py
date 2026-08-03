"""
Consulta la tasa de cambio informal (USD -> MN) en la API de elToque
y actualiza config/tasasConversion en Firebase.

Se ejecuta desde GitHub Actions (ver .github/workflows/actualizar-tasa-cambio.yml).
Variables de entorno esperadas:
  ELTOQUE_TOKEN  - token de la API de elToque (guardado como secreto en GitHub)
  FIREBASE_URL   - URL base de la Realtime Database (sin barra final)
"""
import json
import os
import sys
import urllib.request


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


def buscar_usd(d):
    """Intenta varias formas comunes en que podría venir el dato de USD."""
    if isinstance(d, dict):
        if "USD" in d:
            v = d["USD"]
            if isinstance(v, (int, float)):
                return v
            if isinstance(v, dict):
                for clave in ("venta", "promedio", "price", "value", "avg"):
                    if clave in v:
                        return v[clave]
        if "tasas" in d and isinstance(d["tasas"], dict) and "USD" in d["tasas"]:
            return buscar_usd({"USD": d["tasas"]["USD"]})
        if "data" in d:
            return buscar_usd(d["data"])
    return None


def actualizar_firebase(firebase_url, tasa_usd):
    body = json.dumps({"tasasConversion": {"usd": tasa_usd}}).encode("utf-8")
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

    tasa_usd = buscar_usd(datos)
    if tasa_usd is None:
        print("⚠️ No se pudo interpretar la respuesta de elToque (revisa el JSON de arriba).")
        sys.exit(1)

    print("Tasa USD detectada:", tasa_usd)
    actualizar_firebase(firebase_url, tasa_usd)
    print("✅ Listo. Tasa actualizada a", tasa_usd, "MN por USD.")


if __name__ == "__main__":
    main()
