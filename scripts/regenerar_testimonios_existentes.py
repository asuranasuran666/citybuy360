#!/usr/bin/env python3
"""
Script de UN SOLO USO: recorre los testimonios YA EXISTENTES en Firebase y
reescribe el texto de los que hablan solo del servicio, para que en cada
producto ~80% hable del producto y como maximo ~20% del servicio.

Por cada producto:
  - Cuenta cuantos testimonios son "solo servicio" (atencion, WhatsApp,
    pedido, etc., sin nada del producto).
  - Deja intactos hasta el 20% del total (elegidos al azar) y reescribe
    el resto con frases del producto (specs reales si las hay, o frases
    por tipo de producto / seccion).
  - Reescribe tambien los textos mal formados (ej. "la bateria de mAh").
No toca nombre, estrellas ni fecha: solo el campo "texto".

Uso: DRY_RUN=1 para solo imprimir sin escribir. No es un cron: se lanza a
mano ("Run workflow" en GitHub Actions) y no se vuelve a necesitar.
"""
import json
import os
import random
import re
import sys
import unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agregar_testimonio_diario import elegir_texto

FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://citybuy360-default-rtdb.firebaseio.com")
DRY_RUN = os.environ.get("DRY_RUN") == "1"
MAX_SERVICIO = 0.20

# Fragmentos (sin tildes, minusculas) que delatan una frase de servicio
FRAGMENTOS_SERVICIO = [
    "atencion por whatsapp", "buena atencion", "cumplieron con lo prometido", "primera vez que compro",
    "me explicaron todo", "sin complicaciones", "precio en mn", "resolvieron", "sin problemas con el pedido",
    "rapido y sin", "buen trato", "gracias por la atencion",
]
# Textos mal formados que hay que rehacer
MAL_FORMADOS = [r"de\s*mah", r"de\s*mp\b", r"de\s+pulgadas", r"de\s*gb\b", r"\{v\}", r"con\s+de\s"]


def norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def es_servicio(texto):
    n = norm(texto)
    return any(f in n for f in FRAGMENTOS_SERVICIO)


def esta_mal_formado(texto):
    n = norm(texto)
    return any(re.search(p, n) for p in MAL_FORMADOS)


def fb_get(path):
    with urllib.request.urlopen(f"{FIREBASE_URL}/{path}.json") as r:
        return json.loads(r.read().decode())


def fb_patch(path, data):
    if DRY_RUN:
        return
    req = urllib.request.Request(
        f"{FIREBASE_URL}/{path}.json",
        data=json.dumps(data).encode(),
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)


def main():
    catalogo = fb_get("catalogo") or {}
    revisados = reescritos = 0

    for pid, producto in catalogo.items():
        if not isinstance(producto, dict):
            continue
        testimonios = fb_get(f"testimonios/{pid}") or {}
        if not testimonios:
            continue

        total = len(testimonios)
        revisados += total
        servicio = [k for k, t in testimonios.items() if es_servicio(t.get("texto"))]
        malos = [k for k, t in testimonios.items() if esta_mal_formado(t.get("texto"))]

        permitidos = int(total * MAX_SERVICIO)
        random.shuffle(servicio)
        a_reescribir = set(servicio[permitidos:]) | set(malos)

        for tkey in a_reescribir:
            t = testimonios[tkey]
            nuevo = elegir_texto(
                producto.get("nombre", ""), producto.get("seccion", ""), None,
                producto.get("descripcion", ""), producto.get("detalles", ""),
                solo_producto=True,
            )
            fb_patch(f"testimonios/{pid}/{tkey}", {"texto": nuevo})
            reescritos += 1
            print(f"[{pid}/{tkey}] {t.get('texto','')!r} -> {nuevo!r}")

    print(f"\nRevisados: {revisados} — Reescritos: {reescritos}" + (" (DRY_RUN, nada escrito)" if DRY_RUN else ""))


if __name__ == "__main__":
    main()
