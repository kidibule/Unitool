"""Système de migrations versionnées pour UNITOOL.

Principe :
  - Une table `schema_version` stocke le numéro de la dernière migration appliquée.
  - Les migrations sont des fonctions numérotées appliquées dans l'ordre.
  - Chaque migration n'est appliquée qu'une seule fois.
  - Les erreurs sont loguées clairement — plus de try/except silencieux.

Pour ajouter une migration :
  1. Écrire une nouvelle fonction _mXXX_description(cursor)
  2. L'ajouter à la fin de la liste MIGRATIONS
  3. Ne jamais modifier une migration déjà déployée — toujours en ajouter une nouvelle
"""

import logging

logger = logging.getLogger("unitool.migrations")

# ---------------------------------------------------------------------------
# Données de référence (seed)
# ---------------------------------------------------------------------------

_SHIP_ROLE_OPTIONS = [
    "LIGHT FIGHTER", "MEDIUM FIGHTER", "HEAVY FIGHTER", "STEALTH FIGHTER",
    "INTERDICTOR", "INTERCEPTOR", "GUNSHIP", "BOMBER", "DROPSHIP", "MINELAYER",
    "SNUB FIGHTER", "LIGHT FREIGHT", "MEDIUM FREIGHT", "HEAVY FREIGHT",
    "CARGO", "TRANSPORT", "PASSENGER", "LUXURY", "REFUEL", "PATHFINDER",
    "EXPEDITION", "TOURING", "SCIENCE", "RESEARCH", "REPORTING", "DATA",
    "PROSPECTING", "MINING", "SALVAGE", "REPAIR", "REFINING", "MEDICAL",
    "CONSTRUCTION", "RACING", "MODULAR", "STARTER", "CORVETTE", "FRIGATE",
    "DESTROYER", "CARRIER",
]

_SHIP_CAREER_OPTIONS = [
    "COMBAT", "TRANSPORT", "EXPLORATION", "INDUSTRIAL",
    "SCIENCE", "COMPETITION", "SUPPORT", "INTERDICTION",
]

# ---------------------------------------------------------------------------
# Utilitaires internes
# ---------------------------------------------------------------------------

def _get_version(cursor) -> int:
    """Retourne le numéro de la dernière migration appliquée (0 si aucune)."""
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )
    row = cursor.execute("SELECT version FROM schema_version").fetchone()
    return row[0] if row else 0


def _set_version(cursor, version: int) -> None:
    """Enregistre le numéro de la migration qui vient d'être appliquée."""
    cursor.execute("DELETE FROM schema_version")
    cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))


def _column_exists(cursor, table: str, column: str) -> bool:
    """Vérifie si une colonne existe dans une table."""
    cols = [
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()
    ]
    return column in cols


def _add_column_if_missing(cursor, table: str, column: str, col_type: str) -> None:
    """Ajoute une colonne uniquement si elle est absente. Logue le résultat."""
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        logger.info(f"  Column added: {table}.{column}")
    else:
        logger.debug(f"  Column already present (skipped): {table}.{column}")


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------

def _m001_schema_initial(cursor):
    """Crée toutes les tables de base avec leur schéma complet et à jour.

    Les bases fraîches obtiennent d'emblée le schéma final — elles n'ont donc
    pas besoin des migrations suivantes (ADD COLUMN), qui ne servent qu'aux
    bases legacy créées avant le système de versioning.
    """
    # --- Targets ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            pseudo         TEXT PRIMARY KEY,
            org            TEXT,
            ship           TEXT,
            threat         TEXT,
            notes          TEXT,
            date           TEXT,
            wins           INTEGER DEFAULT 0,
            losses         INTEGER DEFAULT 0,
            alignment      TEXT DEFAULT 'NEUTRAL',
            pvp_lvl        TEXT DEFAULT 'UNKNOWN',
            activity       TEXT DEFAULT 'UNKNOWN',
            sid            TEXT DEFAULT 'N/A',
            org_rank       TEXT DEFAULT 'N/A',
            enlisted_date  TEXT DEFAULT 'N/A',
            language       TEXT DEFAULT 'N/A',
            affiliates     TEXT DEFAULT 'NONE'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS target_notes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            target_pseudo TEXT NOT NULL,
            note_text     TEXT NOT NULL,
            created_at    TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_target_notes_pseudo ON target_notes(target_pseudo)"
    )

    # --- Organizations ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            org_sid    TEXT NOT NULL,
            note_text  TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_notes_sid ON org_notes(org_sid)"
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            sid              TEXT PRIMARY KEY,
            name             TEXT,
            tag              TEXT,
            description      TEXT,
            member_count     INTEGER DEFAULT 0,
            visible_members  TEXT DEFAULT '[]',
            redacted_members TEXT DEFAULT '[]',
            ranks            TEXT DEFAULT '{}',
            org_type         TEXT DEFAULT 'ORGANIZATION',
            specialization   TEXT DEFAULT 'GENERAL',
            allies           TEXT DEFAULT '',
            enemies          TEXT DEFAULT '',
            neutrals         TEXT DEFAULT '',
            updated_at       TEXT,
            alignment        TEXT DEFAULT 'NEUTRAL'
        )
    """)

    # --- Contracts ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            target        TEXT,
            client        TEXT,
            reward        TEXT,
            status        TEXT DEFAULT 'OPEN',
            date          TEXT,
            priority      TEXT DEFAULT 'MEDIUM',
            contract_type TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_types (
            name   TEXT PRIMARY KEY,
            reward TEXT
        )
    """)

    # --- Ships ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ships (
            name                TEXT PRIMARY KEY,
            brand               TEXT,
            role                TEXT,
            career              TEXT,
            size                INTEGER DEFAULT 0,
            crew_size           INTEGER DEFAULT 0,
            length              REAL DEFAULT 0,
            width               REAL DEFAULT 0,
            height              REAL DEFAULT 0,
            mass                REAL DEFAULT 0,
            mass_total          REAL DEFAULT 0,
            scm_speed           REAL DEFAULT 0,
            scm_boost_forward   REAL DEFAULT 0,
            scm_boost_backward  REAL DEFAULT 0,
            nav_max_speed       REAL DEFAULT 0,
            pitch               REAL DEFAULT 0,
            yaw                 REAL DEFAULT 0,
            roll                REAL DEFAULT 0,
            boosted_pitch       REAL DEFAULT 0,
            boosted_yaw         REAL DEFAULT 0,
            boosted_roll        REAL DEFAULT 0,
            accel_main          REAL DEFAULT 0,
            accel_retro         REAL DEFAULT 0,
            accel_maneuver      REAL DEFAULT 0,
            accel_main_boosted  REAL DEFAULT 0,
            hydrogen_capacity   REAL DEFAULT 0,
            fuel_intake_rate    REAL DEFAULT 0,
            fuel_usage_main     REAL DEFAULT 0,
            qt_fuel_capacity    REAL DEFAULT 0,
            qt_range            REAL DEFAULT 0,
            qt_speed            REAL DEFAULT 0,
            qt_spool_time       REAL DEFAULT 0,
            hp                  INTEGER DEFAULT 0,
            shield_hp           INTEGER DEFAULT 0,
            shield_regen        REAL DEFAULT 0,
            pilot_dps           REAL DEFAULT 0,
            pilot_alpha         REAL DEFAULT 0,
            pilot_sustained_dps REAL DEFAULT 0,
            missiles_count      INTEGER DEFAULT 0,
            missiles_damage     REAL DEFAULT 0,
            emission_ir         REAL DEFAULT 0,
            emission_em         REAL DEFAULT 0,
            cargo               REAL DEFAULT 0,
            expedition_fee      REAL DEFAULT 0,
            claim_time          REAL DEFAULT 0,
            expedite_time       REAL DEFAULT 0,
            sc_uuid             TEXT DEFAULT '',
            sc_class_name       TEXT DEFAULT '',
            -- Armure
            armor_hp            INTEGER DEFAULT 0,
            armor_phys_mult     REAL DEFAULT 1,
            armor_energy_mult   REAL DEFAULT 1,
            armor_distortion_mult REAL DEFAULT 1,
            armor_deflect_phys  REAL DEFAULT 0,
            armor_deflect_energy REAL DEFAULT 0,
            armor_ir_mult       REAL DEFAULT 1,
            armor_em_mult       REAL DEFAULT 1,
            armor_cs_mult       REAL DEFAULT 1,
            -- Boucliers (résistances)
            shield_resist_phys        REAL DEFAULT 0,
            shield_resist_energy      REAL DEFAULT 0,
            shield_resist_distortion  REAL DEFAULT 0,
            shield_regen_delay        REAL DEFAULT 0,
            -- Boost / Afterburner
            boost_regen_time    REAL DEFAULT 0,
            boost_regen_delay   REAL DEFAULT 0,
            -- Dissipation / Énergie
            cooling_cap         REAL DEFAULT 0,
            cooling_used_pct    REAL DEFAULT 0,
            power_cap           REAL DEFAULT 0,
            power_used          REAL DEFAULT 0,
            dimensions          TEXT DEFAULT '',
            power_consumption   TEXT DEFAULT '',
            cm_decoy_noise      TEXT DEFAULT '',
            sc_data_json        TEXT DEFAULT ''
        )
    """)

    cursor.execute("CREATE TABLE IF NOT EXISTS ship_roles (name TEXT PRIMARY KEY)")
    cursor.executemany(
        "INSERT OR IGNORE INTO ship_roles (name) VALUES (?)",
        [(r,) for r in _SHIP_ROLE_OPTIONS],
    )
    cursor.execute("CREATE TABLE IF NOT EXISTS ship_careers (name TEXT PRIMARY KEY)")
    cursor.executemany(
        "INSERT OR IGNORE INTO ship_careers (name) VALUES (?)",
        [(c,) for c in _SHIP_CAREER_OPTIONS],
    )

    # --- Components ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_categories (name TEXT PRIMARY KEY)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_types (
            name     TEXT PRIMARY KEY,
            category TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT UNIQUE,
            brand     TEXT,
            type_name TEXT,
            category  TEXT,
            size      INTEGER,
            grade     TEXT,
            -- Stats universels
            stat_power_draw       REAL DEFAULT 0,
            stat_em_gen           REAL DEFAULT 0,
            stat_heat_gen         REAL DEFAULT 0,
            -- Armes (gun / turret)
            stat_dps              REAL DEFAULT 0,
            stat_alpha            REAL DEFAULT 0,
            stat_range            REAL DEFAULT 0,
            stat_fire_rate        REAL DEFAULT 0,
            stat_ammo_count       INTEGER DEFAULT 0,
            -- Missiles / racks
            stat_dmg              REAL DEFAULT 0,
            -- Boucliers
            stat_shield_hp        INTEGER DEFAULT 0,
            stat_shield_regen     REAL DEFAULT 0,
            stat_regen_delay      REAL DEFAULT 0,
            -- Générateur d'énergie
            stat_power_output     REAL DEFAULT 0,
            -- Refroidisseur
            stat_cooling_rate     REAL DEFAULT 0,
            -- Quantum Drive
            stat_qt_range         REAL DEFAULT 0,
            stat_qt_speed         REAL DEFAULT 0,
            stat_qt_spool         REAL DEFAULT 0,
            stat_qt_fuel_usage    REAL DEFAULT 0,
            -- Radar
            stat_detection_range  REAL DEFAULT 0,
            -- Bouclier étendu
            stat_shield_downed_delay REAL DEFAULT 0,
            stat_shield_decay_ratio  REAL DEFAULT 0,
            stat_absorption_phys     REAL DEFAULT 0,
            stat_resistance_phys     REAL DEFAULT 0,
            stat_resistance_dist     REAL DEFAULT 0,
            FOREIGN KEY (type_name) REFERENCES component_types(name)
        )
    """)

    # --- Ship specs & loadout ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ship_specs (
            ship_name TEXT,
            category  TEXT,
            max_qty   INTEGER,
            max_size  INTEGER,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            PRIMARY KEY (ship_name, category)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ship_subtype_specs (
            ship_name    TEXT,
            category     TEXT,
            subtype_name TEXT,
            max_qty      INTEGER,
            max_size     INTEGER,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            PRIMARY KEY (ship_name, category, subtype_name)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ship_slots (
            ship_name    TEXT,
            slot_type    TEXT,
            slot_size    INTEGER,
            max_quantity INTEGER,
            FOREIGN KEY (ship_name) REFERENCES ships(name)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ship_loadout (
            ship_name      TEXT,
            profile_name   TEXT NOT NULL DEFAULT 'DEFAULT',
            category       TEXT,
            subtype_name   TEXT NOT NULL DEFAULT 'GENERIC',
            slot_number    INTEGER,
            component_name TEXT,
            quantity       INTEGER DEFAULT 1,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            FOREIGN KEY (component_name) REFERENCES components(name),
            PRIMARY KEY (ship_name, profile_name, category, subtype_name, slot_number)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ship_loadout_profiles (
            ship_name    TEXT,
            profile_name TEXT,
            PRIMARY KEY (ship_name, profile_name),
            FOREIGN KEY (ship_name) REFERENCES ships(name)
        )
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name)
        SELECT DISTINCT ship_name, COALESCE(NULLIF(profile_name, ''), 'DEFAULT')
        FROM ship_loadout
    """)

    # --- Player ships ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_ships (
            pseudo TEXT,
            ship   TEXT,
            PRIMARY KEY (pseudo, ship)
        )
    """)

    # --- Locations ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            name        TEXT PRIMARY KEY,
            x           REAL,
            y           REAL,
            z           REAL,
            type        TEXT DEFAULT 'POI',
            parent_name TEXT
        )
    """)


def _m002_targets_colonnes_legacy(cursor):
    """Ajoute les colonnes ajoutées progressivement à la table targets (bases legacy)."""
    _add_column_if_missing(cursor, "targets", "pvp_lvl",       "TEXT DEFAULT 'UNKNOWN'")
    _add_column_if_missing(cursor, "targets", "activity",      "TEXT DEFAULT 'UNKNOWN'")
    _add_column_if_missing(cursor, "targets", "sid",           "TEXT DEFAULT 'N/A'")
    _add_column_if_missing(cursor, "targets", "org_rank",      "TEXT DEFAULT 'N/A'")
    _add_column_if_missing(cursor, "targets", "enlisted_date", "TEXT DEFAULT 'N/A'")
    _add_column_if_missing(cursor, "targets", "language",      "TEXT DEFAULT 'N/A'")
    _add_column_if_missing(cursor, "targets", "affiliates",    "TEXT DEFAULT 'NONE'")


def _m003_organizations_colonnes_legacy(cursor):
    """Ajoute les colonnes ajoutées progressivement à la table organizations (bases legacy)."""
    _add_column_if_missing(cursor, "organizations", "org_type",       "TEXT DEFAULT 'ORGANIZATION'")
    _add_column_if_missing(cursor, "organizations", "specialization", "TEXT DEFAULT 'GENERAL'")
    _add_column_if_missing(cursor, "organizations", "allies",         "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "organizations", "enemies",        "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "organizations", "neutrals",       "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "organizations", "alignment",      "TEXT DEFAULT 'NEUTRAL'")
    _add_column_if_missing(cursor, "organizations", "updated_at",     "TEXT")


def _m004_ships_colonnes_legacy(cursor):
    """Ajoute les colonnes de stats vaisseau à la table ships (bases legacy)."""
    ship_cols = [
        ("brand",              "TEXT"),
        ("role",               "TEXT"),
        ("career",             "TEXT"),
        ("size",               "TEXT"),
        ("crew_size",          "INTEGER DEFAULT 0"),
        ("scm_speed",          "TEXT"),
        ("scm_boost_forward",  "TEXT"),
        ("scm_boost_backward", "TEXT"),
        ("nav_max_speed",      "TEXT"),
        ("pitch",              "TEXT"),
        ("yaw",                "TEXT"),
        ("roll",               "TEXT"),
        ("boosted_pitch",      "TEXT"),
        ("boosted_yaw",        "TEXT"),
        ("boosted_roll",       "TEXT"),
        ("power_consumption",  "TEXT"),
        ("cm_decoy_noise",     "TEXT"),
        ("hp",                 "INTEGER DEFAULT 0"),
        ("cargo",              "TEXT"),
        ("dimensions",         "TEXT"),
        ("mass",               "TEXT"),
        ("hydrogen_capacity",  "TEXT"),
        ("qt_fuel_capacity",   "TEXT"),
        ("expedition_fee",     "TEXT"),
        ("claim_time",         "TEXT"),
        ("expedite_time",      "TEXT"),
    ]
    for col_name, col_type in ship_cols:
        _add_column_if_missing(cursor, "ships", col_name, col_type)


def _m005_locations_colonnes_legacy(cursor):
    """Ajoute type et parent_name à la table locations (bases legacy)."""
    _add_column_if_missing(cursor, "locations", "type",        "TEXT DEFAULT 'POI'")
    _add_column_if_missing(cursor, "locations", "parent_name", "TEXT")


def _m006_loadout_rebuild_pk(cursor):
    """Reconstruit ship_loadout avec la bonne clé primaire si nécessaire (bases legacy).

    Les bases créées avant la migration 001 pouvaient avoir ship_loadout sans
    profile_name ou subtype_name dans la clé primaire. Cette migration détecte
    ce cas et reconstruit la table proprement en préservant les données.
    """
    cols = [
        row[1]
        for row in cursor.execute("PRAGMA table_info(ship_loadout)").fetchall()
    ]
    pk_cols = [
        row[1]
        for row in cursor.execute("PRAGMA table_info(ship_loadout)").fetchall()
        if row[5] > 0
    ]
    expected_pk = ["ship_name", "profile_name", "category", "subtype_name", "slot_number"]

    if "profile_name" in cols and "subtype_name" in cols and pk_cols == expected_pk:
        logger.debug("  ship_loadout: primary key already correct, nothing to do.")
        return

    logger.info("  ship_loadout: rebuilding with correct primary key...")

    cursor.execute("""
        CREATE TABLE ship_loadout_new (
            ship_name      TEXT,
            profile_name   TEXT NOT NULL DEFAULT 'DEFAULT',
            category       TEXT,
            subtype_name   TEXT NOT NULL DEFAULT 'GENERIC',
            slot_number    INTEGER,
            component_name TEXT,
            quantity       INTEGER DEFAULT 1,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            FOREIGN KEY (component_name) REFERENCES components(name),
            PRIMARY KEY (ship_name, profile_name, category, subtype_name, slot_number)
        )
    """)

    if "profile_name" in cols and "subtype_name" in cols:
        cursor.execute("""
            INSERT OR REPLACE INTO ship_loadout_new
            SELECT ship_name,
                   COALESCE(NULLIF(profile_name, ''), 'DEFAULT'),
                   category,
                   COALESCE(NULLIF(subtype_name, ''), 'GENERIC'),
                   slot_number, component_name, COALESCE(quantity, 1)
            FROM ship_loadout
        """)
    elif "profile_name" in cols:
        cursor.execute("""
            INSERT OR REPLACE INTO ship_loadout_new
            SELECT sl.ship_name,
                   COALESCE(NULLIF(sl.profile_name, ''), 'DEFAULT'),
                   sl.category,
                   COALESCE(NULLIF(c.type_name, ''), 'GENERIC'),
                   sl.slot_number, sl.component_name, COALESCE(sl.quantity, 1)
            FROM ship_loadout sl
            LEFT JOIN components c ON c.name = sl.component_name
        """)
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO ship_loadout_new
            SELECT sl.ship_name, 'DEFAULT', sl.category,
                   COALESCE(NULLIF(c.type_name, ''), 'GENERIC'),
                   sl.slot_number, sl.component_name, COALESCE(sl.quantity, 1)
            FROM ship_loadout sl
            LEFT JOIN components c ON c.name = sl.component_name
        """)

    cursor.execute("DROP TABLE ship_loadout")
    cursor.execute("ALTER TABLE ship_loadout_new RENAME TO ship_loadout")
    logger.info("  ship_loadout: rebuild complete.")


# ---------------------------------------------------------------------------
# Liste ordonnée des migrations
# Règle : ne jamais modifier une entrée existante, seulement en ajouter.
# ---------------------------------------------------------------------------

def _m007_localise_fr_to_en(cursor):
    """Replace French alignment/status values with English equivalents in existing data."""
    # targets: alignment
    cursor.execute("UPDATE targets SET alignment = 'NEUTRAL' WHERE alignment = 'NEUTRE'")
    cursor.execute("UPDATE targets SET alignment = 'ENEMY'   WHERE alignment = 'ENNEMI'")
    cursor.execute("UPDATE targets SET alignment = 'ALLY'    WHERE alignment = 'AMI'")
    # targets: pvp_lvl / activity
    cursor.execute("UPDATE targets SET pvp_lvl  = 'UNKNOWN' WHERE pvp_lvl  = 'Inconnu'")
    cursor.execute("UPDATE targets SET activity = 'UNKNOWN' WHERE activity = 'Inconnu'")
    # organizations: alignment
    cursor.execute("UPDATE organizations SET alignment = 'NEUTRAL' WHERE alignment = 'NEUTRE'")
    cursor.execute("UPDATE organizations SET alignment = 'ENEMY'   WHERE alignment = 'ENNEMI'")
    cursor.execute("UPDATE organizations SET alignment = 'ALLY'    WHERE alignment = 'AMI'")


def _m008_rename_targets_to_players(cursor):
    """Rename the targets/target_notes tables and target_pseudo column to players/player_notes/player_pseudo."""
    cursor.execute("ALTER TABLE targets RENAME TO players")
    cursor.execute("ALTER TABLE target_notes RENAME TO player_notes")
    cursor.execute("ALTER TABLE player_notes RENAME COLUMN target_pseudo TO player_pseudo")
    cursor.execute("DROP INDEX IF EXISTS idx_target_notes_pseudo")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_notes_pseudo ON player_notes(player_pseudo)")


def _m009_seed_sc_locations(cursor):
    """Upsert Star Citizen planets and moons with correct coordinates and hierarchy.

    Les planètes sont insérées en premier pour que les lunes puissent référencer
    leur parent. Les coordonnées sont en km (format natif Star Citizen).
    """
    locations = [
        # name,          x,            y,           z,      type,      parent
        # --- Planètes ---
        ("HURSTON",    12858745,          0,          0,  "PLANET",       None),
        ("ARCCORP",    18545567,  -22151149,          0,  "PLANET",       None),
        ("MICROTECH",  22935149,   29351490,          0,  "PLANET",       None),
        ("CRUSADER",  -18962172,   -2665623,          0,  "PLANET",       None),
        # --- Lunes de Hurston ---
        ("ARIAL",      12858745,          0,       3815,    "MOON",  "HURSTON"),
        ("ABERDEEN",   12858745,          0,      -3715,    "MOON",  "HURSTON"),
        ("MAGDA",      12858745,       3315,          0,    "MOON",  "HURSTON"),
        ("ITA",        12858745,      -3615,          0,    "MOON",  "HURSTON"),
        # --- Lunes d'ArcCorp ---
        ("LYRIA",      18545567,  -22151149,       3515,    "MOON",  "ARCCORP"),
        ("WALA",       18545567,  -22151149,      -3815,    "MOON",  "ARCCORP"),
        # --- Lunes de microTech ---
        ("CALLIOPE",   22935149,   29351490,       4515,    "MOON",  "MICROTECH"),
        ("CLIO",       22935149,   29351490,      -4215,    "MOON",  "MICROTECH"),
        ("EUTERPE",    22935149,      33866,          0,    "MOON",  "MICROTECH"),
        # --- Lunes de Crusader ---
        ("CELLIN",    -18962172,   -2665623,      10115,    "MOON",  "CRUSADER"),
        ("DAYMAR",    -18962172,   -2665623,     -10115,    "MOON",  "CRUSADER"),
        ("YELA",      -18962172,     -12780,          0,    "MOON",  "CRUSADER"),
    ]
    for name, x, y, z, loc_type, parent in locations:
        cursor.execute(
            """
            INSERT INTO locations (name, x, y, z, type, parent_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x           = excluded.x,
                y           = excluded.y,
                z           = excluded.z,
                type        = excluded.type,
                parent_name = excluded.parent_name
            """,
            (name, x, y, z, loc_type, parent),
        )


def _m010_locations_km_to_meters(cursor):
    """Convertit les coordonnées des locations de km en mètres.

    La migration _m009 a inséré les coordonnées en km (données Excel).
    Star Citizen utilise les mètres en interne, et COORD_UNIT = 'm'.
    On multiplie donc toutes les coordonnées par 1000.
    """
    cursor.execute("UPDATE locations SET x = x * 1000, y = y * 1000, z = z * 1000")


def _m011_locations_add_radius(cursor):
    """Ajoute la colonne radius (mètres) et seed les rayons des corps célestes SC.

    Le rayon est utilisé par l'algorithme triangle SnarePlan :
        snare_dist = (snare_range × route_length) / (2 × source_radius)
    """
    _add_column_if_missing(cursor, "locations", "radius", "REAL DEFAULT 0")

    radii = {
        # Planètes (rayon en mètres)
        "HURSTON":   1_000_000,
        "ARCCORP":   1_000_000,
        "MICROTECH": 1_000_000,
        "CRUSADER":  7_491_000,
        # Lunes de Hurston
        "ARIAL":       315_000,
        "ABERDEEN":    285_000,
        "MAGDA":       290_000,
        "ITA":         325_000,
        # Lunes d'ArcCorp
        "LYRIA":       223_000,
        "WALA":        283_000,
        # Lunes de microTech
        "CALLIOPE":    240_000,
        "CLIO":        250_000,
        "EUTERPE":     215_000,
        # Lunes de Crusader
        "CELLIN":      260_000,
        "DAYMAR":      295_000,
        "YELA":        312_000,
    }
    for name, radius in radii.items():
        cursor.execute(
            "UPDATE locations SET radius = ? WHERE name = ?",
            (radius, name),
        )


# ---------------------------------------------------------------------------
# Liste ordonnée des migrations
# Règle : ne jamais modifier une entrée existante, seulement en ajouter.
# ---------------------------------------------------------------------------

def _m012_locations_add_physics_grid(cursor):
    """Ajoute la colonne physics_grid (mètres) : rayon réel de la zone de départ d'un vaisseau.

    C'est cette valeur que SnarePlan utilise comme altitude dans la formule triangle
    quand aucune lune externe n'est disponible comme point C :
        snare_dist = snare_range × route_length / physics_grid
    """
    _add_column_if_missing(cursor, "locations", "physics_grid", "REAL DEFAULT 0")

    physics_grids = {
        # Planètes (mètres)
        "HURSTON":    2_450_000,
        "CRUSADER":  13_500_000,
        "ARCCORP":    2_200_000,
        "MICROTECH":  2_650_000,
        # Lunes de Hurston
        "ARIAL":       650_000,
        "ABERDEEN":    580_000,
        "MAGDA":       600_000,
        "ITA":         680_000,
        # Lunes de Crusader
        "CELLIN":      550_000,
        "DAYMAR":      620_000,
        "YELA":        640_000,
        # Lunes d'ArcCorp
        "LYRIA":       480_000,
        "WALA":        590_000,
        # Lunes de microTech
        "CALLIOPE":    520_000,
        "CLIO":        540_000,
        "EUTERPE":     450_000,
    }
    for name, pg in physics_grids.items():
        cursor.execute(
            "UPDATE locations SET physics_grid = ? WHERE name = ?",
            (pg, name),
        )


def _m013_fix_moon_coordinates(cursor):
    """Corrige les coordonnées erronées de certaines lunes (en mètres, post-m010).

    Problèmes identifiés :
    - YELA : Y = -12780 km (absolu) au lieu de -2665623 km (parent CRUSADER).
      Résultat : YELA apparaissait à ~2,652,843 km de CRUSADER → triangle aberrant
      → snare_dist = 239.91 km (faux).
    - DAYMAR : Z-offset = 10,115 km seulement, trop petit versus la position réelle.
      SnarePlan montre BC(Crusader-Daymar) ≈ 63,763 km avec altitude ≈ 52,559 km.
      On repositionne DAYMAR à Z = -52,559 km de CRUSADER pour correspondre.

    Toutes les valeurs ci-dessous sont en mètres (COORD_UNIT = 'm').
    """
    corrections = {
        # (x_m, y_m, z_m)
        # YELA : recalée sur le Y de CRUSADER + offset Z original -12780 km
        "YELA":   (-18_962_172_000, -2_665_623_000, -12_780_000),
        # DAYMAR : repositionné à altitude ≈ 52,559 km perpendiculaire à la route
        #          CRUSADER→HURSTON pour donner snare_dist ≈ 12,134 km (SnarePlan)
        "DAYMAR": (-18_962_172_000, -2_665_623_000, -52_559_000),
    }
    for name, (x, y, z) in corrections.items():
        cursor.execute(
            "UPDATE locations SET x = ?, y = ?, z = ? WHERE name = ?",
            (x, y, z, name),
        )


def _m014_fix_cellin_coordinates(cursor):
    """Corrige les coordonnées de CELLIN d'après les données SnarePlan.

    SnarePlan CRUSADER+CELLIN→HURSTON (raw data) :
        altitude = 42,293 km  (distance perpendiculaire à la route CRUSADER→HURSTON)
        origin range (BC) = 51,294 km

    Valeur précédente : Z = 10,115 km (placeholder symétrique de DAYMAR) → altitude
    trop faible → physics_grid de CRUSADER (13,500 km) prenait le dessus à tort.

    Coordonnée absolue en mètres (COORD_UNIT = 'm').
    """
    cursor.execute(
        "UPDATE locations SET z = ? WHERE name = ?",
        (42_293_000, "CELLIN"),
    )


def _m015_app_settings(cursor):
    """Crée la table app_settings pour les préférences utilisateur (ex: org principale)."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)


def _m016_org_events(cursor):
    """Crée la table org_events pour l'agenda de l'organisation."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS org_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)


def _m017_org_events_time(cursor):
    """Ajoute la colonne time à org_events."""
    try:
        cursor.execute("ALTER TABLE org_events ADD COLUMN time TEXT DEFAULT ''")
    except Exception:
        pass  # colonne déjà présente


def _m018_org_events_location_participants(cursor):
    """Ajoute les colonnes location et participants à org_events."""
    _add_column_if_missing(cursor, "org_events", "location",     "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "org_events", "participants", "TEXT DEFAULT ''")


def _m019_ships_sc_fields(cursor):
    """Ajoute les champs SC data miner à la table ships (bases legacy).

    Ces colonnes permettent d'importer directement les fichiers JSON produits
    par le SC data miner et de garder la compatibilité avec les futures mises
    à jour de Star Citizen — il suffira d'ajouter une nouvelle migration.
    """
    new_cols = [
        # Dimensions séparées
        ("length",              "REAL DEFAULT 0"),
        ("width",               "REAL DEFAULT 0"),
        ("height",              "REAL DEFAULT 0"),
        ("mass_total",          "REAL DEFAULT 0"),
        # Accélérations
        ("accel_main",          "REAL DEFAULT 0"),
        ("accel_retro",         "REAL DEFAULT 0"),
        ("accel_maneuver",      "REAL DEFAULT 0"),
        ("accel_main_boosted",  "REAL DEFAULT 0"),
        # Propulsion hydrogène
        ("fuel_intake_rate",    "REAL DEFAULT 0"),
        ("fuel_usage_main",     "REAL DEFAULT 0"),
        # Quantum
        ("qt_range",            "REAL DEFAULT 0"),
        ("qt_speed",            "REAL DEFAULT 0"),
        ("qt_spool_time",       "REAL DEFAULT 0"),
        # Combat / défense
        ("shield_hp",           "INTEGER DEFAULT 0"),
        ("shield_regen",        "REAL DEFAULT 0"),
        ("pilot_dps",           "REAL DEFAULT 0"),
        ("pilot_alpha",         "REAL DEFAULT 0"),
        ("pilot_sustained_dps", "REAL DEFAULT 0"),
        ("missiles_count",      "INTEGER DEFAULT 0"),
        ("missiles_damage",     "REAL DEFAULT 0"),
        # Signature électronique
        ("emission_ir",         "REAL DEFAULT 0"),
        ("emission_em",         "REAL DEFAULT 0"),
        # Identifiants SC
        ("sc_uuid",             "TEXT DEFAULT ''"),
        ("sc_class_name",       "TEXT DEFAULT ''"),
        # Raw JSON (future-proof)
        ("sc_data_json",        "TEXT DEFAULT ''"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "ships", col_name, col_type)

    # Convertir les colonnes TEXT legacy en REAL là où c'est possible.
    # SQLite ne permet pas ALTER COLUMN TYPE, on laisse les données telles quelles
    # (SQLite stocke les numériques en TEXT sans perte pour les requêtes).
    logger.info("  ships: SC data miner columns added.")


def _m020_ships_armor_cooling(cursor):
    """Ajoute les colonnes armure et dissipation/énergie à la table ships."""
    new_cols = [
        ("armor_hp",              "INTEGER DEFAULT 0"),
        ("armor_phys_mult",       "REAL DEFAULT 1"),
        ("armor_energy_mult",     "REAL DEFAULT 1"),
        ("armor_distortion_mult", "REAL DEFAULT 1"),
        ("armor_ir_mult",         "REAL DEFAULT 1"),
        ("armor_em_mult",         "REAL DEFAULT 1"),
        ("cooling_cap",           "REAL DEFAULT 0"),
        ("cooling_used_pct",      "REAL DEFAULT 0"),
        ("power_cap",             "REAL DEFAULT 0"),
        ("power_used",            "REAL DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "ships", col_name, col_type)
    logger.info("  ships: armor & cooling columns added.")


def _m021_components_typed_stats(cursor):
    """Remplace le blob stats TEXT par des colonnes typées dans components.

    Les stats sont désormais séparées par domaine :
      - stats universels  (power_draw, em_gen, heat_gen)
      - armes gun/turret  (dps, alpha, range, fire_rate, ammo_count)
      - missiles          (dmg)
      - boucliers         (shield_hp, shield_regen, regen_delay)
      - énergie           (power_output)
      - refroidisseur     (cooling_rate)
      - quantum drive     (qt_range, qt_speed, qt_spool, qt_fuel_usage)
      - radar             (detection_range)
    """
    new_cols = [
        ("stat_power_draw",      "REAL DEFAULT 0"),
        ("stat_em_gen",          "REAL DEFAULT 0"),
        ("stat_heat_gen",        "REAL DEFAULT 0"),
        ("stat_dps",             "REAL DEFAULT 0"),
        ("stat_alpha",           "REAL DEFAULT 0"),
        ("stat_range",           "REAL DEFAULT 0"),
        ("stat_fire_rate",       "REAL DEFAULT 0"),
        ("stat_ammo_count",      "INTEGER DEFAULT 0"),
        ("stat_dmg",             "REAL DEFAULT 0"),
        ("stat_shield_hp",       "INTEGER DEFAULT 0"),
        ("stat_shield_regen",    "REAL DEFAULT 0"),
        ("stat_regen_delay",     "REAL DEFAULT 0"),
        ("stat_power_output",    "REAL DEFAULT 0"),
        ("stat_cooling_rate",    "REAL DEFAULT 0"),
        ("stat_qt_range",        "REAL DEFAULT 0"),
        ("stat_qt_speed",        "REAL DEFAULT 0"),
        ("stat_qt_spool",        "REAL DEFAULT 0"),
        ("stat_qt_fuel_usage",   "REAL DEFAULT 0"),
        ("stat_detection_range", "REAL DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "components", col_name, col_type)
    logger.info("  components: typed stat columns added.")


def _m023_components_weapon_detail_stats(cursor):
    """Ajoute les colonnes de détail des dégâts armes et vitesse projectile."""
    new_cols = [
        ("stat_dmg_phys",         "REAL DEFAULT 0"),
        ("stat_dmg_energy",       "REAL DEFAULT 0"),
        ("stat_dmg_distortion",   "REAL DEFAULT 0"),
        ("stat_projectile_speed", "REAL DEFAULT 0"),
        ("stat_fire_mode",        "TEXT DEFAULT ''"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "components", col_name, col_type)
    logger.info("  components: weapon detail stat columns added.")


def _m022_components_shield_extended_stats(cursor):
    """Ajoute les colonnes de stats bouclier étendues (délai downed, décay, absorptions/résistances)."""
    new_cols = [
        ("stat_shield_downed_delay", "REAL DEFAULT 0"),
        ("stat_shield_decay_ratio",  "REAL DEFAULT 0"),
        ("stat_absorption_phys",     "REAL DEFAULT 0"),
        ("stat_resistance_phys",     "REAL DEFAULT 0"),
        ("stat_resistance_dist",     "REAL DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "components", col_name, col_type)
    logger.info("  components: shield extended stat columns added.")

def _m024_ships_armor_shield_boost(cursor):
    """Ajoute les colonnes déflection armure, résistances bouclier et boost."""
    new_cols = [
        ("armor_deflect_phys",       "REAL DEFAULT 0"),
        ("armor_deflect_energy",      "REAL DEFAULT 0"),
        ("armor_cs_mult",             "REAL DEFAULT 1"),
        ("shield_resist_phys",        "REAL DEFAULT 0"),
        ("shield_resist_energy",      "REAL DEFAULT 0"),
        ("shield_resist_distortion",  "REAL DEFAULT 0"),
        ("shield_regen_delay",        "REAL DEFAULT 0"),
        ("boost_regen_time",          "REAL DEFAULT 0"),
        ("boost_regen_delay",         "REAL DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        _add_column_if_missing(cursor, "ships", col_name, col_type)
    logger.info("  ships: armor deflection, shield resistance & boost columns added.")


def _m025_components_specialization(cursor):
    """Ajoute la colonne specialization (Military/Civilian/Industrial/Stealth) sur components."""
    _add_column_if_missing(cursor, "components", "specialization", "TEXT DEFAULT ''")
    logger.info("  components: specialization column added.")


def _m026_shields_category_fix(cursor):
    """Corrige la catégorie des shields de DEFENSE → SYSTEMS (correction d'import)."""
    cursor.execute("UPDATE components SET category='SYSTEMS' WHERE type_name='SHIELD' AND category='DEFENSE'")
    cursor.execute("UPDATE component_types SET category='SYSTEMS' WHERE name='SHIELD' AND category='DEFENSE'")
    logger.info("  components: shields category corrected DEFENSE → SYSTEMS.")


MIGRATIONS = [
    (1, _m001_schema_initial),
    (2, _m002_targets_colonnes_legacy),
    (3, _m003_organizations_colonnes_legacy),
    (4, _m004_ships_colonnes_legacy),
    (5, _m005_locations_colonnes_legacy),
    (6, _m006_loadout_rebuild_pk),
    (7, _m007_localise_fr_to_en),
    (8, _m008_rename_targets_to_players),
    (9, _m009_seed_sc_locations),
    (10, _m010_locations_km_to_meters),
    (11, _m011_locations_add_radius),
    (12, _m012_locations_add_physics_grid),
    (13, _m013_fix_moon_coordinates),
    (14, _m014_fix_cellin_coordinates),
    (15, _m015_app_settings),
    (16, _m016_org_events),
    (17, _m017_org_events_time),
    (18, _m018_org_events_location_participants),
    (19, _m019_ships_sc_fields),
    (20, _m020_ships_armor_cooling),
    (21, _m021_components_typed_stats),
    (22, _m022_components_shield_extended_stats),
    (23, _m023_components_weapon_detail_stats),
    (24, _m024_ships_armor_shield_boost),
    (25, _m025_components_specialization),
    (26, _m026_shields_category_fix),
]


# ---------------------------------------------------------------------------
# Point d'entrée public
# ---------------------------------------------------------------------------

def run_migrations(conn, cursor) -> None:
    """Applique toutes les migrations manquantes dans l'ordre.

    Args:
        conn:   connexion SQLite (pour les commits par migration)
        cursor: curseur SQLite actif
    """
    current = _get_version(cursor)
    conn.commit()  # valide la création de schema_version si elle vient d'être créée

    pending = [(v, fn) for v, fn in MIGRATIONS if v > current]

    if not pending:
        logger.debug(f"Database up to date (version {current}), no migration to apply.")
        return

    for version, fn in pending:
        logger.info(f"[MIGRATION] Applying migration {version}: {fn.__name__}")
        fn(cursor)
        _set_version(cursor, version)
        conn.commit()
        logger.info(f"[MIGRATION] Migration {version} applied successfully.")

    logger.info(f"[MIGRATION] Database updated: version {current} -> {pending[-1][0]}")
