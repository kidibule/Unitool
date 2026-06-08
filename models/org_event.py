"""Modèle OrgEvent — représente un événement d'organisation."""

from .base_model import BaseModel


class OrgEvent(BaseModel):
    """Entité métier pour l'agenda d'organisation."""

    COLUMNS = [
        "id",
        "date",
        "time",
        "title",
        "description",
        "location",
        "participants",
    ]

    def __init__(
        self,
        id: int | None = None,
        date: str = "",
        time: str = "",
        title: str = "",
        description: str = "",
        location: str = "",
        participants: str = "",
    ):
        self.id = int(id) if id not in (None, "") else None
        self.date = str(date or "")
        self.time = str(time or "")
        self.title = str(title or "")
        self.description = str(description or "")
        self.location = str(location or "")
        self.participants = str(participants or "")

    @classmethod
    def from_db_row(cls, row: tuple):
        """Construit un OrgEvent à partir d'une ligne DB."""
        return cls.from_tuple(row, cls.COLUMNS)
