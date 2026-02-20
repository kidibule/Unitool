"""Frame pour la gestion des archives / logs et import/export CSV."""

import customtkinter as ctk
import csv
from datetime import datetime
from tkinter import filedialog

# Importation des ressources graphiques
from drake_ui.engine import DrakeConfig, DrakeButton, DrakePopup


class LoggerFrame(ctk.CTkFrame):
    """Permet de créer/mettre à jour des dossiers, importer/exporter CSV.

    Le `controller` doit exposer `db` avec les méthodes `commit` et `query`.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- TITRE ---
        DrakeConfig.create_title(self, "INTEL ARCHIVE SYSTEM - ADVANCED ENCODING")

        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 35,
        }

        # --- 1. IDENTITÉ & MENACE ---
        f_top = ctk.CTkFrame(self, fg_color="transparent")
        f_top.pack(pady=(0, 10), padx=50, fill="x")

        self.p_in = ctk.CTkEntry(
            f_top, placeholder_text="TARGET HANDLE", **entry_kwargs
        )
        self.p_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.p_in.bind("<Return>", self.load_target)

        self.threat_in = ctk.CTkComboBox(
            f_top,
            values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            font=DrakeConfig.FONT_UI,
            fg_color=DrakeConfig.BG_TERMINAL,
            button_color=DrakeConfig.ACCENT_PRIMARY,
            corner_radius=0,
            width=120,
        )
        self.threat_in.pack(side="right")
        self.threat_in.set("LOW")

        # --- 2. DONNÉES RSI (ORG, SID, RANK) ---
        f_rsi = ctk.CTkFrame(self, fg_color="transparent")
        f_rsi.pack(pady=5, padx=50, fill="x")
        self.o_in = ctk.CTkEntry(f_rsi, placeholder_text="ORGANIZATION", **entry_kwargs)
        self.o_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.sid_in = ctk.CTkEntry(f_rsi, placeholder_text="SID", **entry_kwargs)
        self.sid_in.pack(side="left", fill="x", expand=True, padx=5)
        self.rank_in = ctk.CTkEntry(f_rsi, placeholder_text="RANK", **entry_kwargs)
        self.rank_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # --- 3. INFOS COMPLÉMENTAIRES ---
        f_info = ctk.CTkFrame(self, fg_color="transparent")
        f_info.pack(pady=5, padx=50, fill="x")
        self.lang_in = ctk.CTkEntry(f_info, placeholder_text="LANGUAGE", **entry_kwargs)
        self.lang_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.aff_in = ctk.CTkEntry(
            f_info, placeholder_text="AFFILIATES", **entry_kwargs
        )
        self.aff_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # --- 4. COMBAT STATS (WINS / LOSSES) ---
        f_stats = ctk.CTkFrame(self, fg_color="transparent")
        f_stats.pack(pady=5, padx=50, fill="x")
        self.wins_in = ctk.CTkEntry(f_stats, placeholder_text="WINS", **entry_kwargs)
        self.wins_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.loss_in = ctk.CTkEntry(f_stats, placeholder_text="LOSSES", **entry_kwargs)
        self.loss_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # --- 5. ALIGNEMENT & PROFIL ---
        self.a_btn = ctk.CTkSegmentedButton(
            self,
            values=["AMI", "NEUTRE", "ENNEMI"],
            font=DrakeConfig.FONT_UI,
            selected_color=DrakeConfig.ACCENT_PRIMARY,
            unselected_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
        )
        self.a_btn.pack(pady=10)

        f_combat = ctk.CTkFrame(self, fg_color="transparent")
        f_combat.pack(pady=5, padx=50, fill="x")
        self.pvp_in = ctk.CTkComboBox(
            f_combat, values=["NOOB", "ROOKIE", "VETERAN", "ACE"], **entry_kwargs
        )
        self.pvp_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.act_in = ctk.CTkComboBox(
            f_combat,
            values=["PIRATE", "BOUNTY HUNTER", "MINEUR", "TRADER"],
            **entry_kwargs,
        )
        self.act_in.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.s_in = ctk.CTkEntry(self, placeholder_text="CURRENT SHIP", **entry_kwargs)
        self.s_in.pack(pady=5, padx=50, fill="x")

        # --- 6. NOTES ---
        self.n_in = ctk.CTkTextbox(
            self,
            height=80,
            font=DrakeConfig.FONT_LOGS,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            corner_radius=0,
        )
        self.n_in.pack(pady=10, padx=50, fill="x")

        # --- BOUTONS ---
        self.btn_save = DrakeButton(
            self, text="SYNCHRONIZE DATABASE", command=self.save, height=45
        )
        self.btn_save.pack(pady=10, padx=50, fill="x")

        f_btns = ctk.CTkFrame(self, fg_color="transparent")
        f_btns.pack(fill="x", padx=50)
        ctk.CTkButton(
            f_btns,
            text="IMPORT CSV",
            command=self.import_csv,
            fg_color="#222",
            corner_radius=0,
        ).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            f_btns,
            text="EXPORT CSV",
            command=self.export_csv,
            fg_color="#222",
            corner_radius=0,
        ).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(
            f_btns,
            text="CLEAR",
            command=self.clear_fields,
            fg_color="#441111",
            corner_radius=0,
        ).pack(side="left", expand=True, padx=2)

    def save(self):
        h = self.p_in.get().strip().upper()
        if not h:
            return
        # Prepare values and sanitize
        org_val = (self.o_in.get() or "").upper()
        sid_val = (self.sid_in.get() or "").upper()
        rank_val = (self.rank_in.get() or "").upper()
        lang_val = (self.lang_in.get() or "").upper()
        aff_val = (self.aff_in.get() or "").upper()
        align_val = self.a_btn.get() or "NEUTRE"
        ship_val = (self.s_in.get() or "").upper()
        pvp_val = (self.pvp_in.get() or "").upper()
        if pvp_val not in ("NOOB", "ROOKIE", "VETERAN", "ACE"):
            pvp_val = "Inconnu"
        act_val = (self.act_in.get() or "").upper()
        notes_val = self.n_in.get("0.0", "end").strip()
        date_val = datetime.now().strftime("%d/%m/%Y")
        threat_val = self.threat_in.get()
        wins_val = self.wins_in.get() or 0
        losses_val = self.loss_in.get() or 0

        try:
            wins_val = int(self.wins_in.get().strip()) if self.wins_in.get().strip() else 0
        except ValueError:
            wins_val = 0
            self.wins_in.delete(0, "end")
            self.wins_in.insert(0, "0")

        try:
            losses_val = int(self.loss_in.get().strip()) if self.loss_in.get().strip() else 0
        except ValueError:
            losses_val = 0
            self.loss_in.delete(0, "end")
            self.loss_in.insert(0, "0")

        # Check existing record to avoid duplicates
        existing = self.controller.db.query(
            "SELECT org, sid, org_rank, language, affiliates, alignment, ship, pvp_lvl, activity, notes, threat, wins, losses FROM targets WHERE pseudo = ?",
            (h,)
        )

        if existing:
            row = existing[0]
            same = (
                ((row[0] or "").upper() == org_val) and
                ((row[1] or "").upper() == sid_val) and
                ((row[2] or "").upper() == rank_val) and
                ((row[3] or "").upper() == lang_val) and
                ((row[4] or "").upper() == aff_val) and
                ((row[5] or "").upper() == align_val) and
                ((row[6] or "").upper() == ship_val) and
                ((row[7] or "").upper() == pvp_val) and
                ((row[8] or "").upper() == act_val) and
                (row[9] == notes_val) and
                (row[10] == threat_val) and
                (str(row[11]) == str(wins_val)) and
                (str(row[12]) == str(losses_val))
            )
            if same:
                DrakePopup.info("DRAKE SYSTEMS", f"Aucune modification trouvée pour {h}. Aucune sauvegarde effectuée.", parent=self)
                try:
                    if hasattr(self.controller, "log"):
                        self.controller.log(f"Save skipped (no change): {h}", source="LOGGER")
                except Exception:
                    pass
                return
            else:
                confirm = DrakePopup.yesno("CONFIRMATION", f"Le dossier {h} existe déjà. Écraser les données ?", parent=self)
                if not confirm:
                    return

        sql = """INSERT INTO targets (pseudo, org, sid, org_rank, language, affiliates, alignment, ship, pvp_lvl, activity, notes, date, threat, wins, losses)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(pseudo) DO UPDATE SET org=excluded.org, sid=excluded.sid, org_rank=excluded.org_rank, language=excluded.language, 
                 affiliates=excluded.affiliates, alignment=excluded.alignment, ship=excluded.ship, pvp_lvl=excluded.pvp_lvl, 
                 activity=excluded.activity, notes=excluded.notes, date=excluded.date, threat=excluded.threat, wins=excluded.wins, losses=excluded.losses"""

        params = (
            h,
            org_val,
            sid_val,
            rank_val,
            lang_val,
            aff_val,
            align_val,
            ship_val,
            pvp_val,
            act_val,
            notes_val,
            date_val,
            threat_val,
            wins_val,
            losses_val,
        )

        self.controller.db.commit(sql, params)
        DrakePopup.info("DRAKE SYSTEMS", f"Dossier {h} synchronisé.", parent=self)
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(f"Synchronized dossier: {h}", source="LOGGER")
        except Exception:
            pass

    def load_target(self, event=None):
        pseudo = self.p_in.get().strip().upper()
        rows = self.controller.db.query(
            "SELECT * FROM targets WHERE pseudo = ?", (pseudo,)
        )
        if rows:
            r = rows[0]
            # Remplissage des champs selon l'ordre des colonnes dans la table
            self.o_in.delete(0, "end")
            self.o_in.insert(0, r[1] or "")
            self.s_in.delete(0, "end")
            self.s_in.insert(0, r[2] or "")
            self.threat_in.set(r[3] or "LOW")
            self.n_in.delete("0.0", "end")
            self.n_in.insert("0.0", r[4] or "")
            self.wins_in.delete(0, "end")
            self.wins_in.insert(0, str(r[6] or 0))
            self.loss_in.delete(0, "end")
            self.loss_in.insert(0, str(r[7] or 0))
            self.a_btn.set(r[8] or "NEUTRE")
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"Loaded dossier: {pseudo}", source="LOGGER")
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
                        "INSERT OR REPLACE INTO targets (pseudo, org, ship, threat, notes, alignment) VALUES (?,?,?,?,?,?)",
                        (
                            row["pseudo"].upper(),
                            row["org"],
                            row["ship"],
                            row["threat"],
                            row["notes"],
                            row["alignment"],
                        ),
                    )
            DrakePopup.info("SUCCESS", "Import terminé.", parent=self)
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"Imported CSV: {path}", source="LOGGER")
            except Exception:
                pass
        except Exception as e:
            DrakePopup.error("ERROR", str(e), parent=self)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        data = self.controller.db.query("SELECT * FROM targets")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                [
                    "pseudo",
                    "org",
                    "ship",
                    "threat",
                    "notes",
                    "date",
                    "wins",
                    "losses",
                    "alignment",
                ]
            )
            writer.writerows(data)
        DrakePopup.info("SUCCESS", "Données exportées.", parent=self)
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(f"Exported CSV to: {path}", source="LOGGER")
        except Exception:
            pass

    def clear_fields(self):
        for e in [
            self.p_in,
            self.o_in,
            self.sid_in,
            self.rank_in,
            self.lang_in,
            self.aff_in,
            self.s_in,
            self.wins_in,
            self.loss_in,
        ]:


            self.threat_in.set("LOW")
            self.pvp_in.set("NOOB")
            self.a_btn.set("NEUTRE")

            e.delete(0, "end")
            self.n_in.delete("0.0", "end")


            self.focus_set()

        try:
            if hasattr(self.controller, "log"):
                self.controller.log("Cleared logger UI fields", source="LOGGER")
        except Exception:
            pass
