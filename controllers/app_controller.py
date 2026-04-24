"""AppController — contrôleur métier de l'application UNITOOL.

Gère la base de données, les opérations métier et sert d'intermédiaire
entre les vues (views) et la couche données (database).
"""

from database import Database
from .scanner_controller import ScannerController
from .logger_controller import LoggerController
from .contract_controller import ContractController
from .intelligence_controller import IntelligenceController
from .ship_controller import ShipController
from .org_controller import OrgController
from .interception_controller import InterceptionController
import logging
import os


class AppController:
    """Contrôleur principal orchestre la logique métier.

    Responsabilités :
    - Gestion de la database
    - Instanciation des sub-controllers (Scanner, Logger, Contract, Intelligence)
    - Communication entre vues et données
    """

    def __init__(self, db_name: str = "unitool_data.db", reset_db_on_start: bool = False) -> None:
        """Initialise le contrôleur avec une instance de base de données.

        Args:
            db_name: Nom/chemin du fichier de base de données SQLite
        """
        self.db = Database(db_name, reset_on_start=reset_db_on_start)

        # Instanciation des sub-controllers
        self.scanner = ScannerController(self)
        self.logger = LoggerController(self)
        self.contract = ContractController(self)
        self.intelligence = IntelligenceController(self)
        self.ship = ShipController(self)
        self.org = OrgController(self)
        self.interception = InterceptionController(self)  
        # Setup python logger (file + console optional)
        log_path = os.path.join(os.getcwd(), "unitool.log")
        self._logger = logging.getLogger("unitool")
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        # Callback list for UI forwarding (register via register_log_callback)
        self._log_callbacks = []
        # Callback list for dashboard stats refresh in the main right panel
        self._stats_callbacks = []

    def register_log_callback(self, fn):
        """Register a callable to receive (message, source) for UI forwarding."""
        try:
            if callable(fn):
                self._log_callbacks.append(fn)
        except Exception:
            pass

    def unregister_log_callback(self, fn):
        """Unregister a previously registered log callback."""
        try:
            if fn in self._log_callbacks:
                self._log_callbacks.remove(fn)
        except Exception:
            pass

    def register_stats_callback(self, fn):
        """Register a callable used to refresh the right-side dashboard stats."""
        try:
            if callable(fn) and fn not in self._stats_callbacks:
                self._stats_callbacks.append(fn)
        except Exception:
            pass

    def unregister_stats_callback(self, fn):
        """Unregister a previously registered stats callback."""
        try:
            if fn in self._stats_callbacks:
                self._stats_callbacks.remove(fn)
        except Exception:
            pass

    def notify_stats_changed(self) -> None:
        """Notify UI listeners that dashboard counters must be refreshed."""
        try:
            for cb in list(self._stats_callbacks):
                try:
                    cb()
                except Exception:
                    pass
        except Exception:
            pass

    def log(self, message: str, source: str = "APP", level: str = "info") -> None:
        """Central logging API: writes to file and forwards to main view if present.

        Args:
            message: texte du log
            source: étiquette source (ex: INTEL, SCANNER)
            level: niveau ('info','warning','error')
        """
        try:
            txt = f"[{source}] {message}"
            if level.lower() == "warning":
                self._logger.warning(txt)
            elif level.lower() == "error":
                self._logger.error(txt)
            else:
                self._logger.info(txt)
        except Exception:
            pass

        # Previously certain sources (eg. SCANNER) were filtered here which
        # prevented UI forwarding. Keep forwarding for all sources so the
        # UI can display scanner logs and other messages.

        # Forward to registered callbacks (UI terminals)
        try:
            for cb in list(self._log_callbacks):
                try:
                    cb(message, source)
                except Exception:
                    pass
        except Exception:
            pass

        # Backwards-compat: also forward to controller.view if present
        # but avoid double-calling if the view's log handler is already registered
        try:
            if hasattr(self, "view") and getattr(self, "view"):
                try:
                    v_cb = getattr(self.view, "log_message")
                    if v_cb not in self._log_callbacks:
                        self.view.log_message(message, source=source)
                except Exception:
                    # If comparison fails for some reason, fall back to safe call
                    try:
                        self.view.log_message(message, source=source)
                    except Exception:
                        pass
        except Exception:
            pass

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
        self.db.targets.upsert_intel(data)

    def get_target_by_handle(self, handle: str) -> dict:
        """Récupère les infos d'un joueur pour la preview."""
        return self.db.targets.get_by_handle(handle)

    def get_dashboard_stats(self) -> dict:
        """Retourne les compteurs affichés dans le panneau intel principal."""
        try:
            targets_count = self.query("SELECT COUNT(*) FROM targets")
            active_contracts = self.query(
                "SELECT COUNT(*) FROM contracts WHERE status != 'CLOSED'"
            )
            organizations_count = self.query("SELECT COUNT(*) FROM organizations")

            return {
                "targets": int(targets_count[0][0]) if targets_count else 0,
                "active_contracts": int(active_contracts[0][0]) if active_contracts else 0,
                "organizations": int(organizations_count[0][0]) if organizations_count else 0,
            }
        except Exception:
            return {"targets": 0, "active_contracts": 0, "organizations": 0}
