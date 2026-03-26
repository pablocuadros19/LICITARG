"""Configuración central de LICITARG."""

from pathlib import Path

# Rutas
BASE_DIR = Path(__file__).parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# URLs de descarga — Adjudicaciones nacionales COMPR.AR (2015-2020)
ADJUDICACIONES_URLS = {
    2015: "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.10/download/adjudicaciones-2015.csv",
    2016: "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.6/download/adjudicaciones-2016.csv",
    2017: "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.2/download/adjudicaciones-2017.csv",
    2018: "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.15/download/adjudicaciones-2018.csv",
    2019: "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.18/download/adjudicaciones-2019.csv",
    2020: "https://infra.datos.gob.ar/catalog/jgm/dataset/4/distribution/4.20/download/adjudicaciones-2020.csv",
}

# CONTRAT.AR — Obra pública
CONTRATAR_URL = "https://infra.datos.gob.ar/catalog/jgm/dataset/30/distribution/30.3/download/onc-contratar-ofertas.csv"

# SIPRO — Proveedores legacy
SIPRO_URL = "https://infra.datos.gob.ar/catalog/modernizacion/dataset/2/distribution/2.11/download/proveedores.csv"

# Registro Nacional de Sociedades (datos.jus.gob.ar)
# El ZIP más reciente se descarga manualmente desde:
# https://datos.jus.gob.ar/dataset/registro-nacional-de-sociedades
SOCIEDADES_URL = "https://datos.jus.gob.ar/dataset/registro-nacional-de-sociedades"

# Sucursales de interés (MVP hardcodeado)
SUCURSALES = {
    "San Martín": {
        "localidades": ["SAN MARTIN", "SAN MARTÍN", "GRAL. SAN MARTIN", "GENERAL SAN MARTIN",
                        "GENERAL SAN MARTÍN", "VILLA BALLESTER", "JOSE LEON SUAREZ",
                        "VILLA LYNCH", "VILLA MAIPÚ", "BILLINGHURST"],
        "provincia": "Buenos Aires",
    },
    "Tigre": {
        "localidades": ["TIGRE", "DON TORCUATO", "GENERAL PACHECO", "EL TALAR",
                        "BENAVÍDEZ", "BENAVIDEZ", "NORDELTA", "RINCÓN DE MILBERG"],
        "provincia": "Buenos Aires",
    },
    "San Isidro": {
        "localidades": ["SAN ISIDRO", "MARTINEZ", "MARTÍNEZ", "ACASSUSO",
                        "BECCAR", "BOULOGNE", "VILLA ADELINA"],
        "provincia": "Buenos Aires",
    },
    "CABA": {
        "localidades": ["CABA", "CAPITAL FEDERAL", "CIUDAD AUTONOMA DE BUENOS AIRES",
                        "CIUDAD AUTÓNOMA DE BUENOS AIRES", "C.A.B.A.", "BUENOS AIRES"],
        "provincia": "CABA",
    },
}

# Provincias de interés para filtro geográfico
PROVINCIAS_INTERES = ["Buenos Aires", "BUENOS AIRES", "CABA",
                      "Ciudad Autónoma de Buenos Aires",
                      "CIUDAD AUTONOMA DE BUENOS AIRES"]
