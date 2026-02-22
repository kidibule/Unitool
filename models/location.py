from .base_model import BaseModel

import json
import os

class Location(BaseModel):
    def __init__(self, storage_file="data/locations.json"):
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
        self.locations[name.upper()] = coords
        self.save_to_disk()

    def get_all_names(self):
        return sorted(list(self.locations.keys()))

    def save_to_disk(self):
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump(self.locations, f)

    def load_from_disk(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                self.locations.update(json.load(f))