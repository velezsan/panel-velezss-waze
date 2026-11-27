// Cosecha de URs para el panel (ver INSTRUCCIONES-URS.md).
// Son tres bloques que se pegan, en orden, con la herramienta de JavaScript del
// navegador. SOLO LEEN: nunca responden, cierran ni marcan como leído un UR.
// Probado el 20-nov-2026: ROW 288 peticiones y 22,091 URs en 4.5 min; NA 160
// peticiones y 272 URs en 1 min. Una petición a la vez, con pausa.

// ===== BLOQUE 1 (pestaña del WME, ya en tab=issue_tracker): capturar el filtro
window.CAP = [];
if (!window.__svsHook) {
  window.__svsHook = true;
  const of = window.fetch;
  window.fetch = function (input, init) {
    try {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      if (/searchMapUpdateRequests/.test(url)) {
        const b = init && init.body;
        window.CAP.push({ url, body: typeof b === 'string' ? b : null });
      }
    } catch (e) {}
    return of.apply(this, arguments);
  };
}
// se elige el filtro guardado sin tocar ningún renglón de la lista
const el = [...document.querySelectorAll('[class*="filterName"]')]
  .find(e => e.textContent.trim() === 'TodoMX (Con Cerrados)');
for (const t of [el, el.parentElement]) {
  for (const ev of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
    t.dispatchEvent(new MouseEvent(ev, { bubbles: true, cancelable: true, view: window }));
  }
}
await new Promise(r => setTimeout(r, 6000));
// de los cuerpos capturados sirve el más corto (80 caracteres): el que no trae bbox
window.BASEB = window.CAP.filter(c => c.body).sort((a, b) => a.body.length - b.body.length)[0].body;

// ===== BLOQUE 2 (misma pestaña): protobuf a mano, barrido y botón hacia GitHub
window.PB = {
  b64d: s => Uint8Array.from(atob(s), c => c.charCodeAt(0)),
  b64e: u => { let s = ''; for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); return btoa(s); },
  dec(u) {
    const out = []; let i = 0;
    const vi = () => { let r = 0n, s = 0n; for (;;) { const b = u[i++]; r |= BigInt(b & 127) << s; if (!(b & 128)) break; s += 7n; } return r; };
    while (i < u.length) {
      const tag = Number(vi()); const f = tag >>> 3, w = tag & 7; let v;
      if (w === 0) v = vi();
      else if (w === 1) { v = u.slice(i, i + 8); i += 8; }
      else if (w === 2) { const n = Number(vi()); v = u.slice(i, i + n); i += n; }
      else if (w === 5) { v = u.slice(i, i + 4); i += 4; }
      else throw new Error('wire ' + w + ' @' + i);
      out.push([f, w, v]);
    }
    return out;
  },
  vint(n) { n = BigInt.asUintN(64, BigInt(n)); const o = []; do { let b = Number(n & 127n); n >>= 7n; if (n) b |= 128; o.push(b); } while (n); return o; },
  enc(list) {
    const o = [];
    for (const [f, w, v] of list) {
      o.push(...this.vint((f << 3) | w));
      if (w === 0) o.push(...this.vint(v));
      else if (w === 2) { o.push(...this.vint(v.length)); for (const b of v) o.push(b); }
      else { for (const b of v) o.push(b); }
    }
    return Uint8Array.from(o);
  },
  frame(u) { const o = new Uint8Array(5 + u.length); o[0] = 0; new DataView(o.buffer).setUint32(1, u.length); o.set(u, 5); return o; },
  unframe(u) { const fr = []; let i = 0; while (i + 5 <= u.length) { const fl = u[i]; const n = new DataView(u.buffer, u.byteOffset + i + 1, 4).getUint32(0); fr.push([fl, u.slice(i + 5, i + 5 + n)]); i += 5 + n; } return fr; },
  get(list, f) { const x = list.find(e => e[0] === f); return x ? x[2] : undefined; },
  dbl(u) { return new DataView(u.buffer, u.byteOffset, 8).getFloat64(0, true); },
  str(u) { return new TextDecoder().decode(u); }
};
const base = PB.dec(PB.unframe(PB.b64d(window.BASEB))[0][1]);
const f1 = PB.dec(PB.get(base, 1)); const FILTRO = PB.get(f1, 2); const ORDEN = PB.get(base, 5);
const i1base = PB.dec(PB.get(f1, 1)).filter(e => e[0] !== 1 && e[0] !== 4);  // deja país (5=145), 6 y 7
const pt = (lon, lat) => PB.enc([[101, 0, BigInt(Math.round(lon * 1e6))], [102, 0, BigInt(Math.round(lat * 1e6))]]);
window.URQ = {
  body(bb) {
    const bbox = PB.enc([[1, 2, pt(bb[0], bb[1])], [2, 2, pt(bb[2], bb[3])]]);
    const i1 = PB.enc([[1, 2, bbox], ...i1base]);
    const m = PB.enc([[1, 2, PB.enc([[1, 2, i1], [2, 2, FILTRO]])], [2, 0, 500n], [5, 2, ORDEN]]);
    return PB.b64e(PB.frame(m));
  },
  async pedir(env, bb) {
    const url = (env === 'usa' ? '/Descartes' : '/row-Descartes') + '/grpc/com.waze.mapeditor.web.api.MapEditorWebServer/searchMapUpdateRequests';
    const r = await fetch(url, { method: 'POST', credentials: 'include', headers: { 'content-type': 'application/grpc-web-text', 'x-grpc-web': '1', 'x-user-agent': 'grpc-web-javascript/0.1' }, body: this.body(bb) });
    if (!r.ok) throw new Error('http ' + r.status);
    let u = new Uint8Array(await r.arrayBuffer());
    if (u.length && u[0] !== 0 && u[0] !== 0x80) {  // por si un día llega en base64
      const parts = PB.str(u).replace(/\s+/g, '').match(/[A-Za-z0-9+\/]+={0,2}/g) || [];
      const bufs = parts.map(p => PB.b64d(p)); const tot = bufs.reduce((a, b) => a + b.length, 0);
      u = new Uint8Array(tot); let o = 0; for (const b of bufs) { u.set(b, o); o += b.length; }
    }
    const recs = [];
    for (const [fl, p] of PB.unframe(u)) { if (fl & 0x80) continue; for (const [f, w, v] of PB.dec(p)) { if (f === 1 && w === 2) recs.push(v); } }
    return { recs };
  },
  rec(v) {
    const l = PB.dec(v); const g = f => PB.get(l, f);
    const sub = (u, f) => { if (!u) return undefined; try { return PB.get(PB.dec(u), f); } catch (e) { return undefined; } };
    const p = sub(g(2), 2); let lon = null, lat = null;
    if (p) { const pl = PB.dec(p); const a = PB.get(pl, 1), b = PB.get(pl, 2); if (a && a.length === 8) lon = PB.dbl(a); if (b && b.length === 8) lat = PB.dbl(b); }
    const s = u => u ? PB.str(u) : ''; const sec = u => { const x = sub(u, 1); return x === undefined ? 0 : Number(x); };
    const loc = g(20);
    // st: 1 abierto, 2 cerrado · d: descripción con prefijo "SUBTIPO: " · rep: quien reportó · ed: último editor
    return { id: Number(g(1)), lon, lat, t: Number(g(4) ?? 0n), st: Number(g(6) ?? 0n), d: s(g(7)), rep: s(sub(g(8), 2)), ed: s(sub(g(9), 2)), c: sec(g(10)), a: sec(g(11)), edo: s(sub(sub(loc, 6), 2)), ciu: s(sub(sub(loc, 7), 2)) };
  }
};
window.H = { row: { m: new Map(), req: 0, err: [], fin: false, topes: 0 }, usa: { m: new Map(), req: 0, err: [], fin: false, topes: 0 }, t0: Date.now(), fase: 'row' };
const dormir = ms => new Promise(r => setTimeout(r, ms));
(async () => {  // corre de fondo; el avance se consulta en window.H (fase 'listo' al terminar)
  for (const env of ['row', 'usa']) {
    const S = window.H[env]; window.H.fase = env; const cola = [];
    for (let lon = -118; lon < -86; lon += 2) for (let lat = 14; lat < 33; lat += 2) cola.push([[lon, lat, lon + 2, Math.min(lat + 2, 33)], 0]);
    while (cola.length) {
      const [bb, prof] = cola.shift(); let r = null;
      for (let intento = 0; intento < 3 && !r; intento++) {
        try { r = await URQ.pedir(env, bb); } catch (e) { await dormir(2500 * (intento + 1)); if (intento === 2) S.err.push(bb.join(',') + ' ' + String(e).slice(0, 40)); }
      }
      S.req++;
      if (r) {
        if (r.recs.length >= 500 && prof < 9) {  // el servidor topa en 500: la celda se parte en cuatro
          const [a, b, c, d] = bb; const mx = (a + c) / 2, my = (b + d) / 2;
          cola.unshift([[a, b, mx, my], prof + 1], [[mx, b, c, my], prof + 1], [[a, my, mx, d], prof + 1], [[mx, my, c, d], prof + 1]);
        } else {
          if (r.recs.length >= 500) S.topes++;
          for (const v of r.recs) { try { const x = URQ.rec(v); S.m.set(x.id, x); } catch (e) { S.err.push('rec ' + String(e).slice(0, 30)); } }
        }
      }
      S.cola = cola.length; await dormir(350);
    }
    S.fin = true;
  }
  window.H.fase = 'listo'; window.H.t1 = Date.now();
})();
// Para pasar los datos a GitHub: window.name NO sobrevive al ir de waze.com a
// github.com, así que se abre la otra pestaña con un clic real sobre este botón
// (captura de pantalla + clic) y se manda todo con postMessage.
const boton = document.createElement('button'); boton.id = 'svs-abrir'; boton.textContent = 'ABRIR GITHUB (Claude)';
boton.style.cssText = 'position:fixed;left:40%;top:40%;z-index:2147483647;font-size:22px;padding:22px 30px;background:#ffb454;color:#000;border:3px solid #000;border-radius:10px;cursor:pointer';
boton.onclick = () => { window.GH = window.open('https://github.com/velezsan/panel-velezss-waze/upload/main/docs', 'svsgh'); };
document.body.appendChild(boton);
// En la pestaña de GitHub se pone antes el receptor:
//   window.RX={parts:{},n:0,total:null};
//   window.addEventListener('message',e=>{if(e.origin!=='https://www.waze.com'||!e.data||e.data.svs!==1)return;
//     window.RX.parts[e.data.i]=e.data.txt;window.RX.n=Object.keys(window.RX.parts).length;window.RX.total=e.data.total;});
// Y cuando window.H.fase==='listo', desde el WME:
//   const pk={t:Math.floor(Date.now()/1000)};
//   for(const env of ['row','usa'])pk[env]=[...H[env].m.values()].map(x=>[x.id,x.lon,x.lat,x.t,x.st,x.d,x.rep,x.ed,x.c,x.a,x.edo,x.ciu]);
//   const txt=JSON.stringify(pk),T=400000,total=Math.ceil(txt.length/T);
//   for(let i=0;i<total;i++)window.GH.postMessage({svs:1,i,total,txt:txt.slice(i*T,(i+1)*T)},'https://github.com');

// ===== BLOQUE 3 (pestaña de GitHub): armar los dos archivos de cada panel
// recs = pk.row o pk.usa ya unido; panel = 'row' o 'na'; ahora = pk.t
window.BUILD = async (recs, panel, ahora) => {
  const esNA = panel === 'na'; const dir = esNA ? 'docs/na/' : 'docs/';
  const CH = new Set((esNA ? ['editorbcmx', 'carloslaso', 'arturoae'] : ['carloslaso', 'editorbcmx', 'arturoae', 'GWM_', 'drysoft', 'EumirGarciaC2', 'Hector_HF', 'maalrivba', 'arielorellana', 'ManuFC212', 'camachista', 'DavidAbarca']).map(s => s.toLowerCase()));
  const raw = async p => { const r = await fetch('/velezsan/panel-velezss-waze/raw/main/' + p, { cache: 'no-store' }); if (!r.ok) throw new Error('no pude leer ' + p); return r.json(); };
  const old = await raw(dir + 'urs-datos.json'); const oldS = await raw(dir + 'urs-cerrados-champs.json');
  const R = recs.map(a => ({ id: a[0], lon: a[1], lat: a[2], t: a[3], st: a[4], d: a[5], rep: a[6], ed: a[7], c: a[8], a: a[9], edo: a[10], ciu: a[11] }));
  const idx = (arr, mapa) => s => { s = s || ''; if (!mapa.has(s)) { mapa.set(s, arr.length); arr.push(s); } return mapa.get(s); };
  const editores = [''], reporteros = [], estados = [], ciudades = [];
  const iE = idx(editores, new Map([['', 0]])), iR = idx(reporteros, new Map()), iS = idx(estados, new Map()), iC = idx(ciudades, new Map());
  const r6 = x => Math.round(x * 1e6) / 1e6; const limpia = d => (d || '').replace(/^[A-Z][A-Z0-9_]{2,}:\s*/, '').trim();
  const fila = x => [x.id, r6(x.lon), r6(x.lat), x.t, x.c, x.a, iE(x.ed), iR(x.rep), iS(x.edo), iC(x.ciu), limpia(x.d)];
  const ab = R.filter(x => x.st === 1).sort((a, b) => b.c - a.c || b.id - a.id); const ce = R.filter(x => x.st === 2);
  const urs = ab.map(fila);
  // reportes de champs: los de hoy más los ya publicados que hoy no vienen (quedan como cerrados)
  const champs = R.filter(x => x.rep && CH.has(x.rep.toLowerCase())).map(x => [...fila(x), x.st === 1 ? 1 : 0]);
  const hoyCh = new Set(champs.map(f => f[0])); let recuperados = 0;
  for (const f of (old.champs || [])) {
    if (hoyCh.has(f[0])) continue;
    const g = f.slice(0, 12); g[6] = iE(old.editores[f[6]]); g[7] = iR(old.reporteros[f[7]]); g[8] = iS(old.estados[f[8]]); g[9] = iC(old.ciudades[f[9]]); g[11] = 0;
    champs.push(g); recuperados++;
  }
  champs.sort((a, b) => b[4] - a[4] || b[0] - a[0]);
  // URs cerrados cuyo último editor es un champ
  const canon = {}; for (const k of Object.keys(oldS.cerradosChamps || {})) canon[k.toLowerCase()] = k;
  const hoyCe = {};
  for (const x of ce) { if (!x.ed || !CH.has(x.ed.toLowerCase())) continue; const k = canon[x.ed.toLowerCase()] || (canon[x.ed.toLowerCase()] = x.ed); (hoyCe[k] = hoyCe[k] || []).push(x.id); }
  const union = {};
  for (const k of new Set([...Object.keys(oldS.cerradosChamps || {}), ...Object.keys(hoyCe)])) union[k] = [...new Set([...(oldS.cerradosChamps[k] || []), ...(hoyCe[k] || [])])].sort((a, b) => a - b);
  const ventana = {}; for (const k of Object.keys(hoyCe)) ventana[k] = hoyCe[k].length;   // lo que Waze deja ver hoy (40 días)
  // lo mismo por estado, con el nombre corto que usa el panel (para champs-estado.html)
  const ALIAS = { 'veracruz de ignacio de la llave': 'Veracruz', 'coahuila de zaragoza': 'Coahuila', 'michoacán de ocampo': 'Michoacán', 'michoacan de ocampo': 'Michoacán', 'querétaro de arteaga': 'Querétaro', 'queretaro de arteaga': 'Querétaro', 'estado de méxico': 'México', 'estado de mexico': 'México', 'distrito federal': 'Ciudad de México', 'mexico city': 'Ciudad de México' };
  const MX = new Set(['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'México', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas']);
  const porEdo = {}; let sinEdo = 0;
  for (const x of ce) {
    if (!x.ed || !CH.has(x.ed.toLowerCase())) continue;
    const e0 = (x.edo || '').trim(); const e = ALIAS[e0.toLowerCase()] || e0;
    if (!MX.has(e)) { sinEdo++; continue; }   // sin estado o del lado de EUA
    const k = canon[x.ed.toLowerCase()]; const d = porEdo[e] = porEdo[e] || {}; d[k] = (d[k] || 0) + 1;
  }
  const acum = {}; for (const k of Object.keys(union)) acum[k] = union[k].length;         // histórico, corrida tras corrida
  const tipos = Object.assign({}, old.tipos); for (const x of R) if (!tipos[String(x.t)]) tipos[String(x.t)] = 'Tipo ' + x.t;
  const tCe = ce.map(x => x.a || x.c); const ven = ce.length ? [Math.min(...tCe), Math.max(...tCe)] : [0, 0];
  const datos = {
    generado: ahora,   // SIEMPRE en segundos (con texto ISO la página pinta mal la fecha)
    fuente: 'WME ' + (esNA ? 'NA' : 'ROW') + ' · filtro TodoMX (Con Cerrados)', n: urs.length, totalLeidos: R.length, cerradosLeidos: ce.length,
    champsAcumulados: true, ventanaCerrados: ven, cols: old.cols, colsChamps: old.colsChamps, tipos, editores, reporteros, estados, ciudades, champs, urs,
    cerradosPorChamp: ventana, cerradosPorChampEstado: porEdo, cerradosVentanaDias: 40, cerradosAcumulados: acum, cerradosDesde: ven[0], champsTotal: champs.length
  };
  const side = { generado: ahora, fuente: 'WME ' + (esNA ? 'NA' : 'ROW'), desde: oldS.desde, nota: oldS.nota, cerradosChamps: union, cerradosPorChamp: acum };
  return { datos, side, resumen: { panel, leidos: R.length, abiertos: urs.length, antes: old.n, cerrados: ce.length, sinContestar: urs.filter(u => !editores[u[6]]).length, mas28dias: urs.filter(u => (ahora - u[4]) / 86400 >= 28).length, champs: champs.length, recuperados, ventana, acum, estadosConCerrados: Object.keys(porEdo).length, cerradosSinEstado: sinEdo } };
};
// Se suben docs/urs-datos.json + docs/urs-cerrados-champs.json (un commit) y los
// mismos dos nombres en docs/na (otro commit). Antes de enviar el primero se guardan
// los cuatro textos en sessionStorage, porque al enviar el formulario la página se va.
