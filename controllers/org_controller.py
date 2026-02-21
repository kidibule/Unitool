"""OrgController — gère la logique métier des organisations."""

from models import Organization

class OrgController:
    """Contrôleur pour la gestion des organisations."""

    def __init__(self, app_controller):
        """Initialise avec l'instance AppController pour l'accès DB."""
        self.app = app_controller

    def search_orgs(self, query: str) -> list:
        """Recherche rapide pour affichage en liste/vue."""
        if len(query) < 2:
            return []
        
        # AJOUT : On récupère alignment et updated_at directement dans la recherche
        sql = """
        SELECT sid, name, tag, member_count, org_type, specialization, alignment, updated_at
        FROM organizations 
        WHERE sid LIKE ? OR name LIKE ? OR tag LIKE ?
        """
        return self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))

    def get_org_model(self, sid: str) -> Organization:
        """Récupère une organisation et retourne un objet Organization."""
        sql = "SELECT * FROM organizations WHERE sid = ?"
        row = self.app.query(sql, (sid.upper(),))
        if row:
            # Utilise la méthode from_db_row du modèle pour mapper proprement
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
            # On s'assure que alignment est en majuscule si présent
            elif key == "alignment" and value:
                cleaned_kwargs[key] = value.upper()
            elif value is not None:
                cleaned_kwargs[key] = value

        if cleaned_kwargs:
            updates = [f"{key}=?" for key in cleaned_kwargs.keys()]
            params = list(cleaned_kwargs.values())
            params.append(sid.upper()) # Clause WHERE

            sql = f"UPDATE organizations SET {', '.join(updates)} WHERE sid=?"
            self.app.commit(sql, tuple(params))
            
            if hasattr(self.app, "log"):
                self.app.log(f"Org {sid} mise à jour (Champs: {list(cleaned_kwargs.keys())})", source="ORG_CTRL")

    def get_diplomatic_report(self, sid: str) -> dict:
        """Génère un dictionnaire des relations pour la vue."""
        org = self.get_org_model(sid)
        if not org:
            return {}

        return {
            "alignment": org.alignment,
            "allies": org.allies.split(",") if org.allies and org.allies != "NONE" else [],
            "enemies": org.enemies.split(",") if org.enemies and org.enemies != "NONE" else [],
            "neutrals": org.neutrals.split(",") if org.neutrals and org.neutrals != "NONE" else []
        }
    
    def save_scanned_org(self, sid, name, **kwargs):
        """Méthode 'tout-en-un' pour le Scrapbot."""
        sid = sid.upper()
        if self.get_org_model(sid):
            self.update_org(sid, **kwargs)
        else:
            # Logique d'insertion si l'org n'existe pas
            cols = ["sid", "name"] + list(kwargs.keys())
            placeholders = ", ".join(["?"] * len(cols))
            vals = [sid, name] + list(kwargs.values())
            
            sql = f"INSERT INTO organizations ({', '.join(cols)}) VALUES ({placeholders})"
            self.app.commit(sql, tuple(vals))