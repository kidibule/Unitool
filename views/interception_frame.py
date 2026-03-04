import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeComboBox, DrakeButton, DrakeClearButton

class InterceptionFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.selected_sources = [] 
        self.setup_ui()

    def setup_ui(self):
        # --- TITRE AVEC LIGNE SÉPARATRICE ORANGE ---
        # L'argument with_line=True active la barre de la charte graphique
        DrakeConfig.create_title(self, "QUANTUM INTERCEPTION SYSTEM")

        # --- SECTION SÉLECTION DES SOURCES ---
        ctk.CTkLabel(self, text="START POINTS (SOURCES)", font=DrakeConfig.FONT_UI).pack(padx=50, anchor="w")
        
        f_sources = ctk.CTkFrame(self, fg_color="transparent")
        f_sources.pack(pady=5, padx=50, fill="x")

        # Chargement initial des noms depuis la DB
        location_list = self.get_location_names()
        
        self.source_selector = DrakeComboBox(f_sources, values=location_list)
        self.source_selector.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Bouton Ajouter (Style Drake)
        btn_add = DrakeButton(f_sources, text="ADD", width=60, height=30,
                               command=self.add_source_to_list)
        btn_add.pack(side="left", padx=2)

        # Bouton Reset (Style Alerte/Erreur)
        self.btn_clear = DrakeClearButton(f_sources,
                         command=self.clear_sources)
        self.btn_clear.pack(side="left", padx=2)

        # --- COMPTEUR DE SÉLECTION ---
        self.sources_count_label = ctk.CTkLabel(self, text="SOURCES ADDED: 0", 
                                                font=DrakeConfig.FONT_LOGS, 
                                                text_color=DrakeConfig.TEXT_SECONDARY)
        self.sources_count_label.pack(padx=50, anchor="w")

        # --- SECTION DESTINATION ---
        ctk.CTkLabel(self, text="DESTINATION (TARGET POINT)", font=DrakeConfig.FONT_UI).pack(padx=50, anchor="w", pady=(15,0))
        self.dest_selector = DrakeComboBox(self, values=location_list)
        self.dest_selector.pack(pady=5, padx=50, fill="x")

        # --- CONSOLE DE SORTIE (TERMINAL NOIR) ---
        self.output = ctk.CTkTextbox(self, font=DrakeConfig.FONT_LOGS, 
                                     fg_color=DrakeConfig.BG_TERMINAL,
                                     border_color=DrakeConfig.BORDER_COLOR, 
                                     border_width=1, text_color=DrakeConfig.ACCENT_PRIMARY)
        self.output.pack(pady=10, padx=50, fill="both", expand=True)

        # --- BOUTON DE GÉNÉRATION FINAL ---
        self.btn_calc = DrakeButton(self, text="GENERATE SNARE COORDINATES", 
                                   command=self.run_calculation,
                                   height=45)
        self.btn_calc.pack(pady=(10, 20), padx=50, fill="x")

    # ==========================================
    # LOGIQUE DE DONNÉES
    # ==========================================

    def get_location_names(self):
        """Récupère proprement les noms pour les menus."""
        try:
            names = self.controller.interception.get_location_names()
            return names if names else ["NO DATA"]
        except:
            return ["NO DATA"]

    def refresh_locations(self):
        """Force la mise à jour des ComboBox (à appeler après un seed)."""
        new_list = self.get_location_names()
        self.source_selector.configure(values=new_list)
        self.dest_selector.configure(values=new_list)
        self.output.insert("end", ">>> Database refreshed: Selectors updated.\n")

    def add_source_to_list(self):
        selected = self.source_selector.get()
        if selected and selected != "NO DATA":
            if selected not in self.selected_sources:
                self.selected_sources.append(selected)
                self.update_count_label()
                self.output.insert("end", f"[+] Source added: {selected}\n")
                self.controller.log(f"Source added: {selected}", source="INTERCEPTION")
            else:
                self.output.insert("end", f"[!] {selected} already in list.\n")
                self.controller.log(f"{selected} already in list.", source="INTERCEPTION")

    def clear_sources(self):
        self.selected_sources = []
        self.update_count_label()
        self.output.delete("1.0", "end")
        self.output.insert("end", ">>> Selection cleared. Ready for new input.\n")

    def update_count_label(self):
        txt = f"SOURCES ADDED: {len(self.selected_sources)}"
        if self.selected_sources:
            txt += f" ({', '.join(self.selected_sources)})"
        self.sources_count_label.configure(text=txt)

    def run_calculation(self):
        if not self.selected_sources:
            self.output.insert("end", "[ERROR] No source points selected.\n")
            return
        
        dest = self.dest_selector.get()
        self.output.insert("end", f">>> Analyzing lanes toward {dest}...\n")
        
        # On récupère la distance au lieu des coordonnées
        distance_km = self.controller.interception.calculate_snare_distance(self.selected_sources, dest)
        
        if distance_km is not None:
            self.output.insert("end", "\n" + "="*35 + "\n")
            self.output.insert("end", "      SNARE DEPLOYMENT DATA\n")
            self.output.insert("end", "="*35 + "\n")
            self.output.insert("end", f" TARGET: {dest}\n")
            self.output.insert("end", f" OPTIMAL DISTANCE: {distance_km:,.0f} KM\n")
            self.output.insert("end", f" STATUS: POSITION READY\n")
            self.output.insert("end", "="*35 + "\n")
            self.output.insert("end", f"\n>>> INSTRUCTIONS: Fly toward your sources\n")
            self.output.insert("end", f"    until you are at {distance_km:,.0f} KM\n")
            self.output.insert("end", f"    from {dest}.\n")
            self.output.see("end")
        else:
            self.output.insert("end", "[ERROR] Calculation failed.\n")
            self.controller.log("Interception calculation failed.", source="INTERCEPTION")