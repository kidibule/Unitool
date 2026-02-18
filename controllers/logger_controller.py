"""LoggerController — gère l'archivage et import/export de dossiers."""

from datetime import datetime
from models import Target


class LoggerController:
    """Contrôleur pour l'archivage (INTEL ARCHIVE SYSTEM).

    Méthodes :
    - save_target : ajoute ou met à jour un dossier complet
    - load_target : charge un dossier existant
    - import_csv : importe des targets depuis CSV
    - export_csv : exporte les targets vers CSV
    """

    def __init__(self, app_controller):
        """Initialise le contrôleur logger avec le controller app principal.

        Args:
            app_controller: instance d'AppController pour accès à la DB
        """
        self.app = app_controller

    def save_target(
        self,
        pseudo: str,
        org: str = "",
        sid: str = "",
        org_rank: str = "",
        language: str = "",
        affiliates: str = "",
        alignment: str = "NEUTRE",
        ship: str = "",
        pvp_lvl: str = "",
        activity: str = "",
        notes: str = "",
        threat: str = "LOW",
        wins: int = 0,
        losses: int = 0,
    ) -> None:
        """Enregistre un dossier complet (insert ou update)."""
        sql = """
        INSERT INTO targets (pseudo, org, sid, org_rank, language, affiliates, alignment, 
                            ship, pvp_lvl, activity, notes, date, threat, wins, losses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(pseudo) DO UPDATE SET 
            org=excluded.org,
            sid=excluded.sid,
            org_rank=excluded.org_rank,
            language=excluded.language,
            affiliates=excluded.affiliates,
            alignment=excluded.alignment,
            ship=excluded.ship,
            pvp_lvl=excluded.pvp_lvl,
            activity=excluded.activity,
            notes=excluded.notes,
            date=excluded.date,
            threat=excluded.threat,
            wins=excluded.wins,
            losses=excluded.losses
        """
        params = (
            pseudo.upper(),
            org.upper(),
            sid.upper(),
            org_rank.upper(),
            language.upper(),
            affiliates.upper(),
            alignment,
            ship.upper(),
            pvp_lvl.upper(),
            activity.upper(),
            notes,
            datetime.now().strftime("%d/%m/%Y"),
            threat,
            wins,
            losses,
        )
        self.app.commit(sql, params)
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Saved dossier: {pseudo}", source="LOGGER")
        except Exception:
            pass

    def load_target(self, pseudo: str) -> list:
        """Récupère un dossier complet par pseudo."""
        return self.app.query("SELECT * FROM targets WHERE pseudo=?", (pseudo.upper(),))

    def load_target_as_model(self, pseudo: str) -> Target:
        """Récupère un dossier et retourne un objet Target."""
        row = self.app.query("SELECT * FROM targets WHERE pseudo=?", (pseudo.upper(),))
        if row:
            return Target.from_db_row(row[0])
        return None

    def import_targets_csv(self, rows: list) -> None:
        """Importe une liste de rows CSV dans la DB.

        Args:
            rows: liste de dict avec clés {pseudo, org, ship, threat, notes, alignment}
        """
        count = 0
        for row in rows:
            sql = """
            INSERT OR REPLACE INTO targets (pseudo, org, ship, threat, notes, alignment)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                row.get("pseudo", "").upper(),
                row.get("org", "").upper(),
                row.get("ship", "").upper(),
                row.get("threat", "LOW"),
                row.get("notes", ""),
                row.get("alignment", "NEUTRE"),
            )
            self.app.commit(sql, params)
            count += 1
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Imported {count} targets from CSV", source="LOGGER")
        except Exception:
            pass

    def export_targets_csv(self) -> list:
        """Récupère toutes les targets pour export CSV."""
        return self.app.query("SELECT * FROM targets")

    def clear_all_fields(self) -> None:
        """Utilitaire pour nettoyer (dans les vues)."""
        pass
