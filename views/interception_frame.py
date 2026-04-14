"""Quantum interception frame.

Manages locations, source/destination selection,
and snare distance computation.
"""

import customtkinter as ctk
from datetime import datetime
from drake_ui.engine import DrakeConfig, DrakeComboBox, DrakeButton, DrakeClearButton, DrakeEntry, DrakePopup, DrakeTerminal, DrakeTitle2, DrakeTitle4

class InterceptionFrame(ctk.CTkFrame):
    """UI view for interception calculations and location management."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.position_popup = None
        self.selected_sources = [] 
        self.source_active_vars = {}
        self.source_checkboxes = []
        self.moon_checkboxes = []
        self.moon_vars = {}
        self.road_selected_name = ""
        self.road_editing_name = ""
        self.setup_ui()

    def setup_ui(self):
        """Builds a single-window interception layout (no tabs)."""
        DrakeConfig.create_title(self, "QUANTUM INTERCEPTION SYSTEM")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        location_list = self.get_location_names()

        f_add = ctk.CTkFrame(
            container,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        f_add.pack(fill="x", pady=(0, 6))
        top_row = ctk.CTkFrame(f_add, fg_color="transparent")
        top_row.pack(fill="x", padx=6, pady=(8, 4))

        self.road_name_entry = DrakeEntry(
            top_row,
            placeholder_text="Road name",
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.road_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        DrakeButton(top_row, text="SAVE", width=100, command=self.save_road_preset).pack(side="left", padx=(0, 6))
        DrakeButton(top_row, text="GENERATE", width=110, command=self.generate_road_preview).pack(side="left")

        bottom_row = ctk.CTkFrame(f_add, fg_color="transparent")
        bottom_row.pack(fill="x", padx=6, pady=(2, 10))

        self.start_selector = DrakeComboBox(bottom_row, values=location_list, width=160)
        self.start_selector.pack(side="left", padx=(0, 6))
        self.start_selector.set("START")

        DrakeButton(bottom_row, text="ADD START", width=95, command=self.add_start_source).pack(side="left", padx=(0, 6))
        DrakeClearButton(bottom_row, text="CLEAR", width=70, command=self.clear_start_sources).pack(side="left", padx=(0, 8))

        self.dest_selector = DrakeComboBox(
            bottom_row,
            values=location_list,
            width=160,
            command=self.on_destination_changed,
        )
        self.dest_selector.pack(side="left", padx=(0, 6))
        self.dest_selector.set("DESTINATION")

        self.radius_entry = DrakeEntry(
            bottom_row,
            placeholder_text="Radius",
            width=95,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.radius_entry.insert(0, "20000")
        self.radius_entry.pack(side="left", padx=(0, 6))

        self.step_entry = DrakeEntry(
            bottom_row,
            placeholder_text="Step",
            width=80,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.step_entry.insert(0, "500")
        self.step_entry.pack(side="left", padx=(0, 6))

        self.max_dist_entry = DrakeEntry(
            bottom_row,
            placeholder_text="Max",
            width=110,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.max_dist_entry.insert(0, "250000")
        self.max_dist_entry.pack(side="left")

        DrakeButton(
            container,
            text="EDIT POSITIONS",
            command=self.open_position_manager,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            width=110,
            height=22,
            font=("Segoe UI", 9, "bold"),
            corner_radius=0,
        ).pack(anchor="ne", pady=(0, 6))

        lower_sections = ctk.CTkFrame(container, fg_color="transparent")
        lower_sections.pack(fill="both", expand=True)
        lower_sections.grid_columnconfigure(0, weight=1)
        lower_sections.grid_rowconfigure(0, weight=8, minsize=260)
        lower_sections.grid_rowconfigure(1, weight=1, minsize=130)
        lower_sections.grid_rowconfigure(2, weight=1, minsize=150)

        self.road_output = DrakeTerminal(lower_sections)
        self.road_output.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        sources_section = ctk.CTkFrame(
            lower_sections,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        sources_section.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        sources_header = ctk.CTkFrame(sources_section, fg_color="transparent")
        sources_header.pack(fill="x", padx=8, pady=(6, 2))

        DrakeTitle4(sources_header, text="START SOURCES").pack(side="left", pady=0, padx=0)

        self.start_sources_label = ctk.CTkLabel(
            sources_section,
            text="START SOURCES: NONE",
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            anchor="w",
            justify="left",
        )
        self.start_sources_label.pack(fill="x", padx=8, pady=(0, 4))

        self.start_sources_frame = ctk.CTkScrollableFrame(
            sources_section,
            fg_color=DrakeConfig.BG_TERMINAL,
            height=54,
        )
        self.start_sources_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.road_list = ctk.CTkScrollableFrame(
            lower_sections,
            label_text="REGISTERED ROAD PRESETS",
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            height=150,
        )
        self.road_list.grid(row=2, column=0, sticky="nsew")

        self.output = self.road_output
        self.refresh_start_sources_display()
        self.refresh_roads()

    def setup_road_tab(self, parent_tab):
        road_container = ctk.CTkFrame(parent_tab, fg_color="transparent")
        road_container.pack(fill="both", expand=True, padx=20, pady=10)

        DrakeTitle2(road_container, text="ROAD MANAGEMENT").pack(pady=(4, 8), anchor="w")

        # Top creation/update row, inspired by Contract add-form layout.
        f_add = ctk.CTkFrame(
            road_container,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        f_add.pack(pady=(0, 8), fill="x")
        f_add.grid_columnconfigure(0, weight=1)
        f_add.grid_columnconfigure((1, 2, 3), weight=0)

        self.road_name_entry = DrakeEntry(f_add, placeholder_text="Road name")
        self.road_name_entry.grid(row=0, column=0, padx=8, pady=10, sticky="ew")

        DrakeButton(f_add, text="SAVE / UPDATE", width=130, command=self.save_road_preset).grid(row=0, column=1, padx=4, pady=10)
        DrakeButton(f_add, text="LOAD SELECTED", width=120, command=self.load_road_preset).grid(row=0, column=2, padx=4, pady=10)
        DrakeClearButton(f_add, text="DELETE SELECTED", width=130, command=self.delete_road_preset).grid(row=0, column=3, padx=(4, 8), pady=10)

        self.road_list = ctk.CTkScrollableFrame(
            road_container,
            label_text="REGISTERED ROAD PRESETS",
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.road_list.pack(pady=(0, 8), fill="both", expand=True)

        self.road_output = DrakeTerminal(road_container, height=160)
        self.road_output.pack(fill="x")

    # ==========================================
    # DATA LOGIC
    # ==========================================

    def get_location_names(self):
        """Safely fetches location names for selectors."""
        try:
            names = self.controller.interception.get_location_names()
            return names if names else ["NO DATA"]
        except:
            return ["NO DATA"]

    def refresh_locations(self):
        """Refreshes all location selectors."""
        new_list = self.get_location_names()
        if self._widget_exists("dest_selector"):
            current_dest = self.dest_selector.get().strip().upper()
            self.dest_selector.configure(values=new_list)
            if current_dest in new_list:
                self.dest_selector.set(current_dest)
            else:
                self.dest_selector.set("DESTINATION")
        if self._widget_exists("del_pos_selector"):
            self.del_pos_selector.configure(values=new_list)
        if self._widget_exists("new_pos_type"):
            self.on_location_type_change(self.new_pos_type.get())
        self.refresh_start_selector_options()
        self.refresh_roads()
        self.output.insert("end", ">>> Database refreshed: Selectors updated.\n")

    def refresh_start_selector_options(self):
        """Shows only valid remaining start positions for the selected destination."""
        if not self._widget_exists("start_selector"):
            return

        current_start = self.start_selector.get().strip().upper()
        destination = self.dest_selector.get().strip().upper() if self._widget_exists("dest_selector") else ""
        all_locations = [
            str(name).strip().upper()
            for name in self.get_location_names()
            if str(name).strip() and str(name).strip().upper() != "NO DATA"
        ]

        valid_values = []
        for candidate in all_locations:
            if candidate in self.selected_sources:
                continue
            if destination and destination not in {"NO DATA", "DESTINATION"}:
                if candidate == destination:
                    continue
                validation = self.controller.interception.validate_sources_for_destination(
                    self.selected_sources + [candidate],
                    destination,
                )
                if not validation.get("ok"):
                    continue
            valid_values.append(candidate)

        if not valid_values:
            if destination and destination not in {"NO DATA", "DESTINATION"}:
                valid_values = ["NO VALID START"]
            else:
                valid_values = all_locations or ["NO DATA"]

        self.start_selector.configure(values=valid_values)
        if current_start in valid_values:
            self.start_selector.set(current_start)
        else:
            self.start_selector.set("START")

    def get_road_names(self):
        try:
            names = self.controller.interception.get_road_names()
            return names if names else []
        except Exception:
            return []

    def refresh_roads(self):
        if not self._widget_exists("road_list"):
            return

        for widget in self.road_list.winfo_children():
            widget.destroy()

        road_names = self.get_road_names()
        if not road_names:
            ctk.CTkLabel(
                self.road_list,
                text="NO ROAD PRESET SAVED",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=12, pady=(8, 10))
            self.road_selected_name = ""
            return

        if self.road_selected_name not in road_names:
            self.road_selected_name = road_names[0]

        for road_name in road_names:
            road = self.controller.interception.get_road(road_name)
            if not road:
                continue

            selected = road_name == self.road_selected_name
            card = ctk.CTkFrame(
                self.road_list,
                fg_color=DrakeConfig.BG_PANEL,
                corner_radius=0,
                border_width=1,
                border_color=DrakeConfig.ACCENT_PRIMARY if selected else DrakeConfig.BORDER_COLOR,
            )
            card.pack(fill="x", padx=8, pady=3)

            if road_name == (self.road_editing_name or ""):
                self._render_road_edit_row(card, road)
            else:
                self._render_road_display_row(card, road_name, road)

    def _render_road_display_row(self, parent, road_name, road):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=10, pady=7)

        ctk.CTkLabel(
            left,
            text=road_name,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=(
                f"DEST {road['destination_name']} | SRC {len(road['source_names'])}"
                f" | R {road['radius']:.0f} | STEP {road['step']:.0f} | MAX {road['max_dist']:.0f}"
            ),
            font=DrakeConfig.FONT_LOGS,
            text_color=DrakeConfig.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="right", padx=10, pady=7)

        DrakeButton(
            right,
            text="EDIT",
            width=50,
            height=26,
            command=lambda n=road_name: self.start_road_edit(n),
        ).pack(side="left", padx=(0, 6))
        DrakeButton(
            right,
            text="LOAD",
            width=50,
            height=26,
            command=lambda n=road_name: self.load_road_preset(n),
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
            command=lambda n=road_name: self.delete_road_preset(n),
        ).pack(side="left")

    def _render_road_edit_row(self, parent, road):
        editor = ctk.CTkFrame(parent, fg_color="transparent")
        editor.pack(fill="x", expand=True, padx=8, pady=8)

        top = ctk.CTkFrame(editor, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))

        name_entry = DrakeEntry(top, placeholder_text="Road name")
        name_entry.pack(side="left", padx=(0, 8), expand=True, fill="x")
        name_entry.insert(0, road["name"])

        destinations = self.get_location_names()
        dest_combo = DrakeComboBox(top, values=destinations)
        dest_combo.pack(side="left", expand=True, fill="x")
        if road["destination_name"] in destinations:
            dest_combo.set(road["destination_name"])
        elif destinations:
            dest_combo.set(destinations[0])

        middle = ctk.CTkFrame(editor, fg_color="transparent")
        middle.pack(fill="x", pady=(0, 6))

        radius_entry = DrakeEntry(middle, placeholder_text="Radius")
        radius_entry.pack(side="left", padx=(0, 8), expand=True, fill="x")
        radius_entry.insert(0, f"{road['radius']:.0f}")

        step_entry = DrakeEntry(middle, placeholder_text="Step")
        step_entry.pack(side="left", padx=(0, 8), expand=True, fill="x")
        step_entry.insert(0, f"{road['step']:.0f}")

        max_entry = DrakeEntry(middle, placeholder_text="Max dist")
        max_entry.pack(side="left", expand=True, fill="x")
        max_entry.insert(0, f"{road['max_dist']:.0f}")

        source_line = DrakeEntry(editor, placeholder_text="Sources (comma-separated)")
        source_line.pack(fill="x", pady=(0, 8))
        source_line.insert(0, ", ".join(road.get("source_names", [])))

        bottom = ctk.CTkFrame(editor, fg_color="transparent")
        bottom.pack(fill="x")

        DrakeButton(
            bottom,
            text="SAVE",
            width=52,
            height=26,
            command=lambda old=road["name"]: self.save_road_row_inline(
                old,
                name_entry,
                dest_combo,
                source_line,
                radius_entry,
                step_entry,
                max_entry,
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
            command=self.cancel_road_edit,
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
            command=lambda n=road["name"]: self.delete_road_preset(n),
        ).pack(side="left")

    def start_road_edit(self, road_name):
        self.road_selected_name = (road_name or "").strip()
        self.road_editing_name = self.road_selected_name
        self.refresh_roads()

    def cancel_road_edit(self):
        self.road_editing_name = ""
        self.refresh_roads()

    def save_road_row_inline(self, old_name, name_entry, dest_combo, source_line, radius_entry, step_entry, max_entry):
        old_name = (old_name or "").strip()
        new_name = name_entry.get().strip()
        dest = dest_combo.get().strip().upper()
        raw_sources = source_line.get().strip()
        sources = [part.strip().upper() for part in raw_sources.split(",") if part.strip()]

        if not new_name:
            DrakePopup.warning("INTERCEPTION", "Road name is required.", parent=self)
            return

        try:
            radius = float(radius_entry.get().strip())
            step = float(step_entry.get().strip())
            max_dist = float(max_entry.get().strip())
        except Exception:
            DrakePopup.error("INTERCEPTION", "radius, step and max_dist must be numeric.", parent=self)
            return

        if not sources:
            DrakePopup.warning("INTERCEPTION", "At least one source point is required.", parent=self)
            return

        validation = self.controller.interception.validate_sources_for_destination(sources, dest)
        if not validation.get("ok"):
            DrakePopup.warning("INTERCEPTION", validation.get("message") or "Invalid source selection for this destination.", parent=self)
            return

        try:
            self.controller.interception.save_road(new_name, sources, dest, radius, step, max_dist)
            if new_name != old_name:
                self.controller.interception.delete_road(old_name)
            self.road_selected_name = new_name
            self.road_editing_name = ""
            self.refresh_roads()
            self.output.insert("end", f"[+] Road updated: {new_name}\n")
            self.output.see("end")
            if hasattr(self, "road_output"):
                self.road_output.insert("end", f"[+] Road updated: {new_name}\n")
                self.road_output.see("end")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Interception road updated: {new_name}", source="INTERCEPTION")
        except Exception as e:
            DrakePopup.error("INTERCEPTION", str(e), parent=self)

    def _select_road_for_edit(self, road_name):
        self.road_selected_name = (road_name or "").strip()
        if self._widget_exists("road_name_entry"):
            self.road_name_entry.delete(0, "end")
            self.road_name_entry.insert(0, self.road_selected_name)
        if self._widget_exists("snare_road_name_entry"):
            self.snare_road_name_entry.delete(0, "end")
            self.snare_road_name_entry.insert(0, self.road_selected_name)
        self.load_road_preset(road_name=self.road_selected_name)
        self.road_editing_name = ""
        self.refresh_roads()

    def _active_sources_for_save(self):
        if self.selected_sources:
            return [str(s).strip().upper() for s in self.selected_sources if str(s).strip()]

        if self._widget_exists("start_selector"):
            start = self.start_selector.get().strip().upper()
            if start and start not in {"NO DATA", "START", "NO VALID START"}:
                return [start]

        return list(self.selected_sources)

    def add_start_source(self):
        if not self._widget_exists("start_selector"):
            return
        start = self.start_selector.get().strip().upper()
        if not start or start in {"NO DATA", "START", "NO VALID START"}:
            DrakePopup.warning("INTERCEPTION", "Select a valid start location first.", parent=self)
            return

        dest = self.dest_selector.get().strip().upper() if self._widget_exists("dest_selector") else ""
        if not dest or dest in {"NO DATA", "DESTINATION"}:
            DrakePopup.warning("INTERCEPTION", "Select a destination first (cone validation).", parent=self)
            return

        preview_sources = list(self.selected_sources)
        if start not in preview_sources:
            preview_sources.append(start)

        validation = self.controller.interception.validate_sources_for_destination(preview_sources, dest)
        if not validation.get("ok"):
            DrakePopup.warning("INTERCEPTION", validation.get("message") or "This source cannot be used for interception.", parent=self)
            return

        if start not in self.selected_sources:
            self.selected_sources.append(start)
            self.output.insert("end", f"[+] Start source added: {start}\n")
            self.output.see("end")
        self.refresh_start_sources_display()

    def clear_start_sources(self):
        self.selected_sources = []
        self.refresh_start_sources_display()
        self.output.insert("end", "[~] Start sources cleared.\n")
        self.output.see("end")

    def remove_start_source(self, source_name):
        self.selected_sources = [s for s in self.selected_sources if s != source_name]
        self.refresh_start_sources_display()

    def on_destination_changed(self, selected_destination=None):
        """Silently prunes sources that are incompatible with the selected destination."""
        destination = (selected_destination or "").strip().upper()
        if destination and destination not in {"NO DATA", "DESTINATION"} and self.selected_sources:
            kept_sources = []
            changed = False
            for source in self.selected_sources:
                trial_sources = kept_sources + [source]
                validation = self.controller.interception.validate_sources_for_destination(trial_sources, destination)
                if validation.get("ok"):
                    kept_sources.append(source)
                else:
                    changed = True

            if changed:
                self.selected_sources = kept_sources
                self.refresh_start_sources_display()
                return

        self.refresh_start_selector_options()

    def refresh_start_sources_display(self):
        if self._widget_exists("start_sources_label"):
            if self.selected_sources:
                self.start_sources_label.configure(text=f"START SOURCES: {len(self.selected_sources)} selected")
            else:
                self.start_sources_label.configure(text="START SOURCES: NONE")

        if not self._widget_exists("start_sources_frame"):
            self.refresh_start_selector_options()
            return

        for child in self.start_sources_frame.winfo_children():
            child.destroy()

        if not self.selected_sources:
            ctk.CTkLabel(
                self.start_sources_frame,
                text="No start source selected.",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=8, pady=(6, 4))
            return

        for source_name in self.selected_sources:
            row = ctk.CTkFrame(self.start_sources_frame, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            row.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(row, text=source_name, font=DrakeConfig.FONT_LOGS, anchor="w").pack(side="left", padx=8, pady=4)
            DrakeClearButton(
                row,
                text="REMOVE",
                width=74,
                command=lambda n=source_name: self.remove_start_source(n),
            ).pack(side="right", padx=6, pady=3)

        self.refresh_start_selector_options()

    def generate_road_preview(self):
        sources = self._active_sources_for_save()
        if not sources:
            DrakePopup.warning("INTERCEPTION", "Select a start location first.", parent=self)
            return

        dest = self.dest_selector.get().strip().upper() if self._widget_exists("dest_selector") else ""
        if not dest or dest in {"NO DATA", "DESTINATION"}:
            DrakePopup.warning("INTERCEPTION", "Select a destination first.", parent=self)
            return

        try:
            radius = float(self.radius_entry.get().strip())
            step = float(self.step_entry.get().strip())
            max_dist = float(self.max_dist_entry.get().strip())
        except Exception:
            DrakePopup.error("INTERCEPTION", "radius, step and max_dist must be numeric.", parent=self)
            return

        self._run_road_calculation(sources, dest, radius, step, max_dist)

    def _run_road_calculation(self, sources, dest, radius, step, max_dist):
        """Runs interception calculation and renders output report."""
        src = [str(s).strip().upper() for s in (sources or []) if str(s).strip()]
        destination = (dest or "").strip().upper()

        if not src:
            DrakePopup.warning("INTERCEPTION", "No valid start source found for calculation.", parent=self)
            return
        if not destination:
            DrakePopup.warning("INTERCEPTION", "No valid destination found for calculation.", parent=self)
            return

        validation = self.controller.interception.validate_sources_for_destination(src, destination)
        if not validation.get("ok"):
            DrakePopup.warning("INTERCEPTION", validation.get("message") or "Invalid source selection for interception.", parent=self)
            return

        self.output.insert("end", "\n" + "=" * 72 + "\n")
        result = self.controller.interception.calculate_snare_solution(
            src,
            destination,
            radius=radius,
            step=step,
            max_dist=max_dist,
        )

        if result.get("ok"):
            self._render_snare_success(result, src, destination)
            self.output.see("end")
            return

        message = result.get("message") or "Calculation failed."
        self._render_snare_failure(message, src, destination, radius, step, max_dist)
        self.output.see("end")

    def _save_road_common(self, road_name):
        road_name = (road_name or "").strip()
        if not road_name:
            DrakePopup.warning("INTERCEPTION", "Road name is required.", parent=self)
            return False

        sources = self._active_sources_for_save()
        dest = self.dest_selector.get().strip().upper() if hasattr(self, "dest_selector") else ""
        if not dest or dest in {"NO DATA", "DESTINATION"}:
            DrakePopup.warning("INTERCEPTION", "Select a destination first.", parent=self)
            return False

        try:
            radius = float(self.radius_entry.get().strip())
            step = float(self.step_entry.get().strip())
            max_dist = float(self.max_dist_entry.get().strip())
        except Exception:
            DrakePopup.error("INTERCEPTION", "radius, step and max_dist must be numeric.", parent=self)
            return False

        validation = self.controller.interception.validate_sources_for_destination(sources, dest)
        if not validation.get("ok"):
            DrakePopup.warning("INTERCEPTION", validation.get("message") or "Invalid source selection for this destination.", parent=self)
            return False

        try:
            saved_name = self.controller.interception.save_road(
                road_name,
                sources,
                dest,
                radius,
                step,
                max_dist,
            )
            self.road_selected_name = saved_name
            self.road_editing_name = ""
            self.refresh_roads()

            if self._widget_exists("road_name_entry"):
                self.road_name_entry.delete(0, "end")
                self.road_name_entry.insert(0, saved_name)
            if self._widget_exists("snare_road_name_entry"):
                self.snare_road_name_entry.delete(0, "end")
                self.snare_road_name_entry.insert(0, saved_name)

            self.output.insert("end", f"[+] Road saved: {saved_name}\n")
            if hasattr(self, "road_output"):
                self.road_output.insert("end", f"[+] Road saved: {saved_name}\n")
                self.road_output.see("end")
            self.output.see("end")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Interception road saved: {saved_name}", source="INTERCEPTION")
            return True
        except Exception as e:
            DrakePopup.error("INTERCEPTION", str(e), parent=self)
            return False

    def save_road_from_snare(self):
        road_name = self.snare_road_name_entry.get().strip() if self._widget_exists("snare_road_name_entry") else ""
        self._save_road_common(road_name)

    def save_road_preset(self):
        road_name = self.road_name_entry.get().strip() if self._widget_exists("road_name_entry") else ""
        self._save_road_common(road_name)

    def load_road_preset(self, road_name=None):
        selected = (road_name or self.road_selected_name or "").strip()
        if not selected and self._widget_exists("road_name_entry"):
            selected = self.road_name_entry.get().strip()

        if not selected:
            DrakePopup.warning("INTERCEPTION", "Select a road to load.", parent=self)
            return

        road = self.controller.interception.get_road(selected)
        if not road:
            DrakePopup.error("INTERCEPTION", "Selected road was not found.", parent=self)
            self.refresh_roads()
            return

        self.road_selected_name = road["name"]
        self.road_editing_name = ""

        location_set = set(self.get_location_names())
        loaded_sources = [name for name in road["source_names"] if name in location_set]
        destination = road["destination_name"]

        if destination not in location_set:
            DrakePopup.warning(
                "INTERCEPTION",
                f"Destination '{destination}' is missing from locations.",
                parent=self,
            )

        self.selected_sources = loaded_sources
        self.refresh_start_sources_display()

        if destination in location_set:
            self.dest_selector.set(destination)
        else:
            self.dest_selector.set("DESTINATION")

        self.radius_entry.delete(0, "end")
        self.radius_entry.insert(0, f"{road['radius']:.0f}")

        self.step_entry.delete(0, "end")
        self.step_entry.insert(0, f"{road['step']:.0f}")

        self.max_dist_entry.delete(0, "end")
        self.max_dist_entry.insert(0, f"{road['max_dist']:.0f}")

        if hasattr(self, "road_name_entry"):
            self.road_name_entry.delete(0, "end")
            self.road_name_entry.insert(0, road["name"])
        if hasattr(self, "snare_road_name_entry"):
            self.snare_road_name_entry.delete(0, "end")
            self.snare_road_name_entry.insert(0, road["name"])
        first_source = road.get("source_names", [None])[0]
        if first_source and self._widget_exists("start_selector"):
            self.start_selector.set(first_source)
        elif self._widget_exists("start_selector"):
            self.start_selector.set("START")

        self.refresh_start_selector_options()

        self.output.insert("end", f"[+] Road loaded: {road['name']}\n")
        if hasattr(self, "road_output"):
            self.road_output.insert("end", f"[+] Road loaded: {road['name']}\n")
            self.road_output.see("end")
        self.output.see("end")
        if hasattr(self.controller, "log"):
            self.controller.log(f"Interception road loaded: {road['name']}", source="INTERCEPTION")
        # Loading a saved road must immediately run interception with loaded values.
        try:
            self._run_road_calculation(
                loaded_sources,
                destination,
                float(road["radius"]),
                float(road["step"]),
                float(road["max_dist"]),
            )
        except Exception as e:
            self.output.insert("end", f"[ERROR] Auto-generate failed after load: {e}\n")
            self.output.see("end")
        self.refresh_roads()

    def delete_road_preset(self, road_name=None):
        selected = (road_name or self.road_selected_name or "").strip()
        if not selected and self._widget_exists("road_name_entry"):
            selected = self.road_name_entry.get().strip()

        if not selected:
            DrakePopup.warning("INTERCEPTION", "Select a road to delete.", parent=self)
            return

        if not DrakePopup.yesno("INTERCEPTION", f"Delete road {selected}?", parent=self):
            return

        try:
            deleted_name = self.controller.interception.delete_road(selected)
            self.refresh_roads()
            self.output.insert("end", f"[-] Road deleted: {deleted_name}\n")
            if hasattr(self, "road_output"):
                self.road_output.insert("end", f"[-] Road deleted: {deleted_name}\n")
                self.road_output.see("end")
            if self.road_selected_name == deleted_name:
                self.road_selected_name = ""
            if self.road_editing_name == deleted_name:
                self.road_editing_name = ""
            self.output.see("end")
            if hasattr(self.controller, "log"):
                self.controller.log(f"Interception road deleted: {deleted_name}", source="INTERCEPTION")
        except Exception as e:
            DrakePopup.error("INTERCEPTION", str(e), parent=self)

    # Backward-compatible wrappers (legacy route naming)
    def get_route_names(self):
        return self.get_road_names()

    def refresh_routes(self):
        return self.refresh_roads()

    def save_route_from_snare(self):
        return self.save_road_from_snare()

    def save_route_preset(self):
        return self.save_road_preset()

    def load_route_preset(self, route_name=None):
        return self.load_road_preset(route_name)

    def delete_route_preset(self, route_name=None):
        return self.delete_road_preset(route_name)

    def _select_route_for_edit(self, route_name):
        return self._select_road_for_edit(route_name)

    def _widget_exists(self, attr_name):
        widget = getattr(self, attr_name, None)
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def on_source_changed(self, selected_source):
        """Shows moon checkboxes when the selected source is a planet."""
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
        """Updates parent candidates based on selected location type."""
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
        """Opens the location editor window (create/delete)."""
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

        self.output.insert("end", "\n" + "=" * 72 + "\n")

        result = self.controller.interception.calculate_snare_solution(
            active_sources,
            dest,
            radius=radius,
            step=step,
            max_dist=max_dist,
        )

        if result.get("ok"):
            self._render_snare_success(result, active_sources, dest)
            self.output.see("end")
        else:
            message = result.get("message") or "Calculation failed."
            self._render_snare_failure(message, active_sources, dest, radius, step, max_dist)
            self.output.see("end")
            self.controller.log(f"Interception calculation failed: {message}", source="INTERCEPTION")

    def _format_vector(self, point):
        values = point or [0.0, 0.0, 0.0]
        return f"X={values[0]:,.2f} | Y={values[1]:,.2f} | Z={values[2]:,.2f}"

    def _render_snare_success(self, result, sources, dest):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        distance_m = float(result.get("distance_units", 0.0))
        distance_mm = distance_m / 1_000_000.0
        radius_m = float(result.get("radius_units", 0.0))
        step_m = float(result.get("step_units", 0.0))
        max_dist_m = float(result.get("max_dist_units", distance_m))

        # Compute a practical positioning window around the optimal distance.
        window_m = max(step_m * 10.0, radius_m * 0.25)
        zone_min_m = max(0.0, distance_m - window_m)
        zone_max_m = min(max_dist_m, distance_m + window_m)

        zone_min_mm = zone_min_m / 1_000_000.0
        zone_max_mm = zone_max_m / 1_000_000.0
        point = result.get("point")
        avg_dir = result.get("avg_dir")
        limiting = result.get("limiting_source") or "NONE"

        self.output.insert("end", "SNARE INTERCEPTION REPORT\n")
        self.output.insert("end", f"Generated at   : {timestamp}\n")
        self.output.insert("end", "\n[INPUT]\n")
        self.output.insert("end", f"Start points   : {', '.join(sources)}\n")
        self.output.insert("end", f"Destination    : {dest}\n")

        self.output.insert("end", "\n[PARAMETERS]\n")
        self.output.insert("end", f"Radius         : {radius_m:,.0f} m\n")
        self.output.insert("end", f"Step           : {step_m:,.0f} m\n")
        self.output.insert("end", f"Max distance   : {max_dist_m:,.0f} m\n")
        self.output.insert("end", f"Limiting source: {limiting}\n")

        self.output.insert("end", "\n[SOLUTION]\n")
        self.output.insert("end", f"Snare point    : {self._format_vector(point)}\n")
        self.output.insert("end", f"Optimal range  : {distance_m:,.0f} m ({distance_mm:.3f} Mm)\n")
        if avg_dir is not None:
            self.output.insert("end", f"Average dir    : {self._format_vector(avg_dir)}\n")

        self.output.insert("end", "\n[INTERCEPTION WINDOW]\n")
        self.output.insert("end", "+" + "-" * 66 + "+\n")
        self.output.insert(
            "end",
            f"| WORKING ZONE : {zone_min_m:>12,.0f} m -> {zone_max_m:>12,.0f} m ({zone_min_mm:.3f} -> {zone_max_mm:.3f} Mm) |\n",
        )
        self.output.insert(
            "end",
            f"| OPTIMAL POS. : {distance_m:>12,.0f} m ({distance_mm:.3f} Mm)" + " " * 27 + "|\n",
        )
        self.output.insert(
            "end",
            f"| GUIDANCE     : Stay between {zone_min_mm:.3f} Mm and {zone_max_mm:.3f} Mm" + " " * 12 + "|\n",
        )
        self.output.insert("end", "+" + "-" * 66 + "+\n")

        self.output.insert("end", "\n[STATUS]\n")
        self.output.insert("end", "READY FOR DEPLOYMENT\n")
        self.output.insert("end", "=" * 72 + "\n")

    def _render_snare_failure(self, message, sources, dest, radius, step, max_dist):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output.insert("end", "SNARE INTERCEPTION REPORT\n")
        self.output.insert("end", f"Generated at   : {timestamp}\n")
        self.output.insert("end", "\n[INPUT]\n")
        self.output.insert("end", f"Start points   : {', '.join(sources)}\n")
        self.output.insert("end", f"Destination    : {dest}\n")
        self.output.insert("end", "\n[PARAMETERS]\n")
        self.output.insert("end", f"Radius         : {radius:,.0f} m\n")
        self.output.insert("end", f"Step           : {step:,.0f} m\n")
        self.output.insert("end", f"Max distance   : {max_dist:,.0f} m\n")
        self.output.insert("end", "\n[STATUS]\n")
        self.output.insert("end", f"ERROR: {message}\n")
        self.output.insert("end", "=" * 72 + "\n")