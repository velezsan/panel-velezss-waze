#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reglas para revisar los places (venues) de Waze en México.

Son las dos reglas que Santiago ya usa en su userscript "WME MX Toolkit":

  1) Nombres mal escritos: se corre su misma funcion fixGrammar.
  2) Places sin direccion: no tienen calle, o la calle no tiene nombre.

La ortografia es un PORT LITERAL del JavaScript de su script, incluidos sus
diccionarios y sus rarezas. Se hizo asi a proposito: la lista del panel tiene
que proponer exactamente lo mismo que propondria su script al pasar por el
place, si no serian dos criterios distintos para el mismo trabajo. Hay una
prueba (prueba_places.py) que compara contra las salidas reales del navegador.
"""

import re

# ---------------------------------------------------------------------------
# Diccionarios, copiados tal cual del userscript
# ---------------------------------------------------------------------------
ACCENT_FIXES = {
    "mexico": "México", "aguascalientes": "Aguascalientes", "baja california": "Baja California",
    "campeche": "Campeche", "chiapas": "Chiapas", "chihuahua": "Chihuahua", "coahuila": "Coahuila",
    "colima": "Colima", "durango": "Durango", "guanajuato": "Guanajuato", "guerrero": "Guerrero",
    "hidalgo": "Hidalgo", "jalisco": "Jalisco", "michoacan": "Michoacán", "morelos": "Morelos",
    "nayarit": "Nayarit", "nuevo leon": "Nuevo León", "oaxaca": "Oaxaca", "puebla": "Puebla",
    "queretaro": "Querétaro", "quintana roo": "Quintana Roo", "san luis potosi": "San Luis Potosí",
    "sinaloa": "Sinaloa", "sonora": "Sonora", "tabasco": "Tabasco", "tamaulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala", "veracruz": "Veracruz", "yucatan": "Yucatán", "zacatecas": "Zacatecas",
    "cdmx": "CDMX", "merida": "Mérida", "cancun": "Cancún", "leon": "León",
    "guadalajara": "Guadalajara", "monterrey": "Monterrey", "tijuana": "Tijuana", "toluca": "Toluca",
    "zapopan": "Zapopan", "naucalpan": "Naucalpan", "ecatepec": "Ecatepec",
    "nezahualcoyotl": "Nezahualcóyotl", "tlalnepantla": "Tlalnepantla", "coyoacan": "Coyoacán",
    "tlalpan": "Tlalpan", "iztapalapa": "Iztapalapa", "azcapotzalco": "Azcapotzalco",
    "xochimilco": "Xochimilco", "cuernavaca": "Cuernavaca", "hermosillo": "Hermosillo",
    "saltillo": "Saltillo", "mexicali": "Mexicali", "culiacan": "Culiacán", "mazatlan": "Mazatlán",
    "acapulco": "Acapulco", "puerto vallarta": "Puerto Vallarta", "cordoba": "Córdoba",
    "orizaba": "Orizaba", "jalapa": "Xalapa", "villahermosa": "Villahermosa",
    "tuxtla gutierrez": "Tuxtla Gutiérrez", "tepic": "Tepic", "pachuca": "Pachuca",
    "obregon": "Obregón", "clinica": "Clínica", "modulo": "Módulo", "policia": "Policía",
    "estacion": "Estación", "terminal": "Terminal", "publica": "Pública", "jardin": "Jardín",
    "cafe": "Café", "numero": "Número", "salon": "Salón", "almacen": "Almacén",
    "direccion": "Dirección", "atencion": "Atención", "educacion": "Educación",
    "asociacion": "Asociación", "paraiso": "Paraíso", "republica": "República",
    "tecnologico": "Tecnológico", "universidad": "Universidad", "escuela": "Escuela",
    "colegio": "Colegio", "instituto": "Instituto", "facultad": "Facultad", "kinder": "Kínder",
    "hospital": "Hospital", "farmacia": "Farmacia", "consultorio": "Consultorio",
    "laboratorio": "Laboratorio", "restaurante": "Restaurante", "taqueria": "Taquería",
    "panaderia": "Panadería", "tortilleria": "Tortillería", "taller": "Taller",
    "mecanico": "Mecánico", "refaccionaria": "Refaccionaria", "gasolinera": "Gasolinera",
    "tienda": "Tienda", "abarrotes": "Abarrotes", "super": "Súper", "mercado": "Mercado",
    "plaza": "Plaza", "centro": "Centro", "fraccionamiento": "Fraccionamiento",
    "residencial": "Residencial", "colonia": "Colonia", "barrio": "Barrio", "unidad": "Unidad",
    "deportiva": "Deportiva", "habitacional": "Habitacional", "condominio": "Condominio",
    "edificio": "Edificio", "torre": "Torre", "oficina": "Oficina", "despacho": "Despacho",
    "carpinteria": "Carpintería", "cenaduria": "Cenaduría",
    "jose": "José", "maria": "María", "jesus": "Jesús", "angel": "Ángel", "monica": "Mónica",
    "oscar": "Óscar", "martin": "Martín", "victor": "Víctor", "raul": "Raúl", "andres": "Andrés",
    "hector": "Héctor", "cesar": "César", "garcia": "García", "martinez": "Martínez",
    "gonzalez": "González", "rodriguez": "Rodríguez", "lopez": "López", "perez": "Pérez",
    "sanchez": "Sánchez", "fernandez": "Fernández", "ramirez": "Ramírez", "torres": "Torres",
    "flores": "Flores", "rivera": "Rivera", "gomez": "Gómez", "diaz": "Díaz", "cruz": "Cruz",
    "reyes": "Reyes", "morales": "Morales", "ortiz": "Ortiz", "gutierrez": "Gutiérrez",
    "chavez": "Chávez", "ramos": "Ramos", "alvarez": "Álvarez", "castillo": "Castillo",
    "jimenez": "Jiménez", "vazquez": "Vázquez", "nuñez": "Núñez",
    "kfc": "KFC", "burger king": "Burger King", "mcdonalds": "McDonald's",
    "mcdonald's": "McDonald's", "subway": "Subway", "starbucks": "Starbucks",
    "dominos": "Domino's Pizza", "pizza hut": "Pizza Hut", "little caesars": "Little Caesars",
    "sanborns": "Sanborns", "chilis": "Chili's", "italiannis": "Italianni's",
    "7-eleven": "7-Eleven", "seven eleven": "7-Eleven", "extra": "Tiendas Extra",
    "circulo k": "Círculo K", "chedraui": "Chedraui", "soriana": "Soriana", "aurrera": "Bodega Aurrerá", "superama": "Superama", "costco": "Costco", "sams": "Sam's Club",
    "city club": "City Club", "liverpool": "Liverpool",
    "palacio de hierro": "El Palacio de Hierro", "sears": "Sears", "coppel": "Coppel",
    "elektra": "Elektra", "woolworth": "Woolworth",
    "home depot": "The Home Depot", "office depot": "Office Depot", "officemax": "OfficeMax",
    "autozone": "AutoZone", "farmacia guadalajara": "Farmacia Guadalajara",
    "farmacia del ahorro": "Farmacia del Ahorro", "farmacias similares": "Farmacias Similares",
    "bbva": "BBVA", "bancomer": "BBVA", "citibanamex": "Banamex", "banamex": "Banamex",
    "santander": "Santander", "hsbc": "HSBC", "scotiabank": "Scotiabank", "banorte": "Banorte",
    "inbursa": "Inbursa", "banco azteca": "Banco Azteca", "telcel": "Telcel",
    "movistar": "Movistar", "at&t": "AT&T", "megacable": "Megacable", "izzi": "Izzi",
    "totalplay": "Totalplay", "sky": "SKY", "dish": "Dish", "infinitum": "Infinitum",
    "bp": "BP", "shell": "Shell", "mobil": "Mobil", "g500": "G500",
    "repsol": "Repsol", "imss": "IMSS", "issste": "ISSSTE", "cfe": "CFE", "cac": "CAC",
    "fedex": "FedEx", "l'occitane": "L'Occitane", "hotel hi": "Hotel hi",
    "firstcash": "FirstCash", "cargogas": "CargoGas", "banregio": "BanRegio",
    "todogas": "TodoGas", "ecovia": "EcoVía",
}

ALLOWED = {
    "IMSS", "UMF", "HGZ", "HGR", "UMAE", "ISSSTE", "INSABI", "SS", "COFEPRIS", "DIF", "NSS",
    "CURP", "CRIT", "INAPAM", "CONADIC", "SAT", "SHCP", "RFC", "ISR", "IVA", "IEPS", "ISAN",
    "UMA", "SMV", "CLABE", "CNBV", "CONDUSEF", "CONSAR", "AFORE", "SIEFORE", "BMV", "BIVA",
    "PIB", "INPC", "FOBAPROA", "IPAB", "FONACOT", "INFONAVIT", "FOVISSSTE", "PROFECO",
    "SEGOB", "SRE", "SEDENA", "SEMAR", "SSPC", "SEP", "SEMARNAT", "SENER", "SE", "SADER",
    "SICT", "STPS", "SEDATU", "SECTUR", "SFP", "CJF", "SCJN", "TEPJF", "FGR", "PGR", "GN",
    "MP", "PDI", "SSC", "C5", "SSP", "DOF", "INE", "CNDH", "INEGI", "CONEVAL", "INAI",
    "COFECE", "IFT", "CFE", "CONAGUA", "CONAFOR", "CONANP", "CAPUFE", "ASA", "AICM", "AIFA",
    "C.F.E.", "UNAM", "IPN", "UAM", "ITESM", "TEC", "ITAM", "CONAHCYT", "INBAL", "INAH",
    "COMIPEMS", "CENEVAL", "UANL", "UAQ", "INEA", "CBTIS", "MORENA", "PRI", "PRD", "PVEM",
    "PT", "MC", "CDMX", "SLP", "ZIM", "ZMVM", "KFC", "CAC", "XXI", "HSBC", "BBVA", "BMW",
    "VW", "DHL", "UPS", "SCT", "HEB", "GMC", "CPA", "S.A.", "C.V.", "S.C.", "A.C.", "S.A.B.",
    "S.A.P.I.", "S.R.L.", "I.A.P.", "II", "III", "IV", "VI", "VII", "VIII", "IX", "KTM",
    "AM", "PM", "SA", "CV", "SC", "AC", "SAPI", "LLC", "INC", "SOS", "IAP", "MG", "RTP", "AT&T",
    # las va agregando Santiago conforme salen en el panel
    "ES", "UAS", "ABL", "CEDIS", "CMD", "HNI", "MIT", "DSPM", "HGSZMF",
    "ABC", "CAM", "FMA", "CEA",
    # Sexta tanda: propuesta automática sobre las 1,771 que quedaban, para no
    # revisarlas una por una. Aquí las que son claramente siglas: sin vocales,
    # de tres letras o menos, o instituciones y empresas conocidas.
    "+GF+", "A.C", "A.G.", "A.R.", "AAM", "AB", "ABA", "ABB", "ABS", "ABX", "AC.", "ACE",
    "ACM", "ACN", "ACQ", "ACV", "ADESA", "ADF", "ADS", "AEM", "AER", "AF", "AFL", "AFS",
    "AGE", "AGM", "AHLĀ", "AI", "AIG", "AK", "ALD", "ALMEX", "ALP", "ALV", "AMD", "AME",
    "AMI", "AMP", "AN", "ANDA", "AOA", "AOC", "APA", "APF", "APM", "ARO", "ASC", "ASG",
    "ASK", "ASM", "ASO", "ASTRO", "ATC", "ATD", "ATI", "ATN", "ATS", "AVE", "AVM", "AXTEL",
    "BAM", "BASA", "BAT", "BB", "BC", "BCPK", "BCR", "BDI", "BES", "BG", "BGD", "BH", "BHP",
    "BIC", "BIM", "BJ", "BKL", "BKS", "BM", "BMC", "BME", "BMG", "BN", "BOG", "BRISA", "BSH",
    "BSM", "BT", "BTS", "BW", "BWW", "BX", "BYP", "BYU", "C.C.T.19DST0083F", "C.P.", "C.S.U",
    "C.S.U.", "CA", "CAD", "CAMSA", "CAP", "CAR", "CARD", "CAS", "CAV", "CBA", "CBS", "CCCH",
    "CCM", "CCN", "CCS", "CCU", "CDC", "CDG", "CDH", "CDI", "CDM", "CDO", "CDR", "CEC",
    "CEDES", "CEI", "CEM", "CER", "CETEC", "CEV", "CG", "CH", "CHN", "CI", "CIAP", "CIC",
    "CID", "CIDEB", "CIDEP", "CIE", "CIETT", "CIMA", "CIP", "CIS", "CL", "CLC", "CME", "CMF",
    "CMS", "CMX", "CNCI", "CNH", "CNSF", "COE", "COVID", "CP", "CPE", "CPI", "CPKC", "CPKCR",
    "CPL", "CPM", "CPPS", "CR", "CRA", "CRGS", "CS", "CSC", "CSE", "CSI", "CSM", "CUM",
    "CUS", "CVA", "CWC", "CWE", "DAM", "DANA", "DAP", "DBG", "DCA", "DCM", "DDA", "DDM",
    "DEA", "DEC", "DG", "DGI", "DGM", "DH", "DHK", "DID", "DJ", "DLG", "DLI", "DM", "DML",
    "DMT", "DRL", "DS", "DSI", "DSV", "DTF", "DUM", "DX", "DYA", "EAM", "EBD", "EC", "ECG",
    "EEM", "EEUU", "EG", "EHS", "EIC", "EJ", "EMA", "EMI", "EMS", "ENAI", "EP", "EPC", "EPL",
    "EQ", "EQU", "ES04710", "ES05577", "ES07096", "ES07485", "ES08877", "ESG", "ETN", "EXX",
    "EYP", "EZ", "EZI", "FA", "FAMA", "FARQ", "FCQ", "FF", "FG", "FGJNL", "FH", "FIME", "FL",
    "FLN", "FLY", "FMCM", "FMVZ", "FR", "FRA", "FRISA", "FSSPX", "FUD", "FX", "FYR", "G.C.",
    "G.I.", "GA", "GAO", "GAP", "GAR", "GB", "GC", "GDC", "GDD", "GDL", "GEN", "GEO", "GES",
    "GFS", "GGI", "GH", "GHASE", "GHG", "GIA", "GIF", "GJC", "GLDS", "GLI", "GLM", "GLR",
    "GMB", "GMM", "GMX", "GNP", "GO", "GPF", "GR", "GRG", "GRM", "GRUMA", "GSA", "GSI",
    "GSL", "GSO", "GT", "GT+", "GTCX", "GTM", "GTN", "GUM", "GVT", "GW", "GXO", "GYA", "GYR",
    "GZP", "HB", "HBS", "HCB", "HCG", "HEMSA", "HFZ", "HGO", "HGZMF", "HIG", "HIR", "HND",
    "HOB", "HRG", "HSC", "HSRL", "HVM", "HVR", "HYA", "IA", "IBP", "IBS", "ICM", "ICU",
    "IEC", "IGA", "IIQ", "IM", "IMF", "IMI", "INP", "IP", "IPA", "IPADE", "IPG", "IQ", "IQS",
    "ISA", "ISE", "ISI", "ISL", "ITASA", "IZY", "J.A.", "J.J.", "JAP", "JAV", "JB", "JCC",
    "JCI", "JD", "JFA", "JFZ", "JHG", "JHK", "JIR", "JIT", "JK", "JL", "JLA", "JLB", "JLC",
    "JP", "JRD", "JV", "JW", "K+S", "KAM", "KB", "KE", "KET", "KF", "KG", "KKO", "KKSP",
    "KOD", "KOI", "KP", "KSG", "KW", "KYN", "LAB", "LBD", "LBS", "LC", "LCI", "LDI", "LDN",
    "LDR", "LEA", "LED", "LEN", "LGS", "LGZ", "LMM", "LOP", "LPI", "LPM", "LR", "LS", "LSC",
    "LT", "LUX", "LVE", "LVT", "LY", "LYR", "LYX", "M.A.", "MAG", "MAM", "MARCO", "MBC",
    "MBM", "MBPH", "MCD", "MCR", "MD", "MDX", "MDY", "MEI", "MGM", "MH", "MJ", "MJL", "MK",
    "MKDC", "MKT", "MLP", "MM", "MMA", "MMM", "MNA", "MO", "MOMA", "MOR", "MPI", "MPM",
    "MQL", "MRM", "MSI", "MSNC", "MT", "MTC", "MTD", "MTM", "MTP", "MV", "MVA", "MVC", "MY",
    "MYA", "MYD", "MYM", "N.L", "NAD", "NASA", "NC", "NDT", "NEF", "NGK", "NH", "NHC", "NIU",
    "NOG", "NOVA", "NOX", "NP", "NPI", "NRM", "NT", "NUTEC", "NY", "NYC", "OAT", "OB", "OCA",
    "ODA", "ODS", "OE", "OEM", "OES", "OG", "OM", "OMA", "OMG", "ONE", "OSR", "P.P.", "PCN",
    "PCS", "PCV", "PDC", "PEI", "PEM", "PFS", "PG", "PGB", "PHK", "PIASA", "PIM", "PJENL",
    "PJF", "PJNL", "PMC", "PMM", "PMS", "PNT", "PO", "PP", "PPGMX", "PS", "PSC", "PTAR",
    "PTM", "PWR", "PYME", "PYOSA", "QFS", "QIN", "QPM", "QYE", "R.L", "RAC", "RAM", "RCA",
    "RCH", "RCM", "RCO", "RCP", "RCR", "RCV", "RDC", "RDI", "RDT", "REA", "REG", "RF", "RGC",
    "RIC", "RIMSA", "RK", "RLS", "RMG", "RMS", "ROMA", "ROW", "RP", "RPM", "RRQB", "RRT",
    "RS", "RSM", "RTE", "RV", "RVG", "RX", "S.E.R", "S.F.P", "SAE", "SAF", "SAG", "SAM",
    "SAR", "SAS", "SAZ", "SBG", "SCA", "SCP", "SCYF", "SEG", "SEMSA", "SEMTY", "SFE", "SFO",
    "SG", "SGI", "SH", "SHI", "SHN", "SIC", "SICAE", "SIE", "SIM", "SIMA", "SIO", "SISSA",
    "SIT", "SJ", "SKF", "SL", "SLS", "SM", "SMBC", "SMP", "SOA", "SOE", "SPC", "SPF", "SPM",
    "SPS", "SPV", "SR", "SSPM", "SSPV", "SST", "STE", "STI", "STIVA", "STK", "STU", "SYR",
    "SYS", "SÜD", "T.O.P.", "T.V.", "TAE", "TAF", "TBS", "TBT", "TCH", "TD", "TDG", "TDI",
    "TDR", "TEA+", "TECSA", "TEL", "TES", "TFO", "TG", "TH", "TI", "TKD", "TKP", "TL", "TLA",
    "TLM", "TLR", "TM", "TME", "TMP", "TMR", "TMS", "TOP", "TPA", "TPC", "TPS", "TQ", "TRMX",
    "TSC", "TSH", "TSI", "TSN", "TTQ", "TUM", "TVC", "TVH", "TVM", "TYG", "TÜV", "UAD",
    "UMI", "UMO", "UMT", "UP", "UPG", "US", "USAER", "USG", "USP", "UU", "UV", "VAO", "VBC",
    "VC", "VEA", "VEP", "VG", "VHS", "VISA", "VN", "VUE", "VYR", "WA", "WB", "WC", "WDM",
    "WEG", "WHY", "WIA", "WKS", "WO", "WTC", "XDC", "XE", "XI", "XIII", "XVI", "XVIII", "XX",
    "XX!", "XXIII", "XXV", "XY", "YGA", "YIB", "YSM", "ZAZ", "ZF", "ZOE", "ZU",
    # quinta tanda
    "HM", "MAC", "RM", "SCC", "UNEME", "ACS", "BYD", "CECAM", "CEN", "CEU", "CODE", "EDEC",
    "HD", "HP", "IOS", "JG", "JJ", "KC", "MF", "PCM", "PGJ", "SB", "XO", "CAI",
    # cuarta tanda
    "JM", "LM", "MR", "SADM", "UMM", "AG", "ERRE", "ICET", "RC", "TYM", "ADN", "JC", "VIP",
    "CM", "EMME", "GILSA", "GNV", "HG", "IZA", "SSNL", "AIM", "CROC", "FM", "FNSI",
    # tercera tanda
    "NAR", "UDEM", "ENC", "ORG", "CED", "PAL", "ALA", "LP", "NL", "MTY", "ABP", "GE", "JT",
    # segunda tanda, de la revisión una por una en el panel
    "UAC", "GM", "CB", "CSU", "SNTE", "CETIS", "GS", "SUD", "AAA", "DNA", "FC", "S.A", "TV",
    "ATR", "CONALEP", "CTM", "EMMSA", "FINSA", "HC", "ITL", "LTH", "MS", "MX", "ODM",
    "RR", "TRP", "UANE", "UJED", "UMAA", "UNID", "A.P.I.N.", "AA", "ABM", "ADL", "ADM",
    "ADOSA", "ALILA", "ARAF", "ATM", "AVL", "BARF", "BBQ", "BCD", "BCM", "BOC",
    "BPS", "BS", "C.B.T.A.", "C.V", "CAPT", "CBC", "CBH", "CBTA", "CDE",
    "CECAP", "CECATI", "CEMI", "CENDI", "CEO", "CIAC", "CIDT", "CIMEC", "CINSA", "CIVET",
    "CN", "CNC", "COCEEEPA", "COECYT", "COGA", "COMIMSA", "CSN", "CSR", "CT", "CTN",
    "DASA", "DAZ", "DILL", "DSJ", "DSM", "DT", "DYLSA", "EA", "EBDI", "EIYSE",
    "ESMED", "ESSEX", "FCA", "FEM", "GHSP", "GI", "GNC", "GP", "GUECSA", "GWM",
    "HDI", "HFL", "HQ", "HR", "IAC", "IBLC", "ICR", "IDEHSA", "IESEC", "IESIZ",
    "IFM", "IMES", "IMPAC", "ING", "ISAE", "ISISA", "ISMA", "ISS", "ISSTE", "IT", "J.C.",
    "JAC", "JR", "JS", "LCD", "LG", "M.F.C.", "M.G.", "MEX", "MJB", "ML", "MQ",
    "MSA", "MVP", "N.L.", "NDIAC", "NG", "OC", "OCP", "OMNIA", "OTR", "OV", "PC",
    "PEPI", "PFP", "PGJE", "PHOR", "PICS", "PMW", "PRONNIF", "PVC", "QAHWA", "QX",
    "RBJ", "RCG", "REYSI", "RG", "RGM", "RH", "RHI", "RL", "RT", "S.C.L.", "S.O.S.", "SDS",
    "SEAT", "SEMEFO", "SIBSA", "SNTSA", "SNTSS", "SOFEN", "STAM", "TAD", "TAP",
    "TEPSA", "TLE", "TNT", "TRC", "TSM", "UAAAN", "UFI", "UNEA", "UNILAM", "UNIVAS", "UPL",
    "UTEST", "UTT", "UVM", "VF", "VMV", "XCF", "XV", "YMCA",
    # séptima tanda: iniciales con punto (la corrección las volvía "JV") y marcas
    # que solo existen en mayúsculas
    "AHMSA", "IHOP", "J.V.",
    # octava tanda: siglas de universidades, comisiones y marcas que salieron
    # en la caja de mayúsculas del panel
    "ARPE", "ATMR", "AZ", "B.C.", "BDH", "BF", "BRP", "C.F.E", "CCC", "CEART", "CESPM",
    "CESPT", "CU", "CUU", "ESL", "FEX", "GRN", "HMO", "HV", "IMARC", "ITSON", "OASA",
    "R.L.", "TJ", "UABC", "UACJ", "UAT", "UGRS", "YZA",
}

# Categorías donde una calle no aplica: son accidentes geográficos y obras, no
# domicilios. No entran en la regla de "sin dirección" (sí en la ortografía).
# Santiago pidió sacarlas al ver la primera lista: salían ríos y lagunas.
SIN_CALLE_EXENTAS = {
    "RIVER_STREAM", "SEA_LAKE_POOL", "CANAL", "DAM", "ISLAND", "FOREST_GROVE",
    "SWAMP_MARSH", "HILL_MOUNTAIN", "BEACH", "TUNNEL", "BRIDGE",
    "JUNCTION_INTERCHANGE", "RAILROAD_CROSSING", "SCENIC_LOOKOUT_VIEWPOINT",
}

LOWERS = {"a", "de", "del", "y", "o", "en", "con", "por", "para", "al", "un", "una", "e", "u",
          "and", "at"}
CONDITIONAL_ARTICLES = {"el", "la", "los", "las"}
PREPOSITIONS = {"de", "del", "a", "en", "por", "con", "para", "al"}
# Marcas que se dejan tal cual, y solo en estas formas exactas (distingue mayúsculas)
KEEP_AS_IS = [
    "OXXO", "Oxxo", "Toks", "Tok's", "FirstCash",
    # marcas con mayúscula interna que marcó Santiago en el panel
    "CIBanco", "Back2Back", "SushiStar", "ABControl", "AlSuper", "BanBajio", "BanBajío",
    "BarberShop", "BocaPalma", "CADHaus", "CECyTeC", "CircleK", "CombuGas", "ConstruAlianza",
    "CrossSport", "DeMueble", "EnelX", "EvoFit", "FlexTec", "FullOK", "GamePlanet", "GmbH",
    "HairStyle", "IIbérica", "InnovaSport", "KickOff", "KinderClinik", "KiwiGo", "L’Anfora",
    "LagAcero", "LagunAcero", "LaserMex", "MacStore", "MiGasolina", "MiPlaza", "MyTAAC",
    "NoManches", "PetroLaguna", "PowerFit", "PressoTechnik", "ProFit", "ProHumanidad",
    "RamosPlanta", "SantaRita", "ServicePoint", "SkinMedical", "SonyGas", "Sta.Ma.",
    "Tee*Zone",
    # tercera tanda
    "BanRegio", "TodoGas", "EcoVía", "CargoGas",
    # cuarta tanda ("FullOk" y "FullOK" andan las dos en el mapa)
    "ChargeNow", "SuKarne", "DeAcero", "FullOk",
    # sexta tanda: marcas con mayúscula interna, se conservan tal cual
    "#TomaVinoMexicano", "*Terapia", "+Empanadas", "1Mundo", "2Dent", "3Pack", "5Punto7",
    "5aSec", "5áSec", "ABCNoticias.mx", "ADental", "AMM's", "ARclad", "AZcom", "AbaSeguros",
    "AccesoMunich", "AcuityBrands", "AeroCarga", "AeroMotor", "AeroMéxico", "AeroViajes",
    "AgroCapital", "AirWelding", "AkzoNobel", "AlPe", "AllergyCo", "AlterStudio", "AluGlass",
    "AmCham", "AmIgo", "AniDent", "ApTec", "AquaMatic", "AquaPro", "ArtLab", "ArteXpress",
    "ArtlieverSoul", "AtelierNails", "AurrerÁ", "AutoColores", "AutoExpress", "AutoGas",
    "AutoKam", "AutoLavado", "AutoScan", "AutoShampoo", "AutoVEN", "AyR", "BHermanos",
    "BLEventos", "BPwork", "BTan", "BabytoKid", "BackOffice", "BalloonBlack", "BanCoppel",
    "BanrRegio", "BarberClub", "BeSa", "BeerBus", "BiblioCiber", "BienEstar", "BinBit",
    "BodyShop", "BoleARTE", "BomBón", "BordArt", "BurGus", "CAtarina", "CBETis", "CBPesa",
    "CCLife", "CDerma", "CECyTE", "CENDINo.", "CHyO", "CIsa", "CarPack", "CarWash",
    "CardioLink", "CargoQuin", "CarneMart", "CasaBella", "CeCyTe", "CeDeReg", "CePeDi",
    "CediGrafic", "CerJuárez", "ChambaMart", "ChargePoint", "CheckPoint", "CiRgos",
    "CiberSpace", "CloudSourceIT", "CoMO", "ComNor", "ComRegio", "CombiTacos", "CompuMark",
    "CompuMax", "ConMet", "ConSiente", "ConfiabilidadMX", "ConvertiAuto", "CookiesCo",
    "CopyArq", "CorPo", "CoreMTY", "CorpoNext", "CorteAcero", "CotitaCake", "CoyotePark",
    "CrediMotors", "CrediSoluciones", "CrossFit", "CrossFitters", "CsoftMTY", "Cto.Duna",
    "CubboX", "CyR", "DGas", "DItalia", "DLimpieza", "DeArce", "DePesca", "DeWalt",
    "DeliCarnes", "DelySnack", "DentALRO", "DentaLumex", "DentalBO", "DentalMed",
    "DermaExperts", "DessAir", "DiGiLand", "DongJin", "Dr.Andrés", "Dra.Emma",
    "Dra.Esmarlyn", "Dra.Ingrid", "Dra.Leticia", "Dress’It", "DrinksLab", "D´Luxe",
    "D’Bazar", "D’Luxe", "EGOMode", "EZRide", "EasyPrint", "EcoBikes", "EcoClean",
    "EcoSistemas", "EcoVia", "EconoDent", "EduKite", "ElFyr", "ElUro", "ElectroFerretería",
    "EnbalanC", "EnerSys", "EnvíoShop", "EpicGroup", "EscCha", "EstarBien", "EuroCar",
    "EverNeed", "EzMi", "FasTracKids", "FastKart", "FerTrade", "FerreTodo", "FibraMTY",
    "First.Cash", "FisioCelen", "FitClub", "FitFit", "FixerTech", "FlashPark", "ForLabs",
    "FotoLab", "FreshFood", "FrunchPop", "FullGas", "GTime", "GasOne", "GelMx",
    "GeoAventura", "GeoParque", "GerJor", "GilTrevino", "GoCredit", "GoldenSNT", "GrafTech",
    "GuerraGómez", "HGermano", "HNk", "HanMex", "HariMasa", "HemoVita", "HighPark",
    "HillSafe", "HiperLumen", "HomeCenter", "HomeDepot", "HomeTime", "HotDogs", "IBeauty",
    "IIRSAcero", "IPark", "IRspa", "IdeArte", "IglesiaSan", "ImplArt", "ImpresionArte",
    "InHedge", "InmediK", "InnoDent", "InnovMed", "InnovaMed", "InovaDent",
    "IntegraRedGreen", "IntegraTours", "IntelAir", "InteriMöbel", "InvoiceOne.mx", "IonBond",
    "IphoneLand", "JArdín", "JDIbarra", "JJr", "Jac&Ray", "JaecooLinda", "JazzConnexion",
    "JezLa", "KCrentas", "KalaMedia", "KeFotos", "KemKare", "KidsTown", "KindMed", "KirKot",
    "KooKay", "KwonDo", "LEDs", "LavaFresh", "LePizzeria", "Lic.Diego", "LivIn", "LoJack",
    "LogisAll", "LoviDent", "LozMer", "LyzChapa", "MEGAlogistics", "MItras", "MLTi",
    "MUultieléctrica", "MacGeek", "MacZone", "MadCoffee", "MagicWash", "MarCar", "MarMar",
    "MariLens", "Mario.Garza", "MarisQ8", "MarySal", "MaxiHome", "MaxiRent", "McCall",
    "McCarthy's", "McCarthys", "McCormick", "McFlys", "McGregor", "McKernan", "McKinley",
    "MecaniCar", "MedCare", "MedHome", "MediAcces", "MerKdon", "MercaDia", "MetroMeter",
    "MiniBodegas", "MonYor", "MoraZul", "MotoRad", "Mr.Bravo420", "Mr.Pizza", "NLMon",
    "NaturalFilms", "NeoMed", "NetPoint", "NewLighting", "NitroRx", "NorthSide",
    "NovedadesLa", "NovoDent", "NreLighting", "O.Spa.Salón", "OdontoMTY", "OmniSorce",
    "OnDerm", "OnlyFit", "OpenAg", "OrthoTrauma", "PGCina", "PIzza", "PRGarque",
    "PROducciones", "PaMiCampo", "Pak2Go", "PaqMex", "ParaMascotas", "PecasGarage",
    "PennyNailsStudio", "PenyRiel", "PepsicoI", "PerfecPack", "PermaChef", "PetLobby",
    "PetVet", "PetroCalibrations", "PetroMex", "PizzAndLove", "PlacitaG", "PlanNet",
    "PlastiSanta", "PlayCity", "PleniTÚ", "PodoClean", "PolyOne", "Pre*Star", "PreStar",
    "PrintWorks", "ProApoyo", "ProCell", "ProDynamics", "ProLogis", "ProMakeup", "ProMedic",
    "ProMesa", "ProMotros", "ProSESA", "ProSankin", "ProximityParks", "PyME", "QuieroChamba",
    "RTours", "RaJet", "Radiotec3D", "RayBar", "RayTools", "ReMax", "ReciLaurs",
    "RedExpress", "ReduClinic", "RefaccionariaDávila", "RegioCar", "RegioDental", "RegioLab",
    "RegioPack", "RelTek", "ReparacionesMTZ", "RigNet", "RuffusVet", "RyL", "S.A.de",
    "SAldivar", "SCyF", "SWISSLab", "SantaRosa", "ScotiaBank", "SeAH", "SerMaCon",
    "ServiAcero", "SiberDay", "SisMex", "SkyGamers", "SmartFix", "SmileLab", "SolMex",
    "SonoViche", "SportAuto", "StarCluster", "StonCor", "SubWay", "SunSet", "SuperColchones",
    "SurtiPet", "SurtiSnack", "SyPPASA", "SysOp", "TLTerminals", "TOPAZdeluxe", "TRiBÜ",
    "TSCMex", "TUrgentes", "TaeHwa", "TaeKwonDo", "TakiMex", "TeFort", "TecBlue",
    "TecnoBlinds", "TecnoGam", "TecnoTinta", "TeknoBike", "TelePerformance", "TempZone",
    "TermoGas", "TicTac", "TiendaSoccer", "TintoLav", "TintoPet", "TodoDren", "TomaReto",
    "TomaVinoMexicano", "TopoChico", "TorRey", "TorreCID", "TortiTrigo", "TostiRegia",
    "TownHouse", "TransVidrio", "TranspadeX", "TresMásDos", "TurboLlantas", "TyT",
    "TydenBrooks", "UltraVioleta", "UnidadSanta", "UrbiVilla", "VIPs", "VaGO", "VaRo",
    "VeganMunch", "VetConnect", "VetDoctor", "ViBa", "ViBe", "VillaGon", "VivaAerobus",
    "WAsh", "WatSon", "WeClean", "WeWork", "WishLand", "WorldWide", "XBlaster", "XtraCurvy",
    "YGas", "YaRepara.com", "YanFeng", "YoTeCielo", "[E]Bosco", "[E]Matamoros", "eFC",
    "eFarma", "eValor", "enTecnología", "euroDólar", "iClean", "iD", "iLed", "iQ", "iR",
    "iRepair", "iShop", "iStay", "iStudy", "iWash", "iZZi", "moreEnglish", "nutriADN",
    "pARQUE", "vVsta",
    # quinta tanda
    "TecMilenio", "@Destination", "5àSec", "DePrizza", "MercaDía", "SwissLab", "AlEn",
    # séptima tanda
    "CECyTEC",
    # octava tanda
    "3Dental", "AlFaEs", "CBTis", "CECyTES", "MoldeArte", "SuperChivas", "TotalGas",
    "ViveBús",
]
# Se arman en un solo patrón (van más de cincuenta): una pasada en vez de una
# por marca, que con miles de places sí se nota.
_RE_KEEP = None
# Palabras indiferentes: se quedan como vengan escritas y no se proponen ni se
# marcan. "KM 110+100" se queda en KM y "Km 22" se queda en Km; igual con las
# siglas que también son palabras normales, para que "GAMA Muebles" y "Gama
# Muebles" convivan sin que ninguna de las dos salga en la lista. Solo aplica
# si la palabra ya traía alguna mayúscula: en un nombre todo en minúsculas sí
# se le pone la inicial, como a cualquier otra palabra.
RESPETAR_FORMA = {"km", "kms",
                  "dar", "gama", "idea", "mas", "med", "dic", "cat", "cab",
                  "pisa", "spa", "usa", "ok", "ar", "ap", "ta", "os", "capa",
                  # sexta tanda: las que no se pueden decidir a ciegas se dejan
                  # como vengan escritas, que es lo único que no puede hacer daño
                  "abar", "abasa", "abba", "absa", "abtec", "adex", "adia", "adni", "adwa",
                  "aecom", "aegbn", "aeme", "agape", "aglo", "aiasa", "aigsa", "aima",
                  "alco", "alda", "alera", "algol", "alsa", "alsea", "alva", "amah", "ambia",
                  "amex", "amif", "amnsa", "ance", "anmon", "apec", "apen", "apisa", "apsa",
                  "apsi", "aquor", "arcyt", "ardan", "arpac", "arris", "asap", "asea",
                  "asev", "asis", "askco", "aspe", "asuni", "atesa", "atmx", "atos", "auros",
                  "axxa", "ayvi", "balam", "bemis", "bemol", "besta", "beto", "beysa",
                  "binet", "birsa", "bread", "bydsa", "bymsa", "cacep", "cadi", "cafam",
                  "camm", "cams", "carso", "cart", "casam", "cast", "cato", "cayam", "cbmas",
                  "cbre", "ccai", "cdem", "cdni", "cdpi", "ceae", "cebi", "cebsa", "cecac",
                  "cecat", "cece", "cecit", "cecyt", "ceda", "cedei", "cedet", "cedi",
                  "cedim", "ceduk", "cefi", "cegbi", "ceio", "cejn", "cemac", "cemer",
                  "cemix", "cenka", "ceox", "cepai", "cepar", "cepog", "cerya", "cesi",
                  "ceti", "ceva", "cfea", "cicam", "cidem", "cimat", "cimav", "cims", "cisa",
                  "cisem", "cites", "citi", "citsa", "cmuch", "cnop", "coka", "comex",
                  "comsa", "cone", "conv", "cope", "coreb", "corp", "cova", "crisa", "crown",
                  "cucep", "cucsa", "curam", "cvac", "cysa", "d.j.i.s.c.", "daare", "dacsa",
                  "dags", "dakar", "damf", "daos", "dareh", "davsa", "defg", "delf", "demac",
                  "demsa", "derly", "dicsa", "digar", "dilsa", "dims", "dinsa", "dipsa",
                  "dissa", "ditmo", "dmmi", "doiaz", "dose", "drie", "dttec", "durc", "dyca",
                  "e.e.u.u.", "ebex", "ecsa", "edssa", "educa", "egade", "egap", "egat",
                  "ehisa", "ehko", "einsa", "elsei", "emaet", "emcar", "emec", "emis",
                  "emsa", "emsad", "enco", "enoc", "epsa", "eqcos", "erick", "erma", "ersa",
                  "esab", "esdm", "esmi", "estoa", "evimi", "exan", "exca", "exxa",
                  "f.n.s.i.", "fagsa", "fave", "fecsa", "fesa", "fics", "fims", "fisc",
                  "focim", "foods", "fóvea", "gafer", "gafi", "galo", "gami", "gamo",
                  "garyr", "gati", "gave", "gebi", "geea", "gein", "gema", "gepsa", "getsa",
                  "gill", "gmso", "gocar", "gopar", "goru", "guvi", "hcco", "hega", "helc",
                  "hemaq", "hisa", "hoga", "hsac", "hvac", "iafcj", "iasa", "iasd", "icam",
                  "icami", "icasa", "icce", "icem", "icnsa", "icon", "icsp", "icum", "idear",
                  "ideen", "ideka", "idtec", "idunn", "iece", "ieee", "iemsa", "iewc",
                  "ifix", "igsa", "igui", "ihsa", "iicc", "iims", "ilpea", "ilsp", "imaz",
                  "imeba", "immar", "impeg", "imsa", "inasa", "inba", "inbi", "inde", "indi",
                  "inec", "ingea", "inics", "inko", "insum", "ipasa", "ipco.", "ipem",
                  "ipesa", "ipmco", "ipnl", "ippm", "ipsa", "irpac", "isac", "isga", "isgo",
                  "itesa", "iutt", "iwtp", "jagr", "jema", "jireh", "jokr", "jomar", "jumex",
                  "kalen", "kapse", "keigi", "koat", "labnl", "lear", "loes", "lovi", "ltda",
                  "lumaa", "luva", "maba", "mach", "magg", "maggi", "mahle", "maky", "malro",
                  "mapsa", "maqro", "mdic", "meic", "mesil", "metsa", "mevsa", "mexi",
                  "meyva", "mibel", "mibos", "migs", "mimah", "minar", "mitc", "mold",
                  "molo", "mtya", "mutt", "muvi", "mysa", "nabhi", "nadro", "namm", "naza",
                  "nican", "nice", "nidec", "nitto", "nosa", "nossa", "novem", "novus",
                  "numen", "odina", "ompi", "onix", "ontal", "ortho", "osyma", "otif",
                  "oton", "parc", "pcel", "pcell", "peisa", "pepsa", "picsa", "pidev",
                  "pits", "pitt", "popo", "prome", "psaip", "ptyem", "putz", "rade", "radec",
                  "raga", "rapsa", "rasa", "rase", "rego", "relsa", "remai", "remsa", "resa",
                  "reset", "rgis", "ribs", "riisa", "rirsa", "rosco", "ryasa", "saar",
                  "sacmi", "safi", "saisa", "sapa", "sarm", "saro", "sbpro", "scuda", "sdum",
                  "sems", "sepsa", "serco", "sero", "sersa", "siam", "sier", "sigma",
                  "simaq", "simec", "sims", "sinaí", "sindu", "sios", "sisca", "sitnl",
                  "sito", "sitsa", "sitv", "siww", "sofom", "soho", "solis", "somal",
                  "stihl", "supsa", "susi", "sysco", "tdah", "teco", "tedi", "tepso",
                  "tersa", "timsa", "totsa", "trasa", "tress", "tsim", "tuesa", "tyasa",
                  "tymsa", "uabcs", "uanle", "ubim", "udat", "umeb", "umega", "upes",
                  "urrea", "usem", "ussa", "utec", "utres", "uvne", "vaeo", "veca", "vima",
                  "vipa", "vipet", "vw&man", "waxx", "weir", "woory", "xcien", "xkin",
                  "xxvi", "yosi", "zeiss", "zenda", "zuri",
                  # séptima tanda: palabras que son marca y palabra normal a la vez,
                  # se quedan como vengan escritas
                  "alfa", "arca", "arco", "care", "gas", "gym", "kia", "lala", "six",
                  "vips", "walmart",
                  # las marcas en mayúsculas: se respeta lo que escribió el editor,
                  # ni se aplastan ni se fuerzan
                  "axa", "cemex", "famsa", "femsa", "ixe", "pemex", "suspe",
                  # octava tanda: marca y palabra a la vez, o siglas que también
                  # se escriben como nombre propio
                  "aptiv", "aura", "blink", "cut", "eni", "esfer", "uach",}

# Palabras que Santiago revisó y descartó: la corrección está bien y no son
# siglas. No cambian nada de la ortografía, solo sirven para que la página de
# revisión no las vuelva a preguntar, en cualquier navegador.
NO_SON_SIGLAS = {
    "AIR", "ALO!", "AROVA", "ARSA", "ARTEAGA", "BANCO", "BANORTE",
    "CAUSA", "CESAME", "CHAPA", "COCACOLA", "COPY", "CREE", "Chilorio'S",
    "CoSinaloa", "DANSA", "DE", "DELTAPLAST", "DEM", "DENTAL", "DIMAC", "DK", "EJIDO", "EL",
    "EPCA", "EXA", "FE", "FED", "FERSA", "FESTO", "Fisher'S", "GALES", "GIS", "GISA",
    "GNZLZ", "GOMA", "GOVI", "GRILL", "GST", "GVE", "GÜERO", "IN", "INBURSA",
    "INNOTEC", "IPOC", "IRSA", "ISUZU", "JAPASA", "JDF", "JESUS", "JIBE", "JIS", "JOSE",
    "JUANA", "KID'S", "KMIN", "LAGUNA", "LALO", "LAMSA", "LUMEN", "LYRBA",
    "MADRE", "MAPFRE", "MAQCER", "MAVITHA", "MAY", "MEDICAB", "MEZE", "MILSA",
    "MINSA", "MUMA", "MUR", "NAN", "NET", "NGFIT", "NORCAST", "ORAL", "OSC", "OSEA",
    "PArque", "PLANO", "PLIMSA", "POWER", "PRAISA", "PUNTO", "PaPa", "REMI",
    "RENTA", "REPSA", "RIVA", "SACSA", "SALIN", "SEKKAN", "SHORE", "SIMAS", "SIMSA", "SOSA", "SUPERIOR", "SURA", "SURMAN", "TOJI", "TOKA", "TYCSA", "URBAN", "VARA",
    "VELEZ", "VERSA", "VIMSA", "VOSS", "WALK", "XFIT", "iGUi",
    # sexta tanda: palabras y nombres escritos a gritos, la corrección es la buena
    "11:ONCE", "ABEL", "ALTA", "AMA", "AMOR", "APOYO", "AQUI", "AREA", "ARENA", "AS", "ASI",
    "CANTÚ", "CASA", "CASTA", "CLARA", "CLUB", "COLOR", "CORTE", "CRUZ", "DATA", "DEEP",
    "DENSO", "DES", "DIAZ", "DIEGO", "DIEZ", "DIGA", "DON", "EH", "ELITE", "ESA", "ESE",
    "ESTE", "ETAPA", "FIFA", "FLOR", "GALA", "GAME", "GAMMA", "GORDO", "GROUP", "GRUPO",
    "HALO", "HOME", "HOPE", "INDIO", "IRENE", "IZZI", "JENNY", "JUAN", "LEAL", "LEGO",
    "LEONA", "LIFE", "LINDA", "LOVE", "LUNA", "MAN", "MARIA", "MARS", "MART", "MAX", "MI",
    "NO.", "NUEVA", "ON", "PASA", "PEGAR", "PEPE", "POLLO", "POP", "PROF", "PUNTA", "REDES",
    "ROBLE", "SALÓN", "SAME", "SAN", "SANTA", "SANTO", "SER", "SIGUE", "SOGA", "SUSHI",
    "TACOS", "TAURO", "TE", "TEAM", "THINK", "UNICA", "UNO", "VA", "VISTA", "VIVES", "VIVIR",
    "WASH",
    # octava tanda: palabras normales escritas a gritos
    "CAMPO", "NIÑOS", "RIO", "SALUD", "SHOP",
}

# ---------------------------------------------------------------------------
# Dos arreglos respecto al JavaScript original, pedidos por Santiago
# ---------------------------------------------------------------------------
# 1) Las llaves de ACCENT_FIXES con espacio nunca se aplicaban: fixGrammar
#    corrige palabra por palabra, así que "circulo k" o "nuevo leon" jamás
#    coincidían y quedaban como "Circulo K" y "Nuevo Leon". Aquí se hace una
#    pasada previa por frases, de la más larga a la más corta.
FRASES = sorted((k for k in ACCENT_FIXES if " " in k), key=len, reverse=True)

# 2) Una inicial con punto ("Jorge A. Treviño") se convertía en la preposición
#    "a" porque LOWERS no distinguía el punto. Ahora se respeta la inicial.
_RE_INICIAL = re.compile(r"^[A-Za-zÀ-ÿ]\.$")


def es_inicial(w):
    """Una sola letra seguida de punto: es una inicial, no una palabra."""
    return bool(_RE_INICIAL.match(w))


# 3) Varias entradas del diccionario traen palabras de más respecto a su llave
#    ("palacio de hierro" -> "El Palacio de Hierro", "sams" -> "Sam's Club",
#    "aurrera" -> "Bodega Aurrerá", "extra" -> "Tiendas Extra"). Si el nombre
#    ya traía esas palabras, se duplicaban: "El Palacio de Hierro" acababa como
#    "El El Palacio de Hierro" y "Sams Club" como "Sam's Club Club". Aquí se
#    recorta lo que ya está puesto a un lado o al otro.
def _sin_duplicar(reemplazo, antes, despues):
    palabras = reemplazo.split(" ")
    if len(palabras) > 1:
        prev = [p for p in re.split(r"[\s\-]+", antes.strip()) if p]
        while len(palabras) > 1 and prev and palabras[0].lower() == prev[-1].lower():
            palabras.pop(0)
            prev.pop()
    if len(palabras) > 1:
        sig = [p for p in re.split(r"[\s\-]+", despues.strip()) if p]
        i = 0
        while len(palabras) > 1 and i < len(sig) and palabras[-1].lower() == sig[i].lower():
            palabras.pop()
            i += 1
    return " ".join(palabras)

# ---------------------------------------------------------------------------
# Port de fixGrammar
# ---------------------------------------------------------------------------
LETRA = "A-Za-zÀ-ÿ"          # las mismas clases que usa el JavaScript
_RE_BBVA = re.compile(r"\bBBVA\s+Bancomer\b", re.I)
_RE_PAN = re.compile(r"\bPAN\b")
# primera letra de cada palabra: inicio de cadena o tras uno de esos separadores
# se agregan ¡ ¿ y @ a los separadores: sin ellos "¡QUE TACOS!" quedaba
# "¡que Tacos!" y "@destination" no recuperaba su mayúscula
_RE_CAPITALIZA = re.compile(r"(?:^|[\s\-\(\"/“”&¡¿@]|'(?!s\b))([a-zÀ-ÿ])")
_RE_PALABRA = re.compile(r"([a-zA-ZÀ-ÿ.]+(?:'[a-zA-ZÀ-ÿ]+)?)")
_RE_PUNTOS = re.compile(r"[.,:;()\"“”]")
MARCA_INI = chr(0xE000)   # zona privada de Unicode: no aparece en nombres reales
MARCA_FIN = chr(0xE001)
_RE_MARCADOR = re.compile(MARCA_INI + r"(\d+)" + MARCA_FIN)
_RE_ATT = re.compile(r"\bat&t\b", re.I)
# 5) Lo que va entre corchetes se deja como está: son etiquetas, no palabras
#    ("Pemex [E] 08877"). El paso de minúsculas las aplastaba a "[e]".
_RE_CORCHETES = re.compile(r"\[[^\[\]]{1,24}\]")
# 4) Códigos con letras y números en mayúsculas ("Pemex - ES08877", "Tiendas 3B",
#    "C5", "5TO"): son claves o nombres de marca, no palabras, y el paso de
#    minúsculas los aplastaba ("Es08877", "3b"). Se protegen como las marcas.
_RE_CODIGO = re.compile("(^|[^" + LETRA + r"\d])([" + LETRA + r"\d]+)(?=[^" + LETRA + r"\d]|$)")


def es_codigo(tok):
    """Mezcla letras y números, toda en mayúsculas: ES08877, 3B, C5, 5TO."""
    if tok != tok.upper():
        return False
    return bool(_RE_SOLO_LETRAS.sub("", tok)) and any(ch.isdigit() for ch in tok)


def se_respeta(tok):
    """Palabra que se deja con las mayúsculas que ya traía (KM / Km, GAMA / Gama).

    Si viene toda en minúsculas no se protege: ahí no hay nada que respetar y
    le toca la mayúscula inicial como a cualquier palabra del nombre.
    """
    return tok.lower() in RESPETAR_FORMA and tok != tok.lower()


def _patron_keep():
    """Patrón con todas las marcas de KEEP_AS_IS, de la más larga a la más corta."""
    global _RE_KEEP
    if _RE_KEEP is None:
        piezas = "|".join(re.escape(t) for t in sorted(KEEP_AS_IS, key=len, reverse=True))
        _RE_KEEP = re.compile("(^|[^" + LETRA + "])(" + piezas + ")(?=[^" + LETRA + "]|$)")
    return _RE_KEEP


def fix_grammar(texto):
    """Misma salida que fixGrammar() del userscript."""
    guardadas = []
    src = str(texto)

    def _guardar(m):
        marcador = MARCA_INI + str(len(guardadas)) + MARCA_FIN
        guardadas.append(m.group(2))
        return m.group(1) + marcador

    src = _patron_keep().sub(_guardar, src)

    def _guardar_codigo(m):
        tok = m.group(2)
        if not es_codigo(tok) and not se_respeta(tok):
            return m.group(0)
        marcador = MARCA_INI + str(len(guardadas)) + MARCA_FIN
        guardadas.append(tok)
        return m.group(1) + marcador

    src = _RE_CODIGO.sub(_guardar_codigo, src)

    def _guardar_corchetes(m):
        marcador = MARCA_INI + str(len(guardadas)) + MARCA_FIN
        guardadas.append(m.group(0))
        return marcador

    src = _RE_CORCHETES.sub(_guardar_corchetes, src)

    s = _RE_BBVA.sub("BBVA", src)
    s = _RE_PAN.sub("%%%PAN%%%", s)
    s = _RE_CAPITALIZA.sub(lambda m: m.group(0).upper(), s.lower())

    # frases del diccionario (arreglo 1): se sustituyen antes de la pasada por
    # palabras y se guardan, para que esa pasada no las vuelva a tocar
    for frase in FRASES:
        patron = re.compile("(^|[^" + LETRA + "])(" + re.escape(frase) + ")"
                            "(?=[^" + LETRA + "]|$)", re.I)

        def _guardar_frase(m, frase=frase):
            marcador = MARCA_INI + str(len(guardadas)) + MARCA_FIN
            guardadas.append(_sin_duplicar(ACCENT_FIXES[frase],
                                           s[:m.start(2)], s[m.end(2):]))
            return m.group(1) + marcador

        s = patron.sub(_guardar_frase, s)

    original = s   # los desplazamientos se miden sobre la cadena de esta etapa

    def _palabra(m):
        w = m.group(1)
        offset = m.start(1)
        cl = _RE_PUNTOS.sub("", w)
        l = cl.lower()
        u = cl.upper()
        if w.upper() in ALLOWED:
            return w.upper()
        if l in ACCENT_FIXES:
            return _sin_duplicar(ACCENT_FIXES[l], original[:offset], original[offset + len(w):])
        if u in ALLOWED:
            return u
        if es_inicial(w):
            return w.upper()   # arreglo 2: "Jorge A. Treviño" conserva la inicial
        if l in CONDITIONAL_ARTICLES:
            sub = original[:offset].strip()
            palabras = re.split(r"[\s-]+", sub)
            previa = palabras[-1].lower() if palabras else ""
            if previa in PREPOSITIONS:
                return l
            return w
        if l in LOWERS:
            if offset == 0:
                return w
            if original[offset - 1] == "&":
                return w
            previa1 = original[offset - 1] if offset - 1 >= 0 else ""
            previa2 = original[offset - 2] if offset - 2 >= 0 else ""
            if previa1 in ("-", "(", '"', "'"):
                return w
            if previa1 == " " and previa2 in ("-", "(", '"', "'"):
                return w
            return l
        return w

    s = _RE_PALABRA.sub(_palabra, original)
    s = s.replace("%%%pan%%%", "PAN")
    s = _RE_ATT.sub("AT&T", s)
    s = _RE_MARCADOR.sub(lambda m: guardadas[int(m.group(1))], s)
    return s


def necesita_correccion(texto):
    """Misma condición que needsGrammarFix() del userscript."""
    if not texto or len(texto) < 3:
        return False
    if texto in ALLOWED:
        return False
    return texto != fix_grammar(texto)


# ---------------------------------------------------------------------------
# Ayudas para la lista del panel
# ---------------------------------------------------------------------------
_RE_SOLO_LETRAS = re.compile("[^" + LETRA + "]")
_RE_VOCAL = re.compile("[aeiouáéíóúàèìòùäëïöüAEIOUÁÉÍÓÚÀÈÌÒÙÄËÏÖÜ]")
_RE_DIGITO = re.compile(r"\d")
# palabras cortas que salen en mayúsculas sin ser siglas ("DE", "LA", "THE")
_NO_SIGLAS = (LOWERS | CONDITIONAL_ARTICLES | PREPOSITIONS
              | {"the", "los", "las", "un", "una", "of"})


def _parece_sigla(tok):
    """¿Ese pedazo del nombre trae mayúsculas a propósito?

    Sí para las abreviaturas (GDL, UADY, CTM, C5, 3B) y para las marcas con
    mayúscula interna (BanBajio, AutoZone, iHop). No para las palabras largas
    en mayúsculas, que casi siempre son un nombre escrito a gritos
    ("FARMACIA FRANCESA"), ni para los artículos y preposiciones.
    """
    letras = _RE_SOLO_LETRAS.sub("", tok)
    if not letras or letras.lower() in _NO_SIGLAS:
        return False
    todo_mayus = tok == tok.upper()
    if _RE_DIGITO.search(tok) and todo_mayus:
        return True            # 3B, C5, G500
    if len(letras) < 2:
        return False
    if todo_mayus:
        # corta, o sin vocales: sigla. Larga y con vocales: nombre a gritos.
        return len(letras) <= 5 or not _RE_VOCAL.search(letras)
    return tok != tok.capitalize() and tok != tok.lower()


def siglas_aplastadas(antes, despues):
    """Siglas y marcas que la propuesta deja de respetar.

    Sirve para marcar esos renglones en el panel: casi siempre significan que
    a la lista de siglas permitidas le falta esa palabra, no que el nombre
    esté mal. Santiago las va agregando conforme salen.
    """
    def piezas(s):
        return [t for t in re.split(r"[\s\-/(),]+", s) if _RE_SOLO_LETRAS.sub("", t)]

    despues_piezas = piezas(despues)
    return [t for t in piezas(antes)
            if _parece_sigla(t) and t not in despues_piezas
            and t not in NO_SON_SIGLAS and t.upper() not in NO_SON_SIGLAS]
