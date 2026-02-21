"""Vue principale de l'application — compose les différentes frames.

Contient la sidebar, le container central et le panneau intel droit.
"""

import customtkinter as ctk
from views.scanner_frame import ScannerFrame
from views.logger_frame import LoggerFrame
from views.contract_frame import ContractFrame
from views.intelligence_frame import IntelligenceFrame
from views.ship_frame import ShipFrame
from datetime import datetime

# Import du moteur graphique
from drake_ui.engine import DrakeConfig, DrakeButton


class MainView(ctk.CTkFrame):
    """Container principal qui orchestre les sous-frames.

    Args:
        parent: widget parent (généralement la fenêtre principale)
        controller: référence au controller / application pour accès DB et méthodes
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=DrakeConfig.BG_MAIN)
        self.controller = controller
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
        except Exception:
            pass

        # Configuration responsive de la grille (Sidebar | Container | Intel Panel)
        # Use weights so columns resize proportionally: sidebar 1, container 4, intel 1
        # This yields center column ~= 2/3 of available width (1:4:1 ratio)
        self.grid_columnconfigure(0, weight=1, minsize=200)
        self.grid_columnconfigure(1, weight=4, minsize=600)
        self.grid_columnconfigure(2, weight=1, minsize=200)
        self.grid_rowconfigure(0, weight=1)

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
            ("ContractFrame", "CONTRATS"),
            ("LoggerFrame", "ARCHIVER"),
            ("IntelligenceFrame", "INTEL"),
            ("ShipFrame", "SHIPS"),
        ]

        # Remplacement par des boutons typés Drake
        for name, label in menu_items:
            btn = ctk.CTkButton(
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

        self.frames = {}
        for F in (ScannerFrame, LoggerFrame, ContractFrame, IntelligenceFrame, ShipFrame):
            frame = F(self.container, self.controller)
            self.frames[F.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

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
            rows = self.controller.db.query("SELECT alignment, ship FROM targets")

            total = len(rows)

            # Count open contracts in the system (status not CLOSED)
            open_contracts = 0
            try:
                res = self.controller.db.query("SELECT COUNT(*) FROM contracts WHERE status!='CLOSED'")
                if res and len(res) > 0:
                    open_contracts = int(res[0][0])
            except Exception:
                open_contracts = 0
            known_orgs = 0
            try:
                # On interroge la nouvelle table organizations
                res_org = self.controller.db.query("SELECT COUNT(*) FROM organizations")
                if res_org:
                    known_orgs = int(res_org[0][0])
            except Exception:
                known_orgs = 0

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
            print(f"Intel Error: {e}")

    def show_page(self, page_name):
        """Affiche la frame sélectionnée et rafraîchit ses données"""
        self.frames[page_name].tkraise()
        # Appel du refresh interne de la page si disponible
        if hasattr(self.frames[page_name], "refresh"):
            self.frames[page_name].refresh()
        # Mise à jour globale du panel intel
        self.refresh_intel()

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
