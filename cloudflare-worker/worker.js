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
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
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
