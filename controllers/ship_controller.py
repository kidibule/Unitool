"""Controller pour la gestion des vaisseaux (ships)."""

import json
from models.ship import Ship
from models.component import Component
from services.ship_helpers import clean_number, parse_triple, parse_dimensions, clean_time, extract_header
import csv
from tkinter import filedialog, messagebox


SHIP_CAREER_OPTIONS = [
    "COMBAT",
    "TRANSPORT",
    "EXPLORATION",
    "INDUSTRIAL",
    "SCIENCE",
    "COMPETITION",
    "SUPPORT",
    "INTERDICTION",
]

SHIP_MANUFACTURER_OPTIONS = [
    "Aegis Dynamics",
    "Anvil Aerospace",
    "Aopoa",
    "Argo Astronautics",
    "Banu",
    "Consolidated Outland",
    "Crusader Industries",
    "Drake Interplanetary",
    "Esperia",
    "Gatac Manufacture",
    "Greycat Industrial",
    "Kruger Intergalactic",
    "Mirai",
    "Musashi Industrial & Starflight Concern (MISC)",
    "Origin Jumpworks",
    "Roberts Space Industries (RSI)",
    "Vanduul",
    "Xi'an",
]


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

    def _is_generic_subtype(self, category: str, subtype_name: str) -> bool:
        """WEAPON subgroups (S1/S3/etc.) are logical slot groups, not component type filters."""
        cat = (category or "").strip().upper()
        subtype = (subtype_name or "GENERIC").strip().upper()
        return subtype == "GENERIC" or cat == "WEAPON"

    def save_ship(self, data_dict: dict) -> None:
        ship = Ship(**{
            k: data_dict.get(k, "" if k in (
                "brand", "role", "career", "dimensions", "power_consumption",
                "cm_decoy_noise", "sc_uuid", "sc_class_name", "sc_data_json",
            ) else 0)
            for k in Ship.COLUMNS
            if k != "name"
        } | {"name": str(data_dict.get("name", ""))})

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
        cols = ", ".join(Ship.COLUMNS)
        return self.app.query(
            f"SELECT {cols} FROM ships WHERE name=?", (name.upper(),)
        )

    def load_ship_as_model(self, name: str) -> Ship | None:
        rows = self.load_ship(name)
        return Ship.from_db_row(rows[0]) if rows else None

    def list_ship_names(self) -> list[str]:
        rows = self.app.query("SELECT name FROM ships ORDER BY name")
        return [r[0] for r in rows]

    def list_ship_roles(self) -> list[str]:
        rows = self.app.query("SELECT name FROM ship_roles ORDER BY name")
        roles = [str(r[0]).upper().strip() for r in rows if r and r[0]]
        if roles:
            return roles
        rows = self.app.query("SELECT DISTINCT role FROM ships WHERE role IS NOT NULL AND TRIM(role) <> '' ORDER BY role")
        return [str(r[0]).upper().strip() for r in rows if r and r[0]]

    def list_ship_careers(self) -> list[str]:
        rows = self.app.query("SELECT name FROM ship_careers ORDER BY name")
        careers = [str(r[0]).upper().strip() for r in rows if r and r[0]]
        if careers:
            return careers
        rows = self.app.query("SELECT DISTINCT career FROM ships WHERE career IS NOT NULL AND TRIM(career) <> '' ORDER BY career")
        db_careers = [str(r[0]).upper().strip() for r in rows if r and r[0]]
        return sorted(set(db_careers + SHIP_CAREER_OPTIONS))

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
            title="IMPORT FLEET",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.import_ships_csv(list(reader))
            messagebox.showinfo("UNITOOL", "Import successful!")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def export_ships_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="EXPORT FLEET",
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
            messagebox.showinfo("UNITOOL", "Export successful!")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def import_ships_from_json(self) -> None:
        """Importe un ou plusieurs fichiers JSON SC data miner dans la base.

        Chaque fichier doit être un export du SC ship data miner (format JSON).
        Les fichiers sont traités via Ship.from_sc_json() pour le mapping.
        Les slots éditables du chassis sont automatiquement déduits via
        Ship.slots_from_sc_json() et stockés dans ship_subtype_specs.
        """
        file_paths = filedialog.askopenfilenames(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="IMPORT SC SHIP DATA (JSON)",
        )
        if not file_paths:
            return

        imported = 0
        errors = []
        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                ship = Ship.from_sc_json(data)
                if not ship.name:
                    errors.append(f"{path}: missing Name field")
                    continue

                # --- Upsert ship stats ---
                cols = ", ".join(ship.COLUMNS)
                placeholders = ", ".join(["?"] * len(ship.COLUMNS))
                updates = ", ".join([f"{c}=excluded.{c}" for c in ship.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO ships ({cols}) VALUES ({placeholders}) "
                    f"ON CONFLICT(name) DO UPDATE SET {updates}",
                    ship.to_db_tuple(),
                )

                # --- Déduit et insère les slots du chassis ---
                slots = Ship.slots_from_sc_json(data)
                ship_key = ship.name

                # Supprime les anciennes specs SC pour ce vaisseau avant réimport
                self.app.commit(
                    "DELETE FROM ship_subtype_specs WHERE ship_name = ?",
                    (ship_key,),
                )
                for slot in slots:
                    self.app.commit(
                        """
                        INSERT OR REPLACE INTO ship_subtype_specs
                            (ship_name, category, subtype_name, max_qty, max_size)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            ship_key,
                            slot["category"],
                            slot["subtype_name"],
                            slot["max_qty"],
                            slot["max_size"],
                        ),
                    )
                self._sync_ship_specs_from_subtypes(ship_key)

                # --- Déduit et insère le loadout par défaut ---
                default_load = Ship.defaultload_from_sc_json(data)

                # Efface l'ancien profil DEFAULT SC pour ce vaisseau
                self.app.commit(
                    "DELETE FROM ship_loadout WHERE ship_name = ? AND profile_name = 'DEFAULT'",
                    (ship_key,),
                )
                # S'assure que le profil DEFAULT existe
                self.app.commit(
                    "INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name) VALUES (?, 'DEFAULT')",
                    (ship_key,),
                )

                comp_imported = 0
                for entry in default_load:
                    # Utilise le nom lisible (ex: "Bulwark Shield", "Revenant Gatling")
                    # comme clé primaire dans components ; ClassName SC en fallback.
                    comp_name = entry["component_name"].upper() or entry["component_class"]
                    # Upsert composant dans le catalogue
                    type_part = entry["sc_type"].split(".")[-1]  # ex: "Gun", "Power", …
                    self.app.commit(
                        """
                        INSERT OR IGNORE INTO component_categories (name) VALUES (?)
                        """,
                        (entry["category"],),
                    )
                    self.app.commit(
                        """
                        INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)
                        """,
                        (type_part.upper(), entry["category"]),
                    )
                    self.app.commit(
                        """
                        INSERT OR IGNORE INTO components
                            (name, brand, type_name, category, size, grade)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            comp_name,
                            entry["manufacturer"].upper() or "UNKNOWN",
                            type_part.upper(),
                            entry["category"],
                            entry["max_size"],
                            entry["grade"],
                        ),
                    )
                    # Upsert entrée dans ship_loadout
                    self.app.commit(
                        """
                        INSERT OR REPLACE INTO ship_loadout
                            (ship_name, profile_name, category, subtype_name,
                             slot_number, component_name, quantity)
                        VALUES (?, 'DEFAULT', ?, ?, ?, ?, 1)
                        """,
                        (
                            ship_key,
                            entry["category"],
                            entry["subtype_name"],
                            entry["slot_number"],
                            comp_name,
                        ),
                    )
                    comp_imported += 1

                imported += 1
                slot_summary = ", ".join(
                    f"{s['max_qty']}×{s['subtype_name']}" for s in slots
                ) or "no editable slots"

                if hasattr(self.app, "log"):
                    self.app.log(
                        f"JSON IMPORT: {ship.name} ({ship.brand})  "
                        f"SCM {ship.scm_speed:.0f}  HP {ship.hp}  "
                        f"CARGO {ship.cargo:.0f} SCU  |  "
                        f"{len(slots)} slots  |  {comp_imported} default components",
                        source="FLEET",
                    )

            except json.JSONDecodeError as e:
                errors.append(f"{path}: JSON error — {e}")
            except Exception as e:
                errors.append(f"{path}: {e}")

        msg = f"Imported {imported} ship(s) from JSON."
        if errors:
            msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors)
            messagebox.showwarning("UNITOOL — IMPORT JSON", msg)
        else:
            messagebox.showinfo("UNITOOL — IMPORT JSON", msg)

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

    def update_component_in_db(self, original_name: str, data: dict) -> None:
        old_name = (original_name or "").strip().upper()
        new_name = (data.get("name") or "").strip().upper()
        if not old_name or not new_name:
            raise ValueError("Invalid component name.")

        params = (
            new_name,
            (data.get("brand") or "UNKNOWN").strip().upper(),
            (data.get("type_name") or "GENERIC").strip().upper(),
            (data.get("category") or "SYSTEMS").strip().upper(),
            self._safe_int(data.get("size")),
            (data.get("grade") or "C").strip().upper(),
            data.get("stats", "{}"),
            old_name,
        )

        self.app.commit(
            """
            UPDATE components
            SET name = ?, brand = ?, type_name = ?, category = ?, size = ?, grade = ?, stats = ?
            WHERE UPPER(name) = UPPER(?)
            """,
            params,
        )

        if old_name != new_name:
            self.app.commit(
                """
                UPDATE ship_loadout
                SET component_name = ?
                WHERE UPPER(component_name) = UPPER(?)
                """,
                (new_name, old_name),
            )

    def delete_component_from_db(self, component_name: str) -> None:
        name = (component_name or "").strip().upper()
        if not name:
            return

        self.app.commit(
            "DELETE FROM ship_loadout WHERE UPPER(component_name) = UPPER(?)",
            (name,),
        )
        self.app.commit(
            "DELETE FROM components WHERE UPPER(name) = UPPER(?)",
            (name,),
        )

    def list_components_catalog(self) -> list[tuple]:
        cols = ", ".join(Component.COLUMNS)
        sql = f"SELECT {cols} FROM components ORDER BY category, name"
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
            raise ValueError("TYPE is required.")
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
            raise ValueError("CATEGORY and SUBTYPE are required.")

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
            raise ValueError("Invalid parameters for subtype slot.")
        if qty <= 0 or size <= 0:
            raise ValueError("max_qty and max_size must be > 0.")

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
        if self._is_generic_subtype(category, subtype):
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
                if (not self._is_generic_subtype(category_up, subtype)) and (comp_type or "").upper() != subtype:
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

            cols = ", ".join(Component.COLUMNS)
            comp_data = self.app.query(
                f"SELECT {cols} FROM components WHERE name=?", (component_name.upper(),)
            )
            if not comp_data:
                raise Exception("Composant introuvable dans le catalogue.")

            new_comp = Component.from_db_row(comp_data[0])

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
                and (
                    self._is_generic_subtype(spec["category"], spec["subtype_name"])
                    or spec["subtype_name"] == new_comp.type_name.upper()
                )
                and int(new_comp.size) <= int(spec["max_size"])
            ]

            # Prefer the smallest compatible slot first to preserve larger hardpoints.
            matching_specs.sort(key=lambda s: int(s["max_size"]))

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
                    self.app.log("EQUIP REJECTED: Subtype slot limit reached.", source="FLEET")
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
                self.app.log(f"LOADOUT: {new_comp.name} equipped on {ship.name}", source="FLEET")
            return saved

        except Exception as e:
            if hasattr(self.app, "log"):
                self.app.log(f"LOADOUT ERROR: {str(e)}", source="ERROR")
            return False

    _ALLOWED_SHIP_COLUMNS = frozenset({
        "name", "brand", "role", "career", "size", "crew_size",
        "scm_speed", "scm_boost_forward", "scm_boost_backward",
        "nav_max_speed", "pitch", "yaw", "roll",
        "boosted_pitch", "boosted_yaw", "boosted_roll",
        "power_consumption", "cm_decoy_noise", "hp", "cargo",
        "dimensions", "mass", "hydrogen_capacity", "qt_fuel_capacity",
        "expedition_fee", "claim_time", "expedite_time",
    })

    def update_ship_specs(self, ship_name, data):
        if not data:
            return
        safe_data = {k: v for k, v in data.items() if k in self._ALLOWED_SHIP_COLUMNS}
        if not safe_data:
            return
        set_clause = ", ".join([f"{key} = ?" for key in safe_data.keys()])
        values = list(safe_data.values())
        values.append(ship_name.upper())
        sql = f"UPDATE ships SET {set_clause} WHERE name = ?"
        self.app.commit(sql, tuple(values))

    def extract_ship_stats_from_screenshot(self, image_path: str) -> dict:
        """Lit un screenshot de fiche vaisseau et retourne les champs DB reconnus."""
        from services.ship_ocr_service import extract_ship_stats

        rows = self.app.query("SELECT DISTINCT name, brand, role, career FROM ships")
        ship_records = []
        for r in rows:
            if not r or not r[0]:
                continue
            ship_records.append(
                {
                    "name": str(r[0]).upper().strip(),
                    "brand": (str(r[1]).upper().strip() if len(r) > 1 and r[1] else ""),
                    "role": (str(r[2]).upper().strip() if len(r) > 2 and r[2] else ""),
                    "career": (str(r[3]).upper().strip() if len(r) > 3 and r[3] else ""),
                }
            )
        names = [str(r[0]).upper() for r in rows if r and r[0]]
        brands = [str(r[1]).upper() for r in rows if len(r) > 1 and r[1] and str(r[1]).upper() not in ("UNKNOWN",)]
        roles_db = [str(r[2]).upper() for r in rows if len(r) > 2 and r[2]]
        careers_db = [str(r[3]).upper() for r in rows if len(r) > 3 and r[3]]

        roles_known = self.list_ship_roles()
        careers_known = self.list_ship_careers()
        brands_known = [
            "AEGIS", "AEGIS DYNAMICS", "ANVIL AEROSPACE", "AOPOA",
            "ARGO ASTRONAUTICS", "CONSOLIDATED OUTLAND",
            "CRUSADER INDUSTRIES", "DRAKE INTERPLANETARY", "ESPERIA",
            "GATAC MANUFACTURE", "GREYCAT INDUSTRIAL",
            "KRUGER INTERGALACTIC", "MISC",
            "MUSASHI INDUSTRIAL & STARFLIGHT CONCERN",
            "MIRAI", "ORIGIN JUMPWORKS",
            "ROBERTS SPACE INDUSTRIES", "RSI", "TUMBRIL",
            "BANU", "VANDUUL", "XI'AN",
        ]

        reference_data = {
            "names": sorted(set(names)),
            "brands": sorted(set(brands + brands_known)),
            "roles": sorted(set(roles_db + roles_known)),
            "careers": sorted(set(careers_db + careers_known)),
            "ship_records": ship_records,
        }

        return extract_ship_stats(image_path, reference_data=reference_data)

    def clear_all_fields(self):
        pass
