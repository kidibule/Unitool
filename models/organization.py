"""Modèle Organization — représente une organisation."""

from .base_model import BaseModel


class Organization(BaseModel):
    """Représente une organisation Star Citizen.

    Attributs:
        sid: SID unique de l'organisation
        name: nom complet
        tag: tag court (3-5 chars)
        member_count: nombre de membres
        description: description
    """

    COLUMNS = ["sid", "name", "tag", "member_count", "description"]

    def __init__(
        self,
        sid: str,
        name: str = "",
        tag: str = "",
        member_count: int = 0,
        description: str = "",
    ):
        self.sid = sid.upper() if sid else ""
        self.name = name
        self.tag = tag.upper() if tag else ""
        self.member_count = int(member_count) if member_count else 0
        self.description = description

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
