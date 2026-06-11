"""Couche de connexion SQLite — responsabilité unique.

Ce module ne fait qu'une seule chose : ouvrir et gérer la connexion
à la base de données SQLite, et exposer les deux méthodes fondamentales
query() et commit().

Toute la logique métier (schéma, migrations, opérations) reste dans database.py.
"""

import sqlite3
import os


class DBConnection:
    """Gestion de la connexion SQLite.

    Responsabilités :
    - Ouvrir (et optionnellement réinitialiser) le fichier .db
    - Exposer query() pour les SELECT
    - Exposer commit() pour les INSERT/UPDATE/DELETE
    - Exposer execute() pour les opérations bas niveau (migrations, PRAGMA)
    """

    def __init__(self, db_name: str = "unitool_data.db", reset_on_start: bool = False):
        if reset_on_start and os.path.exists(db_name):
            os.remove(db_name)

        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._lock = __import__("threading").Lock()

    def query(self, sql: str, params: tuple = ()) -> list:
        """Exécute un SELECT et renvoie toutes les lignes."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    def commit(self, sql: str, params: tuple = ()) -> None:
        """Exécute une requête d'écriture puis commit la transaction."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.conn.commit()

    def execute(self, query: str, params: tuple = ()):
        """Raccourci pour exécuter et commiter rapidement."""
        with self._lock:
            cur = self.conn.cursor()
            result = cur.execute(query, params)
            self.conn.commit()
            return result
