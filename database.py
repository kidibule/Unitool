import sqlite3
import time


class Database:
    def __init__(self, db_name="unitool_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup()

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
