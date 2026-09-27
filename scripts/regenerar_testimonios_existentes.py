#!/usr/bin/env python3
"""
Script de UN SOLO USO: recorre los testimonios YA EXISTENTES en Firebase y
regenera el texto de los que sean genéricos (sin mencionar specs reales del
producto), usando la misma lógica de agregar_testimonio_diario.py.

No toca nombre, estrellas ni fecha — solo el campo "texto", y solo si el
producto tiene specs extraíbles (RAM, mAh, MP, pulgadas, procesador, carga
rápida) que el testimonio actual todavía no menciona.

No es un cron: se corre una vez a mano (o vía "Run workflow" manual en
GitHub Actions) y no se vuelve a necesitar después.
"""
import json
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agregar_testimonio_diario import (
    extraer_specs, frase_spec, _con_faltas_ortograficas, APERTURAS, CIERRES,
)

FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://citybuy360-default-rtdb.firebaseio.com")


def fb_get(path):
    with urllib.request.urlopen(f"{FIREBASE_URL}/{path}.json") as r:
        return json.loads(r.read().decode())


def fb_patch(path, data):
    req = urllib.request.Request(
        f"{FIREBASE_URL}/{path}.json",
        data=json.dumps(data).encode(),
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)


def main():
    catalogo = fb_get("catalogo") or {}
    total_regenerados = 0
    total_revisados = 0

    for pid, producto in catalogo.items():
        specs = extraer_specs((producto.get("descripcion", "") or "") + " " + (producto.get("detalles", "") or ""))
        if not specs:
            continue  # sin specs reales que mencionar, no hay nada que mejorar aquí

        testimonios = fb_get(f"testimonios/{pid}") or {}
        if not testimonios:
            continue

        for tkey, t in testimonios.items():
            total_revisados += 1
            texto_actual = (t.get("texto") or "").lower()
            ya_menciona_spec = any(v and str(v).lower() in texto_actual for v in specs.values())
            if ya_menciona_spec:
                continue

            if random.random() < 0.7:
                detalle = frase_spec(specs)
                nuevo_texto = _con_faltas_ortograficas(
                    random.choice(APERTURAS) + detalle + random.choice(CIERRES)
                )
                fb_patch(f"testimonios/{pid}/{tkey}", {"texto": nuevo_texto})
                total_regenerados += 1
                print(f"[{pid}/{tkey}] {t.get('texto','')!r} -> {nuevo_texto!r}")

    print(f"\nRevisados: {total_revisados} — Regenerados: {total_regenerados}")


if __name__ == "__main__":
    main()
