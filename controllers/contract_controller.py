"""ContractController — gère les contrats et bounty board."""

from datetime import datetime
from models import Contract, ContractType
from models.contract import Contract 

class ContractController:
    """Contrôleur des contrats (création, clôture, statistiques, types)."""

    def __init__(self, app_controller):
        # Référence au contrôleur principal pour accès DB/logging
        self.app = app_controller

    # --- Gestion des Contrats ---

    def add_contract(self, target: str, client: str, reward: str, priority: str = "MEDIUM", contract_type: str = None) -> None:
        """Ajoute un contrat en statut OPEN avec horodatage courant."""
        sql = """
        INSERT INTO contracts (target, client, reward, date, status, priority, contract_type)
        VALUES (?, ?, ?, ?, 'OPEN', ?, ?)
        """
        params = (
            target.upper(),
            client.upper(),
            reward,
            datetime.now().strftime("%d/%m %H:%M"),
            priority,
            contract_type,
        )
        self.app.commit(sql, params)
        try:
            if hasattr(self.app, "notify_stats_changed"):
                self.app.notify_stats_changed()
        except Exception:
            pass
        if hasattr(self.app, "log"):
            self.app.log(f"CONTRACT REGISTERED: {target.upper()} PRIO: {priority}", source="DECK")

    def complete_contract(self, contract_id: int, target: str) -> None:
        """Ferme un contrat et met à jour la fiche cible (wins/auto-création)."""
        # Récupérer la récompense pour le log avant fermeture
        res = self.app.query("SELECT reward FROM contracts WHERE id=?", (contract_id,))
        reward_value = res[0][0] if res else "0"

        # Update statut et stats cible
        self.app.commit("UPDATE contracts SET status='CLOSED' WHERE id=?", (contract_id,))
        
        # Tentative d'update du pseudo, sinon création
        self.app.commit("UPDATE targets SET wins = wins + 1 WHERE pseudo=?", (target.upper(),))
        
        # On vérifie si on doit insérer la cible (si non existante)
        check = self.app.query("SELECT pseudo FROM targets WHERE pseudo=?", (target.upper(),))
        if not check:
            self.app.commit(
                "INSERT INTO targets (pseudo, wins, date, alignment) VALUES (?,?,?,'ENNEMI')",
                (target.upper(), 1, datetime.now().strftime("%d/%m/%y"))
            )

        try:
            if hasattr(self.app, "notify_stats_changed"):
                self.app.notify_stats_changed()
        except Exception:
            pass

        if hasattr(self.app, "log"):
            self.app.log(f"MISSION COMPLETE >> {target} | +{reward_value} aUEC", source="DECK")

    def delete_contract(self, contract_id: int) -> None:
        """Supprime définitivement un contrat de la base."""
        self.app.commit("DELETE FROM contracts WHERE id=?", (contract_id,))
        try:
            if hasattr(self.app, "notify_stats_changed"):
                self.app.notify_stats_changed()
        except Exception:
            pass
        if hasattr(self.app, "log"):
            self.app.log(f"TRANSACTION PURGED FROM LOGS (ID: {contract_id})", source="SYS")

    # --- Requêtes de Données ---

    def get_active_contracts_as_models(self):
        """Récupère tous les contrats OPEN et les transforme en objets Contract."""
        # On récupère les lignes brutes de la DB
        rows = self.app.query("SELECT * FROM contracts WHERE status = 'OPEN' ORDER BY date DESC")
        # On les transforme en objets via la méthode de classe du modèle
        return [Contract.from_db_row(row) for row in rows]

    def get_closed_contracts_as_models(self):
        """Récupère tous les contrats CLOSED et les transforme en objets Contract."""
        rows = self.app.query("SELECT * FROM contracts WHERE status = 'CLOSED' ORDER BY date DESC LIMIT 20")
        return [Contract.from_db_row(row) for row in rows]

    def get_total_gains(self):
        """Calcule la somme de toutes les récompenses des contrats fermés."""
        rows = self.app.query("SELECT reward FROM contracts WHERE status = 'CLOSED'")
        total = 0
        for row in rows:
            try:
                # On nettoie la chaîne (enlever points ou espaces) avant de convertir
                val = str(row[0]).replace(".", "").replace(" ", "")
                total += int(val)
            except (ValueError, TypeError):
                continue
        return total

    # --- Gestion des Types ---

    def get_contract_types(self) -> list:
        """Retourne la liste des types de contrats configurés."""
        return self.app.query("SELECT name, reward FROM contract_types")

    def add_contract_type(self, name: str, reward: str) -> bool:
        """Ajoute un type de contrat; retourne False si déjà existant."""
        try:
            self.app.commit("INSERT INTO contract_types VALUES (?, ?)", (name.upper(), reward))
            if hasattr(self.app, "log"):
                self.app.log(f"NEW CONTRACT TYPE: {name.upper()} ({reward} aUEC)", source="SYS")
            return True
        except:
            if hasattr(self.app, "log"):
                self.app.log(f"CONFIG ERROR: TYPE {name} ALREADY EXISTS", source="ERROR")
            return False

    def delete_contract_type(self, name: str) -> None:
        """Supprime un type de contrat existant."""
        self.app.commit("DELETE FROM contract_types WHERE name=?", (name.upper(),))
        if hasattr(self.app, "log"):
            self.app.log(f"CONTRACT TYPE DELETED: {name}", source="SYS")

    # --- Utilitaires ---

    def get_suggestions(self, text: str) -> list:
        """Fournit des suggestions de pseudos pour l'auto-complétion."""
        if not text: return []
        rows = self.app.query("SELECT pseudo FROM targets WHERE pseudo LIKE ? LIMIT 8", (text.upper() + '%',))
        return [r[0] for r in rows]
    
    def get_contract_reward_for_type(self, type_name: str) -> str:
        """Retourne la récompense par défaut associée à un type de contrat."""
        row = self.app.query("SELECT reward FROM contract_types WHERE name=?", (type_name,))
        return row[0][0] if row else "0"
    
    def get_contracts_for_target(self, pseudo: str) -> list:
        # Utilise COLLATE NOCASE pour ignorer les majuscules/minuscules
        sql = "SELECT * FROM contracts WHERE target = ? COLLATE NOCASE ORDER BY date DESC"
        return self.app.query(sql, (pseudo,))

    def get_contracts_for_client(self, pseudo: str) -> list:
        sql = "SELECT * FROM contracts WHERE client = ? COLLATE NOCASE ORDER BY date DESC"
        return self.app.query(sql, (pseudo,))