"""Controller pour la gestion des vaisseaux (ships)."""

from datetime import datetime
from models.ship import Ship
from models.component import Component
import csv
from tkinter import filedialog, messagebox


class ShipController:
    """Contrôleur simple pour CRUD sur la table `ships`.

    Expose des méthodes:
    - save_ship
    - load_ship
    - import_ships_csv
    - export_ships_csv
    """

    def __init__(self, app_controller):
        self.app = app_controller

    def _safe_int(self, value, default=0):
        """Convertit en int sans crasher."""
        try:
            return int(float(value)) if value else default
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value, default=0.0):
        """Convertit en float sans crasher."""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    def save_ship(self, data_dict: dict) -> None:
        """
        Prend un dictionnaire de la vue et le transforme en objet Ship 
        avant de le sauvegarder.
        """
        try:
            # Création de l'objet Ship avec conversion des types
            ship = Ship(
                name=str(data_dict.get("name", "")),
                brand=str(data_dict.get("brand", "")),
                role=str(data_dict.get("role", "")),
                career=str(data_dict.get("career", "")),
                size=str(data_dict.get("size", "")),
                crew_size=self._safe_int(data_dict.get("crew_size")),
                scm_speed=self._safe_int(data_dict.get("scm_speed")),
                scm_boost_forward=self._safe_int(data_dict.get("scm_boost_forward")),
                scm_boost_backward=self._safe_int(data_dict.get("scm_boost_backward")),
                nav_max_speed=self._safe_int(data_dict.get("nav_max_speed")),
                pitch=self._safe_int(data_dict.get("pitch")),
                yaw=self._safe_int(data_dict.get("yaw")),
                roll=self._safe_int(data_dict.get("roll")),
                boosted_pitch=self._safe_int(data_dict.get("boosted_pitch")),
                boosted_yaw=self._safe_int(data_dict.get("boosted_yaw")),
                boosted_roll=self._safe_int(data_dict.get("boosted_roll")),
                power_consumption=str(data_dict.get("power_consumption", "")),
                cm_decoy_noise=str(data_dict.get("cm_decoy_noise", "")),
                hp=self._safe_int(data_dict.get("hp")),
                cargo=self._safe_int(data_dict.get("cargo")),
                dimensions=str(data_dict.get("dimensions", "")),
                mass=str(data_dict.get("mass", "")),
                hydrogen_capacity=self._safe_float(data_dict.get("hydrogen_capacity")),
                qt_fuel_capacity=self._safe_float(data_dict.get("qt_fuel_capacity")),
                expedition_fee=str(data_dict.get("expedition_fee", "")),
                claim_time=self._safe_float(data_dict.get("claim_time")),
                expedite_time=self._safe_float(data_dict.get("expedite_time"))
            )

            # Génération auto de la requête SQL à partir des colonnes du modèle
            cols = ", ".join(ship.COLUMNS)
            placeholders = ", ".join(["?"] * len(ship.COLUMNS))
            updates = ", ".join([f"{c}=excluded.{c}" for c in ship.COLUMNS if c != "name"])

            sql = f"""
                INSERT INTO ships ({cols}) VALUES ({placeholders})
                ON CONFLICT(name) DO UPDATE SET {updates}
            """
            
            self.app.commit(sql, ship.to_db_tuple())
            
            if hasattr(self.app, "log"):
                self.app.log(f"Ship SYNC: {ship.name}", source="FLEET")
                
        except Exception as e:
            raise Exception(f"Controller Error: {str(e)}")

    def load_ship(self, name: str) -> list:
        """Retourne les rows correspondant au nom (uppercased)."""
        return self.app.query("SELECT * FROM ships WHERE name=?", (name.upper(),))

    def load_ship_as_model(self, name: str) -> Ship:
        rows = self.app.query("SELECT * FROM ships WHERE name=?", (name.upper(),))
        if rows:
            # Utilise la méthode de classe que tu as définie
            return Ship.from_db_row(rows[0])
        return None

    def import_ships_csv(self, rows: list) -> None:
        """Import simple depuis une liste de dicts (ex CSV.DictReader)."""
        count = 0
        for r in rows:
            sql = "INSERT OR REPLACE INTO ships (name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, scm_boost_backward, nav_max_speed, pitch, yaw, roll, boosted_pitch, boosted_yaw, boosted_roll, power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass, hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            params = (
                r.get("name", "").upper(),
                r.get("brand", ""),
                r.get("role", ""),
                r.get("career", ""),
                r.get("size", ""),
                r.get("crew_size", 0),
                r.get("scm_speed", ""),
                r.get("scm_boost_forward", ""),
                r.get("scm_boost_backward", ""),
                r.get("nav_max_speed", ""),
                r.get("pitch", ""),
                r.get("yaw", ""),
                r.get("roll", ""),
                r.get("boosted_pitch", ""),
                r.get("boosted_yaw", ""),
                r.get("boosted_roll", ""),
                r.get("power_consumption", ""),
                r.get("cm_decoy_noise", ""),
                r.get("hp", 0),
                r.get("cargo", ""),
                r.get("dimensions", ""),
                r.get("mass", ""),
                r.get("hydrogen_capacity", ""),
                r.get("qt_fuel_capacity", ""),
                r.get("expedition_fee", ""),
                r.get("claim_time", ""),
                r.get("expedite_time", ""),
            )
            self.app.commit(sql, params)
            count += 1
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Imported {count} ships from CSV", source="SHIP")
        except Exception:
            pass

    def export_ships_csv(self) -> list:
        return self.app.query("SELECT * FROM ships")

    def clear_all_fields(self):
        pass

    def load_full_ship(self, name: str) -> Ship:
        ship = self.load_ship_as_model(name)
        
        if ship:
            # Assure-toi que ta requête SELECT récupère bien la colonne category
            sql = """
                SELECT c.id, c.name, c.brand, c.type_name, c.category, c.size, c.grade, c.stats 
                FROM components c
                JOIN ship_loadout sl ON c.name = sl.component_name
                WHERE sl.ship_name = ?
            """
            rows = self.app.query(sql, (ship.name,))
            
            for row in rows:
                # On adapte ici pour correspondre au nouveau __init__ de Component
                comp = Component(
                    name=row[1], 
                    brand=row[2], 
                    type_name=row[3], 
                    category=row[4], # C'est l'argument qui manquait !
                    size=row[5], 
                    grade=row[6],
                    stats=row[7] if len(row) > 7 else {}
                )
                ship.add_component(comp)
                
        return ship

    def equip_component(self, ship_name: str, component_name: str) -> bool:
        """Relie un composant à un vaisseau dans la base de données."""
        try:
            # On pourrait vérifier ici la taille du composant vs la taille du ship
            sql = "INSERT OR REPLACE INTO ship_loadout (ship_name, component_name) VALUES (?, ?)"
            self.app.commit(sql, (ship_name.upper(), component_name.upper()))
            
            if hasattr(self.app, "log"):
                self.app.log(f"LOADOUT: {component_name} équipé sur {ship_name}", source="FLEET")
            return True
        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"LOADOUT ERROR: {str(e)}", source="ERROR")
            return False

    def export_ships_to_csv(self):
        """Exporte la table ships vers un fichier CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="EXPORTER LA FLOTTE"
        )
        if not file_path:
            return

        try:
            # On récupère toutes les données
            rows = self.app.query("SELECT * FROM ships")
            # On récupère les noms des colonnes pour le header
            headers = [description[0] for description in self.app.cursor.description]

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            
            self.app.log(f"EXPORT SUCCESS: {file_path}", source="SYSTEM")
            messagebox.showinfo("UNITOOL", "Exportation réussie !")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_ships_from_csv(self):
        """Importe des vaisseaux depuis un CSV et les insère en base."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="IMPORTER LA FLOTTE"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.import_ships_csv(list(reader)) # Utilise ta méthode existante
                
            messagebox.showinfo("UNITOOL", "Importation terminée avec succès !")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def add_component_to_db(self, data: dict):
        """Inscrit un nouveau composant dans la table components."""
        # On ajoute category ici
        sql = """INSERT OR REPLACE INTO components 
                (name, brand, type_name, category, size, grade, stats) 
                VALUES (?, ?, ?, ?, ?, ?, ?)"""
        
        params = (
            data['name'].upper(), 
            data['brand'].upper(), 
            data['type_name'].upper(), 
            data.get('category', 'SYSTEMS').upper(), # Valeur par défaut si absente
            self._safe_int(data['size']), 
            data['grade'].upper(),
            data.get('stats', '{}')
        )
        self.app.commit(sql, params)