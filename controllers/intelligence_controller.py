"""IntelligenceController — gère le scraping et l'analyse de renseignements."""

from models import Target


class IntelligenceController:
    """Contrôleur pour le module INTELLIGENCE (scraping Selenium, analyse).

    Méthodes :
    - save_player_intel : enregistre les infos scraped d'un joueur
    - get_player_intel : récupère les infos locales d'un joueur
    - save_organization_members : enregistre les membres d'une org
    - get_organization_members : récupère les membres d'une org en local
    """

    def __init__(self, app_controller):
        """Initialise le contrôleur intelligence avec le controller app principal.

        Args:
            app_controller: instance d'AppController pour accès à la DB
        """
        self.app = app_controller

    def save_player_intel(self, data: dict) -> None:
        """Enregistre les infos récupérées par le bot Selenium."""
        self.app.upsert_target_intel(data)
        try:
            if hasattr(self.app, "log"):
                handle = data.get("Handle") or data.get("handle") or data.get("Handle")
                self.app.log(f"Player intel upserted: {handle}", source="INTEL")
        except Exception:
            pass

    def get_player_intel(self, handle: str) -> dict:
        """Récupère les infos locales d'un joueur pour preview."""
        return self.app.get_target_by_handle(handle)

    def update_player_intel(
        self,
        pseudo: str,
        org: str = None,
        sid: str = None,
        org_rank: str = None,
        enlisted_date: str = None,
        language: str = None,
        affiliates: str = None,
    ) -> None:
        """Met à jour les infos intel d'un joueur."""
        updates = []
        params = []

        fields = {
            "org": org,
            "sid": sid,
            "org_rank": org_rank,
            "enlisted_date": enlisted_date,
            "language": language,
            "affiliates": affiliates,
        }

        for key, value in fields.items():
            if value is not None:
                updates.append(f"{key}=?")
                params.append(value)

        if updates:
            params.append(pseudo.upper())
            sql = f"UPDATE targets SET {', '.join(updates)} WHERE pseudo=?"
            self.app.commit(sql, tuple(params))

    def get_all_targets(self) -> list:
        """Récupère tous les targets pour analyse."""
        return self.app.query("SELECT * FROM targets")

    def save_organization_roster(self, org_sid: str, members: list) -> None:
        """Bulk insert des membres d'une organisation.

        Args:
            org_sid: SID de l'organisation
            members: list de dict {handle, rank, ...}
        """
        count = 0
        for member in members:
            handle = member.get("handle", "").upper()
            rank = member.get("rank", "MEMBER")

            if handle and handle != "[REDACTED]":
                # Insérer ou mettre à jour
                sql = """
                INSERT INTO targets (pseudo, org, org_rank, date)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(pseudo) DO UPDATE SET
                    org=excluded.org,
                    org_rank=excluded.org_rank
                """
                params = (handle, org_sid, rank)
                self.app.commit(sql, params)
                count += 1
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Saved {count} members for org {org_sid}", source="INTEL")
        except Exception:
            pass
