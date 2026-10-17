#!/usr/bin/env python3
"""
Destacado temporal para productos de poco movimiento.

Una vez por semana (GitHub Actions):
  1. Quita el destacado a los productos que este mismo script marcó antes
     (solo los que llevan destacadoTemporal=true: los destacados que pones tú
     a mano nunca se tocan).
  2. Elige hasta 4 productos con menos movimiento y los marca destacados
     por 7 días.
  3. Deja una alerta en alertasAdmin con lo que puso y lo que quitó.

"Movimiento" = cuánto subió el contador sales/{id} (clics en "Lo quiero")
desde la foto de la semana anterior. Ese contador no guarda fechas, por eso
el script guarda una foto cada corrida en config/destacadoTemporal.
La primera vez, sin foto previa, usa el contador acumulado como aproximación.

Variables opcionales: DRY_RUN=1 (solo imprime, no escribe), CUPO (default 4),
DIAS (default 7).
"""
import json
import os
import random
import time
import urllib.request
from datetime import date, timedelta

FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://citybuy360-default-rtdb.firebaseio.com")
CUPO = int(os.environ.get("CUPO", "4"))
DIAS = int(os.environ.get("DIAS", "7"))
DRY_RUN = os.environ.get("DRY_RUN") == "1"
ESTADO_PATH = "config/destacadoTemporal"


def fb_get(path):
    with urllib.request.urlopen(f"{FIREBASE_URL}/{path}.json") as r:
        return json.loads(r.read().decode())


def _enviar(metodo, path, data):
    if DRY_RUN:
        print(f"[DRY_RUN] {metodo} {path}: {json.dumps(data, ensure_ascii=False)[:200]}")
        return
    req = urllib.request.Request(
        f"{FIREBASE_URL}/{path}.json",
        data=json.dumps(data).encode(),
        method=metodo,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)


def fb_patch(path, data):
    _enviar("PATCH", path, data)


def fb_put(path, data):
    _enviar("PUT", path, data)


def fb_post(path, data):
    _enviar("POST", path, data)


def _stocks(valor, acumulado):
    """Junta todos los campos 'stock' numéricos de las variantes, sea cual sea su forma."""
    if isinstance(valor, dict):
        for k, v in valor.items():
            if k == "stock" and isinstance(v, (int, float)):
                acumulado.append(v)
            else:
                _stocks(v, acumulado)
    elif isinstance(valor, list):
        for v in valor:
            _stocks(v, acumulado)


def esta_agotado(producto):
    stocks = []
    _stocks(producto.get("variantesMatriz"), stocks)
    _stocks(producto.get("variantes"), stocks)
    return bool(stocks) and all(s <= 0 for s in stocks)


def es_elegible(pid, p, cfg_productos, activos):
    if not isinstance(p, dict) or not p.get("nombre"):
        return False
    if pid in activos:
        return False
    if p.get("activo") is False or p.get("proximaVenta"):
        return False
    if p.get("seccion") == "acceso360":      # el VIP no se mezcla con esto
        return False
    if (cfg_productos.get(pid) or {}).get("active") is False:
        return False
    if p.get("destacado"):                    # ya destacado (a mano): no se toca
        return False
    if esta_agotado(p):
        return False
    return True


def main():
    hoy = date.today()
    hoy_iso = hoy.isoformat()
    hasta_iso = (hoy + timedelta(days=DIAS)).isoformat()

    catalogo = fb_get("catalogo") or {}
    ventas = fb_get("sales") or {}
    cfg_productos = fb_get("config/products") or {}
    estado = fb_get(ESTADO_PATH) or {}

    foto_previa = estado.get("snapshot") or {}
    activos = dict(estado.get("activos") or {})
    ultimos = set(estado.get("ultimos") or [])

    # 1. Quitar los temporales vencidos
    quitados = []
    for pid, hasta in list(activos.items()):
        if hasta <= hoy_iso:
            p = catalogo.get(pid)
            if p and p.get("destacadoTemporal"):
                fb_patch(f"catalogo/{pid}", {"destacado": False, "destacadoTemporal": None, "destacadoHasta": None})
                quitados.append(p.get("nombre", pid))
                p["destacado"] = False
            del activos[pid]

    # 2. Elegir los de menor movimiento
    def movimiento(pid):
        total = ventas.get(pid, 0) or 0
        if foto_previa:
            return total - (foto_previa.get(pid, 0) or 0)
        return total

    candidatos = [pid for pid, p in catalogo.items() if es_elegible(pid, p, cfg_productos, activos)]
    candidatos.sort(key=lambda pid: (movimiento(pid), 1 if pid in ultimos else 0, random.random()))

    cupo_libre = max(0, CUPO - len(activos))
    elegidos = candidatos[:cupo_libre]

    for pid in elegidos:
        fb_patch(f"catalogo/{pid}", {"destacado": True, "destacadoTemporal": True, "destacadoHasta": hasta_iso})
        activos[pid] = hasta_iso

    # 3. Guardar estado (foto de ventas + rotación actual)
    fb_put(ESTADO_PATH, {
        "snapshot": {pid: (ventas.get(pid, 0) or 0) for pid in catalogo},
        "snapshotFecha": hoy_iso,
        "activos": activos,
        "ultimos": elegidos,
    })

    # 4. Alerta para el admin
    nombres = [catalogo[pid].get("nombre", pid) for pid in elegidos]
    partes = []
    if nombres:
        partes.append(f"⭐ Destacado temporal hasta {hasta_iso}: " + ", ".join(nombres))
    if quitados:
        partes.append("Quitados: " + ", ".join(quitados))
    if not partes:
        partes.append("⭐ Destacado temporal: esta semana no hubo productos elegibles")
    fb_post("alertasAdmin", {"texto": " · ".join(partes), "fecha": int(time.time() * 1000), "leida": False})

    print("Elegidos:", nombres)
    print("Quitados:", quitados)


if __name__ == "__main__":
    main()
