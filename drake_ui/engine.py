"""Composants UI partagés et configuration visuelle "Drake".

Contient :
- `DrakeConfig` : constantes de thème (couleurs, polices, espacement)
- `DrakeButton` : bouton pré-stylisé
- `DrakeTerminal` : zone texte / console stylisée
- `DrakeApp` : petite application de démonstration (utilitaire)
"""

from turtle import width

import customtkinter as ctk
from typing import Tuple, Optional


# ==========================================
# 1. CONSTANTES DE LA CHARTE GRAPHIQUE (DRAKE CONFIG)
# ==========================================
class DrakeConfig:
    # Palette de Couleurs
    BG_MAIN = "#1a1a1a"
    BG_PANEL = "#2b2b2b"
    BG_TERMINAL = "#000000"

    ACCENT_PRIMARY = "#ff8c00"  # Dark Orange
    ACCENT_HOVER = "#e67e00"
    ACCENT_ERROR = "#ff4444"

    TEXT_MAIN = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    BORDER_COLOR = "#333333"

    # Typographie
    FONT_UI = ("Segoe UI", 12, "bold")
    FONT_LOGS = ("Courier New", 11)

    # Layout
    PADDING = 15
    CORNER_RADIUS = 5
    BORDER_WIDTH = 1
    FONT_TITLE = ("Orbitron", 16, "bold")

    @staticmethod
    def create_title(
        parent, text: str, pady: Tuple[int, int] = (20, 10), with_line: bool = False
    ):
        """Crée un label de titre stylisé.

        Args:
            parent: widget parent
            text: texte du titre
            pady: padding vertical
            with_line: ajoute une ligne visuelle en dessous
        """
        label = ctk.CTkLabel(
            parent,
            text=text.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )
        label.pack(pady=pady)

        if with_line:
            line = ctk.CTkFrame(parent, height=2, fg_color=DrakeConfig.ACCENT_PRIMARY)
            line.pack(fill="x", padx=100, pady=(0, 20))

        return label


# ==========================================
# 2. COMPOSANTS PRÉ-STYLISEZ (BIBLIOTHÈQUE)
# ==========================================


class DrakeButton(ctk.CTkButton):
    """Bouton CTA pré-configuré selon la charte Drake."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "fg_color": DrakeConfig.ACCENT_PRIMARY,
            "hover_color": DrakeConfig.ACCENT_HOVER,
            "text_color": "#000000",
            "font": DrakeConfig.FONT_UI,
            "corner_radius": DrakeConfig.CORNER_RADIUS,
            "height": 35,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class DrakeTerminal(ctk.CTkTextbox):
    """Zone de texte utilisée comme console/logs avec style prédéfini."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "fg_color": DrakeConfig.BG_TERMINAL,
            "text_color": DrakeConfig.ACCENT_PRIMARY,
            "border_color": DrakeConfig.ACCENT_PRIMARY,
            "border_width": DrakeConfig.BORDER_WIDTH,
            "font": DrakeConfig.FONT_LOGS,
            "corner_radius": DrakeConfig.CORNER_RADIUS,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def log(self, message: str) -> None:
        """Insère une ligne de log formatée et scroll automatique."""
        self.insert("end", f"> {str(message).upper()}...\n")
        self.see("end")


# ==========================================
# 3. POPUPS STYLISÉES (DRAKE DESIGN)
# ==========================================


class DrakePopup:
    """Classe utilitaire pour afficher des popups stylisées en accord avec le design Drake."""

    @staticmethod
    def info(title: str, message: str, parent=None):
        """Popup d'information avec bouton OK."""
        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        popup.geometry("500x200")
        popup.configure(fg_color=DrakeConfig.BG_MAIN)
        popup.resizable(False, False)
        if parent:
            popup.transient(parent)
            popup.grab_set()

        # Frame principal
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titre
        ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(0, 10))

        # Message
        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 11),
            text_color=DrakeConfig.TEXT_MAIN,
            wraplength=450,
            justify="left",
        ).pack(pady=10, fill="both", expand=True)

        # Bouton OK
        def close_popup():
            popup.destroy()

        DrakeButton(frame, text="OK", command=close_popup, height=40).pack(
            fill="x", pady=(10, 0)
        )

    @staticmethod
    def yesno(title: str, message: str, parent=None):
        """Popup yes/no avec deux boutons. Retourne True si oui, False si non."""
        result = {"value": None}

        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        popup.geometry("500x220")
        popup.configure(fg_color=DrakeConfig.BG_MAIN)
        popup.resizable(False, False)
        if parent:
            popup.transient(parent)
            popup.grab_set()

        # Frame principal
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titre
        ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(0, 10))

        # Message
        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 11),
            text_color=DrakeConfig.TEXT_MAIN,
            wraplength=450,
            justify="left",
        ).pack(pady=10, fill="both", expand=True)

        # Frame boutons
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        def on_yes():
            result["value"] = True
            popup.destroy()

        def on_no():
            result["value"] = False
            popup.destroy()

        DrakeButton(buttons_frame, text="OUI", command=on_yes, height=40).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        DrakeButton(
            buttons_frame,
            text="NON",
            fg_color=DrakeConfig.BG_PANEL,
            hover_color="#444444",
            text_color=DrakeConfig.TEXT_MAIN,
            command=on_no,
            height=40,
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

        popup.update()
        popup.wait_window()
        return result["value"] if result["value"] is not None else False

    @staticmethod
    def error(title: str, message: str, parent=None):
        """Popup erreur avec titre et message en rouge."""
        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        popup.geometry("500x220")
        popup.configure(fg_color=DrakeConfig.BG_MAIN)
        popup.resizable(False, False)
        if parent:
            popup.transient(parent)
            popup.grab_set()

        # Frame principal
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titre (en rouge pour erreur)
        ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_ERROR,
        ).pack(pady=(0, 10))

        # Message
        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 11),
            text_color=DrakeConfig.TEXT_MAIN,
            wraplength=450,
            justify="left",
        ).pack(pady=10, fill="both", expand=True)

        # Bouton OK
        def close_popup():
            popup.destroy()

        DrakeButton(
            frame,
            text="OK",
            fg_color=DrakeConfig.ACCENT_ERROR,
            hover_color="#cc0000",
            command=close_popup,
            height=40,
        ).pack(fill="x", pady=(10, 0))


# ==========================================
# 4. INTERFACE UTILISATEUR (APPLICATION)
# ==========================================


class DrakeApp(ctk.CTk):
    """Petite application de démonstration utilisant les composants Drake.

    Utile pour tester visuellement les composants du package.
    """

    def __init__(self) -> None:
        super().__init__()

        # --- CONFIGURATION FENÊTRE ---
        self.title("DRAKE SYSTEMS - OPERATIONAL UNIT")
        self.geometry("700x550")
        self.configure(fg_color=DrakeConfig.BG_MAIN)
        ctk.set_appearance_mode("Dark")

        # --- HEADER ---
        self.lbl_status = ctk.CTkLabel(
            self,
            text="UPLINK STATUS: CONNECTED",
            text_color=DrakeConfig.ACCENT_PRIMARY,
            font=("Segoe UI", 14, "bold"),
        )
        self.lbl_status.pack(pady=(20, 10))

        # --- MAIN CONTAINER ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(
            fill="both", expand=True, padx=DrakeConfig.PADDING, pady=DrakeConfig.PADDING
        )

        # --- INPUT SECTION (FRAME) ---
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(0, 10))

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="ENTER TARGET PARAMETERS",
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            text_color=DrakeConfig.TEXT_MAIN,
            height=40,
        )
        self.entry.pack(fill="x")

        # --- TERMINAL SECTION ---
        self.terminal = DrakeTerminal(self.main_frame, height=250)
        self.terminal.pack(fill="both", expand=True, pady=10)

        # --- ACTION BUTTONS (BOTTOM) ---
        self.btn_execute = DrakeButton(
            self.main_frame, text="INITIALIZE HANDSHAKE", command=self.run_process
        )
        self.btn_execute.pack(fill="x", side="bottom", pady=(10, 0))

    def run_process(self) -> None:
        """Exemple d'enchaînement de logs pour démonstration."""
        input_data = self.entry.get()

        if not input_data:
            self.terminal.log("error: no input detected")
            return

        self.terminal.log(f"targeting: {input_data}")
        self.terminal.log("syncing local buffers")
        self.terminal.log("data extraction in progress")
        self.terminal.log("handshake complete")


# ==========================================
# EXÉCUTION
# ==========================================
if __name__ == "__main__":
    app = DrakeApp()
    app.mainloop()

class DrakeComboBox(ctk.CTkFrame):
    """DrakeComboBox Premium avec dropdown custom et correction du focus."""

    def __init__(self, master, values=None, command=None, variable=None, width=200, **kwargs):
        # 1. Nettoyage des kwargs pour éviter les ValueError
        if "variable" in kwargs:
            variable = kwargs.pop("variable")
        
        fg_color = kwargs.pop("fg_color", DrakeConfig.BG_TERMINAL)
        border_color = kwargs.pop("border_color", DrakeConfig.BORDER_COLOR)
        
        super().__init__(
            master,
            fg_color=fg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=6,
            height=30,
            width=width,
            **kwargs
        )

        self.values = values or []
        self.command = command
        self.is_open = False
        
        # Gestion de la variable
        if variable:
            self.selected_value = variable
        else:
            self.selected_value = ctk.StringVar(value=self.values[0] if self.values else "")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- ENTRY AREA (Cliquable) ---
        self.entry = ctk.CTkButton(
            self,
            textvariable=self.selected_value,
            text_color=DrakeConfig.TEXT_MAIN,
            fg_color="transparent",
            hover_color=DrakeConfig.BG_TERMINAL,
            anchor="w",
            corner_radius=6,
            command=self.toggle_dropdown # <--- Cette méthode doit exister plus bas
        )
        self.entry.grid(row=0, column=0, sticky="nsew", padx=(5, 35))

        # --- ARROW BUTTON ---
        self.button = ctk.CTkButton(
            self,
            text="▼",
            width=32,
            fg_color=DrakeConfig.ACCENT_PRIMARY,
            hover_color=DrakeConfig.ACCENT_HOVER,
            text_color="#000000",
            corner_radius=4,
            command=self.toggle_dropdown
        )
        self.button.place(relx=1, rely=0, anchor="ne", relheight=1)

        self.dropdown = None

    # ===============================
    # LOGIQUE (Vérifie bien que ces noms correspondent !)
    # ===============================

    def toggle_dropdown(self):
        """Bascule l'état d'ouverture du menu."""
        if self.is_open:
            self.close_dropdown()
        else:
            self.open_dropdown()

    def open_dropdown(self):
        if self.is_open: return
        self.is_open = True

        # Calcul position
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()

        self.dropdown = ctk.CTkToplevel(self)
        self.dropdown.overrideredirect(True)
        self.dropdown.attributes("-topmost", True)
        self.dropdown.configure(fg_color=DrakeConfig.ACCENT_PRIMARY)

        height = min(len(self.values) * 35 + 15, 200)
        self.dropdown.geometry(f"{width}x{height}+{x}+{y}")

        border_frame = ctk.CTkFrame(
            self.dropdown,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            border_width=1,
            corner_radius=1
        )
        border_frame.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(border_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        for value in self.values:
            item = ctk.CTkButton(
                scroll,
                text=value,
                fg_color="transparent",
                hover_color=DrakeConfig.ACCENT_PRIMARY,
                text_color=DrakeConfig.TEXT_MAIN,
                anchor="w",
                command=lambda v=value: self.select(v)
            )
            item.pack(fill="x", pady=2)

        # Focus et fermeture
        self.dropdown.bind("<FocusOut>", lambda e: self.close_dropdown())
        self.dropdown.focus()

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.grab_release()
            self.dropdown.destroy()
        self.dropdown = None
        self.is_open = False

    def select(self, value):
        self.selected_value.set(value)
        self.close_dropdown()
        if self.command:
            self.command(value)

    # ===============================
    # PUBLIC API
    # ===============================

    def get(self):
        return self.selected_value.get()

    def set(self, value):
        self.selected_value.set(value)
        
    def configure(self, **kwargs):
        # 1. On intercepte et on traite nos paramètres personnalisés
        if "values" in kwargs:
            self.values = kwargs.pop("values")
            # Optionnel : réinitialiser la valeur sélectionnée si elle n'est plus dans la liste
            if self.get() not in self.values and self.values:
                self.set(self.values[0])

        if "command" in kwargs:
            self.command = kwargs.pop("command")

        if "variable" in kwargs:
            new_var = kwargs.pop("variable")
            self.selected_value = new_var
            self.entry.configure(textvariable=self.selected_value)

        if "text_color" in kwargs:
            color = kwargs.pop("text_color")
            self.entry.configure(text_color=color)

        # 2. On envoie le RESTE (ce qui n'a pas été "pop") au CTkFrame parent
        # kwargs ne contient plus 'values', donc plus de ValueError !
        super().configure(**kwargs)