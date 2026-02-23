import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeTerminal, DrakeButton

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
        # Splitter l'onglet en deux : Recherche à gauche, Ajout à droite
        self.comp_container = ctk.CTkFrame(self.tab_brands, fg_color="transparent")
        self.comp_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Liste des composants existants
        self.comp_list_terminal = DrakeTerminal(self.comp_container)
        self.comp_list_terminal.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Formulaire d'ajout rapide (Drake Style)
        self.add_comp_frame = ctk.CTkFrame(self.comp_container, width=250, fg_color=DrakeConfig.BG_TERMINAL)
        self.add_comp_frame.pack(side="right", fill="y")
        
        ctk.CTkLabel(self.add_comp_frame, text="ADD COMPONENT", font=("Orbitron", 12)).pack(pady=10)
        
        self.new_comp_name = ctk.CTkEntry(self.add_comp_frame, placeholder_text="NAME (ex: FR-66)")
        self.new_comp_name.pack(pady=5, padx=10)
        
        self.new_comp_type = ctk.CTkComboBox(self.add_comp_frame, values=["SHIELD", "POWER_PLANT", "QUANTUM_DRIVE", "COOLER"])
        self.new_comp_type.pack(pady=5, padx=10)

        DrakeButton(self.add_comp_frame, text="SAVE TO DB", command=self.save_new_component).pack(pady=20)

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
        self.lo_ship_selector = ctk.CTkComboBox(left_panel, values=ship_list, command=self.refresh_loadout_view)
        self.lo_ship_selector.pack(pady=5, padx=10)

        ctk.CTkLabel(left_panel, text="EQUIP COMPONENT", font=("Orbitron", 12)).pack(pady=(20, 10))
        # Liste des composants (Dropdown)
        comp_list = [row[0] for row in self.controller.query("SELECT name FROM components")]
        self.lo_comp_selector = ctk.CTkComboBox(left_panel, values=comp_list)
        self.lo_comp_selector.pack(pady=5, padx=10)

        DrakeButton(left_panel, text="INSTALL MODULE", command=self.action_equip).pack(pady=20)

        # --- PANNEAU DROIT : RENDU TERMINAL ---
        self.lo_terminal = DrakeTerminal(self.lo_container)
        self.lo_terminal.pack(side="right", fill="both", expand=True)

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
        """Récupère les données du formulaire et demande au contrôleur de sauvegarder."""
        name = self.new_comp_name.get().strip().upper()
        comp_type = self.new_comp_type.get()
        
        if not name:
            # Tu peux ajouter un message d'erreur ici si tu as une console de log
            print("[ERROR] Le nom du composant est requis.")
            return

        # On prépare les données (tu peux ajouter brand, size, etc. si tu as les champs)
        data = {
            "name": name,
            "type_name": comp_type,
            "brand": "UNKNOWN", # Valeur par défaut ou champ à ajouter
            "size": 1,
            "grade": "C"
        }

        try:
            # On passe par le contrôleur dédié aux composants
            # Note: Assure-toi que ton controller possède une méthode add_component
            self.controller.ship.add_component_to_db(data)
            
            # Reset du champ et feedback
            self.new_comp_name.delete(0, "end")
            print(f"[SUCCESS] {name} ajouté à la base de données.")
            
            # Optionnel : rafraîchir la liste des composants
            # self.run_component_scan() 
            
        except Exception as e:
            print(f"[ERROR] Impossible de sauvegarder : {e}")
        
    def refresh_loadout_view(self, ship_name):
        """Affiche le loadout actuel du vaisseau sélectionné."""
        self.lo_terminal.delete("0.0", "end")
        ship = self.controller.ship.load_full_ship(ship_name)
        
        if not ship: return

        self.lo_terminal.insert("end", f"--- LOADOUT STATUS: {ship.name} ---\n", "ACCENT")
        self.lo_terminal.insert("end", f"BRAND: {ship.brand} | SIZE: {ship.size}\n")
        self.lo_terminal.insert("end", "-"*40 + "\n")

        if not ship.components:
            self.lo_terminal.insert("end", "\n[!] NO MODULES INSTALLED\n", "warning_label")
        else:
            for comp in ship.components:
                self.lo_terminal.insert("end", f"» [{comp.type_name}] {comp.name} - GRADE {comp.grade}\n")

    def action_equip(self):
        """Envoie l'ordre d'équipement au contrôleur."""
        ship_name = self.lo_ship_selector.get()
        comp_name = self.lo_comp_selector.get()
        
        if self.controller.ship.equip_component(ship_name, comp_name):
            self.refresh_loadout_view(ship_name) # Rafraîchir l'affichage
            # Feedback visuel
            self.lo_terminal.insert("end", f"\n[SUCCESS] {comp_name} INSTALLED.", "ACCENT")