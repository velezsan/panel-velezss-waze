// ==UserScript==
// @name         Panel velezss · informar nombre de calle desde el Live Map
// @namespace    https://velezsan.github.io/panel-velezss-waze/
// @version      1.3
// @description  Al abrir "Informar un error en el mapa" en el Live Map, elige "Error general del mapa" y escribe el nombre que propuso el panel. Nunca envía: el botón Enviar lo aprietas tú.
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
  // El formulario real de Waze usa "Error general DEL mapa" (no "en el"), y
  // por dentro el valor es GENERAL_PROBLEM. Buscamos por el valor primero,
  // que no depende del idioma ni de cómo esté redactada la etiqueta.
  const TIPO_VALOR = 'GENERAL_PROBLEM';
  const TIPO_ERROR = 'Error general del mapa';
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

  // Escribir de verdad en un campo. Poner .value a mano no siempre basta:
  // según la librería que use el formulario, el componente vuelve a pintar
  // con su propio estado y borra lo escrito. execCommand('insertText') pasa
  // por el camino del navegador y genera los mismos eventos que el teclado,
  // que es lo que aceptan React, Angular y Vue por igual. Si falla, se usa
  // el setter nativo. Y al final SE COMPRUEBA que el valor quedó.
  function escribir(campo, valor) {
    const doc = campo.ownerDocument;
    try {
      campo.focus();
      if (campo.setSelectionRange) campo.setSelectionRange(0, (campo.value || '').length);
      else if (campo.select) campo.select();
      doc.execCommand('insertText', false, valor);
      if (campo.value === valor) return true;
    } catch (_) {}
    try { ponerValor(campo, valor); } catch (_) {}
    return campo.value === valor;
  }

  const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const TEXTOS_VACIO = ['elige un tema', 'choose a topic', 'elige un asunto'];

  // El elemento MÁS INTERNO cuyo texto es exactamente el buscado. Importa:
  // si tomamos el primero que aparece, agarramos un contenedor de afuera que
  // también contiene ese texto, y el clic no cae en el control.
  function elementoConTexto(doc, textos, selector) {
    const quiere = t => textos.some(x => norm(x) === t);
    const hallados = [...doc.querySelectorAll(selector)]
      .filter(e => quiere(norm(e.textContent)));
    return hallados.length ? hallados[hallados.length - 1] : null;
  }

  // La opción puede pintarse fuera del formulario (en un portal del documento
  // de arriba), así que se busca en todos los documentos, no solo en el suyo.
  function opcionEnCualquierDocumento(textos) {
    for (const d of documentos()) {
      const op = elementoConTexto(d, textos,
        '[role="option"],li,div,span,button,td,p');
      if (op && op.offsetParent !== null) return op;
      if (op) return op;
    }
    return null;
  }

  function opcionQueContenga(trozo) {
    for (const d of documentos()) {
      const c = buscarEn(d, '[role="option"],li,div,span,button,td,p')
        .filter(e => norm(e.textContent).includes(trozo) && e.children.length === 0);
      if (c.length) return c[c.length - 1];
    }
    return null;
  }

  async function elegirTipo(doc) {
    // Camino de Waze: <wz-select placeholder="Elige un tema"> con hijos
    // <wz-option value="GENERAL_PROBLEM">. El texto del placeholder está en el
    // ATRIBUTO, no en el contenido, que es donde lo buscábamos antes.
    const selects = buscarEn(doc, 'wz-select, [placeholder]').filter(e =>
      e.tagName.toLowerCase() === 'wz-select' ||
      TEXTOS_VACIO.includes(norm(e.getAttribute('placeholder'))));
    for (const sel of selects) {
      const ops = buscarEn(doc, 'wz-option').filter(o => sel.contains(o));
      const op = ops.find(o => norm(o.value) === norm(TIPO_VALOR))
        || ops.find(o => norm(o.textContent) === norm(TIPO_ERROR))
        || ops.find(o => /error general/.test(norm(o.textContent)));
      if (!op) continue;
      // abrir el menú (por si hace falta para que el componente reaccione)
      try {
        const menu = sel.shadowRoot && sel.shadowRoot.querySelector('wz-menu');
        if (menu && menu.showMenu) await menu.showMenu();
        const caja = sel.shadowRoot && sel.shadowRoot.querySelector('.select-box');
        if (caja) golpeDeRaton(caja);
      } catch (_) {}
      await new Promise(r => setTimeout(r, 350));
      golpeDeRaton(op);              // esto es lo que fija el valor
      await new Promise(r => setTimeout(r, 350));
      if (!norm(sel.value)) { try { sel.value = op.value; } catch (_) {} }
      await new Promise(r => setTimeout(r, 250));
      if (norm(sel.value) === norm(op.value)) return 'wz-select';
    }

    // Camino normal, por si algún día lo cambian a un <select> de siempre
    for (const sel of buscarEn(doc, 'select')) {
      const op = [...sel.options].find(o => norm(o.textContent) === norm(TIPO_ERROR))
        || [...sel.options].find(o => /error general/.test(norm(o.textContent)));
      if (op) { ponerValor(sel, op.value); return 'select'; }
    }

    // Último recurso: un desplegable cualquiera dibujado a mano. No es lo que
    // usa Waze hoy, pero si lo cambian, esto lo sigue sacando adelante.
    let disparador = elementoConTexto(doc, TEXTOS_VACIO,
      '[role="combobox"],[role="button"],button,div,span,label,p');
    if (!disparador) {
      disparador = buscarEn(doc, 'input').find(i =>
        TEXTOS_VACIO.includes(norm(i.value)) || TEXTOS_VACIO.includes(norm(i.placeholder)));
    }
    if (!disparador) disparador = buscarEn(doc, '[role="combobox"],[aria-haspopup]')[0];
    if (!disparador) return null;
    for (const paso of ['click', 'raton', 'teclado']) {
      if (paso === 'click') disparador.click();
      if (paso === 'raton') golpeDeRaton(disparador);
      if (paso === 'teclado') {
        disparador.focus();
        const w = disparador.ownerDocument.defaultView || window;
        for (const tipo of ['keydown', 'keyup']) {
          disparador.dispatchEvent(new w.KeyboardEvent(tipo,
            { key: 'ArrowDown', code: 'ArrowDown', bubbles: true }));
        }
      }
      await new Promise(r => setTimeout(r, 450));
      // por etiqueta exacta y, si no, por "error general", que aguanta que
      // Waze reescriba la frase ("del mapa" / "en el mapa" / etc.)
      const op = opcionEnCualquierDocumento([TIPO_ERROR])
        || opcionQueContenga('error general');
      if (op) { op.click(); golpeDeRaton(op); await new Promise(r => setTimeout(r, 300)); return paso; }
    }
    return null;
  }

  function golpeDeRaton(el) {
    const w = el.ownerDocument.defaultView || window;
    const r = el.getBoundingClientRect();
    const opciones = { bubbles: true, cancelable: true, view: w,
      clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 };
    for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      try {
        const Ev = t.startsWith('pointer') && w.PointerEvent ? w.PointerEvent : w.MouseEvent;
        el.dispatchEvent(new Ev(t, opciones));
      } catch (_) {}
    }
  }

  // El área de texto de la descripción. Ojo: en el documento hay varias
  // ocultas, de alto cero, que no son el campo que ves; la buena vive dentro
  // del shadow de <wz-textarea>. Nos quedamos siempre con una que se vea.
  function areaDescripcion(doc) {
    const tas = buscarEn(doc, 'textarea');
    return tas.find(seVe) || null;
  }

  function describir(doc, texto) {
    const ta = areaDescripcion(doc);
    if (!ta) return false;
    return escribir(ta, texto);
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

  // TODO lo de Waze está hecho con componentes propios (wz-select, wz-textarea,
  // wz-option) que esconden sus campos dentro de Shadow DOM. querySelectorAll
  // normal no ve ahí adentro: por eso el script escribía en un textarea oculto
  // del documento y no encontraba nunca el desplegable.
  function raicesDe(doc) {
    const out = [doc];
    const rec = raiz => {
      let hijos = [];
      try { hijos = [...raiz.querySelectorAll('*')]; } catch (_) { return; }
      for (const e of hijos) if (e.shadowRoot) { out.push(e.shadowRoot); rec(e.shadowRoot); }
    };
    try { rec(doc); } catch (_) {}
    return out;
  }

  function buscarEn(doc, selector) {
    const out = [];
    for (const r of raicesDe(doc)) {
      try { out.push(...r.querySelectorAll(selector)); } catch (_) {}
    }
    return out;
  }

  const seVe = e => { try { return e.getBoundingClientRect().height > 0; } catch (_) { return false; } };

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

    const texto = PLANTILLA(p.calle);

    // Primero la descripción, que es lo que de verdad importa. Abrir el
    // desplegable puede repintar el formulario y borrarla, así que después
    // de elegir el tipo se vuelve a comprobar y, si hizo falta, se reescribe.
    describir(doc, texto);
    const tipo = await elegirTipo(doc);
    await new Promise(r => setTimeout(r, 300));

    let ta = areaDescripcion(doc);
    if (!ta || ta.value !== texto) describir(doc, texto);
    await new Promise(r => setTimeout(r, 300));

    // Nada de suponer: se mira el estado real de los campos.
    ta = areaDescripcion(doc);
    const descOk = !!ta && ta.value === texto;
    const tipoOk = tipoElegido(doc);

    if (descOk && tipoOk) {
      aviso('Listo: "' + texto + '". Revísalo y dale Enviar.', true);
    } else if (descOk) {
      aviso('Escribí la descripción. Falta que elijas el tipo de error.', false);
    } else if (tipoOk) {
      aviso('Elegí el tipo, pero no pude escribir. Copia: ' + texto, false);
    } else {
      aviso('No pude llenar el formulario. Copia esto: ' + texto, false);
    }
    log('tipo:', tipo, '· tipo puesto:', tipoOk, '· descripción puesta:', descOk,
        '· valor real:', ta && ta.value);
  }

  // ¿Quedó realmente elegido un tipo de error? Vale tanto si es un <select>
  // como si es un control propio: en ese caso ya no debe decir "Elige un tema".
  function tipoElegido(doc) {
    for (const sel of buscarEn(doc, 'wz-select')) {
      if (norm(sel.value)) return true;
    }
    for (const sel of buscarEn(doc, 'select')) {
      const t = norm(sel.selectedOptions[0] && sel.selectedOptions[0].textContent);
      if (t && !TEXTOS_VACIO.includes(t)) return true;
    }
    return false;
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
        version: '1.3',
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

    // Radiografía del formulario: qué controles hay y cómo están hechos.
    // Si algo no se llena, con esto se ve por qué sin tener que adivinar.
    unsafeWindowSeguro().reporteCampos = () => {
      const doc = documentos().find(esElFormulario);
      if (!doc) { console.log('[panel-velezss] no veo el formulario abierto'); return null; }
      const ficha = e => ({
        etiqueta: e.tagName.toLowerCase(),
        rol: e.getAttribute('role') || null,
        tipo: e.getAttribute('type') || null,
        soloLectura: e.readOnly || null,
        valor: (e.value || '').slice(0, 60) || null,
        marcador: (e.placeholder || '').slice(0, 60) || null,
        texto: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) || null,
        clase: (e.className || '').toString().slice(0, 60) || null,
      });
      const info = {
        selects: [...doc.querySelectorAll('select')].map(s => ({
          opciones: [...s.options].map(o => o.textContent.trim()).slice(0, 12) })),
        entradas: [...doc.querySelectorAll('input')].map(ficha).slice(0, 10),
        areasDeTexto: [...doc.querySelectorAll('textarea')].map(ficha),
        combos: [...doc.querySelectorAll('[role="combobox"],[aria-haspopup],[role="listbox"]')].map(ficha).slice(0, 6),
        conElTextoElige: [...doc.querySelectorAll('*')]
          .filter(e => TEXTOS_VACIO.includes(norm(e.textContent)) && e.children.length <= 2)
          .map(ficha).slice(0, 6),
      };
      console.log('[panel-velezss] campos:', JSON.stringify(info, null, 1));
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
