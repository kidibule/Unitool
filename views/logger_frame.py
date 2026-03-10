"""Frame pour la gestion des archives / logs et import/export CSV."""

import customtkinter as ctk
import csv
from datetime import datetime
from tkinter import filedialog
from drake_ui.engine import DrakeConfig, DrakeButton, DrakePopup, DrakeComboBox, DrakeEntry
from controllers.ship_controller import ShipController


class LoggerFrame(ctk.CTkFrame):
    """Vue d'archivage : saisie, import/export et maintenance des dossiers."""

    def __init__(self, parent, controller):
        """Initialise les onglets Players/Organizations/Ships."""
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.ship_controller = ShipController(self.controller)

        # --- TITRE ---
        DrakeConfig.create_title(self, "INTEL ARCHIVE SYSTEM")

        # --- SYSTÈME D'ONGLETS ---
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color=DrakeConfig.BG_PANEL, 
            segmented_button_selected_color=DrakeConfig.ACCENT_PRIMARY,
            segmented_button_selected_hover_color="#e67e22",
            text_color="white"
        )
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tabview.add("PLAYERS")
        self.tabview.add("ORGANIZATIONS")
        self.tabview.add("SHIPS")

        self.tab_targets = self.tabview.tab("PLAYERS")
        self.tab_orgs = self.tabview.tab("ORGANIZATIONS")
        self.tab_ships = self.tabview.tab("SHIPS")

        # Appels des setups
        self.setup_targets_tab()
        self.setup_orgs_tab()
        self.setup_ships_tab()


    def setup_orgs_tab(self):

        """Formulaire Orga avec marges augmentées et titre de section pour les notes"""
        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 35,
            "border_width": 1
        }
        
        # --- SECTION 1 : IDENTITÉ (Marge 50 comme Target) ---
        f_top = ctk.CTkFrame(self.tab_orgs, fg_color="transparent")
        f_top.pack(pady=(20, 5), padx=50, fill="x")

        self.org_sid = DrakeEntry(f_top, placeholder_text="SID (RSI URL ID)", **entry_kwargs)
        self.org_sid.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.org_tag = DrakeEntry(f_top, placeholder_text="TAG (ex: UEE)", width=120, **entry_kwargs)
        self.org_tag.pack(side="right")

        self.org_name = DrakeEntry(self.tab_orgs, placeholder_text="ORGANIZATION NAME", **entry_kwargs)
        self.org_name.pack(pady=5, padx=50, fill="x")

        # --- SECTION 2 : TYPE & ALIGNEMENT ---
        f_type_align = ctk.CTkFrame(self.tab_orgs, fg_color="transparent")
        f_type_align.pack(pady=5, padx=50, fill="x")

        self.org_type = DrakeComboBox(f_type_align, values=["ORGANIZATION", "SYNDICATE", "FACTION", "PMC"])
        self.org_type.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.org_type.set("ORGANIZATION")

        self.org_align = DrakeComboBox(f_type_align, values=["NEUTRE", "AMI", "ENNEMI"])
        self.org_align.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.org_align.set("NEUTRE")

        # --- SECTION 3 : SPÉCIALISATION & DIPLOMATIE ---
        self.org_spec = DrakeEntry(self.tab_orgs, placeholder_text="SPECIALIZATION", **entry_kwargs)
        self.org_spec.pack(pady=5, padx=50, fill="x")

        f_diplomacy = ctk.CTkFrame(self.tab_orgs, fg_color="transparent")
        f_diplomacy.pack(pady=5, padx=50, fill="x")

        self.org_allies = DrakeEntry(f_diplomacy, placeholder_text="ALLIES (TAGS)", **entry_kwargs)
        self.org_allies.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.org_enemies = DrakeEntry(f_diplomacy, placeholder_text="ENEMIES (TAGS)", **entry_kwargs)
        self.org_enemies.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # --- SECTION 4 : NOTES (Avec titre de section) ---
        ctk.CTkLabel(self.tab_orgs, text="MANIFEST & INTELLIGENCE NOTES", 
                     font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(10, 2), padx=50)
        
        self.org_desc = ctk.CTkTextbox(self.tab_orgs, height=120, fg_color=DrakeConfig.BG_TERMINAL, 
                                       border_width=1, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
        self.org_desc.pack(pady=(0, 10), padx=50, fill="x")

        # --- BOUTONS D'ACTION ---
        self.btn_save_org = DrakeButton(self.tab_orgs, text="REGISTER ORGANIZATION", command=self.save_org, height=45)
        self.btn_save_org.pack(pady=10, padx=50, fill="x")

        f_utils = ctk.CTkFrame(self.tab_orgs, fg_color="transparent")
        f_utils.pack(fill="x", padx=50, pady=(0, 20))
        
        DrakeButton(f_utils, text="IMPORT CSV", command=self.import_orgs_csv, 
                fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_utils, text="EXPORT CSV", command=self.export_orgs_csv, 
                fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_utils, text="CLEAR", command=self.clear_org_fields, 
                fg_color="#441111", corner_radius=0).pack(side="left", expand=True, padx=2)

    # --- LOGIQUE DE SAUVEGARDE ET UTILITAIRES POUR LES ORGAS ---

    def save_org(self):
        """Sauvegarde les données de l'onglet Organisation"""
        sid = self.org_sid.get().strip().upper()
        name = self.org_name.get().strip()
        
        if not sid or not name:
            self.controller.log("SID and Name are mandatory for registration.", source="SYSTEM ERROR")
            return

        try:
            self.controller.logger.save_organization(
                sid=sid,
                name=name,
                tag=self.org_tag.get(),
                description=self.org_desc.get("0.0", "end").strip(),
                org_type=self.org_type.get(),
                specialization=self.org_spec.get(),
                allies=self.org_allies.get(),
                enemies=self.org_enemies.get(),
                alignment=self.org_align.get(),
                updated_at=datetime.now().strftime("%d/%m/%Y"),
            )
            self.controller.log(f"Corporate file {sid} synchronized.", source="SYSTEM")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Org registered: {sid}", source="SYSTEM")
            self.clear_org_fields() 
        except Exception as e:
            self.controller.log(f"Failed to save organization: {e}", source="SYSTEM ERROR")

    def import_orgs_csv(self):
        """Importation CSV pour les organisations"""
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                self.controller.logger.import_organizations_csv(list(reader))
            self.controller.log("Organization import completed.", source="DATA")
        except Exception as e:
            self.controller.log(str(e), source="DATA ERROR")

    def export_orgs_csv(self):
        """Exportation CSV pour les organisations"""
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        data = self.controller.logger.export_organizations_csv()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["sid", "name", "tag", "alignment"])
            writer.writerows(data)
        self.controller.log(f"Organizations database exported to {path}", source="DATA")

    def clear_org_fields(self):
        """Réinitialise tous les champs de l'onglet Organisation"""
        self.org_sid.delete(0, "end")
        self.org_name.delete(0, "end")
        self.org_tag.delete(0, "end")
        self.org_spec.delete(0, "end")
        self.org_allies.delete(0, "end")
        self.org_enemies.delete(0, "end")
        self.org_desc.delete("0.0", "end")
        self.org_type.set("ORGANIZATION")
        self.org_align.set("NEUTRE")
        self.focus_set()

    def setup_targets_tab(self):
        
        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 35,
            "border_width": 1
        }

        # --- 1. IDENTITÉ & MENACE ---
        f_top = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_top.pack(pady=(20, 10), padx=50, fill="x")

        self.p_in = DrakeEntry(f_top, placeholder_text="TARGET HANDLE", **entry_kwargs)
        self.p_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.p_in.bind("<Return>", self.load_target)

        self.threat_in = DrakeComboBox(f_top, values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],)

        self.threat_in.pack(side="right")
        self.threat_in.set("LOW")

        # --- 2. DONNÉES RSI (ORG, SID, RANK) ---
        f_rsi = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_rsi.pack(pady=5, padx=50, fill="x")
        self.o_in = DrakeEntry(f_rsi, placeholder_text="ORGANIZATION", **entry_kwargs)
        self.o_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.sid_in = DrakeEntry(f_rsi, placeholder_text="SID", **entry_kwargs)
        self.sid_in.pack(side="left", fill="x", expand=True, padx=5)
        self.rank_in = DrakeEntry(f_rsi, placeholder_text="RANK", **entry_kwargs)
        self.rank_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # --- 3. INFOS COMPLÉMENTAIRES ---
        f_info = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_info.pack(pady=5, padx=50, fill="x")
        self.lang_in = DrakeEntry(f_info, placeholder_text="LANGUAGE", **entry_kwargs)
        self.lang_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.aff_in = DrakeEntry(f_info, placeholder_text="AFFILIATES", **entry_kwargs)
        self.aff_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # --- 4. COMBAT STATS (WINS / LOSSES) ---
        f_stats = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_stats.pack(pady=5, padx=50, fill="x")
        self.wins_in = DrakeEntry(f_stats, placeholder_text="WINS", **entry_kwargs)
        self.wins_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.loss_in = DrakeEntry(f_stats, placeholder_text="LOSSES", **entry_kwargs)
        self.loss_in.pack(side="left", fill="x", expand=True, padx=(5, 0))

        #--- 5. ALIGNEMENT & PROFIL ---
        self.a_btn = DrakeComboBox(
            self.tab_targets,
            values=["AMI", "NEUTRE", "ENNEMI"]
        )

        self.a_btn.pack(pady=(5, 10), padx=50, fill="x")
        self.a_btn.set("NEUTRE")

        f_combat = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_combat.pack(pady=5, padx=50, fill="x")
        self.pvp_in = DrakeComboBox(
            f_combat, 
            values=["NOOB", "ROOKIE", "VETERAN", "ACE"],
)
        self.pvp_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.act_in = DrakeComboBox(
            f_combat,
            values=["PIRATE", "BOUNTY HUNTER", "MINER", "TRADER"]
        )
        self.act_in.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.s_in = DrakeEntry(self.tab_targets, placeholder_text="CURRENT SHIP", **entry_kwargs)
        self.s_in.pack(pady=5, padx=50, fill="x")

        # --- 6. NOTES ---
        self.n_in = ctk.CTkTextbox(
            self.tab_targets,
            height=80,
            font=DrakeConfig.FONT_LOGS,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            corner_radius=0,
        )
        self.n_in.pack(pady=10, padx=50, fill="x")

        # --- BOUTONS ---
        self.btn_save = DrakeButton(self.tab_targets, text="SYNCHRONIZE DATABASE", command=self.save, height=45)
        self.btn_save.pack(pady=10, padx=50, fill="x")

        f_btns = ctk.CTkFrame(self.tab_targets, fg_color="transparent")
        f_btns.pack(fill="x", padx=50, pady=(0, 20))
        
        DrakeButton(f_btns, text="IMPORT CSV", command=self.import_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_btns, text="EXPORT CSV", command=self.export_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_btns, text="CLEAR", command=self.clear_fields, fg_color="#441111", corner_radius=0).pack(side="left", expand=True, padx=2)

    def save(self):
        h = self.p_in.get().strip().upper()
        if not h:
            return
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

        existing = self.controller.logger.get_target_comparison_row(h)

        if existing:
            row = existing
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
                try:
                    self.controller.logger.sync_ship_to_catalog(ship_val)
                except Exception:
                    pass
                DrakePopup.info("SYSTEMS", f"No changes found for {h}. No save performed.", parent=self)
                try:
                    if hasattr(self.controller, "log"):
                        self.controller.log(f"Save skipped (no change): {h}", source="SYSTEM")
                except Exception:
                    pass
                return
            else:
                confirm = DrakePopup.yesno("CONFIRMATION", f"File {h} already exists. Overwrite data?", parent=self)
                if not confirm:
                    return

        self.controller.logger.save_target(
            pseudo=h,
            org=org_val,
            sid=sid_val,
            org_rank=rank_val,
            language=lang_val,
            affiliates=aff_val,
            alignment=align_val,
            ship=ship_val,
            pvp_lvl=pvp_val,
            activity=act_val,
            notes=notes_val,
            threat=threat_val,
            wins=wins_val,
            losses=losses_val,
        )
        DrakePopup.info("SYSTEMS", f"File {h} synchronized.", parent=self)
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(f"Synchronized file: {h}", source="SYSTEM")
        except Exception:
            pass

    def load_target(self, event=None):
        pseudo = self.p_in.get().strip().upper()
        r = self.controller.logger.load_target_row(pseudo)
        if r:
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
                    self.controller.log(f"Loaded file: {pseudo}", source="SYSTEM")
            except Exception:
                pass

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                self.controller.logger.import_targets_csv(list(reader))
                self.controller.log("Import completed.", source="DATA")
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"Imported CSV: {path}", source="DATA")
            except Exception:
                pass
        except Exception as e:
            self.controller.log(str(e), source="DATA ERROR")

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        data = self.controller.logger.export_targets_csv()
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
        self.controller.log("Data exported.", source="DATA")
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(f"Exported CSV to: {path}", source="DATA")
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
                self.controller.log("Cleared logger UI fields", source="SYSTEM")
        except Exception:
            pass

    def setup_ships_tab(self):
        """Configuration complète de l'onglet SHIP MANAGEMENT (27 paramètres)"""
        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 30,
        }

        # --- VALEURS STANDARDS ---
        CAREER_OPTIONS = ["COMBAT", "TRANSPORT", "EXPLORATION", "INDUSTRIAL", "SUPPORT", "COMPETITION", "RESEARCH"]
        ROLE_OPTIONS = [
            "LIGHT FIGHTER", "MEDIUM FIGHTER", "HEAVY FIGHTER", "BOMBER", 
            "FREIGHTER", "DATA RUNNER", "MINING", "SALVAGE", "REFUELING",
            "MEDICAL", "SNUB", "DROP SHIP", "INTERDICTION", "PATROL"
        ]

        # --- HEADER & IDENTITY ---
        f_identity = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_identity.pack(pady=(20, 5), padx=50, fill="x")

        self.ship_name = DrakeEntry(f_identity, placeholder_text="SHIP NAME (Press Enter to Load)", **entry_kwargs)
        self.ship_name.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ship_name.bind("<Return>", self.load_ship)

        self.ship_brand = DrakeEntry(f_identity, placeholder_text="MANUFACTURER", **entry_kwargs)
        self.ship_brand.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # --- ROLE & SPECS ---
        f_role = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_role.pack(pady=5, padx=50, fill="x")
        
        self.ship_role = DrakeComboBox(
            f_role, 
            values=ROLE_OPTIONS,
        )
        self.ship_role.set("ROLE") # Placeholder
        self.ship_role.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        self.ship_career = DrakeComboBox(
            f_role, 
            values=CAREER_OPTIONS, 
        )
        self.ship_career.set("CAREER") # Placeholder
        self.ship_career.pack(side="left", fill="x", expand=True, padx=5)
        
        self.ship_size = DrakeEntry(f_role, placeholder_text="SIZE (1-6)", width=80, **entry_kwargs)
        self.ship_size.pack(side="left", padx=5)
        
        self.ship_crew = DrakeEntry(f_role, placeholder_text="CREW", width=80, **entry_kwargs)
        self.ship_crew.pack(side="right", padx=(5,0))

        # --- SECTION : PROPULSION & SPEED ---
        self._add_section_title(self.tab_ships, "PROPULSION & NAVIGATION")
        
        f_prop = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_prop.pack(pady=5, padx=50, fill="x")
        self.ship_scm = DrakeEntry(f_prop, placeholder_text="SCM SPEED", **entry_kwargs)
        self.ship_scm.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.ship_scm_bf = DrakeEntry(f_prop, placeholder_text="BOOST FWD", **entry_kwargs)
        self.ship_scm_bf.pack(side="left", fill="x", expand=True, padx=5)
        self.ship_scm_bb = DrakeEntry(f_prop, placeholder_text="BOOST BWD", **entry_kwargs)
        self.ship_scm_bb.pack(side="right", fill="x", expand=True, padx=(5,0))

        f_nav = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_nav.pack(pady=5, padx=50, fill="x")
        self.ship_nav = DrakeEntry(f_nav, placeholder_text="NAV MAX SPEED", **entry_kwargs)
        self.ship_nav.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.ship_h2 = DrakeEntry(f_nav, placeholder_text="HYDROGEN CAP", **entry_kwargs)
        self.ship_h2.pack(side="left", fill="x", expand=True, padx=5)
        self.ship_qt = DrakeEntry(f_nav, placeholder_text="QT FUEL CAP", **entry_kwargs)
        self.ship_qt.pack(side="right", fill="x", expand=True, padx=(5,0))

        # --- SECTION : MANEUVERABILITY (Standard vs Boosted) ---
        self._add_section_title(self.tab_ships, "FLIGHT DYNAMICS (PITCH / YAW / ROLL)")
        
        f_dyn = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_dyn.pack(pady=5, padx=50, fill="x")
        self.ship_pitch = DrakeEntry(f_dyn, placeholder_text="PITCH", **entry_kwargs)
        self.ship_pitch.pack(side="left", fill="x", expand=True, padx=(0,2))
        self.ship_yaw = DrakeEntry(f_dyn, placeholder_text="YAW", **entry_kwargs)
        self.ship_yaw.pack(side="left", fill="x", expand=True, padx=2)
        self.ship_roll = DrakeEntry(f_dyn, placeholder_text="ROLL", **entry_kwargs)
        self.ship_roll.pack(side="right", fill="x", expand=True, padx=(2,0))

        f_dyn_b = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_dyn_b.pack(pady=5, padx=50, fill="x")
        self.ship_b_pitch = DrakeEntry(f_dyn_b, placeholder_text="B. PITCH", **entry_kwargs)
        self.ship_b_pitch.pack(side="left", fill="x", expand=True, padx=(0,2))
        self.ship_b_yaw = DrakeEntry(f_dyn_b, placeholder_text="B. YAW", **entry_kwargs)
        self.ship_b_yaw.pack(side="left", fill="x", expand=True, padx=2)
        self.ship_b_roll = DrakeEntry(f_dyn_b, placeholder_text="B. ROLL", **entry_kwargs)
        self.ship_b_roll.pack(side="right", fill="x", expand=True, padx=(2,0))

        # --- SECTION : SURVIVABILITY & LOGISTICS ---
        self._add_section_title(self.tab_ships, "SURVIVABILITY & LOGISTICS")
        
        f_surv = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_surv.pack(pady=5, padx=50, fill="x")
        self.ship_hp = DrakeEntry(f_surv, placeholder_text="TOTAL HP", **entry_kwargs)
        self.ship_hp.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.ship_power = DrakeEntry(f_surv, placeholder_text="POWER CONS.", **entry_kwargs)
        self.ship_power.pack(side="left", fill="x", expand=True, padx=5)
        self.ship_cm = DrakeEntry(f_surv, placeholder_text="CM (DECOY/NOISE)", **entry_kwargs)
        self.ship_cm.pack(side="right", fill="x", expand=True, padx=(5,0))

        f_log = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_log.pack(pady=5, padx=50, fill="x")
        self.ship_cargo = DrakeEntry(f_log, placeholder_text="CARGO (SCU)", **entry_kwargs)
        self.ship_cargo.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.ship_mass = DrakeEntry(f_log, placeholder_text="MASS", **entry_kwargs)
        self.ship_mass.pack(side="left", fill="x", expand=True, padx=5)
        self.ship_dim = DrakeEntry(f_log, placeholder_text="DIMENSIONS", **entry_kwargs)
        self.ship_dim.pack(side="right", fill="x", expand=True, padx=(5,0))

        # --- SECTION : ECONOMY ---
        f_econ = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_econ.pack(pady=5, padx=50, fill="x")
        self.ship_fee = DrakeEntry(f_econ, placeholder_text="EXPEDITION FEE", **entry_kwargs)
        self.ship_fee.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.ship_claim = DrakeEntry(f_econ, placeholder_text="CLAIM TIME", **entry_kwargs)
        self.ship_claim.pack(side="left", fill="x", expand=True, padx=5)
        self.ship_expedite = DrakeEntry(f_econ, placeholder_text="EXPEDITE TIME", **entry_kwargs)
        self.ship_expedite.pack(side="right", fill="x", expand=True, padx=(5,0))

        # --- ACTIONS ---
        self.btn_save_ship = DrakeButton(self.tab_ships, text="SYNC SHIP TO DATABASE", command=self.save_ship, height=45)
        self.btn_save_ship.pack(pady=15, padx=50, fill="x")

        # --- UTILS ---
        f_utils = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        f_utils.pack(fill="x", padx=50, pady=(0, 20))
        DrakeButton(f_utils, text="IMPORT", command=self.import_ships_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_utils, text="EXPORT", command=self.export_ships_csv, fg_color="#222", corner_radius=0).pack(side="left", expand=True, padx=2)
        DrakeButton(f_utils, text="CLEAR", command=self.clear_ship_fields, fg_color="#441111", corner_radius=0).pack(side="left", expand=True, padx=2)

    def _add_section_title(self, parent, title):
        """Petit utilitaire pour ajouter des titres de section Drake"""
        ctk.CTkLabel(parent, text=title, font=DrakeConfig.FONT_UI, 
                     text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(10, 2), padx=50)
        
    def save_ship(self):
        """Sauvegarde sécurisée : bloque l'exécution si les données sont invalides."""
        
        # 1. Récupération des données
        name = self.ship_name.get().strip()
        
        # 2. Sécurité : Nom obligatoire
        if not name:
            self.controller.log("SHIP NAME REQUIRED TO SYNC.", source="SYSTEM ERROR")
            self.ship_name.focus_set()
            return

        numeric_fields = {
            "CREW": self.ship_crew.get(),
            "SCM SPEED": self.ship_scm.get(),
            "BODY HP": self.ship_hp.get(),
            "CARGO": self.ship_cargo.get(),
            "PITCH": self.ship_pitch.get(),
            "YAW": self.ship_yaw.get(),
            "ROLL": self.ship_roll.get()
        }

        for label, value in numeric_fields.items():
            if value:
                try:
                    float(value) 
                except ValueError:
                    self.controller.log(f"INVALID VALUE FOR {label}:\n'{value}' IS NOT A NUMBER.", source="SYSTEM ERROR")
                    return 

        data = {
            "name": name,
            "brand": self.ship_brand.get(),
            "role": self.ship_role.get(),
            "career": self.ship_career.get(),
            "size": self.ship_size.get(),
            "crew_size": self.ship_crew.get(),
            "scm_speed": self.ship_scm.get(),
            "scm_boost_forward": self.ship_scm_bf.get(),
            "scm_boost_backward": self.ship_scm_bb.get(),
            "nav_max_speed": self.ship_nav.get(),
            "pitch": self.ship_pitch.get(),
            "yaw": self.ship_yaw.get(),
            "roll": self.ship_roll.get(),
            "boosted_pitch": self.ship_b_pitch.get(),
            "boosted_yaw": self.ship_b_yaw.get(),
            "boosted_roll": self.ship_b_roll.get(),
            "power_consumption": self.ship_power.get(),
            "cm_decoy_noise": self.ship_cm.get(),
            "hp": self.ship_hp.get(),
            "cargo": self.ship_cargo.get(),
            "dimensions": self.ship_dim.get(),
            "mass": self.ship_mass.get(),
            "hydrogen_capacity": self.ship_h2.get(),
            "qt_fuel_capacity": self.ship_qt.get(),
            "expedition_fee": self.ship_fee.get(),
            "claim_time": self.ship_claim.get(),
            "expedite_time": self.ship_expedite.get()
        }

        try:
            self.ship_controller.save_ship(data)
            self.controller.log(f"SHIP {name.upper()} DATA SYNCED.", source="SYSTEM")
        except Exception as e:
            self.controller.log(f"SYNC ERROR: {str(e)}", source="SYSTEM ERROR")

    def load_ship(self, event=None):
        name = self.ship_name.get().strip()
        if not name: return

        ship = self.ship_controller.load_ship_as_model(name)
        
        if not ship:
            self.controller.log(f"No record for {name}", source="SYSTEM ERROR")
            return

        self.ship_brand.delete(0, "end"); self.ship_brand.insert(0, ship.brand)
        self.ship_role.delete(0, "end"); self.ship_role.insert(0, ship.role)
        self.ship_career.delete(0, "end"); self.ship_career.insert(0, ship.career)
        self.ship_scm.delete(0, "end"); self.ship_scm.insert(0, ship.scm_speed)
        self.ship_hp.delete(0, "end"); self.ship_hp.insert(0, str(ship.hp))
        self.ship_cargo.delete(0, "end"); self.ship_cargo.insert(0, str(ship.cargo))
        self.ship_crew.delete(0, "end"); self.ship_crew.insert(0, str(ship.crew_size))
        self.ship_nav.delete(0, "end"); self.ship_nav.insert(0, ship.nav_max_speed)
        self.ship_name.delete(0, "end"); self.ship_name.insert(0, ship.name)
        self.ship_role.delete(0, "end"); self.ship_role.insert(0, ship.role)
        
        self.controller.log(f"Specs for {ship.name} loaded.", source="SYSTEM")
    
    def import_ships_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                self.ship_controller.import_ships_csv(list(reader))
            self.controller.log("Fleet import successful.", source="DATA")
        except Exception as e:
            self.controller.log(str(e), source="DATA ERROR")

    def export_ships_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        try:
            data = self.ship_controller.export_ships_csv()
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["name", "brand", "role", "career", "size", "crew_size", "scm_speed"]) 
                writer.writerows(data)
            self.controller.log(f"Fleet exported to {path}", source="DATA")
        except Exception as e:
            self.controller.log(str(e), source="DATA ERROR")

    def clear_ship_fields(self):
        for attr in [self.ship_name, self.ship_brand, self.ship_role, 
                     self.ship_career, self.ship_scm, self.ship_nav, 
                     self.ship_hp, self.ship_cargo, self.ship_crew]:
            attr.delete(0, "end")

    def validate_numbers(self, P):
        """Vérifie si la saisie est un nombre (utilisé par register_command)"""
        if P == "" or P.isdigit():
            return True
        return False