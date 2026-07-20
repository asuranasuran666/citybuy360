// ===== ACCESO 360 — núcleo compartido =====
// Usado por index.html, admin.html y acceso360.html.
// Si se cambia el secreto o el algoritmo, se cambia UNA sola vez aquí.
// Genera y verifica códigos con firma matemática (base36 + checksum),
// funciona sin conexión a internet.

var ACCESO360_SECRETO = 'CB360-VIP-CLAVE-2026';

function acceso360Sello(expiraDiaEpoch) {
  var str = expiraDiaEpoch + ACCESO360_SECRETO;
  var hash = 0;
  for (var i = 0; i < str.length; i++) { hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0; }
  var b36 = Math.abs(hash).toString(36).toUpperCase();
  while (b36.length < 5) b36 = '0' + b36;
  return b36.slice(0, 5);
}

function acceso360Generar(dias) {
  var expiraDiaEpoch = Math.floor(Date.now() / 86400000) + dias;
  var expiraB36 = expiraDiaEpoch.toString(36).toUpperCase();
  return { code: 'CB360-' + expiraB36 + '-' + acceso360Sello(expiraDiaEpoch), expiraDiaEpoch: expiraDiaEpoch };
}

// Devuelve { valido: bool, expirado?: bool, formatoReconocido: bool }
function acceso360Verificar(codeRaw) {
  var code = (codeRaw || '').trim().toUpperCase();
  var m = /^CB360-([0-9A-Z]+)-([0-9A-Z]{5})$/.exec(code);
  if (!m) return { valido: false, formatoReconocido: false };
  var expiraB36 = m[1], sello = m[2];
  var expiraDiaEpoch = parseInt(expiraB36, 36);
  if (isNaN(expiraDiaEpoch)) return { valido: false, formatoReconocido: false };
  if (acceso360Sello(expiraDiaEpoch) !== sello) return { valido: false, formatoReconocido: true };
  if (Math.floor(Date.now() / 86400000) > expiraDiaEpoch) return { valido: false, formatoReconocido: true, expirado: true };
  return { valido: true, formatoReconocido: true };
}
