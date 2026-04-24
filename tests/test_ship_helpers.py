"""Tests unitaires pour services/ship_helpers.py."""

import pytest
from services.ship_helpers import clean_number, parse_triple, parse_dimensions, clean_time, extract_header


class TestCleanNumber:
    def test_supprime_espaces_entre_chiffres(self):
        assert clean_number("1 193") == "1193"

    def test_supprime_plusieurs_espaces(self):
        assert clean_number("1 000 000") == "1000000"

    def test_ne_touche_pas_chaine_sans_espace(self):
        assert clean_number("1193") == "1193"

    def test_retourne_vide_si_vide(self):
        assert clean_number("") == ""

    def test_retourne_none_si_none(self):
        assert clean_number(None) is None

    def test_strip_les_espaces_en_debut_fin(self):
        assert clean_number("  1 234  ") == "1234"


class TestParseTriple:
    def test_parse_triplet_standard(self):
        assert parse_triple("68 / 52 / 200") == ("68", "52", "200")

    def test_parse_sans_espaces(self):
        assert parse_triple("68/52/200") == ("68", "52", "200")

    def test_retourne_none_si_pas_trois_parties(self):
        assert parse_triple("68 / 52") == (None, None, None)

    def test_retourne_none_si_une_seule_valeur(self):
        assert parse_triple("68") == (None, None, None)

    def test_parse_avec_decimales(self):
        r1, r2, r3 = parse_triple("1.5 / 2.0 / 3.7")
        assert r1 == "1.5"
        assert r2 == "2.0"
        assert r3 == "3.7"


class TestParseDimensions:
    def test_supprime_suffixe_m(self):
        assert parse_dimensions("17.5 x 21 x 5.5 m") == "17.5 x 21 x 5.5"

    def test_normalise_espaces_autour_x(self):
        assert parse_dimensions("17.5x21x5.5") == "17.5 x 21 x 5.5"

    def test_supprime_m_majuscule(self):
        assert parse_dimensions("10 x 20 x 5 M") == "10 x 20 x 5"

    def test_deja_propre(self):
        assert parse_dimensions("10 x 20 x 5") == "10 x 20 x 5"


class TestCleanTime:
    def test_remplace_O_majuscule_par_zero(self):
        assert clean_time("OO:O5:49") == "00:05:49"

    def test_remplace_o_minuscule_par_zero(self):
        assert clean_time("oo:o5:49") == "00:05:49"

    def test_remplace_points_par_deux_points(self):
        assert clean_time("00.05.49") == "00:05:49"

    def test_strip(self):
        assert clean_time("  00:05:49  ") == "00:05:49"

    def test_chaine_propre(self):
        assert clean_time("12:34:56") == "12:34:56"


class TestExtractHeader:
    def test_extrait_nom_et_fabricant(self):
        name, brand = extract_header(["GLADIUS", "Aegis Dynamics"])
        assert name == "GLADIUS"
        assert brand == "Aegis Dynamics"

    def test_retourne_vide_si_liste_vide(self):
        name, brand = extract_header([])
        assert name == ""
        assert brand == ""

    def test_retourne_brand_vide_si_une_seule_ligne(self):
        name, brand = extract_header(["AURORA"])
        assert name == "AURORA"
        assert brand == ""

    def test_strip_des_espaces(self):
        name, brand = extract_header(["  GLADIUS  ", "  Aegis Dynamics  "])
        assert name == "GLADIUS"
        assert brand == "Aegis Dynamics"
