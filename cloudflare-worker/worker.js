// Worker "citybuy360-tryon" — probador virtual con IA (Gemini 2.5 Flash Image)
// Recibe: foto de la persona (base64) + URL de la imagen del producto.
// Devuelve: la imagen generada (base64) con la prenda puesta.

const ORIGEN_PERMITIDO = 'https://citybuy360.onrender.com';

export default {
  async fetch(request, env) {
    // Preflight CORS (el navegador lo manda antes del POST real)
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: cabecerasCors() });
    }

    const url = new URL(request.url);
    if (url.pathname === '/shein-info') {
      return manejarSheinInfo(request);
    }

    if (request.method !== 'POST') {
      return jsonError('Método no permitido', 405);
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return jsonError('JSON inválido', 400);
    }

    const { fotoBase64, fotoMime, prendaUrl } = body;
    if (!fotoBase64 || !prendaUrl) {
      return jsonError('Faltan datos: fotoBase64 y prendaUrl son obligatorios', 400);
    }

    // Descargar la imagen del producto (ya está en tu repo de GitHub) y pasarla a base64
    let prendaBase64, prendaMime;
    try {
      const resPrenda = await fetch(prendaUrl);
      if (!resPrenda.ok) throw new Error('No se pudo descargar la imagen del producto');
      prendaMime = resPrenda.headers.get('content-type') || 'image/jpeg';
      const buffer = await resPrenda.arrayBuffer();
      prendaBase64 = arrayBufferABase64(buffer);
    } catch (e) {
      return jsonError('Error descargando la imagen del producto: ' + e.message, 500);
    }

    // Llamar a Gemini con las dos imágenes
    const prompt = 'Toma la primera imagen (una persona) y la segunda imagen (una prenda de ropa). ' +
      'Genera una imagen fotorrealista de la misma persona usando esa prenda puesta, ' +
      'manteniendo su rostro, cuerpo, pose y fondo lo más natural posible. No agregues texto ni marcas de agua.';

    let resultado;
    try {
      const respuestaGemini = await fetch(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent',
        {
          method: 'POST',
          headers: {
            'x-goog-api-key': env.GEMINI_API_KEY,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contents: [{
              parts: [
                { text: prompt },
                { inline_data: { mime_type: fotoMime || 'image/jpeg', data: fotoBase64 } },
                { inline_data: { mime_type: prendaMime, data: prendaBase64 } },
              ],
            }],
          }),
        }
      );

      if (!respuestaGemini.ok) {
        const detalle = await respuestaGemini.text();
        return jsonError('Gemini rechazó la solicitud: ' + detalle, 502);
      }

      const data = await respuestaGemini.json();
      const partes = data?.candidates?.[0]?.content?.parts || [];
      const partesImagen = partes.find(p => p.inlineData || p.inline_data);
      const inline = partesImagen?.inlineData || partesImagen?.inline_data;

      if (!inline) {
        return jsonError('Gemini no devolvió ninguna imagen. Puede que el contenido haya sido bloqueado.', 502);
      }

      resultado = { imagenBase64: inline.data, mimeType: inline.mimeType || inline.mime_type || 'image/png' };
    } catch (e) {
      return jsonError('Error llamando a Gemini: ' + e.message, 500);
    }

    return new Response(JSON.stringify(resultado), {
      headers: { 'Content-Type': 'application/json', ...cabecerasCors() },
    });
  },
};

function cabecerasCors() {
  return {
    'Access-Control-Allow-Origin': ORIGEN_PERMITIDO,
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Lee un link de Shein (típicamente el link corto onelink.shein.com que se comparte
// desde la app) y extrae el nombre y la imagen del producto vía meta tags Open Graph.
// Nota: la página completa de producto en shein.com está protegida por un captcha
// anti-bot, así que ahí no siempre se puede leer; el precio siempre se ingresa a mano.
async function manejarSheinInfo(request) {
  const url = new URL(request.url);
  const link = url.searchParams.get('url');
  if (!link) return jsonError('Falta el parámetro url', 400);

  let html;
  try {
    const resp = await fetch(link, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'es-ES,es;q=0.9',
      },
      redirect: 'follow',
    });
    html = await resp.text();
  } catch (e) {
    return jsonError('Error leyendo el link: ' + e.message, 500);
  }

  const nombre = extraerMeta(html, 'og:title') || extraerTitulo(html);
  const imagen = extraerMeta(html, 'og:image');

  if (!nombre && !imagen) {
    return jsonError('No se pudo leer ese link (puede que Shein esté bloqueando la lectura automática). Copia nombre e imagen a mano.', 502);
  }

  return new Response(JSON.stringify({ nombre: limpiarHtml(nombre || ''), imagen: imagen || '' }), {
    headers: { 'Content-Type': 'application/json', ...cabecerasCors() },
  });
}

function extraerMeta(html, prop) {
  var re = new RegExp('<meta[^>]+(?:property|name)=["\']' + prop + '["\'][^>]+content=["\']([^"\']*)["\']', 'i');
  var m = html.match(re);
  if (m) return m[1];
  var re2 = new RegExp('<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']' + prop + '["\']', 'i');
  var m2 = html.match(re2);
  return m2 ? m2[1] : null;
}

function extraerTitulo(html) {
  var m = html.match(/<title[^>]*>([^<]*)<\/title>/i);
  return m ? m[1] : null;
}

function limpiarHtml(str) {
  return str.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
}

function jsonError(mensaje, status) {
  return new Response(JSON.stringify({ error: mensaje }), {
    status,
    headers: { 'Content-Type': 'application/json', ...cabecerasCors() },
  });
}

function arrayBufferABase64(buffer) {
  let binario = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) binario += String.fromCharCode(bytes[i]);
  return btoa(binario);
}
