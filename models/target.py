"""Modèle Target — représente une cible (joueur/contact)."""

from datetime import datetime
from .base_model import BaseModel


class Target(BaseModel):
    """Représente une cible (joueur Star Citizen).

    Attributs:
        pseudo: pseudonyme unique du joueur
        org: organisation principale
        ship: vaisseau actuel
        threat: niveau de menace (LOW, MEDIUM, HIGH, CRITICAL)
        notes: notes de renseignement
        alignment: alignement (AMI, NEUTRE, ENNEMI, PIRATE)
        pvp_lvl: niveau PvP (NOOB, ROOKIE, VETERAN, ACE)
        activity: activité principale (PIRATE, BOUNTY HUNTER, MINEUR, TRADER)
        sid: SID de l'organisation
        org_rank: rang dans l'organisation
        date: date d'ajout/dernière mise à jour
        wins: nombre de victoires glanées
        losses: nombre de défaites
        enlisted_date: date d'enlistement RSI
        language: langue(s) parlée(s)
        affiliates: affiliations secondaires
    """

    # Colonnes de la table targets
    COLUMNS = [
        "pseudo",
        "org",
        "ship",
        "threat",
        "notes",
        "date",
        "wins",
        "losses",
        "alignment",
        "pvp_lvl",
        "activity",
        "sid",
        "org_rank",
        "enlisted_date",
        "language",
        "affiliates",
    ]

    # Valeurs par défaut
    DEFAULT_ALIGNMENT = "NEUTRE"
    DEFAULT_PVP_LVL = "Inconnu"
    DEFAULT_ACTIVITY = "Inconnu"
    DEFAULT_THREAT = "LOW"

    def __init__(
        self,
        pseudo: str,
        org: str = "",
        ship: str = "",
        threat: str = DEFAULT_THREAT,
        notes: str = "",
        alignment: str = DEFAULT_ALIGNMENT,
        pvp_lvl: str = DEFAULT_PVP_LVL,
        activity: str = DEFAULT_ACTIVITY,
        sid: str = "N/A",
        org_rank: str = "N/A",
        date: str = None,
        wins: int = 0,
        losses: int = 0,
        enlisted_date: str = "N/A",
        language: str = "N/A",
        affiliates: str = "NONE",
    ):
        self.pseudo = pseudo.upper() if pseudo else ""
        self.org = org.upper() if org else ""
        self.ship = ship.upper() if ship else ""
        self.threat = threat
        self.notes = notes
        self.alignment = alignment
        self.pvp_lvl = pvp_lvl
        self.activity = activity
        self.sid = sid.upper() if sid else "N/A"
        self.org_rank = org_rank.upper() if org_rank else "N/A"
        self.date = date or datetime.now().strftime("%d/%m/%Y")
        self.wins = int(wins) if wins else 0
        self.losses = int(losses) if losses else 0
        self.enlisted_date = enlisted_date
        self.language = language
        self.affiliates = affiliates.upper() if affiliates else "NONE"

    def is_threat(self) -> bool:
        """Retourne True si c'est une menace (ENNEMI ou PIRATE)."""
        return self.alignment in ["ENNEMI", "PIRATE"]

    def is_friendly(self) -> bool:
        """Retourne True si c'est un allié."""
        return self.alignment == "AMI"

    def is_neutral(self) -> bool:
        """Retourne True si c'est neutre."""
        return self.alignment == "NEUTRE"

    def add_win(self) -> None:
        """Incrémente le compteur de victoires."""
        self.wins += 1
        self.date = datetime.now().strftime("%d/%m/%Y")

    def add_loss(self) -> None:
        """Incrémente le compteur de défaites."""
        self.losses += 1
        self.date = datetime.now().strftime("%d/%m/%Y")

    def pvp_ratio(self) -> float:
        """Retourne le ratio victoires/défaites."""
        if self.losses == 0:
            return float(self.wins) if self.wins > 0 else 0.0
        return self.wins / self.losses

    def threat_level_numeric(self) -> int:
        """Convertit threat string en valeur numérique (0-3)."""
        threat_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        return threat_map.get(self.threat, 0)

    @classmethod
    def from_db_row(cls, row: tuple):
        """Crée une instance à partir d'une row de DB."""
        return cls.from_tuple(row, cls.COLUMNS)

    def to_db_tuple(self) -> tuple:
        """Convertit en tuple pour insertion/update DB."""
        return self.to_tuple(self.COLUMNS)
