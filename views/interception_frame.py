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
        self.position_popup = None
        self.selected_sources = [] 
        self.source_active_vars = {}
        self.source_checkboxes = []
        self.moon_checkboxes = []
        self.moon_vars = {}
        self.setup_ui()

    def setup_ui(self):
        """Construit l'interface complète (contrôles + terminal de sortie)."""
        DrakeConfig.create_title(self, "QUANTUM INTERCEPTION SYSTEM")

        self.int_container = ctk.CTkFrame(self, fg_color="transparent")
        self.int_container.pack(fill="both", expand=True, padx=20, pady=10)

        location_list = self.get_location_names()

        self.int_tabview = DrakeConfig.create_tabview(
            self.int_container,
            segmented_button_selected_hover_color=DrakeConfig.ACCENT_HOVER,
            pack_padx=0,
            pack_pady=0,
        )

        tab_snare = self.int_tabview.add("SNARE")

        DrakeButton(
            tab_snare,
            text="EDIT POSITIONS",
            command=self.open_position_manager,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            width=90,
            height=20,
            font=("Segoe UI", 9, "bold"),
            corner_radius=0,
        ).pack(anchor="ne", padx=10, pady=(8, 2))

        snare_container = ctk.CTkFrame(tab_snare, fg_color="transparent")
        snare_container.pack(fill="both", expand=True, padx=20, pady=(4, 20))

        left = ctk.CTkFrame(snare_container, width=250, fg_color=DrakeConfig.BG_MAIN)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self.snare_controls = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.snare_controls.pack(fill="both", expand=True, padx=0, pady=(0, 6))

        right = DrakeTerminal(snare_container)
        right.pack(side="right", fill="both", expand=True)

        DrakeTitle2(self.snare_controls, text="SNARE SETUP").pack(pady=(10, 8))

        DrakeTitle4(self.snare_controls, text="START POINT").pack(pady=(0, 2), padx=12)
        self.source_selector = DrakeComboBox(self.snare_controls, values=location_list, command=self.on_source_changed)
        self.source_selector.pack(pady=5, padx=12, fill="x")

        self.source_moons_frame = ctk.CTkFrame(self.snare_controls, fg_color="transparent")

        self.source_actions = ctk.CTkFrame(self.snare_controls, fg_color="transparent")
        self.source_actions.pack(pady=(4, 6), padx=12, fill="x")
        DrakeButton(self.source_actions, text="ADD", width=80, command=self.add_source_to_list).pack(side="left", padx=(0, 4))
        self.btn_clear = DrakeClearButton(self.source_actions, command=self.clear_sources)
        self.btn_clear.pack(side="left", padx=(4, 0))

        DrakeTitle4(self.snare_controls, text="DESTINATION").pack(pady=(8, 2), padx=12)
        self.dest_selector = DrakeComboBox(self.snare_controls, values=location_list)
        self.dest_selector.pack(pady=5, padx=12, fill="x")

        DrakeTitle4(self.snare_controls, text="RADIUS (UNITS)").pack(pady=(8, 2), padx=12)
        self.radius_entry = DrakeEntry(self.snare_controls, placeholder_text="20000")
        self.radius_entry.insert(0, "20000")
        self.radius_entry.pack(pady=4, padx=12, fill="x")

        DrakeTitle4(self.snare_controls, text="STEP (UNITS)").pack(pady=(4, 2), padx=12)
        self.step_entry = DrakeEntry(self.snare_controls, placeholder_text="500")
        self.step_entry.insert(0, "500")
        self.step_entry.pack(pady=4, padx=12, fill="x")

        DrakeTitle4(self.snare_controls, text="MAX DIST (UNITS)").pack(pady=(4, 2), padx=12)
        self.max_dist_entry = DrakeEntry(self.snare_controls, placeholder_text="250000")
        self.max_dist_entry.insert(0, "250000")
        self.max_dist_entry.pack(pady=4, padx=12, fill="x")

        ctk.CTkFrame(self.snare_controls, fg_color=DrakeConfig.BORDER_COLOR, height=1).pack(fill="x", padx=12, pady=(6, 8))

        DrakeTitle4(self.snare_controls, text="SELECTED SOURCES").pack(pady=(12, 2), padx=12)
        self.sources_count_label = ctk.CTkLabel(
            self.snare_controls,
            text="SOURCES ADDED: 0",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            justify="left",
            wraplength=220,
        )
        self.sources_count_label.pack(pady=(0, 8), padx=12, fill="x")

        self.sources_check_frame = ctk.CTkScrollableFrame(
            self.snare_controls,
            fg_color=DrakeConfig.BG_TERMINAL,
            height=120,
        )
        self.sources_check_frame.pack(pady=(0, 8), padx=12, fill="x")

        self.btn_calc = DrakeButton(
            left,
            text="GENERATE SNARE SOLUTION",
            command=self.run_calculation,
            height=45,
        )
        self.btn_calc.pack(side="bottom", pady=(6, 10), padx=12, fill="x")

        self.on_source_changed(self.source_selector.get())

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
        """Force la mise à jour des ComboBox."""
        new_list = self.get_location_names()
        self.source_selector.configure(values=new_list)
        self.dest_selector.configure(values=new_list)
        if self._widget_exists("del_pos_selector"):
            self.del_pos_selector.configure(values=new_list)
        if hasattr(self, "source_selector"):
            self.on_source_changed(self.source_selector.get())
        if self._widget_exists("new_pos_type"):
            self.on_location_type_change(self.new_pos_type.get())
        self.output.insert("end", ">>> Database refreshed: Selectors updated.\n")

    def _widget_exists(self, attr_name):
        widget = getattr(self, attr_name, None)
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def on_source_changed(self, selected_source):
        """Affiche des checkboxes de lunes si la source choisie est une planète."""
        if not hasattr(self, "source_moons_frame"):
            return

        self.source_moons_frame.pack_forget()
        for child in self.source_moons_frame.winfo_children():
            child.destroy()
        self.moon_checkboxes = []
        self.moon_vars = {}

        source_name = (selected_source or "").strip().upper()
        if not source_name or source_name == "NO DATA":
            return

        try:
            source_type = self.controller.interception.get_location_type(source_name)
            if source_type != "PLANET":
                return

            moons = self.controller.interception.get_child_moons(source_name)
            if not moons:
                return

            self.source_moons_frame.pack(pady=(2, 6), padx=12, fill="x", before=self.source_actions)
            DrakeTitle4(self.source_moons_frame, text="INCLUDE CHILD MOONS").pack(pady=(0, 2), padx=0, anchor="w")
            for moon_name in moons:
                moon_var = ctk.StringVar(value="off")
                checkbox = ctk.CTkCheckBox(
                    self.source_moons_frame,
                    text=moon_name,
                    variable=moon_var,
                    onvalue="on",
                    offvalue="off",
                    text_color=DrakeConfig.TEXT_MAIN,
                    fg_color=DrakeConfig.ACCENT_PRIMARY,
                    hover_color=DrakeConfig.ACCENT_HOVER,
                    checkmark_color="#000000",
                )
                checkbox.pack(pady=2, anchor="w")
                self.moon_checkboxes.append(checkbox)
                self.moon_vars[moon_name] = moon_var
        except Exception:
            return

    def on_location_type_change(self, selected_type):
        """Met à jour les choix de parent en fonction du type sélectionné."""
        if not self._widget_exists("new_pos_parent"):
            return

        loc_type = (selected_type or "POI").strip().upper()

        try:
            if loc_type == "MOON":
                candidates = self.controller.interception.get_location_names_by_type(["PLANET"])
            elif loc_type == "PLANET":
                candidates = self.controller.interception.get_location_names()
            else:
                candidates = []
        except Exception:
            candidates = []

        values = ["NONE"] + [name for name in candidates if name != "NO DATA"]
        self.new_pos_parent.configure(values=values)
        self.new_pos_parent.set("NONE")

    def _close_position_manager(self):
        if self.position_popup is not None:
            try:
                self.position_popup.destroy()
            except Exception:
                pass
            self.position_popup = None

    def open_position_manager(self):
        """Ouvre la fenêtre d'édition des positions (create/delete)."""
        if self.position_popup is not None:
            try:
                if self.position_popup.winfo_exists():
                    self.position_popup.lift()
                    self.position_popup.focus_force()
                    return
            except Exception:
                self.position_popup = None

        self.position_popup = DrakeConfig.create_modal_window(
            parent=self,
            title="INTERCEPTION - POSITION EDITOR",
            geometry="460x560",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )
        self.position_popup.protocol("WM_DELETE_WINDOW", self._close_position_manager)

        root = ctk.CTkScrollableFrame(self.position_popup, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=10, pady=10)

        DrakeTitle2(root, text="POSITION MANAGEMENT").pack(pady=(8, 8))

        location_list = self.get_location_names()

        DrakeTitle4(root, text="NEW POSITION").pack(pady=(4, 2), padx=12)
        self.new_pos_name = DrakeEntry(root, placeholder_text="NAME (ex: ARC-L2)")
        self.new_pos_name.pack(pady=4, padx=12, fill="x")

        DrakeTitle4(root, text="LOCATION TYPE").pack(pady=(4, 2), padx=12)
        self.new_pos_type = DrakeComboBox(
            root,
            values=["STATION", "PLANET", "MOON", "LAGRANGE", "OUTPOST", "ASTEROID", "OTHER"],
            command=self.on_location_type_change,
        )
        self.new_pos_type.set("STATION")
        self.new_pos_type.pack(pady=4, padx=12, fill="x")

        DrakeTitle4(root, text="PARENT LOCATION").pack(pady=(4, 2), padx=12)
        self.new_pos_parent = DrakeComboBox(root, values=["NONE"])
        self.new_pos_parent.set("NONE")
        self.new_pos_parent.pack(pady=4, padx=12, fill="x")

        self.new_pos_x = DrakeEntry(root, placeholder_text="X")
        self.new_pos_x.pack(pady=2, padx=12, fill="x")
        self.new_pos_y = DrakeEntry(root, placeholder_text="Y")
        self.new_pos_y.pack(pady=2, padx=12, fill="x")
        self.new_pos_z = DrakeEntry(root, placeholder_text="Z")
        self.new_pos_z.pack(pady=2, padx=12, fill="x")

        DrakeButton(root, text="SAVE POSITION", command=self.action_create_position).pack(pady=(6, 8), padx=12, fill="x")

        DrakeTitle4(root, text="DELETE POSITION").pack(pady=(6, 2), padx=12)
        self.del_pos_selector = DrakeComboBox(root, values=location_list)
        self.del_pos_selector.pack(pady=4, padx=12, fill="x")
        DrakeClearButton(root, text="DELETE POSITION", command=self.action_delete_position).pack(pady=(2, 8), padx=12, fill="x")

        self.on_location_type_change(self.new_pos_type.get())

    def add_source_to_list(self):
        selected = self.source_selector.get()
        if selected and selected != "NO DATA":
            to_add = [selected]
            checked_moons = [moon for moon, var in self.moon_vars.items() if var.get() == "on"]
            to_add.extend(checked_moons)

            added_now = []
            already_present = []

            for item in to_add:
                if item not in self.selected_sources:
                    self.selected_sources.append(item)
                    added_now.append(item)
                else:
                    already_present.append(item)

            self.update_count_label()

            if added_now:
                self.output.insert("end", f"[+] Sources added: {', '.join(added_now)}\n")
                self.controller.log(f"Sources added: {', '.join(added_now)}", source="INTERCEPTION")

            if already_present:
                self.output.insert("end", f"[!] Already in list: {', '.join(already_present)}\n")
                self.controller.log(f"Already in list: {', '.join(already_present)}", source="INTERCEPTION")

    def action_create_position(self):
        name = self.new_pos_name.get().strip().upper()
        loc_type = self.new_pos_type.get().strip().upper() if hasattr(self, "new_pos_type") else "POI"
        parent_name = self.new_pos_parent.get().strip().upper() if hasattr(self, "new_pos_parent") else "NONE"
        x = self.new_pos_x.get().strip()
        y = self.new_pos_y.get().strip()
        z = self.new_pos_z.get().strip()

        if not name:
            DrakePopup.warning("INTERCEPTION", "Position name is required.", parent=self)
            return

        try:
            saved_name = self.controller.interception.upsert_location(name, x, y, z, loc_type, parent_name)
            self.refresh_locations()
            self.new_pos_name.delete(0, "end")
            self.new_pos_x.delete(0, "end")
            self.new_pos_y.delete(0, "end")
            self.new_pos_z.delete(0, "end")
            self.new_pos_type.set("POI")
            self.new_pos_parent.set("NONE")
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

    def _update_sources_summary(self):
        active_count = sum(1 for name, var in self.source_active_vars.items() if var.get() == "on")
        self.sources_count_label.configure(text=f"SOURCES ADDED: {len(self.selected_sources)} | ACTIVE: {active_count}")

    def update_count_label(self):
        previous_states = {
            name: (var.get() == "on")
            for name, var in self.source_active_vars.items()
        }

        if hasattr(self, "sources_check_frame"):
            for child in self.sources_check_frame.winfo_children():
                child.destroy()

        self.source_active_vars = {}
        self.source_checkboxes = []

        for source_name in self.selected_sources:
            var = ctk.StringVar(value="on" if previous_states.get(source_name, True) else "off")
            checkbox = ctk.CTkCheckBox(
                self.sources_check_frame,
                text=source_name,
                variable=var,
                onvalue="on",
                offvalue="off",
                text_color=DrakeConfig.TEXT_MAIN,
                fg_color=DrakeConfig.ACCENT_PRIMARY,
                hover_color=DrakeConfig.ACCENT_HOVER,
                checkmark_color="#000000",
                command=self._update_sources_summary,
            )
            checkbox.pack(anchor="w", pady=1)
            self.source_checkboxes.append(checkbox)
            self.source_active_vars[source_name] = var

        self._update_sources_summary()

    def run_calculation(self):
        active_sources = [
            source_name
            for source_name in self.selected_sources
            if self.source_active_vars.get(source_name) is not None and self.source_active_vars[source_name].get() == "on"
        ]

        if not active_sources:
            self.output.insert("end", "[ERROR] No source points selected.\n")
            return
        
        dest = self.dest_selector.get()
        start_points_label = ", ".join(active_sources)

        try:
            radius = float(self.radius_entry.get().strip())
            step = float(self.step_entry.get().strip())
            max_dist = float(self.max_dist_entry.get().strip())
            if radius <= 0 or step <= 0 or max_dist <= 0:
                raise ValueError
        except Exception:
            self.output.insert("end", "[ERROR] radius, step and max_dist must be positive numbers.\n")
            return

        self.output.insert("end", "\n" + "-" * 58 + "\n")

        result = self.controller.interception.calculate_snare_solution(
            active_sources,
            dest,
            radius=radius,
            step=step,
            max_dist=max_dist,
        )

        if result.get("ok"):
            point = result.get("point") or [0.0, 0.0, 0.0]
            point_txt = f"({point[0]:,.2f}, {point[1]:,.2f}, {point[2]:,.2f})"
            limiting = result.get("limiting_source") or "N/A"

            self.output.insert("end", "SNARE SOLUTION REPORT\n")
            self.output.insert("end", f"START POINT(S): {start_points_label}\n")
            self.output.insert("end", f"DESTINATION: {dest}\n")
            self.output.insert("end", f"SNARE POINT (X,Y,Z): {point_txt}\n")
            self.output.insert("end", f"OPTIMAL DISTANCE (KM): {result['distance_km']:,.3f}\n")
            self.output.insert(
                "end",
                "PARAMETERS: "
                f"radius={result['radius_units']:,.0f}u ({result['radius_km']:,.3f} km), "
                f"step={result['step_units']:,.0f}u, "
                f"max_dist={result['max_dist_units']:,.0f}u, "
                f"unit={self.controller.interception.COORD_UNIT}\n",
            )
            self.output.insert("end", f"LIMITING SOURCE: {limiting}\n")
            self.output.insert("end", "STATUS: READY\n")
            self.output.see("end")
        else:
            message = result.get("message") or "Calculation failed."
            self.output.insert("end", f"[ERROR] {message}\n")
            self.controller.log(f"Interception calculation failed: {message}", source="INTERCEPTION")