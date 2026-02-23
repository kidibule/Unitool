import sqlite3
import time


class Database:
    def __init__(self, db_name="unitool_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup()
        self.seed_test_ships()  # Seed de vaisseaux pour tests et développement

    def setup(self):
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
            updated_at TEXT
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
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS ships (
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
            )"""
        )

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
            type TEXT DEFAULT 'POI'
        )""")

        self.conn.commit()
        self._seed_default_locations()

        # --- TABLE COMPONENT_TYPES ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS component_types (
            name TEXT PRIMARY KEY,
            category TEXT -- ex: AVIONICS, PROPULSION, SYSTEMS
        )""")

        # --- TABLE COMPONENTS ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            brand TEXT,
            type_name TEXT,
            size INTEGER,
            grade TEXT,
            stats TEXT, -- On peut stocker du JSON ici pour la flexibilité
            FOREIGN KEY (type_name) REFERENCES component_types(name)
        )""")

        # --- TABLE SHIP_LOADOUT (Lien entre Ship et Composants) ---
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ship_loadout (
            ship_name TEXT,
            component_name TEXT,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (ship_name) REFERENCES ships(name),
            FOREIGN KEY (component_name) REFERENCES components(name),
            PRIMARY KEY (ship_name, component_name)
        )""")

    def _seed_default_locations(self):
        """Infection de points de base si vide."""
        check = self.query("SELECT COUNT(*) FROM locations")
        if check[0][0] == 0:
            default_locs = [
                ('ARC-L1', 150000.0, 25000.0, 0.0, 'STATION'),
                ('CELLIN', 45000.0, 12000.0, 500.0, 'MOON'),
                ('DAYMAR', 48000.0, -15000.0, -200.0, 'MOON'),
                ('YELA', 52000.0, 5000.0, 1200.0, 'MOON')
            ]
            for loc in default_locs:
                self.commit("INSERT INTO locations (name, x, y, z, type) VALUES (?, ?, ?, ?, ?)", loc)

    def query(self, sql, params=()):
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def commit(self, sql, params=()):
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

        params = (
            data["Handle"],
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
        sql = "SELECT org, sid, org_rank, enlisted_date, language FROM targets WHERE pseudo = ?"
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

    def add_location(self, name, x, y, z, loc_type="POI"):
        sql = """INSERT INTO locations (name, x, y, z, type) 
                 VALUES (?, ?, ?, ?, ?) 
                 ON CONFLICT(name) DO UPDATE SET x=excluded.x, y=excluded.y, z=excluded.z, type=excluded.type"""
        self.commit(sql, (name.upper(), x, y, z, loc_type))

    def seed_test_ships(self):
        """Injecte des vaisseaux de test pour valider l'interface ShipFrame."""
        ships = [
            # (name, brand, role, career, size, crew, scm, boost_f, boost_b, nav, pitch, yaw, roll, b_pitch, b_yaw, b_roll, power, decoy, hp, cargo, dim, mass, hydro, qt, fee, claim, expedite)
            (
                "CUTLASS BLACK", "DRAKE INTERPLANETARY", "Medium Fighter / Freight", "Combat / Transport", 
                "Medium", 3, "165", "450", "300", "1115", "35", "35", "115", "45", "45", "150", 
                "Standard", "48", 32000, "46", "29x26x10m", "226k kg", "550000", "2500", "2500", "12", "4"
            ),
            (
                "GLADIUS", "AEGIS DYNAMICS", "Light Fighter", "Combat", 
                "Small", 1, "210", "580", "400", "1230", "65", "65", "210", "85", "85", "280", 
                "High", "32", 12000, "0", "15x17x5m", "48k kg", "120000", "580", "1200", "5", "1"
            ),
            (
                "CARRACK", "ANVIL AEROSPACE", "Expedition", "Exploration", 
                "Large", 6, "115", "250", "150", "950", "15", "15", "45", "20", "20", "55", 
                "Extreme", "96", 185000, "456", "126x76x30m", "4M kg", "18M", "44000", "15000", "45", "15"
            ),
            (
                "MERCURY STAR RUNNER", "CRUSADER INDUSTRIES", "Data Runner / Transport", "Transport", 
                "Medium", 3, "215", "520", "380", "1285", "38", "38", "125", "48", "48", "160", 
                "Standard", "64", 45000, "114", "40x38x11m", "250k kg", "850000", "3200", "4500", "15", "5"
            ),
            (
                "F7C-M SUPER HORNET", "ANVIL AEROSPACE", "Medium Fighter", "Combat", 
                "Small", 2, "175", "480", "350", "1215", "45", "45", "135", "55", "55", "180", 
                "High", "48", 24000, "0", "22x21x6m", "78k kg", "180000", "750", "1800", "8", "2"
            )
        ]

        sql = """INSERT OR REPLACE INTO ships (
            name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, 
            scm_boost_backward, nav_max_speed, pitch, yaw, roll, boosted_pitch, 
            boosted_yaw, boosted_roll, power_consumption, cm_decoy_noise, hp, cargo, 
            dimensions, mass, hydrogen_capacity, qt_fuel_capacity, expedition_fee, 
            claim_time, expedite_time
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

        for ship in ships:
            self.commit(sql, ship)
        
        print(f"DEBUG: {len(ships)} vaisseaux de test injectés.")

    # --- GESTION DES COMPOSANTS ---

    def add_component_type(self, name, category):
        self.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", (name.upper(), category.upper()))

    def add_component(self, name, brand, type_name, size, grade, stats="{}"):
        sql = "INSERT OR REPLACE INTO components (name, brand, type_name, size, grade, stats) VALUES (?, ?, ?, ?, ?, ?)"
        self.commit(sql, (name.upper(), brand.upper(), type_name.upper(), size, grade.upper(), stats))

    def equip_component_to_ship(self, ship_name, component_name, qty=1):
        """Lien MVC : Le contrôleur appellera cette méthode pour modifier le loadout"""
        sql = "INSERT OR REPLACE INTO ship_loadout (ship_name, component_name, quantity) VALUES (?, ?, ?)"
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