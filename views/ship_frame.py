from tkinter import messagebox

import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeTerminal, DrakeButton, DrakeComboBox

class ShipFrame(ctk.CTkFrame):
    """Interface de gestion de la flotte (Ships & Brands)."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- HEADER (Identique au ScannerFrame) ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)

        # Titre stylisé Orbitron
        self.title_label = ctk.CTkLabel(
            header, text="FLEET DATABASE", 
            font=("Orbitron", 16, "bold"), 
            text_color="#ff8c00"
        )
        self.title_label.pack(side="left", expand=True, padx=(100, 0))

        # --- TABVIEW (Identique au ScannerFrame) ---
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color=DrakeConfig.BG_PANEL, 
            segmented_button_selected_color=DrakeConfig.ACCENT_PRIMARY,
            segmented_button_selected_hover_color="#e67e22",
            text_color="white"
        )
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        # Création des onglets
        self.tab_ships = self.tabview.add("SHIPS")  # Liste des vaisseaux avec moteur de recherche et fiches techniques
        self.tab_brands = self.tabview.add("COMPONENTS")  # À implémenter : Liste des fabricants et composants (moteurs, armes, etc.)
        self.tab_loadout = self.tabview.add("LOADOUT")  # À implémenter : Interface d'équipement des composants sur un vaisseau

        # Configuration des onglets
        self.setup_ships_tab()
        self.setup_components_tab()
        self.setup_loadout_tab()

    def setup_ships_tab(self):
        """Configure l'onglet de recherche de vaisseaux (Ships)."""
        # Barre de recherche existante
        self.ship_search_entry = ctk.CTkEntry(
            self.tab_ships, placeholder_text="RECHERCHER UN VAISSEAU (NOM OU RÔLE)...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.ship_search_entry.pack(pady=(10, 5), padx=20, fill="x")
        self.ship_search_entry.bind("<KeyRelease>", self.run_ship_scan)

        # --- NOUVELLE BARRE D'OUTILS (IMPORT/EXPORT) ---
        toolbar = ctk.CTkFrame(self.tab_ships, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        # Bouton Import
        self.btn_import = DrakeButton(
            toolbar, text="IMPORT CSV", 
            command=self.controller.ship.import_ships_from_csv,
            width=150
        )
        self.btn_import.pack(side="left", padx=5)

        # Bouton Export
        self.btn_export = DrakeButton(
            toolbar, text="EXPORT CSV", 
            command=self.controller.ship.export_ships_to_csv,
            width=150
        )
        self.btn_export.pack(side="left", padx=5)

        # Terminal de résultats existant
        self.ship_results = DrakeTerminal(self.tab_ships)
        self.ship_results.pack(pady=5, padx=10, fill="both", expand=True)
    
    def setup_components_tab(self):
        """Configure l'onglet de gestion des composants."""

        self.mapping_types = {
            "SYSTEMS": ["Shield Generator", "Power Plant", "Cooler"],
            "WEAPON": ["Laser Repeater", "Laser Cannon", "Ballistic Repeater", "Ballistic Cannon", "Distortion Repeater"],
            "PROPULSION": ["Quantum Drive", "Hydrogen Thruster"],
            "MODULE": ["Mining Laser", "Salvage Beam", "Tractor Beam"]
        }

        self.comp_container = ctk.CTkFrame(self.tab_brands, fg_color="transparent")
        self.comp_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Liste à gauche
        self.comp_list_terminal = DrakeTerminal(self.comp_container)
        self.comp_list_terminal.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Formulaire à droite
        self.add_comp_frame = ctk.CTkFrame(self.comp_container, width=280, fg_color=DrakeConfig.BG_TERMINAL)
        self.add_comp_frame.pack(side="right", fill="y")
        
        ctk.CTkLabel(self.add_comp_frame, text="ADD COMPONENT", font=("Orbitron", 14, "bold"), text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=15)

        # --- FORMULAIRE D'AJOUT ---
        # Catégorie (Le Slot Physique)
        ctk.CTkLabel(self.add_comp_frame, text="SLOT CATEGORY", font=("Orbitron", 10)).pack(pady=(10, 0))
        self.new_comp_category = ctk.CTkComboBox(self.add_comp_frame, 
            values=["SYSTEMS", "WEAPON", "PROPULSION", "MODULE"], command=self.on_category_change)
        self.new_comp_category.pack(pady=5, padx=15, fill="x")

        # Type (Le type de module précis)
        ctk.CTkLabel(self.add_comp_frame, text="MODULE TYPE", font=("Orbitron", 10)).pack(pady=(10, 0))
        self.new_comp_type = ctk.CTkComboBox(self.add_comp_frame, 
            values=["Shield Generator", "Power Plant", "Cooler", "Quantum Drive", "Laser Repeater", "Ballistic Cannon", "Missile Rack"])
        self.new_comp_type.pack(pady=5, padx=15, fill="x")

        self.new_comp_category.set("SYSTEMS")
        self.on_category_change("SYSTEMS")
        
        # Nom et Marque
        self.new_comp_name = ctk.CTkEntry(self.add_comp_frame, placeholder_text="MODEL NAME (ex: FR-66)")
        self.new_comp_name.pack(pady=5, padx=15, fill="x")
        
        self.new_comp_brand = ctk.CTkEntry(self.add_comp_frame, placeholder_text="MANUFACTURER (ex: AEGIS)")
        self.new_comp_brand.pack(pady=5, padx=15, fill="x")

        # Taille
        ctk.CTkLabel(self.add_comp_frame, text="SIZE", font=("Orbitron", 10)).pack(pady=(10, 0))
        self.new_comp_size = ctk.CTkComboBox(self.add_comp_frame, values=["0", "1", "2", "3", "4", "5"])
        self.new_comp_size.pack(pady=5, padx=15, fill="x")

        # Grade (Optionnel pour le look)
        self.new_comp_grade = ctk.CTkComboBox(self.add_comp_frame, values=["A", "B", "C", "D"])
        self.new_comp_grade.set("C")
        self.new_comp_grade.pack(pady=5, padx=15, fill="x")

        DrakeButton(self.add_comp_frame, text="SAVE TO DATABASE", command=self.save_new_component).pack(pady=30, padx=15, fill="x")

    # Nouvelle méthode dans ShipFrame
    def setup_loadout_tab(self):
        """Interface pour équiper les composants sur un vaisseau."""
        # Splitter l'écran : Gauche (Sélection) | Droite (Visualisation)
        self.lo_container = ctk.CTkFrame(self.tab_loadout, fg_color="transparent")
        self.lo_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- PANNEAU GAUCHE : SÉLECTION ---
        left_panel = ctk.CTkFrame(self.lo_container, fg_color=DrakeConfig.BG_TERMINAL, width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left_panel, text="SELECT SHIP", font=("Orbitron", 12)).pack(pady=10)
        # Liste des vaisseaux (Dropdown)
        ship_list = [row[0] for row in self.controller.query("SELECT name FROM ships")]
        self.lo_ship_selector = DrakeComboBox(left_panel, values=ship_list, command=self.refresh_loadout_view)
        self.lo_ship_selector.pack(pady=5, padx=10)

        ctk.CTkLabel(left_panel, text="EQUIP COMPONENT", font=("Orbitron", 12)).pack(pady=(20, 10))
        # Liste des composants (Dropdown)
        comp_list = [row[0] for row in self.controller.query("SELECT name FROM components")]
        self.lo_comp_selector = DrakeComboBox(left_panel, values=comp_list)
        self.lo_comp_selector.pack(pady=5, padx=10)

        DrakeButton(left_panel, text="INSTALL MODULE", command=self.action_equip).pack(pady=20)

        DrakeButton(left_panel, text="REFRESH LISTS", 
                    command=self.update_selectors, 
                    width=100).pack(pady=5)

        # --- PANNEAU DROIT : RENDU TERMINAL ---
        self.lo_terminal = DrakeTerminal(self.lo_container)
        self.lo_terminal.pack(side="right", fill="both", expand=True)

                
                # --- [RENDU DES COMPOSANTS ÉQUIPÉS] ---
    def run_ship_scan(self, event):
        """Moteur de rendu des fiches techniques."""
        q = self.ship_search_entry.get().strip().upper()
        self.ship_results.delete("0.0", "end")

        if len(q) > 1:
            # Utilisation directe de self.controller.query (délégué à Database)
            sql = "SELECT name FROM ships WHERE name LIKE ? OR brand LIKE ? LIMIT 10"
            rows = self.controller.query(sql, (f"%{q}%", f"%{q}%"))

            for row in rows:
                ship_name = row[0]
                ship = self.controller.ship.load_ship_as_model(ship_name)
                
                if not ship: continue

                tag_ship_click = f"edit_ship_{ship.name.replace(' ', '_')}"

                # --- [RENDU FORMAT DOSSIER] ---
                self.ship_results.insert("end", " ■ ", "ACCENT") 
                self.ship_results.insert("end", f"{ship.brand.upper()} {ship.name.upper()} ", (tag_ship_click, "NEUTRE"))
                self.ship_results.insert("end", f"[{ship.size.upper()}]\n", "info_label")
                
                self.ship_results.insert("end", f"   ROLE: {ship.role} | CAREER: {ship.career}\n")
                self.ship_results.insert("end", f"   CREW: {ship.crew_size} | CARGO: {ship.cargo} SCU | HP: {ship.hp}\n")

                self.ship_results.insert("end", "   " + "-"*45 + "\n", "separator")
                
                # Stats techniques
                stats = [
                    ("SCM/NAV SPEED", f"{ship.scm_speed} / {ship.nav_max_speed} m/s"),
                    ("PITCH/YAW/ROLL", f"{ship.pitch}/{ship.yaw}/{ship.roll}"),
                    ("BOOSTED P/Y/R", f"{ship.boosted_pitch}/{ship.boosted_yaw}/{ship.boosted_roll}")
                ]
                for label, val in stats:
                    self.ship_results.insert("end", f"   {label:<25} | {val:<20}\n", "ACCENT")

                self.ship_results.insert("end", "   " + "-"*45 + "\n", "separator")
                self.ship_results.insert("end", "   CLAIM: ", "warning_label")
                self.ship_results.insert("end", f"BASE: {ship.claim_time}m | EXPEDITE: {ship.expedite_time}m\n")
                
                self.ship_results.insert("end", f"{'='*60}\n\n")

                self.ship_results.tag_bind(tag_ship_click, "<Double-Button-1>", 
                                         lambda e, n=ship.name: self.open_edit_window(n))
                
                # --- [RENDU DES COMPOSANTS ÉQUIPÉS] ---
                if ship.components:
                    self.ship_results.insert("end", " 🛰️ LOADOUT / COMPONENTS:\n", "ACCENT")
                    for comp in ship.components:
                        self.ship_results.insert("end", f"   • [{comp.type_name:<15}] {comp.brand} {comp.name} (Size {comp.size})\n")
                else:
                    self.ship_results.insert("end", "   NO COMPONENTS REGISTERED\n", "warning_label")

                self.ship_results.insert("end", f"{'='*60}\n\n")
                                         
    def open_edit_window(self, ship_name):
        # À implémenter : Fenêtre CTkTopLevel avec les champs du modèle Ship
        pass

    def save_new_component(self):
        """Récupère les données du formulaire et les enregistre."""
        # 1. Récupération des valeurs depuis les widgets
        name = self.new_comp_name.get().strip().upper()
        brand = self.new_comp_brand.get().strip().upper() or "UNKNOWN"
        # On utilise type_name pour le détail (ex: Laser Repeater) 
        # et category pour le slot (ex: WEAPON)
        category = self.new_comp_category.get().upper()
        size = int(self.new_comp_size.get())
        grade = self.new_comp_grade.get().upper()
        
        if not name:
            print("[ERROR] Le nom est requis.")
            return

        # 2. Préparation du dictionnaire DATA (Dynamique maintenant !)
        data = {
            "name": name,
            "brand": brand,
            "type_name": category, # Tu peux changer si tu as un autre champ
            "category": category,  # Crucial pour la table ship_specs
            "size": size,          # Crucial pour la validation can_add_component
            "grade": grade,
            "stats": "{}"          # JSON vide par défaut
        }

        try:
            # 3. Envoi au contrôleur
            self.controller.ship.add_component_to_db(data)
            
            # Feedback & Nettoyage
            self.new_comp_name.delete(0, "end")
            self.new_comp_brand.delete(0, "end")
            
            # On rafraîchit les sélecteurs de l'onglet Loadout pour voir le nouveau composant
            self.update_selectors()
            
            print(f"[SUCCESS] {name} enregistré : {category} S{size}")
            
        except Exception as e:
            print(f"[ERROR] Échec de sauvegarde : {e}")
        
    def refresh_loadout_view(self, ship_name):
        """Affiche le loadout actuel et les slots disponibles."""
        self.lo_terminal.delete("0.0", "end")
        ship = self.controller.ship.load_full_ship(ship_name)
        
        if not ship: return

        self.lo_terminal.insert("end", f"--- CONFIGURATION : {ship.name} ---\n", "ACCENT")
        self.lo_terminal.insert("end", f"CHASSIS: {ship.brand} | CLASS: {ship.size}\n")
        self.lo_terminal.insert("end", "="*50 + "\n\n")

        # --- AFFICHAGE DES SLOTS PAR CATÉGORIE ---
        self.lo_terminal.insert("end", " [ HARDPOINTS & SLOTS ]\n", "info_label")
        
        for cat, specs in ship.capabilities.items():
            # On compte combien on a de composants de cette catégorie
            current_count = sum(1 for c in ship.components if c.category == cat)
            
            # Couleur d'alerte si plein
            tag = "ACCENT" if current_count < specs['max_qty'] else "warning_label"
            
            status_text = f"  • {cat:<12} : {current_count}/{specs['max_qty']} slots "
            status_text += f"(Max Size: S{specs['max_size']})\n"
            
            self.lo_terminal.insert("end", status_text, tag)

        self.lo_terminal.insert("end", "\n" + "-"*50 + "\n")
        self.lo_terminal.insert("end", " [ INSTALLED MODULES ]\n", "info_label")

        if not ship.components:
            self.lo_terminal.insert("end", "\n [!] NO MODULES INSTALLED\n", "warning_label")
        else:
            for comp in ship.components:
                self.lo_terminal.insert("end", f"  » [{comp.category}] {comp.brand} {comp.name} (S{comp.size})\n")

    def action_equip(self):
        """Envoie l'ordre d'équipement au contrôleur avec gestion des erreurs."""
        ship_name = self.lo_ship_selector.get()
        comp_name = self.lo_comp_selector.get()
        
        if not ship_name or not comp_name:
            return

        # Le contrôleur va appeler ship.can_add_component()
        success = self.controller.ship.equip_component(ship_name, comp_name)
        
        # On rafraîchit la vue pour voir le changement ou l'erreur
        self.refresh_loadout_view(ship_name)
        
        if success:
            self.lo_terminal.insert("end", f"\n\n [ OK ] {comp_name} INSTALLED SUCCESSFULLY.", "ACCENT")
        else:
            # Note: Si ton equip_component affiche déjà une messagebox, 
            # ce log terminal est un bonus de style "Drake".
            self.lo_terminal.insert("end", f"\n\n [ ERROR ] INSTALLATION FAILED. CHECK SLOTS/SIZE.", "warning_label")

    def update_selectors(self):
        """Met à jour les menus déroulants avec les données de la DB."""
        ships = [row[0] for row in self.controller.query("SELECT name FROM ships")]
        comps = [row[0] for row in self.controller.query("SELECT name FROM components")]
        self.lo_ship_selector.configure(values=ships)
        self.lo_comp_selector.configure(values=comps)

    def run_component_scan(self):
        """Affiche les composants avec une hiérarchie visuelle."""
        self.comp_list_terminal.delete("0.0", "end")
        
        # 1. On récupère tous les composants triés par catégorie et type
        sql = "SELECT * FROM components ORDER BY category, type_name, name"
        rows = self.controller.query(sql)
        
        last_cat = None
        last_type = None

        for row in rows:
            # colonnes : id, name, brand, type_name, category, size, grade, stats
            comp_name, brand, comp_type, category, size, grade = row[1], row[2], row[3], row[4], row[5], row[6]

            # --- AFFICHAGE DE LA CATÉGORIE (Niveau 1) ---
            if category != last_cat:
                self.comp_list_terminal.insert("end", f"\n▼ {category}\n", "ACCENT")
                last_cat = category
                last_type = None # Reset le type quand la catégorie change

            # --- AFFICHAGE DU TYPE (Niveau 2) ---
            if comp_type != last_type:
                self.comp_list_terminal.insert("end", f"  ↳ {comp_type}\n", "info_label")
                last_type = comp_type

            # --- AFFICHAGE DU COMPOSANT (Détails) ---
            details = f"    • {brand:<12} | {comp_name:<18} | S{size} | GRADE {grade}\n"
            self.comp_list_terminal.insert("end", details)

        # Ajout d'une petite barre de défilement auto
        self.comp_list_terminal.see("end")

    def on_category_change(self, choice):
        """Met à jour la liste des types selon la catégorie sélectionnée."""
        # 1. Récupérer les nouveaux types correspondants
        new_values = self.mapping_types.get(choice, [])
        
        # 2. Configurer la ComboBox des types avec ces valeurs
        self.new_comp_type.configure(values=new_values)
        
        # 3. Sélectionner la première valeur par défaut si elle existe
        if new_values:
            self.new_comp_type.set(new_values[0])
        else:
            self.new_comp_type.set("")