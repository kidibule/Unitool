"""Utilitaires de seed Location depuis JSON vers SQLite."""

from .base_model import BaseModel

import json
import os

class Location(BaseModel):
    """Legacy model conservé pour compatibilité historique."""

    def __init__(self, storage_file="data/locations.json"):
        """Initialise les positions par défaut puis charge le stockage disque."""
        self.storage_file = storage_file
        self.locations = {
            # Coordonnées en mètres (unité native Star Citizen)
            "HURSTON":   [12858745000,           0,         0],
            "ARCCORP":   [18545567000,  -22151149000,         0],
            "MICROTECH": [22935149000,   29351490000,         0],
            "CRUSADER":  [-18962172000,  -2665623000,         0],
            "ARIAL":     [12858745000,           0,   3815000],
            "ABERDEEN":  [12858745000,           0,  -3715000],
            "MAGDA":     [12858745000,     3315000,         0],
            "ITA":       [12858745000,    -3615000,         0],
            "LYRIA":     [18545567000,  -22151149000,   3515000],
            "WALA":      [18545567000,  -22151149000,  -3815000],
            "CALLIOPE":  [22935149000,   29351490000,   4515000],
            "CLIO":      [22935149000,   29351490000,  -4215000],
            "EUTERPE":   [22935149000,      33866000,         0],
            "CELLIN":    [-18962172000,  -2665623000,  10115000],
            "DAYMAR":    [-18962172000,  -2665623000, -10115000],
            "YELA":      [-18962172000,    -12780000,         0],
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


class LocationSeedImporter:
    """Charge des coordonnées seed depuis un JSON (fallback intégré)."""

    DEFAULT_SEED = {
        # Coordonnées en mètres (unité native Star Citizen)
        "HURSTON":   [12858745000,           0,         0],
        "ARCCORP":   [18545567000,  -22151149000,         0],
        "MICROTECH": [22935149000,   29351490000,         0],
        "CRUSADER":  [-18962172000,  -2665623000,         0],
        "ARIAL":     [12858745000,           0,   3815000],
        "ABERDEEN":  [12858745000,           0,  -3715000],
        "MAGDA":     [12858745000,     3315000,         0],
        "ITA":       [12858745000,    -3615000,         0],
        "LYRIA":     [18545567000,  -22151149000,   3515000],
        "WALA":      [18545567000,  -22151149000,  -3815000],
        "CALLIOPE":  [22935149000,   29351490000,   4515000],
        "CLIO":      [22935149000,   29351490000,  -4215000],
        "EUTERPE":   [22935149000,      33866000,         0],
        "CELLIN":    [-18962172000,  -2665623000,  10115000],
        "DAYMAR":    [-18962172000,  -2665623000, -10115000],
        "YELA":      [-18962172000,    -12780000,         0],
    }

    @classmethod
    def load_seed_map(cls, seed_file="data/locations.json"):
        """Retourne un mapping name -> [x,y,z] valide, depuis JSON ou fallback."""
        seed = dict(cls.DEFAULT_SEED)
        if not os.path.exists(seed_file):
            return seed

        try:
            with open(seed_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception:
            return seed

        if not isinstance(loaded, dict):
            return seed

        normalized = {}
        for name, coords in loaded.items():
            if not isinstance(name, str):
                continue
            if not isinstance(coords, (list, tuple)) or len(coords) < 3:
                continue
            try:
                normalized[name.strip().upper()] = [
                    float(coords[0]),
                    float(coords[1]),
                    float(coords[2]),
                ]
            except (TypeError, ValueError):
                continue

        return normalized if normalized else seed