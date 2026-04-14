"""Fonctions utilitaires pour le nettoyage et le parsing des données vaisseau."""

import re


def clean_number(value: str) -> str:
    """Supprime les espaces de séparation dans les nombres. Ex: '1 193' -> '1193'"""
    if not value:
        return value
    return re.sub(r'(?<=\d)\s+(?=\d)', '', value.strip())


def parse_triple(value: str):
    """Parse '68 / 52 / 200' -> ('68', '52', '200')"""
    parts = re.split(r'\s*/\s*', value.strip())
    if len(parts) == 3:
        return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return None, None, None


def parse_dimensions(value: str) -> str:
    """Normalise '17.5 x 21 x 5.5 m' -> '17.5 x 21 x 5.5'"""
    value = re.sub(r'\s*m$', '', value.strip(), flags=re.IGNORECASE)
    value = re.sub(r'\s*x\s*', ' x ', value)
    return value


def clean_time(value: str) -> str:
    """Corrige les erreurs OCR sur les timestamps. Ex: 'OO:O5:49' -> '00:05:49'"""
    value = value.replace('O', '0').replace('o', '0')
    value = value.replace('.', ':')
    return value.strip()


def extract_header(lines: list) -> tuple:
    """
    Extrait le nom et le fabricant depuis les premières lignes du texte OCR.
    Ligne 0 = nom du vaisseau (ex: 'GLADIUS')
    Ligne 1 = fabricant (ex: 'Aegis Dynamics')
    """
    name = lines[0].strip() if len(lines) > 0 else ""
    brand = lines[1].strip() if len(lines) > 1 else ""
    return name, brand
