"""ContractController — gère les contrats et bounty board."""

from datetime import datetime


class ContractController:
    """Contrôleur pour les contrats (BOUNTY BOARD).

    Méthodes :
    - add_contract : crée un nouveau contrat
    - get_active_contracts : liste les contrats actifs
    - get_closed_contracts : liste les contrats complétés
    - complete_contract : marque un contrat comme fermé
    - delete_contract : supprime un contrat
    - get_contract_types : liste les types disponibles
    - add_contract_type : crée un nouveau type
    - delete_contract_type : supprime un type
    """

    def __init__(self, app_controller):
        """Initialise le contrôleur contrat avec le controller app principal.

        Args:
            app_controller: instance d'AppController pour accès à la DB
        """
        self.app = app_controller

    def add_contract(
        self,
        target: str,
        client: str,
        reward: str,
        priority: str = "MEDIUM",
        contract_type: str = None,
    ) -> None:
        """Ajoute un nouveau contrat."""
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

    def get_active_contracts(self) -> list:
        """Retourne tous les contrats actifs (OPEN)."""
        return self.app.query(
            "SELECT * FROM contracts WHERE status='OPEN' ORDER BY id DESC"
        )

    def get_closed_contracts(self) -> list:
        """Retourne tous les contrats fermés (CLOSED)."""
        return self.app.query(
            "SELECT * FROM contracts WHERE status='CLOSED' ORDER BY id DESC"
        )

    def complete_contract(self, contract_id: int, target: str) -> None:
        """Marque un contrat comme fermé et incrémente les wins de la cible."""
        self.app.commit(
            "UPDATE contracts SET status='CLOSED' WHERE id=?", (contract_id,)
        )
        # Incrémenter les wins
        self.app.commit(
            "UPDATE targets SET wins = wins + 1 WHERE pseudo=?", (target.upper(),)
        )

    def delete_contract(self, contract_id: int) -> None:
        """Supprime un contrat de l'historique."""
        self.app.commit("DELETE FROM contracts WHERE id=?", (contract_id,))

    def get_contract_types(self) -> list:
        """Récupère tous les types de contrats."""
        return self.app.query("SELECT name, reward FROM contract_types")

    def add_contract_type(self, name: str, reward: str) -> None:
        """Ajoute un nouveau type de contrat."""
        self.app.commit(
            "INSERT INTO contract_types VALUES (?, ?)", (name.upper(), reward)
        )

    def delete_contract_type(self, name: str) -> None:
        """Supprime un type de contrat."""
        self.app.commit("DELETE FROM contract_types WHERE name=?", (name.upper(),))

    def get_contract_reward_for_type(self, contract_type: str) -> str:
        """Récupère la récompense d'un type de contrat."""
        result = self.app.query(
            "SELECT reward FROM contract_types WHERE name=?", (contract_type,)
        )
        return result[0][0] if result else None
