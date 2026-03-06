"""Frame de gestion flotte.

Regroupe les onglets Ships, Loadout et Config
pour administrer le catalogue et l'équipement des vaisseaux.
"""

import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeTerminal, DrakeButton, DrakeComboBox, DrakeEntry, DrakePopup, DrakeTitle1, DrakeTitle2, DrakeTitle3, DrakeTitle4, DrakeClearButton

class ShipFrame(ctk.CTkFrame):
    """Interface de gestion de la flotte (Ships, Components & Loadout)."""

    def __init__(self, parent, controller):
        """Initialise la vue et prépare le mapping de types UI."""
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.component_popup = None
        
        # Mapping des types pour le formulaire
        self.mapping_types = {
            "SYSTEMS": ["Shield Generator", "Power Plant", "Cooler"],
            "WEAPON": ["Laser Repeater", "Laser Cannon", "Ballistic Repeater", "Ballistic Cannon", "Distortion Repeater"],
            "PROPULSION": ["Quantum Drive", "Hydrogen Thruster"],
            "MODULE": ["Mining Laser", "Salvage Beam", "Tractor Beam"]
        }

        self._setup_ui()

    # --- INITIALISATION UI ---

    def _setup_ui(self):
        """Initialise la structure globale de l'interface."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)

        self.title_label = DrakeTitle1(
            header, text="FLEET DATABASE"
        )
        self.title_label.pack(expand=True, padx=(0, 0))

        # Onglets principaux
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color=DrakeConfig.BG_PANEL, 
            segmented_button_selected_color=DrakeConfig.ACCENT_PRIMARY,
            segmented_button_selected_hover_color="#e67e22",
            text_color="white"
        )
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tab_ships = self.tabview.add("SHIPS")
        self.tab_loadout = self.tabview.add("LOADOUT")
        self.tab_config = self.tabview.add("CONFIG")

        self.setup_ships_tab()
        self.setup_loadout_tab()
        self.setup_config_tab()

    def refresh(self):
        """Rafraîchissement appelé quand la page SHIPS est affichée."""
        try:
            self.update_selectors()
            if hasattr(self, "cfg_slot_ship"):
                self.refresh_config_tab()
        except Exception:
            pass

    # --- ONGLET SHIPS ---

    def setup_ships_tab(self):
        """Moteur de recherche et fiches techniques."""
        self.ship_search_entry = DrakeEntry(
            self.tab_ships, placeholder_text="RECHERCHER UN VAISSEAU (NOM OU RÔLE)...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.ship_search_entry.pack(pady=(10, 5), padx=20, fill="x")
        self.ship_search_entry.bind("<KeyRelease>", self.run_ship_scan)

        # Toolbar
        toolbar = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        DrakeButton(toolbar, text="IMPORT CSV", width=150,
                    command=self.controller.ship.import_ships_from_csv).pack(side="left", padx=5)
        
        DrakeButton(toolbar, text="EXPORT CSV", width=150,
                    command=self.controller.ship.export_ships_to_csv).pack(side="left", padx=5)

        self.ship_results = DrakeTerminal(self.tab_ships)
        self.ship_results.pack(pady=5, padx=10, fill="both", expand=True)

    # --- ONGLET COMPONENTS ---

    def setup_components_tab(self):
        """Gestion de la base de données des composants."""
        self.open_component_manager()

    def _widget_exists(self, attr_name):
        widget = getattr(self, attr_name, None)
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def _close_component_manager(self):
        if self.component_popup is not None:
            try:
                self.component_popup.destroy()
            except Exception:
                pass
            self.component_popup = None

    def open_component_manager(self):
        """Ouvre la fenêtre d'édition des composants."""
        if self.component_popup is not None:
            try:
                if self.component_popup.winfo_exists():
                    self.component_popup.lift()
                    self.component_popup.focus_force()
                    return
            except Exception:
                self.component_popup = None

        self.component_popup = DrakeConfig.create_modal_window(
            parent=self,
            title="FLEET - COMPONENT MANAGER",
            geometry="980x620",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )
        self.component_popup.protocol("WM_DELETE_WINDOW", self._close_component_manager)

        self.comp_container = ctk.CTkFrame(self.component_popup, fg_color="transparent")
        self.comp_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Panneau de contrôle (Gauche)
        self.add_comp_frame = ctk.CTkFrame(self.comp_container, width=250, fg_color=DrakeConfig.BG_MAIN)
        self.add_comp_frame.pack(side="left", fill="y", padx=(0, 10))
        self.add_comp_frame.pack_propagate(False)

        self.add_comp_scroll = ctk.CTkScrollableFrame(self.add_comp_frame, fg_color="transparent")
        self.add_comp_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        DrakeTitle2(self.add_comp_scroll, text="ADD COMPONENT").pack(pady=15)

        # Champs du formulaire
        DrakeTitle4(self.add_comp_scroll, "SLOT CATEGORY").pack(pady=(0, 2), padx=10)
        categories = self.controller.ship.list_component_categories() or list(self.mapping_types.keys())
        self.new_comp_category = DrakeComboBox(self.add_comp_scroll, 
                            values=categories, 
                                                command=self.on_category_change)
        self.new_comp_category.pack(pady=5, padx=15, fill="x")

        DrakeTitle4(self.add_comp_scroll, "MODULE TYPE").pack(pady=(0, 2), padx=10)
        self.new_comp_type = DrakeComboBox(self.add_comp_scroll, values=[])
        self.new_comp_type.pack(pady=5, padx=15, fill="x")

        self.new_comp_name = DrakeEntry(self.add_comp_scroll, placeholder_text="MODEL NAME (ex: FR-66)")
        self.new_comp_name.pack(pady=5, padx=15, fill="x")
        
        self.new_comp_brand = DrakeEntry(self.add_comp_scroll, placeholder_text="MANUFACTURER (ex: AEGIS)")
        self.new_comp_brand.pack(pady=5, padx=15, fill="x")

        DrakeTitle4(self.add_comp_scroll, "SIZE").pack(pady=(0, 2), padx=10)
        self.new_comp_size = DrakeComboBox(self.add_comp_scroll, values=["0", "1", "2", "3", "4", "5"])
        self.new_comp_size.pack(pady=5, padx=15, fill="x")

        DrakeTitle4(self.add_comp_scroll, "GRADE").pack(pady=(0, 2), padx=10)
        self.new_comp_grade = DrakeComboBox(self.add_comp_scroll, values=["A", "B", "C", "D"])
        self.new_comp_grade.set("C")
        self.new_comp_grade.pack(pady=5, padx=15, fill="x")

        DrakeButton(self.add_comp_scroll, text="SAVE TO DATABASE", 
                    command=self.save_new_component).pack(pady=(0, 8), padx=15, fill="x")
        
        self.update_selectors()

        # Initialisation par défaut
        default_cat = categories[0] if categories else "SYSTEMS"
        self.new_comp_category.set(default_cat)
        self.on_category_change(default_cat)

        # Zone principale (Droite)
        comp_main = ctk.CTkFrame(self.comp_container, fg_color=DrakeConfig.BG_TERMINAL)
        comp_main.pack(side="right", fill="both", expand=True)

        self.comp_list_terminal = DrakeTerminal(comp_main)
        self.comp_list_terminal.pack(fill="both", expand=True)

        self.run_component_scan()

        # --- ONGLET LOADOUT ---

    def setup_loadout_tab(self):
        """Interface d'équipement avec contrôle à gauche et slots à droite."""
        DrakeButton(
            self.tab_loadout,
            text="EDIT COMPONENTS",
            command=self.open_component_manager,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            width=100,
            height=20,
            font=("Segoe UI", 9, "bold"),
            corner_radius=0,
        ).pack(anchor="ne", padx=20, pady=(8, 2))

        self.lo_container = ctk.CTkFrame(self.tab_loadout, fg_color="transparent")
        self.lo_container.pack(fill="both", expand=True, padx=20, pady=(4, 20))

        # --- PANNEAU DE CONTRÔLE (GAUCHE) ---
        ctrl_panel = ctk.CTkFrame(self.lo_container, fg_color=DrakeConfig.BG_MAIN, width=250)
        ctrl_panel.pack(side="left", fill="y", padx=(0, 10))
        ctrl_panel.pack_propagate(False)

        ctrl_scroll = ctk.CTkScrollableFrame(ctrl_panel, fg_color="transparent")
        ctrl_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        DrakeTitle2(ctrl_scroll, text="SHIP SELECTION").pack(pady=(15, 5))

        # Sélecteur de vaisseau
        self.lo_ship_selector = DrakeComboBox(ctrl_scroll, values=["SHIP"], command=self.on_ship_selected)
        self.lo_ship_selector.pack(pady=5, padx=15, fill="x")

        DrakeTitle4(ctrl_scroll, text="LOADOUT PROFILE").pack(pady=(15, 0))

        # Nouveau sélecteur de profils
        self.lo_profile_selector = DrakeComboBox(
            ctrl_scroll, 
            values=["DEFAULT"], 
            command=self.action_load_profile
        )
        self.lo_profile_selector.set("DEFAULT")
        self.lo_profile_selector.pack(pady=5, padx=15, fill="x")

        self.lo_new_profile = DrakeEntry(ctrl_scroll, placeholder_text="NEW PROFILE NAME")
        self.lo_new_profile.pack(pady=(8, 5), padx=15, fill="x")

        DrakeButton(ctrl_scroll, text="CREATE PROFILE", command=self.action_create_profile).pack(pady=(0, 8), padx=15, fill="x")

        # Terminal de résumé
        DrakeTitle4(ctrl_scroll, text="CURRENT CONFIGURATION").pack(pady=(20, 0), padx=15)
        self.lo_status_terminal = DrakeTerminal(ctrl_scroll, height=250)
        self.lo_status_terminal.pack(pady=5, padx=15, fill="x")

        # Bouton Purge (en bas)
        DrakeClearButton(ctrl_panel, text="CLEAR ALL SLOTS", command=self.action_clear_loadout,
                    fg_color="#440000", hover_color="#770000").pack(side="bottom", pady=20, padx=15, fill="x")

        # --- PANNEAU DES SLOTS (DROITE) ---
        self.lo_slots_frame = ctk.CTkScrollableFrame(
            self.lo_container, 
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text="HARDPOINT CONFIGURATION",
            label_font=("Orbitron", 12),
            label_text_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.lo_slots_frame.pack(side="right", fill="both", expand=True)

        self.update_selectors()

    def setup_config_tab(self):
        """Onglet dédié à la création de sous-types et de slots par sous-type."""
        root = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=20, pady=20)

        left = ctk.CTkFrame(root, fg_color=DrakeConfig.BG_MAIN, width=250)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        left_content = ctk.CTkFrame(left, fg_color="transparent")
        left_content.pack(fill="both", expand=True, padx=0, pady=0)

        right = ctk.CTkScrollableFrame(
            root,
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text="SLOT CONFIGURATION",
            label_font=("Orbitron", 12),
            label_text_color=DrakeConfig.ACCENT_PRIMARY,
        )
        right.pack(side="right", fill="both", expand=True)

        DrakeTitle2(left_content, text="CONFIGURATION").pack(pady=(12, 0))
        
        DrakeTitle3(left_content, text="CATEGORY / TYPES").pack(pady=(2, 8))

        DrakeTitle4(left_content, text="--- CATEGORY ---").pack(pady=(4, 2), padx=12)

        self.cfg_type_new_category = DrakeEntry(left_content, placeholder_text="NEW CATEGORY NAME (ex: WEAPON)")
        self.cfg_type_new_category.pack(pady=4, padx=12, fill="x")

        DrakeButton(left_content, text="ADD CATEGORY", command=self.action_add_category).pack(pady=(0, 8), padx=12, fill="x")

        ctk.CTkFrame(left_content, fg_color="#2a2a2a", height=1).pack(fill="x", padx=12, pady=(2, 10))

        DrakeTitle4(left_content, text="--- TYPES (BY CATEGORY) ---").pack(pady=(0, 2), padx=12)

        categories = self.controller.ship.list_component_categories() or list(self.mapping_types.keys())

        DrakeTitle4(left_content, text="CATEGORY").pack(pady=(0, 2), padx=12)
        self.cfg_type_category = DrakeComboBox(left_content, values=categories, command=self.on_cfg_type_category_change)
        self.cfg_type_category.pack(pady=4, padx=12, fill="x")

        self.cfg_type_entry = DrakeEntry(left_content, placeholder_text="NEW TYPE NAME (ex: SHIELD GENERATOR)")
        self.cfg_type_entry.pack(pady=4, padx=12, fill="x")

        type_actions = ctk.CTkFrame(left_content, fg_color="transparent")
        type_actions.pack(pady=(2, 8), padx=12, fill="x")
        DrakeButton(type_actions, text="ADD TYPE", command=self.action_add_subtype).pack(side="left", padx=(0, 4), fill="x", expand=True)

        DrakeTitle4(left_content, text="EXISTING TYPES").pack(pady=(0, 2), padx=12)
        self.cfg_type_selector = DrakeComboBox(left_content, values=[])
        self.cfg_type_selector.pack(pady=4, padx=12, fill="x")

        DrakeClearButton(left_content, text="DELETE TYPE", command=self.action_delete_subtype,
                fg_color="#550000", hover_color="#770000").pack(pady=(0, 4), padx=12, fill="x")

        DrakeTitle2(right, text="SLOT CREATION").pack(pady=(12, 8))

        ship_values = self.controller.ship.list_ship_names()
        row1 = ctk.CTkFrame(right, fg_color="transparent")
        row1.pack(fill="x", padx=12)

        DrakeTitle4(row1, text="SHIP").pack(pady=(0, 4))
        self.cfg_slot_ship = DrakeComboBox(row1, values=ship_values, command=self.on_cfg_slot_ship_change)
        self.cfg_slot_ship.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="CATÉGORIE").pack(pady=(0, 4))
        self.cfg_slot_category = DrakeComboBox(row1, values=categories, command=self.on_cfg_slot_category_change)
        self.cfg_slot_category.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="TYPE").pack(pady=(0, 4))
        self.cfg_slot_subtype = DrakeComboBox(row1, values=[])
        self.cfg_slot_subtype.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="MAX QTY").pack(pady=(0, 4))
        self.cfg_slot_qty = DrakeEntry(row1, placeholder_text="ex: 2")
        self.cfg_slot_qty.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="MAX SIZE").pack(pady=(0, 4))
        self.cfg_slot_size = DrakeEntry(row1, placeholder_text="ex: 1")
        self.cfg_slot_size.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="EXISTING SLOTS").pack(pady=(0, 4))
        self.cfg_slot_selector = DrakeComboBox(row1, values=[], command=self.on_cfg_slot_pick)
        self.cfg_slot_selector.pack(pady=4, fill="x")

        slot_actions = ctk.CTkFrame(right, fg_color="transparent")
        slot_actions.pack(pady=10, padx=12, fill="x")
        DrakeButton(slot_actions, text="SAVE SLOT", command=self.action_save_slot_spec).pack(side="left", padx=4)
        DrakeButton(slot_actions, text="REFRESH", command=self.refresh_config_tab).pack(side="left", padx=4)
        DrakeClearButton(slot_actions, text="DELETE SLOT", command=self.action_delete_slot_spec).pack(side="right", padx=4)

        self.cfg_slot_terminal = DrakeTerminal(right)
        self.cfg_slot_terminal.pack(padx=12, pady=8, fill="both", expand=True)

        if categories:
            self.cfg_type_category.set(categories[0])
            self.cfg_slot_category.set(categories[0])
            self.on_cfg_type_category_change(categories[0])
            self.on_cfg_slot_category_change(categories[0])
        if ship_values:
            self.cfg_slot_ship.set(ship_values[0])
            self.on_cfg_slot_ship_change(ship_values[0])
        self.refresh_config_tab()

    # --- LOGIQUE ET HELPER METHODS ---

    def _create_form_label(self, parent, text):
        """Helper pour créer des labels uniformes."""
        lbl = ctk.CTkLabel(parent, text=text, font=("Orbitron", 10), text_color="#aaaaaa")
        lbl.pack(pady=(10, 0))
        return lbl

    def run_ship_scan(self, event=None):
        """Affiche les fiches techniques des vaisseaux."""
        q = self.ship_search_entry.get().strip().upper()
        self.ship_results.delete("0.0", "end")
        if len(q) < 2: return

        names = self.controller.ship.search_ship_names(q, limit=10)
        for ship_name in names:
            ship = self.controller.ship.load_ship_as_model(ship_name)
            if not ship: continue
            
            tag = f"edit_{ship.name.replace(' ', '_')}"
            self.ship_results.insert("end", " ■ ", "ACCENT") 
            self.ship_results.insert("end", f"{ship.brand} {ship.name} ", (tag, "NEUTRE"))
            self.ship_results.insert("end", f"[{ship.size.upper()}]\n", "info_label")
            self.ship_results.insert("end", f"   ROLE: {ship.role} | CREW: {ship.crew_size} | CARGO: {ship.cargo} SCU\n")
            self.ship_results.insert("end", "   " + "-"*45 + "\n", "separator")
            
            # Affichage des composants équipés
            if ship.components:
                self.ship_results.insert("end", "   LOADOUT:\n", "ACCENT")
                for c in ship.components:
                    self.ship_results.insert("end", f"     • [{c.category}] {c.brand} {c.name} (S{c.size})\n")
            
            self.ship_results.insert("end", f"{'='*60}\n\n")
            self.ship_results.tag_bind(tag, "<Double-Button-1>", lambda e, n=ship.name: self.open_edit_window(n))

    def save_new_component(self):
        """Sauvegarde un composant et rafraîchit les vues."""
        if not self._widget_exists("new_comp_name"):
            self.open_component_manager()
            return

        name = self.new_comp_name.get().strip().upper()
        if not name: return

        data = {
            "name": name,
            "brand": self.new_comp_brand.get().strip().upper() or "UNKNOWN",
            "type_name": self.new_comp_type.get(),
            "category": self.new_comp_category.get(),
            "size": int(self.new_comp_size.get()),
            "grade": self.new_comp_grade.get(),
            "stats": "{}"
        }
        
        try:
            self.controller.ship.add_component_to_db(data)
            self.new_comp_name.delete(0, "end")
            self.run_component_scan()
            self.update_selectors()
        except Exception as e:
            self.controller.log(f"Error adding component: {e}", source="FLEET")

    # --- ACTIONS ---
    def on_category_change(self, choice):
        if not self._widget_exists("new_comp_type"):
            return

        new_values = self.controller.ship.list_component_subtypes(choice)
        if not new_values:
            new_values = self.mapping_types.get(choice, [])
        self.new_comp_type.configure(values=new_values)
        if new_values: self.new_comp_type.set(new_values[0])

    def filter_components_by_cat(self, choice):
        if choice == "ALL":
            comps = [r[0] for r in self.controller.ship.list_components_catalog()]
        else:
            comps = self.controller.ship.get_compatible_components(choice, 99)
        self.lo_comp_selector.configure(values=comps)
        if comps: self.lo_comp_selector.set(comps[0])

    def action_equip(self):
        ship, comp = self.lo_ship_selector.get(), self.lo_comp_selector.get()
        if ship and comp:
            if self.controller.ship.equip_component(ship, comp):
                self.refresh_loadout_view(ship)

    def run_component_scan(self):
        """Liste hiérarchique des composants en DB."""
        if not self._widget_exists("comp_list_terminal"):
            return

        self.comp_list_terminal.delete("0.0", "end")
        rows = self.controller.ship.list_components_catalog()
        last_cat = None
        for r in rows:
            if r[3] != last_cat:
                self.comp_list_terminal.insert("end", f"\n▼ {r[3]}\n", "ACCENT")
                last_cat = r[3]
            self.comp_list_terminal.insert("end", f"   • {r[1]:<12} | {r[0]:<18} | S{r[4]} | GR-{r[5]}\n")

    def open_edit_window(self, ship_name):
        """Ouvre une interface de modification complète (Full Access) pour un vaisseau."""
        ship = self.controller.ship.load_ship_as_model(ship_name)
        if not ship: return

        # --- CONFIGURATION FENÊTRE ---
        edit_win = DrakeConfig.create_modal_window(
            parent=self,
            title=f"DRAKE SYSTEMS - DATABASE OVERRIDE: {ship_name}",
            geometry="800x700",
            fg_color=DrakeConfig.BG_PANEL,
            resizable=True,
        )

        # Header stylisé
        header = ctk.CTkFrame(edit_win, fg_color=DrakeConfig.ACCENT_PRIMARY, height=50, corner_radius=0)
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(header, text=f"UNAUTHORIZED ACCESS // DATA OVERRIDE // {ship_name.upper()}", 
                     font=("Orbitron", 14, "bold"), text_color="black").pack(pady=12)

        # Système d'onglets internes à la fenêtre d'édition
        inner_tabview = ctk.CTkTabview(edit_win, fg_color=DrakeConfig.BG_TERMINAL)
        inner_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_general = inner_tabview.add("GENERAL")
        tab_flight = inner_tabview.add("FLIGHT")
        tab_logistics = inner_tabview.add("LOGISTICS")

        # --- DICTIONNAIRE DE WIDGETS POUR RÉCUPÉRATION ---
        self.edit_entries = {}

        def create_field(parent, label, key, default_val):
            self._create_form_label(parent, label)
            entry = DrakeEntry(parent, fg_color=DrakeConfig.BG_PANEL, border_color="#333333")
            entry.insert(0, str(default_val))
            entry.pack(fill="x", padx=20, pady=5)
            self.edit_entries[key] = entry

        # --- ONGLET 1 : GENERAL (Identité) ---
        create_field(tab_general, "MANUFACTURER", "brand", ship.brand)
        create_field(tab_general, "MODEL NAME", "name", ship.name)
        create_field(tab_general, "SIZE CLASS (S1-S6)", "size", ship.size)
        create_field(tab_general, "PRIMARY ROLE", "role", ship.role)
        create_field(tab_general, "CAREER", "career", ship.career)

        # --- ONGLET 2 : FLIGHT (Performances) ---
        f_container = ctk.CTkFrame(tab_flight, fg_color="transparent")
        f_container.pack(fill="both", expand=True)
        
        col1 = ctk.CTkFrame(f_container, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True)
        col2 = ctk.CTkFrame(f_container, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True)

        create_field(col1, "SCM SPEED", "scm_speed", ship.scm_speed)
        create_field(col1, "NAV SPEED", "nav_max_speed", ship.nav_max_speed)
        create_field(col1, "PITCH", "pitch", ship.pitch)
        create_field(col1, "YAW", "yaw", ship.yaw)
        create_field(col1, "ROLL", "roll", ship.roll)

        create_field(col2, "HULL HP", "hp", ship.hp)
        create_field(col2, "BOOST PITCH", "boosted_pitch", ship.boosted_pitch)
        create_field(col2, "BOOST YAW", "boosted_yaw", ship.boosted_yaw)
        create_field(col2, "BOOST ROLL", "boosted_roll", ship.boosted_roll)

        # --- ONGLET 3 : LOGISTICS (Fret & Assurance) ---
        create_field(tab_logistics, "CARGO CAPACITY (SCU)", "cargo", ship.cargo)
        create_field(tab_logistics, "CREW SIZE", "crew_size", ship.crew_size)
        create_field(tab_logistics, "CLAIM TIME (MINUTES)", "claim_time", ship.claim_time)
        create_field(tab_logistics, "EXPEDITE TIME (MINUTES)", "expedite_time", ship.expedite_time)
        create_field(tab_logistics, "EXPEDITE COST (aUEC)", "expedite_cost", getattr(ship, 'expedite_cost', 0))

        # --- BOUTON DE SAUVEGARDE GLOBALE ---
        def perform_full_update():
            try:
                # On compile toutes les entrées dans un dictionnaire
                final_data = {}
                for key, widget in self.edit_entries.items():
                    val = widget.get()
                    # Conversion auto si la clé est connue pour être numérique
                    if key in ['scm_speed', 'nav_max_speed', 'hp', 'crew_size', 'claim_time', 'expedite_time']:
                        final_data[key] = int(val)
                    elif key in ['pitch', 'yaw', 'roll', 'cargo', 'boosted_pitch', 'boosted_yaw', 'boosted_roll']:
                        final_data[key] = float(val)
                    else:
                        final_data[key] = val.upper()

                # Appel au contrôleur
                self.controller.ship.update_ship_specs(ship_name, final_data)
                
                self.controller.log("CORE DATABASE SYNCHRONIZED.", source="DRAKE OS")
                edit_win.destroy()
                self.run_ship_scan() # Refresh le terminal
                
            except ValueError as e:
                self.controller.log(f"Invalid format in numeric field: {e}", source="DATA ERROR")

        save_btn = DrakeButton(edit_win, text="APPLY ALL MODIFICATIONS", 
                               command=perform_full_update)
        save_btn.pack(pady=20, padx=40, fill="x")

    def refresh_loadout_view(self, ship_name):
        """Affiche les slots à droite et met à jour le terminal à gauche."""
        if not ship_name:
            ship_name = self.lo_ship_selector.get()
        if not ship_name:
            return

        profile_name = self._get_active_profile()

        # 1. Nettoyage de l'existant
        for widget in self.lo_slots_frame.winfo_children():
            widget.destroy()
        self.lo_status_terminal.delete("0.0", "end")

        # 2. Chargement des données du vaisseau
        ship = self.controller.ship.load_full_ship(ship_name, profile_name)
        if not ship:
            return

        slot_specs = self.controller.ship.get_ship_slot_specs(ship_name)
        if not slot_specs:
            self.lo_status_terminal.insert("end", "> NO SLOT SPECS FOUND FOR THIS SHIP.\n")
            return

        self.lo_status_terminal.insert("end", f"> ANALYZING {ship_name} [{profile_name}]...\n", "ACCENT")

        # 3. Création des lignes par catégorie + sous-type
        current_cat = None
        for spec in slot_specs:
            cat = spec["category"]
            subtype = spec["subtype_name"]
            max_qty = int(spec["max_qty"])
            max_size = int(spec["max_size"])

            # Titre de catégorie
            if current_cat != cat:
                ctk.CTkLabel(self.lo_slots_frame, text=f"--- {cat} ---", 
                            font=("Orbitron", 11, "bold"), text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=(10, 5))
                current_cat = cat

            subtype_label = subtype if subtype != "GENERIC" else "ALL TYPES"
            ctk.CTkLabel(self.lo_slots_frame, text=f"{subtype_label} (MAX {max_qty})",
                         font=("Orbitron", 10), text_color="#AAAAAA").pack(pady=(2, 2), padx=12, anchor="w")

            for i in range(max_qty):
                # Récupère les composants compatibles et l'actuel
                available, current = self.controller.ship.get_slot_data(
                    ship.name,
                    profile_name,
                    cat,
                    subtype,
                    max_size,
                    i,
                )
                
                # Carte de ligne (Slot)
                card = ctk.CTkFrame(self.lo_slots_frame, fg_color="#121212", border_width=1, border_color="#333333")
                card.pack(fill="x", padx=10, pady=2)

                ctk.CTkLabel(card, text=f"S{max_size} Slot {i+1}", width=80, font=("Orbitron", 10)).pack(side="left", padx=10)
                
                # Menu de sélection
                combo = DrakeComboBox(card, values=["EMPTY"] + available, width=220)
                combo.set(current)
                combo.pack(side="left", padx=10, pady=5)

                # Bouton de sauvegarde INDIVIDUEL
                save_btn = DrakeButton(card, text="SAVE", width=60, 
                                    command=lambda c=combo, ct=cat, st=subtype, idx=i: self.action_mount(ct, st, idx, c.get()))
                save_btn.pack(side="right", padx=10)

                # Ajout au terminal de gauche pour le récapitulatif
                self.lo_status_terminal.insert("end", f"[{cat}::{subtype_label}] SLT{i+1}: {current}\n")

    def save_slot_config(self, ship_name, category, subtype_name, slot_index, combo_widget):
        """Action du bouton SET : Enregistre la config via le contrôleur."""
        selection = combo_widget.get()
        profile_name = self._get_active_profile()
        if self.controller.ship.mount_component(ship_name, category, subtype_name, slot_index, selection, profile_name):
            self.controller.log(
                f"LOADOUT SYNC: {ship_name} [{profile_name}] -> {selection} (Slot {slot_index + 1})",
                source="FLEET",
            )
        else:
            self.controller.log("Failed to sync with ship database.", source="DRAKE OS ERROR")
        
    def action_mount(self, category, subtype_name, slot_index, component_name):
        """Enregistre le composant sélectionné en base de données."""
        ship_name = self.lo_ship_selector.get()
        profile_name = self._get_active_profile()
        if not ship_name: return

        # Appel au contrôleur pour sauvegarder en DB
        if self.controller.ship.mount_component(ship_name, category, subtype_name, slot_index, component_name, profile_name):
            # On rafraîchit TOUTE la vue pour mettre à jour le terminal de gauche
            self.refresh_loadout_view(ship_name)
            self.controller.log(
                f"Component mounted: {ship_name} [{profile_name}] {category}/{subtype_name} -> {component_name}",
                source="FLEET",
            )
        else:
            self.controller.log("Database Sync Failed. Incompatible hardware.", source="DRAKE OS")
    
    def action_clear_loadout(self):
        """Supprime tous les composants installés sur le vaisseau actuel."""
        ship_name = self.lo_ship_selector.get()
        profile_name = self._get_active_profile()
        if not ship_name: return
        
        if DrakePopup.yesno("DRAKE OS", f"WIPE PROFILE [{profile_name}] FOR {ship_name}?", parent=self):
            self.controller.ship.clear_ship_loadout(ship_name, profile_name)
            # Rafraîchissement de l'interface
            self.refresh_loadout_view(ship_name)
    
    def update_selectors(self):
        """Rafraîchit la liste des vaisseaux dans le menu déroulant."""
        try:
            ships = self.controller.ship.list_ship_names()
            # On configure le ComboBox avec ces noms
            self.lo_ship_selector.configure(values=ships)
            if ships and self.lo_ship_selector.get() not in ships:
                self.lo_ship_selector.set(ships[0])
                self.on_ship_selected(ships[0])

            if hasattr(self, "cfg_slot_ship"):
                self.cfg_slot_ship.configure(values=ships)
                if ships and self.cfg_slot_ship.get() not in ships:
                    self.cfg_slot_ship.set(ships[0])
                    self.on_cfg_slot_ship_change(ships[0])

            if hasattr(self, "cfg_type_category"):
                categories = self.controller.ship.list_component_categories() or list(self.mapping_types.keys())
                self.cfg_type_category.configure(values=categories)
                self.cfg_slot_category.configure(values=categories)

            if self._widget_exists("new_comp_category"):
                categories = self.controller.ship.list_component_categories() or list(self.mapping_types.keys())
                self.new_comp_category.configure(values=categories)
        except Exception as e:
            self.controller.log(f"Update selectors error: {e}", source="FLEET")

    def on_cfg_type_category_change(self, category):
        subtypes = self.controller.ship.list_component_subtypes(category)
        if not subtypes:
            subtypes = self.mapping_types.get(category, [])
        self.cfg_type_selector.configure(values=subtypes if subtypes else ["NO DATA"])
        if subtypes:
            self.cfg_type_selector.set(subtypes[0])
        else:
            self.cfg_type_selector.set("NO DATA")
        self.refresh_type_terminal()

    def action_add_type(self):
        category = self.cfg_type_new_category.get().strip().upper()
        if not category:
            DrakePopup.warning("DRAKE OS", "TYPE requis", parent=self)
            return
        try:
            self.controller.ship.create_component_category(category)
            self.cfg_type_new_category.delete(0, "end")
            self.update_selectors()
            self.cfg_type_category.set(category)
            self.cfg_slot_category.set(category)
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(category)
        except Exception as e:
            DrakePopup.error("DRAKE OS", str(e), parent=self)

    def refresh_type_terminal(self):
        return

    def action_add_category(self):
        category = self.cfg_type_new_category.get().strip().upper()
        if not category:
            DrakePopup.warning("DRAKE OS", "CATÉGORIE requise", parent=self)
            return
        try:
            self.controller.ship.create_component_category(category)
            self.cfg_type_new_category.delete(0, "end")
            self.update_selectors()
            self.cfg_type_category.set(category)
            self.cfg_slot_category.set(category)
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(category)
        except Exception as e:
            DrakePopup.error("DRAKE OS", str(e), parent=self)

    def action_add_subtype(self):
        category = self.cfg_type_category.get().strip().upper()
        subtype = self.cfg_type_entry.get().strip().upper()
        if not category or not subtype:
            DrakePopup.warning("DRAKE OS", "CATÉGORIE et TYPE requis", parent=self)
            return
        try:
            self.controller.ship.create_component_subtype(category, subtype)
            self.cfg_type_entry.delete(0, "end")
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(self.cfg_slot_category.get())
            if self._widget_exists("new_comp_category"):
                self.on_category_change(self.new_comp_category.get())
        except Exception as e:
            DrakePopup.error("DRAKE OS", str(e), parent=self)

    def action_delete_subtype(self):
        category = self.cfg_type_category.get().strip().upper()
        subtype = self.cfg_type_selector.get().strip().upper()
        if not subtype or subtype == "NO DATA":
            return
        if not DrakePopup.yesno("DRAKE OS", f"DELETE TYPE {subtype} ?", parent=self):
            return
        self.controller.ship.delete_component_subtype(category, subtype)
        self.on_cfg_type_category_change(category)
        self.on_cfg_slot_category_change(self.cfg_slot_category.get())
        if self._widget_exists("new_comp_category"):
            self.on_category_change(self.new_comp_category.get())

    def on_cfg_slot_ship_change(self, _ship_name):
        self.refresh_slot_terminal()

    def _set_slot_type_locked(self, locked: bool):
        if not hasattr(self, "cfg_slot_subtype"):
            return
        if locked:
            self.cfg_slot_subtype.entry.configure(
                command=lambda: None,
                text_color="#6f6f6f",
                hover_color=DrakeConfig.BG_TERMINAL,
            )
            self.cfg_slot_subtype.button.configure(
                command=lambda: None,
                fg_color="#4a4a4a",
                hover_color="#4a4a4a",
                text_color="#9a9a9a",
            )
        else:
            self.cfg_slot_subtype.entry.configure(
                command=self.cfg_slot_subtype.toggle_dropdown,
                text_color=DrakeConfig.TEXT_MAIN,
                hover_color=DrakeConfig.BG_TERMINAL,
            )
            self.cfg_slot_subtype.button.configure(
                command=self.cfg_slot_subtype.toggle_dropdown,
                fg_color=DrakeConfig.ACCENT_PRIMARY,
                hover_color=DrakeConfig.ACCENT_HOVER,
                text_color="#000000",
            )

    def on_cfg_slot_category_change(self, category):
        if (category or "").strip().upper() == "WEAPON":
            self.cfg_slot_subtype.configure(values=["GENERIC"])
            self.cfg_slot_subtype.set("GENERIC")
            self._set_slot_type_locked(True)
            return

        self._set_slot_type_locked(False)

        subtypes = self.controller.ship.list_component_subtypes(category)
        if not subtypes:
            subtypes = self.mapping_types.get(category, [])
        self.cfg_slot_subtype.configure(values=subtypes if subtypes else ["GENERIC"])
        if subtypes:
            self.cfg_slot_subtype.set(subtypes[0])
        else:
            self.cfg_slot_subtype.set("GENERIC")

    def refresh_slot_terminal(self):
        if not hasattr(self, "cfg_slot_terminal"):
            return
        ship_name = self.cfg_slot_ship.get().strip().upper() if hasattr(self, "cfg_slot_ship") else ""
        self.cfg_slot_selector.configure(values=["NO DATA"])
        self.cfg_slot_selector.set("NO DATA")
        self.cfg_slot_terminal.delete("0.0", "end")
        if not ship_name:
            return
        specs = self.controller.ship.list_subtype_specs(ship_name)
        self.cfg_slot_terminal.insert("end", f"> SLOT SPECS - {ship_name}\n", "ACCENT")
        keys = []
        for cat, subtype, qty, size in specs:
            key = f"{cat}::{subtype}"
            keys.append(key)
            self.cfg_slot_terminal.insert("end", f"[{cat}] {subtype:<20} | QTY={qty} | SIZE=S{size}\n")

        self.cfg_slot_selector.configure(values=keys if keys else ["NO DATA"])
        if keys:
            self.cfg_slot_selector.set(keys[0])
        else:
            self.cfg_slot_selector.set("NO DATA")

    def on_cfg_slot_pick(self, selection):
        if not selection or selection == "NO DATA" or "::" not in selection:
            return
        ship_name = self.cfg_slot_ship.get().strip().upper()
        cat, subtype = selection.split("::", 1)
        self.cfg_slot_category.set(cat)
        self.on_cfg_slot_category_change(cat)
        self.cfg_slot_subtype.set(subtype)

        specs = self.controller.ship.list_subtype_specs(ship_name)
        for c, st, qty, size in specs:
            if c == cat and st == subtype:
                self.cfg_slot_qty.delete(0, "end")
                self.cfg_slot_qty.insert(0, str(qty))
                self.cfg_slot_size.delete(0, "end")
                self.cfg_slot_size.insert(0, str(size))
                break

    def action_save_slot_spec(self):
        ship_name = self.cfg_slot_ship.get().strip().upper()
        category = self.cfg_slot_category.get().strip().upper()
        subtype = self.cfg_slot_subtype.get().strip().upper()
        if category == "WEAPON":
            subtype = "GENERIC"
        if not ship_name or not category or not subtype:
            DrakePopup.warning("DRAKE OS", "SHIP / CATEGORY / SUBTYPE requis", parent=self)
            return
        try:
            qty = int(self.cfg_slot_qty.get().strip())
            max_size = int(self.cfg_slot_size.get().strip())
            self.controller.ship.upsert_subtype_spec(ship_name, category, subtype, qty, max_size)
            self.refresh_slot_terminal()
            if self.lo_ship_selector.get().strip().upper() == ship_name:
                self.refresh_loadout_view(ship_name)
        except Exception as e:
            DrakePopup.error("DRAKE OS", str(e), parent=self)

    def action_delete_slot_spec(self):
        ship_name = self.cfg_slot_ship.get().strip().upper()
        selection = self.cfg_slot_selector.get().strip().upper()
        if not ship_name or not selection or selection == "NO DATA" or "::" not in selection:
            return
        cat, subtype = selection.split("::", 1)
        if not DrakePopup.yesno("DRAKE OS", f"DELETE SLOT SPEC {cat}::{subtype} ?", parent=self):
            return
        self.controller.ship.delete_subtype_spec(ship_name, cat, subtype)
        self.refresh_slot_terminal()
        if self.lo_ship_selector.get().strip().upper() == ship_name:
            self.refresh_loadout_view(ship_name)

    def refresh_config_tab(self):
        if hasattr(self, "cfg_type_category"):
            self.on_cfg_type_category_change(self.cfg_type_category.get())
        if hasattr(self, "cfg_slot_ship"):
            self.refresh_slot_terminal()
    
    def update_profile_list(self, ship_name, selected_profile=None):
        """Récupère les profils de loadout disponibles pour le vaisseau sélectionné."""
        try:
            profiles = self.controller.ship.list_loadout_profiles(ship_name)
                
            self.lo_profile_selector.configure(values=profiles)
            current = (selected_profile or self.lo_profile_selector.get() or "DEFAULT").upper()
            if current not in profiles:
                current = "DEFAULT"
            self.lo_profile_selector.set(current)
                
        except Exception as e:
            self.controller.log(f"Error updating profiles: {e}", source="FLEET")

    def _get_active_profile(self):
        profile = (self.lo_profile_selector.get() or "DEFAULT").strip().upper()
        return profile or "DEFAULT"

    def on_ship_selected(self, ship_name):
        if not ship_name:
            return
        self.update_profile_list(ship_name)
        self.refresh_loadout_view(ship_name)

    def action_create_profile(self):
        ship_name = self.lo_ship_selector.get()
        if not ship_name:
            DrakePopup.warning("DRAKE OS", "SELECT A SHIP FIRST.", parent=self)
            return

        new_profile = self.lo_new_profile.get().strip().upper()
        if not new_profile:
            DrakePopup.warning("DRAKE OS", "ENTER A PROFILE NAME.", parent=self)
            return

        source_profile = self._get_active_profile()
        created = self.controller.ship.create_loadout_profile(
            ship_name,
            new_profile,
            source_profile=source_profile,
            overwrite=False,
        )
        if not created:
            DrakePopup.warning("DRAKE OS", f"PROFILE {new_profile} ALREADY EXISTS.", parent=self)
            return

        self.lo_new_profile.delete(0, "end")
        self.update_profile_list(ship_name, selected_profile=new_profile)
        self.refresh_loadout_view(ship_name)

    def action_load_profile(self, profile_name):
        """Charge la configuration d'un profil spécifique."""
        ship_name = self.lo_ship_selector.get()
        if not ship_name or ship_name == "":
            return
        self.refresh_loadout_view(ship_name)