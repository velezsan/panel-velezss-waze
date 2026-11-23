// Barra de arriba del panel: marca y cambio entre los dos servidores.
(function () {
  function poner() {
    if (document.querySelector('.barra-top')) return;
    var ruta = location.pathname;
    var esNA = /\/na\//.test(ruta);
    var pagina = ruta.split('/').pop() || 'index.html';
    var soloRow = { 'pases.html': 1 };
    var otra = (esNA || !soloRow[pagina]) ? pagina : 'index.html';
    var nav = document.createElement('nav');
    nav.className = 'barra-top';
    nav.setAttribute('aria-label', 'Panel');
    var marca = document.createElement('a');
    marca.className = 'marca';
    marca.href = 'index.html';
    marca.title = 'Ir a la portada';
    marca.innerHTML = '<span class="logo">v</span><span>velezss</span><small>panel del mapa</small>';
    var caja = document.createElement('div');
    caja.className = 'servidores';
    var row = document.createElement('a');
    row.textContent = 'ROW · México';
    row.href = esNA ? '../' + otra : pagina;
    var na = document.createElement('a');
    na.textContent = 'NA · Frontera';
    na.href = esNA ? pagina : 'na/' + otra;
    (esNA ? na : row).className = 'act';
    (esNA ? na : row).setAttribute('aria-current', 'page');
    caja.appendChild(row);
    caja.appendChild(na);
    nav.appendChild(marca);
    nav.appendChild(caja);
    document.body.insertBefore(nav, document.body.firstChild);
  }
  if (document.body) poner(); else document.addEventListener('DOMContentLoaded', poner);
})();
