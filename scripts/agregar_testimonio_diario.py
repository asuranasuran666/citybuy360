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
import re
import time
import urllib.request

FIREBASE_URL = os.environ.get("FIREBASE_URL", "https://citybuy360-default-rtdb.firebaseio.com")

NOMBRES_FEM = ["Yanet", "Yailin", "Yusleidy", "Yusleidys", "Yamila", "Yumisleidis", "Yordanka",
    "Yaquelin", "Yeni", "Yolanda", "Yaimara", "Marisol", "Maritza", "Caridad", "Mercedes", "María",
    "Carmen", "Ana", "Rosa", "Isabel", "Dianelys", "Niurka", "Liset", "Yadira", "Suyen", "Marlenis",
    "Dayana", "Yusimí", "Odalys", "Yenisleidis", "Xiomara", "Zoila", "Bárbara", "Aylin", "Yisel",
    "Leticia", "Nurys", "Yuliet", "Yanelis", "Yaditza", "Dianne", "Yenima", "Milagros", "Anisley"]
NOMBRES_MASC = ["Jorge Luis", "José", "Antonio", "Carlos", "Juan", "Luis", "Miguel", "Pedro",
    "Manuel", "Yosvani", "Yunier", "Yasmani", "Yoel", "Yordan", "Yordanis", "Osmany", "Reinier",
    "Alexei", "Alberto", "Roberto", "Reinaldo", "Leonel", "Maikel", "Raidel", "Yandry", "Ernesto",
    "Frank", "Ariel", "Leandro", "Dayron", "Bárbaro", "Ramón", "Rolando", "Yosbel", "Yoandry", "Dariel"]
APELLIDOS_INICIALES = ["González", "Hernández", "Rodríguez", "Martínez", "Díaz", "López", "Pérez",
    "Sánchez", "Álvarez", "Gómez", "Torres", "Reyes", "Ramírez", "Cruz", "Fernández", "Suárez",
    "Castillo", "Morales", "Ortiz", "Rojas", "Machado", "Fonseca", "Aguilar", "Pupo", "Osorio",
    "Peña", "Leyva", "Guerra", "Milán", "Columbié"]
APODOS = ["Cuqui", "Yuni", "Nany", "Pity", "Fefa", "Tato", "Bebo", "Mima", "Kiki",
    "Nene", "La Reina del Hogar", "El Tremendo", "Yuni94", "Cuqui.23", "MamiLinda", "PapiChulo05",
    "LaGuajira", "ElGuajiro", "Bombón23", "Chiqui.HAB"]


def _con_typo(palabra):
    """Simula errores de tecleo reales: letras adyacentes intercambiadas."""
    if len(palabra) < 4 or random.random() >= 0.10:
        return palabra
    i = random.randint(0, len(palabra) - 2)
    return palabra[:i] + palabra[i + 1] + palabra[i] + palabra[i + 2:]


def _variar_caso(palabra):
    r = random.random()
    if r < 0.55:
        return palabra          # normal (como lo escribió el generador)
    if r < 0.75:
        return palabra.lower()  # todo minúscula (muy común en WhatsApp/reseñas reales)
    if r < 0.90:
        return palabra.upper()  # todo mayúscula
    return palabra[0].lower() + palabra[1:]  # inicial en minúscula, resto normal


def generar_nombre():
    if random.random() < 0.15:
        return random.choice(APODOS), None
    es_fem = random.random() < 0.55
    base = NOMBRES_FEM if es_fem else NOMBRES_MASC
    nombre = _con_typo(random.choice(base))

    r = random.random()
    if r < 0.22:
        # Solo el nombre, sin apellido — muy común en reseñas reales
        completo = nombre
    elif r < 0.55:
        # Nombre + una inicial (formato no siempre igual: con/sin punto, may/min)
        inicial = random.choice(APELLIDOS_INICIALES)[0]
        formatos = [inicial + ".", inicial, inicial.lower() + "."]
        completo = nombre + " " + random.choice(formatos)
    elif r < 0.75:
        # Nombre + dos iniciales
        i1 = random.choice(APELLIDOS_INICIALES)[0]
        i2 = random.choice(APELLIDOS_INICIALES)[0]
        completo = nombre + " " + i1 + "." + i2 + "."
    else:
        # Nombre + apellido completo, a veces en minúscula (nadie corrige el autocorrector)
        apellido = random.choice(APELLIDOS_INICIALES)
        if random.random() < 0.4:
            apellido = apellido.lower()
        completo = nombre + " " + apellido

    # Variación de caso general, aplicada de vez en cuando sobre el resultado ya armado
    if random.random() < 0.18:
        completo = _variar_caso(completo)

    return completo, ("f" if es_fem else "m")

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

# ── Specs reales del producto (RAM, batería, cámara, etc.) ──────────────────
# Se extraen de "descripcion" + "detalles" cuando el producto las trae, para
# que el comentario hable del producto concreto y no solo de la satisfacción
# general — un cliente real que compró una tablet o un power bank casi
# siempre menciona algo de esto.
PATRONES_SPEC = [
    ("ram", re.compile(r'(\d+)\s?GB\s*(?:de)?\s*RAM', re.I)),
    ("almacenamiento", re.compile(r'(\d+)\s?(?:GB|TB)\s*(?:de)?\s*(?:almacenamiento|memoria interna|rom)', re.I)),
    ("bateria", re.compile(r'(\d[\d.,]*)\s?mAh', re.I)),
    ("camara", re.compile(r'(\d+)\s?(?:MP|Mpx|megap[íi]xeles)', re.I)),
    ("pantalla", re.compile(r'(\d+[.,]?\d*)\s?(?:pulgadas|")', re.I)),
    ("procesador", re.compile(r'(octa-?core|quad-?core|snapdragon\s?\w*|mediatek\s?\w*|helio\s?\w*|unisoc\s?\w*)', re.I)),
    ("carga_rapida", re.compile(r'carga\s*r[áa]pida(?:\s*(?:de)?\s*(\d+\s?W))?', re.I)),
]

FRASES_SPEC = {
    "ram": ["con {v}GB de RAM se mueve fluido, no se traba ni con varias apps abiertas",
            "los {v}GB de RAM rinden bien para el uso diario", "la RAM alcanza, no se pone lenta"],
    "almacenamiento": ["los {v}GB de almacenamiento me alcanzan bien", "buen espacio para guardar fotos y apps, {v}GB rinde"],
    "bateria": ["la batería de {v}mAh aguanta bien un día completo", "con {v}mAh no tengo que estar cargando a cada rato",
                "el power bank de {v}mAh carga el teléfono varias veces sin problema"],
    "camara": ["la cámara de {v}MP se ve bien en fotos de día", "las fotos con la cámara de {v}MP salen nítidas"],
    "pantalla": ["la pantalla de {v} pulgadas se ve nítida", "buen tamaño de pantalla, {v} pulgadas es cómodo para ver videos"],
    "procesador": ["con el {v} anda fluido, no se traba", "el {v} responde bien, sin demoras"],
    "carga_rapida": ["carga bastante rápido, se agradece", "la carga rápida sí se nota, en poco rato ya tiene batería"],
}


def extraer_specs(texto):
    specs = {}
    for clave, patron in PATRONES_SPEC:
        m = patron.search(texto or "")
        if m and m.groups() and m.group(1):
            specs[clave] = m.group(1)
        elif m:
            specs[clave] = ""
    return specs


def frase_spec(specs):
    """Elige una spec al azar de las encontradas y arma la frase con su valor."""
    clave = random.choice(list(specs.keys()))
    valor = specs[clave]
    plantilla = random.choice(FRASES_SPEC[clave])
    return plantilla.format(v=valor) if "{v}" in plantilla and valor else random.choice(FRASES_SPEC[clave]).replace("{v} ", "").replace("{v}", "")

# Cuando el género del nombre no coincide con la sección del producto (ej:
# nombre de mujer en ropa de hombre), se reencuadra como compra para alguien
# más, en vez de hablar en primera persona de cómo le queda a ella/él.
RELACIONAL_HOMBRE = [
    "a mi esposo le quedó bien, buena tela",
    "se lo compré a mi novio y le gustó",
    "mi esposo lo usa seguido, buena calidad",
    "a mi esposo le encantó, buen corte",
    "se lo llevé a mi novio, buena tela",
    "mi esposo dice que es cómoda, buena calidad",
]
RELACIONAL_MUJER = [
    "se lo compré a mi mamá y le encantó",
    "mi hija quedó feliz con esto",
    "a mi mamá le gustó mucho, buena calidad",
    "se lo llevé a mi hija y le quedó bien",
    "mi mamá lo usa seguido, buena tela",
    "a mi hija le encantó el color",
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


def _con_faltas_ortograficas(texto):
    """Ruido ortográfico ocasional — tildes perdidas, abreviaturas informales."""
    if random.random() < 0.25:
        for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")]:
            texto = texto.replace(a, b)
    if random.random() < 0.12:
        texto = re.sub(r'\bque\b', 'q', texto)
        texto = re.sub(r'\bporque\b', 'xq', texto)
    return texto


def elegir_texto(nombre_producto, seccion, genero=None, descripcion="", detalles=""):
    specs = extraer_specs((descripcion or "") + " " + (detalles or ""))

    if specs and random.random() < 0.7:
        # La mayoría de las veces que hay specs reales, el comentario las menciona
        detalle = frase_spec(specs)
    elif seccion == "hombre" and genero == "f":
        detalle = random.choice(RELACIONAL_HOMBRE)
    elif seccion == "mujer" and genero == "m":
        detalle = random.choice(RELACIONAL_MUJER)
    else:
        tipo = detectar_tipo(nombre_producto)
        pool = POOLS_TIPO.get(tipo) or POR_CATEGORIA.get(seccion) or GENERICAS
        # ~20% de las veces, va genérico aunque haya pool específico
        detalle = random.choice(GENERICAS) if random.random() < 0.2 else random.choice(pool)

    texto = random.choice(APERTURAS) + detalle + random.choice(CIERRES)
    return _con_faltas_ortograficas(texto)


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

    nombre_gen, genero = generar_nombre()
    testimonio = {
        "nombre": nombre_gen,
        "texto": elegir_texto(producto.get("nombre", ""), producto.get("seccion", ""), genero,
                              producto.get("descripcion", ""), producto.get("detalles", "")),
        "estrellas": estrella_nueva,
        "fecha": int(time.time() * 1000),
    }
    fb_post(f"testimonios/{pid}", testimonio)

    print(f"Agregado a '{producto.get('nombre', pid)}' ({pid}): {estrella_nueva}★ — \"{testimonio['texto']}\"")
    print(f"Nuevo conteo: {nuevo_count} votos, promedio {nuevo_total / nuevo_count:.2f}")


if __name__ == "__main__":
    main()
