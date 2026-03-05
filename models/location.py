"""Modèle Location — stockage local de positions (x, y, z)."""

from .base_model import BaseModel

import json
import os

class Location(BaseModel):
    """Gère un catalogue local de coordonnées avec persistance JSON."""

    def __init__(self, storage_file="data/locations.json"):
        """Initialise les positions par défaut puis charge le stockage disque."""
        self.storage_file = storage_file
        self.locations = {
            "ARC-L1": [150000, 25000, 0],
            "CELLIN": [45000, 12000, 500],
            "DAYMAR": [48000, -15000, -200],
            "YELA": [52000, 5000, 1200]
        }
        self.load_from_disk()

    def get_coords(self, name):
        """Retourne les coordonnées [x, y, z] d'un lieu"""
        return self.locations.get(name.upper(), None)

    def add_location(self, name, coords):
        """Ajoute ou remplace une position puis sauvegarde sur disque."""
        self.locations[name.upper()] = coords
        self.save_to_disk()

    def get_all_names(self):
        """Retourne les noms de positions triés alphabétiquement."""
        return sorted(list(self.locations.keys()))

    def save_to_disk(self):
        """Sérialise le dictionnaire des positions vers un fichier JSON."""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump(self.locations, f)

    def load_from_disk(self):
        """Charge les positions depuis le disque si le fichier existe."""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                self.locations.update(json.load(f))