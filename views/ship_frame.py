from tkinter import messagebox
import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeTerminal, DrakeButton, DrakeComboBox

class ShipFrame(ctk.CTkFrame):
    """Interface de gestion de la flotte (Ships, Components & Loadout)."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
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

        self.title_label = ctk.CTkLabel(
            header, text="FLEET DATABASE // SECURE ACCESS", 
            font=("Orbitron", 16, "bold"), 
            text_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.title_label.pack(side="left", expand=True, padx=(100, 0))

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
        self.tab_components = self.tabview.add("COMPONENTS")
        self.tab_loadout = self.tabview.add("LOADOUT")

        self.setup_ships_tab()
        self.setup_loadout_tab()
        self.setup_components_tab()

    # --- ONGLET SHIPS ---

    def setup_ships_tab(self):
        """Moteur de recherche et fiches techniques."""
        self.ship_search_entry = ctk.CTkEntry(
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
        self.comp_container = ctk.CTkFrame(self.tab_components, fg_color="transparent")
        self.comp_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Terminal de visualisation (Gauche)
        self.comp_list_terminal = DrakeTerminal(self.comp_container)
        self.comp_list_terminal.pack(side="right", fill="both", expand=True, padx=(0, 10))
        
        # Formulaire d'ajout (Droite)
        self.add_comp_frame = ctk.CTkFrame(self.comp_container, width=280, fg_color=DrakeConfig.BG_MAIN)
        self.add_comp_frame.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.add_comp_frame, text="ADD COMPONENT", font=("Orbitron", 14, "bold"), 
                     text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=15)

        # Champs du formulaire
        self._create_form_label(self.add_comp_frame, "SLOT CATEGORY")
        self.new_comp_category = DrakeComboBox(self.add_comp_frame, 
                                                values=list(self.mapping_types.keys()), 
                                                command=self.on_category_change)
        self.new_comp_category.pack(pady=5, padx=15, fill="x")

        self._create_form_label(self.add_comp_frame, "MODULE TYPE")
        self.new_comp_type = DrakeComboBox(self.add_comp_frame, values=[])
        self.new_comp_type.pack(pady=5, padx=15, fill="x")

        self.new_comp_name = ctk.CTkEntry(self.add_comp_frame, placeholder_text="MODEL NAME (ex: FR-66)")
        self.new_comp_name.pack(pady=5, padx=15, fill="x")
        
        self.new_comp_brand = ctk.CTkEntry(self.add_comp_frame, placeholder_text="MANUFACTURER (ex: AEGIS)")
        self.new_comp_brand.pack(pady=5, padx=15, fill="x")

        self._create_form_label(self.add_comp_frame, "SIZE")
        self.new_comp_size = DrakeComboBox(self.add_comp_frame, values=["0", "1", "2", "3", "4", "5"])
        self.new_comp_size.pack(pady=5, padx=15, fill="x")

        self._create_form_label(self.add_comp_frame, "GRADE")
        self.new_comp_grade = DrakeComboBox(self.add_comp_frame, values=["A", "B", "C", "D"])
        self.new_comp_grade.set("C")
        self.new_comp_grade.pack(pady=5, padx=15, fill="x")

        DrakeButton(self.add_comp_frame, text="SAVE TO DATABASE", 
                    command=self.save_new_component).pack(pady=30, padx=15, fill="x")
        
        self.update_selectors()

        # Initialisation par défaut
        self.on_category_change("SYSTEMS")
        self.run_component_scan()

        # --- ONGLET LOADOUT ---

    def setup_loadout_tab(self):
        """Interface d'équipement dynamique."""
        self.lo_container = ctk.CTkFrame(self.tab_loadout, fg_color="transparent")
        self.lo_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- PANNEAU DE CONTRÔLE (GAUCHE) ---
        ctrl_panel = ctk.CTkFrame(self.lo_container, fg_color=DrakeConfig.BG_MAIN, width=200)
        ctrl_panel.pack(side="left", fill="y", padx=(0, 10))
        ctrl_panel.pack_propagate(False) # Garde la largeur fixe

        ctk.CTkLabel(ctrl_panel, text="LOADOUT CONTROL", font=("Orbitron", 12, "bold"), 
                    text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=10)

        # 1. Sélecteur de vaisseau
        self.lo_ship_selector = DrakeComboBox(ctrl_panel, values=[], command=self.refresh_loadout_view)
        self.lo_ship_selector.pack(pady=5, padx=10)

        # 2. Filtre de catégorie
        self._create_form_label(ctrl_panel, "FILTER BY CAT")
        self.lo_filter_cat = DrakeComboBox(ctrl_panel, values=["ALL", "WEAPON", "SYSTEMS", "PROPULSION"],
                                        command=self.filter_components_by_cat)
        self.lo_filter_cat.pack(pady=5, padx=10)
        self.lo_filter_cat.set("ALL")

        # 3. Sélecteur de composant (C'est lui qui manquait !)
        self._create_form_label(ctrl_panel, "QUICK INSTALL")
        self.lo_comp_selector = DrakeComboBox(ctrl_panel, values=[]) # Déclaré ICI
        self.lo_comp_selector.pack(pady=5, padx=10)

        # 4. Boutons
        DrakeButton(ctrl_panel, text="INSTALL MODULE", command=self.action_equip).pack(pady=20, padx=10, fill="x")
        DrakeButton(ctrl_panel, text="REFRESH LISTS", command=self.update_selectors).pack(pady=5, padx=10)

        # --- PANNEAU DES SLOTS (DROITE) ---
        self.lo_slots_frame = ctk.CTkScrollableFrame(
            self.lo_container, 
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text="SHIP HARDPOINTS CONFIGURATION",
            label_font=("Orbitron", 12),
            label_text_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.lo_slots_frame.pack(side="right", fill="both", expand=True)

        # MAINTENANT on peut appeler update_selectors() car tous les widgets existent
        self.update_selectors()

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

        rows = self.controller.query("SELECT name FROM ships WHERE name LIKE ? OR brand LIKE ? LIMIT 10", (f"%{q}%", f"%{q}%"))
        for row in rows:
            ship = self.controller.ship.load_ship_as_model(row[0])
            if not ship: continue
            
            tag = f"edit_{ship.name.replace(' ', '_')}"
            self.ship_results.insert("end", " ■ ", "ACCENT") 
            self.ship_results.insert("end", f"{ship.brand} {ship.name} ", (tag, "NEUTRE"))
            self.ship_results.insert("end", f"[{ship.size.upper()}]\n", "info_label")
            self.ship_results.insert("end", f"   ROLE: {ship.role} | CREW: {ship.crew_size} | CARGO: {ship.cargo} SCU\n")
            self.ship_results.insert("end", "   " + "-"*45 + "\n", "separator")
            
            # Affichage des composants équipés
            if ship.components:
                self.ship_results.insert("end", "   🛰️ LOADOUT:\n", "ACCENT")
                for c in ship.components:
                    self.ship_results.insert("end", f"     • [{c.category}] {c.brand} {c.name} (S{c.size})\n")
            
            self.ship_results.insert("end", f"{'='*60}\n\n")
            self.ship_results.tag_bind(tag, "<Double-Button-1>", lambda e, n=ship.name: self.open_edit_window(n))

    def save_new_component(self):
        """Sauvegarde un composant et rafraîchit les vues."""
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
            print(f"Error: {e}")

    def update_selectors(self):
        """Met à jour les listes déroulantes de l'onglet Loadout."""
        ships = [r[0] for r in self.controller.query("SELECT name FROM ships")]
        self.lo_ship_selector.configure(values=ships)
        self.filter_components_by_cat(self.lo_filter_cat.get())

    # --- ACTIONS ---
    def on_category_change(self, choice):
        new_values = self.mapping_types.get(choice, [])
        self.new_comp_type.configure(values=new_values)
        if new_values: self.new_comp_type.set(new_values[0])

    def filter_components_by_cat(self, choice):
        sql = "SELECT name FROM components" if choice == "ALL" else "SELECT name FROM components WHERE category = ?"
        params = () if choice == "ALL" else (choice,)
        comps = [r[0] for r in self.controller.query(sql, params)]
        self.lo_comp_selector.configure(values=comps)
        if comps: self.lo_comp_selector.set(comps[0])

    def action_equip(self):
        ship, comp = self.lo_ship_selector.get(), self.lo_comp_selector.get()
        if ship and comp:
            if self.controller.ship.equip_component(ship, comp):
                self.refresh_loadout_view(ship)

    def action_clear_loadout(self):
        ship = self.lo_ship_selector.get()
        if ship and messagebox.askyesno("DRAKE OS", f"PURGE ALL MODULES FROM {ship}?"):
            self.controller.query("DELETE FROM ship_loadout WHERE ship_name = ?", (ship.upper(),))
            self.refresh_loadout_view(ship)

    def run_component_scan(self):
        """Liste hiérarchique des composants en DB."""
        self.comp_list_terminal.delete("0.0", "end")
        rows = self.controller.query("SELECT name, brand, type_name, category, size, grade FROM components ORDER BY category, name")
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
        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"DRAKE SYSTEMS - DATABASE OVERRIDE: {ship_name}")
        edit_win.geometry("800x700")
        edit_win.after(10, edit_win.lift)
        edit_win.configure(fg_color=DrakeConfig.BG_PANEL)

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
            entry = ctk.CTkEntry(parent, fg_color=DrakeConfig.BG_PANEL, border_color="#333333")
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
                
                messagebox.showinfo("DRAKE OS", "CORE DATABASE SYNCHRONIZED.")
                edit_win.destroy()
                self.run_ship_scan() # Refresh le terminal
                
            except ValueError as e:
                messagebox.showerror("DATA ERROR", f"Invalid format in numeric field: {e}")

        save_btn = DrakeButton(edit_win, text="APPLY ALL MODIFICATIONS", 
                               command=perform_full_update)
        save_btn.pack(pady=20, padx=40, fill="x")

    def refresh_loadout_view(self, ship_name):
        """Affiche les slots du vaisseau sous forme de cartes techniques."""
        # 1. Nettoyage
        for widget in self.lo_slots_frame.winfo_children():
            widget.destroy()

        # 2. Chargement des données
        ship = self.controller.ship.load_full_ship(ship_name)
        if not ship: return

        # Filtrage par catégorie (si lo_filter_cat est sur "WEAPON" par ex)
        filter_val = self.lo_filter_cat.get()

        for cat, specs in ship.capabilities.items():
            if filter_val != "ALL" and filter_val != cat:
                continue

            # Header de section (ex: --- WEAPONS ---)
            section_label = ctk.CTkLabel(self.lo_slots_frame, text=f" {cat} SYSTEMS ", 
                                         font=("Orbitron", 12, "bold"), text_color=DrakeConfig.ACCENT_PRIMARY)
            section_label.pack(fill="x", pady=(10, 5))

            for i in range(specs['max_qty']):
                # Création de la Carte de Slot
                slot_card = ctk.CTkFrame(self.lo_slots_frame, fg_color="#121212", border_width=1, border_color="#222222")
                slot_card.pack(fill="x", padx=10, pady=3)

                # Icône et Nom du Slot
                icon = "⚔" if cat == "WEAPON" else "🛡" if cat == "SYSTEMS" else "🚀"
                ctk.CTkLabel(slot_card, text=f"{icon} SLOT {i+1:02d}", width=100,
                             font=("Orbitron", 10), text_color="#666666").pack(side="left", padx=10)

                # Récupération des données du slot via le contrôleur
                available, current = self.controller.ship.get_slot_data(ship.name, cat, specs['max_size'], i)

                # Menu déroulant de l'équipement
                combo = DrakeComboBox(slot_card, values=["EMPTY"] + available, width=250)
                combo.set(current)
                combo.pack(side="right", padx=10, pady=5)

                # Commande de montage automatique
                combo.configure(command=lambda val, c=cat, idx=i: self.action_mount(c, idx, val))

        # Update du status
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=f"HULL: {ship_name}\nSTATUS: SCANNED\nSLOTS: OK")
    def save_slot_config(self, ship_name, category, slot_index, combo_widget):
        """Action du bouton SET : Enregistre la config via le contrôleur."""
        selection = combo_widget.get()
        if self.controller.ship.mount_component(ship_name, category, slot_index, selection):
            if hasattr(self.controller.app, "log"):
                self.controller.app.log(f"LOADOUT SYNC: {ship_name} -> {selection} (Slot {slot_index})")
        else:
            messagebox.showerror("DRAKE OS ERROR", "Failed to sync with ship database.")
        
    def get_compatible_components(self, category, max_size):
        """Récupère les composants qui matchent la catégorie et la taille."""
        # Attention à la casse : "PROPULSION" vs "Propulsion"
        query = "SELECT name FROM components WHERE UPPER(category) = UPPER(?) AND size <= ?"
        rows = self.db.query(query, (category, max_size))
        return [r[0] for r in rows]
    
    def action_mount(self, category, slot_index, component_name):
        ship_name = self.lo_ship_selector.get()
        success = self.controller.ship.mount_component(ship_name, category, slot_index, component_name)
        
        if success:
            self.status_label.configure(text=f"LOADOUT UPDATED\n{component_name}\nINSTALLED ON SLOT {slot_index+1}")
        else:
            messagebox.showerror("DRAKE ERROR", "Installation failed. Check component compatibility.")