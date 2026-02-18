"""Base pour tous les modèles — encapsule logique commune."""

from typing import Any, Dict
from datetime import datetime


class BaseModel:
    """Classe de base pour tous les modèles.

    Fournit des méthodes utilitaires pour la sérialisation/désérialisation
    et la gestion des attributs.
    """

    def __init__(self, **kwargs):
        """Initialise le modèle avec les attributs fournis."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le modèle en dictionnaire."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }

    def to_tuple(self, columns: list) -> tuple:
        """Convertit le modèle en tuple selon l'ordre des colonnes.

        Args:
            columns: liste des noms de colonnes dans l'ordre
        """
        return tuple(getattr(self, col, None) for col in columns)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Crée une instance du modèle à partir d'un dictionnaire."""
        return cls(**data)

    @classmethod
    def from_tuple(cls, data: tuple, columns: list):
        """Crée une instance du modèle à partir d'un tuple.

        Args:
            data: tuple de valeurs
            columns: liste des noms de colonnes
        """
        return cls(**dict(zip(columns, data)))

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({attrs})"
