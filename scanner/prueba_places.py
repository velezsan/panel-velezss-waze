#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprueba que el port de fixGrammar da lo mismo que el JavaScript.

Los pares de abajo se sacaron corriendo el userscript de Santiago tal cual en
el navegador, sobre nombres reales de places de Waze (Querétaro, Monterrey,
CDMX, Guadalajara, Mérida y Tijuana) más casos de borde hechos a mano para
tocar cada rama de la función. Si el port se desvía, esta prueba lo dice.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from places import fix_grammar, necesita_correccion, siglas_aplastadas

# (nombre, lo que devuelve el JavaScript)
PARES = [
    # --- marcas que se dejan tal cual
    ("OXXO", "OXXO"), ("Oxxo", "Oxxo"), ("oxxo", "Oxxo"),
    ("Toks", "Toks"), ("Tok's", "Tok's"), ("toks", "Toks"),
    # --- PAN protegido, BBVA Bancomer, AT&T
    ("PAN", "PAN"), ("El PAN de cada dia", "El PAN de Cada Dia"),
    ("BBVA Bancomer Centro", "BBVA Centro"), ("bbva bancomer", "BBVA"),
    ("AT&T", "AT&T"), ("at&t Plaza", "AT&T Plaza"),
    # --- siglas con puntos
    ("S.A. de C.V.", "S.A. de C.V."),
    ("C.F.E.", "C.F.E."), ("cfe", "CFE"),
    ("D.H.L", "DHL"),
    ("I.N.A.H. Centro regional de Jalisco", "INAH Centro Regional de Jalisco"),
    # --- siglas del diccionario
    ("IMSS UMF 33", "IMSS UMF 33"), ("imss umf 33", "IMSS UMF 33"),
    # --- las que fue marcando Santiago al revisar el panel
    ("ABL Consultores", "ABL Consultores"), ("CEDIS Bimbo", "CEDIS Bimbo"),
    ("CMD Monterrey", "CMD Monterrey"), ("HNI Torreon", "HNI Torreon"),
    ("INNOTEC", "Innotec"),   # lo descartó en la segunda revisión
    ("MIT Academy", "MIT Academy"),
    ("DSPM Zapopan", "DSPM Zapopan"), ("HGSZMF No. 4", "HGSZMF No. 4"),
    ("FirstCash", "FirstCash"),
    ("UAS Facultad de Derecho", "UAS Facultad de Derecho"),
    ("ES", "ES"),
    # --- apóstrofos y marcas del diccionario
    ("McDonald's", "McDonald's"), ("mcdonalds", "McDonald's"),
    ("l'occitane", "L'Occitane"),
    ("El Palacio de Hierro", "El Palacio de Hierro"),
    ("7-eleven", "7-Eleven"),
    ("ihop", "iHop"),
    # --- acentos
    ("Café de la Parroquia", "Café de la Parroquia"),
    ("cafe de la parroquia", "Café de la Parroquia"),
    ("Jardin de los Ninos", "Jardín de los Ninos"),
    ("Taqueria El Paisa", "Taquería El Paisa"),
    ("Modulo de Atencion", "Módulo de Atención"),
    ("Estacion 21 de Marzo", "Estación 21 de Marzo"),
    ("Correos de Mexico Queretaro Centro", "Correos de México Querétaro Centro"),
    ("La barriada queretaro", "La Barriada Querétaro"),
    ("Ay Maria Panaderia", "Ay María Panadería"),
    ("Super Shoes", "Súper Shoes"),
    ("Nuñez y Asociados", "Núñez y Asociados"),
    # --- artículos y preposiciones
    ("Los Arcos", "Los Arcos"), ("los arcos", "Los Arcos"),
    ("Casa de los Abuelos", "Casa de los Abuelos"),
    ("Casa Los Abuelos", "Casa Los Abuelos"),
    ("Tienda y Abarrotes", "Tienda y Abarrotes"),
    ("Tienda & Abarrotes", "Tienda & Abarrotes"),
    ("El rincon de los sentidos", "El Rincon de los Sentidos"),
    ("Hotel La Casa de los dos Leones", "Hotel La Casa de los Dos Leones"),
    ("Iglesia de nuestra señora de la Merced", "Iglesia de Nuestra Señora de la Merced"),
    ("Librería cristiana Del Rey", "Librería Cristiana del Rey"),
    ("Secretaria de educación Querétaro", "Secretaria de Educación Querétaro"),
    ("Museo casa de la Zacatecana AC", "Museo Casa de la Zacatecana AC"),
    ("Centro de seguridad social IMSS", "Centro de Seguridad Social IMSS"),
    # --- separadores raros
    ("Hotel-Restaurante", "Hotel-Restaurante"),
    ("Hotel - Restaurante", "Hotel - Restaurante"),
    ("(el buen sabor)", "(El Buen Sabor)"),
    ("Uno/Dos", "Uno/Dos"),
    ("Uno / Dos", "Uno / Dos"),
    ('"el mesón"', '"El Mesón"'),
    ("Super Farmacia", "Súper Farmacia"),
    ("Clinica 12 de Diciembre", "Clínica 12 de Diciembre"),
    ("Escuela Primaria Benito Juarez", "Escuela Primaria Benito Juarez"),
    ("Extintores y equipos de seguridad", "Extintores y Equipos de Seguridad"),
    ("Ale Boutique, Ropa fina para mujer", "Ale Boutique, Ropa Fina para Mujer"),
    ("Rey del dulce", "Rey del Dulce"),
    ("La casa del atrio", "La Casa del Atrio"),
    ("Pastes kikos Pino Suárez", "Pastes Kikos Pino Suárez"),
    ("a", "A"), ("de", "De"), ("y", "Y"), ("EL", "El"),
    # --- siglas que el script aplasta (lo que Santiago irá curando)
    ("GDL Centro", "Gdl Centro"), ("Farmacia GDL", "Farmacia Gdl"),
    ("Universidad CNCI - Querétaro Zaragoza", "Universidad Cnci - Querétaro Zaragoza"),
    ("SAT - ADSC Querétaro", "SAT - Adsc Querétaro"),
    ("ESCI", "Esci"), ("SUSPE", "Suspe"),
    ("Laboratorios LABSA", "Laboratorios Labsa"),
    ("Tayrona BTQ", "Tayrona Btq"),
    ("UADY Facultad de Medicina", "Uady Facultad de Medicina"),
    ("GTS (GLOBAL THERMAL SOLUTIONS)", "Gts (Global Thermal Solutions)"),
    ("Citibanamex - 16 de Septiembre", "Banamex - 16 de Septiembre"),
    # --- errores de verdad
    ("LIBRERÍA DE MONJAS", "Librería de Monjas"),
    ("FARMACIA FRANCESA", "Farmacia Francesa"),
    ("THE LIT 13", "The Lit 13"),
    ("pasteleria el molino", "Pasteleria El Molino"),
    ("noun studio", "Noun Studio"),
    ("plasttel", "Plasttel"),
    ("MASTER inovacion electronica", "Master Inovacion Electronica"),
    ("Panificadora CENTENO", "Panificadora Centeno"),
    ("Instituto de belleza IMAGEN", "Instituto de Belleza Imagen"),
    ("VIPS", "Vips"), ("Vips", "Vips"), ("vips", "Vips"),
    ("Cocina económica haley", "Cocina Económica Haley"),
    ("La piramide", "La Piramide"),
    ("Paleteria michoacana", "Paleteria Michoacana"),
    # --- sin cambios
    ("Punto de lectura", "Punto de Lectura"),
    ("Riel store", "Riel Store"),
    ("MG Motors", "MG Motors"),
]


# Casos donde el port se aparta del JavaScript A PROPÓSITO, porque Santiago
# pidió arreglar lo que se pudiera. La columna del medio es lo que daba su
# script; la de la derecha es lo que damos ahora.
MEJORAS = [
    # iniciales con punto: ya no se vuelven la preposición "a"
    ("PJENL - Sala Jorge A. Treviño", "Pjenl - Sala Jorge a Treviño", "Pjenl - Sala Jorge A. Treviño"),
    ("Jorge A. Treviño", "Jorge a Treviño", "Jorge A. Treviño"),
    ("Hospital A. López Mateos", "Hospital a López Mateos", "Hospital A. López Mateos"),
    # frases del diccionario, que antes nunca se aplicaban
    ("circulo k", "Circulo K", "Círculo K"),
    ("nuevo leon", "Nuevo Leon", "Nuevo León"),
    ("Fiscalia de nuevo leon", "Fiscalia de Nuevo Leon", "Fiscalia de Nuevo León"),
    ("san luis potosi", "San Luis Potosi", "San Luis Potosí"),
    ("tuxtla gutierrez", "Tuxtla Gutierrez", "Tuxtla Gutiérrez"),
    ("palacio de hierro", "Palacio de Hierro", "El Palacio de Hierro"),
    ("home depot", "Home Depot", "The Home Depot"),
    ("hotel hi", "Hotel Hi", "Hotel hi"),
    ("puerto vallarta", "Puerto Vallarta", "Puerto Vallarta"),
    ("farmacia del ahorro", "Farmacia del Ahorro", "Farmacia del Ahorro"),
    # entradas cuyo valor trae palabras de más que la llave: ya no se duplican
    # (en su script la llave de dos palabras no disparaba, así que lo dejaba
    #  intacto; la duplicación la introdujo la pasada de frases y aquí se evita)
    ("El Palacio de Hierro", "El Palacio de Hierro", "El Palacio de Hierro"),
    ("Palacio de Hierro", "Palacio de Hierro", "El Palacio de Hierro"),
    ("Sams Club", "Sam's Club Club", "Sam's Club"),
    ("Bodega Aurrera", "Bodega Bodega Aurrerá", "Bodega Aurrerá"),
    ("Tiendas Extra", "Tiendas Tiendas Extra", "Tiendas Extra"),
    ("The Home Depot", "The Home Depot", "The Home Depot"),
    # estas tres sí las duplicaba su script (llaves de una palabra)
    # códigos con letras y números: antes se aplastaban
    ("Pemex - ES08877", "Pemex - Es08877", "Pemex - ES08877"),
    ("Tiendas 3B", "Tiendas 3b", "Tiendas 3B"),
    ("C5 Sinaloa", "C5 Sinaloa", "C5 Sinaloa"),
    ("TACOS EL 5TO", "Tacos El 5to", "Tacos El 5TO"),
    # el kilómetro se queda como lo escribieron, en mayúsculas o en minúsculas
    ("Caseta Las Brisas KM 110+100", "Caseta Las Brisas Km 110+100",
     "Caseta Las Brisas KM 110+100"),
    ("Km 22 Carretera Libre", "Km 22 Carretera Libre", "Km 22 Carretera Libre"),
    # lo que va entre corchetes es una etiqueta, no una palabra
    ("Pemex [E] 08877", "Pemex [e] 08877", "Pemex [E] 08877"),
    # CargoGas: primero lo puso como dos palabras y luego lo aprobó tal cual
    # en el panel, así que se queda con su mayúscula interna
    ("CargoGas", "Cargogas", "CargoGas"),
    ("CARGOGAS Norte", "Cargogas Norte", "CargoGas Norte"),
    ("BANREGIO Centro", "Banregio Centro", "BanRegio Centro"),
    ("Ecovia Linea 1", "Ecovia Linea 1", "EcoVía Linea 1"),
    ("SuKarne Monterrey", "Sukarne Monterrey", "SuKarne Monterrey"),
    ("ChargeNow", "Chargenow", "ChargeNow"),
    ("DeAcero Planta", "Deacero Planta", "DeAcero Planta"),
    ("VIP Salón", "Vip Salón", "VIP Salón"),
    ("FIRSTCASH", "Firstcash", "FirstCash"),
    # siglas que Santiago fue aprobando: ya no se aplastan
    ("Industrias ABC S.A. de C.V.", "Industrias Abc S.A. de C.V.",
     "Industrias ABC S.A. de C.V."),
    ("Súper y Carnes ABC", "Súper y Carnes Abc", "Súper y Carnes ABC"),
    ("CAM No. 5 Héroes Coahuilenses", "Cam No. 5 Héroes Coahuilenses",
     "CAM No. 5 Héroes Coahuilenses"),
    ("CTM Querétaro", "Ctm Querétaro", "CTM Querétaro"),
    ("UAC - Facultad de Ciencias", "Uac - Facultad de Ciencias",
     "UAC - Facultad de Ciencias"),
    # marcas con mayúscula interna: se conserva la forma exacta
    ("BanBajio - Plaza Zaragoza", "Banbajio - Plaza Zaragoza",
     "BanBajio - Plaza Zaragoza"),
    ("CIBanco Torreón", "Cibanco Torreón", "CIBanco Torreón"),
    ("AlSuper Centro", "Alsuper Centro", "AlSuper Centro"),
    ("Sta.Ma. de Guadalupe", "Sta.ma. de Guadalupe", "Sta.Ma. de Guadalupe"),
    # los signos de apertura también abren palabra
    ("¡QUE TACOS!", "¡que Tacos!", "¡Que Tacos!"),
    ("¿Donde estan los tacos?", "¿donde Estan Los Tacos?", "¿Donde Estan Los Tacos?"),
    # palabras indiferentes: las siglas que también son palabras normales se
    # quedan como vengan, ni se corrigen ni se marcan
    ("GAMA Muebles", "Gama Muebles", "GAMA Muebles"),
    ("Farmacia MAS", "Farmacia Mas", "Farmacia MAS"),
    ("Ropa USA", "Ropa Usa", "Ropa USA"),
    ("SPA Relax", "Spa Relax", "SPA Relax"),
    # y si el nombre viene todo en minúsculas, sí le toca su mayúscula inicial
    ("gama muebles", "Gama Muebles", "Gama Muebles"),
]

# Lo ya bien escrito no debe cambiar al volver a pasarlo (idempotencia).
IDEMPOTENTES = [
    "El Palacio de Hierro", "Sam's Club", "Bodega Aurrerá", "Tiendas Extra",
    "The Home Depot", "Círculo K", "Nuevo León", "Farmacia Guadalajara",
    "Jorge A. Treviño", "S.A. de C.V.", "IMSS UMF 33", "OXXO", "AT&T",
    "Café de la Parroquia", "Farmacia del Ahorro", "McDonald's", "L'Occitane",
    "Pemex - ES08877", "Tiendas 3B", "C5 Sinaloa", "UAS Facultad de Derecho",
    "Caseta Las Brisas KM 110+100", "Km 22 Carretera Libre",
    "CargoGas", "FirstCash", "Pemex [E] 08877", "CEDIS Bimbo", "BanRegio Torreón",
    "TodoGas", "EcoVía Línea 1", "UDEM Campus", "Grupo NL", "MTY Centro",
    "SuKarne Monterrey", "ChargeNow", "DeAcero Planta", "VIP Salón", "FullOk",
    "BanBajio - Plaza Zaragoza", "CIBanco Torreón", "AlSuper Centro",
    "UAC - Facultad de Ciencias", "Templo SUD", "CETIS No. 48", "Autobuses AAA",
    "GAMA Muebles", "Gama Muebles", "Spa Relax", "Ropa USA", "La Idea",
]


def main():
    fallos = []
    for nombre, esperado in PARES:
        obtenido = fix_grammar(nombre)
        if obtenido != esperado:
            fallos.append((nombre, esperado, obtenido))

    print(f"comparados contra el JavaScript: {len(PARES)} nombres")
    if fallos:
        print(f"\nDIFERENCIAS: {len(fallos)}\n")
        for nombre, esperado, obtenido in fallos:
            print(f"  entrada : {nombre!r}")
            print(f"  JS dice : {esperado!r}")
            print(f"  Python  : {obtenido!r}\n")
    else:
        print("sin diferencias: el port da exactamente lo mismo")

    # los arreglos pedidos: aquí SÍ debe diferir del JavaScript
    print("\narreglos pedidos (se apartan del JavaScript a propósito):")
    malas_mejoras = 0
    for nombre, antes_js, esperado in MEJORAS:
        obtenido = fix_grammar(nombre)
        ok = obtenido == esperado
        if not ok:
            malas_mejoras += 1
        marca = "ok " if ok else "MAL"
        cambio = "" if antes_js == esperado else f"   (tu script daba {antes_js!r})"
        print(f"  {marca} {nombre!r} -> {obtenido!r}{cambio}")

    # idempotencia: pasar dos veces no debe cambiar nada
    print("\nidempotencia (lo ya correcto no se toca):")
    malas_idem = 0
    for nombre in IDEMPOTENTES:
        obtenido = fix_grammar(nombre)
        ok = obtenido == nombre
        if not ok:
            malas_idem += 1
            print(f"  MAL {nombre!r} -> {obtenido!r}")
    if not malas_idem:
        print(f"  ok  los {len(IDEMPOTENTES)} se quedaron igual")

    # la marca de siglas aplastadas, que es lo que el panel resalta
    casos = [
        ("Farmacia GDL", ["GDL"]),
        ("UADY Facultad de Medicina", ["UADY"]),
        ("Tiendas 3B", []),        # ya no se aplasta: se protege el código
        ("BanBajio - Plaza Zaragoza", []),   # ya se respeta la marca
        ("SAT - ADSC Querétaro", ["ADSC"]),           # SAT sí está en la lista
        ("VIPS", ["VIPS"]),
        # las palabras largas en mayúsculas son un nombre a gritos, no siglas:
        # esas no se marcan, porque la corrección sí es la buena
        ("LIBRERÍA DE MONJAS", []),
        ("FARMACIA FRANCESA", []),
        ("Panificadora CENTENO", []),
        ("Café de la Parroquia", []),
        ("IMSS UMF 33", []),
        ("McDonald's", []),
        ("Medievo XXI", []),
        ("Pemex - ES08877", []),
        ("GAMA Muebles", []),        # indiferente: ni se corrige ni se marca
    ]
    print("\nmarca de siglas aplastadas:")
    malos = 0
    for nombre, esperado in casos:
        obtenido = siglas_aplastadas(nombre, fix_grammar(nombre))
        ok = obtenido == esperado
        if not ok:
            malos += 1
        print(f"  {'ok ' if ok else 'MAL'} {nombre!r} -> {obtenido}")

    print()
    if fallos or malos or malas_mejoras or malas_idem:
        print("HAY PROBLEMAS")
        sys.exit(1)
    print("TODO BIEN")


if __name__ == "__main__":
    main()
