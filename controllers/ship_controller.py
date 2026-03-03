"""Controller pour la gestion des vaisseaux (ships)."""

from models.ship import Ship
from models.component import Component
import csv
from tkinter import filedialog, messagebox


class ShipController:
    """Contrôleur métier pour CRUD ships/components/loadout."""

    def __init__(self, app_controller):
        self.app = app_controller

    def _normalize_profile(self, profile_name: str | None) -> str:
        profile = (profile_name or "DEFAULT").strip().upper()
        return profile or "DEFAULT"

    def _sync_ship_specs_from_subtypes(self, ship_name: str) -> None:
        ship = ship_name.upper()
        rows = self.app.query(
            """
            SELECT category, SUM(max_qty), MAX(max_size)
            FROM ship_subtype_specs
            WHERE ship_name = ?
            GROUP BY category
            """,
            (ship,),
        )

        self.app.commit("DELETE FROM ship_specs WHERE ship_name = ?", (ship,))
        for category, total_qty, max_size in rows:
            self.app.commit(
                """
                INSERT OR REPLACE INTO ship_specs (ship_name, category, max_qty, max_size)
                VALUES (?, ?, ?, ?)
                """,
                (ship, category, int(total_qty or 0), int(max_size or 0)),
            )

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

    def list_component_categories(self) -> list[str]:
        rows = self.app.query(
            """
            SELECT name AS category FROM component_categories
            UNION
            SELECT DISTINCT category FROM component_types
            UNION
            SELECT DISTINCT category FROM components
            ORDER BY category
            """
        )
        return [r[0] for r in rows if r and r[0]]

    def create_component_category(self, category_name: str) -> None:
        category = (category_name or "").strip().upper()
        if not category:
            raise ValueError("TYPE requis.")
        self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", (category,))

    def delete_component_category(self, category_name: str) -> None:
        category = (category_name or "").strip().upper()
        if not category:
            return
        self.app.commit("DELETE FROM component_categories WHERE name = ?", (category,))

    def list_component_subtypes(self, category: str) -> list[str]:
        rows = self.app.query(
            """
            SELECT name
            FROM component_types
            WHERE UPPER(category) = UPPER(?)
            ORDER BY name
            """,
            (category,),
        )
        return [r[0] for r in rows if r and r[0]]

    def create_component_subtype(self, category: str, subtype_name: str) -> None:
        cat = (category or "").strip().upper()
        subtype = (subtype_name or "").strip().upper()
        if not cat or not subtype:
            raise ValueError("CATEGORY et SUBTYPE requis.")

        self.app.commit(
            "INSERT OR IGNORE INTO component_categories (name) VALUES (?)",
            (cat,),
        )

        self.app.commit(
            "INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)",
            (subtype, cat),
        )

    def delete_component_subtype(self, category: str, subtype_name: str) -> None:
        cat = (category or "").strip().upper()
        subtype = (subtype_name or "").strip().upper()
        if not cat or not subtype:
            return

        self.app.commit(
            "DELETE FROM component_types WHERE name = ? AND category = ?",
            (subtype, cat),
        )

    def list_subtype_specs(self, ship_name: str) -> list[tuple]:
        return self.app.query(
            """
            SELECT category, subtype_name, max_qty, max_size
            FROM ship_subtype_specs
            WHERE ship_name = ?
            ORDER BY category, subtype_name
            """,
            (ship_name.upper(),),
        )

    def upsert_subtype_spec(
        self,
        ship_name: str,
        category: str,
        subtype_name: str,
        max_qty: int,
        max_size: int,
    ) -> None:
        ship = ship_name.upper()
        cat = (category or "").strip().upper()
        subtype = (subtype_name or "").strip().upper()
        qty = self._safe_int(max_qty, 0)
        size = self._safe_int(max_size, 0)

        if not ship or not cat or not subtype:
            raise ValueError("Paramètres invalides pour le slot de sous-type.")
        if qty <= 0 or size <= 0:
            raise ValueError("max_qty et max_size doivent être > 0.")

        self.app.commit(
            """
            INSERT OR REPLACE INTO ship_subtype_specs (ship_name, category, subtype_name, max_qty, max_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ship, cat, subtype, qty, size),
        )
        self._sync_ship_specs_from_subtypes(ship)

    def delete_subtype_spec(self, ship_name: str, category: str, subtype_name: str) -> None:
        ship = ship_name.upper()
        cat = (category or "").strip().upper()
        subtype = (subtype_name or "").strip().upper()

        self.app.commit(
            "DELETE FROM ship_subtype_specs WHERE ship_name = ? AND category = ? AND subtype_name = ?",
            (ship, cat, subtype),
        )
        self._sync_ship_specs_from_subtypes(ship)

    def get_compatible_components(self, category, max_size):
        query = "SELECT name FROM components WHERE UPPER(category) = UPPER(?) AND size <= ? ORDER BY name"
        rows = self.app.query(query, (category, max_size))
        return [r[0] for r in rows]

    def get_compatible_components_by_subtype(self, category, subtype_name, max_size):
        query = """
            SELECT name
            FROM components
            WHERE UPPER(category) = UPPER(?)
              AND UPPER(type_name) = UPPER(?)
              AND size <= ?
            ORDER BY name
        """
        rows = self.app.query(query, (category, subtype_name, max_size))
        return [r[0] for r in rows]

    def get_ship_slot_specs(self, ship_name: str) -> list[dict]:
        ship = ship_name.upper()

        subtype_rows = self.app.query(
            """
            SELECT category, subtype_name, max_qty, max_size
            FROM ship_subtype_specs
            WHERE ship_name = ?
            ORDER BY category, subtype_name
            """,
            (ship,),
        )
        if subtype_rows:
            return [
                {
                    "category": row[0],
                    "subtype_name": row[1],
                    "max_qty": int(row[2] or 0),
                    "max_size": int(row[3] or 0),
                }
                for row in subtype_rows
            ]

        # Fallback legacy: une ligne générique par catégorie
        rows = self.app.query(
            """
            SELECT category, max_qty, max_size
            FROM ship_specs
            WHERE ship_name = ?
            ORDER BY category
            """,
            (ship,),
        )
        legacy_specs = [
            {
                "category": row[0],
                "subtype_name": "GENERIC",
                "max_qty": int(row[1] or 0),
                "max_size": int(row[2] or 0),
            }
            for row in rows
        ]

        if legacy_specs:
            return legacy_specs

        # Fallback dev-friendly: permettre la création de loadout même sans specs.
        return [
            {
                "category": "WEAPON",
                "subtype_name": "GENERIC",
                "max_qty": 1,
                "max_size": 1,
            }
        ]

    def get_slot_data(self, ship_name, profile_name, category, subtype_name, max_size, slot_index):
        profile = self._normalize_profile(profile_name)
        subtype = (subtype_name or "GENERIC").strip().upper()
        if subtype == "GENERIC":
            available = self.get_compatible_components(category, max_size)
        else:
            available = self.get_compatible_components_by_subtype(category, subtype, max_size)
        sql = """
            SELECT component_name FROM ship_loadout
            WHERE ship_name = ? AND profile_name = ? AND category = ? AND subtype_name = ? AND slot_number = ?
        """
        result = self.app.query(sql, (ship_name.upper(), profile, category.upper(), subtype, slot_index))
        current = result[0][0] if result else "EMPTY"
        return available, current

    def mount_component(self, ship_name, category, subtype_name, slot_index, component_name, profile_name="DEFAULT"):
        profile = self._normalize_profile(profile_name)
        subtype = (subtype_name or "GENERIC").strip().upper()
        ship = ship_name.upper()
        category_up = category.upper()
        try:
            self.app.commit(
                "INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name) VALUES (?, ?)",
                (ship, profile),
            )

            if component_name == "EMPTY":
                self.app.commit(
                    "DELETE FROM ship_loadout WHERE ship_name = ? AND profile_name = ? AND category = ? AND subtype_name = ? AND slot_number = ?",
                    (ship, profile, category_up, subtype, slot_index),
                )
            else:
                comp_rows = self.app.query(
                    "SELECT category, type_name, size FROM components WHERE name = ?",
                    (component_name.upper(),),
                )
                if not comp_rows:
                    return False

                comp_cat, comp_type, comp_size = comp_rows[0]
                if (comp_cat or "").upper() != category_up:
                    return False
                if subtype != "GENERIC" and (comp_type or "").upper() != subtype:
                    return False

                spec_rows = self.app.query(
                    """
                    SELECT max_size FROM ship_subtype_specs
                    WHERE ship_name = ? AND category = ? AND subtype_name = ?
                    """,
                    (ship, category_up, subtype),
                )
                if spec_rows:
                    max_size = int(spec_rows[0][0] or 0)
                    if int(comp_size or 0) > max_size:
                        return False

                self.app.commit(
                    """
                    INSERT OR REPLACE INTO ship_loadout (ship_name, profile_name, category, subtype_name, slot_number, component_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (ship, profile, category_up, subtype, slot_index, component_name.upper()),
                )
            return True
        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"Loadout sync error: {e}", source="ERROR")
            return False

    def clear_ship_loadout(self, ship_name: str, profile_name: str = "DEFAULT") -> None:
        profile = self._normalize_profile(profile_name)
        self.app.commit(
            "DELETE FROM ship_loadout WHERE ship_name = ? AND profile_name = ?",
            (ship_name.upper(), profile),
        )

    def list_loadout_profiles(self, ship_name: str) -> list[str]:
        try:
            ship = ship_name.upper()
            self.app.commit(
                "INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name) VALUES (?, 'DEFAULT')",
                (ship,),
            )
            rows = self.app.query(
                """
                SELECT profile_name
                FROM ship_loadout_profiles
                WHERE ship_name = ?
                UNION
                SELECT DISTINCT profile_name
                FROM ship_loadout
                WHERE ship_name = ? AND profile_name IS NOT NULL
                ORDER BY profile_name
                """,
                (ship, ship),
            )
            profiles = [r[0] for r in rows if r and r[0]]
            return ["DEFAULT", *profiles] if "DEFAULT" not in profiles else profiles
        except Exception:
            return ["DEFAULT"]

    def create_loadout_profile(
        self,
        ship_name: str,
        profile_name: str,
        source_profile: str = "DEFAULT",
        overwrite: bool = False,
    ) -> bool:
        try:
            ship = ship_name.upper()
            target = self._normalize_profile(profile_name)
            source = self._normalize_profile(source_profile)

            if not target:
                return False

            exists = self.app.query(
                "SELECT 1 FROM ship_loadout_profiles WHERE ship_name = ? AND profile_name = ?",
                (ship, target),
            )
            if exists and not overwrite:
                return False

            self.app.commit(
                "INSERT OR REPLACE INTO ship_loadout_profiles (ship_name, profile_name) VALUES (?, ?)",
                (ship, target),
            )

            if overwrite:
                self.app.commit(
                    "DELETE FROM ship_loadout WHERE ship_name = ? AND profile_name = ?",
                    (ship, target),
                )

            self.app.commit(
                """
                INSERT OR IGNORE INTO ship_loadout (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
                SELECT ship_name, ?, category, subtype_name, slot_number, component_name, quantity
                FROM ship_loadout
                WHERE ship_name = ? AND profile_name = ?
                """,
                (target, ship, source),
            )
            return True
        except Exception:
            return False

    def load_full_ship(self, name: str, profile_name: str = "DEFAULT") -> Ship | None:
        profile = self._normalize_profile(profile_name)
        ship = self.load_ship_as_model(name)
        if not ship:
            return None

        subtype_specs = self.get_ship_slot_specs(ship.name)
        aggregated_caps = {}
        for spec in subtype_specs:
            category = spec["category"]
            aggregated_caps.setdefault(category, {"max_qty": 0, "max_size": 0})
            aggregated_caps[category]["max_qty"] += int(spec["max_qty"])
            aggregated_caps[category]["max_size"] = max(aggregated_caps[category]["max_size"], int(spec["max_size"]))
        for category, cap in aggregated_caps.items():
            ship.set_capability(category=category, max_qty=cap["max_qty"], max_size=cap["max_size"])

        sql = """
            SELECT c.id, c.name, c.brand, c.type_name, c.category, c.size, c.grade, c.stats
            FROM components c
            JOIN ship_loadout sl ON c.name = sl.component_name
            WHERE sl.ship_name = ? AND sl.profile_name = ?
        """
        comp_rows = self.app.query(sql, (ship.name, profile))
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

    def equip_component(self, ship_name: str, component_name: str, profile_name: str = "DEFAULT") -> bool:
        try:
            profile = self._normalize_profile(profile_name)
            ship = self.load_full_ship(ship_name, profile)
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

            slot_specs = self.get_ship_slot_specs(ship.name)
            matching_specs = [
                spec
                for spec in slot_specs
                if spec["category"] == new_comp.category.upper()
                and (spec["subtype_name"] == "GENERIC" or spec["subtype_name"] == new_comp.type_name.upper())
                and int(new_comp.size) <= int(spec["max_size"])
            ]

            chosen_spec = matching_specs[0] if matching_specs else None
            if not chosen_spec:
                if hasattr(self.app, "log"):
                    self.app.log("EQUIP REJECTED: Aucun slot compatible.", source="FLEET")
                return False

            used_rows = self.app.query(
                """
                SELECT slot_number FROM ship_loadout
                WHERE ship_name = ? AND profile_name = ? AND category = ? AND subtype_name = ?
                """,
                (ship.name, profile, chosen_spec["category"], chosen_spec["subtype_name"]),
            )
            used_slots = {int(r[0]) for r in used_rows if r and r[0] is not None}

            slot_index = None
            for idx in range(int(chosen_spec["max_qty"])):
                if idx not in used_slots:
                    slot_index = idx
                    break

            if slot_index is None:
                if hasattr(self.app, "log"):
                    self.app.log("EQUIP REJECTED: Limite du sous-type atteinte.", source="FLEET")
                return False

            saved = self.mount_component(
                ship.name,
                new_comp.category,
                chosen_spec["subtype_name"],
                slot_index,
                new_comp.name,
                profile,
            )
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
