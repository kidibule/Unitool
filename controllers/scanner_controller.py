"""ScannerController — gère la recherche et édition de cibles."""

from models import Target


class ScannerController:
    """Contrôleur pour le scanner de cibles.

    Méthodes :
    - search_targets : recherche par pseudo, org, SID
    - update_target : met à jour une cible
    - export_targets : exporte les cibles en CSV
    """

    def __init__(self, app_controller):
        """Initialise le contrôleur scanner avec le controller app principal.

        Args:
            app_controller: instance d'AppController pour accès à la DB
        """
        self.app = app_controller

    def search_targets(self, query: str) -> list:
        """Cherche des cibles par pseudo, org ou SID."""
        if len(query) <= 1:
            return []
        
        sql = """
        SELECT pseudo, org, ship, alignment, pvp_lvl, activity, sid, enlisted_date, language 
        FROM targets 
        WHERE pseudo LIKE ? OR org LIKE ? OR sid LIKE ?
        """
        return self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))

    def search_targets_as_models(self, query: str) -> list:
        """Cherche des cibles et retourne des objets Target."""
        if len(query) <= 1:
            return []
        sql = "SELECT * FROM targets WHERE pseudo LIKE ? OR org LIKE ? OR sid LIKE ?"
        rows = self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [Target.from_db_row(row) for row in rows]

    def get_target_full(self, pseudo: str) -> list:
        """Récupère toutes les colonnes d'une cible."""
        sql = ("SELECT pseudo, org, ship, threat, notes, date, wins, losses, alignment, "
               "pvp_lvl, activity, sid, org_rank, enlisted_date, language "
               "FROM targets WHERE pseudo=?")
        return self.app.query(sql, (pseudo,))

    def update_target(
        self,
        pseudo: str,
        org: str = None,
        ship: str = None,
        alignment: str = None,
        notes: str = None,
        sid: str = None,
        pvp_lvl: str = None,
        activity: str = None,
        language: str = None,
        **kwargs,
    ) -> None:
        """Met à jour les infos d'une cible."""
        updates = []
        params = []

        fields = {
            "org": org,
            "ship": ship,
            "alignment": alignment,
            "notes": notes,
            "sid": sid,
            "pvp_lvl": pvp_lvl,
            "activity": activity,
            "language": language,
        }
        fields.update(kwargs)

        for key, value in fields.items():
            if value is not None:
                updates.append(f"{key}=?")
                params.append(value)

        if updates:
            params.append(pseudo)
            sql = f"UPDATE targets SET {', '.join(updates)} WHERE pseudo=?"
            self.app.commit(sql, tuple(params))

            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(pseudo.upper()) # Pour le WHERE pseudo = ?

            sql = f"UPDATE targets SET {set_clause} WHERE pseudo = ?"
    
    # Utilise self.app.execute ou self.app.query selon ta structure
        return self.app.query(sql, tuple(values))

    def export_targets_csv(self) -> list:
        """Récupère tous les targets pour export."""
        rows = self.app.query("SELECT * FROM targets")
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Exporting {len(rows)} targets to CSV", source="SCANNER")
        except Exception:
            pass
        return rows

def update_target(self, pseudo: str, **kwargs) -> None:
        """Met à jour les infos d'une cible avec validation des types."""
        
        # LISTE DES CHAMPS NUMÉRIQUES À PROTÉGER
        numeric_fields = ['wins', 'losses']
        
        cleaned_kwargs = {}
        for key, value in kwargs.items():
            if key in numeric_fields:
                try:
                    # On tente de convertir. Si ça échoue, on ignore ou on met 0
                    cleaned_kwargs[key] = int(value)
                except (ValueError, TypeError):
                    cleaned_kwargs[key] = 0
            else:
                cleaned_kwargs[key] = value

        # Utilisation des données nettoyées pour la suite du SQL
        if cleaned_kwargs:
            updates = [f"{key}=?" for key in cleaned_kwargs.keys()]
            params = list(cleaned_kwargs.values())
            params.append(pseudo.upper()) # Pour le WHERE

            sql = f"UPDATE targets SET {', '.join(updates)} WHERE pseudo=?"
            self.app.commit(sql, tuple(params))
