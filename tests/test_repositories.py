"""Tests unitaires pour les repositories (target, org, location, ship)."""

import sqlite3
import pytest
from db_migrations import run_migrations
from repositories.player_repository import PlayerRepository
from repositories.org_repository import OrgRepository
from repositories.location_repository import LocationRepository
from repositories.ship_repository import ShipRepository


def make_db():
    """Crée une base en mémoire avec le schéma complet (via migrations)."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    run_migrations(conn, cursor)

    class FakeDB:
        pass

    db = FakeDB()
    db.conn = conn
    db.cursor = cursor

    def query(sql, params=()):
        cursor.execute(sql, params)
        return cursor.fetchall()

    def commit(sql, params=()):
        cursor.execute(sql, params)
        conn.commit()

    db.query = query
    db.commit = commit
    return db


# ===========================================================================
# TargetRepository
# ===========================================================================

class TestTargetRepositoryIntel:
    def test_upsert_intel_insere_nouvelle_target(self):
        repo = PlayerRepository(make_db())
        repo.upsert_intel({
            "Handle": "player1", "OrgaNom": "TEST_ORG", "SID": "SID001",
            "Affiliates": "NONE", "Rang": "MEMBER",
            "Date": "01/01/2024", "Language": "FR",
        })
        rows = repo._db.query("SELECT pseudo FROM players WHERE pseudo='PLAYER1'")
        assert len(rows) == 1

    def test_upsert_intel_met_a_jour_si_handle_existe_deja(self):
        repo = PlayerRepository(make_db())
        data = {
            "Handle": "player1", "OrgaNom": "ORG_A", "SID": "SID001",
            "Affiliates": "NONE", "Rang": "MEMBER",
            "Date": "01/01/2024", "Language": "FR",
        }
        repo.upsert_intel(data)
        data["OrgaNom"] = "ORG_B"
        repo.upsert_intel(data)
        rows = repo._db.query("SELECT org FROM players WHERE pseudo='PLAYER1'")
        assert rows[0][0] == "ORG_B"

    def test_get_by_handle_retourne_none_si_inconnu(self):
        repo = PlayerRepository(make_db())
        assert repo.get_by_handle("fantome") is None

    def test_get_by_handle_retourne_none_si_handle_vide(self):
        repo = PlayerRepository(make_db())
        assert repo.get_by_handle("") is None

    def test_get_by_handle_retourne_les_bonnes_donnees(self):
        repo = PlayerRepository(make_db())
        repo.upsert_intel({
            "Handle": "alice", "OrgaNom": "ALPHAORG", "SID": "ALP01",
            "Affiliates": "NONE", "Rang": "OFFICER",
            "Date": "02/02/2024", "Language": "EN",
        })
        result = repo.get_by_handle("alice")
        assert result is not None
        assert result["OrgaNom"] == "ALPHAORG"
        assert result["SID"] == "ALP01"
        assert result["Rang"] == "OFFICER"
        assert result["Language"] == "EN"


class TestTargetRepositoryNotes:
    def _make_target(self, db, handle="TESTUSER"):
        db.commit(
            "INSERT OR IGNORE INTO players (pseudo) VALUES (?)", (handle,)
        )

    def test_add_note_insere_une_note(self):
        db = make_db()
        repo = PlayerRepository(db)
        self._make_target(db)
        repo.add_note("TESTUSER", "note un")
        rows = db.query("SELECT note_text FROM player_notes WHERE player_pseudo='TESTUSER'")
        assert len(rows) == 1
        assert rows[0][0] == "note un"

    def test_add_note_ignore_si_texte_vide(self):
        db = make_db()
        repo = PlayerRepository(db)
        self._make_target(db)
        repo.add_note("TESTUSER", "  ")
        rows = db.query("SELECT * FROM player_notes WHERE player_pseudo='TESTUSER'")
        assert len(rows) == 0

    def test_get_notes_retourne_liste_vide_si_aucune(self):
        repo = PlayerRepository(make_db())
        assert repo.get_notes("INEXISTANT") == []

    def test_get_notes_ordre_descendant(self):
        db = make_db()
        repo = PlayerRepository(db)
        self._make_target(db)
        repo.add_note("TESTUSER", "note 1")
        repo.add_note("TESTUSER", "note 2")
        notes = repo.get_notes("TESTUSER")
        texts = [n[1] for n in notes]
        assert texts[0] == "note 2"
        assert texts[1] == "note 1"

    def test_update_note_modifie_le_texte(self):
        db = make_db()
        repo = PlayerRepository(db)
        self._make_target(db)
        repo.add_note("TESTUSER", "ancienne note")
        note_id = db.query(
            "SELECT id FROM player_notes WHERE player_pseudo='TESTUSER'"
        )[0][0]
        repo.update_note("TESTUSER", note_id, "nouvelle note")
        rows = db.query("SELECT note_text FROM player_notes WHERE id=?", (note_id,))
        assert rows[0][0] == "nouvelle note"

    def test_delete_note_supprime_la_note(self):
        db = make_db()
        repo = PlayerRepository(db)
        self._make_target(db)
        repo.add_note("TESTUSER", "a supprimer")
        note_id = db.query(
            "SELECT id FROM player_notes WHERE player_pseudo='TESTUSER'"
        )[0][0]
        repo.delete_note("TESTUSER", note_id)
        rows = db.query(
            "SELECT * FROM player_notes WHERE player_pseudo='TESTUSER'"
        )
        assert len(rows) == 0


class TestTargetRepositoryPlayerShips:
    def test_add_player_ship_insere(self):
        db = make_db()
        repo = PlayerRepository(db)
        repo.add_player_ship("ALICE", "AURORA")
        rows = db.query("SELECT ship FROM player_ships WHERE pseudo='ALICE'")
        assert rows[0][0] == "AURORA"

    def test_get_player_ships_retourne_liste_vide_si_aucun(self):
        repo = PlayerRepository(make_db())
        assert repo.get_player_ships("INCONNU") == []

    def test_get_player_ships_retourne_les_ships(self):
        db = make_db()
        repo = PlayerRepository(db)
        repo.add_player_ship("BOB", "AURORA")
        repo.add_player_ship("BOB", "CUTLASS")
        ships = repo.get_player_ships("BOB")
        assert "AURORA" in ships
        assert "CUTLASS" in ships

    def test_delete_player_ship_supprime_un_ship_specifique(self):
        db = make_db()
        repo = PlayerRepository(db)
        repo.add_player_ship("CHARLIE", "AURORA")
        repo.add_player_ship("CHARLIE", "CUTLASS")
        repo.delete_player_ship("CHARLIE", "AURORA")
        ships = repo.get_player_ships("CHARLIE")
        assert "AURORA" not in ships
        assert "CUTLASS" in ships

    def test_delete_all_player_ships_vide_tous_les_ships(self):
        db = make_db()
        repo = PlayerRepository(db)
        repo.add_player_ship("DAVE", "AURORA")
        repo.add_player_ship("DAVE", "CUTLASS")
        repo.delete_all_player_ships("DAVE")
        assert repo.get_player_ships("DAVE") == []


# ===========================================================================
# OrgRepository
# ===========================================================================

class TestOrgRepository:
    def _make_org(self, db, sid="ORG1"):
        db.commit(
            "INSERT OR IGNORE INTO organizations (sid, name) VALUES (?, ?)",
            (sid, "Test Org"),
        )

    def test_add_note_insere_une_note(self):
        db = make_db()
        repo = OrgRepository(db)
        self._make_org(db)
        repo.add_note("ORG1", "note org")
        rows = db.query("SELECT note_text FROM org_notes WHERE org_sid='ORG1'")
        assert rows[0][0] == "note org"

    def test_add_note_ignore_si_texte_vide(self):
        db = make_db()
        repo = OrgRepository(db)
        self._make_org(db)
        repo.add_note("ORG1", "")
        rows = db.query("SELECT * FROM org_notes WHERE org_sid='ORG1'")
        assert len(rows) == 0

    def test_get_notes_retourne_liste_vide_si_aucune(self):
        repo = OrgRepository(make_db())
        assert repo.get_notes("INCONNUE") == []

    def test_get_notes_ordre_descendant(self):
        db = make_db()
        repo = OrgRepository(db)
        self._make_org(db)
        repo.add_note("ORG1", "premiere")
        repo.add_note("ORG1", "deuxieme")
        notes = repo.get_notes("ORG1")
        texts = [n[1] for n in notes]
        assert texts[0] == "deuxieme"

    def test_update_note_modifie_le_texte(self):
        db = make_db()
        repo = OrgRepository(db)
        self._make_org(db)
        repo.add_note("ORG1", "old")
        note_id = db.query("SELECT id FROM org_notes WHERE org_sid='ORG1'")[0][0]
        repo.update_note("ORG1", note_id, "new")
        rows = db.query("SELECT note_text FROM org_notes WHERE id=?", (note_id,))
        assert rows[0][0] == "new"

    def test_delete_note_supprime_la_note(self):
        db = make_db()
        repo = OrgRepository(db)
        self._make_org(db)
        repo.add_note("ORG1", "a effacer")
        note_id = db.query("SELECT id FROM org_notes WHERE org_sid='ORG1'")[0][0]
        repo.delete_note("ORG1", note_id)
        rows = db.query("SELECT * FROM org_notes WHERE org_sid='ORG1'")
        assert len(rows) == 0

    def test_add_event_insere_un_evenement(self):
        db = make_db()
        repo = OrgRepository(db)

        repo.add_event("2026-06-08", "21:30", "Briefing", "Point tactique", "Discord", "ALPHA, BRAVO")

        rows = db.query(
            "SELECT date, time, title, description, location, participants FROM org_events"
        )
        assert len(rows) == 1
        assert rows[0] == (
            "2026-06-08",
            "21:30",
            "Briefing",
            "Point tactique",
            "Discord",
            "ALPHA, BRAVO",
        )

    def test_update_event_modifie_les_champs(self):
        db = make_db()
        repo = OrgRepository(db)
        repo.add_event("2026-06-08", "20:00", "Avant", "desc", "lieu", "P1")
        evt_id = db.query("SELECT id FROM org_events LIMIT 1")[0][0]

        repo.update_event(evt_id, "Apres", "22:45", "nouvelle desc", "Pyro", "P2, P3")

        rows = db.query(
            "SELECT title, time, description, location, participants FROM org_events WHERE id=?",
            (evt_id,),
        )
        assert rows[0] == ("Apres", "22:45", "nouvelle desc", "Pyro", "P2, P3")

    def test_delete_event_supprime_l_entree(self):
        db = make_db()
        repo = OrgRepository(db)
        repo.add_event("2026-06-08", "", "A supprimer", "", "", "")
        evt_id = db.query("SELECT id FROM org_events LIMIT 1")[0][0]

        repo.delete_event(evt_id)

        rows = db.query("SELECT id FROM org_events WHERE id=?", (evt_id,))
        assert rows == []


# ===========================================================================
# LocationRepository
# ===========================================================================

class TestLocationRepository:
    def test_get_all_names_pre_rempli_au_depart(self):
        repo = LocationRepository(make_db())
        names = repo.get_all_names()
        # Les migrations pré-remplissent 16 lieux (4 planètes + 12 lunes)
        assert len(names) == 16
        assert "HURSTON" in names
        assert "ABERDEEN" in names
        assert "CLIO" in names

    def test_upsert_insere_un_lieu(self):
        db = make_db()
        repo = LocationRepository(db)
        repo.upsert("HURSTON", 1.0, 2.0, 3.0, "PLANET")
        names = repo.get_all_names()
        assert "HURSTON" in names

    def test_upsert_met_a_jour_les_coordonnees(self):
        db = make_db()
        repo = LocationRepository(db)
        repo.upsert("HURSTON", 1.0, 2.0, 3.0, "PLANET")
        repo.upsert("HURSTON", 9.9, 8.8, 7.7, "PLANET")
        rows = db.query("SELECT x FROM locations WHERE name='HURSTON'")
        assert rows[0][0] == 9.9

    def test_get_all_names_ordre_alphabetique(self):
        db = make_db()
        repo = LocationRepository(db)
        repo.upsert("MICROTECH", 0.0, 0.0, 0.0)
        repo.upsert("ABERDEEN", 0.0, 0.0, 0.0)
        repo.upsert("CRUSADER", 0.0, 0.0, 0.0)
        names = repo.get_all_names()
        assert names == sorted(names)


# ===========================================================================
# ShipRepository
# ===========================================================================

class TestShipRepository:
    def test_add_component_type_insere(self):
        db = make_db()
        repo = ShipRepository(db)
        repo.add_component_type("SHIELD", "DEFENSE")
        rows = db.query("SELECT category FROM component_types WHERE name='SHIELD'")
        assert rows[0][0] == "DEFENSE"

    def test_add_component_type_ignore_les_doublons(self):
        db = make_db()
        repo = ShipRepository(db)
        repo.add_component_type("SHIELD", "DEFENSE")
        repo.add_component_type("SHIELD", "DEFENSE")
        rows = db.query("SELECT COUNT(*) FROM component_types WHERE name='SHIELD'")
        assert rows[0][0] == 1

    def test_add_component_insere(self):
        db = make_db()
        repo = ShipRepository(db)
        repo.add_component_type("RADAR", "AVIONICS")
        repo.add_component("TORRI", "LIGHTNING", "RADAR", "AVIONICS", 2, "A")
        rows = db.query("SELECT brand FROM components WHERE name='TORRI'")
        assert rows[0][0] == "LIGHTNING"

    def test_equip_component_associe_au_vaisseau(self):
        db = make_db()
        repo = ShipRepository(db)
        repo.add_component_type("SHIELD", "DEFENSE")
        repo.add_component("SHIELD_X1", "BEHR", "SHIELD", "DEFENSE", 1, "C")
        repo.equip_component("AURORA MR", "SHIELD_X1", 1)
        rows = db.query(
            "SELECT component_name FROM ship_loadout WHERE ship_name='AURORA MR'"
        )
        assert rows[0][0] == "SHIELD_X1"

    def test_get_ship_components_retourne_les_composants(self):
        db = make_db()
        repo = ShipRepository(db)
        repo.add_component_type("SHIELD", "DEFENSE")
        repo.add_component("SHIELD_X1", "BEHR", "SHIELD", "DEFENSE", 1, "C")
        repo.equip_component("AURORA MR", "SHIELD_X1", 1)
        components = repo.get_ship_components("AURORA MR")
        assert len(components) >= 1

    def test_get_ship_components_retourne_vide_si_aucun(self):
        repo = ShipRepository(make_db())
        assert repo.get_ship_components("GHOST SHIP") == []
