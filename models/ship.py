"""Modèle Ship — représente un vaisseau enregistré dans la base."""

from datetime import datetime
from .base_model import BaseModel


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
        "boosted",
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
        scm_speed: str = "",
        scm_boost_forward: str = "",
        scm_boost_backward: str = "",
        nav_max_speed: str = "",
        pitch: str = "",
        yaw: str = "",
        roll: str = "",
        boosted: str = "",
        power_consumption: str = "",
        cm_decoy_noise: str = "",
        hp: int = 0,
        cargo: str = "",
        dimensions: str = "",
        mass: str = "",
        hydrogen_capacity: str = "",
        qt_fuel_capacity: str = "",
        expedition_fee: str = "",
        claim_time: str = "",
        expedite_time: str = "",
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
        self.boosted = boosted
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
            boosted=data.get("boosted", ""),
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
