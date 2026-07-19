// ===== VENDEDORES — login offline (matemático) =====
// Usado por admin.html (generar códigos) y vendedores.html (verificarlos sin red).
// Mismo patrón que acceso360-core.js pero con secreto propio, para no mezclar sistemas.

var VENDEDOR_SECRETO = 'CB360-VENDOR-KEY-2026';

function vendedorSello(idNum) {
  var str = idNum + VENDEDOR_SECRETO;
  var hash = 0;
  for (var i = 0; i < str.length; i++) { hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0; }
  var b36 = Math.abs(hash).toString(36).toUpperCase();
  while (b36.length < 5) b36 = '0' + b36;
  return b36.slice(0, 5);
}

function vendedorGenerar(idNum) {
  var idB36 = idNum.toString(36).toUpperCase();
  return 'VEND-' + idB36 + '-' + vendedorSello(idNum);
}

// Devuelve { valido: bool, formatoReconocido: bool, id?: number }
function vendedorVerificar(codeRaw) {
  var code = (codeRaw || '').trim().toUpperCase();
  var m = /^VEND-([0-9A-Z]+)-([0-9A-Z]{5})$/.exec(code);
  if (!m) return { valido: false, formatoReconocido: false };
  var idB36 = m[1], sello = m[2];
  var idNum = parseInt(idB36, 36);
  if (isNaN(idNum)) return { valido: false, formatoReconocido: false };
  if (vendedorSello(idNum) !== sello) return { valido: false, formatoReconocido: true };
  return { valido: true, formatoReconocido: true, id: idNum };
}
