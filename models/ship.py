"""Modèle Ship — représente un vaisseau enregistré dans la base."""

import json
from collections import defaultdict
from .base_model import BaseModel
from .component import Component


# ---------------------------------------------------------------------------
# Table de correspondance : type SC (JSON) → (catégorie DB, sous-type DB)
# Pour ajouter un nouveau type SC : ajouter une entrée ici.
# ---------------------------------------------------------------------------
SC_TYPE_TO_SLOT = {
    # Armes pilote
    "WeaponGun":        ("WEAPON",     "GUN"),
    "Turret":           ("WEAPON",     "GUN"),
    "MissileLauncher":  ("WEAPON",     "MISSILE RACK"),
    "BombLauncher":     ("WEAPON",     "BOMB RACK"),
    # Défense active
    "WeaponDefensive":  ("SYSTEMS",    "COUNTERMEASURE"),
    # Systèmes
    "Shield":           ("SYSTEMS",    "SHIELD"),
    "PowerPlant":       ("SYSTEMS",    "POWER PLANT"),
    "Cooler":           ("SYSTEMS",    "COOLER"),
    "Radar":            ("SYSTEMS",    "RADAR"),
    "FlightController": ("SYSTEMS",    "FLIGHT BLADE"),
    "LifeSupportGenerator": ("SYSTEMS", "LIFE SUPPORT"),
    # Propulsion
    "QuantumDrive":     ("PROPULSION", "QUANTUM DRIVE"),
    "JumpDrive":        ("PROPULSION", "JUMP DRIVE"),
    "FuelIntake":       ("PROPULSION", "FUEL INTAKE"),
    # Modules
    "WeaponMining":     ("MODULE",     "MINING LASER"),
    "SalvageHead":      ("MODULE",     "SALVAGE HEAD"),
    "TractorBeam":      ("MODULE",     "TRACTOR BEAM"),
    "TowingBeam":       ("MODULE",     "TOWING BEAM"),
}


class Ship(BaseModel):
    """Représente un vaisseau.

    Attributs principaux:
        name: nom / identifiant du vaisseau (unique)
        brand: fabricant
        role: rôle (ex: LIGHT FREIGHT)
        career: carrière (ex: TRANSPORTER)
        size: classe de taille SC (1-10)
        crew_size: équipage minimum

    Les champs préfixés sc_ proviennent directement du data miner SC.
    sc_data_json stocke le JSON brut complet pour garantir la compatibilité
    avec les futures mises à jour de SC.
    """

    COLUMNS = [
        # ---- Identification ----
        "name",
        "brand",
        "role",
        "career",
        "size",
        "crew_size",
        # ---- Dimensions ----
        "length",
        "width",
        "height",
        "mass",
        "mass_total",
        # ---- Vitesses ----
        "scm_speed",
        "scm_boost_forward",
        "scm_boost_backward",
        "nav_max_speed",
        # ---- Maniabilité ----
        "pitch",
        "yaw",
        "roll",
        "boosted_pitch",
        "boosted_yaw",
        "boosted_roll",
        # ---- Accélérations ----
        "accel_main",
        "accel_retro",
        "accel_maneuver",
        "accel_main_boosted",
        # ---- Propulsion hydrogène ----
        "hydrogen_capacity",
        "fuel_intake_rate",
        "fuel_usage_main",
        # ---- Quantum ----
        "qt_fuel_capacity",
        "qt_range",
        "qt_speed",
        "qt_spool_time",
        # ---- Combat ----
        "hp",
        "shield_hp",
        "shield_regen",
        "pilot_dps",
        "pilot_alpha",
        "pilot_sustained_dps",
        "missiles_count",
        "missiles_damage",
        # ---- Signature ----
        "emission_ir",
        "emission_em",
        # ---- Cargo ----
        "cargo",
        # ---- Assurance ----
        "expedition_fee",
        "claim_time",
        "expedite_time",
        # ---- Identifiants SC ----
        "sc_uuid",
        "sc_class_name",
        # ---- Champs legacy / compat ----
        "dimensions",
        "power_consumption",
        "cm_decoy_noise",
        # ---- Raw JSON (future-proof) ----
        "sc_data_json",
    ]

    DEFAULT_STATUS = "UNKNOWN"

    def __init__(
        self,
        name: str,
        brand: str = "",
        role: str = "",
        career: str = "",
        size: int = 0,
        crew_size: int = 0,
        # Dimensions
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        mass: float = 0.0,
        mass_total: float = 0.0,
        # Vitesses
        scm_speed: float = 0.0,
        scm_boost_forward: float = 0.0,
        scm_boost_backward: float = 0.0,
        nav_max_speed: float = 0.0,
        # Maniabilité
        pitch: float = 0.0,
        yaw: float = 0.0,
        roll: float = 0.0,
        boosted_pitch: float = 0.0,
        boosted_yaw: float = 0.0,
        boosted_roll: float = 0.0,
        # Accélérations
        accel_main: float = 0.0,
        accel_retro: float = 0.0,
        accel_maneuver: float = 0.0,
        accel_main_boosted: float = 0.0,
        # Propulsion hydrogène
        hydrogen_capacity: float = 0.0,
        fuel_intake_rate: float = 0.0,
        fuel_usage_main: float = 0.0,
        # Quantum
        qt_fuel_capacity: float = 0.0,
        qt_range: float = 0.0,
        qt_speed: float = 0.0,
        qt_spool_time: float = 0.0,
        # Combat
        hp: int = 0,
        shield_hp: int = 0,
        shield_regen: float = 0.0,
        pilot_dps: float = 0.0,
        pilot_alpha: float = 0.0,
        pilot_sustained_dps: float = 0.0,
        missiles_count: int = 0,
        missiles_damage: float = 0.0,
        # Signature
        emission_ir: float = 0.0,
        emission_em: float = 0.0,
        # Cargo
        cargo: float = 0.0,
        # Assurance
        expedition_fee: float = 0.0,
        claim_time: float = 0.0,
        expedite_time: float = 0.0,
        # Identifiants SC
        sc_uuid: str = "",
        sc_class_name: str = "",
        # Legacy / compat
        dimensions: str = "",
        power_consumption: str = "",
        cm_decoy_noise: str = "",
        # Raw JSON
        sc_data_json: str = "",
    ):
        self.name = name.upper() if name else ""
        self.brand = brand.upper() if brand else ""
        self.role = role.upper() if role else ""
        self.career = career.upper() if career else ""
        self.size = int(size) if size else 0
        self.crew_size = int(crew_size) if crew_size else 0
        # Dimensions
        self.length = float(length) if length else 0.0
        self.width = float(width) if width else 0.0
        self.height = float(height) if height else 0.0
        self.mass = float(mass) if mass else 0.0
        self.mass_total = float(mass_total) if mass_total else 0.0
        # Vitesses
        self.scm_speed = float(scm_speed) if scm_speed else 0.0
        self.scm_boost_forward = float(scm_boost_forward) if scm_boost_forward else 0.0
        self.scm_boost_backward = float(scm_boost_backward) if scm_boost_backward else 0.0
        self.nav_max_speed = float(nav_max_speed) if nav_max_speed else 0.0
        # Maniabilité
        self.pitch = float(pitch) if pitch else 0.0
        self.yaw = float(yaw) if yaw else 0.0
        self.roll = float(roll) if roll else 0.0
        self.boosted_pitch = float(boosted_pitch) if boosted_pitch else 0.0
        self.boosted_yaw = float(boosted_yaw) if boosted_yaw else 0.0
        self.boosted_roll = float(boosted_roll) if boosted_roll else 0.0
        # Accélérations
        self.accel_main = float(accel_main) if accel_main else 0.0
        self.accel_retro = float(accel_retro) if accel_retro else 0.0
        self.accel_maneuver = float(accel_maneuver) if accel_maneuver else 0.0
        self.accel_main_boosted = float(accel_main_boosted) if accel_main_boosted else 0.0
        # Propulsion hydrogène
        self.hydrogen_capacity = float(hydrogen_capacity) if hydrogen_capacity else 0.0
        self.fuel_intake_rate = float(fuel_intake_rate) if fuel_intake_rate else 0.0
        self.fuel_usage_main = float(fuel_usage_main) if fuel_usage_main else 0.0
        # Quantum
        self.qt_fuel_capacity = float(qt_fuel_capacity) if qt_fuel_capacity else 0.0
        self.qt_range = float(qt_range) if qt_range else 0.0
        self.qt_speed = float(qt_speed) if qt_speed else 0.0
        self.qt_spool_time = float(qt_spool_time) if qt_spool_time else 0.0
        # Combat
        self.hp = int(hp) if hp else 0
        self.shield_hp = int(shield_hp) if shield_hp else 0
        self.shield_regen = float(shield_regen) if shield_regen else 0.0
        self.pilot_dps = float(pilot_dps) if pilot_dps else 0.0
        self.pilot_alpha = float(pilot_alpha) if pilot_alpha else 0.0
        self.pilot_sustained_dps = float(pilot_sustained_dps) if pilot_sustained_dps else 0.0
        self.missiles_count = int(missiles_count) if missiles_count else 0
        self.missiles_damage = float(missiles_damage) if missiles_damage else 0.0
        # Signature
        self.emission_ir = float(emission_ir) if emission_ir else 0.0
        self.emission_em = float(emission_em) if emission_em else 0.0
        # Cargo
        self.cargo = float(cargo) if cargo else 0.0
        # Assurance
        self.expedition_fee = float(expedition_fee) if expedition_fee else 0.0
        self.claim_time = float(claim_time) if claim_time else 0.0
        self.expedite_time = float(expedite_time) if expedite_time else 0.0
        # Identifiants SC
        self.sc_uuid = sc_uuid or ""
        self.sc_class_name = sc_class_name or ""
        # Legacy / compat
        self.dimensions = dimensions or ""
        self.power_consumption = power_consumption or ""
        self.cm_decoy_noise = cm_decoy_noise or ""
        # Raw JSON
        self.sc_data_json = sc_data_json or ""

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
            return False, f"ERROR: No [{component.category}] slot on this chassis."

        # 1. Vérification de la Taille (S1, S2, etc.)
        if int(component.size) > cap["max_size"]:
            return False, f"SIZE: S{component.size} exceeds limit (Max S{cap['max_size']})."

        # 2. Vérification de la Quantité d'emplacements
        current_count = sum(1 for c in self.components if c.category == component.category)
        if current_count >= cap["max_qty"]:
            return False, f"SLOTS: All [{component.category}] slots are full ({cap['max_qty']}/{cap['max_qty']})."

        return True, "Valid configuration."

    def add_component(self, component: Component) -> bool:
        """Ajoute le composant seulement si la validation passe."""
        allowed, message = self.can_add_component(component)
        if allowed:
            self.components.append(component)
            return True
        print(f"REJECTED: {message}") # Debug ou Log
        return False

    @classmethod
    def from_db_row(cls, row: tuple):
        if not row:
            return None
        data = dict(zip(cls.COLUMNS, row))
        return cls(**{k: data.get(k) for k in cls.COLUMNS})

    def to_db_tuple(self) -> tuple:
        return self.to_tuple(self.COLUMNS)

    @classmethod
    def from_sc_json(cls, data: dict) -> "Ship":
        """Crée un Ship depuis un fichier JSON exporté par le SC data miner.

        Tous les champs explicitement mappés ici correspondent aux clés du JSON
        (version 4.x). Le JSON brut est stocké dans sc_data_json pour garantir
        la compatibilité avec les futures mises à jour de Star Citizen — ajouter
        un nouveau champ ne nécessite qu'un mapping ici + une migration DB.

        Args:
            data: dict chargé depuis un fichier JSON SC (ex: aegs_avenger_titan.json)
        """
        flight = data.get("FlightCharacteristics", {})
        speeds = flight.get("Speeds", {})
        angular = flight.get("AngularRates", {})
        angular_b = flight.get("AngularRatesBoosted", {})
        accel = flight.get("Acceleration", {})
        accel_raw = accel.get("Raw", {})
        accel_boost = accel.get("Boosted", {})

        propulsion = data.get("Propulsion", {})
        fuel_usage = propulsion.get("FuelUsage", {})

        qt = data.get("QuantumTravel", {})
        shields = data.get("ShieldsTotal", {})
        weaponry = data.get("Weaponry", {})
        missiles = weaponry.get("Missiles", {})
        emission = data.get("Emission", {})
        insurance = data.get("Insurance", {})
        manufacturer = data.get("Manufacturer", {})

        name = data.get("Name", "")
        length = data.get("Length", 0.0)
        width = data.get("Width", 0.0)
        height = data.get("Height", 0.0)

        return cls(
            name=name,
            brand=manufacturer.get("Name", ""),
            role=data.get("Role", ""),
            career=data.get("Career", ""),
            size=data.get("Size", 0),
            crew_size=data.get("Crew", 0),
            # Dimensions
            length=length,
            width=width,
            height=height,
            mass=data.get("Mass", 0.0),
            mass_total=data.get("MassTotal", 0.0),
            # Vitesses
            scm_speed=speeds.get("Scm", 0.0),
            scm_boost_forward=speeds.get("BoostForward", 0.0),
            scm_boost_backward=speeds.get("BoostBackward", 0.0),
            nav_max_speed=speeds.get("Max", 0.0),
            # Maniabilité
            pitch=angular.get("Pitch", 0.0),
            yaw=angular.get("Yaw", 0.0),
            roll=angular.get("Roll", 0.0),
            boosted_pitch=angular_b.get("Pitch", 0.0),
            boosted_yaw=angular_b.get("Yaw", 0.0),
            boosted_roll=angular_b.get("Roll", 0.0),
            # Accélérations
            accel_main=accel_raw.get("Main", 0.0),
            accel_retro=accel_raw.get("Retro", 0.0),
            accel_maneuver=accel_raw.get("Maneuver", 0.0),
            accel_main_boosted=accel_boost.get("Main", 0.0),
            # Propulsion hydrogène
            hydrogen_capacity=propulsion.get("FuelCapacity", 0.0),
            fuel_intake_rate=propulsion.get("FuelIntakeRate", 0.0),
            fuel_usage_main=fuel_usage.get("Main", 0.0),
            # Quantum
            qt_fuel_capacity=qt.get("FuelCapacity", 0.0),
            qt_range=qt.get("Range", 0.0),
            qt_speed=qt.get("Speed", 0.0),
            qt_spool_time=qt.get("SpoolTime", 0.0),
            # Combat
            hp=data.get("Health", 0),
            shield_hp=shields.get("Hp", 0),
            shield_regen=shields.get("Regen", 0.0),
            pilot_dps=weaponry.get("PilotDps", 0.0),
            pilot_alpha=weaponry.get("PilotAlpha", 0.0),
            pilot_sustained_dps=weaponry.get("PilotSustainedDps", 0.0),
            missiles_count=missiles.get("Count", 0),
            missiles_damage=weaponry.get("TotalMissiles", 0.0),
            # Signature
            emission_ir=emission.get("IrShields", 0.0),
            emission_em=emission.get("EmShields", 0.0),
            # Cargo
            cargo=data.get("Cargo", 0.0),
            # Assurance
            expedition_fee=insurance.get("ExpeditedCost", 0.0),
            claim_time=insurance.get("StandardClaimTime", 0.0),
            expedite_time=insurance.get("ExpeditedClaimTime", 0.0),
            # Identifiants SC
            sc_uuid=data.get("UUID", ""),
            sc_class_name=data.get("ClassName", ""),
            # Legacy: dimensions as string for compat
            dimensions=f"{length}x{width}x{height}",
            # Raw JSON pour future-proofing
            sc_data_json=json.dumps(data, ensure_ascii=False),
        )

    @staticmethod
    def slots_from_sc_json(data: dict) -> list[dict]:
        """Déduit les slots éditables du chassis depuis un JSON SC data miner.

        Seuls les hardpoints de premier niveau (chassis) avec Editable=True
        sont retenus. Les sous-slots (composants dans une tourelle, missiles
        dans un rack, etc.) sont ignorés — ils relèvent du loadout, pas des
        specs du chassis.

        Returns:
            Liste de dicts {"category", "subtype_name", "max_qty", "max_size"}
            prêts à insérer dans ship_subtype_specs. Les sous-types incluent la
            taille pour séparer les slots de tailles différentes d'une même
            catégorie (ex: "GUN S3" vs "GUN S4").
        """
        slot_counts: dict[tuple, int] = defaultdict(int)

        for item in data.get("Loadout", []):
            # Seuls les hardpoints du chassis (pas de parent)
            if item.get("PortId") != item.get("RootPortId"):
                continue
            # Uniquement les slots modifiables par le joueur
            if not item.get("Editable", False):
                continue
            max_size = item.get("MaxSize", 0)
            if not max_size:
                continue

            # Résolution du type SC : CompatibleTypes[0].Type en priorité,
            # sinon le champ Type de l'item lui-même.
            compat = item.get("CompatibleTypes", [])
            if compat:
                sc_type_raw = compat[0].get("Type", "")
            else:
                sc_type_raw = item.get("Type", "")

            # Type SC = partie avant le "." (ex: "Turret.GunTurret" → "Turret")
            sc_type = sc_type_raw.split(".")[0]

            if sc_type not in SC_TYPE_TO_SLOT:
                continue  # slot non-pertinent pour le joueur (door, room, light…)

            category, base_subtype = SC_TYPE_TO_SLOT[sc_type]
            subtype_name = f"{base_subtype} S{max_size}"
            slot_counts[(category, subtype_name, max_size)] += 1

        return [
            {
                "category": category,
                "subtype_name": subtype_name,
                "max_qty": count,
                "max_size": max_size,
            }
            for (category, subtype_name, max_size), count in sorted(slot_counts.items())
        ]

    @property
    def total_power_draw(self):
        return sum(float(c.stats.get("power_draw", 0)) for c in self.components)

    @property
    def total_shields(self):
        """Bouclier total : valeur importée du JSON ou calculée depuis les composants."""
        if self.shield_hp:
            return self.shield_hp
        return sum(float(c.stats.get("shield_hp", 0)) for c in self.components if c.category == "SYSTEMS")

