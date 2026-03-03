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

    def get_target_comparison_row(self, pseudo: str):
        """Retourne les champs nécessaires pour vérifier les changements avant sauvegarde."""
        rows = self.app.query(
            """
            SELECT org, sid, org_rank, language, affiliates, alignment,
                   ship, pvp_lvl, activity, notes, threat, wins, losses
            FROM targets
            WHERE pseudo = ?
            """,
            (pseudo.upper(),),
        )
        return rows[0] if rows else None

    def load_target(self, pseudo: str) -> list:
        """Récupère un dossier complet par pseudo."""
        return self.app.query("SELECT * FROM targets WHERE pseudo=?", (pseudo.upper(),))

    def load_target_row(self, pseudo: str):
        rows = self.load_target(pseudo)
        return rows[0] if rows else None

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

    def save_organization(
        self,
        sid: str,
        name: str,
        tag: str = "",
        description: str = "",
        org_type: str = "ORGANIZATION",
        specialization: str = "GENERAL",
        allies: str = "",
        enemies: str = "",
        alignment: str = "NEUTRE",
        updated_at: str | None = None,
    ) -> None:
        sql = """
        INSERT INTO organizations (sid, name, tag, description, org_type, specialization, allies, enemies, alignment, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sid) DO UPDATE SET
            name=excluded.name,
            tag=excluded.tag,
            description=excluded.description,
            org_type=excluded.org_type,
            specialization=excluded.specialization,
            allies=excluded.allies,
            enemies=excluded.enemies,
            alignment=excluded.alignment,
            updated_at=excluded.updated_at
        """
        params = (
            sid.upper(),
            name,
            (tag or "").upper(),
            description,
            org_type,
            (specialization or "GENERAL").upper(),
            (allies or "").upper(),
            (enemies or "").upper(),
            alignment,
            updated_at or datetime.now().strftime("%d/%m/%Y"),
        )
        self.app.commit(sql, params)

    def import_organizations_csv(self, rows: list[dict]) -> int:
        count = 0
        sql = "INSERT OR REPLACE INTO organizations (sid, name, tag, alignment) VALUES (?,?,?,?)"
        for row in rows:
            sid = (row.get("sid") or "").upper().strip()
            if not sid:
                continue
            self.app.commit(
                sql,
                (
                    sid,
                    row.get("name", ""),
                    (row.get("tag") or "").upper(),
                    row.get("alignment", "NEUTRE"),
                ),
            )
            count += 1
        return count

    def export_organizations_csv(self) -> list:
        return self.app.query("SELECT sid, name, tag, alignment FROM organizations")

    def export_targets_csv(self) -> list:
        """Récupère toutes les targets pour export CSV."""
        return self.app.query("SELECT * FROM targets")

    def clear_all_fields(self) -> None:
        """Utilitaire pour nettoyer (dans les vues)."""
        pass
