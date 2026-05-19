# CITYBUY360 — Catálogo Digital

**URL:** https://citybuy360.onrender.com  
**Admin:** https://citybuy360.onrender.com/admin.html  
**Repo:** https://github.com/asuranasuran666/citybuy360

---

## Stack

| Tecnología | Uso |
|-----------|-----|
| HTML / CSS / JS | Frontend completo en un solo archivo |
| Firebase Realtime DB | Ratings, visitas, ventas, config admin |
| GitHub API | Publicar productos desde el admin |
| Render | Hosting con deploy automático desde GitHub |
| Chart.js | Gráficas en el admin |

---

## Archivos clave

| Archivo | Qué es |
|--------|--------|
| `index.html` | Catálogo completo |
| `admin.html` | Panel de administración |
| `backups/` | Copias automáticas del index antes de cada cambio |
| `*.jpg / *.jpeg` | Fotos de productos en la raíz |

---

## Flujo de trabajo

### Cambios manuales (código)
```bash
git add .
git pull origin main --rebase   # SIEMPRE antes de push
git commit -m "descripcion"
git push
```

### Cambios desde el admin
El admin hace commit directo a GitHub vía API. Después de usar el admin, hacer siempre `git pull origin main --rebase` antes del próximo push manual.

---

## Firebase — estructura de datos

```
ratings/{producto}          → votos y promedio de estrellas
analytics/visits/YYYY-MM-DD → visitas diarias
sales/{producto}            → clics en "Lo quiero"
config/sections/{id}        → activo/inactivo + fecha expiración
config/products/{id}        → activo/inactivo
```

---

## Secciones del catálogo

| ID | Nombre | Productos |
|----|--------|-----------|
| `destacado` | ⭐ Lo más destacado | blumer, gorra, freedom, bolsomovil |
| `ropa-interior` | 👙 Ropa Interior | blumer, sujetador |
| `ropa-moda` | 👕 Ropa y Moda | paris, ngu, gdm, aac, usa, freedom, mblancas, mnegras |
| `accesorios` | 👜 Accesorios | bolsomovil, gorrobebe, gorra |
| `servicios` | ⚡ Servicios | saldo, citybuy360familia |

---

## Pendientes

### Cambios menores acumulados
- [ ] Fecha de expiración por producto en admin (no solo por sección)
- [ ] Verificar tooltip PC más grande en live
- [ ] Verificar margen slider/sección en live

### Funcionalidades por implementar
- [ ] Barra de categorías scrollable con tags `data-genero` en cards
- [ ] Barra de navegación fija abajo tipo Temu
- [ ] Banner informativo 2 columnas tipo Temu
- [ ] CityWEB360 — card de servicio
- [ ] deploy.bat — automatizar git push

### Proyectos futuros
- [ ] Catálogo dinámico con productos en Firebase
- [ ] Virtual try-on con IA
- [ ] Rutina semanal de análisis de visitas y ventas

---

## Decisiones tomadas

- **Todo en un solo index.html** — simplicidad de despliegue, sin build process
- **Mobile-first en grid** — 2 columnas por defecto, 4 en PC (evita fallos de breakpoints)
- **GitHub API para productos nuevos** — sin backend propio, fotos en el repo
- **Firebase para datos** — tiempo real, gratis en tier básico
- **WhatsApp como canal de venta** — sin pasarela de pago
- **Sin Firebase dinámico por ahora** — productos en HTML estático para mantener simplicidad

---

*Última actualización: Mayo 2026*
