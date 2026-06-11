"""Tests unitaires pour controllers/ship_controller.py.

Le AppController et la DB sont mockés pour que les tests
restent rapides et sans effets de bord (pas de fichier DB créé).
"""

import pytest
from unittest.mock import MagicMock, call
from controllers.ship_controller import ShipController


def make_controller():
    """Crée un ShipController avec un AppController entièrement mocké."""
    app = MagicMock()
    app.query.return_value = []
    app.commit.return_value = None
    return ShipController(app)


class TestSafeInt:
    def setup_method(self):
        self.ctrl = make_controller()

    def test_convertit_entier(self):
        assert self.ctrl._safe_int(42) == 42

    def test_convertit_chaine_entiere(self):
        assert self.ctrl._safe_int("7") == 7

    def test_convertit_float_en_int(self):
        assert self.ctrl._safe_int("3.9") == 3

    def test_retourne_defaut_si_none(self):
        assert self.ctrl._safe_int(None) == 0

    def test_retourne_defaut_si_chaine_vide(self):
        assert self.ctrl._safe_int("") == 0

    def test_retourne_defaut_si_invalide(self):
        assert self.ctrl._safe_int("abc", default=99) == 99


class TestSafeFloat:
    def setup_method(self):
        self.ctrl = make_controller()

    def test_convertit_float(self):
        assert self.ctrl._safe_float(3.14) == 3.14

    def test_convertit_chaine_float(self):
        assert self.ctrl._safe_float("2.5") == 2.5

    def test_retourne_defaut_si_none(self):
        assert self.ctrl._safe_float(None) == 0.0

    def test_retourne_defaut_si_chaine_vide(self):
        assert self.ctrl._safe_float("") == 0.0

    def test_retourne_defaut_si_invalide(self):
        assert self.ctrl._safe_float("xyz", default=1.0) == 1.0


class TestIsGenericSubtype:
    def setup_method(self):
        self.ctrl = make_controller()

    def test_subtype_generic_retourne_true(self):
        assert self.ctrl._is_generic_subtype("SHIELD", "GENERIC") is True

    def test_category_weapon_retourne_toujours_true(self):
        # "GUN S3" → stripped = "GUN" → non vide et non GENERIC → False
        # seul un subtype vide ou "GENERIC" pur doit retourner True
        assert self.ctrl._is_generic_subtype("WEAPON", "GENERIC") is True
        assert self.ctrl._is_generic_subtype("WEAPON", "") is True

    def test_subtype_specifique_non_weapon_retourne_false(self):
        assert self.ctrl._is_generic_subtype("SHIELD", "BUBBLE") is False
        assert self.ctrl._is_generic_subtype("COOLER", "ACTIVE") is False

    def test_gere_valeurs_none(self):
        # None → traité comme GENERIC
        assert self.ctrl._is_generic_subtype("SHIELD", None) is True


class TestNormalizeProfile:
    def setup_method(self):
        self.ctrl = make_controller()

    def test_valeur_standard(self):
        assert self.ctrl._normalize_profile("combat") == "COMBAT"

    def test_none_retourne_default(self):
        assert self.ctrl._normalize_profile(None) == "DEFAULT"

    def test_chaine_vide_retourne_default(self):
        assert self.ctrl._normalize_profile("") == "DEFAULT"

    def test_strip_espaces(self):
        assert self.ctrl._normalize_profile("  ALPHA  ") == "ALPHA"


class TestListShipNames:
    def test_retourne_liste_de_noms(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = [("GLADIUS",), ("AURORA",)]
        result = ctrl.list_ship_names()
        assert result == ["GLADIUS", "AURORA"]

    def test_retourne_liste_vide(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = []
        assert ctrl.list_ship_names() == []


class TestSearchShipNames:
    def test_recherche_vide_retourne_vide(self):
        ctrl = make_controller()
        result = ctrl.search_ship_names("")
        assert result == []
        ctrl.app.query.assert_not_called()

    def test_recherche_retourne_correspondances(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = [("GLADIUS",)]
        result = ctrl.search_ship_names("glad")
        assert "GLADIUS" in result


class TestUpsertSubtypeSpec:
    def test_leve_erreur_si_parametres_invalides(self):
        ctrl = make_controller()
        with pytest.raises(ValueError):
            ctrl.upsert_subtype_spec("", "WEAPON", "GENERIC", 2, 3)

    def test_leve_erreur_si_qty_zero(self):
        ctrl = make_controller()
        with pytest.raises(ValueError):
            ctrl.upsert_subtype_spec("GLADIUS", "WEAPON", "GENERIC", 0, 3)

    def test_leve_erreur_si_size_zero(self):
        ctrl = make_controller()
        with pytest.raises(ValueError):
            ctrl.upsert_subtype_spec("GLADIUS", "WEAPON", "GENERIC", 2, 0)

    def test_appelle_commit_et_sync(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = []
        ctrl.upsert_subtype_spec("GLADIUS", "WEAPON", "GENERIC", 2, 3)
        assert ctrl.app.commit.called


class TestGetCompatibleComponents:
    def test_retourne_noms_de_composants(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = [("LASER_REPEATER",), ("DISTORTION_CANNON",)]
        result = ctrl.get_compatible_components("WEAPON", 3)
        assert result == ["LASER_REPEATER", "DISTORTION_CANNON"]

    def test_retourne_vide_si_aucun(self):
        ctrl = make_controller()
        ctrl.app.query.return_value = []
        assert ctrl.get_compatible_components("WEAPON", 1) == []
