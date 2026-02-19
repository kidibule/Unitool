"""Vue pour gestion des vaisseaux (ships) — interface similaire à LoggerFrame."""

import customtkinter as ctk
from tkinter import filedialog
import csv
from datetime import datetime

from drake_ui.engine import DrakeConfig, DrakeButton, DrakePopup


class ShipFrame(ctk.CTkFrame):
    """Interface simple pour créer/mettre à jour des ships."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        DrakeConfig.create_title(self, "SHIP MANAGEMENT")

        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 35,
        }

        f_top = ctk.CTkFrame(self, fg_color="transparent")
        f_top.pack(pady=(0, 10), padx=50, fill="x")

        self.name_in = ctk.CTkEntry(f_top, placeholder_text="SHIP NAME", **entry_kwargs)
        self.name_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.name_in.bind("<Return>", self.load_ship)

        self.brand_in = ctk.CTkEntry(f_top, placeholder_text="BRAND", **entry_kwargs)
        self.brand_in.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Role / Career
        f_desc = ctk.CTkFrame(self, fg_color="transparent")
        f_desc.pack(pady=5, padx=50, fill="x")
        self.role_in = ctk.CTkEntry(f_desc, placeholder_text="ROLE", **entry_kwargs)
        self.role_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.career_in = ctk.CTkEntry(f_desc, placeholder_text="CAREER", **entry_kwargs)
        self.career_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        # Size / crew
        f_size = ctk.CTkFrame(self, fg_color="transparent")
        f_size.pack(pady=5, padx=50, fill="x")
        self.size_in = ctk.CTkEntry(f_size, placeholder_text="SIZE", **entry_kwargs)
        self.size_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.crew_in = ctk.CTkEntry(f_size, placeholder_text="CREW SIZE", **entry_kwargs)
        self.crew_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        # Speed / boost fields
        f_speed = ctk.CTkFrame(self, fg_color="transparent")
        f_speed.pack(pady=5, padx=50, fill="x")
        self.scm_in = ctk.CTkEntry(f_speed, placeholder_text="SCM SPEED", **entry_kwargs)
        self.scm_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.scm_bf_in = ctk.CTkEntry(f_speed, placeholder_text="SCM BOOST FORWARD", **entry_kwargs)
        self.scm_bf_in.pack(side="left", fill="x", expand=True, padx=5)
        self.scm_bb_in = ctk.CTkEntry(f_speed, placeholder_text="SCM BOOST BACKWARD", **entry_kwargs)
        self.scm_bb_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        f_nav = ctk.CTkFrame(self, fg_color="transparent")
        f_nav.pack(pady=5, padx=50, fill="x")
        self.nav_in = ctk.CTkEntry(f_nav, placeholder_text="NAV MAX SPEED", **entry_kwargs)
        self.nav_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.pitch_in = ctk.CTkEntry(f_nav, placeholder_text="PITCH", **entry_kwargs)
        self.pitch_in.pack(side="left", fill="x", expand=True, padx=5)
        self.yaw_in = ctk.CTkEntry(f_nav, placeholder_text="YAW", **entry_kwargs)
        self.yaw_in.pack(side="left", fill="x", expand=True, padx=5)
        self.roll_in = ctk.CTkEntry(f_nav, placeholder_text="ROLL", **entry_kwargs)
        self.roll_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        # Performance / systems
        f_sys = ctk.CTkFrame(self, fg_color="transparent")
        f_sys.pack(pady=5, padx=50, fill="x")
        self.boosted_cb = ctk.CTkComboBox(f_sys, values=["","YES","NO"], **entry_kwargs)
        self.boosted_cb.set("")
        self.boosted_cb.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.power_in = ctk.CTkEntry(f_sys, placeholder_text="POWER CONSUMPTION", **entry_kwargs)
        self.power_in.pack(side="left", fill="x", expand=True, padx=5)
        self.cm_in = ctk.CTkEntry(f_sys, placeholder_text="CM DECOY/NOISE", **entry_kwargs)
        self.cm_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        # HP / Cargo / mass
        f_stats2 = ctk.CTkFrame(self, fg_color="transparent")
        f_stats2.pack(pady=5, padx=50, fill="x")
        self.hp_in = ctk.CTkEntry(f_stats2, placeholder_text="HP", **entry_kwargs)
        self.hp_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.cargo_in = ctk.CTkEntry(f_stats2, placeholder_text="CARGO", **entry_kwargs)
        self.cargo_in.pack(side="left", fill="x", expand=True, padx=5)
        self.dim_in = ctk.CTkEntry(f_stats2, placeholder_text="DIMENSIONS", **entry_kwargs)
        self.dim_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        f_misc = ctk.CTkFrame(self, fg_color="transparent")
        f_misc.pack(pady=5, padx=50, fill="x")
        self.mass_in = ctk.CTkEntry(f_misc, placeholder_text="MASS", **entry_kwargs)
        self.mass_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.h2_in = ctk.CTkEntry(f_misc, placeholder_text="HYDROGEN CAPACITY", **entry_kwargs)
        self.h2_in.pack(side="left", fill="x", expand=True, padx=5)
        self.qt_in = ctk.CTkEntry(f_misc, placeholder_text="QT FUEL CAPACITY", **entry_kwargs)
        self.qt_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        f_times = ctk.CTkFrame(self, fg_color="transparent")
        f_times.pack(pady=5, padx=50, fill="x")
        self.expedition_in = ctk.CTkEntry(f_times, placeholder_text="EXPEDITION FEE", **entry_kwargs)
        self.expedition_in.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.claim_time_in = ctk.CTkEntry(f_times, placeholder_text="CLAIM TIME", **entry_kwargs)
        self.claim_time_in.pack(side="left", fill="x", expand=True, padx=5)
        self.expedite_time_in = ctk.CTkEntry(f_times, placeholder_text="EXPEDITE TIME", **entry_kwargs)
        self.expedite_time_in.pack(side="right", fill="x", expand=True, padx=(5,0))

        self.btn_save = DrakeButton(self, text="SAVE SHIP", command=self.save_ship, height=45)
        self.btn_save.pack(pady=10, padx=50, fill="x")

        f_btns = ctk.CTkFrame(self, fg_color="transparent")
        f_btns.pack(fill="x", padx=50)
        ctk.CTkButton(f_btns, text="IMPORT CSV", command=self.import_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(f_btns, text="EXPORT CSV", command=self.export_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(f_btns, text="CLEAR", command=self.clear_fields, fg_color="#441111", corner_radius=0).pack(side="left", expand=True, padx=2)

    def save_ship(self):
        name = (self.name_in.get() or "").strip().upper()
        if not name:
            return
        brand = (self.brand_in.get() or "").upper()
        role = (self.role_in.get() or "").upper()
        career = (self.career_in.get() or "").upper()
        size = (self.size_in.get() or "")
        crew = (self.crew_in.get() or 0)
        scm = (self.scm_in.get() or "")
        scm_bf = (self.scm_bf_in.get() or "")
        scm_bb = (self.scm_bb_in.get() or "")
        nav = (self.nav_in.get() or "")
        pitch = (self.pitch_in.get() or "")
        yaw = (self.yaw_in.get() or "")
        roll = (self.roll_in.get() or "")
        boosted = (self.boosted_cb.get() or "")
        power = (self.power_in.get() or "")
        cm = (self.cm_in.get() or "")
        hp = (self.hp_in.get() or 0)
        cargo = (self.cargo_in.get() or "")
        dimensions = (self.dim_in.get() or "")
        mass = (self.mass_in.get() or "")
        h2 = (self.h2_in.get() or "")
        qt = (self.qt_in.get() or "")
        expedition = (self.expedition_in.get() or "")
        claim_time = (self.claim_time_in.get() or "")
        expedite_time = (self.expedite_time_in.get() or "")

        sql = """INSERT INTO ships (name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, scm_boost_backward,
                 nav_max_speed, pitch, yaw, roll, boosted, power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass,
                 hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(name) DO UPDATE SET brand=excluded.brand, role=excluded.role, career=excluded.career, size=excluded.size,
                 crew_size=excluded.crew_size, scm_speed=excluded.scm_speed, scm_boost_forward=excluded.scm_boost_forward, scm_boost_backward=excluded.scm_boost_backward,
                 nav_max_speed=excluded.nav_max_speed, pitch=excluded.pitch, yaw=excluded.yaw, roll=excluded.roll, boosted=excluded.boosted,
                 power_consumption=excluded.power_consumption, cm_decoy_noise=excluded.cm_decoy_noise, hp=excluded.hp, cargo=excluded.cargo, dimensions=excluded.dimensions, mass=excluded.mass,
                 hydrogen_capacity=excluded.hydrogen_capacity, qt_fuel_capacity=excluded.qt_fuel_capacity, expedition_fee=excluded.expedition_fee, claim_time=excluded.claim_time, expedite_time=excluded.expedite_time"""

        params = (
            name, brand, role, career, size, crew, scm, scm_bf, scm_bb,
            nav, pitch, yaw, roll, boosted, power, cm, hp, cargo, dimensions, mass,
            h2, qt, expedition, claim_time, expedite_time
        )
        try:
            self.controller.db.commit(sql, params)
            DrakePopup.info("SUCCESS", f"Ship {name} saved.", parent=self)
            if hasattr(self.controller, "log"):
                try:
                    self.controller.log(f"Saved ship: {name}", source="SHIP")
                except Exception:
                    pass
        except Exception as e:
            DrakePopup.error("ERROR", str(e), parent=self)

    def load_ship(self, event=None):
        name = (self.name_in.get() or "").strip().upper()
        if not name:
            return
        rows = self.controller.db.query("SELECT * FROM ships WHERE name = ?", (name,))
        if not rows:
            DrakePopup.info("NOT FOUND", f"No ship found: {name}", parent=self)
            return
        r = rows[0]
        # fill fields according to columns order in DB (name, brand, role, career, size, crew_size, scm_speed, ...)
        self.name_in.delete(0, "end"); self.name_in.insert(0, r[0] or "")
        self.brand_in.delete(0, "end"); self.brand_in.insert(0, r[1] or "")
        self.role_in.delete(0, "end"); self.role_in.insert(0, r[2] or "")
        self.career_in.delete(0, "end"); self.career_in.insert(0, r[3] or "")
        self.size_in.delete(0, "end"); self.size_in.insert(0, r[4] or "")
        self.crew_in.delete(0, "end"); self.crew_in.insert(0, str(r[5] or 0))
        self.scm_in.delete(0, "end"); self.scm_in.insert(0, r[6] or "")
        self.scm_bf_in.delete(0, "end"); self.scm_bf_in.insert(0, r[7] or "")
        self.scm_bb_in.delete(0, "end"); self.scm_bb_in.insert(0, r[8] or "")
        self.nav_in.delete(0, "end"); self.nav_in.insert(0, r[9] or "")
        self.pitch_in.delete(0, "end"); self.pitch_in.insert(0, r[10] or "")
        self.yaw_in.delete(0, "end"); self.yaw_in.insert(0, r[11] or "")
        self.roll_in.delete(0, "end"); self.roll_in.insert(0, r[12] or "")
        self.boosted_cb.set(r[13] or "")
        self.power_in.delete(0, "end"); self.power_in.insert(0, r[14] or "")
        self.cm_in.delete(0, "end"); self.cm_in.insert(0, r[15] or "")
        self.hp_in.delete(0, "end"); self.hp_in.insert(0, str(r[16] or 0))
        self.cargo_in.delete(0, "end"); self.cargo_in.insert(0, r[17] or "")
        self.dim_in.delete(0, "end"); self.dim_in.insert(0, r[18] or "")
        self.mass_in.delete(0, "end"); self.mass_in.insert(0, r[19] or "")
        self.h2_in.delete(0, "end"); self.h2_in.insert(0, r[20] or "")
        self.qt_in.delete(0, "end"); self.qt_in.insert(0, r[21] or "")
        self.expedition_in.delete(0, "end"); self.expedition_in.insert(0, r[22] or "")
        self.claim_time_in.delete(0, "end"); self.claim_time_in.insert(0, r[23] or "")
        self.expedite_time_in.delete(0, "end"); self.expedite_time_in.insert(0, r[24] or "")
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(f"Loaded ship: {name}", source="SHIP")
        except Exception:
            pass

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    self.controller.db.commit(
                        "INSERT OR REPLACE INTO ships (name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, scm_boost_backward, nav_max_speed, pitch, yaw, roll, boosted, power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass, hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
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
                            row.get("boosted", ""),
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
                        ),
                    )
            DrakePopup.info("SUCCESS", "Import terminé.", parent=self)
        except Exception as e:
            DrakePopup.error("ERROR", str(e), parent=self)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        data = self.controller.db.query("SELECT * FROM ships")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["name","brand","role","career","size","crew_size","scm_speed","scm_boost_forward","scm_boost_backward","nav_max_speed","pitch","yaw","roll","boosted","power_consumption","cm_decoy_noise","hp","cargo","dimensions","mass","hydrogen_capacity","qt_fuel_capacity","expedition_fee","claim_time","expedite_time"])
            writer.writerows(data)
        DrakePopup.info("SUCCESS", "Données exportées.", parent=self)

    def clear_fields(self):
        for e in [self.name_in, self.brand_in, self.role_in, self.career_in, self.size_in, self.crew_in, self.scm_in, self.scm_bf_in, self.scm_bb_in, self.nav_in, self.pitch_in, self.yaw_in, self.roll_in, self.power_in, self.cm_in, self.hp_in, self.cargo_in, self.dim_in, self.mass_in, self.h2_in, self.qt_in, self.expedition_in, self.claim_time_in, self.expedite_time_in]:
            e.delete(0, "end")
        self.boosted_cb.set("")
