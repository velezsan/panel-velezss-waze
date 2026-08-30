#!/usr/bin/env python3
"""Actividad de los Local Champs en el foro de México.

Recorre las categorías de México del Discourse de Waze (JSON público, sin
iniciar sesión) y cuenta, por champ y dentro de una ventana de días, cuántos
temas inició y cuántas respuestas escribió, separando la categoría de
desbloqueos del resto de las secciones.

El buscador del foro (/discuss/search) está prohibido en robots.txt, así que
no se usa: se leen los listados de categoría y los temas, que sí están
permitidos. Entre petición y petición hay una pausa para no apretar el foro.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://www.waze.com/discuss"
CAT_MEXICO = "editors/mexico/4569"      # categoría padre; incluye subcategorías
CAT_DESBLOQUEOS = 4571                   # "Unlocks, Updates and Closures"
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

HEADERS = {"User-Agent": "panel-velezss-waze (+https://velezsan.github.io/panel-velezss-waze)"}


def log(msg):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def champs():
    """La misma lista que usa el escáner, para no tenerla en dos lados."""
    sys.path.insert(0, AQUI)
    import scan
    return set(scan.CHAMPS_MX)


class Foro:
    def __init__(self, pausa=0.4):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.pausa = pausa
        self.peticiones = 0
        self.errores = 0

    def get(self, ruta, params=None):
        time.sleep(self.pausa)
        self.peticiones += 1
        try:
            r = self.s.get(BASE + ruta, params=params, timeout=30)
        except requests.RequestException as e:
            self.errores += 1
            log(f"  ! error de red en {ruta}: {e}")
            return None
        if r.status_code != 200:
            self.errores += 1
            log(f"  ! HTTP {r.status_code} en {ruta}")
            return None
        try:
            return r.json()
        except ValueError:
            self.errores += 1
            return None


def _fecha(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None


def temas_recientes(foro, corte, max_paginas=60):
    """Ids de los temas con actividad desde `corte`, recorriendo el listado."""
    ids, pagina = [], 0
    while pagina < max_paginas:
        d = foro.get(f"/c/{CAT_MEXICO}/l/latest.json", {"page": pagina})
        if not d:
            break
        temas = (d.get("topic_list") or {}).get("topics") or []
        if not temas:
            break
        en_ventana = 0
        for t in temas:
            f = _fecha(t.get("bumped_at")) or _fecha(t.get("created_at"))
            if f and f >= corte:
                en_ventana += 1
                ids.append(t["id"])
        log(f"  página {pagina}: {len(temas)} temas, {en_ventana} dentro de la ventana")
        # los fijados salen arriba con fecha vieja: solo paramos si la página
        # entera quedó fuera de la ventana
        if en_ventana == 0 and pagina > 0:
            break
        if not (d.get("topic_list") or {}).get("more_topics_url"):
            break
        pagina += 1
    return list(dict.fromkeys(ids))


def posts_del_tema(foro, tema_id):
    """Todos los posts de un tema (el JSON trae los primeros 20)."""
    d = foro.get(f"/t/{tema_id}.json")
    if not d:
        return None, []
    cat = d.get("category_id")
    flujo = d.get("post_stream") or {}
    posts = list(flujo.get("posts") or [])
    traidos = {p.get("id") for p in posts}
    faltan = [i for i in (flujo.get("stream") or []) if i not in traidos]
    for i in range(0, len(faltan), 20):
        lote = faltan[i:i + 20]
        extra = foro.get(f"/t/{tema_id}/posts.json",
                         [("post_ids[]", x) for x in lote])
        if not extra:
            break
        posts.extend((extra.get("post_stream") or {}).get("posts") or [])
    return cat, posts


def recolectar(dias=60, pausa=0.4, limite_temas=0):
    lista = champs()
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    foro = Foro(pausa)
    log(f"champs a seguir: {len(lista)} · ventana: {dias} días")

    ids = temas_recientes(foro, corte)
    if limite_temas:
        ids = ids[:limite_temas]
    log(f"temas con actividad en la ventana: {len(ids)}")

    cuentas = {}
    vacio = {"desbloqueos": {"temas": 0, "respuestas": 0},
             "otras": {"temas": 0, "respuestas": 0}}
    for n, tid in enumerate(ids, 1):
        cat, posts = posts_del_tema(foro, tid)
        if cat is None:
            continue
        seccion = "desbloqueos" if cat == CAT_DESBLOQUEOS else "otras"
        for p in posts:
            usuario = (p.get("username") or "").strip()
            if not usuario or usuario.lower() not in lista:
                continue
            f = _fecha(p.get("created_at"))
            if not f or f < corte:
                continue
            reg = cuentas.setdefault(usuario, json.loads(json.dumps(vacio)))
            clave = "temas" if p.get("post_number") == 1 else "respuestas"
            reg[seccion][clave] += 1
        if n % 25 == 0:
            log(f"  {n}/{len(ids)} temas revisados · {foro.peticiones} peticiones")

    salida = {
        "actualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana_dias": dias,
        "categoria_desbloqueos": CAT_DESBLOQUEOS,
        "temas_revisados": len(ids),
        "peticiones": foro.peticiones,
        "errores": foro.errores,
        "champs": cuentas,
    }
    return salida


SALIDA = os.path.join(RAIZ, "docs", "data", "foro.json")


def guardar(datos):
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    log("escrito docs/data/foro.json (lo leen los dos paneles)")


def revisado_hace_menos_de(horas):
    """True si el archivo de salida ya se actualizó hace poco."""
    try:
        with open(SALIDA, encoding="utf-8") as f:
            fecha = datetime.fromisoformat(json.load(f)["actualizado"])
    except Exception:
        return False
    edad = datetime.now(timezone.utc) - fecha
    if edad < timedelta(hours=horas):
        log(f"el foro se revisó hace {edad.total_seconds() / 3600:.1f} h: no toca todavía")
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=60)
    ap.add_argument("--pausa", type=float, default=0.4)
    ap.add_argument("--limite-temas", type=int, default=0,
                    help="solo para pruebas: revisa nada más los primeros N temas")
    ap.add_argument("--sin-guardar", action="store_true")
    ap.add_argument("--si-viejo", type=float, default=0,
                    help="no hacer nada si el archivo se actualizó hace menos de N horas")
    a = ap.parse_args()
    if a.si_viejo and revisado_hace_menos_de(a.si_viejo):
        return
    datos = recolectar(a.dias, a.pausa, a.limite_temas)
    resumen = sorted(datos["champs"].items(),
                     key=lambda kv: -(kv[1]["desbloqueos"]["temas"] + kv[1]["desbloqueos"]["respuestas"]
                                      + kv[1]["otras"]["temas"] + kv[1]["otras"]["respuestas"]))
    for nombre, c in resumen:
        log(f"  {nombre}: desbloqueos {c['desbloqueos']['temas']}/{c['desbloqueos']['respuestas']}"
            f" · otras {c['otras']['temas']}/{c['otras']['respuestas']}  (temas/respuestas)")
    if not a.sin_guardar:
        guardar(datos)
    log(f"listo: {datos['temas_revisados']} temas, {datos['peticiones']} peticiones, {datos['errores']} errores")


if __name__ == "__main__":
    main()
