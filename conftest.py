"""conftest.py — Ajoute la racine du projet au sys.path pour pytest.

Permet aux tests dans tests/ d'importer les modules racine
(database, db_connection, db_migrations, repositories, etc.)
sans avoir besoin d'un package installé.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
