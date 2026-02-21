"""Modèle Organization — représente une organisation."""

from .base_model import BaseModel


from datetime import datetime
from .base_model import BaseModel


class Organization(BaseModel):
    """Représente une organisation Star Citizen.

    Attributs:
        sid: SID unique de l'organisation (ex: SCRP)
        name: Nom complet
        tag: Tag court (3-5 chars)
        description: Manifeste ou description
        member_count: Nombre total de membres
        visible_members: Liste des membres publics (JSON ou string)
        redacted_members: Liste des membres cachés (JSON ou string)
        ranks: Liste des grades et leurs niveaux (ex: "Amiral:1,Pilote:5")
        org_type: Type d'organisation (PMC, Corporation, etc.)
        specialization: Spécialisation (Salvage, Combat, etc.)
        allies: Tags des organisations alliées
        enemies: Tags des organisations ennemies
        neutrals: Tags des organisations neutres
        updated_at: Date de dernière mise à jour
    """

    COLUMNS = [
        "sid", "name", "tag", "description", "member_count", 
        "visible_members", "redacted_members", "ranks", 
        "org_type", "specialization", "allies", "enemies", 
        "neutrals", "updated_at"
    ]

    def __init__(
        self,
        sid: str,
        name: str = "",
        tag: str = "",
        description: str = "",
        member_count: int = 0,
        visible_members: str = "[]",
        redacted_members: str = "[]",
        ranks: str = "{}",
        org_type: str = "ORGANIZATION",
        specialization: str = "GENERAL",
        allies: str = "",
        enemies: str = "",
        neutrals: str = "",
        updated_at: str = None,
    ):
        # Identifiants
        self.sid = sid.upper() if sid else ""
        self.name = name
        self.tag = tag.upper() if tag else ""
        self.description = description
        
        # Effectifs
        self.member_count = int(member_count) if member_count else 0
        self.visible_members = visible_members
        self.redacted_members = redacted_members
        
        # Structure et Type
        self.ranks = ranks
        self.org_type = org_type.upper()
        self.specialization = specialization.upper()
        
        # Diplomatie
        self.allies = allies.upper()
        self.enemies = enemies.upper()
        self.neutrals = neutrals.upper()
        
        # Metadata
        self.updated_at = updated_at or datetime.now().strftime("%d/%m/%Y")

    def is_large(self) -> bool:
        """Retourne True si l'org a plus de 100 membres."""
        return self.member_count > 100

    def rsi_url(self) -> str:
        """Retourne l'URL RSI de l'organisation."""
        return f"https://robertsspaceindustries.com/orgs/{self.sid}"

    @classmethod
    def from_db_row(cls, row: tuple):
        """Crée une instance à partir d'une row de DB."""
        return cls.from_tuple(row, cls.COLUMNS)

    def to_db_tuple(self) -> tuple:
        """Convertit en tuple pour insertion/update DB."""
        return self.to_tuple(self.COLUMNS)
