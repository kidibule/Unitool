"""Frame d'interception quantique.

Permet de gérer les positions, sélectionner des points source/destination
et lancer le calcul de distance de déploiement snare.
"""

import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeComboBox, DrakeButton, DrakeClearButton, DrakeEntry, DrakePopup, DrakeTerminal, DrakeTitle2, DrakeTitle4

class InterceptionFrame(ctk.CTkFrame):
    """Vue UI pour le calcul et la gestion des positions d'interception."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.selected_sources = [] 
        self.setup_ui()

    def setup_ui(self):
        """Construit l'interface complète (contrôles + terminal de sortie)."""
        DrakeConfig.create_title(self, "QUANTUM INTERCEPTION SYSTEM")

        self.int_container = ctk.CTkFrame(self, fg_color=DrakeConfig.BG_PANEL)
        self.int_container.pack(fill="both", expand=True, padx=20, pady=20)

        left = ctk.CTkFrame(self.int_container, width=250, fg_color=DrakeConfig.BG_MAIN)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        right = DrakeTerminal(self.int_container)
        right.pack(side="right", fill="both", expand=True)

        DrakeTitle2(left, text="SNARE SETUP").pack(pady=15)

        location_list = self.get_location_names()

        DrakeTitle4(left, text="START POINT").pack(pady=(0, 2), padx=12)
        self.source_selector = DrakeComboBox(left, values=location_list)
        self.source_selector.pack(pady=5, padx=12, fill="x")

        source_actions = ctk.CTkFrame(left, fg_color="transparent")
        source_actions.pack(pady=(4, 6), padx=12, fill="x")
        DrakeButton(source_actions, text="ADD", width=80, command=self.add_source_to_list).pack(side="left", padx=(0, 4))
        self.btn_clear = DrakeClearButton(source_actions, command=self.clear_sources)
        self.btn_clear.pack(side="left", padx=(4, 0))

        DrakeTitle4(left, text="DESTINATION").pack(pady=(8, 2), padx=12)
        self.dest_selector = DrakeComboBox(left, values=location_list)
        self.dest_selector.pack(pady=5, padx=12, fill="x")

        DrakeTitle4(left, text="NEW POSITION").pack(pady=(10, 2), padx=12)
        self.new_pos_name = DrakeEntry(left, placeholder_text="NAME (ex: ARC-L2)")
        self.new_pos_name.pack(pady=4, padx=12, fill="x")

        self.new_pos_x = DrakeEntry(left, placeholder_text="X")
        self.new_pos_x.pack(pady=2, padx=12, fill="x")
        self.new_pos_y = DrakeEntry(left, placeholder_text="Y")
        self.new_pos_y.pack(pady=2, padx=12, fill="x")
        self.new_pos_z = DrakeEntry(left, placeholder_text="Z")
        self.new_pos_z.pack(pady=2, padx=12, fill="x")

        DrakeButton(left, text="SAVE POSITION", command=self.action_create_position).pack(pady=(6, 8), padx=12, fill="x")

        DrakeTitle4(left, text="DELETE POSITION").pack(pady=(6, 2), padx=12)
        self.del_pos_selector = DrakeComboBox(left, values=location_list)
        self.del_pos_selector.pack(pady=4, padx=12, fill="x")
        DrakeClearButton(left, text="DELETE POSITION", command=self.action_delete_position).pack(pady=(2, 8), padx=12, fill="x")

        ctk.CTkFrame(left, fg_color=DrakeConfig.BORDER_COLOR, height=1).pack(fill="x", padx=12, pady=(6, 8))

        DrakeTitle4(left, text="SELECTED SOURCES").pack(pady=(12, 2), padx=12)
        self.sources_count_label = ctk.CTkLabel(
            left,
            text="SOURCES ADDED: 0",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            justify="left",
            wraplength=220,
        )
        self.sources_count_label.pack(pady=(0, 8), padx=12, fill="x")

        self.btn_calc = DrakeButton(
            left,
            text="GENERATE SNARE COORDINATES",
            command=self.run_calculation,
            height=45,
        )
        self.btn_calc.pack(side="bottom", pady=20, padx=12, fill="x")

        self.output = right

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
        if hasattr(self, "del_pos_selector"):
            self.del_pos_selector.configure(values=new_list)
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

    def action_create_position(self):
        name = self.new_pos_name.get().strip().upper()
        x = self.new_pos_x.get().strip()
        y = self.new_pos_y.get().strip()
        z = self.new_pos_z.get().strip()

        if not name:
            DrakePopup.warning("INTERCEPTION", "Position name is required.", parent=self)
            return

        try:
            saved_name = self.controller.interception.upsert_location(name, x, y, z)
            self.refresh_locations()
            self.new_pos_name.delete(0, "end")
            self.new_pos_x.delete(0, "end")
            self.new_pos_y.delete(0, "end")
            self.new_pos_z.delete(0, "end")
            self.output.insert("end", f"[+] Position saved: {saved_name}\n")
            self.output.see("end")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Interception position saved: {saved_name}", source="INTERCEPTION")
        except Exception as e:
            DrakePopup.error("INTERCEPTION", str(e), parent=self)

    def action_delete_position(self):
        name = self.del_pos_selector.get().strip().upper() if hasattr(self, "del_pos_selector") else ""
        if not name or name == "NO DATA":
            DrakePopup.warning("INTERCEPTION", "Select a position to delete.", parent=self)
            return

        if not DrakePopup.yesno("INTERCEPTION", f"Delete position {name}?", parent=self):
            return

        try:
            deleted_name = self.controller.interception.delete_location(name)
            self.selected_sources = [s for s in self.selected_sources if s != deleted_name]
            self.update_count_label()
            self.refresh_locations()
            self.output.insert("end", f"[-] Position deleted: {deleted_name}\n")
            self.output.see("end")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Interception position deleted: {deleted_name}", source="INTERCEPTION")
        except Exception as e:
            DrakePopup.error("INTERCEPTION", str(e), parent=self)

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