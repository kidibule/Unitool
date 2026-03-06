import sqlite3
import time
import json
import os
from tkinter import messagebox


class Database:
    def __init__(self, db_name="unitool_data.db", reset_on_start: bool = False):
        # Option pratique pour repartir d'une base propre au lancement (debug/dev)
        if reset_on_start and os.path.exists(db_name):
            os.remove(db_name)

        # Connexion SQLite + curseur principal réutilisé dans tout le projet
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        # Initialisation / migration du schéma
        self.setup()

    def execute(self, query, params=()):
        """Raccourci pour exécuter et commiter rapidement."""
        result = self.cursor.execute(query, params)
        self.conn.commit()
        return result

    def setup(self):
        """Crée les tables et applique les migrations légères (ALTER TABLE).

        Cette méthode est idempotente : elle peut être relancée sans casser
        une base déjà existante.
        """
        # --- TABLE TARGETS ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS targets 
            (pseudo TEXT PRIMARY KEY, org TEXT, ship TEXT, threat TEXT, notes TEXT, 
             date TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, alignment TEXT DEFAULT 'NEUTRE',
             pvp_lvl TEXT DEFAULT 'Inconnu', activity TEXT DEFAULT 'Inconnu',
             sid TEXT DEFAULT 'N/A', org_rank TEXT DEFAULT 'N/A', 
             enlisted_date TEXT DEFAULT 'N/A', language TEXT DEFAULT 'N/A')""")

        # Migrations pour Targets
        new_columns = [
            ("pvp_lvl", "TEXT DEFAULT 'Inconnu'"),
            ("activity", "TEXT DEFAULT 'Inconnu'"),
            ("sid", "TEXT DEFAULT 'N/A'"),
            ("org_rank", "TEXT DEFAULT 'N/A'"),
            ("enlisted_date", "TEXT DEFAULT 'N/A'"),
            ("language", "TEXT DEFAULT 'N/A'"),
            ("affiliates", "TEXT DEFAULT 'NONE'"),
        ]
        for col_name, col_type in new_columns:
            try: self.cursor.execute(f"ALTER TABLE targets ADD COLUMN {col_name} {col_type}")
            except: pass

        # --- TABLE ORGANIZATIONS ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS organizations (
            sid TEXT PRIMARY KEY,
            name TEXT,
            tag TEXT,
            description TEXT,
            member_count INTEGER DEFAULT 0,
            visible_members TEXT DEFAULT '[]',
            redacted_members TEXT DEFAULT '[]',
            ranks TEXT DEFAULT '{}',
            org_type TEXT DEFAULT 'ORGANIZATION',
            specialization TEXT DEFAULT 'GENERAL',
            allies TEXT DEFAULT '',
            enemies TEXT DEFAULT '',
            neutrals TEXT DEFAULT '',
            updated_at TEXT,
            alignment TEXT DEFAULT 'NEUTRE'
        )""")

        # Migration pour Organizations
        org_columns = [
            ("org_type", "TEXT DEFAULT 'ORGANIZATION'"),
            ("specialization", "TEXT DEFAULT 'GENERAL'"),
            ("allies", "TEXT DEFAULT ''"),
            ("enemies", "TEXT DEFAULT ''"),
            ("neutrals", "TEXT DEFAULT ''"),
            ("alignment", "TEXT DEFAULT 'NEUTRE'"),
            ("updated_at", "TEXT"),
        ]
        for col_name, col_type in org_columns:
            try: self.cursor.execute(f"ALTER TABLE organizations ADD COLUMN {col_name} {col_type}")
            except: pass

        # Table Contracts
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS contracts 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, client TEXT, reward TEXT, 
             status TEXT DEFAULT 'OPEN', date TEXT, priority TEXT DEFAULT 'MEDIUM', contract_type TEXT)"""
        )

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS contract_types 
            (name TEXT PRIMARY KEY, reward TEXT)""")

        # Table for ships 
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ships (
            name TEXT PRIMARY KEY,
            brand TEXT,
            role TEXT,
            career TEXT,
            size TEXT,
            crew_size INTEGER DEFAULT 0,
            scm_speed TEXT,
            scm_boost_forward TEXT,
            scm_boost_backward TEXT,
            nav_max_speed TEXT,
            pitch TEXT,
            yaw TEXT,
            roll TEXT,
            boosted_pitch TEXT,
            boosted_yaw TEXT,
            boosted_roll TEXT,
            power_consumption TEXT,
            cm_decoy_noise TEXT,
            hp INTEGER DEFAULT 0,
            cargo TEXT,
            dimensions TEXT,
            mass TEXT,
            hydrogen_capacity TEXT,
            qt_fuel_capacity TEXT,
            expedition_fee TEXT,
            claim_time TEXT,
            expedite_time TEXT
        )""")
        # Ensure legacy DBs get new ship columns if missing
        ship_columns = [
            ("brand", "TEXT"),
            ("role", "TEXT"),
            ("career", "TEXT"),
            ("size", "TEXT"),
            ("crew_size", "INTEGER DEFAULT 0"),
            ("scm_speed", "TEXT"),
            ("scm_boost_forward", "TEXT"),
            ("scm_boost_backward", "TEXT"),
            ("nav_max_speed", "TEXT"),
            ("pitch", "TEXT"),
            ("yaw", "TEXT"),
            ("roll", "TEXT"),
            ("boosted_pitch", "TEXT"),
            ("boosted_yaw", "TEXT"),
            ("boosted_roll", "TEXT"),
            ("power_consumption", "TEXT"),
            ("cm_decoy_noise", "TEXT"),
            ("hp", "INTEGER DEFAULT 0"),
            ("cargo", "TEXT"),
            ("dimensions", "TEXT"),
            ("mass", "TEXT"),
            ("hydrogen_capacity", "TEXT"),
            ("qt_fuel_capacity", "TEXT"),
            ("expedition_fee", "TEXT"),
            ("claim_time", "TEXT"),
            ("expedite_time", "TEXT"),
        ]

        for col_name, col_type in ship_columns:
            try:
                self.cursor.execute(f"ALTER TABLE ships ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass

                # --- 2. TABLE DES TYPES (Pour le filtrage) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS component_categories (
            name TEXT PRIMARY KEY
        )""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS component_types (
            name TEXT PRIMARY KEY,  -- ex: LASER_REPEATER, SHIELD_GEN
            category TEXT           -- ex: WEAPON, SYSTEMS, PROPULSION
        )""")

        # --- 3. TABLE DES COMPOSANTS (Catalogue) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,       -- ex: FR-66
            brand TEXT,             -- ex: SHIBIN
            type_name TEXT,         -- ex: SHIELD_GEN
            category TEXT,          -- ex: SYSTEMS (Doublon utile pour la performance)
            size INTEGER,
            grade TEXT,
            stats TEXT,             -- JSON string
            FOREIGN KEY (type_name) REFERENCES component_types(name)
        )""")

 #       # --- 4. TABLE DES CAPABILITÉS (Limites d'équipement par vaisseau) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ship_specs (
            ship_name TEXT,
            category TEXT,      -- WEAPON, SYSTEMS, PROPULSION
            max_qty INTEGER,    -- Nombre de slots
            max_size INTEGER,   -- Taille max par slot
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            PRIMARY KEY (ship_name, category)
        )""")

        # --- TABLE DES SOUS-TYPES (Limites fines par type de composant) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ship_subtype_specs (
            ship_name TEXT,
            category TEXT,       -- WEAPON, SYSTEMS, PROPULSION
            subtype_name TEXT,   -- ex: SHIELD GENERATOR, QUANTUM DRIVE
            max_qty INTEGER,
            max_size INTEGER,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            PRIMARY KEY (ship_name, category, subtype_name)
        )""")

        # --- 4. TABLE DES SLOTS (Limites d'équipement par vaisseau) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ship_slots (
            ship_name TEXT,
            slot_type TEXT,      -- ex: 'WEAPON', 'SHIELD', 'POWER_PLANT'
            slot_size INTEGER,   -- ex: 3
            max_quantity INTEGER, -- ex: 3 (pour 3 armes)
            FOREIGN KEY (ship_name) REFERENCES ships(name)
        )""")

        # --- 4. TABLE LOADOUT (Version corrigée avec Slots) ---
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS ship_loadout (
            ship_name TEXT,
            profile_name TEXT NOT NULL DEFAULT 'DEFAULT',
            category TEXT,          -- La colonne manquante est ici
            subtype_name TEXT NOT NULL DEFAULT 'GENERIC',
            slot_number INTEGER,    -- Celle-ci aussi
            component_name TEXT,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            FOREIGN KEY (component_name) REFERENCES components(name),
            PRIMARY KEY (ship_name, profile_name, category, subtype_name, slot_number)
            )"""
        )

        # Migration: garantir profile_name + subtype_name dans la clé primaire (legacy DB compat)
        loadout_cols = [row[1] for row in self.cursor.execute("PRAGMA table_info(ship_loadout)").fetchall()]
        loadout_pk_cols = [row[1] for row in self.cursor.execute("PRAGMA table_info(ship_loadout)").fetchall() if row[5] > 0]
        expected_pk = ["ship_name", "profile_name", "category", "subtype_name", "slot_number"]

        # Si le schéma legacy est détecté, on reconstruit la table puis on recopie les données.
        if ("profile_name" not in loadout_cols) or ("subtype_name" not in loadout_cols) or (loadout_pk_cols != expected_pk):
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS ship_loadout_new (
                ship_name TEXT,
                profile_name TEXT NOT NULL DEFAULT 'DEFAULT',
                category TEXT,
                subtype_name TEXT NOT NULL DEFAULT 'GENERIC',
                slot_number INTEGER,
                component_name TEXT,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (ship_name) REFERENCES ships(name),
                FOREIGN KEY (component_name) REFERENCES components(name),
                PRIMARY KEY (ship_name, profile_name, category, subtype_name, slot_number)
                )"""
            )

            if "profile_name" in loadout_cols and "subtype_name" in loadout_cols:
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO ship_loadout_new
                    (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
                    SELECT ship_name,
                           COALESCE(NULLIF(profile_name, ''), 'DEFAULT'),
                           category,
                           COALESCE(NULLIF(subtype_name, ''), 'GENERIC'),
                           slot_number,
                           component_name,
                           COALESCE(quantity, 1)
                    FROM ship_loadout
                    """
                )
            elif "profile_name" in loadout_cols:
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO ship_loadout_new
                    (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
                    SELECT sl.ship_name,
                           COALESCE(NULLIF(sl.profile_name, ''), 'DEFAULT'),
                           sl.category,
                           COALESCE(NULLIF(c.type_name, ''), 'GENERIC'),
                           sl.slot_number,
                           sl.component_name,
                           COALESCE(sl.quantity, 1)
                    FROM ship_loadout sl
                    LEFT JOIN components c ON c.name = sl.component_name
                    """
                )
            else:
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO ship_loadout_new
                    (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
                    SELECT sl.ship_name,
                           'DEFAULT',
                           sl.category,
                           COALESCE(NULLIF(c.type_name, ''), 'GENERIC'),
                           sl.slot_number,
                           sl.component_name,
                           COALESCE(sl.quantity, 1)
                    FROM ship_loadout sl
                    LEFT JOIN components c ON c.name = sl.component_name
                    """
                )

            self.cursor.execute("DROP TABLE ship_loadout")
            self.cursor.execute("ALTER TABLE ship_loadout_new RENAME TO ship_loadout")

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS ship_loadout_profiles (
                ship_name TEXT,
                profile_name TEXT,
                PRIMARY KEY (ship_name, profile_name),
                FOREIGN KEY (ship_name) REFERENCES ships(name)
            )"""
        )

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name)
            SELECT DISTINCT ship_name, COALESCE(NULLIF(profile_name, ''), 'DEFAULT')
            FROM ship_loadout
            """
        )

        self.conn.commit()
        # Table linking players to multiple ships (used by add_ship/get_ships)
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS player_ships (
                pseudo TEXT,
                ship TEXT,
                PRIMARY KEY (pseudo, ship)
            )"""
        )

        self.conn.commit()

        # --- TABLE LOCATIONS (Pour le Quantum Interception System) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS locations (
            name TEXT PRIMARY KEY,
            x REAL,
            y REAL,
            z REAL,
            type TEXT DEFAULT 'POI',
            parent_name TEXT
        )""")

        try:
            self.cursor.execute("ALTER TABLE locations ADD COLUMN type TEXT DEFAULT 'POI'")
        except Exception:
            pass

        try:
            self.cursor.execute("ALTER TABLE locations ADD COLUMN parent_name TEXT")
        except Exception:
            pass

        self.conn.commit()

    def query(self, sql, params=()):
        """Exécute un SELECT et renvoie toutes les lignes."""
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def commit(self, sql, params=()):
        """Exécute une requête d'écriture puis commit la transaction."""
        self.cursor.execute(sql, params)
        self.conn.commit()

    # --- MÉTHODES AJOUTÉES/CORRIGÉES (Désormais bien DANS la classe) ---

    def upsert_target_intel(self, data):
        """Insère ou met à jour les infos récupérées par le bot"""
        sql = """INSERT INTO targets (pseudo, org, sid, affiliates, org_rank, enlisted_date, language, date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(pseudo) DO UPDATE SET
                 org=excluded.org,
                 sid=excluded.sid,
                 affiliates=excluded.affiliates,
                 org_rank=excluded.org_rank,
                 enlisted_date=excluded.enlisted_date,
                 language=excluded.language,
                 date=excluded.date"""

        handle = str(data.get("Handle", "")).strip().upper()

        params = (
            handle,
            data["OrgaNom"],
            data["SID"],
            data.get("Affiliates", "NONE"),
            data["Rang"],
            data["Date"],
            data["Language"],
            time.strftime("%d/%m/%Y"),
        )

        self.commit(sql, params)

    def get_target_by_handle(self, handle):
        """Récupère les infos d'un joueur pour la preview"""
        handle = str(handle or "").strip()
        if not handle:
            return None

        sql = "SELECT org, sid, org_rank, enlisted_date, language FROM targets WHERE UPPER(pseudo) = UPPER(?)"
        res = self.query(sql, (handle,))
        if res:
            row = res[0]
            return {
                "OrgaNom": row[0],
                "SID": row[1],
                "Rang": row[2],
                "Date": row[3],
                "Language": row[4],
            }
        return None

    def add_ship(self, pseudo, ship):
        """Ajoute un ship à un joueur."""
        if ship and ship.strip():
            sql = "INSERT OR IGNORE INTO player_ships (pseudo, ship) VALUES (?, ?)"
            self.commit(sql, (pseudo, ship.upper()))

    def get_ships(self, pseudo):
        """Récupère tous les ships d'un joueur."""
        sql = "SELECT ship FROM player_ships WHERE pseudo = ? ORDER BY ship"
        rows = self.query(sql, (pseudo,))
        return [row[0] for row in rows]

    def delete_ship(self, pseudo, ship):
        """Supprime un ship d'un joueur."""
        sql = "DELETE FROM player_ships WHERE pseudo = ? AND ship = ?"
        self.commit(sql, (pseudo, ship))

    def delete_all_ships(self, pseudo):
        """Supprime tous les ships d'un joueur."""
        sql = "DELETE FROM player_ships WHERE pseudo = ?"
        self.commit(sql, (pseudo,))

    # --- MÉTHODES SPÉCIFIQUES ---
    def get_all_location_names(self):
        """Récupère uniquement les noms des lieux pour les ComboBox."""
        res = self.query("SELECT name FROM locations ORDER BY name ASC")
        return [row[0] for row in res]

    def add_location(self, name, x, y, z, loc_type="POI", parent_name=None):
        sql = """INSERT INTO locations (name, x, y, z, type, parent_name) 
                 VALUES (?, ?, ?, ?, ?, ?) 
                 ON CONFLICT(name) DO UPDATE SET x=excluded.x, y=excluded.y, z=excluded.z, type=excluded.type, parent_name=excluded.parent_name"""
        self.commit(sql, (name.upper(), x, y, z, loc_type, parent_name))

    # --- GESTION DES COMPOSANTS ---

    def add_component_type(self, name, category):
        self.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", (name.upper(), category.upper()))

    def add_component(self, name, brand, type_name, category, size, grade, stats="{}"):
        # On ajoute category dans le INSERT
        sql = """INSERT OR REPLACE INTO components 
                (name, brand, type_name, category, size, grade, stats) 
                VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.commit(sql, (name.upper(), brand.upper(), type_name.upper(), category.upper(), size, grade.upper(), stats))

    def equip_component_to_ship(self, ship_name, component_name, qty=1):
        """Lien MVC : Le contrôleur appellera cette méthode pour modifier le loadout"""
        sql = """
            INSERT OR REPLACE INTO ship_loadout
            (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
            VALUES (?, 'DEFAULT', 'LEGACY', 'GENERIC', 0, ?, ?)
        """
        self.commit(sql, (ship_name.upper(), component_name.upper(), qty))

    def get_ship_components(self, ship_name):
        """Récupère tous les composants équipés sur un vaisseau"""
        sql = """
            SELECT c.*, ct.category 
            FROM components c
            JOIN ship_loadout sl ON c.name = sl.component_name
            JOIN component_types ct ON c.type_name = ct.name
            WHERE sl.ship_name = ?
        """
        return self.query(sql, (ship_name.upper(),))
    
    def seed_test_data(self):
        """Réinitialise et injecte les configurations de slots."""
        print("[DATABASE] CLEANING AND INJECTING HARDPOINTS...")

        # Données des Vaisseaux (simplifié pour le test)
        test_ships = [
            ("AVENGER TITAN", "AEGIS", "S2", "LIGHT FREIGHTER"),
            ("CUTLASS BLACK", "DRAKE", "S3", "MEDIUM FREIGHTER"),
            ("ARROW", "ANVIL", "S1", "LIGHT FIGHTER")
        ]

        # Données des Slots (ship_name, category, max_qty, max_size)
        # C'est ICI que l'interface décide de ce qu'elle affiche
        test_specs = [
            # AVENGER TITAN
            ("AVENGER TITAN", "WEAPON", 3, 3),
            ("AVENGER TITAN", "SYSTEMS", 4, 1), # 2 Shield + 2 Cooler = 4
            ("AVENGER TITAN", "PROPULSION", 1, 1),

            # CUTLASS BLACK
            ("CUTLASS BLACK", "WEAPON", 6, 3),
            ("CUTLASS BLACK", "SYSTEMS", 6, 2),
            ("CUTLASS BLACK", "PROPULSION", 1, 2),

            # ARROW
            ("ARROW", "WEAPON", 4, 3),
            ("ARROW", "SYSTEMS", 3, 1),
            ("ARROW", "PROPULSION", 1, 1)
        ]

        # Limites fines par sous-type
        test_subtype_specs = [
            # AVENGER TITAN
            ("AVENGER TITAN", "SYSTEMS", "SHIELD GENERATOR", 2, 1),
            ("AVENGER TITAN", "SYSTEMS", "POWER PLANT", 1, 1),
            ("AVENGER TITAN", "SYSTEMS", "COOLER", 1, 1),
            ("AVENGER TITAN", "PROPULSION", "QUANTUM DRIVE", 1, 1),
            ("AVENGER TITAN", "PROPULSION", "HYDROGEN THRUSTER", 1, 1),

            # CUTLASS BLACK
            ("CUTLASS BLACK", "SYSTEMS", "SHIELD GENERATOR", 2, 2),
            ("CUTLASS BLACK", "SYSTEMS", "POWER PLANT", 2, 2),
            ("CUTLASS BLACK", "SYSTEMS", "COOLER", 2, 2),
            ("CUTLASS BLACK", "PROPULSION", "QUANTUM DRIVE", 1, 2),
            ("CUTLASS BLACK", "PROPULSION", "HYDROGEN THRUSTER", 1, 2),

            # ARROW
            ("ARROW", "SYSTEMS", "SHIELD GENERATOR", 1, 1),
            ("ARROW", "SYSTEMS", "POWER PLANT", 1, 1),
            ("ARROW", "SYSTEMS", "COOLER", 1, 1),
            ("ARROW", "PROPULSION", "QUANTUM DRIVE", 1, 1),
        ]

        test_component_types = [
            ("SHIELD GENERATOR", "SYSTEMS"),
            ("POWER PLANT", "SYSTEMS"),
            ("COOLER", "SYSTEMS"),
            ("LASER REPEATER", "WEAPON"),
            ("LASER CANNON", "WEAPON"),
            ("BALLISTIC REPEATER", "WEAPON"),
            ("BALLISTIC CANNON", "WEAPON"),
            ("DISTORTION REPEATER", "WEAPON"),
            ("QUANTUM DRIVE", "PROPULSION"),
            ("HYDROGEN THRUSTER", "PROPULSION"),
            ("MINING LASER", "MODULE"),
            ("SALVAGE BEAM", "MODULE"),
            ("TRACTOR BEAM", "MODULE"),
        ]

        test_component_categories = [
            ("SYSTEMS",),
            ("WEAPON",),
            ("PROPULSION",),
            ("MODULE",),
        ]

        try:
            # 1. Insertion vaisseaux
            for ship in test_ships:
                self.cursor.execute("INSERT OR REPLACE INTO ships (name, brand, size, role) VALUES (?, ?, ?, ?)", ship)

            # 2. Vider les anciennes specs pour éviter les résidus qui bloquent l'affichage
            self.cursor.execute("DELETE FROM ship_specs")
            self.cursor.execute("DELETE FROM ship_subtype_specs")

            # 3. Insertion des nouvelles specs
            for spec in test_specs:
                self.cursor.execute("""
                    INSERT INTO ship_specs (ship_name, category, max_qty, max_size) 
                    VALUES (?, ?, ?, ?)
                """, spec)

            for subtype_spec in test_subtype_specs:
                self.cursor.execute(
                    """
                    INSERT INTO ship_subtype_specs (ship_name, category, subtype_name, max_qty, max_size)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    subtype_spec,
                )

            for component_type in test_component_types:
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO component_types (name, category)
                    VALUES (?, ?)
                    """,
                    component_type,
                )

            for component_category in test_component_categories:
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO component_categories (name)
                    VALUES (?)
                    """,
                    component_category,
                )

            # 4. Injecter quelques composants pour tester les menus déroulants
            test_components = [
                ("FR-66", "SHIBIN", "SHIELD", "SYSTEMS", 1, "A"),
                ("BULDOG", "KRIG", "REPEATER", "WEAPON", 1, "C"),
                ("CF-337 PANTHER", "KLAUS", "REPEATER", "WEAPON", 3, "A"),
                ("ATLAS", "UNKNOWN", "QUANTUM", "PROPULSION", 1, "A")
            ]
            for comp in test_components:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO components (name, brand, type_name, category, size, grade) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, comp)

            self.conn.commit()
            print("[DATABASE] SUCCESS: Ship specs fully reloaded.")
            
        except Exception as e:
            print(f"[ERROR] Seeding failed: {e}")