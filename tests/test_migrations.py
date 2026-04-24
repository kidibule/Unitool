"""Tests unitaires pour db_migrations.py."""

import sqlite3
import pytest
from db_migrations import (
    _get_version,
    _set_version,
    _column_exists,
    _add_column_if_missing,
    run_migrations,
    MIGRATIONS,
)


def make_db():
    """Crée une base SQLite en mémoire avec connexion et curseur."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    return conn, cursor


class TestGetSetVersion:
    def test_retourne_zero_si_table_absente(self):
        conn, cursor = make_db()
        assert _get_version(cursor) == 0

    def test_cree_la_table_schema_version(self):
        conn, cursor = make_db()
        _get_version(cursor)
        tables = [r[0] for r in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        assert "schema_version" in tables

    def test_set_puis_get_version(self):
        conn, cursor = make_db()
        _get_version(cursor)  # crée la table
        _set_version(cursor, 3)
        assert _get_version(cursor) == 3

    def test_set_ecrase_la_version_precedente(self):
        conn, cursor = make_db()
        _get_version(cursor)
        _set_version(cursor, 2)
        _set_version(cursor, 5)
        assert _get_version(cursor) == 5

    def test_un_seul_enregistrement_dans_la_table(self):
        conn, cursor = make_db()
        _get_version(cursor)
        _set_version(cursor, 1)
        _set_version(cursor, 2)
        count = cursor.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
        assert count == 1


class TestColumnExists:
    def test_retourne_true_si_colonne_existe(self):
        conn, cursor = make_db()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        assert _column_exists(cursor, "test", "name") is True

    def test_retourne_false_si_colonne_absente(self):
        conn, cursor = make_db()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        assert _column_exists(cursor, "test", "email") is False


class TestAddColumnIfMissing:
    def test_ajoute_colonne_absente(self):
        conn, cursor = make_db()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        _add_column_if_missing(cursor, "test", "name", "TEXT")
        assert _column_exists(cursor, "test", "name") is True

    def test_ne_plante_pas_si_colonne_deja_presente(self):
        conn, cursor = make_db()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        # Ne doit pas lever d'exception
        _add_column_if_missing(cursor, "test", "name", "TEXT")
        assert _column_exists(cursor, "test", "name") is True


class TestRunMigrations:
    def test_applique_toutes_les_migrations_sur_base_vide(self):
        conn, cursor = make_db()
        run_migrations(conn, cursor)
        version = _get_version(cursor)
        assert version == MIGRATIONS[-1][0]

    def test_base_apres_migration_contient_les_tables_cles(self):
        conn, cursor = make_db()
        run_migrations(conn, cursor)
        tables = {
            r[0]
            for r in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected in ["targets", "ships", "components", "ship_loadout",
                         "organizations", "locations", "schema_version"]:
            assert expected in tables, f"Table manquante : {expected}"

    def test_idempotent_relancer_ne_change_pas_la_version(self):
        conn, cursor = make_db()
        run_migrations(conn, cursor)
        version_apres_premier = _get_version(cursor)
        run_migrations(conn, cursor)
        assert _get_version(cursor) == version_apres_premier

    def test_reprend_a_partir_de_la_bonne_version(self):
        conn, cursor = make_db()
        # Simule une base partiellement migrée (migrations 1-3 déjà appliquées)
        run_migrations(conn, cursor)
        _set_version(cursor, 3)
        conn.commit()
        # Relancer ne doit pas crasher et doit arriver à la version finale
        run_migrations(conn, cursor)
        assert _get_version(cursor) == MIGRATIONS[-1][0]

    def test_targets_a_toutes_les_colonnes_apres_migration(self):
        conn, cursor = make_db()
        run_migrations(conn, cursor)
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(targets)").fetchall()]
        for col in ["pseudo", "pvp_lvl", "activity", "sid", "org_rank",
                    "enlisted_date", "language", "affiliates"]:
            assert col in cols, f"Colonne manquante dans targets : {col}"

    def test_ship_loadout_a_la_bonne_cle_primaire(self):
        conn, cursor = make_db()
        run_migrations(conn, cursor)
        pk_cols = [
            r[1]
            for r in cursor.execute("PRAGMA table_info(ship_loadout)").fetchall()
            if r[5] > 0
        ]
        assert pk_cols == ["ship_name", "profile_name", "category", "subtype_name", "slot_number"]
