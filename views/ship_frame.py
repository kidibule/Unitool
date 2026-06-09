"""Frame de gestion flotte.

Regroupe les onglets Ships, Loadout et Config
pour administrer le catalogue et l'équipement des vaisseaux.
"""

import customtkinter as ctk
from tkinter import filedialog
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeClearButton, DrakeComboBox, DrakeDualComboBox, DrakeEntry, DrakeEntryLight, DrakeTerminal, DrakeTitle1, DrakeTitle2, DrakeTitle3, DrakeTitle4, DrakeComboBoxLight, DrakePopup, DrakeSuggestionManager
from controllers.ship_controller import SHIP_CAREER_OPTIONS, SHIP_MANUFACTURER_OPTIONS

class ShipFrame(ctk.CTkFrame):
    """Interface de gestion de la flotte (Ships, Components & Loadout)."""

    def __init__(self, parent, controller, mode: str = "all"):
        """Initialise la vue et prépare le mapping de types UI."""
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        mode_normalized = (mode or "all").strip().lower()
        self.mode = mode_normalized if mode_normalized in {"all", "catalog_only", "loadout_only"} else "all"
        self.component_popup = None
        self.component_editing_name = None
        self.cfg_slot_editing_key = None
        self.lo_slot_widgets = []
        self.cfg_slot_selected_key = ""
        self._loadout_ship_values = []
        self._validated_loadout_ship = ""
        self._loadout_suggestion_manager = DrakeSuggestionManager(self)
        
        # Mapping des types pour le formulaire
        self.mapping_types = {
            "SYSTEMS": ["Shield Generator", "Power Plant", "Cooler"],
            "WEAPON": ["Laser Repeater", "Laser Cannon", "Ballistic Repeater", "Ballistic Cannon", "Distortion Repeater"],
            "PROPULSION": ["Quantum Drive", "Hydrogen Thruster"],
            "MODULE": ["Mining Laser", "Salvage Beam", "Tractor Beam"]
        }

        self._setup_ui()
        self._suspend_cfg_slot_pick = False

    # --- INITIALISATION UI ---

    def _setup_ui(self):
        """Initialise la structure globale de l'interface."""
        self.role_options = self.controller.ship.list_ship_roles()
        self.career_options = self.controller.ship.list_ship_careers()

        # En mode catalogue embarqué dans DATABASE, on affiche directement
        # le contenu SHIPS sans titre ni sous-onglets.
        if self.mode == "catalog_only":
            self.tab_ships = self
            self.setup_ships_tab()
            return

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)

        title_text = "FLEET DATABASE"
        if self.mode == "loadout_only":
            title_text = "SHIP LOADOUT"

        self.title_label = DrakeTitle1(
            header, text=title_text
        )
        self.title_label.pack(expand=True, padx=(0, 0))

        # Onglets principaux
        self.tabview = DrakeConfig.create_tabview(self)
        try:
            self.tabview.configure(command=self._on_ship_tab_changed)
        except Exception:
            pass

        if self.mode in ("all", "catalog_only"):
            self.tab_ships = self.tabview.add("SHIPS")
            self.setup_ships_tab()

        if self.mode in ("all", "loadout_only"):
            self.tab_loadout = self.tabview.add("LOADOUT")
            self.tab_config = self.tabview.add("CONFIG")
            self.setup_loadout_tab()
            self.setup_config_tab()

    def refresh(self):
        """Rafraîchissement appelé quand la page SHIPS est affichée."""
        try:
            self._reset_loadout_ship_entry_on_page_load()
            self.update_selectors()
            if hasattr(self, "cfg_slot_ship"):
                self.refresh_config_tab()
        except Exception:
            pass

    # --- ONGLET SHIPS ---

    def setup_ships_tab(self):
        """Moteur de recherche et fiches techniques."""
        ships_parent = getattr(self, "tab_ships", self)

        self.ship_search_entry = DrakeEntry(
            ships_parent, placeholder_text="SEARCH A SHIP (NAME OR ROLE)...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.ship_search_entry.pack(pady=(10, 5), padx=20, fill="x")
        self.ship_search_entry.bind("<KeyRelease>", self.run_ship_scan)

        # Toolbar
        toolbar = ctk.CTkFrame(ships_parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        left_actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_actions.pack(side="left")

        DrakeButton(left_actions, text="IMPORT CSV", width=150,
                    command=self.controller.ship.import_ships_from_csv).pack(side="left", padx=5)
        
        DrakeButton(left_actions, text="EXPORT CSV", width=150,
                    command=self.controller.ship.export_ships_to_csv).pack(side="left", padx=5)

        if self.mode == "catalog_only":
            DrakeButton(
                toolbar,
                text="ADD SHIP",
                width=150,
                command=self._open_archive_ship_tab,
            ).pack(side="right", padx=5)

        self.ship_results = DrakeTerminal(ships_parent)
        self.ship_results.pack(pady=5, padx=10, fill="both", expand=True)
        self.ship_results.tag_config("ACCENT", foreground=DrakeConfig.ACCENT_PRIMARY)
        self.ship_results.tag_config("ship_name_white", foreground=DrakeConfig.TEXT_MAIN)

    def _open_archive_ship_tab(self):
        """Ouvre une popup ARCHIVE sur l'onglet SHIPS depuis DATABASE."""
        try:
            view = getattr(self.controller, "view", None)
            if view is not None and hasattr(view, "open_archive_popup"):
                view.open_archive_popup("SHIPS")
        except Exception:
            pass

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

    def _get_all_component_categories(self) -> list[str]:
        """Retourne une liste de catégories stable (DB + catégories par défaut UI)."""
        db_categories = self.controller.ship.list_component_categories() or []
        merged = []
        seen = set()

        for cat in db_categories + list(self.mapping_types.keys()):
            cat_up = (cat or "").strip().upper()
            if not cat_up or cat_up in seen:
                continue
            seen.add(cat_up)
            merged.append(cat_up)

        return merged

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

        container = ctk.CTkFrame(self.component_popup, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        DrakeTitle2(container, text="COMPONENT DATABASE").pack(pady=(0, 10))

        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(fill="both", expand=True)

        self.add_comp_frame = ctk.CTkFrame(content, width=250, fg_color=DrakeConfig.BG_MAIN)
        self.add_comp_frame.pack(side="left", fill="y", padx=(0, 10))
        self.add_comp_frame.pack_propagate(False)

        self.add_comp_scroll = ctk.CTkScrollableFrame(self.add_comp_frame, fg_color="transparent")
        self.add_comp_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        DrakeTitle2(self.add_comp_scroll, text="ADD COMPONENT").pack(pady=15)

        categories = self._get_all_component_categories()

        DrakeTitle4(self.add_comp_scroll, "SLOT CATEGORY").pack(pady=(0, 2), padx=10)
        self.new_comp_category = DrakeComboBox(
            self.add_comp_scroll,
            values=categories,
            command=self.on_category_change,
        )
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

        DrakeButton(
            self.add_comp_scroll,
            text="SAVE TO DATABASE",
            command=self.save_new_component,
        ).pack(pady=(0, 8), padx=15, fill="x")

        self.update_selectors()

        # Initialisation par défaut
        default_cat = categories[0] if categories else "SYSTEMS"
        self.new_comp_category.set(default_cat)
        self.on_category_change(default_cat)

        self.comp_list_scroll = ctk.CTkScrollableFrame(
            content,
            label_text="REGISTERED COMPONENTS",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.comp_list_scroll.pack(side="right", fill="both", expand=True)

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

        # Champ de recherche ship avec suggestions (style Contracts target/client)
        self.lo_ship_selector = DrakeEntry(ctrl_scroll, placeholder_text="SEARCH SHIP (NAME)...")
        self.lo_ship_selector.pack(pady=5, padx=15, fill="x")
        self._loadout_suggestion_manager.attach(
            self.lo_ship_selector,
            get_items=self._loadout_ship_suggestions,
            on_validate=self._on_loadout_ship_validated,
            on_preview=self._on_loadout_ship_preview,
            on_clear=self._on_loadout_ship_cleared,
            normalize=lambda s: str(s).strip().upper(),
            max_items=10,
        )
        self.lo_ship_selector.bind("<KeyRelease>", self._on_loadout_ship_text_changed, add="+")

        self.lo_ship_cycle_indicator = ctk.CTkLabel(
            ctrl_scroll,
            text="",
            font=("Consolas", 9),
            text_color=DrakeConfig.TEXT_SECONDARY,
        )
        self.lo_ship_cycle_indicator.pack(pady=(0, 4), padx=15, anchor="e")

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

    def _reset_loadout_ship_entry_on_page_load(self):
        """Nettoie l'état de suggestion quand on revient sur la page SHIPS."""
        if not self._widget_exists("lo_ship_selector"):
            return
        self._close_ship_popup()
        self._validated_loadout_ship = ""
        self._set_ship_cycle_indicator(0, 0)
        text = self.lo_ship_selector.get().strip().upper()
        if text:
            self._clear_loadout_preview_pending_validation()

    def _on_page_leave(self):
        """Réinitialise le champ ship en quittant le menu SHIPS."""
        self._close_ship_popup()
        self._validated_loadout_ship = ""
        if self._widget_exists("lo_ship_selector"):
            try:
                self.lo_ship_selector.delete(0, "end")
                if hasattr(self.lo_ship_selector, "_activate_placeholder"):
                    self.lo_ship_selector._activate_placeholder()
            except Exception:
                pass
        self._set_ship_cycle_indicator(0, 0)
        self._clear_loadout_preview_pending_validation()

    def _loadout_ship_suggestions(self, raw_query: str):
        query = (raw_query or "").strip().upper()
        ships = [str(s).strip().upper() for s in self._loadout_ship_values]
        if not ships:
            return []
        if not query:
            return ships[:10]

        starts = [s for s in ships if s.startswith(query)]
        contains = [s for s in ships if query in s and s not in starts]
        return (starts + contains)[:10]

    def _on_loadout_ship_preview(self, _entry_widget, value: str, index: int, total: int):
        self._set_ship_cycle_indicator(index, total)
        if value != self._validated_loadout_ship:
            self._clear_loadout_preview_pending_validation()

    def _on_loadout_ship_validated(self, _entry_widget, value: str):
        self._set_ship_cycle_indicator(0, 0)
        self.on_ship_selected(value)

    def _on_loadout_ship_cleared(self, _entry_widget):
        self._validated_loadout_ship = ""
        self._set_ship_cycle_indicator(0, 0)
        self._clear_loadout_preview_pending_validation()

    def _on_loadout_ship_text_changed(self, event):
        if getattr(event, "keysym", "") in ("Return", "Tab", "ISO_Left_Tab", "Escape"):
            return
        value = self.lo_ship_selector.get().strip().upper()
        try:
            placeholder = str(self.lo_ship_selector.cget("placeholder_text") or "").strip().upper()
        except Exception:
            placeholder = ""
        if placeholder and value == placeholder:
            value = ""
        if not value:
            return
        if value != self._validated_loadout_ship:
            self._clear_loadout_preview_pending_validation()

    def _set_ship_cycle_indicator(self, index: int, total: int):
        if not self._widget_exists("lo_ship_cycle_indicator"):
            return
        if total <= 0:
            self.lo_ship_cycle_indicator.configure(text="")
            return
        safe_index = max(0, min(index, total))
        self.lo_ship_cycle_indicator.configure(text=f"{safe_index}/{total}")

    def _clear_loadout_preview_pending_validation(self):
        if self._widget_exists("lo_slots_frame"):
            for widget in self.lo_slots_frame.winfo_children():
                widget.destroy()
        self.lo_slot_widgets = []
        if self._widget_exists("lo_status_terminal"):
            self.lo_status_terminal.delete("0.0", "end")
            self.lo_status_terminal.insert("end", "> SELECT A SHIP AND VALIDATE SUGGESTION (ENTER/CLICK).\n", "ACCENT")

    def _close_ship_popup(self):
        if hasattr(self, "_loadout_suggestion_manager"):
            try:
                self._loadout_suggestion_manager.close_all()
            except Exception:
                pass
        self._set_ship_cycle_indicator(0, 0)

    def _on_ship_tab_changed(self, *_args):
        # Ferme les suggestions loadout si l'utilisateur quitte l'onglet LOADOUT.
        try:
            current_tab = self.tabview.get()
        except Exception:
            current_tab = ""
        if current_tab != "LOADOUT":
            self._close_ship_popup()

    def setup_config_tab(self):
        """Onglet dédié à la création de sous-types et de slots par sous-type."""
        # Réserve la même hauteur visuelle que la rangée "EDIT COMPONENTS"
        # de l'onglet LOADOUT pour éviter un décalage vertical entre tabs.
        top_spacer = ctk.CTkFrame(self.tab_config, fg_color="transparent", height=20)
        top_spacer.pack(fill="x", padx=20, pady=(8, 2))
        top_spacer.pack_propagate(False)

        root = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=20, pady=(4, 20))

        left = ctk.CTkFrame(root, fg_color=DrakeConfig.BG_MAIN, width=250)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        left_content = ctk.CTkFrame(left, fg_color="transparent")
        left_content.pack(fill="both", expand=True, padx=0, pady=0)

        right = ctk.CTkFrame(root, fg_color=DrakeConfig.BG_TERMINAL)
        right.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        DrakeTitle2(left_content, text="CONFIGURATION").pack(pady=(12, 0))
        
        DrakeTitle3(left_content, text="CATEGORY / TYPES").pack(pady=(2, 8))

        DrakeTitle4(left_content, text="--- CATEGORY ---").pack(pady=(4, 2), padx=12)

        self.cfg_type_new_category = DrakeEntry(left_content, placeholder_text="NEW CATEGORY NAME (ex: WEAPON)")
        self.cfg_type_new_category.pack(pady=4, padx=12, fill="x")

        DrakeButton(left_content, text="ADD CATEGORY", command=self.action_add_category).pack(pady=(0, 8), padx=12, fill="x")

        ctk.CTkFrame(left_content, fg_color="#2a2a2a", height=1).pack(fill="x", padx=12, pady=(2, 10))

        DrakeTitle4(left_content, text="--- TYPES (BY CATEGORY) ---").pack(pady=(0, 2), padx=12)

        categories = self._get_all_component_categories()

        DrakeTitle4(left_content, text="CATEGORY").pack(pady=(0, 2), padx=12)
        self.cfg_type_category = DrakeComboBox(left_content, values=categories, command=self.on_cfg_type_category_change)
        self.cfg_type_category.pack(pady=4, padx=12, fill="x")

        self.cfg_type_entry = DrakeEntry(left_content, placeholder_text="NEW TYPE NAME (ex: SHIELD GENERATOR)")
        self.cfg_type_entry.pack(pady=4, padx=12, fill="x")

        type_actions = ctk.CTkFrame(left_content, fg_color="transparent")
        type_actions.pack(pady=(2, 8), padx=12, fill="x")
        DrakeButton(type_actions, text="ADD TYPE", command=self.action_add_subtype).pack(side="left", padx=(0, 4), fill="x", expand=True)

        bottom_type_block = ctk.CTkFrame(left_content, fg_color="transparent")
        bottom_type_block.pack(side="bottom", fill="x", padx=12, pady=(0, 4))

        DrakeTitle4(bottom_type_block, text="EXISTING TYPES").pack(pady=(0, 2), fill="x")
        self.cfg_type_selector = DrakeComboBox(bottom_type_block, values=[])
        self.cfg_type_selector.pack(pady=(0, 4), fill="x")

        DrakeClearButton(bottom_type_block, text="DELETE TYPE", command=self.action_delete_subtype,
            fg_color="#550000", hover_color="#770000").pack(pady=(0, 0), fill="x")

        # Slot creation form - fixed height container
        creation_panel = ctk.CTkFrame(right, fg_color="transparent")
        creation_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        DrakeTitle2(creation_panel, text="SLOT CREATION").pack(pady=(12, 8), padx=12)

        ship_values = self.controller.ship.list_ship_names()
        row1 = ctk.CTkFrame(creation_panel, fg_color="transparent")
        row1.pack(fill="x", padx=12)

        DrakeTitle4(row1, text="SHIP").pack(pady=(0, 4))
        self.cfg_slot_ship =  DrakeComboBoxLight(row1, values=ship_values, command=self.on_cfg_slot_ship_change)
        self.cfg_slot_ship.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="CATEGORY").pack(pady=(0, 4))
        self.cfg_slot_category = DrakeComboBoxLight(row1, values=categories, command=self.on_cfg_slot_category_change)
        self.cfg_slot_category.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="TYPE").pack(pady=(0, 4))
        self.cfg_slot_subtype = DrakeComboBoxLight(row1, values=[])
        self.cfg_slot_subtype.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="MAX QTY").pack(pady=(0, 4))
        self.cfg_slot_qty = DrakeEntryLight(row1, placeholder_text="ex: 2")
        self.cfg_slot_qty.pack(pady=4, fill="x")

        DrakeTitle4(row1, text="MAX SIZE").pack(pady=(0, 4))
        self.cfg_slot_size = DrakeEntryLight(row1, placeholder_text="ex: 1")
        self.cfg_slot_size.pack(pady=4, fill="x")

        slot_actions = ctk.CTkFrame(creation_panel, fg_color="transparent")
        slot_actions.pack(pady=10, padx=12, fill="x")
        slot_actions_inner = ctk.CTkFrame(slot_actions, fg_color="transparent")
        slot_actions_inner.pack(anchor="center")
        DrakeButton(slot_actions_inner, text="SAVE SLOT", command=self.action_save_slot_spec).pack(side="left", padx=4)

        # Registered specs - scrollable, expands to fill remaining space
        self.cfg_slot_list = ctk.CTkScrollableFrame(
            right,
            label_text="REGISTERED SLOT SPECS",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.cfg_slot_list.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)

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
            self.ship_results.insert("end", f"{ship.brand} {ship.name} ", (tag, "ship_name_white"))
            self.ship_results.insert("end", f"[{ship.size.upper()}]\n", "info_label")
            self.ship_results.insert("end", f"   ROLE: {ship.role} | CAREER: {ship.career}\n")
            self.ship_results.insert("end", "   [GENERAL]\n", "ACCENT")
            self.ship_results.insert(
                "end",
                f"   - CARGO: {ship.cargo} SCU | CLAIM: {ship.claim_time} min | EXPEDITE: {ship.expedite_time} min\n"
            )
            self.ship_results.insert("end", f"   - EXPEDITE COST: {ship.expedition_fee} aUEC\n")
            self.ship_results.insert("end", f"   - CREW: {ship.crew_size}\n")

            self.ship_results.insert("end", "   [FLIGHT]\n", "ACCENT")
            self.ship_results.insert(
                "end",
                f"   - SCM: {ship.scm_speed} | NAV: {ship.nav_max_speed} | HP: {ship.hp}\n"
            )
            self.ship_results.insert(
                "end",
                f"   - PITCH/YAW/ROLL: {ship.pitch}/{ship.yaw}/{ship.roll}\n"
            )
            self.ship_results.insert(
                "end",
                f"   - BOOST P/Y/R: {ship.boosted_pitch}/{ship.boosted_yaw}/{ship.boosted_roll}\n"
            )
            self.ship_results.insert("end", "   " + "-"*45 + "\n", "separator")

            # Affichage du loadout par défaut complet (inclut les slots vides).
            self.ship_results.insert("end", "   DEFAULT LOADOUT (BY CATEGORY):\n", "ACCENT")
            default_lines = self._build_default_loadout_lines(ship.name)
            if default_lines:
                for line in default_lines:
                    self.ship_results.insert("end", f"{line}\n")
            else:
                self.ship_results.insert("end", "   No slot specs available.\n", "small_info")
            
            self.ship_results.insert("end", f"{'='*60}\n\n")
            self.ship_results.tag_bind(tag, "<Double-Button-1>", lambda e, n=ship.name: self.open_edit_window(n))

    def _build_default_loadout_lines(self, ship_name: str) -> list[str]:
        """Construit les lignes d'affichage du profil DEFAULT, slots vides inclus."""
        ship_up = ship_name.upper()
        specs = self.controller.ship.get_ship_slot_specs(ship_up)
        if not specs:
            return []

        loadout_rows = self.controller.ship.app.query(
            """
            SELECT category, subtype_name, slot_number, component_name
            FROM ship_loadout
            WHERE ship_name = ? AND profile_name = 'DEFAULT'
            """,
            (ship_up,),
        )
        loadout_map = {
            (str(r[0]).upper(), str(r[1]).upper(), int(r[2])): str(r[3]).upper()
            for r in loadout_rows
        }

        equipped_names = sorted(set(loadout_map.values()))
        comp_map = {}
        for comp_name in equipped_names:
            comp_rows = self.controller.ship.app.query(
                "SELECT name, type_name, size, grade FROM components WHERE name = ?",
                (comp_name,),
            )
            if comp_rows:
                name, type_name, size, grade = comp_rows[0]
                comp_map[str(name).upper()] = {
                    "name": name,
                    "type_name": type_name,
                    "size": size,
                    "grade": grade,
                }

        lines = []
        current_category = None
        specs_sorted = sorted(
            specs,
            key=lambda s: (
                str(s.get("category", "")).upper(),
                str(s.get("subtype_name", "")).upper(),
            ),
        )

        for spec in specs_sorted:
            category = str(spec.get("category", "")).upper()
            subtype = str(spec.get("subtype_name", "GENERIC")).upper()
            max_qty = int(spec.get("max_qty", 0) or 0)
            max_size = int(spec.get("max_size", 0) or 0)

            if max_qty <= 0:
                continue

            if category != current_category:
                lines.append(f"   {category}")
                current_category = category

            for slot_index in range(max_qty):
                key = (category, subtype, slot_index)
                equipped_name = loadout_map.get(key)
                if equipped_name and equipped_name in comp_map:
                    comp = comp_map[equipped_name]
                    if category == "WEAPON":
                        lines.append(
                            f"     - {subtype} : {comp['type_name']} | S{comp['size']} | {comp['name']} | {comp['grade']}"
                        )
                    else:
                        lines.append(
                            f"     - {subtype} : S{comp['size']} | {comp['name']} | {comp['grade']}"
                        )
                else:
                    if category == "WEAPON":
                        lines.append(
                            f"     - {subtype} : EMPTY"
                        )
                    else:
                        lines.append(
                            f"     - {subtype} : S{max_size} | EMPTY | -"
                        )

        return lines

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
        """Affiche le catalogue de composants dans une liste scrollable."""
        if not self._widget_exists("comp_list_scroll"):
            return

        for widget in self.comp_list_scroll.winfo_children():
            widget.destroy()

        rows = self.controller.ship.list_components_catalog()
        if not rows:
            ctk.CTkLabel(
                self.comp_list_scroll,
                text="NO COMPONENT REGISTERED",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=12, pady=12)
            return

        last_cat = None
        for r in rows:
            if r[3] != last_cat:
                ctk.CTkLabel(
                    self.comp_list_scroll,
                    text=r[3],
                    font=("Orbitron", 12, "bold"),
                    text_color=DrakeConfig.ACCENT_PRIMARY,
                ).pack(anchor="w", padx=10, pady=(12, 4))
                last_cat = r[3]

            card = ctk.CTkFrame(
                self.comp_list_scroll,
                fg_color=DrakeConfig.BG_PANEL,
                corner_radius=0,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
            )
            card.pack(fill="x", padx=8, pady=3)

            component = {
                "name": r[0],
                "brand": r[1],
                "type_name": r[2],
                "category": r[3],
                "size": r[4],
                "grade": r[5],
            }

            if self.component_editing_name == r[0]:
                self._render_component_edit_row(card, component)
            else:
                self._render_component_display_row(card, component)

    def _render_component_display_row(self, parent, component):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        ctk.CTkLabel(
            left,
            text=component["name"],
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"{component['brand']}  |  {component['type_name']}",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="right", padx=10, pady=8)

        ctk.CTkLabel(
            right,
            text=f"S{component['size']}",
            font=("Segoe UI", 11, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
            width=36,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            right,
            text=f"GR-{component['grade']}",
            font=("Segoe UI", 11, "bold"),
            text_color=DrakeConfig.TEXT_MAIN,
            width=54,
        ).pack(side="left", padx=(0, 12))
        DrakeButton(
            right,
            text="EDIT",
            width=52,
            height=26,
            command=lambda name=component["name"]: self.start_component_edit(name),
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            right,
            text="DELETE",
            width=64,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.ACCENT_ERROR,
            text_color=DrakeConfig.ACCENT_ERROR,
            hover_color="#330000",
            command=lambda name=component["name"]: self.delete_component_row(name),
        ).pack(side="left")

    def _render_component_edit_row(self, parent, component):
        editor = ctk.CTkFrame(parent, fg_color="transparent")
        editor.pack(fill="x", expand=True, padx=8, pady=8)

        top = ctk.CTkFrame(editor, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))

        categories = self._get_all_component_categories()
        category_combo = DrakeComboBox(top, values=categories)
        category_combo.pack(side="left", padx=(0, 8), expand=True, fill="x")
        category_combo.set(component["category"])

        subtype_values = self.controller.ship.list_component_subtypes(component["category"])
        if not subtype_values:
            subtype_values = self.mapping_types.get(component["category"], [])
        subtype_combo = DrakeComboBox(top, values=subtype_values if subtype_values else [component["type_name"]])
        subtype_combo.pack(side="left", expand=True, fill="x")
        subtype_combo.set(component["type_name"])

        middle = ctk.CTkFrame(editor, fg_color="transparent")
        middle.pack(fill="x", pady=(0, 6))

        name_entry = DrakeEntry(middle, placeholder_text="MODEL NAME")
        name_entry.pack(side="left", padx=(0, 8), expand=True, fill="x")
        name_entry.insert(0, component["name"])

        brand_entry = DrakeEntry(middle, placeholder_text="MANUFACTURER")
        brand_entry.pack(side="left", expand=True, fill="x")
        brand_entry.insert(0, component["brand"])

        bottom = ctk.CTkFrame(editor, fg_color="transparent")
        bottom.pack(fill="x")

        size_combo = DrakeComboBox(bottom, values=["0", "1", "2", "3", "4", "5"])
        size_combo.pack(side="left", padx=(0, 8), expand=True, fill="x")
        size_combo.set(str(component["size"]))

        grade_combo = DrakeComboBox(bottom, values=["A", "B", "C", "D"])
        grade_combo.pack(side="left", padx=(0, 8), expand=True, fill="x")
        grade_combo.set(component["grade"])

        def on_inline_category_change(choice):
            values = self.controller.ship.list_component_subtypes(choice)
            if not values:
                values = self.mapping_types.get(choice, [])
            subtype_combo.configure(values=values if values else ["GENERIC"])
            subtype_combo.set(values[0] if values else "GENERIC")

        category_combo.configure(command=on_inline_category_change)

        DrakeButton(
            bottom,
            text="SAVE",
            width=52,
            height=26,
            command=lambda original=component["name"]: self.save_component_row(
                original,
                name_entry,
                brand_entry,
                category_combo,
                subtype_combo,
                size_combo,
                grade_combo,
            ),
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            bottom,
            text="CANCEL",
            width=70,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=self.cancel_component_edit,
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            bottom,
            text="DELETE",
            width=64,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.ACCENT_ERROR,
            text_color=DrakeConfig.ACCENT_ERROR,
            hover_color="#330000",
            command=lambda name=component["name"]: self.delete_component_row(name),
        ).pack(side="left")

    def start_component_edit(self, component_name):
        self.component_editing_name = (component_name or "").strip().upper()
        self.run_component_scan()

    def cancel_component_edit(self):
        self.component_editing_name = None
        self.run_component_scan()

    def save_component_row(self, original_name, name_entry, brand_entry, category_combo, subtype_combo, size_combo, grade_combo):
        name = name_entry.get().strip().upper()
        brand = brand_entry.get().strip().upper() or "UNKNOWN"
        category = category_combo.get().strip().upper()
        type_name = subtype_combo.get().strip().upper()
        grade = grade_combo.get().strip().upper()
        size_value = size_combo.get().strip()

        if not name or not category or not type_name or not size_value or not grade:
            self.controller.log("COMPONENT SAVE ABORTED: all component fields are required.", source="FLEET")
            return

        try:
            data = {
                "name": name,
                "brand": brand,
                "category": category,
                "type_name": type_name,
                "size": int(size_value),
                "grade": grade,
                "stats": "{}",
            }
            self.controller.ship.update_component_in_db(original_name, data)
            self.component_editing_name = None
            self.run_component_scan()
            self.update_selectors()
            if self.lo_ship_selector.get():
                self.refresh_loadout_view(self.lo_ship_selector.get())
            self.controller.log(f"COMPONENT UPDATED: {original_name} -> {name}", source="FLEET")
        except Exception as e:
            self.controller.log(f"COMPONENT SAVE FAILED: {e}", source="SYSTEM ERROR")

    def delete_component_row(self, component_name):
        name = (component_name or "").strip().upper()
        if not name:
            return
        if not DrakePopup.yesno("SYSTEM", f"DELETE COMPONENT {name} ?", parent=self.component_popup):
            return
        try:
            self.controller.ship.delete_component_from_db(name)
            if self.component_editing_name == name:
                self.component_editing_name = None
            self.run_component_scan()
            self.update_selectors()
            if self.lo_ship_selector.get():
                self.refresh_loadout_view(self.lo_ship_selector.get())
            self.controller.log(f"COMPONENT DELETED: {name}", source="FLEET")
        except Exception as e:
            self.controller.log(f"COMPONENT DELETE FAILED: {e}", source="SYSTEM ERROR")

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
        try:
            edit_win.grab_release()
        except Exception:
            pass
        try:
            edit_win.attributes("-topmost", False)
        except Exception:
            pass

        ctk.CTkLabel(
            edit_win,
            text=f"EDIT SHIP DATA: {ship_name.upper()}",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(12, 4))

        # Système d'onglets internes à la fenêtre d'édition
        inner_tabview = ctk.CTkTabview(edit_win, fg_color=DrakeConfig.BG_TERMINAL)
        inner_tabview.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        
        tab_general = inner_tabview.add("GENERAL")
        tab_flight = inner_tabview.add("FLIGHT")
        tab_logistics = inner_tabview.add("LOGISTICS")

        # --- DICTIONNAIRE DE WIDGETS POUR RÉCUPÉRATION ---
        self.edit_entries = {}

        def create_field(parent, label, key, default_val):
            self._create_form_label(parent, label)
            entry = DrakeEntryLight(parent)
            entry.insert(0, "" if default_val is None else str(default_val))
            entry.pack(fill="x", padx=20, pady=5)
            self.edit_entries[key] = entry

        def create_combo_field(parent, label, key, values, default_val, placeholder=None):
            self._create_form_label(parent, label)
            combo = DrakeComboBoxLight(parent, values=values)
            current_value = "" if default_val is None else str(default_val).upper().strip()
            if current_value and current_value not in [str(v).upper() for v in values]:
                combo.configure(values=list(values) + [current_value])
            combo.set(current_value or (placeholder or (values[0] if values else "")))
            combo.pack(fill="x", padx=20, pady=5)
            self.edit_entries[key] = combo

        def set_widget_value(widget, value):
            text = "" if value is None else str(value)
            if isinstance(widget, DrakeDualComboBox):
                widget.set(text)
                return
            if isinstance(widget, (DrakeComboBox, DrakeComboBoxLight)):
                current_values = [str(v).upper() for v in getattr(widget, "values", [])]
                target = text.upper().strip()
                if target and target not in current_values:
                    widget.configure(values=list(getattr(widget, "values", [])) + [target])
                widget.set(target or "")
                return
            widget.delete(0, "end")
            if text:
                widget.insert(0, text)

        def create_multiselect_field(parent, label, key, options, default_val):
            self._create_form_label(parent, label)
            ms = DrakeDualComboBox(parent, values=options, combo_class=DrakeComboBoxLight)
            ms.set("" if default_val is None else str(default_val))
            ms.pack(fill="x", padx=20, pady=5)
            self.edit_entries[key] = ms

        # --- ONGLET 1 : GENERAL (Identité) ---
        create_combo_field(
            tab_general,
            "MANUFACTURER",
            "brand",
            SHIP_MANUFACTURER_OPTIONS,
            ship.brand,
            placeholder="MANUFACTURER",
        )
        create_field(tab_general, "MODEL NAME", "name", ship.name)
        create_field(tab_general, "SIZE CLASS (S1-S6)", "size", ship.size)
        create_multiselect_field(tab_general, "ROLE(S)", "role", self.role_options, ship.role)
        create_combo_field(tab_general, "CAREER", "career", self.career_options or SHIP_CAREER_OPTIONS, ship.career, placeholder="CAREER")

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
        create_field(tab_logistics, "EXPEDITE COST (aUEC)", "expedition_fee", ship.expedition_fee)

        # --- BOUTON DE SAUVEGARDE GLOBALE ---
        def perform_full_update():
            try:
                int_fields = {
                    "scm_speed",
                    "nav_max_speed",
                    "hp",
                    "crew_size",
                }
                float_fields = {
                    "claim_time",
                    "expedite_time",
                    "pitch",
                    "yaw",
                    "roll",
                    "cargo",
                    "boosted_pitch",
                    "boosted_yaw",
                    "boosted_roll",
                }

                def parse_int(raw: str) -> int:
                    txt = str(raw or "").strip().replace(",", ".")
                    if txt == "":
                        return 0
                    return int(float(txt))

                def parse_float(raw: str) -> float:
                    txt = str(raw or "").strip().replace(",", ".")
                    if txt == "":
                        return 0.0
                    if ":" in txt:
                        parts = txt.split(":")
                        if len(parts) == 3 and all(part.isdigit() for part in parts):
                            hours, minutes, seconds = [int(part) for part in parts]
                            return round(hours * 60 + minutes + (seconds / 60.0), 2)
                    return float(txt)

                # On compile toutes les entrées dans un dictionnaire
                final_data = {}
                for key, widget in self.edit_entries.items():
                    val = widget.get()
                    # Conversion auto si la clé est connue pour être numérique
                    if key in int_fields:
                        final_data[key] = parse_int(val)
                    elif key in float_fields:
                        final_data[key] = parse_float(val)
                    else:
                        final_data[key] = val.upper()

                # Appel au contrôleur
                self.controller.ship.update_ship_specs(ship_name, final_data)
                
                self.controller.log("CORE DATABASE SYNCHRONIZED.", source="SYSTEM")
                edit_win.destroy()
                self.run_ship_scan() # Refresh le terminal
                
            except ValueError as e:
                self.controller.log(f"Invalid format in numeric field: {e}", source="SYSTEM ERROR")

        def import_ocr_screenshot():
            ocr_fields = {
                "brand",
                "role",
                "career",
                "size",
                "crew_size",
                "scm_speed",
                "nav_max_speed",
                "pitch",
                "yaw",
                "roll",
                "hp",
                "boosted_pitch",
                "boosted_yaw",
                "boosted_roll",
                "cargo",
                "claim_time",
                "expedite_time",
                "expedition_fee",
            }

            image_path = filedialog.askopenfilename(
                title="IMPORT SCREENSHOT SHIP STATS",
                filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")],
            )
            if not image_path:
                return

            try:
                parsed = self.controller.ship.extract_ship_stats_from_screenshot(image_path)
            except Exception as e:
                self.controller.log(f"OCR IMPORT FAILED: {e}", source="SYSTEM ERROR")
                return

            if not parsed:
                self.controller.log("OCR IMPORT: no stats detected in this screenshot.", source="FLEET")
                return

            # Ne jamais renommer le ship automatiquement depuis OCR.
            parsed.pop("name", None)

            for key in ocr_fields:
                widget = self.edit_entries.get(key)
                if widget is None:
                    continue
                set_widget_value(widget, "")

            for key, value in parsed.items():
                if key not in self.edit_entries:
                    continue
                widget = self.edit_entries[key]
                set_widget_value(widget, value)

            self.controller.log(
                f"OCR IMPORT: {len(parsed)} field(s) detected for {ship_name}",
                source="FLEET",
            )
            self.controller.log(
                f"OCR IMPORT READY: review the {len(parsed)} detected field(s), then click APPLY ALL MODIFICATIONS.",
                source="FLEET",
            )

        #ocr_btn = DrakeButton(edit_win, text="OCR SCREENSHOT IMPORT", command=import_ocr_screenshot)
        #ocr_btn.pack(pady=(10, 8), padx=20, fill="x")

        btn_cancel = DrakeButton(
            edit_win,
            text="CANCEL",
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=edit_win.destroy,
        )
        btn_cancel.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        btn_save = DrakeButton(
            edit_win,
            text="SAVE CHANGES",
            command=perform_full_update,
            height=40,
        )
        btn_save.pack(side="bottom", fill="x", padx=20, pady=(10, 5))

    def refresh_loadout_view(self, ship_name):
        """Affiche les slots à droite et met à jour le terminal à gauche."""
        if not ship_name:
            ship_name = self.lo_ship_selector.get().strip().upper()
        if not ship_name:
            return

        profile_name = self._get_active_profile()

        # 1. Nettoyage de l'existant
        self.lo_slot_widgets = []
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

        # 3. Création des lignes par catégorie + sous-type
        current_cat = None
        for spec in slot_specs:
            cat = spec["category"]
            subtype = spec["subtype_name"]
            max_qty = int(spec["max_qty"])
            max_size = int(spec["max_size"])

            # Titre de catégorie
            if current_cat != cat:
                ctk.CTkLabel(
                    self.lo_slots_frame,
                    text=cat,
                    font=("Orbitron", 12, "bold"),
                    text_color=DrakeConfig.ACCENT_PRIMARY,
                ).pack(pady=(10, 4), padx=10, anchor="w")
                current_cat = cat

            subtype_label = subtype if subtype != "GENERIC" else "ALL TYPES"
            ctk.CTkLabel(
                self.lo_slots_frame,
                text=f"{subtype_label}  |  MAX {max_qty}",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(pady=(0, 3), padx=12, anchor="w")

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
                card = ctk.CTkFrame(
                    self.lo_slots_frame,
                    fg_color=DrakeConfig.BG_PANEL,
                    corner_radius=0,
                    border_width=1,
                    border_color=DrakeConfig.BORDER_COLOR,
                )
                card.pack(fill="x", padx=8, pady=3)

                left = ctk.CTkFrame(card, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True, padx=10, pady=5)

                ctk.CTkLabel(
                    left,
                    text=f"S{max_size} SLOT {i+1}",
                    font=("Segoe UI", 11, "bold"),
                    anchor="w",
                ).pack(anchor="w")
                
                # Menu de sélection
                combo = DrakeComboBoxLight(card, values=["EMPTY"] + available, width=220)
                combo.set(current)
                combo.pack(side="left", padx=(0, 10), pady=5)
                self.lo_slot_widgets.append((cat, subtype, i, combo))

                # Bouton de sauvegarde INDIVIDUEL
                save_btn = DrakeButton(
                    card,
                    text="SAVE",
                    width=60,
                    height=24,
                    command=lambda c=combo, ct=cat, st=subtype, idx=i: self.action_mount(ct, st, idx, c.get()),
                )
                save_btn.pack(side="right", padx=10, pady=5)

        self._refresh_loadout_status_terminal_from_widgets(ship_name)
        self._render_loadout_global_actions()

    def _refresh_loadout_status_terminal_from_widgets(self, ship_name=None):
        """Rafraîchit le résumé avec les valeurs actuellement visibles dans les combos."""
        if not self._widget_exists("lo_status_terminal"):
            return

        if not ship_name:
            ship_name = self.lo_ship_selector.get().strip().upper()
        profile_name = self._get_active_profile()

        self.lo_status_terminal.delete("0.0", "end")
        self.lo_status_terminal.insert("end", f"> ANALYZING {ship_name} [{profile_name}]...\n", "ACCENT")

        for category, subtype_name, slot_index, combo in self.lo_slot_widgets:
            subtype_label = subtype_name if subtype_name != "GENERIC" else "ALL TYPES"
            try:
                selection = (combo.get() or "EMPTY").strip().upper() or "EMPTY"
            except Exception:
                selection = "EMPTY"
            self.lo_status_terminal.insert(
                "end",
                f"[{category}::{subtype_label}] SLT{slot_index + 1}: {selection}\n",
            )

    def _render_loadout_global_actions(self):
        """Affiche les actions globales à la fin de la liste des slots (zone droite)."""
        if not self._widget_exists("lo_slots_frame"):
            return

        actions_wrap = ctk.CTkFrame(self.lo_slots_frame, fg_color="transparent")
        actions_wrap.pack(fill="x", pady=(14, 8))

        actions = ctk.CTkFrame(actions_wrap, fg_color="transparent")
        actions.pack(anchor="center")

        DrakeButton(
            actions,
            text="SAVE ALL SLOTS",
            command=self.action_save_all_slots,
            width=180,
        ).pack(side="left", padx=(0, 8))

        DrakeClearButton(
            actions,
            text="CLEAR ALL TO EMPTY",
            command=self.action_clear_all_slots_to_empty,
            fg_color="#440000",
            hover_color="#770000",
            width=180,
        ).pack(side="left")

    def action_save_all_slots(self):
        """Enregistre tous les slots visibles d'un coup pour le profil actif."""
        ship_name = self.lo_ship_selector.get().strip().upper()
        profile_name = self._get_active_profile()
        if not ship_name:
            self.controller.log("LOADOUT SAVE ABORTED: select a ship first.", source="FLEET")
            return
        if not self.lo_slot_widgets:
            self.controller.log("LOADOUT SAVE ABORTED: no slot to save.", source="FLEET")
            return

        total = 0
        failed = 0
        for category, subtype_name, slot_index, combo in self.lo_slot_widgets:
            selection = (combo.get() or "EMPTY").strip().upper() or "EMPTY"
            total += 1
            ok = self.controller.ship.mount_component(
                ship_name,
                category,
                subtype_name,
                slot_index,
                selection,
                profile_name,
            )
            if not ok:
                failed += 1

        self.refresh_loadout_view(ship_name)

        if failed:
            self.controller.log(
                f"BATCH SAVE PARTIAL: {ship_name} [{profile_name}] {total - failed}/{total} slots saved.",
                source="FLEET",
            )
            return

        self.controller.log(
            f"BATCH SAVE OK: {ship_name} [{profile_name}] {total} slots saved.",
            source="FLEET",
        )

    def action_clear_all_slots_to_empty(self):
        """Vide tous les slots visibles (EMPTY) puis sauvegarde en lot."""
        ship_name = self.lo_ship_selector.get().strip().upper()
        profile_name = self._get_active_profile()
        if not ship_name:
            self.controller.log("CLEAR ALL ABORTED: select a ship first.", source="FLEET")
            return
        if not self.lo_slot_widgets:
            self.controller.log("CLEAR ALL ABORTED: no slot to clear.", source="FLEET")
            return

        if not DrakePopup.yesno("SYSTEM", f"SET ALL SLOTS TO EMPTY FOR [{profile_name}] ?", parent=self):
            return

        for _, _, _, combo in self.lo_slot_widgets:
            combo.set("EMPTY")

        self.controller.log(
            f"CLEAR ALL REQUESTED: {ship_name} [{profile_name}] set to EMPTY before batch save.",
            source="FLEET",
        )

        self.action_save_all_slots()

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
            self.controller.log("Failed to sync with ship database.", source="SYSTEM ERROR")
        
    def action_mount(self, category, subtype_name, slot_index, component_name):
        """Enregistre le composant sélectionné en base de données."""
        ship_name = self.lo_ship_selector.get().strip().upper()
        profile_name = self._get_active_profile()
        if not ship_name: return

        # Appel au contrôleur pour sauvegarder en DB
        if self.controller.ship.mount_component(ship_name, category, subtype_name, slot_index, component_name, profile_name):
            # On garde les autres modifications locales non sauvegardées intactes.
            self._refresh_loadout_status_terminal_from_widgets(ship_name)
            self.controller.log(
                f"Component mounted: {ship_name} [{profile_name}] {category}/{subtype_name} -> {component_name}",
                source="FLEET",
            )
        else:
            self.controller.log("Database Sync Failed. Incompatible hardware.", source="SYSTEM ERROR")
    
    def action_clear_loadout(self):
        """Supprime tous les composants installés sur le vaisseau actuel."""
        ship_name = self.lo_ship_selector.get().strip().upper()
        profile_name = self._get_active_profile()
        if not ship_name: return
        
        if DrakePopup.yesno("SYSTEM", f"WIPE PROFILE [{profile_name}] FOR {ship_name}?", parent=self):
            self.controller.ship.clear_ship_loadout(ship_name, profile_name)
            # Rafraîchissement de l'interface
            self.refresh_loadout_view(ship_name)
            self.controller.log(
                f"PROFILE WIPE OK: {ship_name} [{profile_name}] cleared.",
                source="FLEET",
            )
    
    def update_selectors(self):
        """Rafraîchit la liste des vaisseaux dans le menu déroulant."""
        try:
            ships = self.controller.ship.list_ship_names()
            self._loadout_ship_values = ships or []
            current = self.lo_ship_selector.get().strip().upper() if self._widget_exists("lo_ship_selector") else ""
            known_ships = [str(s).strip().upper() for s in ships]
            if ships and current and current not in known_ships:
                self.lo_ship_selector.delete(0, "end")
                self.lo_ship_selector.insert(0, str(ships[0]).strip().upper())
                self.on_ship_selected(str(ships[0]).strip().upper())

            if hasattr(self, "cfg_slot_ship"):
                self.cfg_slot_ship.configure(values=ships)
                if ships and self.cfg_slot_ship.get() not in ships:
                    self.cfg_slot_ship.set(ships[0])
                    self.on_cfg_slot_ship_change(ships[0])

            if hasattr(self, "cfg_type_category"):
                categories = self._get_all_component_categories()
                self.cfg_type_category.configure(values=categories)
                self.cfg_slot_category.configure(values=categories)

            if self._widget_exists("new_comp_category"):
                categories = self._get_all_component_categories()
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
            self.controller.log("ADD TYPE ABORTED: type is required.", source="FLEET")
            return
        try:
            self.controller.ship.create_component_category(category)
            self.cfg_type_new_category.delete(0, "end")
            self.update_selectors()
            self.cfg_type_category.set(category)
            self.cfg_slot_category.set(category)
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(category)
            self.controller.log(f"CATEGORY CREATED: {category}", source="FLEET")
        except Exception as e:
            self.controller.log(f"CATEGORY CREATE FAILED: {e}", source="SYSTEM ERROR")

    def refresh_type_terminal(self):
        return

    def action_add_category(self):
        category = self.cfg_type_new_category.get().strip().upper()
        if not category:
            self.controller.log("ADD CATEGORY ABORTED: category is required.", source="FLEET")
            return
        try:
            self.controller.ship.create_component_category(category)
            self.cfg_type_new_category.delete(0, "end")
            self.update_selectors()
            self.cfg_type_category.set(category)
            self.cfg_slot_category.set(category)
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(category)
            self.controller.log(f"CATEGORY CREATED: {category}", source="FLEET")
        except Exception as e:
            self.controller.log(f"CATEGORY CREATE FAILED: {e}", source="SYSTEM ERROR")

    def action_add_subtype(self):
        category = self.cfg_type_category.get().strip().upper()
        subtype = self.cfg_type_entry.get().strip().upper()
        if not category or not subtype:
            self.controller.log("ADD SUBTYPE ABORTED: category and type are required.", source="FLEET")
            return
        try:
            self.controller.ship.create_component_subtype(category, subtype)
            self.cfg_type_entry.delete(0, "end")
            self.on_cfg_type_category_change(category)
            self.on_cfg_slot_category_change(self.cfg_slot_category.get())
            if self._widget_exists("new_comp_category"):
                self.on_category_change(self.new_comp_category.get())
            self.controller.log(f"SUBTYPE CREATED: {category}::{subtype}", source="FLEET")
        except Exception as e:
            self.controller.log(f"SUBTYPE CREATE FAILED: {e}", source="SYSTEM ERROR")

    def action_delete_subtype(self):
        category = self.cfg_type_category.get().strip().upper()
        subtype = self.cfg_type_selector.get().strip().upper()
        if not subtype or subtype == "NO DATA":
            return
        if not DrakePopup.yesno("SYSTEM", f"DELETE TYPE {subtype} ?", parent=self):
            return
        self.controller.ship.delete_component_subtype(category, subtype)
        self.on_cfg_type_category_change(category)
        self.on_cfg_slot_category_change(self.cfg_slot_category.get())
        if self._widget_exists("new_comp_category"):
            self.on_category_change(self.new_comp_category.get())
        self.controller.log(f"SUBTYPE DELETED: {category}::{subtype}", source="FLEET")

    def on_cfg_slot_ship_change(self, _ship_name):
        self.refresh_slot_terminal()

    def _set_slot_type_locked(self, locked: bool):
        if not hasattr(self, "cfg_slot_subtype"):
            return
        subtype_hover = getattr(self.cfg_slot_subtype, "_HOVER", DrakeConfig.BG_PANEL)
        if locked:
            self.cfg_slot_subtype.entry.configure(
                command=lambda: None,
                text_color="#6f6f6f",
                hover_color=subtype_hover,
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
                hover_color=subtype_hover,
            )
            self.cfg_slot_subtype.button.configure(
                command=self.cfg_slot_subtype.toggle_dropdown,
                fg_color=DrakeConfig.ACCENT_PRIMARY,
                hover_color=DrakeConfig.ACCENT_HOVER,
                text_color="#000000",
            )

    def on_cfg_slot_category_change(self, category):
        category_up = (category or "").strip().upper()
        self._set_slot_type_locked(False)

        if category_up == "WEAPON":
            weapon_groups = ["GENERIC", "S1", "S2", "S3", "S4", "S5"]
            self.cfg_slot_subtype.configure(values=weapon_groups)
            current = self.cfg_slot_subtype.get().strip().upper()
            self.cfg_slot_subtype.set(current if current in weapon_groups else "GENERIC")
            return

        subtypes = self.controller.ship.list_component_subtypes(category_up)
        if not subtypes:
            subtypes = self.mapping_types.get(category_up, [])
        self.cfg_slot_subtype.configure(values=subtypes if subtypes else ["GENERIC"])
        if subtypes:
            self.cfg_slot_subtype.set(subtypes[0])
        else:
            self.cfg_slot_subtype.set("GENERIC")

    def refresh_slot_terminal(self):
        if not hasattr(self, "cfg_slot_list"):
            return
        ship_name = self.cfg_slot_ship.get().strip().upper() if hasattr(self, "cfg_slot_ship") else ""
        current_selection = (self.cfg_slot_selected_key or "").strip().upper()

        for widget in self.cfg_slot_list.winfo_children():
            widget.destroy()

        if not ship_name:
            return
        specs = self.controller.ship.list_subtype_specs(ship_name)

        ctk.CTkLabel(
            self.cfg_slot_list,
            text=f"SLOT SPECS - {ship_name}",
            font=("Orbitron", 12, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", padx=10, pady=(8, 6))

        keys = []
        edit_key = (self.cfg_slot_editing_key or "").strip().upper()
        for cat, subtype, qty, size in specs:
            key = f"{cat}::{subtype}"
            keys.append(key)

            card = ctk.CTkFrame(
                self.cfg_slot_list,
                fg_color=DrakeConfig.BG_PANEL,
                corner_radius=0,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
            )
            card.pack(fill="x", padx=8, pady=3)

            if edit_key == key:
                self._render_slot_edit_row(card, cat, subtype, qty, size, ship_name)
            else:
                self._render_slot_display_row(card, cat, subtype, qty, size)

        if not specs:
            ctk.CTkLabel(
                self.cfg_slot_list,
                text="NO SLOT SPEC REGISTERED",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=12, pady=(4, 10))

        if keys:
            self.cfg_slot_selected_key = current_selection if current_selection in keys else keys[0]
        else:
            self.cfg_slot_selected_key = ""

    def start_slot_edit(self, key: str):
        """Passe une ligne de slot spec en mode édition inline."""
        self.cfg_slot_editing_key = (key or "").strip().upper()
        self.refresh_slot_terminal()

    def cancel_slot_edit(self):
        """Annule l'édition inline d'une ligne de slot spec."""
        self.cfg_slot_editing_key = None
        self.refresh_slot_terminal()

    def save_slot_row_inline(self, original_cat, original_subtype, category_combo, subtype_combo, qty_entry, size_entry):
        """Sauvegarde les modifications inline d'une ligne de slot spec."""
        ship_name = self.cfg_slot_ship.get().strip().upper()
        new_cat = category_combo.get().strip().upper()
        new_subtype = subtype_combo.get().strip().upper()
        qty_raw = qty_entry.get().strip()
        size_raw = size_entry.get().strip()

        if not ship_name or not new_cat or not new_subtype or not qty_raw or not size_raw:
            self.controller.log("SLOT SPEC SAVE ABORTED: all fields are required.", source="FLEET")
            return

        try:
            qty = int(qty_raw)
            max_size = int(size_raw)
        except ValueError:
            self.controller.log("SLOT SPEC SAVE FAILED: qty and size must be integers.", source="FLEET")
            return

        if qty > 6:
            self.controller.log("SLOT SPEC SAVE ABORTED: max qty is 6.", source="FLEET")
            return
        if max_size > 10:
            self.controller.log("SLOT SPEC SAVE ABORTED: max size is 10.", source="FLEET")
            return

        try:
            if new_cat != original_cat or new_subtype != original_subtype:
                self.controller.ship.delete_subtype_spec(ship_name, original_cat, original_subtype)
            self.controller.ship.upsert_subtype_spec(ship_name, new_cat, new_subtype, qty, max_size)
            self.cfg_slot_editing_key = None
            self.refresh_slot_terminal()
            if self.lo_ship_selector.get().strip().upper() == ship_name:
                self.refresh_loadout_view(ship_name)
            self.controller.log(
                f"SLOT SPEC SAVED: {ship_name} {new_cat}::{new_subtype} QTY {qty} SIZE S{max_size}",
                source="FLEET",
            )
        except Exception as e:
            self.controller.log(f"SLOT SPEC SAVE FAILED: {e}", source="SYSTEM ERROR")

    def _render_slot_display_row(self, parent, cat, subtype, qty, size):
        """Affiche une ligne de slot spec en mode lecture."""
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=10, pady=7)

        ctk.CTkLabel(
            left,
            text=f"{cat} :: {subtype}",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"QTY {qty}  |  SIZE S{size}",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="right", padx=10, pady=7)

        DrakeButton(
            right,
            text="EDIT",
            width=52,
            height=26,
            command=lambda c=cat, st=subtype: self.start_slot_edit(f"{c}::{st}"),
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            right,
            text="DELETE",
            width=64,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.ACCENT_ERROR,
            text_color=DrakeConfig.ACCENT_ERROR,
            hover_color="#330000",
            command=lambda c=cat, st=subtype: self.action_delete_slot_spec_direct(c, st),
        ).pack(side="left")

    def _render_slot_edit_row(self, parent, cat, subtype, qty, size, ship_name):
        """Affiche une ligne de slot spec en mode édition inline."""
        editor = ctk.CTkFrame(parent, fg_color="transparent")
        editor.pack(fill="x", expand=True, padx=8, pady=8)

        top = ctk.CTkFrame(editor, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))

        categories = self._get_all_component_categories()
        category_combo = DrakeComboBox(top, values=categories)
        category_combo.set(cat)
        category_combo.pack(side="left", padx=(0, 8), expand=True, fill="x")

        subtypes = self.controller.ship.list_component_subtypes(cat)
        if not subtypes:
            subtypes = self.mapping_types.get(cat, [])
        subtype_combo = DrakeComboBox(top, values=subtypes if subtypes else ["GENERIC"])
        subtype_combo.set(subtype)
        subtype_combo.pack(side="left", expand=True, fill="x")

        def on_inline_category_change(choice):
            subs = self.controller.ship.list_component_subtypes(choice)
            if not subs:
                subs = self.mapping_types.get(choice, [])
            subtype_combo.configure(values=subs if subs else ["GENERIC"])
            subtype_combo.set(subs[0] if subs else "GENERIC")

        category_combo.configure(command=on_inline_category_change)

        middle = ctk.CTkFrame(editor, fg_color="transparent")
        middle.pack(fill="x", pady=(0, 6))

        qty_entry = DrakeEntry(middle, placeholder_text="MAX QTY")
        qty_entry.pack(side="left", padx=(0, 8), expand=True, fill="x")
        qty_entry.insert(0, str(qty))

        size_entry = DrakeEntry(middle, placeholder_text="MAX SIZE")
        size_entry.pack(side="left", expand=True, fill="x")
        size_entry.insert(0, str(size))

        bottom = ctk.CTkFrame(editor, fg_color="transparent")
        bottom.pack(fill="x")

        DrakeButton(
            bottom,
            text="SAVE",
            width=52,
            height=26,
            command=lambda oc=cat, os=subtype: self.save_slot_row_inline(
                oc, os, category_combo, subtype_combo, qty_entry, size_entry
            ),
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            bottom,
            text="CANCEL",
            width=70,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=self.cancel_slot_edit,
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            bottom,
            text="DELETE",
            width=64,
            height=26,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.ACCENT_ERROR,
            text_color=DrakeConfig.ACCENT_ERROR,
            hover_color="#330000",
            command=lambda c=cat, st=subtype: self.action_delete_slot_spec_direct(c, st),
        ).pack(side="left")

    def _pick_slot_spec_from_list(self, selection):
        if not selection or "::" not in selection:
            return
        self.cfg_slot_selected_key = selection.strip().upper()
        self.on_cfg_slot_pick(selection)

    def action_delete_slot_spec_direct(self, category, subtype):
        """Suppression directe depuis une ligne de la liste des specs."""
        ship_name = self.cfg_slot_ship.get().strip().upper()
        cat = (category or "").strip().upper()
        st = (subtype or "").strip().upper()
        if not ship_name or not cat or not st:
            return
        if not DrakePopup.yesno("SYSTEM", f"DELETE SLOT SPEC {cat}::{st} ?", parent=self):
            return
        self.controller.ship.delete_subtype_spec(ship_name, cat, st)
        self.cfg_slot_editing_key = None
        self.refresh_slot_terminal()
        if self.lo_ship_selector.get().strip().upper() == ship_name:
            self.refresh_loadout_view(ship_name)
        self.controller.log(f"SLOT SPEC DELETED: {ship_name} {cat}::{st}", source="FLEET")

    def on_cfg_slot_pick(self, selection):
        if getattr(self, "_suspend_cfg_slot_pick", False):
            return
        if not selection or selection == "NO DATA" or "::" not in selection:
            return
        self.cfg_slot_selected_key = selection.strip().upper()
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
        if not ship_name or not category or not subtype:
            self.controller.log("SLOT SPEC SAVE ABORTED: ship / category / subtype are required.", source="FLEET")
            return
        try:
            qty = int(self.cfg_slot_qty.get().strip())
            max_size = int(self.cfg_slot_size.get().strip())

            if qty > 6:
                self.controller.log("SLOT SPEC SAVE ABORTED: max qty is 6.", source="FLEET")
                return
            if max_size > 10:
                self.controller.log("SLOT SPEC SAVE ABORTED: max size is 10.", source="FLEET")
                return

            self.controller.ship.upsert_subtype_spec(ship_name, category, subtype, qty, max_size)
            self.refresh_slot_terminal()
            self.cfg_slot_category.set(category)
            self.on_cfg_slot_category_change(category)
            self.cfg_slot_subtype.set(subtype)
            if self.lo_ship_selector.get().strip().upper() == ship_name:
                self.refresh_loadout_view(ship_name)
            self.controller.log(
                f"SLOT SPEC SAVED: {ship_name} {category}::{subtype} QTY {qty} SIZE S{max_size}",
                source="FLEET",
            )
        except Exception as e:
            self.controller.log(f"SLOT SPEC SAVE FAILED: {e}", source="SYSTEM ERROR")

    def action_delete_slot_spec(self):
        ship_name = self.cfg_slot_ship.get().strip().upper()
        selection = (self.cfg_slot_selected_key or "").strip().upper()
        if not ship_name or not selection or selection == "NO DATA" or "::" not in selection:
            return
        cat, subtype = selection.split("::", 1)
        if not DrakePopup.yesno("SYSTEM", f"DELETE SLOT SPEC {cat}::{subtype} ?", parent=self):
            return
        self.controller.ship.delete_subtype_spec(ship_name, cat, subtype)
        self.refresh_slot_terminal()
        if self.lo_ship_selector.get().strip().upper() == ship_name:
            self.refresh_loadout_view(ship_name)
        self.controller.log(f"SLOT SPEC DELETED: {ship_name} {cat}::{subtype}", source="FLEET")

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
        ship_name = (ship_name or "").strip().upper()
        if not ship_name:
            return
        self._validated_loadout_ship = ship_name
        self.update_profile_list(ship_name)
        self.refresh_loadout_view(ship_name)

    def action_create_profile(self):
        ship_name = self.lo_ship_selector.get().strip().upper()
        if not ship_name:
            self.controller.log("PROFILE CREATE ABORTED: select a ship first.", source="FLEET")
            return

        new_profile = self.lo_new_profile.get().strip().upper()
        if not new_profile:
            self.controller.log("PROFILE CREATE ABORTED: enter a profile name.", source="FLEET")
            return

        source_profile = self._get_active_profile()
        created = self.controller.ship.create_loadout_profile(
            ship_name,
            new_profile,
            source_profile=source_profile,
            overwrite=False,
        )
        if not created:
            self.controller.log(f"PROFILE CREATE ABORTED: {new_profile} already exists.", source="FLEET")
            return

        self.lo_new_profile.delete(0, "end")
        self.update_profile_list(ship_name, selected_profile=new_profile)
        self.refresh_loadout_view(ship_name)
        self.controller.log(
            f"PROFILE CREATED: {ship_name} [{new_profile}] cloned from [{source_profile}]",
            source="FLEET",
        )

    def action_load_profile(self, profile_name):
        """Charge la configuration d'un profil spécifique."""
        ship_name = self.lo_ship_selector.get().strip().upper()
        if not ship_name or ship_name == "":
            return
        self.refresh_loadout_view(ship_name)
        self.controller.log(f"PROFILE LOADED: {ship_name} [{profile_name}]", source="FLEET")