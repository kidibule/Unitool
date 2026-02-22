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

        # Configuration des onglets
        self.setup_ships_tab()

    def setup_ships_tab(self):
        """Configure l'onglet de recherche de vaisseaux (Ships)."""
        self.ship_search_entry = ctk.CTkEntry(
            self.tab_ships, placeholder_text="RECHERCHER UN VAISSEAU (NOM OU RÔLE)...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.ship_search_entry.pack(pady=10, padx=20, fill="x")
        self.ship_search_entry.bind("<KeyRelease>", self.run_ship_scan)

        self.ship_results = DrakeTerminal(self.tab_ships)
        self.ship_results.pack(pady=5, padx=10, fill="both", expand=True)

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

    def open_edit_window(self, ship_name):
        # À implémenter : Fenêtre CTkTopLevel avec les champs du modèle Ship
        pass