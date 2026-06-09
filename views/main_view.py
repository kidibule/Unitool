"""Vue principale de l'application — compose les différentes frames.

Contient la sidebar, le container central et le panneau intel droit.
"""

import customtkinter as ctk
from importlib import import_module
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeEntry
from datetime import datetime



class MainView(ctk.CTkFrame):
    """Container principal qui orchestre les sous-frames.

    Args:
        parent: widget parent (généralement la fenêtre principale)
        controller: référence au controller / application pour accès DB et méthodes
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=DrakeConfig.BG_MAIN)
        self.controller = controller
        self._layout_mode = None
        self._compact_breakpoint = 1200
        # Register this view as a log receiver on the controller (uses callback API)
        try:
            if self.controller is not None:
                # Backwards-compat: keep direct reference
                try:
                    self.controller.view = self
                except Exception:
                    pass
                # Preferred: register the log callback
                if hasattr(self.controller, "register_log_callback"):
                    self.controller.register_log_callback(self.log_message)
                if hasattr(self.controller, "register_stats_callback"):
                    self.controller.register_stats_callback(self.request_intel_refresh)
        except Exception:
            pass

        # Configuration responsive de la grille (Sidebar | Container | Intel Panel)
        # Use weights so columns resize proportionally: sidebar 1, container 4, intel 1
        # This yields center column ~= 2/3 of available width (1:4:1 ratio)
        self.grid_columnconfigure(0, weight=1, minsize=120)
        self.grid_columnconfigure(1, weight=4, minsize=280)
        self.grid_columnconfigure(2, weight=1, minsize=120)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # --- SIDEBAR (Navigation Drake) ---
        # Sidebar will size dynamically according to grid weights
        self.sidebar = ctk.CTkFrame(self, corner_radius=0, fg_color=DrakeConfig.BG_PANEL)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Logo/Titre
        ctk.CTkLabel(
            self.sidebar,
            text="Unitool",
            font=("Orbitron", 28, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(30, 0))
        ctk.CTkLabel(
            self.sidebar,
            text="TACTICAL SYSTEMS",
            font=("Orbitron", 10),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(pady=(0, 30))

        menu_items = [
            ("ScannerFrame", "DATABASE"),
            ("ContractFrame", "CONTRACTS"),
            ("LoggerFrame", "ARCHIVE"),
            ("IntelligenceFrame", "INTEL"),
            ("InterceptionFrame", "INTERCEPTION"),
            ("ShipFrame", "SHIP LOADOUT"),
            ("MiningFrame", "MINING"),
            ("OrgFrame", "ORGANISATIONS"),
        ]

        # Remplacement par des boutons typés Drake
        for name, label in menu_items:
            btn = DrakeButton(
                self.sidebar,
                text=label,
                command=lambda n=name: self.show_page(n),
                fg_color="transparent",
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
                hover_color=DrakeConfig.ACCENT_HOVER,
                text_color=DrakeConfig.TEXT_MAIN,
                font=DrakeConfig.FONT_UI,
                corner_radius=0,
                height=45,
            )
            btn.pack(pady=4, padx=15, fill="x")

        # --- ZONE CENTRALE (Le "Deck") ---
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Lazy loading: chaque page est créée à la demande lors du premier affichage.
        self.frames = {}
        self.page_specs = {
            "ScannerFrame": {"module": "views.scanner_frame", "class": "ScannerFrame", "kwargs": {}},
            "ContractFrame": {"module": "views.contract_frame", "class": "ContractFrame", "kwargs": {}},
            "LoggerFrame": {"module": "views.logger_frame", "class": "LoggerFrame", "kwargs": {}},
            "IntelligenceFrame": {"module": "views.intelligence_frame", "class": "IntelligenceFrame", "kwargs": {}},
            "InterceptionFrame": {"module": "views.interception_frame", "class": "InterceptionFrame", "kwargs": {}},
            "ShipFrame": {"module": "views.ship_frame", "class": "ShipFrame", "kwargs": {"mode": "loadout_only"}},
            "MiningFrame": {"module": "views.mining_frame", "class": "MiningFrame", "kwargs": {}},
            "OrgFrame": {"module": "views.org_frame", "class": "OrgFrame", "kwargs": {}},
        }

        # --- BATTLE INTEL PANEL (HUD DROITE) ---
        # Intel panel will size dynamically according to grid weights
        self.intel_panel = ctk.CTkFrame(self, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
        self.intel_panel.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)

        # Séparateur visuel gauche
        line = ctk.CTkFrame(
            self.intel_panel, width=2, fg_color=DrakeConfig.BORDER_COLOR
        )
        line.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.intel_panel,
            text="BATTLE INTEL",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=20)

        # Widgets de statistiques
        self.stat_targets = self.create_stat_widget("KNOWN CONTACTS", "0")
        self.stat_orgs = self.create_stat_widget("KNOWN ORGANIZATIONS", "0")
        self.stat_active_contracts = self.create_stat_widget("ACTIVE CONTRACTS", "0")
        

        # --- CENTRAL LOG TERMINAL (HUD DROITE) ---
        ctk.CTkLabel(
            self.intel_panel,
            text="SYSTEM LOGS",
            font=("Orbitron", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(pady=(20, 5), padx=20, anchor="center")

        # Initialisation du terminal global
        from drake_ui.engine import DrakeTerminal  # Assure-toi de l'import

        # Let the terminal expand to fill the intel panel
        self.terminal = DrakeTerminal(self.intel_panel, height=360, fg_color=DrakeConfig.BG_TERMINAL)
        self.terminal.pack(padx=8, pady=6, fill="both", expand=True)
        self.terminal.log("SYSTEM BOOT: OK")
        self.terminal.log("UPLINK: ESTABLISHED")

        # Petit pied de page version logicielle
        ctk.CTkLabel(
            self.intel_panel,
            text="VER ALPHA 1.0.0 - OPS STATUS: NOMINAL",
            font=("Consolas", 9),
            text_color="#444",
        ).pack(side="bottom", pady=10)

        self.show_page("ScannerFrame")

        # Responsive: réorganise la grille quand la fenêtre devient étroite.
        self.bind("<Configure>", self._on_resize, add="+")
        self.after(50, self._apply_responsive_layout)

    def _on_resize(self, _event=None):
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        width = self.winfo_width()
        if width <= 1:
            return

        compact = width < self._compact_breakpoint
        new_mode = "compact" if compact else "wide"
        if new_mode == self._layout_mode:
            return

        self._layout_mode = new_mode

        if new_mode == "compact":
            # Mode compact: panneau intel en bas pour préserver la zone centrale.
            self.grid_columnconfigure(0, weight=1, minsize=110)
            self.grid_columnconfigure(1, weight=5, minsize=260)
            self.grid_columnconfigure(2, weight=0, minsize=0)
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1, minsize=180)

            self.sidebar.grid_configure(row=0, column=0, sticky="nsew")
            self.container.grid_configure(row=0, column=1, columnspan=2, sticky="nsew", padx=8, pady=8)
            self.intel_panel.grid_configure(row=1, column=0, columnspan=3, sticky="nsew", padx=0, pady=0)
        else:
            # Mode large: disposition classique en 3 colonnes.
            self.grid_columnconfigure(0, weight=1, minsize=120)
            self.grid_columnconfigure(1, weight=4, minsize=280)
            self.grid_columnconfigure(2, weight=1, minsize=120)
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=0)

            self.sidebar.grid_configure(row=0, column=0, sticky="nsew")
            self.container.grid_configure(row=0, column=1, columnspan=1, sticky="nsew", padx=10, pady=10)
            self.intel_panel.grid_configure(row=0, column=2, columnspan=1, sticky="nsew", padx=0, pady=0)

    def create_stat_widget(self, title, value):
        """Crée un bloc de données stylisé Drake"""
        f = ctk.CTkFrame(
            self.intel_panel,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            corner_radius=0,
        )
        f.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(
            f,
            text=title,
            font=("Segoe UI", 9, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(pady=(5, 0))

        lbl = ctk.CTkLabel(
            f,
            text=value,
            font=("Orbitron", 22, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )
        lbl.pack(pady=(0, 5))
        return lbl

    def refresh_intel(self):
        """Mise à jour des données temps réel du panel de droite"""
        try:
            stats = self.controller.get_dashboard_stats()
            total = stats.get("players", 0)
            open_contracts = stats.get("active_contracts", 0)
            known_orgs = stats.get("organizations", 0)

            self.stat_targets.configure(text=f"{total:03d}")  # Format 001, 002...
            self.stat_active_contracts.configure(
                text=f"{open_contracts:03d}",
                text_color=(
                    DrakeConfig.ACCENT_ERROR
                    if open_contracts > 0
                    else DrakeConfig.ACCENT_PRIMARY
                ),
            )
            self.stat_orgs.configure(text=f"{known_orgs:03d}")

        except Exception as e:
            try:
                if hasattr(self.controller, "log"):
                    self.controller.log(f"Intel refresh error: {e}", source="UI")
            except Exception:
                pass

    def request_intel_refresh(self):
        """Planifie un refresh UI sûr des widgets de stats du panneau droit."""
        try:
            self.after(0, self.refresh_intel)
        except Exception:
            try:
                self.refresh_intel()
            except Exception:
                pass

    def _prompt_org_setup(self):
        """Popup de configuration de l'organisation principale."""
        top = ctk.CTkToplevel(self)
        top.title("ORGANIZATION SETUP")
        top.geometry("480x400")
        top.resizable(False, False)
        top.configure(fg_color=DrakeConfig.BG_MAIN)
        top.grab_set()
        top.focus_set()

        # ── Titre ──
        ctk.CTkLabel(
            top,
            text="⚙  MAIN ORGANIZATION",
            font=("Orbitron", 14, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            top,
            text="Set your organization before opening this section.",
            font=("Consolas", 10),
            text_color=DrakeConfig.TEXT_SECONDARY,
            wraplength=420,
        ).pack(pady=(0, 18))

        # ── Séparateur ──
        ctk.CTkFrame(top, height=1, fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0).pack(fill="x", padx=20)

        # ── Saisie manuelle ──
        ctk.CTkLabel(
            top,
            text="ENTER SID MANUALLY",
            font=("Consolas", 9),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(14, 2))

        entry_frame = ctk.CTkFrame(top, fg_color="transparent")
        entry_frame.pack(fill="x", padx=24)

        sid_entry = DrakeEntry(
            entry_frame,
            placeholder_text="EX: SCRP",
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            height=36,
        )
        sid_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def _confirm_manual():
            sid = sid_entry.get().strip().upper()
            if not sid:
                return
            self.controller.set_setting("my_org_sid", sid)
            top.destroy()
            self.show_page("OrgFrame")

        DrakeButton(
            entry_frame,
            text="CONFIRM",
            width=90,
            height=36,
            command=_confirm_manual,
        ).pack(side="left")

        sid_entry.bind("<Return>", lambda e: _confirm_manual())

        # ── Séparateur ──
        ctk.CTkFrame(top, height=1, fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0).pack(fill="x", padx=20, pady=(16, 0))

        # ── Sélection parmi les orgs enregistrées ──
        ctk.CTkLabel(
            top,
            text="OR SELECT FROM SAVED ORGANIZATIONS",
            font=("Consolas", 9),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(12, 2))

        # Charge les orgs disponibles
        try:
            rows = self.controller.query(
                "SELECT sid, name FROM organizations ORDER BY name", ()
            )
            org_options = [f"{r[1] or r[0]}  [{r[0]}]" for r in rows if r[0]]
        except Exception:
            org_options = []

        select_frame = ctk.CTkFrame(top, fg_color="transparent")
        select_frame.pack(fill="x", padx=24)

        if org_options:
            combo_var = ctk.StringVar(value=org_options[0])
            combo = ctk.CTkComboBox(
                select_frame,
                values=org_options,
                variable=combo_var,
                state="readonly",
                fg_color=DrakeConfig.BG_TERMINAL,
                border_color=DrakeConfig.BORDER_COLOR,
                button_color=DrakeConfig.ACCENT_PRIMARY,
                dropdown_fg_color=DrakeConfig.BG_PANEL,
                text_color=DrakeConfig.TEXT_MAIN,
                height=36,
            )
            combo.pack(side="left", fill="x", expand=True, padx=(0, 8))

            def _confirm_select():
                val = combo_var.get()
                # Extrait le SID entre crochets
                import re
                m = re.search(r"\[([^\]]+)\]", val)
                sid = m.group(1).strip().upper() if m else val.strip().upper()
                if not sid:
                    return
                self.controller.set_setting("my_org_sid", sid)
                top.destroy()
                self.show_page("OrgFrame")

            DrakeButton(
                select_frame,
                text="SELECT",
                width=90,
                height=36,
                command=_confirm_select,
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                select_frame,
                text="No organizations found in database.",
                font=("Consolas", 10),
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", pady=6)

        # ── Bouton annuler ──
        DrakeButton(
            top,
            text="CANCEL",
            width=120,
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            command=top.destroy,
        ).pack(pady=(20, 10))

    def show_page(self, page_name):
        """Affiche la frame sélectionnée et rafraîchit ses données"""
        # Vérifie si l'org principale est configurée avant d'ouvrir la section organisations
        if page_name == "OrgFrame":
            sid = self.controller.get_setting("my_org_sid", "")
            if not sid:
                self._prompt_org_setup()
                return

        previous_page = getattr(self, "_current_page_name", None)
        # Evite les refresh inutiles si l'utilisateur reclique sur le menu deja actif.
        if previous_page == page_name:
            return

        frame = self._get_or_create_frame(page_name)

        # Réinitialisation ciblée de la page quittée (sans manipuler les placeholders internes)
        if previous_page and previous_page in self.frames and previous_page != page_name:
            previous_frame = self.frames.get(previous_page)
            try:
                if previous_frame is not None and hasattr(previous_frame, "_on_page_leave"):
                    previous_frame._on_page_leave()
            except Exception:
                pass

        # Ferme les popups de suggestion sur toutes les pages,
        # y compris celle que l'on quitte.
        for candidate in list(self.frames.values()):
            try:
                if hasattr(candidate, "_close_popup"):
                    candidate._close_popup()
                if hasattr(candidate, "_close_ship_popup"):
                    candidate._close_ship_popup()
            except Exception:
                pass

        frame.tkraise()
        # Appel du refresh interne de la page si disponible
        if hasattr(frame, "refresh"):
            frame.refresh()
        # Réinitialise les placeholders des combobox à chaque affichage de page.
        self._reset_combobox_placeholders_in_frame(frame)
        # Mise à jour globale du panel intel
        self.refresh_intel()
        self._current_page_name = page_name

    def _get_or_create_frame(self, page_name):
        """Retourne une page existante ou l'instancie à la demande."""
        frame = self.frames.get(page_name)
        if frame is not None:
            return frame

        spec = self.page_specs.get(page_name)
        if spec is None:
            raise KeyError(f"Unknown page: {page_name}")

        module = import_module(spec["module"])
        frame_class = getattr(module, spec["class"])
        kwargs = spec.get("kwargs", {})
        frame = frame_class(self.container, self.controller, **kwargs)
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frames[page_name] = frame
        return frame

    def _iter_children_recursive(self, widget):
        """Parcourt récursivement l'arborescence des widgets enfants."""
        for child in widget.winfo_children():
            yield child
            yield from self._iter_children_recursive(child)

    def _reset_placeholders_in_frame(self, frame):
        """Réinitialise les CTkEntry avec placeholder lors d'un changement de menu."""
        for widget in self._iter_children_recursive(frame):
            if not isinstance(widget, ctk.CTkEntry):
                continue
            try:
                placeholder = widget.cget("placeholder_text")
            except Exception:
                placeholder = ""
            if not placeholder:
                continue

            try:
                # Reset robuste: état neutre puis réactivation visuelle du placeholder.
                if hasattr(widget, "_deactivate_placeholder"):
                    widget._deactivate_placeholder()
                widget.delete(0, "end")
                if hasattr(widget, "_activate_placeholder"):
                    try:
                        focus_widget = widget.winfo_toplevel().focus_get()
                    except Exception:
                        focus_widget = None
                    if focus_widget != widget:
                        widget._activate_placeholder()
            except Exception:
                # Certains champs peuvent être temporaires/disabled: on ignore.
                pass

    def _is_resettable_combobox(self, widget) -> bool:
        """Détermine si un widget expose une API combobox resettable (get/set)."""
        if isinstance(widget, ctk.CTkComboBox):
            return True
        if "ComboBox" in widget.__class__.__name__ and hasattr(widget, "get") and hasattr(widget, "set"):
            return True
        return False

    def _reset_combobox_placeholders_in_frame(self, frame):
        """Réinitialise toutes les combobox de la page à leur valeur initiale (placeholder logique)."""
        for widget in self._iter_children_recursive(frame):
            if not self._is_resettable_combobox(widget):
                continue

            try:
                if hasattr(widget, "close_dropdown"):
                    widget.close_dropdown(reason="page_change")
            except Exception:
                pass

            try:
                if not hasattr(widget, "_drake_placeholder_value"):
                    widget._drake_placeholder_value = widget.get()

                placeholder_value = getattr(widget, "_drake_placeholder_value", None)
                if placeholder_value is not None:
                    widget.set(placeholder_value)
            except Exception:
                pass

    def log_message(self, message, source="SYS"):
        """Méthode centrale pour envoyer des logs vers le panneau de droite"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Elevate scanner-related logs visually
        try:
            if source == "SCANNER":
                # Add a clear separator and explicit scanner tag
                self.terminal.log(f"--- SCANNER: {message} ---")
                return
        except Exception:
            pass

        self.terminal.log(f"[{source}] {message}")
