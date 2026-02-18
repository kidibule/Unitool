"""Modèle ContractType — représente un type de contrat pré-configuré."""

from .base_model import BaseModel


class ContractType(BaseModel):
    """Représente un type de contrat avec récompense par défaut.

    Attributs:
        name: nom du type (VHRT, ERT, AAA, etc.)
        reward: récompense standard en aUEC
    """

    COLUMNS = ["name", "reward"]

    # Types courants
    VHRT = "VHRT"  # Very High Risk Tactical
    ERT = "ERT"  # Extremely Resilient Target
    HRT = "HRT"  # High Risk Tactical
    MRT = "MRT"  # Medium Risk Tactical
    LRT = "LRT"  # Low Risk Tactical

    def __init__(self, name: str, reward: str = "0"):
        self.name = name.upper() if name else ""
        self.reward = str(reward)

    def get_reward_int(self) -> int:
        """Retourne la récompense sous forme d'entier."""
        try:
            return int(str(self.reward).replace(" ", "").replace(",", ""))
        except ValueError:
            return 0

    def is_high_risk(self) -> bool:
        """Retourne True si c'est un contrat haut risque."""
        return self.name in [self.ERT, self.HRT]

    def is_pvp(self) -> bool:
        """Retourne True si c'est un contrat PvP (contient 'T')."""
        return "T" in self.name

    @classmethod
    def from_db_row(cls, row: tuple):
        """Crée une instance à partir d'une row de DB."""
        return cls.from_tuple(row, cls.COLUMNS)

    def to_db_tuple(self) -> tuple:
        """Convertit en tuple pour insertion/update DB."""
        return self.to_tuple(self.COLUMNS)
