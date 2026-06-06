# CITYBUY360 — Estado del Proyecto

**URL:** https://citybuy360.onrender.com  
**Admin:** https://citybuy360.onrender.com/admin.html  
**VIP:** https://citybuy360.onrender.com/acceso360.html  
**Repo:** https://github.com/asuranasuran666/citybuy360

---

## Stack

| Tecnología | Uso |
|-----------|-----|
| HTML / CSS / JS | Frontend completo en archivos estáticos |
| Firebase Realtime DB | Ratings, visitas, ventas, config, precios, interfaz, acceso360, mensajes |
| GitHub API | Publicar y editar productos desde el admin |
| Render | Hosting con deploy automático desde GitHub |
| Chart.js | Gráficas en el admin |
| EmailJS | Envío de correos de acceso VIP desde el admin |

---

## Archivos clave

| Archivo | Qué es |
|--------|--------|
| `index.html` | Catálogo completo |
| `admin.html` | Panel de administración |
| `acceso360.html` | Página VIP exclusiva para miembros |
| `backups/` | Copias automáticas del index antes de cada cambio |
| `*.jpg / *.jpeg` | Fotos de productos en la raíz |

---

## Flujo de trabajo Git

```bash
git fetch origin
git reset --hard origin/main   # SIEMPRE antes de copiar archivos nuevos
# ... copiar archivos descargados ...
git add .
git commit -m "descripcion"
git push
```

**NUNCA** usar `git pull` con cambios locales sin hacer stash primero.

---

## Firebase — estructura de datos

```
ratings/{producto}              → votos y promedio de estrellas
analytics/visits/YYYY-MM-DD    → visitas diarias (excluye admin)
sales/{producto}               → clics en "Lo quiero" por producto
config/sections/{id}           → activo/inactivo + fecha expiración
config/products/{id}           → activo/inactivo + fecha expiración
config/categorias/{val}        → categorías de género personalizadas
prices/{producto}              → precio editable desde admin
interfaz/                      → catbar, slider, acceso360, bottomnav, ribbons ON/OFF
interfaz/ribbon1               → texto del ribbon 1
interfaz/ribbon2               → texto del ribbon 2
interfaz/ribbon1active         → true/false
interfaz/ribbon2active         → true/false
interfaz/tasas                 → true/false — card tasas de cambio
interfaz/ticker                → texto marquesina o false para desactivar
acceso360/seccionActiva        → legacy (ahora usa acceso360.html)
acceso360/codes/{codigo}       → true/false — códigos de acceso válidos
acceso360/clientes/{codigo}    → correo, referencia, fecha, expira
acceso360/solicitudes/{id}     → correo, fecha, estado (pendiente/procesando)
mensajes/{id}                  → texto, fecha — mensajes de la tienda
```

### Reglas Firebase
```json
{
  "rules": {
    "ratings":    { ".read": true, ".write": true },
    "config":     { ".read": true, ".write": true },
    "analytics":  { ".read": true, ".write": true },
    "sales":      { ".read": true, ".write": true },
    "prices":     { ".read": true, ".write": true },
    "interfaz":   { ".read": true, ".write": true },
    "acceso360":  { ".read": true, ".write": true },
    "mensajes":   { ".read": true, ".write": true }
  }
}
```

---

## Secciones del catálogo

| ID | Nombre | Productos |
|----|--------|-----------|
| `destacado` | ⭐ Lo más destacado | variable |
| `ropa-interior` | 👙 Ropa Interior | blumer, sujetador |
| `ropa-moda` | 👕 Ropa y Moda | paris, ngu, gdm, aac, usa, freedom, mblancas, mnegras |
| `accesorios` | 👜 Accesorios | bolsomovil, gorrobebe, gorra |
| `servicios` | ⚡ Servicios | saldo, citybuy360familia, tasas |
| `acceso360` | ✦ Acceso 360 | ventilador (y más por publicar) |

---

## Categorías de género (filtros)

`mujer` · `hombre` · `unisex` · `ninos` · `electrodomesticos` · `aseo` · `servicios`

Se añaden nuevas desde el admin en Tab Nuevo Producto → campo Categoría.

---

## ACCESO 360 — Flujo completo

1. Cliente compra → confirmas el pago
2. Le mandas WhatsApp con link a la tienda + oferta VIP
3. En la tienda pulsa el modal VIP → introduce su correo → queda en lista de espera
4. Tú en el admin (Tab Acceso 360) ves la solicitud → pulsas "Generar acceso ✦"
5. Admin genera código `CB360-XXXXX` + preview del correo profesional
6. Pulsas "📧 Enviar correo de acceso" → sale por EmailJS desde `citybuy360.contacto@gmail.com`
7. Cliente recibe correo con código → entra a `citybuy360.onrender.com/acceso360.html`
8. Introduce código → confeti + modal de bienvenida → productos VIP

### EmailJS configurado
- Service ID: `service_am1p2nq`
- Template ID: `template_uhydc3u`
- Public Key: guardada en localStorage del admin

---

## Panel Admin — Tabs

| Tab | Función |
|-----|---------|
| Control | Activar/desactivar secciones y productos con fecha de expiración. Estrella ⭐ acumula cambios de Destacados — guardar con botón dorado |
| Analíticas | Visitas hoy/semana/mes + gráfica (excluye visitas del admin) |
| Ventas | Tabla de clics en "Lo quiero" por producto |
| Nuevo producto | Formulario completo: fotos, nombre, precio, tallas, colores, descripción, género, sección. Publica vía GitHub API con backup automático |
| Precios | Editar precios en tiempo real desde Firebase |
| Interfaz | Toggles visuales: slider, catbar, bottomnav, ribbons (con editor de texto), marquesina, card tasas |
| Acceso 360 | Solicitudes pendientes, generador de códigos, envío de correo EmailJS, lista de clientes activos |
| Mensajes | Publicar mensajes que aparecen en la campanita 🔔 del catálogo |

---

## Pendientes activos

### Por arreglar
- [ ] Limpiar sección Destacados (fijos en HTML que no se quitan)
- [ ] 360 en PC no debe tener dorado (solo ACCESO 360 badge lo lleva)
- [ ] Tasas elToque: verificar que corsproxy.io funciona

### Por implementar
- [ ] `data-genero` en cards existentes completar + filtro funcional
- [ ] Productos en pre-venta / reserva exclusiva Acceso 360
- [ ] Card de novedades (opciones A/B/C/D acumuladas)
- [ ] Motor de precios automático + basado en ventas
- [ ] Contador de ventas visible en cards para visitantes
- [ ] CityWEB360 card de servicio
- [ ] deploy.bat

### Pendiente del dueño
- [ ] Republicar ventilador con `data-genero="electrodomesticos"`
- [ ] Desactivar código ADMIN360 en Firebase cuando termine pruebas

### Proyectos futuros
- [ ] IA genera descripción desde foto del producto
- [ ] Catálogo dinámico con productos en Firebase
- [ ] Virtual try-on con IA
- [ ] Minivideos en cards para impulsar productos
- [ ] Rutina semanal análisis visitas y ventas

---

*Última actualización: Junio 2026*
