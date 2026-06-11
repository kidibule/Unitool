"""Controller pour la gestion des vaisseaux (ships)."""

import json
import os
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

    @staticmethod
    def _strip_size_suffix(subtype_name: str) -> str:
        """Strip trailing size label: 'GUN S3' → 'GUN', 'SHIELD S1' → 'SHIELD'."""
        import re
        return re.sub(r'\s+S\d+$', '', (subtype_name or '').strip().upper())

    def _is_generic_subtype(self, category: str, subtype_name: str) -> bool:
        """True when the subtype carries no type_name filtering (show all of category)."""
        stripped = self._strip_size_suffix(subtype_name)
        return not stripped or stripped == "GENERIC"

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
            rows = self.app.query(f"SELECT {', '.join(Ship.COLUMNS)} FROM ships")
            headers = list(Ship.COLUMNS)

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
        choice = messagebox.askquestion(
            "IMPORT JSON",
            "Importer depuis un dossier ?\n\nOui = choisir un dossier\nNon = choisir des fichiers",
            icon="question",
        )
        if choice == "yes":
            folder = filedialog.askdirectory(title="IMPORT SC SHIP DATA — Choisir un dossier")
            if not folder:
                return
            file_paths = [
                os.path.join(root, fname)
                for root, _dirs, files in os.walk(folder)
                for fname in files
                if fname.lower().endswith(".json")
            ]
            if not file_paths:
                messagebox.showinfo("UNITOOL — IMPORT JSON", "Aucun fichier .json trouvé dans ce dossier.")
                return
        else:
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

    def import_ships_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les ships depuis ships.json (StarCitizenWiki) avec loadout par défaut.

        Cache : cache/scwiki-ships.json, TTL 7 jours.
        Réutilise Ship.from_sc_json() et Ship.defaultload_from_sc_json() car le
        format ships.json SCWiki est identique au format SC data miner.
        """
        import threading, urllib.request, time

        SHIPS_URL   = "https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/master/ships.json"
        CACHE_DIR   = os.path.join(os.path.dirname(__file__), "..", "cache")
        SHIPS_CACHE = os.path.join(CACHE_DIR, "scwiki-ships.json")
        TTL         = 7 * 24 * 3600

        def _do():
            os.makedirs(CACHE_DIR, exist_ok=True)

            # ── Chargement ships.json ────────────────────────────────────────
            cache_ok = (
                not force_refresh
                and os.path.isfile(SHIPS_CACHE)
                and (time.time() - os.path.getmtime(SHIPS_CACHE)) < TTL
            )
            if cache_ok:
                age = (time.time() - os.path.getmtime(SHIPS_CACHE)) / 86400
                if hasattr(self.app, "log"):
                    self.app.log(f"SCWIKI SHIPS: cache utilisé (age {age:.1f}j)", source="FLEET")
                with open(SHIPS_CACHE, encoding="utf-8") as f:
                    ships_data = json.load(f)
            else:
                try:
                    if hasattr(self.app, "log"):
                        self.app.log("SCWIKI SHIPS: téléchargement ships.json ...", source="FLEET")
                    with urllib.request.urlopen(SHIPS_URL, timeout=30) as r:
                        content = r.read().decode("utf-8")
                    ships_data = json.loads(content)
                    with open(SHIPS_CACHE, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    if os.path.isfile(SHIPS_CACHE):
                        if hasattr(self.app, "log"):
                            self.app.log(f"SCWIKI SHIPS: erreur réseau — cache expiré utilisé. ({e})", source="FLEET")
                        with open(SHIPS_CACHE, encoding="utf-8") as f:
                            ships_data = json.load(f)
                    else:
                        messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur téléchargement ships.json:\n{e}")
                        return

            imported = skipped = errors = 0
            for raw in ships_data:
                name = (raw.get("Name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                try:
                    ship = Ship.from_sc_json(raw)
                    if not ship.name:
                        skipped += 1
                        continue

                    # ── Upsert ship stats ────────────────────────────────────
                    cols = ", ".join(Ship.COLUMNS)
                    phs  = ", ".join(["?"] * len(Ship.COLUMNS))
                    upd  = ", ".join([f"{c}=excluded.{c}" for c in Ship.COLUMNS if c != "name"])
                    self.app.commit(
                        f"INSERT INTO ships ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                        ship.to_db_tuple(),
                    )

                    # ── Slots du chassis ─────────────────────────────────────
                    slots = Ship.slots_from_sc_json(raw)
                    self.app.commit("DELETE FROM ship_subtype_specs WHERE ship_name = ?", (ship.name,))
                    for slot in slots:
                        self.app.commit(
                            "INSERT OR REPLACE INTO ship_subtype_specs (ship_name, category, subtype_name, max_qty, max_size) VALUES (?, ?, ?, ?, ?)",
                            (ship.name, slot["category"], slot["subtype_name"], slot["max_qty"], slot["max_size"]),
                        )
                    self._sync_ship_specs_from_subtypes(ship.name)

                    # ── Loadout par défaut ────────────────────────────────────
                    default_load = Ship.defaultload_from_sc_json(raw)
                    self.app.commit(
                        "DELETE FROM ship_loadout WHERE ship_name = ? AND profile_name = 'DEFAULT'",
                        (ship.name,),
                    )
                    self.app.commit(
                        "INSERT OR IGNORE INTO ship_loadout_profiles (ship_name, profile_name) VALUES (?, 'DEFAULT')",
                        (ship.name,),
                    )
                    for entry in default_load:
                        comp_name = entry["component_name"].upper() or entry["component_class"]
                        type_part = entry["sc_type"].split(".")[-1]
                        self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", (entry["category"],))
                        self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", (type_part.upper(), entry["category"]))
                        self.app.commit(
                            "INSERT OR IGNORE INTO components (name, brand, type_name, category, size, grade) VALUES (?, ?, ?, ?, ?, ?)",
                            (comp_name, entry["manufacturer"].upper() or "UNKNOWN", type_part.upper(), entry["category"], entry["max_size"], entry["grade"]),
                        )
                        self.app.commit(
                            "INSERT OR REPLACE INTO ship_loadout (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity) VALUES (?, 'DEFAULT', ?, ?, ?, ?, 1)",
                            (ship.name, entry["category"], entry["subtype_name"], entry["slot_number"], comp_name),
                        )

                    if hasattr(self.app, "log"):
                        self.app.log(
                            f"SCWIKI SHIPS: {ship.name}  SCM {ship.scm_speed:.0f}  HP {ship.hp}  "
                            f"{len(slots)} slots  {len(default_load)} composants par défaut",
                            source="FLEET",
                        )
                    imported += 1

                except Exception as e:
                    errors += 1
                    if hasattr(self.app, "log"):
                        self.app.log(f"SCWIKI SHIPS: erreur {name} — {e}", source="FLEET")

            msg = f"SCWIKI SHIPS IMPORT: {imported} ships importés. {skipped} ignorés. {errors} erreurs."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do, daemon=True).start()

    def import_components_from_json(self) -> None:
        """Importe un ou plusieurs fichiers JSON SC data miner (items individuels)."""
        choice = messagebox.askquestion(
            "IMPORT COMPONENTS JSON",
            "Importer depuis un dossier ?\n\nOui = choisir un dossier\nNon = choisir des fichiers",
            icon="question",
        )
        if choice == "yes":
            folder = filedialog.askdirectory(title="IMPORT SC COMPONENTS — Choisir un dossier")
            if not folder:
                return
            file_paths = [
                os.path.join(root, fname)
                for root, _dirs, files in os.walk(folder)
                for fname in files
                if fname.lower().endswith(".json")
            ]
            if not file_paths:
                messagebox.showinfo("UNITOOL — IMPORT JSON", "Aucun fichier .json trouvé dans ce dossier.")
                return
        else:
            file_paths = filedialog.askopenfilenames(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="IMPORT SC COMPONENT DATA (JSON)",
            )
            if not file_paths:
                return

        imported, skipped, errors = 0, 0, []
        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                comp = Component.from_sc_item_json(data)
                if not comp:
                    skipped += 1
                    continue

                # Upsert catégorie et type
                self.app.commit(
                    "INSERT OR IGNORE INTO component_categories (name) VALUES (?)",
                    (comp.category,),
                )
                self.app.commit(
                    "INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)",
                    (comp.type_name, comp.category),
                )

                # Upsert composant avec toutes ses stats
                cols = ", ".join(Component.COLUMNS)
                placeholders = ", ".join(["?"] * len(Component.COLUMNS))
                updates = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({placeholders}) "
                    f"ON CONFLICT(name) DO UPDATE SET {updates}",
                    comp.to_db_tuple(),
                )
                imported += 1
                if hasattr(self.app, "log"):
                    self.app.log(
                        f"COMPONENT IMPORT: {comp.name} [{comp.category}/{comp.type_name}] S{comp.size}{comp.grade}",
                        source="FLEET",
                    )
            except json.JSONDecodeError as e:
                errors.append(f"{os.path.basename(path)}: JSON error — {e}")
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        msg = f"Importé {imported} composant(s). Ignoré {skipped} fichier(s) non reconnus."
        if errors:
            msg += f"\n\nErreurs ({len(errors)}):\n" + "\n".join(errors)
            messagebox.showwarning("UNITOOL — IMPORT COMPONENTS", msg)
        else:
            messagebox.showinfo("UNITOOL — IMPORT COMPONENTS", msg)

    # Mapping grade entier → lettre SC (1 = meilleur = A)
    _GRADE_MAP = {1: "A", 2: "B", 3: "C", 4: "D"}
    # Types ship-items à importer comme armes
    _WEAPON_TYPES = {"WeaponGun", "Turret", "MissileLauncher", "BombLauncher"}

    def import_weapons_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les armes depuis ship-items.json (cache partagé 7 jours)."""
        import threading

        def _do_import():
            try:
                raw = self._load_scwiki_ship_items(force_refresh)
            except Exception as e:
                messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur chargement:\n{e}")
                return

            imported = skipped = 0
            for item in raw:
                item_type = str(item.get("type", "")).split(".")[0]
                if item_type not in self._WEAPON_TYPES:
                    continue

                name = (item.get("name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                std          = item.get("stdItem") or {}
                weapon_block = std.get("Weapon") or {}
                ammo_block   = std.get("Ammunition") or {}
                rn_block     = std.get("ResourceNetwork") or {}
                mfr_block    = std.get("Manufacturer") or std.get("manufacturer") or {}
                emit_block   = std.get("Emission") or {}
                modes        = weapon_block.get("Modes") or []
                first_mode   = modes[0] if modes else {}
                usage        = (rn_block.get("Usage") or {}).get("Power") or {}
                desc_data    = std.get("DescriptionData") or {}
                specialization = (desc_data.get("Class") or "").strip()

                grade_num = int(item.get("grade") or 1)
                if isinstance(mfr_block, dict):
                    brand = (mfr_block.get("Name") or item.get("manufacturer") or "UNKNOWN").strip().upper()
                else:
                    brand = str(item.get("manufacturer") or "UNKNOWN").strip().upper()

                type_name = self._weapon_type_name(
                    item_type=item_type,
                    subtype=item.get("subType") or "",
                    class_name=item.get("className") or "",
                )

                comp = Component(
                    name=name.upper(),
                    brand=brand,
                    type_name=type_name,
                    category="WEAPON",
                    size=int(item.get("size") or std.get("Size") or 1),
                    grade=self._GRADE_MAP.get(grade_num, "C"),
                    specialization=specialization,
                    stat_dps=float(weapon_block.get("Damage", {}).get("Burst") or first_mode.get("Dps") or 0),
                    stat_alpha=float(first_mode.get("Alpha") or first_mode.get("DamagePerShot") or 0),
                    stat_range=float(ammo_block.get("Range") or weapon_block.get("EffectiveRange") or 0),
                    stat_fire_rate=float(weapon_block.get("RateOfFire") or first_mode.get("RoundsPerMinute") or 0),
                    stat_ammo_count=int(weapon_block.get("Capacity") or 0),
                    stat_power_draw=float(usage.get("Maximum") or 0),
                    stat_em_gen=float((emit_block.get("Em") or {}).get("Maximum") or 0),
                )

                self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", ("WEAPON",))
                self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", (type_name, "WEAPON"))
                cols = ", ".join(Component.COLUMNS)
                phs  = ", ".join(["?"] * len(Component.COLUMNS))
                upd  = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                    comp.to_db_tuple(),
                )
                imported += 1

            msg = f"SCWIKI IMPORT: {imported} armes importées. {skipped} ignorées (sans nom)."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do_import, daemon=True).start()

    @staticmethod
    def _weapon_type_name(item_type: str, subtype: str, class_name: str) -> str:
        """Déduit un type lisible depuis le className SC.

        Exemples :
          KLWE_LASERREPEATER_S5       → LASER REPEATER
          BEHR_BALLISTICGATLING_S4    → BALLISTIC GATLING
          ASAD_DISTORTIONREPEATER_S2  → DISTORTION REPEATER
          KLWE_MASSDRIVER_S2          → MASS DRIVER
          MissileLauncher + MissileRack → MISSILE RACK
          Turret + GunTurret          → TURRET
        """
        import re

        # ── Missiles / Bombes ─────────────────────────────────────────────
        if item_type in ("MissileLauncher", "BombLauncher"):
            sub_map = {
                "MissileRack": "MISSILE RACK",
                "BombRack":    "BOMB RACK",
            }
            return sub_map.get(subtype, "MISSILE RACK")

        # ── Tourelles ────────────────────────────────────────────────────
        if item_type == "Turret":
            sub_map = {
                "GunTurret":     "TURRET",
                "MannedTurret":  "MANNED TURRET",
                "MissileTurret": "MISSILE TURRET",
                "PDCTurret":     "PDC TURRET",
                "BallTurret":    "BALL TURRET",
                "TopTurret":     "TOP TURRET",
                "BottomTurret":  "BOTTOM TURRET",
                "CanardTurret":  "CANARD TURRET",
                "NoseMounted":   "NOSE TURRET",
                "Utility":       "UTILITY TURRET",
            }
            return sub_map.get(subtype, "TURRET")

        # ── WeaponGun : extraire le type depuis le className ──────────────
        cls = class_name.upper()
        # Ordre important : du plus spécifique au plus général
        _PROJ_KEYWORDS = [
            ("LASERSCATTERGUN",     "LASER SCATTERGUN"),
            ("LASERREPEATER",       "LASER REPEATER"),
            ("LASERCANNON",         "LASER CANNON"),
            ("LASERBEAM",           "LASER BEAM"),
            ("LASERGATLING",        "LASER GATLING"),
            ("BALLISTICGATLING",    "BALLISTIC GATLING"),
            ("JAVELINBALLISTICCAN", "BALLISTIC CANNON"),
            ("BALLISTICCANNON",     "BALLISTIC CANNON"),
            ("BALLISTICREPEATER",   "BALLISTIC REPEATER"),
            ("BALLISTICSCATTERGUN", "BALLISTIC SCATTERGUN"),
            ("DISTORTIONREPEATER",  "DISTORTION REPEATER"),
            ("DISTORTIONCANNON",    "DISTORTION CANNON"),
            ("DISTORTIONSCATTERGUN","DISTORTION SCATTERGUN"),
            ("MASSDRIVER",          "MASS DRIVER"),
            ("NEUTRONCANNON",       "NEUTRON CANNON"),
            ("NEUTRONREPEATER",     "NEUTRON REPEATER"),
            ("PLASMACANNON",        "PLASMA CANNON"),
            ("TACHYONCANNON",       "TACHYON CANNON"),
            ("TACHYONBEAM",         "TACHYON BEAM"),
            ("ENERGYREPEATER",      "ENERGY REPEATER"),
            ("SCATTERGUN",          "SCATTERGUN"),
        ]
        for keyword, label in _PROJ_KEYWORDS:
            if keyword in cls:
                return label

        # Fallback : sous-type SC ou item_type brut
        sub_map_gun = {
            "Gun":        "GUN",
            "GunTurret":  "TURRET",
        }
        return sub_map_gun.get(subtype, subtype.upper() or item_type.upper())


    _SCWIKI_CACHE_TTL       = 7 * 24 * 3600

    def _load_scwiki_ship_items(self, force_refresh: bool = False) -> list:
        """Retourne ship-items.json depuis le cache (ou le télécharge si absent/expiré)."""
        import urllib.request, time
        cache_dir  = os.path.join(os.path.dirname(__file__), "..", "cache")
        cache_file = os.path.join(cache_dir, "ship-items.json")
        os.makedirs(cache_dir, exist_ok=True)

        cache_ok = (
            not force_refresh
            and os.path.isfile(cache_file)
            and (time.time() - os.path.getmtime(cache_file)) < self._SCWIKI_CACHE_TTL
        )
        if cache_ok:
            age = (time.time() - os.path.getmtime(cache_file)) / 86400
            if hasattr(self.app, "log"):
                self.app.log(f"SCWIKI: cache utilisé (age {age:.1f}j)", source="FLEET")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        if hasattr(self.app, "log"):
            self.app.log("SCWIKI: téléchargement ship-items.json ...", source="FLEET")
        try:
            with urllib.request.urlopen(self._SCWIKI_SHIP_ITEMS_URL, timeout=30) as resp:
                content = resp.read().decode("utf-8")
            data = json.loads(content)
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(content)
            if hasattr(self.app, "log"):
                self.app.log(f"SCWIKI: cache mis à jour [{cache_file}]", source="FLEET")
            return data
        except Exception as e:
            if os.path.isfile(cache_file):
                if hasattr(self.app, "log"):
                    self.app.log(f"SCWIKI: erreur réseau — cache expiré utilisé. ({e})", source="FLEET")
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            raise

    def import_quantum_drives_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les Quantum Drives depuis ship-items.json (cache partagé)."""
        import threading

        def _do():
            try:
                raw = self._load_scwiki_ship_items(force_refresh)
            except Exception as e:
                messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur chargement:\n{e}")
                return

            imported = skipped = 0
            for item in raw:
                if not str(item.get("type", "")).startswith("QuantumDrive"):
                    continue

                name = (item.get("name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                std   = item.get("stdItem") or {}
                qt    = std.get("QuantumDrive") or {}
                sj    = qt.get("StandardJump") or {}
                rn    = std.get("ResourceNetwork") or {}
                emit  = std.get("Emission") or {}
                usage = (rn.get("Usage") or {}).get("Power") or {}
                mfr   = std.get("Manufacturer") or {}
                desc_data     = std.get("DescriptionData") or {}
                specialization = (desc_data.get("Class") or "").strip()

                grade_num = int(item.get("grade") or 1)
                brand = (
                    mfr.get("Name") if isinstance(mfr, dict)
                    else str(item.get("manufacturer") or "UNKNOWN")
                ).strip().upper()

                comp = Component(
                    name=name.upper(),
                    brand=brand or "UNKNOWN",
                    type_name="QUANTUM DRIVE",
                    category="PROPULSION",
                    size=int(item.get("size") or std.get("Size") or 1),
                    grade=self._GRADE_MAP.get(grade_num, "C"),
                    specialization=specialization,
                    stat_qt_speed=float(sj.get("DriveSpeed") or 0),
                    stat_qt_spool=float(sj.get("SpoolUpTime") or 0),
                    stat_regen_delay=float(sj.get("CooldownTime") or 0),
                    stat_qt_fuel_usage=float(qt.get("FuelConsumptionSCUPerGM") or 0),
                    stat_power_draw=float(usage.get("Maximum") or 0),
                    stat_em_gen=float((emit.get("Em") or {}).get("Maximum") or 0),
                )

                self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", ("PROPULSION",))
                self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", ("QUANTUM DRIVE", "PROPULSION"))
                cols = ", ".join(Component.COLUMNS)
                phs  = ", ".join(["?"] * len(Component.COLUMNS))
                upd  = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                    comp.to_db_tuple(),
                )
                imported += 1

            msg = f"SCWIKI QT IMPORT: {imported} quantum drives importés. {skipped} ignorés."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do, daemon=True).start()

    def import_coolers_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les Coolers depuis ship-items.json (cache partagé)."""
        import threading

        def _do():
            try:
                raw = self._load_scwiki_ship_items(force_refresh)
            except Exception as e:
                messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur chargement:\n{e}")
                return

            imported = skipped = 0
            for item in raw:
                if not str(item.get("type", "")).startswith("Cooler"):
                    continue

                name = (item.get("name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                std   = item.get("stdItem") or {}
                rn    = std.get("ResourceNetwork") or {}
                emit  = std.get("Emission") or {}
                gen   = rn.get("Generation") or {}
                usage = (rn.get("Usage") or {}).get("Power") or {}
                mfr   = std.get("Manufacturer") or {}
                desc_data     = std.get("DescriptionData") or {}
                specialization = (desc_data.get("Class") or "").strip()

                grade_num = int(item.get("grade") or std.get("Grade") or 1)
                brand = (
                    mfr.get("Name") if isinstance(mfr, dict)
                    else str(item.get("manufacturer") or "UNKNOWN")
                ).strip().upper()

                comp = Component(
                    name=name.upper(),
                    brand=brand or "UNKNOWN",
                    type_name="COOLER",
                    category="SYSTEMS",
                    size=int(item.get("size") or std.get("Size") or 1),
                    grade=self._GRADE_MAP.get(grade_num, "C"),
                    specialization=specialization,
                    stat_cooling_rate=float(gen.get("Coolant") or 0),
                    stat_power_draw=float(usage.get("Maximum") or 0),
                    stat_em_gen=float((emit.get("Em") or {}).get("Maximum") or 0),
                )

                self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", ("SYSTEMS",))
                self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", ("COOLER", "SYSTEMS"))
                cols = ", ".join(Component.COLUMNS)
                phs  = ", ".join(["?"] * len(Component.COLUMNS))
                upd  = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                    comp.to_db_tuple(),
                )
                imported += 1

            msg = f"SCWIKI COOLER IMPORT: {imported} coolers importés. {skipped} ignorés."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do, daemon=True).start()

    def import_powerplants_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les Power Plants depuis ship-items.json (cache partagé)."""
        import threading

        def _do():
            try:
                raw = self._load_scwiki_ship_items(force_refresh)
            except Exception as e:
                messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur chargement:\n{e}")
                return

            imported = skipped = 0
            for item in raw:
                if not str(item.get("type", "")).startswith("PowerPlant"):
                    continue

                name = (item.get("name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                std   = item.get("stdItem") or {}
                rn    = std.get("ResourceNetwork") or {}
                emit  = std.get("Emission") or {}
                gen   = rn.get("Generation") or {}
                usage = (rn.get("Usage") or {}).get("Coolant") or {}
                mfr   = std.get("Manufacturer") or {}
                desc_data     = std.get("DescriptionData") or {}
                specialization = (desc_data.get("Class") or "").strip()

                grade_num = int(item.get("grade") or std.get("Grade") or 1)
                brand = (
                    mfr.get("Name") if isinstance(mfr, dict)
                    else str(item.get("manufacturer") or "UNKNOWN")
                ).strip().upper()

                comp = Component(
                    name=name.upper(),
                    brand=brand or "UNKNOWN",
                    type_name="POWER PLANT",
                    category="SYSTEMS",
                    size=int(item.get("size") or std.get("Size") or 1),
                    grade=self._GRADE_MAP.get(grade_num, "C"),
                    specialization=specialization,
                    stat_power_output=float(gen.get("Power") or 0),
                    stat_heat_gen=float(usage.get("Maximum") or 0),
                    stat_em_gen=float((emit.get("Em") or {}).get("Maximum") or 0),
                )

                self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", ("SYSTEMS",))
                self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", ("POWER PLANT", "SYSTEMS"))
                cols = ", ".join(Component.COLUMNS)
                phs  = ", ".join(["?"] * len(Component.COLUMNS))
                upd  = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                    comp.to_db_tuple(),
                )
                imported += 1

            msg = f"SCWIKI POWER PLANT IMPORT: {imported} power plants importés. {skipped} ignorés."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do, daemon=True).start()

    def import_shields_from_scwiki(self, force_refresh: bool = False) -> None:
        """Importe les Shield Generators depuis ship-items.json (cache partagé)."""
        import threading

        def _do():
            try:
                raw = self._load_scwiki_ship_items(force_refresh)
            except Exception as e:
                messagebox.showerror("UNITOOL — SCWIKI IMPORT", f"Erreur chargement:\n{e}")
                return

            imported = skipped = 0
            for item in raw:
                if not str(item.get("type", "")).startswith("Shield"):
                    continue

                name = (item.get("name") or "").strip()
                if not name or name.startswith("<="):
                    skipped += 1
                    continue

                std   = item.get("stdItem") or {}
                shld  = std.get("Shield") or {}
                rn    = std.get("ResourceNetwork") or {}
                emit  = std.get("Emission") or {}
                usage = (rn.get("Usage") or {}).get("Power") or {}
                absorb = shld.get("Absorption") or {}
                mfr   = std.get("Manufacturer") or {}
                desc_data     = std.get("DescriptionData") or {}
                specialization = (desc_data.get("Class") or "").strip()

                grade_num = int(item.get("grade") or std.get("Grade") or 1)
                brand = (
                    mfr.get("Name") if isinstance(mfr, dict)
                    else str(item.get("manufacturer") or "UNKNOWN")
                ).strip().upper()

                comp = Component(
                    name=name.upper(),
                    brand=brand or "UNKNOWN",
                    type_name="SHIELD",
                    category="SYSTEMS",
                    size=int(item.get("size") or std.get("Size") or 1),
                    grade=self._GRADE_MAP.get(grade_num, "C"),
                    specialization=specialization,
                    stat_shield_hp=float(shld.get("MaxShieldHealth") or 0),
                    stat_shield_regen=float(shld.get("MaxShieldRegen") or 0),
                    stat_regen_delay=float(shld.get("DamagedDelay") or 0),
                    stat_shield_downed_delay=float(shld.get("DownedDelay") or 0),
                    stat_shield_decay_ratio=float(shld.get("DecayRatio") or 0),
                    stat_absorption_phys=float((absorb.get("Physical") or {}).get("Maximum") or 0),
                    stat_resistance_phys=float((absorb.get("Energy") or {}).get("Maximum") or 0),
                    stat_resistance_dist=float((absorb.get("Distortion") or {}).get("Maximum") or 0),
                    stat_power_draw=float(usage.get("Maximum") or 0),
                    stat_em_gen=float((emit.get("Em") or {}).get("Maximum") or 0),
                )

                self.app.commit("INSERT OR IGNORE INTO component_categories (name) VALUES (?)", ("SYSTEMS",))
                self.app.commit("INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)", ("SHIELD", "SYSTEMS"))
                cols = ", ".join(Component.COLUMNS)
                phs  = ", ".join(["?"] * len(Component.COLUMNS))
                upd  = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
                self.app.commit(
                    f"INSERT INTO components ({cols}) VALUES ({phs}) ON CONFLICT(name) DO UPDATE SET {upd}",
                    comp.to_db_tuple(),
                )
                imported += 1

            msg = f"SCWIKI SHIELD IMPORT: {imported} shields importés. {skipped} ignorés."
            if hasattr(self.app, "log"):
                self.app.log(msg, source="FLEET")
            messagebox.showinfo("UNITOOL — SCWIKI IMPORT", msg)

        threading.Thread(target=_do, daemon=True).start()

    def add_component_to_db(self, data: dict) -> None:
        comp = Component(
            name=str(data.get("name") or "").strip().upper(),
            brand=str(data.get("brand") or "UNKNOWN").strip().upper(),
            type_name=str(data.get("type_name") or "UNDEFINED").strip().upper(),
            category=str(data.get("category") or "SYSTEMS").strip().upper(),
            size=self._safe_int(data.get("size") or 1),
            grade=str(data.get("grade") or "C").strip().upper(),
        )
        cols = ", ".join(Component.COLUMNS)
        placeholders = ", ".join(["?"] * len(Component.COLUMNS))
        updates = ", ".join([f"{c}=excluded.{c}" for c in Component.COLUMNS if c != "name"])
        self.app.commit(
            f"INSERT INTO components ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(name) DO UPDATE SET {updates}",
            comp.to_db_tuple(),
        )

    def update_component_in_db(self, original_name: str, data: dict) -> None:
        old_name = (original_name or "").strip().upper()
        new_name = (data.get("name") or "").strip().upper()
        if not old_name or not new_name:
            raise ValueError("Invalid component name.")

        self.app.commit(
            """
            UPDATE components
            SET name = ?, brand = ?, type_name = ?, category = ?, size = ?, grade = ?
            WHERE UPPER(name) = UPPER(?)
            """,
            (
                new_name,
                (data.get("brand") or "UNKNOWN").strip().upper(),
                (data.get("type_name") or "GENERIC").strip().upper(),
                (data.get("category") or "SYSTEMS").strip().upper(),
                self._safe_int(data.get("size")),
                (data.get("grade") or "C").strip().upper(),
                old_name,
            ),
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
        base_type = self._strip_size_suffix(subtype)
        if self._is_generic_subtype(category, base_type):
            available = self.get_compatible_components(category, max_size)
        else:
            available = self.get_compatible_components_by_subtype(category, base_type, max_size)
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
        base_type = self._strip_size_suffix(subtype)
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
                if (not self._is_generic_subtype(category_up, base_type)) and (comp_type or "").upper() != base_type:
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

        comp_cols = ", ".join(f"c.{col}" for col in Component.COLUMNS)
        sql = f"""
            SELECT {comp_cols}
            FROM components c
            JOIN ship_loadout sl ON c.name = sl.component_name
            WHERE sl.ship_name = ? AND sl.profile_name = ?
        """
        comp_rows = self.app.query(sql, (ship.name, profile))
        for row in comp_rows:
            ship.components.append(Component.from_db_row(row))

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
                    or self._strip_size_suffix(spec["subtype_name"]) == new_comp.type_name.upper()
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
