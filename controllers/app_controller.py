"""AppController — contrôleur métier de l'application UNITOOL.

Gère la base de données, les opérations métier et sert d'intermédiaire
entre les vues (views) et la couche données (database).
"""

from database import Database
from .scanner_controller import ScannerController
from .logger_controller import LoggerController
from .contract_controller import ContractController
from .intelligence_controller import IntelligenceController


class AppController:
    """Contrôleur principal orchestre la logique métier.

    Responsabilités :
    - Gestion de la database
    - Instanciation des sub-controllers (Scanner, Logger, Contract, Intelligence)
    - Communication entre vues et données
    """

    def __init__(self, db_name: str = "unitool_data.db") -> None:
        """Initialise le contrôleur avec une instance de base de données.

        Args:
            db_name: Nom/chemin du fichier de base de données SQLite
        """
        self.db = Database(db_name)

        # Instanciation des sub-controllers
        self.scanner = ScannerController(self)
        self.logger = LoggerController(self)
        self.contract = ContractController(self)
        self.intelligence = IntelligenceController(self)

    # --- PROPRIÉTÉS DE COMPATIBILITÉ (accès direct à la DB pour les vues) ---

    @property
    def cursor(self):
        """Accès au curseur SQLite pour opérations brutes."""
        return self.db.cursor

    @property
    def conn(self):
        """Accès à la connexion SQLite pour opérations brutes."""
        return self.db.conn

    # --- MÉTHODES DÉLÉGUÉES À LA BASE DE DONNÉES ---

    def query(self, sql: str, params: tuple = ()):
        """Exécute une requête SELECT."""
        return self.db.query(sql, params)

    def commit(self, sql: str, params: tuple = ()):
        """Exécute une requête INSERT/UPDATE/DELETE."""
        self.db.commit(sql, params)

    def upsert_target_intel(self, data: dict) -> None:
        """Insère ou met à jour les infos récupérées par le bot."""
        self.db.upsert_target_intel(data)

    def get_target_by_handle(self, handle: str) -> dict:
        """Récupère les infos d'un joueur pour la preview."""
        return self.db.get_target_by_handle(handle)
