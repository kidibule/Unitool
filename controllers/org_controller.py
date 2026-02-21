"""OrgController — gère la logique métier des organisations."""

from models import Organization


class OrgController:
    """Contrôleur pour la gestion des organisations.

    Méthodes :
    - search_orgs : recherche par nom, tag ou SID
    - get_org_model : récupère une instance d'Organization
    - update_org : mise à jour dynamique (diplomatie, membres, etc.)
    - get_diplomatic_report : analyse les relations alliés/ennemis
    """

    def __init__(self, app_controller):
        """Initialise avec l'instance AppController pour l'accès DB."""
        self.app = app_controller

    def search_orgs(self, query: str) -> list:
        """Recherche rapide pour affichage en liste/vue."""
        if len(query) < 2:
            return []
        
        sql = """
        SELECT sid, name, tag, member_count, org_type, specialization 
        FROM organizations 
        WHERE sid LIKE ? OR name LIKE ? OR tag LIKE ?
        """
        return self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))

    def get_org_model(self, sid: str) -> Organization:
        """Récupère une organisation et retourne un objet Organization."""
        sql = "SELECT * FROM organizations WHERE sid = ?"
        row = self.app.query(sql, (sid.upper(),))
        if row:
            return Organization.from_db_row(row[0])
        return None

    def update_org(self, sid: str, **kwargs) -> None:
        """Met à jour les informations d'une organisation avec protection des types."""
        
        # Champs numériques à valider
        numeric_fields = ['member_count']
        
        cleaned_kwargs = {}
        for key, value in kwargs.items():
            if key in numeric_fields:
                try:
                    cleaned_kwargs[key] = int(value)
                except (ValueError, TypeError):
                    cleaned_kwargs[key] = 0
            elif value is not None:
                cleaned_kwargs[key] = value

        if cleaned_kwargs:
            updates = [f"{key}=?" for key in cleaned_kwargs.keys()]
            params = list(cleaned_kwargs.values())
            params.append(sid.upper()) # Clause WHERE

            sql = f"UPDATE organizations SET {', '.join(updates)} WHERE sid=?"
            self.app.commit(sql, tuple(params))
            
            if hasattr(self.app, "log"):
                self.app.log(f"Org {sid} mise à jour", source="ORG_CTRL")

    def get_diplomatic_report(self, sid: str) -> dict:
        """Génère un dictionnaire des relations pour la vue."""
        org = self.get_org_model(sid)
        if not org:
            return {}

        return {
            "allies": org.allies.split(",") if org.allies != "NONE" else [],
            "enemies": org.enemies.split(",") if org.enemies != "NONE" else [],
            "neutrals": org.neutrals.split(",") if org.neutrals != "NONE" else []
        }

    def export_orgs_csv(self) -> list:
        """Récupère toutes les organisations pour l'export."""
        return self.app.query("SELECT * FROM organizations")
    
    def save_scanned_org(self, sid, name, **kwargs):
        """Méthode 'tout-en-un' pour le Scrapbot."""
        if self.get_org_model(sid):
            self.update_org(sid, **kwargs)
        else:
            # Logique d'insertion ici...
            pass