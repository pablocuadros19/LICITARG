"""Utilidades de formateo: CUIT, montos, fechas."""

import re


def normalizar_cuit(cuit) -> str:
    """Normaliza CUIT a formato 11 dígitos sin guiones.

    Acepta: '30-70703412-9', '30707034129', 30707034129, etc.
    Devuelve: '30707034129' o '' si no es válido.
    """
    if cuit is None:
        return ""
    cuit_str = str(cuit).strip()
    # Quitar guiones, puntos, espacios
    cuit_limpio = re.sub(r"[-.\s]", "", cuit_str)
    # Validar que sean 11 dígitos
    if re.match(r"^\d{11}$", cuit_limpio):
        return cuit_limpio
    return ""


def formatear_cuit(cuit: str) -> str:
    """Formatea CUIT para mostrar: 30-70703412-9."""
    cuit = normalizar_cuit(cuit)
    if len(cuit) != 11:
        return cuit
    return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"


def formatear_monto(monto, moneda: str = "ARS") -> str:
    """Formatea monto numérico para mostrar."""
    try:
        valor = float(monto)
    except (ValueError, TypeError):
        return str(monto)

    if valor >= 1_000_000_000:
        return f"${valor / 1_000_000_000:,.1f}B {moneda}"
    if valor >= 1_000_000:
        return f"${valor / 1_000_000:,.1f}M {moneda}"
    if valor >= 1_000:
        return f"${valor / 1_000:,.1f}K {moneda}"
    return f"${valor:,.0f} {moneda}"


def normalizar_provincia(provincia: str) -> str:
    """Normaliza nombre de provincia para comparación."""
    if not provincia:
        return ""
    p = provincia.strip().upper()
    # Mapeo de variantes comunes
    variantes = {
        "CABA": "CABA",
        "CAPITAL FEDERAL": "CABA",
        "C.A.B.A.": "CABA",
        "CIUDAD AUTONOMA DE BUENOS AIRES": "CABA",
        "CIUDAD AUTÓNOMA DE BUENOS AIRES": "CABA",
        "BUENOS AIRES": "BUENOS AIRES",
        "BS AS": "BUENOS AIRES",
        "BS. AS.": "BUENOS AIRES",
        "PCIA. DE BUENOS AIRES": "BUENOS AIRES",
        "PCIA DE BUENOS AIRES": "BUENOS AIRES",
    }
    return variantes.get(p, p)


def normalizar_localidad(localidad: str) -> str:
    """Normaliza localidad para comparación."""
    if not localidad:
        return ""
    loc = localidad.strip().upper()
    # Quitar prefijos comunes
    loc = re.sub(r"^(GRAL\.\s*|GENERAL\s+)", "GENERAL ", loc)
    loc = re.sub(r"^(SAN\s+)", "SAN ", loc)
    return loc.strip()
