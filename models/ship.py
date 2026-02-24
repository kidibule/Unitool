"""Modèle Ship — représente un vaisseau enregistré dans la base."""

from datetime import datetime
from .base_model import BaseModel
from .component import Component


class Ship(BaseModel):
    """Représente un vaisseau.

    Attributs principaux:
        name: nom / identifiant du vaisseau (unique)
        model: modèle/type du vaisseau
        owner: pseudo du propriétaire (si connu)
        registry: immatriculation / indicatif
        status: état courant (OPERATIONAL, DAMAGED, DESTROYED, UNKNOWN)
        location: position ou zone connue
        notes: notes libres
        date: date d'ajout / dernière mise à jour
    """

    COLUMNS = [
        "name",
        "brand",
        "role",
        "career",
        "size",
        "crew_size",
        "scm_speed",
        "scm_boost_forward",
        "scm_boost_backward",
        "nav_max_speed",
        "pitch",
        "yaw",
        "roll",
        "boosted_pitch",
        "boosted_yaw",
        "boosted_roll",
        "power_consumption",
        "cm_decoy_noise",
        "hp",
        "cargo",
        "dimensions",
        "mass",
        "hydrogen_capacity",
        "qt_fuel_capacity",
        "expedition_fee",
        "claim_time",
        "expedite_time",
    ]

    DEFAULT_STATUS = "UNKNOWN"

    def __init__(
         self,
        name: str,
        brand: str = "",
        role: str = "",
        career: str = "",
        size: str = "",
        crew_size: int = 0,
        scm_speed: int = 0,
        scm_boost_forward: int = 0,
        scm_boost_backward: int = 0,
        nav_max_speed: int = 0,
        pitch: int = 0,
        yaw: int = 0,
        roll: int = 0,
        boosted_pitch: int = 0,
        boosted_yaw: int = 0,
        boosted_roll: int = 0,
        power_consumption: str = "",
        cm_decoy_noise: str = "",
        hp: int = 0,
        cargo: int = 0,
        dimensions: str = "",
        mass: str = "",
        hydrogen_capacity: float = 0.0,
        qt_fuel_capacity: float = 0.0,
        expedition_fee: str = "",
        claim_time: float = 0.0,
        expedite_time: float = 0.0,
    ):
        self.name = name.upper() if name else ""
        self.brand = brand.upper() if brand else ""
        self.role = role.upper() if role else ""
        self.career = career.upper() if career else ""
        self.size = size
        self.crew_size = int(crew_size) if crew_size else 0
        self.scm_speed = scm_speed
        self.scm_boost_forward = scm_boost_forward
        self.scm_boost_backward = scm_boost_backward
        self.nav_max_speed = nav_max_speed
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll
        self.boosted_pitch = boosted_pitch
        self.boosted_yaw = boosted_yaw
        self.boosted_roll = boosted_roll
        self.power_consumption = power_consumption
        self.cm_decoy_noise = cm_decoy_noise
        self.hp = int(hp) if hp else 0
        self.cargo = cargo
        self.dimensions = dimensions
        self.mass = mass
        self.hydrogen_capacity = hydrogen_capacity
        self.qt_fuel_capacity = qt_fuel_capacity
        self.expedition_fee = expedition_fee
        self.claim_time = claim_time
        self.expedite_time = expedite_time

        self.components = [] 
        self.capabilities = {}

    def set_capability(self, category: str, max_qty: int, max_size: int):
        """Définit les limites d'équipement pour une catégorie (ex: WEAPON, 4, 3)."""
        self.capabilities[category.upper()] = {
            "max_qty": max_qty,
            "max_size": max_size
        }

    def can_add_component(self, component: Component) -> tuple[bool, str]:
        """
        Vérifie si le composant respecte les specs du châssis.
        Retourne (True, "OK") ou (False, "Raison du refus").
        """
        cap = self.capabilities.get(component.category.upper())
        
        if not cap:
            return False, f"ERREUR : Aucun slot [{component.category}] sur ce châssis."

        # 1. Vérification de la Taille (S1, S2, etc.)
        if int(component.size) > cap["max_size"]:
            return False, f"TAILLE : S{component.size} excède la limite (Max S{cap['max_size']})."

        # 2. Vérification de la Quantité d'emplacements
        current_count = sum(1 for c in self.components if c.category == component.category)
        if current_count >= cap["max_qty"]:
            return False, f"SLOTS : Tous les emplacements [{component.category}] sont occupés ({cap['max_qty']}/{cap['max_qty']})."

        return True, "Configuration valide."

    def add_component(self, component: Component) -> bool:
        """Ajoute le composant seulement si la validation passe."""
        allowed, message = self.can_add_component(component)
        if allowed:
            self.components.append(component)
            return True
        print(f"REFUSÉ : {message}") # Debug ou Log
        return False

    @classmethod
    def from_db_row(cls, row: tuple):
        if not row:
            return None
        data = dict(zip(cls.COLUMNS, row))
        return cls(
            name=data.get("name"),
            brand=data.get("brand", ""),
            role=data.get("role", ""),
            career=data.get("career", ""),
            size=data.get("size", ""),
            crew_size=data.get("crew_size", 0),
            scm_speed=data.get("scm_speed", ""),
            scm_boost_forward=data.get("scm_boost_forward", ""),
            scm_boost_backward=data.get("scm_boost_backward", ""),
            nav_max_speed=data.get("nav_max_speed", ""),
            pitch=data.get("pitch", ""),
            yaw=data.get("yaw", ""),
            roll=data.get("roll", ""),
            boosted_pitch=data.get("boosted_pitch", ""),
            boosted_yaw=data.get("boosted_yaw", ""),
            boosted_roll=data.get("boosted_roll", ""),
            power_consumption=data.get("power_consumption", ""),
            cm_decoy_noise=data.get("cm_decoy_noise", ""),
            hp=data.get("hp", 0),
            cargo=data.get("cargo", ""),
            dimensions=data.get("dimensions", ""),
            mass=data.get("mass", ""),
            hydrogen_capacity=data.get("hydrogen_capacity", ""),
            qt_fuel_capacity=data.get("qt_fuel_capacity", ""),
            expedition_fee=data.get("expedition_fee", ""),
            claim_time=data.get("claim_time", ""),
            expedite_time=data.get("expedite_time", ""),
        )

    def to_db_tuple(self) -> tuple:
        return self.to_tuple(self.COLUMNS)
    
    @property
    def total_power_draw(self):
        """Exemple de calcul dynamique basé sur les composants équipés"""
        return sum(float(c.stats.get("power_draw", 0)) for c in self.components)
        # --- CALCULS DYNAMIQUES ---

    @property
    def total_shields(self):
        """Calcule la capacité de bouclier totale basée sur les stats des composants."""
        return sum(float(c.stats.get("shield_hp", 0)) for c in self.components if c.category == "SYSTEMS")

