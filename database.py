import sqlite3
import time

class Database:
    def __init__(self, db_name='unitool_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup()

    def setup(self):
        # Table Targets avec les nouveaux champs Intel
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS targets 
            (pseudo TEXT PRIMARY KEY, org TEXT, ship TEXT, threat TEXT, notes TEXT, 
             date TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, alignment TEXT DEFAULT 'NEUTRE',
             pvp_lvl TEXT DEFAULT 'Inconnu', activity TEXT DEFAULT 'Inconnu',
             sid TEXT DEFAULT 'N/A', org_rank TEXT DEFAULT 'N/A', 
             enlisted_date TEXT DEFAULT 'N/A', language TEXT DEFAULT 'N/A')''')
        
        # --- MIGRATIONS AUTOMATIQUES ---
        new_columns = [
            ("pvp_lvl", "TEXT DEFAULT 'Inconnu'"),
            ("activity", "TEXT DEFAULT 'Inconnu'"),
            ("sid", "TEXT DEFAULT 'N/A'"),
            ("org_rank", "TEXT DEFAULT 'N/A'"),
            ("enlisted_date", "TEXT DEFAULT 'N/A'"),
            ("language", "TEXT DEFAULT 'N/A'"),
            ("affiliates", "TEXT DEFAULT 'NONE'") 
        ]
        
        for col_name, col_type in new_columns:
            try:
                self.cursor.execute(f"ALTER TABLE targets ADD COLUMN {col_name} {col_type}")
            except: pass

        # Table Contracts
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS contracts 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, client TEXT, reward TEXT, 
             status TEXT DEFAULT 'OPEN', date TEXT, priority TEXT DEFAULT 'MEDIUM', contract_type TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS contract_types 
            (name TEXT PRIMARY KEY, reward TEXT)''')
        
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
        sql = '''INSERT INTO targets (pseudo, org, sid, affiliates, org_rank, enlisted_date, language, date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(pseudo) DO UPDATE SET
                 org=excluded.org,
                 sid=excluded.sid,
                 affiliates=excluded.affiliates,
                 org_rank=excluded.org_rank,
                 enlisted_date=excluded.enlisted_date,
                 language=excluded.language,
                 date=excluded.date'''
        
        params = (
            data['Handle'], 
            data['OrgaNom'], 
            data['SID'],    
            data.get('Affiliates', 'NONE'),
            data['Rang'], 
            data['Date'], 
            data['Language'],
            time.strftime("%d/%m/%Y")
        )   
        
        self.commit(sql, params)

    def get_target_by_handle(self, handle):
        """Récupère les infos d'un joueur pour la preview"""
        sql = "SELECT org, sid, org_rank, enlisted_date, language FROM targets WHERE pseudo = ?"
        res = self.query(sql, (handle,))
        if res:
            row = res[0]
            return {
                'OrgaNom': row[0],
                'SID': row[1],
                'Rang': row[2],
                'Date': row[3],
                'Language': row[4]
            }
        return None