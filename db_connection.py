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

        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def query(self, sql: str, params: tuple = ()) -> list:
        """Exécute un SELECT et renvoie toutes les lignes."""
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def commit(self, sql: str, params: tuple = ()) -> None:
        """Exécute une requête d'écriture puis commit la transaction."""
        self.cursor.execute(sql, params)
        self.conn.commit()

    def execute(self, query: str, params: tuple = ()):
        """Raccourci pour exécuter et commiter rapidement."""
        result = self.cursor.execute(query, params)
        self.conn.commit()
        return result
