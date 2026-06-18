"""Modèle Ship — représente un vaisseau enregistré dans la base."""

import json
import math
from collections import defaultdict
from .base_model import BaseModel
from .component import Component


# ---------------------------------------------------------------------------
# Table de correspondance : type SC (JSON) → (catégorie DB, sous-type DB)
# Pour ajouter un nouveau type SC : ajouter une entrée ici.
# ---------------------------------------------------------------------------
SC_TYPE_TO_SLOT = {
    # ── Clés full-type (priorité sur les clés base) ──────────────────────
    "Turret.PDCTurret":     ("WEAPON",     "PDC"),
    # ── Armes pilote ─────────────────────────────────────────────────────
    "WeaponGun":        ("WEAPON",     "GUN"),
    "Turret":           ("WEAPON",     "GUN"),
    "TurretBase":       ("WEAPON",     "MANNED TURRET"),
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
        # ---- Armure ----
        "armor_hp",
        "armor_phys_mult",       # ResistanceMultipliers.Physical  (0.81 = -19% dmg pris)
        "armor_energy_mult",     # ResistanceMultipliers.Energy    (1.21 = +21% dmg pris)
        "armor_distortion_mult", # ResistanceMultipliers.Distortion
        "armor_deflect_phys",    # Deflection.Physical
        "armor_deflect_energy",  # Deflection.Energy
        "armor_ir_mult",         # SignalMultipliers.Infrared
        "armor_em_mult",         # SignalMultipliers.Electromagnetic
        "armor_cs_mult",         # SignalMultipliers.CrossSection
        # ---- Boucliers (stats) ----
        "shield_resist_phys",        # ShieldsTotal.Resistance.Physical.Maximum
        "shield_resist_energy",      # ShieldsTotal.Resistance.Energy.Maximum
        "shield_resist_distortion",  # ShieldsTotal.Resistance.Distortion.Maximum
        "shield_regen_delay",        # ShieldsTotal.RegenerationTime
        # ---- Boost / Afterburner ----
        "boost_regen_time",      # Afterburner.RegenTime
        "boost_regen_delay",     # Afterburner.CapacitorRegenDelayAfterUse
        # ---- Dissipation / Énergie ----
        "cooling_cap",
        "cooling_used_pct",
        "power_cap",
        "power_used",
        # ---- Segments d'énergie par groupe (Power.MaxSegments) ----
        "power_seg_flight",       # FlightController (propulsion / blade)
        "power_seg_weapon",       # WeaponGun  (arrondi au sup)
        "power_seg_radar",        # Radar
        "power_seg_cooler",       # Cooler
        "power_seg_shield",       # Shield
        "power_seg_lifesupport",  # LifeSupportGenerator
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
        # Armure
        armor_hp: int = 0,
        armor_phys_mult: float = 1.0,
        armor_energy_mult: float = 1.0,
        armor_distortion_mult: float = 1.0,
        armor_deflect_phys: float = 0.0,
        armor_deflect_energy: float = 0.0,
        armor_ir_mult: float = 1.0,
        armor_em_mult: float = 1.0,
        armor_cs_mult: float = 1.0,
        # Boucliers (résistances)
        shield_resist_phys: float = 0.0,
        shield_resist_energy: float = 0.0,
        shield_resist_distortion: float = 0.0,
        shield_regen_delay: float = 0.0,
        # Boost
        boost_regen_time: float = 0.0,
        boost_regen_delay: float = 0.0,
        # Dissipation / Énergie
        cooling_cap: float = 0.0,
        cooling_used_pct: float = 0.0,
        power_cap: float = 0.0,
        power_used: float = 0.0,
        # Segments d'énergie par groupe
        power_seg_flight: int = 0,
        power_seg_weapon: int = 0,
        power_seg_radar: int = 0,
        power_seg_cooler: int = 0,
        power_seg_shield: int = 0,
        power_seg_lifesupport: int = 0,
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
        # Armure
        self.armor_hp = int(armor_hp) if armor_hp else 0
        self.armor_phys_mult = float(armor_phys_mult) if armor_phys_mult is not None else 1.0
        self.armor_energy_mult = float(armor_energy_mult) if armor_energy_mult is not None else 1.0
        self.armor_distortion_mult = float(armor_distortion_mult) if armor_distortion_mult is not None else 1.0
        self.armor_deflect_phys = float(armor_deflect_phys) if armor_deflect_phys else 0.0
        self.armor_deflect_energy = float(armor_deflect_energy) if armor_deflect_energy else 0.0
        self.armor_ir_mult = float(armor_ir_mult) if armor_ir_mult is not None else 1.0
        self.armor_em_mult = float(armor_em_mult) if armor_em_mult is not None else 1.0
        self.armor_cs_mult = float(armor_cs_mult) if armor_cs_mult is not None else 1.0
        # Boucliers (résistances)
        self.shield_resist_phys = float(shield_resist_phys) if shield_resist_phys else 0.0
        self.shield_resist_energy = float(shield_resist_energy) if shield_resist_energy else 0.0
        self.shield_resist_distortion = float(shield_resist_distortion) if shield_resist_distortion else 0.0
        self.shield_regen_delay = float(shield_regen_delay) if shield_regen_delay else 0.0
        # Boost
        self.boost_regen_time = float(boost_regen_time) if boost_regen_time else 0.0
        self.boost_regen_delay = float(boost_regen_delay) if boost_regen_delay else 0.0
        # Dissipation / Énergie
        self.cooling_cap = float(cooling_cap) if cooling_cap else 0.0
        self.cooling_used_pct = float(cooling_used_pct) if cooling_used_pct else 0.0
        self.power_cap = float(power_cap) if power_cap else 0.0
        self.power_used = float(power_used) if power_used else 0.0
        # Segments d'énergie par groupe
        self.power_seg_flight      = int(power_seg_flight or 0)
        self.power_seg_weapon      = int(power_seg_weapon or 0)
        self.power_seg_radar       = int(power_seg_radar or 0)
        self.power_seg_cooler      = int(power_seg_cooler or 0)
        self.power_seg_shield      = int(power_seg_shield or 0)
        self.power_seg_lifesupport = int(power_seg_lifesupport or 0)
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
        armor = data.get("Armor", {})
        resist_mult = armor.get("ResistanceMultipliers", {})
        sig_mult    = armor.get("SignalMultipliers", {})
        deflection  = armor.get("Deflection", {})
        shields_resist = shields.get("Resistance", {})
        ab = flight.get("Afterburner", {})
        cooling = data.get("Cooling", {})
        power_data = data.get("Power", {})
        manufacturer = data.get("Manufacturer", {})

        name = data.get("Name", "")
        length = data.get("Length", 0.0)
        width = data.get("Width", 0.0)
        height = data.get("Height", 0.0)

        _weapon_seg_keys = ("WeaponGun", "MissileLauncher", "BombLauncher", "WeaponDefensive")
        _weapon_seg_max = max(
            (math.ceil(power_data.get("MaxSegments", {}).get(k, 0)) for k in _weapon_seg_keys),
            default=0,
        )

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
            # Armure — source : ResistanceMultipliers (valeur nette dommages subis)
            armor_hp=armor.get("Health", 0),
            armor_phys_mult=resist_mult.get("Physical", 1.0),
            armor_energy_mult=resist_mult.get("Energy", 1.0),
            armor_distortion_mult=resist_mult.get("Distortion", 1.0),
            armor_deflect_phys=deflection.get("Physical", 0.0),
            armor_deflect_energy=deflection.get("Energy", 0.0),
            armor_ir_mult=sig_mult.get("Infrared", 1.0),
            armor_em_mult=sig_mult.get("Electromagnetic", 1.0),
            armor_cs_mult=sig_mult.get("CrossSection", 1.0),
            # Boucliers — résistances
            shield_resist_phys=shields_resist.get("Physical", {}).get("Maximum", 0.0),
            shield_resist_energy=shields_resist.get("Energy", {}).get("Maximum", 0.0),
            shield_resist_distortion=shields_resist.get("Distortion", {}).get("Maximum", 0.0),
            shield_regen_delay=shields.get("RegenerationTime", 0.0),
            # Boost / Afterburner
            boost_regen_time=ab.get("RegenTime", 0.0),
            boost_regen_delay=ab.get("CapacitorRegenDelayAfterUse", 0.0),
            # Dissipation / Énergie
            cooling_cap=cooling.get("GenerationSegments", 0.0),
            cooling_used_pct=cooling.get("UsedSegmentsShieldsPct", 0.0),
            power_cap=power_data.get("GenerationSegments", 0.0),
            power_used=power_data.get("UsedSegmentsShields", 0.0),
            # Segments d'énergie par groupe — source : Power.MaxSegments
            # WeaponGun est arrondi au supérieur car la valeur peut être décimale (ex: 3.1 → 4)
            # power_seg_weapon = max de tous les groupes armes (Gun + Missile + Bomb)
            power_seg_flight=int(power_data.get("MaxSegments", {}).get("FlightController", 0)),
            power_seg_weapon=_weapon_seg_max,
            power_seg_radar=int(power_data.get("MaxSegments", {}).get("Radar", 0)),
            power_seg_cooler=int(power_data.get("MaxSegments", {}).get("Cooler", 0)),
            power_seg_shield=int(power_data.get("MaxSegments", {}).get("Shield", 0)),
            power_seg_lifesupport=int(power_data.get("MaxSegments", {}).get("LifeSupportGenerator", 0)),
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
    def defaultload_from_sc_json(data: dict) -> list[dict]:
        """Déduit le loadout par défaut depuis un JSON SC data miner.

        Gère quatre cas :
          1. Item chassis directement éditable, type connu → composant direct.
          2. Item chassis Turret/TurretBase éditable sans enfants éditables →
             la tourelle elle-même (ex: PDC).
          3. Item chassis Turret/TurretBase éditable avec enfants éditables →
             les enfants éditables sont des armes.
          4. Item chassis NON éditable avec ClassName → composant fixe.
             - Si c'est une tourelle : aussi importer les armes dans ses ports
               (2 niveaux de profondeur : tourelle → gimbal → arme).
        """
        _GRADE = {1: "C", 2: "B", 3: "A", 4: "A"}

        results = []
        slot_counters: dict[tuple, int] = defaultdict(int)
        # Compteur séparé pour les sous-slots d'armes de tourelle
        # Clé : (category, subtype_name, parent_subtype_name)
        sub_slot_counters: dict[tuple, int] = defaultdict(int)

        def _resolve_type(sc_type_raw: str):
            """Cherche dans SC_TYPE_TO_SLOT : full-type d'abord, base ensuite."""
            return (
                SC_TYPE_TO_SLOT.get(sc_type_raw)
                or SC_TYPE_TO_SLOT.get(sc_type_raw.split(".")[0])
            )

        def _append(comp_item: dict, size: int, sc_type_raw: str,
                    parent_subtype: str | None = None) -> None:
            class_name = comp_item.get("ClassName", "")
            if not class_name:
                return
            mapping = _resolve_type(sc_type_raw)
            if not mapping:
                return
            category, base_subtype = mapping
            subtype_name = f"{base_subtype} S{size}"

            if parent_subtype:
                key = (category, subtype_name, parent_subtype)
                slot_number = sub_slot_counters[key]
                sub_slot_counters[key] += 1
            else:
                key2 = (category, subtype_name)
                slot_number = slot_counters[key2]
                slot_counters[key2] += 1

            results.append({
                "component_class": class_name.upper(),
                "component_name":  comp_item.get("Name") or class_name,
                "manufacturer":    comp_item.get("ManufacturerName", ""),
                "sc_type":         comp_item.get("Type", sc_type_raw),
                "category":        category,
                "subtype_name":    subtype_name,
                "parent_subtype":  parent_subtype,
                "max_size":        size,
                "grade_num":       int(comp_item.get("Grade") or 1),
                "grade":           _GRADE.get(int(comp_item.get("Grade") or 1), "C"),
                "slot_number":     slot_number,
            })

        def _process_children(parent: dict, parent_max_size: int,
                               parent_subtype: str | None = None) -> None:
            """Parcourt les enfants directs d'un item (armes éditables)."""
            for child in parent.get("Loadout", []):
                if not child.get("Editable", False):
                    continue
                child_type = child.get("Type", "")
                if not _resolve_type(child_type):
                    continue
                child_size = child.get("MaxSize") or parent_max_size
                _append(child, child_size, child_type, parent_subtype)

        def _extract_turret_weapons(turret_item: dict, turret_subtype: str) -> None:
            """Extrait les armes 2 niveaux profonds : tourelle → gimbal → arme."""
            for gimbal in turret_item.get("Loadout", []):
                g_type_base = gimbal.get("Type", "").split(".")[0]
                if g_type_base not in ("Turret", "TurretBase", "WeaponGun"):
                    continue
                gimbal_size = gimbal.get("MaxSize", 0)
                for weapon in gimbal.get("Loadout", []):
                    w_type = weapon.get("Type", "")
                    if not _resolve_type(w_type):
                        continue
                    w_size = weapon.get("MaxSize") or gimbal_size
                    if not w_size:
                        continue
                    _append(weapon, w_size, w_type, parent_subtype=turret_subtype)

        for item in data.get("Loadout", []):
            if item.get("PortId") != item.get("RootPortId"):
                continue
            max_size = item.get("MaxSize", 0)
            if not max_size:
                continue
            sc_type_raw = item.get("Type", "")
            sc_type_base = sc_type_raw.split(".")[0]
            editable = item.get("Editable", False)
            mapping = _resolve_type(sc_type_raw)

            if editable and mapping:
                if sc_type_base in ("Turret", "TurretBase"):
                    ed_children = [c for c in item.get("Loadout", []) if c.get("Editable", False)]
                    if ed_children:
                        _process_children(item, max_size)
                    else:
                        # PDC ou tourelle sans armes éditables → la tourelle est le composant
                        _append(item, max_size, sc_type_raw)
                        # PDC : son arme fixe interne
                        category, base_subtype = mapping
                        parent_sub = f"{base_subtype} S{max_size}"
                        _extract_turret_weapons(item, parent_sub)
                else:
                    _append(item, max_size, sc_type_raw)
            elif not editable:
                has_editable_children = any(
                    c.get("Editable", False) for c in item.get("Loadout", [])
                )
                if has_editable_children:
                    _process_children(item, max_size)
                elif mapping and item.get("ClassName"):
                    _append(item, max_size, sc_type_raw)
                    # Si c'est une tourelle fixe, extraire aussi les armes dans ses ports
                    if sc_type_base in ("Turret", "TurretBase"):
                        category, base_subtype = mapping
                        parent_sub = f"{base_subtype} S{max_size}"
                        _extract_turret_weapons(item, parent_sub)

        return results

    @staticmethod
    def slots_from_sc_json(data: dict) -> list[dict]:
        """Déduit les slots du chassis depuis un JSON SC data miner.

        Retourne aussi les sous-slots d'armes pour les tourelles (2 niveaux :
        tourelle → gimbal → arme). Pour les sous-slots, max_qty = nombre PAR
        slot parent (ex: 2 armes par tourelle), et parent_subtype est défini.
        """
        slot_counts:     dict[tuple, int] = defaultdict(int)  # (cat, sub, size) → total
        sub_slot_counts: dict[tuple, int] = defaultdict(int)  # (cat, sub, size, parent) → per_parent

        def _resolve_type(sc_type_raw: str):
            return (
                SC_TYPE_TO_SLOT.get(sc_type_raw)
                or SC_TYPE_TO_SLOT.get(sc_type_raw.split(".")[0])
            )

        def _count_slot(sc_type_raw: str, size: int,
                        parent_subtype: str | None = None) -> None:
            mapping = _resolve_type(sc_type_raw)
            if not mapping:
                return
            category, base_subtype = mapping
            subtype_name = f"{base_subtype} S{size}"
            if parent_subtype:
                sub_slot_counts[(category, subtype_name, size, parent_subtype)] += 1
            else:
                slot_counts[(category, subtype_name, size)] += 1

        def _extract_turret_weapon_slots(item: dict, parent_subtype: str) -> None:
            """Compte les armes 2 niveaux profonds : tourelle → gimbal → arme."""
            seen: set[tuple] = set()
            for gimbal in item.get("Loadout", []):
                g_type_base = gimbal.get("Type", "").split(".")[0]
                if g_type_base not in ("Turret", "TurretBase", "WeaponGun"):
                    continue
                gimbal_size = gimbal.get("MaxSize", 0)
                for weapon in gimbal.get("Loadout", []):
                    w_type = weapon.get("Type", "")
                    mapping = _resolve_type(w_type)
                    if not mapping:
                        continue
                    w_size = weapon.get("MaxSize") or gimbal_size
                    if not w_size:
                        continue
                    key = (w_type, w_size)
                    if key not in seen:
                        seen.add(key)
                    _count_slot(w_type, w_size, parent_subtype)

        for item in data.get("Loadout", []):
            if item.get("PortId") != item.get("RootPortId"):
                continue
            max_size = item.get("MaxSize", 0)
            if not max_size:
                continue

            editable = item.get("Editable", False)
            sc_type_raw = item.get("Type", "")
            sc_type_base = sc_type_raw.split(".")[0]

            if editable:
                # Priorité : type de l'item lui-même (plus spécifique, ex: Turret.PDCTurret)
                # puis CompatibleTypes[0] comme fallback
                mapping = _resolve_type(sc_type_raw)
                if not mapping:
                    compat = item.get("CompatibleTypes", [])
                    compat_type = compat[0].get("Type", "") if compat else ""
                    mapping = _resolve_type(compat_type)
                if not mapping:
                    continue
                category, base_subtype = mapping
                resolved_base = sc_type_raw.split(".")[0]

                if resolved_base in ("Turret", "TurretBase"):
                    ed_children = [c for c in item.get("Loadout", []) if c.get("Editable", False)]
                    if ed_children:
                        for child in ed_children:
                            child_size = child.get("MaxSize") or max_size
                            _count_slot(child.get("Type", ""), child_size)
                    else:
                        _count_slot(sc_type_raw, max_size)
                        parent_sub = f"{base_subtype} S{max_size}"
                        _extract_turret_weapon_slots(item, parent_sub)
                else:
                    _count_slot(sc_type_raw, max_size)
            else:
                has_editable_children = any(
                    c.get("Editable", False) for c in item.get("Loadout", [])
                )
                if has_editable_children:
                    for child in item.get("Loadout", []):
                        if not child.get("Editable", False):
                            continue
                        child_type = child.get("Type", "")
                        if not _resolve_type(child_type):
                            continue
                        child_size = child.get("MaxSize") or max_size
                        _count_slot(child_type, child_size)
                elif _resolve_type(sc_type_raw) and item.get("ClassName"):
                    _count_slot(sc_type_raw, max_size)
                    if sc_type_base in ("Turret", "TurretBase"):
                        mapping = _resolve_type(sc_type_raw)
                        category, base_subtype = mapping
                        parent_sub = f"{base_subtype} S{max_size}"
                        _extract_turret_weapon_slots(item, parent_sub)

        results = [
            {
                "category":       category,
                "subtype_name":   subtype_name,
                "max_qty":        count,
                "max_size":       max_size,
                "parent_subtype": None,
            }
            for (category, subtype_name, max_size), count in sorted(slot_counts.items())
        ]
        # Ajouter les sous-slots d'armes de tourelle (max_qty = per parent)
        for (category, subtype_name, max_size, parent_subtype), per_parent in sorted(sub_slot_counts.items()):
            # Dédupliquer : on stocke le maximum observé par parent (ex: 2 armes / tourelle)
            # per_parent est en réalité le total accumulé — on divise par le nombre de parents
            parent_count = slot_counts.get((category.replace("WEAPON", "WEAPON"), parent_subtype.rsplit(" S", 1)[0], int(parent_subtype.rsplit("S", 1)[-1])), 1)
            # Chercher le parent_count depuis slot_counts
            parent_key = next(
                (k for k in slot_counts if k[1] == parent_subtype), None
            )
            if parent_key:
                parent_count = slot_counts[parent_key]
            qty_per_parent = per_parent // parent_count if parent_count else per_parent
            results.append({
                "category":       category,
                "subtype_name":   subtype_name,
                "max_qty":        qty_per_parent,
                "max_size":       max_size,
                "parent_subtype": parent_subtype,
            })
        return results

    @property
    def total_power_draw(self):
        return sum(float(c.stats.get("power_draw", 0)) for c in self.components)

    @property
    def total_shields(self):
        """Bouclier total : valeur importée du JSON ou calculée depuis les composants."""
        if self.shield_hp:
            return self.shield_hp
        return sum(float(c.stats.get("shield_hp", 0)) for c in self.components if c.category == "SYSTEMS")

