"""Tests unitaires pour les modèles Ship et Component."""

import pytest
from models.ship import Ship
from models.component import Component


class TestComponent:
    def test_init_normalise_en_majuscules(self):
        comp = Component(name="gladius laser", brand="ager", type_name="laser", category="weapon", size=2, grade="a")
        assert comp.name == "GLADIUS LASER"
        assert comp.brand == "AGER"
        assert comp.type_name == "LASER"
        assert comp.category == "WEAPON"
        assert comp.grade == "A"

    def test_valeurs_par_defaut(self):
        comp = Component(name="", brand=None, type_name=None, category=None, size=1, grade=None)
        assert comp.name == "UNKNOWN"
        assert comp.brand == "UNKNOWN"
        assert comp.type_name == "UNKNOWN"
        assert comp.category == "SYSTEMS"
        assert comp.grade == "C"

    def test_stats_par_defaut_vide(self):
        comp = Component(name="X", brand="Y", type_name="T", category="CAT", size=1, grade="B")
        # Les stats typées existent et valent 0 par défaut
        assert comp.stat_dps == 0.0
        assert comp.stat_shield_hp == 0
        assert comp.stat_power_output == 0.0

    def test_stats_personnalisees(self):
        comp = Component(name="X", brand="Y", type_name="T", category="CAT", size=1, grade="B", stat_dps=100.0)
        assert comp.stat_dps == 100.0

    def test_from_db_transforme_ligne(self):
        # from_db (legacy) : id, name, brand, type_name, category, size, grade, stats
        row = (1, "LASER", "RSI", "ENERGY", "WEAPON", 2, "A", "{}")
        comp = Component.from_db(row)
        assert comp.name == "LASER"
        assert comp.brand == "RSI"
        assert comp.category == "WEAPON"
        assert comp.size == 2

    def test_from_db_retourne_none_si_row_vide(self):
        assert Component.from_db(None) is None


class TestShip:
    def _make_ship(self, name="GLADIUS", brand="Aegis Dynamics"):
        return Ship(name=name, brand=brand)

    def test_init_normalise_nom_en_majuscule(self):
        ship = Ship(name="gladius", brand="aegis dynamics")
        assert ship.name == "GLADIUS"
        assert ship.brand == "AEGIS DYNAMICS"

    def test_valeurs_par_defaut(self):
        ship = self._make_ship()
        assert ship.crew_size == 0
        assert ship.hp == 0
        assert ship.components == []
        assert ship.capabilities == {}

    def test_set_capability(self):
        ship = self._make_ship()
        ship.set_capability("WEAPON", max_qty=4, max_size=3)
        assert ship.capabilities["WEAPON"]["max_qty"] == 4
        assert ship.capabilities["WEAPON"]["max_size"] == 3

    def test_can_add_component_sans_capability_refuse(self):
        ship = self._make_ship()
        comp = Component(name="LASER", brand="RSI", type_name="ENERGY", category="WEAPON", size=1, grade="A")
        ok, msg = ship.can_add_component(comp)
        assert ok is False
        assert "No [" in msg

    def test_can_add_component_taille_trop_grande_refuse(self):
        ship = self._make_ship()
        ship.set_capability("WEAPON", max_qty=4, max_size=2)
        comp = Component(name="BIG_GUN", brand="RSI", type_name="BALLISTIC", category="WEAPON", size=3, grade="A")
        ok, msg = ship.can_add_component(comp)
        assert ok is False
        assert "SIZE" in msg

    def test_can_add_component_valide(self):
        ship = self._make_ship()
        ship.set_capability("WEAPON", max_qty=4, max_size=3)
        comp = Component(name="LASER", brand="RSI", type_name="ENERGY", category="WEAPON", size=2, grade="A")
        ok, msg = ship.can_add_component(comp)
        assert ok is True

    def test_can_add_component_slots_pleins_refuse(self):
        ship = self._make_ship()
        ship.set_capability("WEAPON", max_qty=1, max_size=3)
        comp1 = Component(name="LASER1", brand="RSI", type_name="ENERGY", category="WEAPON", size=1, grade="A")
        comp2 = Component(name="LASER2", brand="RSI", type_name="ENERGY", category="WEAPON", size=1, grade="A")
        ship.add_component(comp1)
        ok, msg = ship.can_add_component(comp2)
        assert ok is False
        assert "SLOTS" in msg

    def test_add_component_accepte_composant_valide(self):
        ship = self._make_ship()
        ship.set_capability("WEAPON", max_qty=2, max_size=3)
        comp = Component(name="LASER", brand="RSI", type_name="ENERGY", category="WEAPON", size=1, grade="A")
        result = ship.add_component(comp)
        assert result is True
        assert len(ship.components) == 1

    def test_add_component_refuse_composant_invalide(self):
        ship = self._make_ship()
        comp = Component(name="LASER", brand="RSI", type_name="ENERGY", category="WEAPON", size=1, grade="A")
        result = ship.add_component(comp)
        assert result is False
        assert len(ship.components) == 0
