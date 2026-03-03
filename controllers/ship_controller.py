"""Controller pour la gestion des vaisseaux (ships)."""

from models.ship import Ship
from models.component import Component
import csv
from tkinter import filedialog, messagebox


class ShipController:
    """Contrôleur métier pour CRUD ships/components/loadout."""

    def __init__(self, app_controller):
        self.app = app_controller

    def _safe_int(self, value, default=0):
        try:
            return int(float(value)) if value not in (None, "") else default
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value, default=0.0):
        try:
            return float(value) if value not in (None, "") else default
        except (ValueError, TypeError):
            return default

    def save_ship(self, data_dict: dict) -> None:
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
            expedite_time=self._safe_float(data_dict.get("expedite_time")),
        )

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

    def load_ship(self, name: str) -> list:
        return self.app.query("SELECT * FROM ships WHERE name=?", (name.upper(),))

    def load_ship_as_model(self, name: str) -> Ship | None:
        rows = self.load_ship(name)
        return Ship.from_db_row(rows[0]) if rows else None

    def list_ship_names(self) -> list[str]:
        rows = self.app.query("SELECT name FROM ships ORDER BY name")
        return [r[0] for r in rows]

    def search_ship_names(self, query_text: str, limit: int = 10) -> list[str]:
        if not query_text:
            return []
        q = query_text.strip().upper()
        rows = self.app.query(
            "SELECT name FROM ships WHERE name LIKE ? OR brand LIKE ? ORDER BY name LIMIT ?",
            (f"%{q}%", f"%{q}%", int(limit)),
        )
        return [r[0] for r in rows]

    def import_ships_csv(self, rows: list) -> None:
        count = 0
        sql = """
            INSERT OR REPLACE INTO ships (
                name, brand, role, career, size, crew_size, scm_speed,
                scm_boost_forward, scm_boost_backward, nav_max_speed,
                pitch, yaw, roll, boosted_pitch, boosted_yaw, boosted_roll,
                power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass,
                hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        for row in rows:
            params = (
                row.get("name", "").upper(),
                row.get("brand", ""),
                row.get("role", ""),
                row.get("career", ""),
                row.get("size", ""),
                row.get("crew_size", 0),
                row.get("scm_speed", ""),
                row.get("scm_boost_forward", ""),
                row.get("scm_boost_backward", ""),
                row.get("nav_max_speed", ""),
                row.get("pitch", ""),
                row.get("yaw", ""),
                row.get("roll", ""),
                row.get("boosted_pitch", ""),
                row.get("boosted_yaw", ""),
                row.get("boosted_roll", ""),
                row.get("power_consumption", ""),
                row.get("cm_decoy_noise", ""),
                row.get("hp", 0),
                row.get("cargo", ""),
                row.get("dimensions", ""),
                row.get("mass", ""),
                row.get("hydrogen_capacity", ""),
                row.get("qt_fuel_capacity", ""),
                row.get("expedition_fee", ""),
                row.get("claim_time", ""),
                row.get("expedite_time", ""),
            )
            self.app.commit(sql, params)
            count += 1

        if hasattr(self.app, "log"):
            self.app.log(f"Imported {count} ships from CSV", source="SHIP")

    def export_ships_csv(self) -> list:
        return self.app.query("SELECT * FROM ships")

    def import_ships_from_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="IMPORTER LA FLOTTE",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.import_ships_csv(list(reader))
            messagebox.showinfo("UNITOOL", "Importation terminée avec succès !")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def export_ships_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="EXPORTER LA FLOTTE",
        )
        if not file_path:
            return

        try:
            rows = self.app.query("SELECT * FROM ships")
            headers = [description[0] for description in self.app.cursor.description]

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            if hasattr(self.app, "log"):
                self.app.log(f"EXPORT SUCCESS: {file_path}", source="SYSTEM")
            messagebox.showinfo("UNITOOL", "Exportation réussie !")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def add_component_to_db(self, data: dict):
        sql = """
            INSERT OR REPLACE INTO components
            (name, brand, type_name, category, size, grade, stats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["name"].upper(),
            data["brand"].upper(),
            data["type_name"].upper(),
            data.get("category", "SYSTEMS").upper(),
            self._safe_int(data["size"]),
            data["grade"].upper(),
            data.get("stats", "{}"),
        )
        self.app.commit(sql, params)

    def list_components_catalog(self) -> list[tuple]:
        sql = "SELECT name, brand, type_name, category, size, grade FROM components ORDER BY category, name"
        return self.app.query(sql)

    def get_compatible_components(self, category, max_size):
        query = "SELECT name FROM components WHERE UPPER(category) = UPPER(?) AND size <= ? ORDER BY name"
        rows = self.app.query(query, (category, max_size))
        return [r[0] for r in rows]

    def get_slot_data(self, ship_name, category, max_size, slot_index):
        available = self.get_compatible_components(category, max_size)
        sql = """
            SELECT component_name FROM ship_loadout
            WHERE ship_name = ? AND category = ? AND slot_number = ?
        """
        result = self.app.query(sql, (ship_name.upper(), category.upper(), slot_index))
        current = result[0][0] if result else "EMPTY"
        return available, current

    def mount_component(self, ship_name, category, slot_index, component_name):
        try:
            if component_name == "EMPTY":
                self.app.commit(
                    "DELETE FROM ship_loadout WHERE ship_name = ? AND category = ? AND slot_number = ?",
                    (ship_name.upper(), category.upper(), slot_index),
                )
            else:
                self.app.commit(
                    """
                    INSERT OR REPLACE INTO ship_loadout (ship_name, category, slot_number, component_name)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ship_name.upper(), category.upper(), slot_index, component_name.upper()),
                )
            return True
        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"Loadout sync error: {e}", source="ERROR")
            return False

    def clear_ship_loadout(self, ship_name: str) -> None:
        self.app.commit("DELETE FROM ship_loadout WHERE ship_name = ?", (ship_name.upper(),))

    def list_loadout_profiles(self, ship_name: str) -> list[str]:
        try:
            rows = self.app.query(
                "SELECT DISTINCT profile_name FROM ship_loadout WHERE ship_name = ? AND profile_name IS NOT NULL",
                (ship_name.upper(),),
            )
            profiles = [r[0] for r in rows if r and r[0]]
            return ["DEFAULT", *profiles] if "DEFAULT" not in profiles else profiles
        except Exception:
            return ["DEFAULT"]

    def load_full_ship(self, name: str) -> Ship | None:
        ship = self.load_ship_as_model(name)
        if not ship:
            return None

        specs_rows = self.app.query(
            "SELECT category, max_qty, max_size FROM ship_specs WHERE ship_name = ?",
            (ship.name,),
        )
        for spec in specs_rows:
            ship.set_capability(category=spec[0], max_qty=spec[1], max_size=spec[2])

        sql = """
            SELECT c.id, c.name, c.brand, c.type_name, c.category, c.size, c.grade, c.stats
            FROM components c
            JOIN ship_loadout sl ON c.name = sl.component_name
            WHERE sl.ship_name = ?
        """
        comp_rows = self.app.query(sql, (ship.name,))
        for row in comp_rows:
            ship.components.append(
                Component(
                    name=row[1],
                    brand=row[2],
                    type_name=row[3],
                    category=row[4],
                    size=row[5],
                    grade=row[6],
                    stats=row[7] if len(row) > 7 else {},
                )
            )

        return ship

    def equip_component(self, ship_name: str, component_name: str) -> bool:
        try:
            ship = self.load_full_ship(ship_name)
            if not ship:
                raise Exception("Vaisseau introuvable.")

            comp_data = self.app.query(
                "SELECT * FROM components WHERE name=?", (component_name.upper(),)
            )
            if not comp_data:
                raise Exception("Composant introuvable dans le catalogue.")

            row = comp_data[0]
            new_comp = Component(
                name=row[1],
                brand=row[2],
                type_name=row[3],
                category=row[4],
                size=row[5],
                grade=row[6],
            )

            allowed, message = ship.can_add_component(new_comp)
            if not allowed:
                if hasattr(self.app, "log"):
                    self.app.log(f"EQUIP REJECTED: {message}", source="FLEET")
                messagebox.showwarning("UNITOOL - Limitation", message)
                return False

            cap = ship.capabilities.get(new_comp.category.upper())
            if not cap:
                return False

            used_rows = self.app.query(
                "SELECT slot_number FROM ship_loadout WHERE ship_name = ? AND category = ?",
                (ship.name, new_comp.category.upper()),
            )
            used_slots = {int(r[0]) for r in used_rows if r and r[0] is not None}

            slot_index = None
            for idx in range(int(cap["max_qty"])):
                if idx not in used_slots:
                    slot_index = idx
                    break

            if slot_index is None:
                if hasattr(self.app, "log"):
                    self.app.log("EQUIP REJECTED: Aucun slot libre.", source="FLEET")
                return False

            saved = self.mount_component(ship.name, new_comp.category, slot_index, new_comp.name)
            if saved and hasattr(self.app, "log"):
                self.app.log(f"LOADOUT: {new_comp.name} équipé sur {ship.name}", source="FLEET")
            return saved

        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"LOADOUT ERROR: {str(e)}", source="ERROR")
            return False

    def update_ship_specs(self, ship_name, data):
        if not data:
            return
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        values.append(ship_name.upper())
        sql = f"UPDATE ships SET {set_clause} WHERE name = ?"
        self.app.commit(sql, tuple(values))

    def clear_all_fields(self):
        pass
