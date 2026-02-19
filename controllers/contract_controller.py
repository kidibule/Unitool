# """ContractController — gère les contrats et bounty board."""

# from datetime import datetime
# from models import Contract, ContractType


# class ContractController:
#     """Contrôleur pour les contrats (BOUNTY BOARD).

#     Méthodes :
#     - add_contract : crée un nouveau contrat
#     - get_active_contracts : liste les contrats actifs
#     - get_closed_contracts : liste les contrats complétés
#     - complete_contract : marque un contrat comme fermé
#     - delete_contract : supprime un contrat
#     - get_contract_types : liste les types disponibles
#     - add_contract_type : crée un nouveau type
#     - delete_contract_type : supprime un type
#     """

#     def __init__(self, app_controller):
#         """Initialise le contrôleur contrat avec le controller app principal.

#         Args:
#             app_controller: instance d'AppController pour accès à la DB
#         """
#         self.app = app_controller

#     def add_contract(
#         self,
#         target: str,
#         client: str,
#         reward: str,
#         priority: str = "MEDIUM",
#         contract_type: str = None,
#     ) -> None:
#         """Ajoute un nouveau contrat."""
#         sql = """
#         INSERT INTO contracts (target, client, reward, date, status, priority, contract_type)
#         VALUES (?, ?, ?, ?, 'OPEN', ?, ?)
#         """
#         params = (
#             target.upper(),
#             client.upper(),
#             reward,
#             datetime.now().strftime("%d/%m %H:%M"),
#             priority,
#             contract_type,
#         )
#         try:
#             self.app.commit(sql, params)
#             if hasattr(self.app, "log"):
#                 self.app.log(f"New contract: {target} (prio={priority})", source="CONTRACT")
#         except Exception:
#             pass

#     def get_active_contracts(self) -> list:
#         """Retourne tous les contrats actifs (OPEN)."""
#         return self.app.query(
#             "SELECT * FROM contracts WHERE status='OPEN' ORDER BY id DESC"
#         )

#     def get_active_contracts_as_models(self) -> list:
#         """Retourne tous les contrats actifs sous forme d'objets Contract."""
#         rows = self.get_active_contracts()
#         return [Contract.from_db_row(row) for row in rows]

#     def get_closed_contracts(self) -> list:
#         """Retourne tous les contrats fermés (CLOSED)."""
#         return self.app.query(
#             "SELECT * FROM contracts WHERE status='CLOSED' ORDER BY id DESC"
#         )

#     def get_closed_contracts_as_models(self) -> list:
#         """Retourne tous les contrats fermés sous forme d'objets Contract."""
#         rows = self.get_closed_contracts()
#         return [Contract.from_db_row(row) for row in rows]

#     def complete_contract(self, contract_id: int, target: str) -> None:
#         """Marque un contrat comme fermé et incrémente les wins de la cible."""
#         self.app.commit(
#             "UPDATE contracts SET status='CLOSED' WHERE id=?", (contract_id,)
#         )
#         # Incrémenter les wins
#         self.app.commit(
#             "UPDATE targets SET wins = wins + 1 WHERE pseudo=?", (target.upper(),)
#         )
#         try:
#             if hasattr(self.app, "log"):
#                 self.app.log(f"Contract completed: {contract_id} for {target}", source="CONTRACT")
#         except Exception:
#             pass

#     def delete_contract(self, contract_id: int) -> None:
#         """Supprime un contrat de l'historique."""
#         try:
#             self.app.commit("DELETE FROM contracts WHERE id=?", (contract_id,))
#             if hasattr(self.app, "log"):
#                 self.app.log(f"Contract deleted: {contract_id}", source="CONTRACT")
#         except Exception:
#             pass

#     def get_contract_types(self) -> list:
#         """Récupère tous les types de contrats."""
#         return self.app.query("SELECT name, reward FROM contract_types")

#     def add_contract_type(self, name: str, reward: str) -> None:
#         """Ajoute un nouveau type de contrat."""
#         self.app.commit(
#             "INSERT INTO contract_types VALUES (?, ?)", (name.upper(), reward)
#         )
#         try:
#             if hasattr(self.app, "log"):
#                 self.app.log(f"Contract type added: {name} ({reward})", source="CONTRACT")
#         except Exception:
#             pass

#     def delete_contract_type(self, name: str) -> None:
#         """Supprime un type de contrat."""
#         try:
#             self.app.commit("DELETE FROM contract_types WHERE name=?", (name.upper(),))
#             if hasattr(self.app, "log"):
#                 self.app.log(f"Contract type removed: {name}", source="CONTRACT")
#         except Exception:
#             pass

#     def get_contract_reward_for_type(self, contract_type: str) -> str:
#         """Récupère la récompense d'un type de contrat."""
#         result = self.app.query(
#             "SELECT reward FROM contract_types WHERE name=?", (contract_type,)
#         )
#         return result[0][0] if result else None

#     def get_contracts_for_target(self, target: str) -> list:
#         """Retourne tous les contrats (ouverts et fermés) pour une cible donnée."""
#         return self.app.query(
#             "SELECT * FROM contracts WHERE target=? ORDER BY id DESC", (target.upper(),)
#         )

#     def get_contracts_for_target_as_models(self, target: str) -> list:
#         """Retourne les contrats d'une cible sous forme d'objets Contract."""
#         rows = self.get_contracts_for_target(target)
#         return [Contract.from_db_row(row) for row in rows]

#     def get_contracts_for_client(self, client: str) -> list:
#         """Retourne tous les contrats où le `client` est l'auteur (target may differ)."""
#         return self.app.query(
#             "SELECT * FROM contracts WHERE client=? ORDER BY id DESC", (client.upper(),)
#         )

#     def get_contracts_for_client_as_models(self, client: str) -> list:
#         """Retourne les contrats d'un client sous forme d'objets Contract."""
#         rows = self.get_contracts_for_client(client)
#         return [Contract.from_db_row(row) for row in rows]


"""ContractController — gère les contrats et bounty board."""

from datetime import datetime
from models import Contract, ContractType
from models.contract import Contract 

class ContractController:
    def __init__(self, app_controller):
        self.app = app_controller

    # --- Gestion des Contrats ---

    def add_contract(self, target: str, client: str, reward: str, priority: str = "MEDIUM", contract_type: str = None) -> None:
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
        if hasattr(self.app, "log"):
            self.app.log(f"CONTRACT REGISTERED: {target.upper()} | PRIO: {priority}", source="DECK")

    def complete_contract(self, contract_id: int, target: str) -> None:
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

        if hasattr(self.app, "log"):
            self.app.log(f"MISSION ACCOMPLISHED >> {target} | +{reward_value} aUEC", source="FINANCE")

    def delete_contract(self, contract_id: int) -> None:
        self.app.commit("DELETE FROM contracts WHERE id=?", (contract_id,))
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
        return self.app.query("SELECT name, reward FROM contract_types")

    def add_contract_type(self, name: str, reward: str) -> bool:
        try:
            self.app.commit("INSERT INTO contract_types VALUES (?, ?)", (name.upper(), reward))
            if hasattr(self.app, "log"):
                self.app.log(f"NEW CONTRACT TYPE: {name.upper()} ({reward} aUEC)", source="SYS_CFG")
            return True
        except:
            if hasattr(self.app, "log"):
                self.app.log(f"CONFIG ERROR: TYPE {name} ALREADY EXISTS", source="ERROR")
            return False

    def delete_contract_type(self, name: str) -> None:
        self.app.commit("DELETE FROM contract_types WHERE name=?", (name.upper(),))
        if hasattr(self.app, "log"):
            self.app.log(f"CONTRACT TYPE DELETED: {name}", source="SYS_CFG")

    # --- Utilitaires ---

    def get_suggestions(self, text: str) -> list:
        if not text: return []
        rows = self.app.query("SELECT pseudo FROM targets WHERE pseudo LIKE ? LIMIT 8", (text.upper() + '%',))
        return [r[0] for r in rows]
    
    def get_contract_reward_for_type(self, type_name: str) -> str:
        row = self.app.query("SELECT reward FROM contract_types WHERE name=?", (type_name,))
        return row[0][0] if row else "0"
    
    def get_contracts_for_target(self, pseudo: str) -> list:
        # Utilise COLLATE NOCASE pour ignorer les majuscules/minuscules
        sql = "SELECT * FROM contracts WHERE target = ? COLLATE NOCASE ORDER BY date DESC"
        return self.app.query(sql, (pseudo,))

    def get_contracts_for_client(self, pseudo: str) -> list:
        sql = "SELECT * FROM contracts WHERE client = ? COLLATE NOCASE ORDER BY date DESC"
        return self.app.query(sql, (pseudo,))