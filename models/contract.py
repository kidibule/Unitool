"""Modèle Contract — représente un contrat/bounty."""

from datetime import datetime
from .base_model import BaseModel


class Contract(BaseModel):
    """Représente un contrat (bounty/mission).

    Attributs:
        id: identifiant unique
        target: pseudo de la cible
        client: ID du client
        reward: récompense en aUEC
        status: état du contrat (OPEN, CLOSED)
        date: date de création
        priority: priorité (LOW, MEDIUM, HIGH, CRITICAL)
        contract_type: type de contrat (VHRT, ERT, etc.)
    """

    COLUMNS = [
        "id",
        "target",
        "client",
        "reward",
        "status",
        "date",
        "priority",
        "contract_type",
    ]

    # États possibles
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"

    # Priorités
    PRIORITY_LOW = "LOW"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_CRITICAL = "CRITICAL"

    def __init__(
        self,
        target: str,
        client: str = "",
        reward: str = "0",
        status: str = STATUS_OPEN,
        date: str = None,
        priority: str = PRIORITY_MEDIUM,
        contract_type: str = None,
        id: int = None,
    ):
        self.id = id
        self.target = target.upper() if target else ""
        self.client = client.upper() if client else ""
        self.reward = str(reward)
        self.status = status
        self.date = date or datetime.now().strftime("%d/%m %H:%M")
        self.priority = priority
        self.contract_type = contract_type

    def is_open(self) -> bool:
        """Retourne True si le contrat est actif."""
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        """Retourne True si le contrat est fermé."""
        return self.status == self.STATUS_CLOSED

    def close(self) -> None:
        """Marque le contrat comme fermé."""
        self.status = self.STATUS_CLOSED
        self.date = datetime.now().strftime("%d/%m %H:%M")

    def get_reward_int(self) -> int:
        """Retourne la récompense sous forme d'entier."""
        try:
            return int(str(self.reward).replace(" ", "").replace(",", ""))
        except ValueError:
            return 0

    def priority_numeric(self) -> int:
        """Convertit priority string en valeur numérique (0-3)."""
        priority_map = {
            self.PRIORITY_LOW: 0,
            self.PRIORITY_MEDIUM: 1,
            self.PRIORITY_HIGH: 2,
            self.PRIORITY_CRITICAL: 3,
        }
        return priority_map.get(self.priority, 1)

    @classmethod
    def from_db_row(cls, row: tuple):
        """Crée une instance à partir d'une row de DB."""
        return cls.from_tuple(row, cls.COLUMNS)

    def to_db_tuple(self) -> tuple:
        """Convertit en tuple pour insertion/update DB."""
        return self.to_tuple(self.COLUMNS)
