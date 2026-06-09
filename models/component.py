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
    ]

    def __init__(
        self,
        name: str,
        brand: str = "UNKNOWN",
        type_name: str = "UNKNOWN",
        category: str = "SYSTEMS",
        size: int = 1,
        grade: str = "C",
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
        # Compat legacy (ignoré)
        stats=None,
    ):
        self.name      = (name or "UNKNOWN").upper()
        self.brand     = (brand or "UNKNOWN").upper()
        self.type_name = (type_name or "UNKNOWN").upper()
        self.category  = (category or "SYSTEMS").upper()
        self.size      = int(size) if size else 1
        self.grade     = (grade or "C").upper()
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
