// ==UserScript==
// @name         Panel velezss · informar nombre de calle desde el Live Map
// @namespace    https://velezsan.github.io/panel-velezss-waze/
// @version      1.1
// @description  Al abrir "Informar un error en el mapa" en el Live Map, elige "Error general en el mapa" y escribe el nombre que propuso el panel. Nunca envía: el botón Enviar lo aprietas tú.
// @author       velezss
// @match        https://velezsan.github.io/panel-velezss-waze/*
// @match        https://www.waze.com/*live-map*
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-start
// @updateURL    https://raw.githubusercontent.com/velezsan/panel-velezss-waze/main/reportar-nombre-livemap.user.js
// @downloadURL  https://raw.githubusercontent.com/velezsan/panel-velezss-waze/main/reportar-nombre-livemap.user.js
// ==/UserScript==

(function () {
  'use strict';

  // Cuánto tiempo se considera "fresco" lo último que abriste desde el panel.
  // Si pasa más, el script no llena nada, para no meter en un reporte el
  // nombre de una calle que abriste hace media hora.
  const VIGENCIA_MIN = 20;
  const TIPO_ERROR = 'Error general en el mapa';
  const PLANTILLA = calle => `El nombre de la calle es: ${calle}`;

  const log = (...a) => console.log('[panel-velezss]', ...a);

  // Señal de vida. Sin esto, cuando algo falla no hay manera de distinguir
  // "el script no está instalado" de "el script está y no funcionó".
  function senal(txt) {
    const pintar = () => {
      const d = document.createElement('div');
      d.textContent = txt;
      d.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:2147483647;' +
        'background:#123d1c;color:#fff;font:12px system-ui;padding:6px 10px;' +
        'border-radius:8px;opacity:.9;pointer-events:none';
      document.body.appendChild(d);
      setTimeout(() => d.remove(), 5000);
    };
    if (document.body) pintar();
    else document.addEventListener('DOMContentLoaded', pintar);
  }

  // ------------------------------------------------------------------
  // LADO 1: el panel. Al hacer clic en "Live Map", guarda qué calle es.
  // ------------------------------------------------------------------
  if (location.hostname === 'velezsan.github.io') {
    const anotar = e => {
      const a = e.target.closest && e.target.closest('a.lm');
      if (!a) return;
      // el nombre viaja en el hash del enlace, que es el que arma el panel
      let calle = '', seg = '';
      try {
        const h = new URLSearchParams(new URL(a.href).hash.slice(1));
        calle = h.get('calle') || '';
        seg = h.get('seg') || '';
      } catch (_) {}
      if (!calle) return;
      GM_setValue('pendiente', JSON.stringify({ calle, seg, cuando: Date.now() }));
      log('anotado para el Live Map:', calle, '· segmento', seg);
    };
    // clic normal, clic derecho (copiar enlace) y botón de en medio
    ['click', 'contextmenu', 'auxclick'].forEach(t =>
      document.addEventListener(t, anotar, true));
    senal('✓ script de reporte activo');
    return;
  }

  // ------------------------------------------------------------------
  // LADO 2: el Live Map. Espera el formulario y lo llena.
  // ------------------------------------------------------------------

  // El hash lo borra Waze en cuanto arranca su aplicación, así que hay que
  // leerlo aquí, en document-start, antes que nadie. Es el respaldo por si
  // GM_setValue no trajo nada (por ejemplo si abriste el enlace a mano).
  let delHash = null;
  try {
    const h = new URLSearchParams(location.hash.slice(1));
    if (h.get('calle')) delHash = { calle: h.get('calle'), seg: h.get('seg') || '' };
  } catch (_) {}

  function pendiente() {
    if (delHash) return delHash;
    try {
      const d = JSON.parse(GM_getValue('pendiente', '') || 'null');
      if (!d) return null;
      if (Date.now() - d.cuando > VIGENCIA_MIN * 60000) {
        log('lo último del panel ya está viejo; no lleno nada');
        return null;
      }
      return d;
    } catch (_) { return null; }
  }

  // Poner un valor en un campo de React sin que lo ignore: hay que usar el
  // setter nativo y luego avisarle con los eventos que él escucha.
  //
  // Ojo con el iframe: sus elementos pertenecen a otra ventana, así que hay
  // que tomar las clases y el constructor de eventos DE ESA ventana. Con las
  // del documento de arriba, el navegador responde "Illegal invocation".
  function ponerValor(campo, valor) {
    const w = campo.ownerDocument.defaultView || window;
    const proto = campo instanceof w.HTMLTextAreaElement ? w.HTMLTextAreaElement.prototype
      : (campo instanceof w.HTMLSelectElement ? w.HTMLSelectElement.prototype
      : w.HTMLInputElement.prototype);
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(campo, valor);
    campo.dispatchEvent(new w.Event('input', { bubbles: true }));
    campo.dispatchEvent(new w.Event('change', { bubbles: true }));
  }

  // El elemento MÁS INTERNO cuyo texto es exactamente el buscado. Importa:
  // si tomamos el primero que aparece, agarramos un contenedor de afuera que
  // también contiene ese texto, y el clic no cae en el control.
  function elementoConTexto(doc, textos, selector) {
    const quiere = t => textos.some(x => x.toLowerCase() === t);
    const hallados = [...doc.querySelectorAll(selector)]
      .filter(e => quiere((e.textContent || '').trim().toLowerCase()));
    return hallados.length ? hallados[hallados.length - 1] : null;
  }

  function elegirTipo(doc) {
    // 1) si es un <select> de verdad, por texto visible
    for (const sel of doc.querySelectorAll('select')) {
      const op = [...sel.options].find(o => o.textContent.trim() === TIPO_ERROR);
      if (op) { ponerValor(sel, op.value); return 'select'; }
    }
    // 2) si es un desplegable dibujado a mano, abrirlo y clicar la opción
    const disparador =
      elementoConTexto(doc, ['elige un tema', 'choose a topic'],
                       '[role="combobox"],[role="button"],button,div,span')
      || doc.querySelector('[role="combobox"]');
    if (!disparador) return null;
    disparador.click();
    return new Promise(res => setTimeout(() => {
      const op = elementoConTexto(doc, [TIPO_ERROR],
                                  '[role="option"],li,div,span,button');
      if (op) { op.click(); res('lista'); } else res(null);
    }, 400));
  }

  function describir(doc, texto) {
    const ta = doc.querySelector('textarea');
    if (!ta) return false;
    ponerValor(ta, texto);
    return true;
  }

  function aviso(txt, ok) {
    let c = document.getElementById('pv-aviso');
    if (!c) {
      c = document.createElement('div');
      c.id = 'pv-aviso';
      c.style.cssText = 'position:fixed;bottom:18px;left:50%;transform:translateX(-50%);' +
        'z-index:2147483647;padding:10px 16px;border-radius:10px;font:14px system-ui;' +
        'box-shadow:0 4px 14px rgba(0,0,0,.25);max-width:80vw;text-align:center';
      document.body.appendChild(c);
    }
    c.style.background = ok ? '#123d1c' : '#4a1f1f';
    c.style.color = '#fff';
    c.textContent = txt;
    clearTimeout(aviso._t);
    aviso._t = setTimeout(() => c.remove(), 9000);
  }

  // Todos los documentos donde puede estar el formulario: el de arriba y los
  // de cada iframe del mismo origen (el de Waze carga de www.waze.com, igual
  // que el Live Map). No damos por hecho que sea un iframe: si algún día lo
  // dibujan directo en la página, esto lo encuentra igual.
  function documentos() {
    const salida = [document];
    const meter = doc => {
      for (const f of doc.querySelectorAll('iframe')) {
        let d = null;
        try { d = f.contentDocument; } catch (_) {}   // otro origen: ni modo
        if (d && !salida.includes(d)) { salida.push(d); meter(d); }
      }
    };
    try { meter(document); } catch (_) {}
    return salida;
  }

  // ¿Este documento es el formulario de reporte? Pedimos las dos señas: el
  // área de texto y algún rastro del formulario, para no escribir por error
  // en cualquier otro campo de la página.
  function esElFormulario(doc) {
    if (!doc.querySelector('textarea')) return false;
    const t = (doc.body && doc.body.innerText || '').toLowerCase();
    return /informar un error|report a map|tipo de error|describe el error|elige un tema|choose a topic/.test(t);
  }

  const yaLlenados = new WeakSet();

  async function intentar(doc) {
    if (!doc || yaLlenados.has(doc)) return;
    if (!esElFormulario(doc)) return;

    const p = pendiente();
    if (!p) return;
    yaLlenados.add(doc);

    const tipo = await elegirTipo(doc);
    const texto = PLANTILLA(p.calle);
    const desc = describir(doc, texto);

    if (desc && tipo) {
      aviso('Formulario llenado: "' + texto + '". Revísalo y dale Enviar.', true);
    } else if (desc) {
      aviso('Escribí la descripción, pero no pude elegir el tipo de error. Selecciónalo tú.', false);
    } else {
      aviso('No pude llenar el formulario. El nombre es: ' + p.calle, false);
    }
    log('tipo:', tipo, '· descripción:', desc, '·', texto);
  }

  function vigilar() {
    const revisar = () => { try { documentos().forEach(intentar); } catch (e) { log('fallo al revisar:', e); } };
    new MutationObserver(revisar).observe(document.documentElement, { childList: true, subtree: true });
    // el formulario carga su contenido después de aparecer, así que también por reloj
    setInterval(revisar, 700);
    revisar();

    // Diagnóstico a mano: escribe reporteEstado() en la consola y te dice qué
    // está viendo el script. Sirve para saber por qué no llenó algo.
    unsafeWindowSeguro().reporteEstado = () => {
      const docs = documentos();
      const info = {
        version: '1.1',
        url: location.href,
        pendiente: pendiente(),
        documentosVisibles: docs.length,
        conAreaDeTexto: docs.filter(d => d.querySelector('textarea')).length,
        reconocidosComoFormulario: docs.filter(esElFormulario).length,
        iframesEnLaPagina: document.querySelectorAll('iframe').length,
      };
      console.log('[panel-velezss] estado:', info);
      return info;
    };
  }

  // Publicar la función de diagnóstico donde la consola la pueda ver, tanto
  // si el gestor nos da unsafeWindow como si no.
  function unsafeWindowSeguro() {
    try { return typeof unsafeWindow !== 'undefined' ? unsafeWindow : window; }
    catch (_) { return window; }
  }

  senal('✓ script de reporte activo');
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', vigilar);
  } else {
    vigilar();
  }
})();
