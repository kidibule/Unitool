"""Modèle Component — représente un composant de vaisseau."""

from models.base_model import BaseModel


class Component(BaseModel):
    """Entité métier pour un composant (arme, système, propulsion, etc.).

    Les colonnes sont séparées en deux blocs bien distincts :
      • Identification  — nom, marque, type, catégorie, taille, grade
      • Stats propres   — statistiques spécifiques au composant (pas du ship)
    """

    # -----------------------------------------------------------------------
    # Colonnes DB (dans cet ordre exact pour SELECT/INSERT)
    # -----------------------------------------------------------------------
    COLUMNS = [
        # ── Identification ──────────────────────────────────────────────────
        "name",
        "brand",
        "type_name",
        "category",
        "size",
        "grade",
        "specialization",       # profil du composant : Military / Civilian / Industrial / Stealth
        # ── Stats universels (tous composants) ──────────────────────────────
        "stat_power_draw",          # consommation électrique (segments)
        "stat_em_gen",              # génération EM
        "stat_heat_gen",            # génération thermique
        # ── Armes (GUN / TURRET) ────────────────────────────────────────────
        "stat_dps",                 # DPS pilot
        "stat_alpha",               # dommage par tir
        "stat_range",               # portée (m)
        "stat_fire_rate",           # cadence (rps)
        "stat_ammo_count",          # munitions
        # ── Missiles / racks ────────────────────────────────────────────────
        "stat_dmg",                 # dommage par missile
        # ── Boucliers ───────────────────────────────────────────────────────
        "stat_shield_hp",           # HP bouclier
        "stat_shield_regen",        # régén /s
        "stat_regen_delay",         # délai avant régén (s)
        # ── Générateur d'énergie ────────────────────────────────────────────
        "stat_power_output",        # sortie électrique (segments)
        # ── Refroidisseur ───────────────────────────────────────────────────
        "stat_cooling_rate",        # taux de refroidissement (segments/s)
        # ── Quantum Drive ───────────────────────────────────────────────────
        "stat_qt_range",            # portée QT (m)
        "stat_qt_speed",            # vitesse QT (m/s)
        "stat_qt_spool",            # temps d'amorçage (s)
        "stat_qt_fuel_usage",       # consommation carburant QT
        # ── Radar ───────────────────────────────────────────────────────────
        "stat_detection_range",     # portée détection (m)
        # ── Bouclier étendu ─────────────────────────────────────────────────
        "stat_shield_downed_delay", # délai de régén après destruction totale (s)
        "stat_shield_decay_ratio",  # ratio de décroissance des HP (0–1)
        "stat_absorption_phys",     # absorption max dégâts physiques (0–1)
        "stat_resistance_phys",     # résistance max dégâts physiques (0–1)
        "stat_resistance_dist",     # résistance max distorsion (0–1)
        # ── Armes — détail dégâts ───────────────────────────────────────────
        "stat_dmg_phys",            # dégâts physiques par tir
        "stat_dmg_energy",          # dégâts énergie par tir
        "stat_dmg_distortion",      # dégâts distorsion par tir
        "stat_projectile_speed",    # vitesse projectile (m/s)
        "stat_fire_mode",           # mode de tir (Single/Burst/Charge)
    ]

    def __init__(
        self,
        name: str,
        brand: str = "UNKNOWN",
        type_name: str = "UNKNOWN",
        category: str = "SYSTEMS",
        size: int = 1,
        grade: str = "C",
        specialization: str = "",
        # Stats universels
        stat_power_draw: float = 0.0,
        stat_em_gen: float = 0.0,
        stat_heat_gen: float = 0.0,
        # Armes gun/turret
        stat_dps: float = 0.0,
        stat_alpha: float = 0.0,
        stat_range: float = 0.0,
        stat_fire_rate: float = 0.0,
        stat_ammo_count: int = 0,
        # Missiles
        stat_dmg: float = 0.0,
        # Boucliers
        stat_shield_hp: int = 0,
        stat_shield_regen: float = 0.0,
        stat_regen_delay: float = 0.0,
        # Énergie
        stat_power_output: float = 0.0,
        # Refroidisseur
        stat_cooling_rate: float = 0.0,
        # Quantum Drive
        stat_qt_range: float = 0.0,
        stat_qt_speed: float = 0.0,
        stat_qt_spool: float = 0.0,
        stat_qt_fuel_usage: float = 0.0,
        # Radar
        stat_detection_range: float = 0.0,
        # Bouclier étendu
        stat_shield_downed_delay: float = 0.0,
        stat_shield_decay_ratio: float = 0.0,
        stat_absorption_phys: float = 0.0,
        stat_resistance_phys: float = 0.0,
        stat_resistance_dist: float = 0.0,
        # Armes — détail dégâts
        stat_dmg_phys: float = 0.0,
        stat_dmg_energy: float = 0.0,
        stat_dmg_distortion: float = 0.0,
        stat_projectile_speed: float = 0.0,
        stat_fire_mode: str = "",
        # Compat legacy (ignoré)
        stats=None,
    ):
        self.name      = (name or "UNKNOWN").upper()
        self.brand     = (brand or "UNKNOWN").upper()
        self.type_name = (type_name or "UNKNOWN").upper()
        self.category  = (category or "SYSTEMS").upper()
        self.size      = int(size) if size else 1
        self.grade     = (grade or "C").upper()
        self.specialization = (specialization or "").strip().title()
        # Stats universels
        self.stat_power_draw = float(stat_power_draw or 0)
        self.stat_em_gen     = float(stat_em_gen or 0)
        self.stat_heat_gen   = float(stat_heat_gen or 0)
        # Armes
        self.stat_dps        = float(stat_dps or 0)
        self.stat_alpha      = float(stat_alpha or 0)
        self.stat_range      = float(stat_range or 0)
        self.stat_fire_rate  = float(stat_fire_rate or 0)
        self.stat_ammo_count = int(stat_ammo_count or 0)
        # Missiles
        self.stat_dmg        = float(stat_dmg or 0)
        # Boucliers
        self.stat_shield_hp    = int(stat_shield_hp or 0)
        self.stat_shield_regen = float(stat_shield_regen or 0)
        self.stat_regen_delay  = float(stat_regen_delay or 0)
        # Énergie
        self.stat_power_output = float(stat_power_output or 0)
        # Refroidisseur
        self.stat_cooling_rate = float(stat_cooling_rate or 0)
        # Quantum Drive
        self.stat_qt_range     = float(stat_qt_range or 0)
        self.stat_qt_speed     = float(stat_qt_speed or 0)
        self.stat_qt_spool     = float(stat_qt_spool or 0)
        self.stat_qt_fuel_usage = float(stat_qt_fuel_usage or 0)
        # Radar
        self.stat_detection_range = float(stat_detection_range or 0)
        # Bouclier étendu
        self.stat_shield_downed_delay = float(stat_shield_downed_delay or 0)
        self.stat_shield_decay_ratio  = float(stat_shield_decay_ratio or 0)
        self.stat_absorption_phys     = float(stat_absorption_phys or 0)
        self.stat_resistance_phys     = float(stat_resistance_phys or 0)
        self.stat_resistance_dist     = float(stat_resistance_dist or 0)
        # Armes — détail dégâts
        self.stat_dmg_phys         = float(stat_dmg_phys or 0)
        self.stat_dmg_energy       = float(stat_dmg_energy or 0)
        self.stat_dmg_distortion   = float(stat_dmg_distortion or 0)
        self.stat_projectile_speed = float(stat_projectile_speed or 0)
        self.stat_fire_mode        = str(stat_fire_mode or "")

    # -----------------------------------------------------------------------
    # Sérialisation DB
    # -----------------------------------------------------------------------
    @classmethod
    def from_db_row(cls, row: tuple) -> "Component | None":
        """Construit depuis un tuple SELECT … (colonnes dans l'ordre COLUMNS)."""
        if not row:
            return None
        data = dict(zip(cls.COLUMNS, row))
        return cls(**{k: data.get(k) for k in cls.COLUMNS})

    def to_db_tuple(self) -> tuple:
        return tuple(getattr(self, col) for col in self.COLUMNS)

    # -----------------------------------------------------------------------
    # Import SC data miner (fichier JSON individual item)
    # -----------------------------------------------------------------------
    @classmethod
    def from_sc_item_json(cls, data: dict) -> "Component | None":
        """Construit un Component depuis un fichier JSON SC data miner (item individuel).

        Compatible avec le format exporté par le data miner SC :
            { "Item": { "name": ..., "type": ..., "stdItem": { "Shield": {...}, ... } } }
        """
        item = data.get("Item", {})
        if not item:
            return None

        std = item.get("stdItem", {})

        name = (item.get("name") or "").strip().upper()
        if not name or "PLACEHOLDER" in name:
            return None

        manufacturer_code = (item.get("manufacturer") or "UNKNOWN").strip().upper()
        size = int(item.get("size") or std.get("Size") or 1)
        grade_num = int(item.get("grade") or std.get("Grade") or 3)
        grade = {1: "A", 2: "B", 3: "C", 4: "D"}.get(grade_num, "C")
        sc_type = (item.get("type") or "").strip()

        # Mapping SC type → (category DB, type_name DB)
        _SC_TYPE_MAP = {
            "Shield":           ("SYSTEMS",    "SHIELD"),
            "PowerPlant":       ("SYSTEMS",    "POWER PLANT"),
            "Cooler":           ("SYSTEMS",    "COOLER"),
            "Radar":            ("SYSTEMS",    "RADAR"),
            "FlightController": ("SYSTEMS",    "FLIGHT BLADE"),
            "QuantumDrive":     ("PROPULSION", "QUANTUM DRIVE"),
            "WeaponGun":        ("WEAPON",     "GUN"),
            "Turret":           ("WEAPON",     "GUN"),
            "MissileLauncher":  ("WEAPON",     "MISSILE RACK"),
            "WeaponMining":     ("MODULE",     "MINING LASER"),
        }
        category, type_name = _SC_TYPE_MAP.get(sc_type, ("SYSTEMS", sc_type.upper() or "UNDEFINED"))

        # ── Stats universels ─────────────────────────────────────────────
        power_draw = 0.0
        em_gen = 0.0
        rn = std.get("ResourceNetwork", {})
        for state in (rn.get("States") or []):
            for delta in (state.get("Deltas") or []):
                if delta.get("Resource") == "Power":
                    power_draw = float(delta.get("Rate") or 0)
                    break
        emission = std.get("Emission", {})
        em_gen = float((emission.get("Em") or {}).get("Maximum") or 0)

        # ── Bouclier ─────────────────────────────────────────────────────
        shield_hp = shield_regen = regen_delay = downed_delay = 0.0
        decay_ratio = absorption_phys = resistance_phys = resistance_dist = 0.0
        sh = std.get("Shield", {})
        if sh:
            shield_hp       = float(sh.get("MaxShieldHealth") or 0)
            shield_regen    = float(sh.get("MaxShieldRegen") or 0)
            regen_delay     = float(sh.get("DamagedDelay") or 0)
            downed_delay    = float(sh.get("DownedDelay") or 0)
            decay_ratio     = float(sh.get("DecayRatio") or 0)
            absorption_phys = float((sh.get("Absorption") or {}).get("Physical", {}).get("Maximum") or 0)
            resistance_phys = float((sh.get("Resistance") or {}).get("Physical", {}).get("Maximum") or 0)
            resistance_dist = float((sh.get("Resistance") or {}).get("Distortion", {}).get("Maximum") or 0)

        # ── Énergie ──────────────────────────────────────────────────────
        power_output = 0.0
        pp = std.get("PowerPlant", {})
        if pp:
            power_output = float(pp.get("Output") or 0)
        if not power_output:
            # JSON SC data miner : sortie dans ResourceNetwork.Generation.Power
            power_output = float((rn.get("Generation") or {}).get("Power") or 0)

        # ── Refroidisseur ────────────────────────────────────────────────
        cooling_rate = 0.0
        co = std.get("Cooler", {})
        if co:
            cooling_rate = float(co.get("CoolingRate") or 0)
        if not cooling_rate:
            # JSON SC data miner : taux dans ResourceNetwork.Generation.Coolant
            rn_gen = rn.get("Generation", {})
            if rn_gen.get("Coolant"):
                cooling_rate = float(rn_gen["Coolant"])
            else:
                # Fallback : chercher dans les Deltas (GeneratedResource == "Coolant")
                for state in (rn.get("States") or []):
                    for delta in (state.get("Deltas") or []):
                        if delta.get("GeneratedResource") == "Coolant":
                            cooling_rate = float(delta.get("GeneratedRate") or 0)
                            break

        # ── Quantum Drive ────────────────────────────────────────────────
        qt_range = qt_speed = qt_spool = qt_fuel = 0.0
        qd = std.get("QuantumDrive", {})
        if qd:
            sj = qd.get("StandardJump") or {}
            qt_speed  = float(sj.get("DriveSpeed") or qd.get("Speed") or 0)
            qt_spool  = float(sj.get("SpoolUpTime") or qd.get("SpoolTime") or 0)
            # Efficiency en Gm/SCU (ou FuelEfficiencyGMPerSCU si présent)
            qt_range  = float(qd.get("FuelEfficiencyGMPerSCU") or qd.get("Range") or 0)
            # Consommation en SCU/Gm
            qt_fuel   = float(qd.get("FuelConsumptionSCUPerGM") or qd.get("FuelRate") or 0)

        # ── Armes ────────────────────────────────────────────────────────
        dps = alpha = fire_rate = weapon_range = ammo_count = 0.0
        wep = std.get("Weapon", {})
        dmg_phys = dmg_energy = dmg_dist = proj_speed = 0.0
        fire_mode = ""
        if wep:
            weapon_range = float(wep.get("EffectiveRange") or 0)
            fire_rate    = float(wep.get("RateOfFire") or 0)
            fire_mode    = (wep.get("FireMode") or "").strip()
            dmg          = wep.get("Damage") or {}
            alpha        = float(dmg.get("AlphaTotal") or 0)
            dps          = float(dmg.get("DpsTotal") or dmg.get("Burst") or dmg.get("Sustained") or 0)
            alpha_detail = dmg.get("Alpha") or {}
            dmg_phys     = float(alpha_detail.get("Physical") or 0)
            dmg_energy   = float(alpha_detail.get("Energy") or 0)
            dmg_dist     = float(alpha_detail.get("Distortion") or 0)
            capacity     = (
                (wep.get("Capacitor") or {}).get("MaxAmmoLoad")
                or wep.get("MaxAmmoLoad")
                or wep.get("Capacity")
                or 0
            )
            ammo_count   = float(capacity) if capacity else 0.0
            # vitesse projectile depuis Ammunition
            ammo_data    = std.get("Ammunition") or {}
            proj_speed   = float(ammo_data.get("Speed") or 0)

        # ── Radar ────────────────────────────────────────────────────────
        detection_range = 0.0
        rd = std.get("Radar", {}) or std.get("Sensor", {})
        if rd:
            # Portée explicite si présente, sinon sensibilité EM (0-1) * 10000 comme proxy
            detection_range = float(
                rd.get("Range")
                or rd.get("DetectionRange")
                or (rd.get("Sensitivity") or {}).get("EM", 0) * 10000
                or 0
            )

        return cls(
            name=name,
            brand=manufacturer_code,
            type_name=type_name,
            category=category,
            size=size,
            grade=grade,
            stat_power_draw=power_draw,
            stat_em_gen=em_gen,
            stat_dps=dps,
            stat_alpha=alpha,
            stat_range=weapon_range,
            stat_fire_rate=fire_rate,
            stat_ammo_count=int(ammo_count),
            stat_shield_hp=int(shield_hp),
            stat_shield_regen=shield_regen,
            stat_regen_delay=regen_delay,
            stat_shield_downed_delay=downed_delay,
            stat_shield_decay_ratio=decay_ratio,
            stat_absorption_phys=absorption_phys,
            stat_resistance_phys=resistance_phys,
            stat_resistance_dist=resistance_dist,
            stat_power_output=power_output,
            stat_cooling_rate=cooling_rate,
            stat_qt_range=qt_range,
            stat_qt_speed=qt_speed,
            stat_qt_spool=qt_spool,
            stat_qt_fuel_usage=qt_fuel,
            stat_detection_range=detection_range,
            stat_dmg_phys=dmg_phys,
            stat_dmg_energy=dmg_energy,
            stat_dmg_distortion=dmg_dist,
            stat_projectile_speed=proj_speed,
            stat_fire_mode=fire_mode,
        )

    # -----------------------------------------------------------------------
    # Compat legacy (ancienne API)
    # -----------------------------------------------------------------------
    @classmethod
    def from_db(cls, row) -> "Component | None":
        """Ancienne API — conservée pour ne pas casser le code existant."""
        if not row:
            return None
        # L'ancienne table avait : id, name, brand, type_name, category, size, grade, stats
        return cls(
            name=row[1] if len(row) > 1 else "",
            brand=row[2] if len(row) > 2 else "",
            type_name=row[3] if len(row) > 3 else "",
            category=row[4] if len(row) > 4 else "",
            size=row[5] if len(row) > 5 else 1,
            grade=row[6] if len(row) > 6 else "C",
        )
