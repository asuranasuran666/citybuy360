#!/usr/bin/env python3
"""
Agrega UN testimonio nuevo a UN producto elegido al azar del catálogo,
simulando el crecimiento orgánico natural del historial de una tienda real
(en vez de que todos los productos salgan con su historial completo desde
el día uno). Se ejecuta una vez al día vía GitHub Actions.

Usa la misma API pública de Firebase Realtime Database que ya usa
actualizar_tasa.py — no necesita token porque las reglas de /catalogo,
/ratings y /testimonios ya son de lectura/escritura pública.

Los productos marcados como Destacado tienen 3x más probabilidad de ser
elegidos (así reciben más reseñas con el tiempo, como pasaría con un
producto que de verdad vende más).
"""
import json
import os
import random
import time
import urllib.request

FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://citybuy360-default-rtdb.firebaseio.com")

NOMBRES = [
    "Yaditza R.", "Osmany P.", "Liset M.", "Reinier G.", "Yusleidys F.",
    "Ariel D.", "Yailin C.", "Leandro T.", "Marlenis V.", "Dayron S.",
    "Yosbel A.", "Niurka L.", "Alexei B.", "Yanelis Q.", "Frank H.",
    "Dianelys O.", "Ernesto M.", "Yadira P.", "Raidel C.", "Suyen G.",
]

TIPOS_PRODUCTO = [
    (["media", "calcetin", "calcetín"], "medias"),
    (["gorra", "sombrero", "cachucha"], "gorra"),
    (["ventilador"], "ventilador"),
    (["audifono", "audífono", "auricular", "bocina", "parlante", "altavoz"], "audio"),
    (["saldo", "recarga"], "recarga"),
    (["perfume", "colonia", "crema", "locion", "loción", "shampoo", "champú", "jabon", "jabón", "desodorante"], "aseo_especifico"),
    (["zapato", "tenis", "sandalia", "bota", "chancleta"], "calzado"),
    (["mochila", "bolso", "cartera", "maleta"], "bolso"),
    (["reloj"], "reloj"),
    (["juguete", "muñeca", "muneca", "carrito"], "juguete"),
    (["cargador", "cable", "power bank", "bateria portatil", "batería portátil"], "accesorio_electronico"),
    (["camisa", "camiseta", "pulover", "pulóver", "blusa", "vestido", "pantalon", "pantalón", "short", "saya", "falda"], "ropa"),
]

POOLS_TIPO = {
    "medias": ["buena tela, no aprietan para nada", "calientan bien, buena calidad", "no se han descosido después de varios lavados", "cómodas para todo el día", "buen grosor, ni muy finas ni muy gruesas", "se ven bien, además duraderas", "no se les corre el hilo", "buen ajuste, no se bajan caminando", "material suave, no pican", "aguantan bien el uso diario"],
    "gorra": ["buen ajuste, no me aprieta", "protege bien del sol", "buena tela, no destiñe con el sudor", "se ve mejor en persona que en la foto", "buen material, ligera", "me quedó cómoda, ajusta bien", "la visera es firme, no se dobla", "buen bordado, se ve de calidad", "ajustable, sirve para varias cabezas", "no destiñe con el sol"],
    "ventilador": ["buena brisa, silencioso", "la batería dura bastante", "las velocidades funcionan bien todas", "liviano y fácil de mover", "cumple lo que promete, buen producto", "se siente resistente, no es de mala calidad", "carga rápido y dura harto tiempo", "se puede colgar o poner de mesa sin problema", "buen tamaño, no ocupa mucho espacio", "funciona bien hasta en la potencia más baja"],
    "audio": ["buen sonido para el precio", "la batería aguanta bastante", "se conecta rápido por bluetooth", "cómodos, no molestan al usarlos rato largo", "cumple bien, sin cortes de sonido", "buena calidad, no esperaba tanto por el precio", "el micrófono también funciona bien", "buen alcance, no se corta la señal", "vienen con su estuche y todo", "graves buenos para el precio"],
    "recarga": ["llegó el saldo al momento, sin demora", "cómodo hacerlo todo por WhatsApp, sin salir de casa", "rápido, en minutos ya tenía el saldo", "buen servicio, sin complicaciones", "confiable, ya es la segunda vez que recargo aquí", "todo correcto, el monto llegó completo", "mejor que hacer cola en otro lado", "proceso rápido, sin vueltas", "llegó exacto lo que pedí, sin fallas", "buena opción, rápido y sin dramas"],
    "aseo_especifico": ["huele muy bien, dura bastante", "buena textura, no reseca", "rinde bastante, no se acaba rápido", "buena calidad, se nota la diferencia", "ya voy a comprar otro, me gustó bastante", "el olor se queda todo el día", "no irrita la piel, va bien", "buena presentación, se ve de calidad", "cumple lo que anuncia", "rinde más de lo que pensé"],
    "calzado": ["buena talla, ajustó como esperaba", "cómodos para caminar todo el día", "buen material, no aprietan", "se ven mejor en persona", "buena calidad para el precio", "la suela se siente resistente", "no se despegan con el uso", "buen agarre, no resbalan", "quedaron a la medida exacta", "buen acabado, se ven caros"],
    "bolso": ["buen espacio, cabe bastante", "material resistente, buen acabado", "los cierres funcionan bien", "se ve mejor en persona que en la foto", "buena calidad para lo que costó", "las costuras se ven firmes", "buen tamaño, ni muy grande ni muy chico", "los tirantes son cómodos", "buen material, no se ve barato", "aguanta bien el peso sin romperse"],
    "reloj": ["se ve bien, buen acabado", "la batería aguanta bien", "cómodo, no aprieta la muñeca", "funciona bien, sin fallas hasta ahora", "buena calidad para el precio", "la correa se siente resistente", "se ve mejor en persona", "buen tamaño de pantalla", "marca bien la hora, sin atrasarse", "buen acabado, no se ve barato"],
    "juguete": ["a mi hijo le encantó, buena calidad", "aguanta bien el uso de los niños", "buen material, no se rompió rápido", "tal cual la foto, buen tamaño", "buenos colores, buen acabado", "seguro para que jueguen sin problema", "trae buenas piezas, nada de mala calidad", "buen tamaño, ni muy chico ni muy grande"],
    "accesorio_electronico": ["funciona bien, carga rápido", "buen cable, resistente", "cumple lo que promete", "buena calidad para el precio", "no se ha dañado con el uso diario", "buen largo de cable, alcanza bien", "carga parejo, sin problemas", "buen material, se siente resistente"],
    "ropa": ["me quedó bien, la talla ajustó perfecto", "buena tela, no destiñe al lavar", "buen corte, se ve mejor en persona", "el color es igual a la foto", "cómoda, la uso seguido", "buena calidad para el precio", "no se encoge al lavarla", "buen acabado en las costuras", "la tela no se ve barata", "ajustó justo a mi talla"],
}

POR_CATEGORIA = {
    "mujer": ["me quedó divina, tal cual la talla que pedí", "la tela se siente de buena calidad, no rasca", "combina con todo, ya me la e puesto varias veces", "buen corte, no se ve barata para nada", "el color es igualito a la foto", "no se encoge ni destiñe al lavar"],
    "hombre": ["buena tela, no se destiñó al lavarla", "pedí mi talla de siempre y ajustó perfecto", "buen acabado, se ve mejor en persona", "cómoda y fresca, la uso para todo", "aguanta bien el uso diario", "buen material, no se ve barato"],
    "ninos": ["le quedó perfecta a mi niño, buena talla", "tela suave, no le dio alergia", "buena calidad para lo que cuesta", "aguanta el trote de los niños sin dañarse rápido", "buen tamaño, tal cual la talla pedida"],
    "unisex": ["se ve bien, buen acabado", "combina con todo lo que tengo", "buena calidad, no se siente barato", "ajusta bien, cómodo de usar", "buen material, se ve resistente"],
    "electronica": ["funciona excelente, la batería dura bastante", "se conecta rápido, sin interferencias", "buena calidad para el precio", "llegó bien empacado y prendió a la primera", "cumple lo que promete sin fallas"],
    "aseo": ["huele bien y rinde bastante", "buena textura, no reseca", "cumple lo que promete", "buena relación cantidad-precio", "buena presentación del producto"],
    "servicios": ["cumplieron rápido con lo acordado", "buena comunicación durante todo el proceso", "resolvieron todo sin complicaciones", "excelente atención de principio a fin", "todo salió tal cual se acordó"],
}

GENERICAS = [
    "buena atención por WhatsApp, resolvieron mis dudas rapido",
    "todo bien, cumplieron con lo prometido",
    "primera vez que compro aqui y quedé satisfecho",
    "buen trato, me explicaron todo antes de decidir",
    "rapido y sin complicaciones, todo ok",
    "me gustó que el precio en MN estaba claro desde el principio",
    "buena atención, resolvieron rápido mis dudas",
    "sin problemas con el pedido, todo en orden",
]

APERTURAS = ["", "", "", "todo bien, ", "me encantó, ", "quedé satisfecho, ", "buena experiencia, ",
             "sin quejas, ", "genial, ", "la verdad, ", "no tengo quejas, ", "todo perfecto, ",
             "super contento, ", "muy bien, "]
CIERRES = ["", "", "", ", gracias", ", recomendado", "!!", " 👍", " 😍", " 🙌",
           ", seguro repito", ", gracias por la atención", ", 100% recomendado", ", todo excelente"]


def detectar_tipo(nombre):
    n = (nombre or "").lower()
    for claves, tipo in TIPOS_PRODUCTO:
        if any(c in n for c in claves):
            return tipo
    return None


def elegir_texto(nombre_producto, seccion):
    tipo = detectar_tipo(nombre_producto)
    pool = POOLS_TIPO.get(tipo) or POR_CATEGORIA.get(seccion) or GENERICAS
    # ~20% de las veces, va genérico aunque haya pool específico
    detalle = random.choice(GENERICAS) if random.random() < 0.2 else random.choice(pool)
    return random.choice(APERTURAS) + detalle + random.choice(CIERRES)


def elegir_estrella(avg_objetivo):
    r = random.random()
    if r < 0.08:
        return 3
    if avg_objetivo >= 4.6:
        return 5 if random.random() < 0.80 else 4
    if avg_objetivo >= 4.3:
        return 5 if random.random() < 0.55 else 4
    return 5 if random.random() < 0.30 else 4


def fb_get(path):
    with urllib.request.urlopen(f"{FIREBASE_URL}/{path}.json") as r:
        return json.loads(r.read().decode())


def fb_put(path, data):
    req = urllib.request.Request(
        f"{FIREBASE_URL}/{path}.json",
        data=json.dumps(data).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)


def fb_post(path, data):
    req = urllib.request.Request(
        f"{FIREBASE_URL}/{path}.json",
        data=json.dumps(data).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)


def main():
    catalogo = fb_get("catalogo") or {}
    if not catalogo:
        print("Catálogo vacío, nada que hacer.")
        return

    ids = list(catalogo.keys())
    # Los productos Destacado tienen 3x más chance de ser elegidos.
    pesos = [3 if catalogo[pid].get("destacado") else 1 for pid in ids]
    pid = random.choices(ids, weights=pesos, k=1)[0]
    producto = catalogo[pid]

    ratings_actual = fb_get(f"ratings/{pid}") or {"total": 0, "count": 0}
    count_actual = ratings_actual.get("count", 0)
    total_actual = ratings_actual.get("total", 0)
    avg_actual = (total_actual / count_actual) if count_actual else 4.4

    estrella_nueva = elegir_estrella(avg_actual)
    nuevo_count = count_actual + 1
    nuevo_total = total_actual + estrella_nueva
    fb_put(f"ratings/{pid}", {"total": nuevo_total, "count": nuevo_count})

    testimonio = {
        "nombre": random.choice(NOMBRES),
        "texto": elegir_texto(producto.get("nombre", ""), producto.get("seccion", "")),
        "estrellas": estrella_nueva,
        "fecha": int(time.time() * 1000),
    }
    fb_post(f"testimonios/{pid}", testimonio)

    print(f"Agregado a '{producto.get('nombre', pid)}' ({pid}): {estrella_nueva}★ — \"{testimonio['texto']}\"")
    print(f"Nuevo conteo: {nuevo_count} votos, promedio {nuevo_total / nuevo_count:.2f}")


if __name__ == "__main__":
    main()
