"""Composants UI partagés et configuration visuelle "Drake".

Contient :
- `DrakeConfig` : constantes de thème (couleurs, polices, espacement)
- `DrakeButton` : bouton pré-stylisé
- `DrakeEntry` : champ texte pré-stylisé
- `DrakeTerminal` : zone texte / console stylisée
- `DrakeApp` : petite application de démonstration (utilitaire)
"""

import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from typing import Any, Callable, Dict, Optional, Tuple


# ==========================================
# 1. CONSTANTES DE LA CHARTE GRAPHIQUE (DRAKE CONFIG)
# ==========================================
class DrakeConfig:
    # Palette de Couleurs
    BG_MAIN = "#1a1a1a"
    BG_PANEL = "#2b2b2b"
    BG_TERMINAL = "#000000"

    ACCENT_PRIMARY = "#ff8c00" 
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

    @staticmethod
    def create_modal_window(
        parent,
        title: str,
        geometry: str = "500x220",
        fg_color: Optional[str] = None,
        resizable: bool = False,
    ):
        """Crée une fenêtre modale toujours au premier plan de la fenêtre principale."""
        def _is_valid_widget(widget) -> bool:
            try:
                return widget is not None and bool(widget.winfo_exists())
            except Exception:
                return False

        owner = None
        try:
            if parent is not None and hasattr(parent, "winfo_toplevel"):
                owner = parent.winfo_toplevel()
            else:
                owner = parent
        except Exception:
            owner = parent

        master = owner if _is_valid_widget(owner) else (parent if _is_valid_widget(parent) else None)
        popup = ctk.CTkToplevel(master) if master is not None else ctk.CTkToplevel()
        popup.title(title)
        popup.geometry(geometry)
        popup.configure(fg_color=fg_color or DrakeConfig.BG_MAIN)
        popup.resizable(resizable, resizable)

        if _is_valid_widget(owner):
            try:
                popup.transient(owner)
            except Exception:
                pass

        try:
            popup.attributes("-topmost", True)
        except Exception:
            pass

        try:
            popup.lift()
            popup.focus_force()
        except Exception:
            pass

        try:
            popup.grab_set()
        except Exception:
            pass

        return popup


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
            "height": 30,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class DrakeEntry(ctk.CTkEntry):
    """Champ texte pré-configuré selon la charte Drake."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "text_color": DrakeConfig.TEXT_MAIN,
            "border_color": DrakeConfig.BORDER_COLOR,
            "border_width": DrakeConfig.BORDER_WIDTH,
            "corner_radius": 0,
            "height": 35,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class DrakeEntryLight(ctk.CTkEntry):
    """Variante plus claire de DrakeEntry, optimisée pour les fonds noirs."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": "#2b2b2b",
            "text_color": DrakeConfig.TEXT_MAIN,
            "border_color": "#555555",
            "border_width": 1,
            "corner_radius": 6,
            "height": 35,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class DrakeSuggestionManager:
    """Gestionnaire réutilisable de suggestions pour les champs texte.

    Usage:
        manager = DrakeSuggestionManager(self)
        manager.attach(
            entry_widget,
            get_items=lambda q: [...],
            on_validate=lambda entry, value: ...,  # optionnel
        )
    """

    def __init__(self, root) -> None:
        self.root = root
        self._popup = None
        self._listbox = None
        self._owner = None
        self._entry_cfg: Dict[Any, Dict[str, Any]] = {}
        self._entry_state: Dict[Any, Dict[str, Any]] = {}

        try:
            self.root.winfo_toplevel().bind("<Configure>", self._update_popup_pos, add="+")
        except Exception:
            pass

    def attach(
        self,
        entry_widget,
        *,
        get_items: Callable[[str], list],
        on_validate: Optional[Callable[[Any, str], None]] = None,
        on_preview: Optional[Callable[[Any, str, int, int], None]] = None,
        on_clear: Optional[Callable[[Any], None]] = None,
        normalize: Optional[Callable[[str], str]] = None,
        max_items: int = 10,
    ) -> None:
        self._entry_cfg[entry_widget] = {
            "get_items": get_items,
            "on_validate": on_validate,
            "on_preview": on_preview,
            "on_clear": on_clear,
            "normalize": normalize or (lambda s: str(s)),
            "max_items": max_items,
        }
        self._entry_state[entry_widget] = {"items": [], "index": -1}

        entry_widget.bind("<KeyRelease>", lambda e, w=entry_widget: self._on_key_release(e, w), add="+")
        entry_widget.bind("<FocusOut>", lambda e, w=entry_widget: self._on_focus_out(e, w), add="+")
        entry_widget.bind("<Return>", lambda e, w=entry_widget: self._confirm_entry(w), add="+")
        entry_widget.bind("<KeyPress-Tab>", lambda e, w=entry_widget: self._on_tab_cycle(e, w, reverse=False), add="+")
        entry_widget.bind("<KeyPress-ISO_Left_Tab>", lambda e, w=entry_widget: self._on_tab_cycle(e, w, reverse=True), add="+")
        entry_widget.bind("<Shift-KeyPress-Tab>", lambda e, w=entry_widget: self._on_tab_cycle(e, w, reverse=True), add="+")

    def close_all(self) -> None:
        self._destroy_popup_visual()
        for state in self._entry_state.values():
            state["items"] = []
            state["index"] = -1

    def _state(self, entry_widget):
        return self._entry_state.setdefault(entry_widget, {"items": [], "index": -1})

    def _cfg(self, entry_widget):
        return self._entry_cfg.get(entry_widget)

    def _normalize(self, entry_widget, value: str) -> str:
        cfg = self._cfg(entry_widget)
        if not cfg:
            return str(value)
        try:
            return cfg["normalize"](str(value))
        except Exception:
            return str(value)

    def _set_entry_value(self, entry_widget, value: str) -> None:
        entry_widget.delete(0, "end")
        entry_widget.insert(0, self._normalize(entry_widget, str(value)))

    def _compute_items(self, entry_widget, raw_value: str) -> list:
        cfg = self._cfg(entry_widget)
        if not cfg:
            return []
        val = (raw_value or "").strip()
        if not val:
            return []
        try:
            items = cfg["get_items"](val) or []
        except Exception:
            items = []
        max_items = int(cfg.get("max_items", 10) or 10)
        return list(items)[:max_items]

    def _on_key_release(self, event, entry_widget):
        if self._cfg(entry_widget) is None:
            return

        keysym = getattr(event, "keysym", "")
        if keysym == "Escape":
            self.close_all()
            return
        if keysym in ("Down", "Up", "Return", "Tab"):
            return

        value = entry_widget.get().strip()
        state = self._state(entry_widget)
        if not value:
            state["items"] = []
            state["index"] = -1
            if self._owner == entry_widget:
                self._destroy_popup_visual()
            cfg = self._cfg(entry_widget)
            if cfg and cfg.get("on_clear"):
                try:
                    cfg["on_clear"](entry_widget)
                except Exception:
                    pass
            return

        items = self._compute_items(entry_widget, value)
        state["items"] = items
        state["index"] = -1
        if items:
            self._show_popup(entry_widget, items)
        elif self._owner == entry_widget:
            self._destroy_popup_visual()

    def _on_tab_cycle(self, _event, entry_widget, reverse: bool = False):
        if self._cfg(entry_widget) is None:
            return "break"

        state = self._state(entry_widget)
        items = list(state.get("items") or [])
        if self._owner != entry_widget or not items:
            items = self._compute_items(entry_widget, entry_widget.get())
            state["items"] = items
            state["index"] = -1

        if not items:
            if self._owner == entry_widget:
                self._destroy_popup_visual()
            return "break"

        step = -1 if reverse else 1
        state["index"] = (int(state.get("index", -1)) + step) % len(items)
        selected = items[state["index"]]
        self._set_entry_value(entry_widget, selected)
        self._show_popup(entry_widget, items, selected_item=selected)

        cfg = self._cfg(entry_widget)
        if cfg and cfg.get("on_preview"):
            try:
                cfg["on_preview"](entry_widget, self._normalize(entry_widget, str(selected)), state["index"] + 1, len(items))
            except Exception:
                pass
        return "break"

    def _confirm_entry(self, entry_widget):
        if self._cfg(entry_widget) is None:
            return "break"

        raw = entry_widget.get().strip()
        if not raw:
            if self._owner == entry_widget:
                self._destroy_popup_visual()
            return "break"

        state = self._state(entry_widget)
        items = list(state.get("items") or [])
        if self._owner != entry_widget or not items:
            items = self._compute_items(entry_widget, raw)

        selected = raw
        raw_up = raw.upper()
        for candidate in items:
            cand = str(candidate).strip()
            if cand.upper() == raw_up:
                selected = cand
                break
        else:
            for candidate in items:
                cand = str(candidate).strip()
                if cand.upper().startswith(raw_up):
                    selected = cand
                    break

        self._set_entry_value(entry_widget, selected)
        state["items"] = []
        state["index"] = -1
        if self._owner == entry_widget:
            self._destroy_popup_visual()

        cfg = self._cfg(entry_widget)
        if cfg and cfg.get("on_validate"):
            try:
                cfg["on_validate"](entry_widget, self._normalize(entry_widget, str(selected)))
            except Exception:
                pass
        return "break"

    def _show_popup(self, entry_widget, items, selected_item=None):
        self._destroy_popup_visual()
        self.root.update_idletasks()

        popup = tk.Toplevel(self.root)
        popup.wm_overrideredirect(True)
        popup.attributes("-topmost", True)

        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        w = entry_widget.winfo_width()

        lb = tk.Listbox(
            popup,
            bg=DrakeConfig.BG_PANEL,
            fg=DrakeConfig.TEXT_MAIN,
            font=(DrakeConfig.FONT_LOGS[0], 10),
            selectbackground=DrakeConfig.ACCENT_PRIMARY,
            selectforeground=DrakeConfig.BG_MAIN,
            highlightthickness=1,
            highlightbackground=DrakeConfig.BORDER_COLOR,
            bd=0,
            activestyle="none",
        )
        for item in items:
            lb.insert(tk.END, self._normalize(entry_widget, str(item)))
        lb.pack(fill="both", expand=True)

        if selected_item is not None:
            selected_norm = self._normalize(entry_widget, str(selected_item)).strip().upper()
            for idx, item in enumerate(items):
                if self._normalize(entry_widget, str(item)).strip().upper() == selected_norm:
                    lb.selection_clear(0, tk.END)
                    lb.selection_set(idx)
                    lb.activate(idx)
                    break

        popup.geometry(f"{w}x{len(items) * 22}+{x}+{y}")
        popup.lift()
        lb.bind("<ButtonRelease-1>", lambda _e, w=entry_widget, l=lb: self._select_item(w, l), add="+")

        self._popup = popup
        self._listbox = lb
        self._owner = entry_widget

    def _select_item(self, entry_widget, listbox):
        selection = listbox.curselection()
        if selection:
            self._set_entry_value(entry_widget, listbox.get(selection[0]))
            cfg = self._cfg(entry_widget)
            if cfg and cfg.get("on_validate"):
                try:
                    cfg["on_validate"](entry_widget, entry_widget.get().strip())
                except Exception:
                    pass
        state = self._state(entry_widget)
        state["items"] = []
        state["index"] = -1
        self._destroy_popup_visual()

    def _on_focus_out(self, _event, entry_widget):
        if self._owner != entry_widget:
            return
        self.root.after(120, self._close_if_unfocused)

    def _widget_is_descendant(self, widget, ancestor) -> bool:
        if widget is None or ancestor is None:
            return False
        try:
            current = widget
            while current is not None:
                if current == ancestor:
                    return True
                current = current.master
        except Exception:
            return False
        return False

    def _close_if_unfocused(self):
        if not self._popup:
            return
        focus_widget = self.root.focus_get()
        if focus_widget == self._owner:
            return
        if self._listbox and focus_widget == self._listbox:
            return
        if self._widget_is_descendant(focus_widget, self._popup):
            return
        self._destroy_popup_visual()

    def _update_popup_pos(self, _event=None):
        if self._popup and self._owner:
            x = self._owner.winfo_rootx()
            y = self._owner.winfo_rooty() + self._owner.winfo_height()
            w = self._owner.winfo_width()
            self._popup.geometry(f"{w}x{self._popup.winfo_height()}+{x}+{y}")

    def _destroy_popup_visual(self):
        if self._popup:
            self._popup.destroy()
        self._popup = None
        self._listbox = None
        self._owner = None


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
        popup = DrakeConfig.create_modal_window(
            parent=parent,
            title=title,
            geometry="500x200",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=False,
        )

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

        popup = DrakeConfig.create_modal_window(
            parent=parent,
            title=title,
            geometry="500x220",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=False,
        )

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
        popup = DrakeConfig.create_modal_window(
            parent=parent,
            title=title,
            geometry="500x220",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=False,
        )

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

    @staticmethod
    def warning(title: str, message: str, parent=None):
        """Popup avertissement avec style Drake (accent orange)."""
        popup = DrakeConfig.create_modal_window(
            parent=parent,
            title=title,
            geometry="500x220",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=False,
        )

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 11),
            text_color=DrakeConfig.TEXT_MAIN,
            wraplength=450,
            justify="left",
        ).pack(pady=10, fill="both", expand=True)

        DrakeButton(
            frame,
            text="OK",
            fg_color=DrakeConfig.ACCENT_PRIMARY,
            hover_color=DrakeConfig.ACCENT_HOVER,
            text_color="#000000",
            command=popup.destroy,
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

# ==========================================
# OUTILS DE GRAPHIQUE (EXTRA)
# ==========================================

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
        if self.is_open:
            self.close_dropdown()
        else:
            self.close_dropdown() 
            self.open_dropdown()

    def open_dropdown(self):
        if self.is_open: 
            self.close_dropdown()
            return
            
        self.is_open = True

        # Calcul position exacte
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        field_width = self.winfo_width()
        dropdown_width = self._compute_dropdown_width(field_width)

        # Création du Toplevel
        self.dropdown = ctk.CTkToplevel(self)
        self.dropdown.overrideredirect(True)
        self.dropdown.attributes("-topmost", True)
        
        # --- Liaison pour suivre le mouvement ---
        self._parent_window = self.winfo_toplevel()
        self._move_bind_id = self._parent_window.bind("<Configure>", self._update_pos, add="+")
        self._click_bind_id = self._parent_window.bind("<ButtonPress-1>", self._on_parent_click, add="+")
        
        self._reposition_dropdown()

        # Hauteur dynamique
        height = min(len(self.values) * 35 + 10, 200)
        self.dropdown.geometry(f"{dropdown_width}x{height}+{x}+{y}")
        self.dropdown.configure(fg_color=DrakeConfig.ACCENT_PRIMARY)

        # Frame de bordure style Drake
        border_frame = ctk.CTkFrame(
            self.dropdown,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            border_width=1,
            corner_radius=0
        )
        border_frame.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(border_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # Remplissage
        for value in self.values:
            item = ctk.CTkButton(
                scroll,
                text=str(value).upper(),
                fg_color="transparent",
                hover_color=DrakeConfig.ACCENT_PRIMARY,
                text_color=DrakeConfig.TEXT_MAIN,
                anchor="w",
                height=30,
                corner_radius=0,
                command=lambda v=value: self.select(v)
            )
            item.pack(fill="x", pady=1)

        # --- LOGIQUE DE FERMETURE ---
        self.dropdown.after(10, self.dropdown.focus_set)
        self.dropdown.bind("<FocusOut>", lambda _e: self.close_dropdown(), add="+")

    def _point_in_widget(self, widget, x_root: int, y_root: int) -> bool:
        if widget is None or not widget.winfo_exists():
            return False
        x1 = widget.winfo_rootx()
        y1 = widget.winfo_rooty()
        x2 = x1 + widget.winfo_width()
        y2 = y1 + widget.winfo_height()
        return x1 <= x_root <= x2 and y1 <= y_root <= y2

    def _on_parent_click(self, event):
        """Ferme la liste si clic hors combobox ET hors dropdown."""
        if not self.is_open or not self.dropdown:
            return
        x, y = event.x_root, event.y_root
        in_combo = self._point_in_widget(self, x, y)
        in_dropdown = self._point_in_widget(self.dropdown, x, y)
        if not in_combo and not in_dropdown:
            self.close_dropdown()

    def _reposition_dropdown(self):
        """Calcule et applique la position."""
        if self.dropdown:
            self.update_idletasks()
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            field_width = self.winfo_width()
            dropdown_width = self._compute_dropdown_width(field_width)
            
            height = min(len(self.values) * 35 + 10, 200)
            self.dropdown.geometry(f"{dropdown_width}x{height}+{x}+{y}")

    def _compute_dropdown_width(self, field_width: int) -> int:
        """Largeur du dropdown = largeur du champ, sauf si un item est plus long."""
        try:
            font_obj = tkfont.Font(font=self.entry.cget("font"))
        except Exception:
            font_obj = tkfont.nametofont("TkDefaultFont")

        max_item_px = 0
        for value in self.values:
            text_px = font_obj.measure(str(value).upper())
            if text_px > max_item_px:
                max_item_px = text_px

        # Marge interne + scrollbar + respirations visuelles
        required_width = max_item_px + 56
        raw_width = max(field_width, required_width)

        # Sous Windows avec scaling (125%, 150%...), geometry() applique un facteur
        # supplémentaire; on compense pour conserver la largeur visuelle du champ.
        try:
            tk_scaling = float(self.tk.call("tk", "scaling"))
        except Exception:
            tk_scaling = 1.0
        if tk_scaling <= 0:
            tk_scaling = 1.0

        return max(1, int(round(raw_width / tk_scaling)))

    def _update_pos(self, event=None):
        """Appelé quand la fenêtre principale bouge."""
        if self.is_open and self.dropdown:
            self._reposition_dropdown()

    def close_dropdown(self):
        if self.dropdown:
            if hasattr(self, "_move_bind_id"):
                self._parent_window.unbind("<Configure>", self._move_bind_id)
                delattr(self, "_move_bind_id")
            if hasattr(self, "_click_bind_id"):
                self._parent_window.unbind("<ButtonPress-1>", self._click_bind_id)
                delattr(self, "_click_bind_id")

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

        if "values" in kwargs:
            self.values = kwargs.pop("values")
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

        super().configure(**kwargs)

class DrakeComboBoxLight(ctk.CTkFrame):
    """Variante plus claire de DrakeComboBox, optimisée pour les fonds noirs.

    Identique à DrakeComboBox, mais avec un fond #2b2b2b et une bordure #555555
    pour améliorer la visibilité lorsque le widget est posé sur un fond noir.
    """

    # Couleurs spécifiques à cette variante
    _BG      = "#2b2b2b"  # BG_PANEL — clairement distinct du fond noir
    _BORDER  = "#555555"  # Bordure plus lumineuse que BORDER_COLOR (#333333)
    _HOVER   = "#3a3a3a"  # Hover de la zone de texte

    def __init__(self, master, values=None, command=None, variable=None, width=200, **kwargs):
        if "variable" in kwargs:
            variable = kwargs.pop("variable")

        fg_color     = kwargs.pop("fg_color", self._BG)
        border_color = kwargs.pop("border_color", self._BORDER)

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

        if variable:
            self.selected_value = variable
        else:
            self.selected_value = ctk.StringVar(value=self.values[0] if self.values else "")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- ENTRY AREA ---
        self.entry = ctk.CTkButton(
            self,
            textvariable=self.selected_value,
            text_color=DrakeConfig.TEXT_MAIN,
            fg_color="transparent",
            hover_color=self._HOVER,
            anchor="w",
            corner_radius=6,
            command=self.toggle_dropdown
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

    def toggle_dropdown(self):
        if self.is_open:
            self.close_dropdown()
        else:
            self.close_dropdown()
            self.open_dropdown()

    def open_dropdown(self):
        if self.is_open:
            self.close_dropdown()
            return

        self.is_open = True

        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        field_width = self.winfo_width()
        dropdown_width = self._compute_dropdown_width(field_width)

        self.dropdown = ctk.CTkToplevel(self)
        self.dropdown.overrideredirect(True)
        self.dropdown.attributes("-topmost", True)

        self._parent_window = self.winfo_toplevel()
        self._move_bind_id = self._parent_window.bind("<Configure>", self._update_pos, add="+")
        self._click_bind_id = self._parent_window.bind("<ButtonPress-1>", self._on_parent_click, add="+")

        self._reposition_dropdown()

        height = min(len(self.values) * 35 + 10, 200)
        self.dropdown.geometry(f"{dropdown_width}x{height}+{x}+{y}")
        self.dropdown.configure(fg_color=DrakeConfig.ACCENT_PRIMARY)

        border_frame = ctk.CTkFrame(
            self.dropdown,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            border_width=1,
            corner_radius=0
        )
        border_frame.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(border_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        for value in self.values:
            item = ctk.CTkButton(
                scroll,
                text=str(value).upper(),
                fg_color="transparent",
                hover_color=DrakeConfig.ACCENT_PRIMARY,
                text_color=DrakeConfig.TEXT_MAIN,
                anchor="w",
                height=30,
                corner_radius=0,
                command=lambda v=value: self.select(v)
            )
            item.pack(fill="x", pady=1)

        self.dropdown.after(10, self.dropdown.focus_set)
        self.dropdown.bind("<FocusOut>", lambda _e: self.close_dropdown(), add="+")

    def _point_in_widget(self, widget, x_root: int, y_root: int) -> bool:
        if widget is None or not widget.winfo_exists():
            return False
        x1 = widget.winfo_rootx()
        y1 = widget.winfo_rooty()
        x2 = x1 + widget.winfo_width()
        y2 = y1 + widget.winfo_height()
        return x1 <= x_root <= x2 and y1 <= y_root <= y2

    def _on_parent_click(self, event):
        if not self.is_open or not self.dropdown:
            return
        x, y = event.x_root, event.y_root
        in_combo = self._point_in_widget(self, x, y)
        in_dropdown = self._point_in_widget(self.dropdown, x, y)
        if not in_combo and not in_dropdown:
            self.close_dropdown()

    def _reposition_dropdown(self):
        if self.dropdown:
            self.update_idletasks()
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            field_width = self.winfo_width()
            dropdown_width = self._compute_dropdown_width(field_width)
            height = min(len(self.values) * 35 + 10, 200)
            self.dropdown.geometry(f"{dropdown_width}x{height}+{x}+{y}")

    def _compute_dropdown_width(self, field_width: int) -> int:
        try:
            font_obj = tkfont.Font(font=self.entry.cget("font"))
        except Exception:
            font_obj = tkfont.nametofont("TkDefaultFont")

        max_item_px = 0
        for value in self.values:
            text_px = font_obj.measure(str(value).upper())
            if text_px > max_item_px:
                max_item_px = text_px

        required_width = max_item_px + 56
        raw_width = max(field_width, required_width)

        try:
            tk_scaling = float(self.tk.call("tk", "scaling"))
        except Exception:
            tk_scaling = 1.0
        if tk_scaling <= 0:
            tk_scaling = 1.0

        return max(1, int(round(raw_width / tk_scaling)))

    def _update_pos(self, event=None):
        if self.is_open and self.dropdown:
            self._reposition_dropdown()

    def close_dropdown(self):
        if self.dropdown:
            if hasattr(self, "_move_bind_id"):
                self._parent_window.unbind("<Configure>", self._move_bind_id)
                delattr(self, "_move_bind_id")
            if hasattr(self, "_click_bind_id"):
                self._parent_window.unbind("<ButtonPress-1>", self._click_bind_id)
                delattr(self, "_click_bind_id")
            self.dropdown.destroy()
            self.dropdown = None
        self.is_open = False

    def select(self, value):
        self.selected_value.set(value)
        self.close_dropdown()
        if self.command:
            self.command(value)

    def get(self):
        return self.selected_value.get()

    def set(self, value):
        self.selected_value.set(value)

    def configure(self, **kwargs):
        if "values" in kwargs:
            self.values = kwargs.pop("values")
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
        super().configure(**kwargs)


class DrakeDualComboBox(ctk.CTkFrame):
    """Deux comboboxes côte à côte pour sélectionner jusqu'à 2 rôles.

    API compatible DrakeComboBox / DrakeEntry :
    - get()          → str, "ROLE1, ROLE2" ou "ROLE1" ou ""
    - set(value)     → parse et remplit les 2 selects
    - delete(s, e)   → vide les 2
    - insert(i, v)   → alias set()
    - values         → property, liste des valeurs disponibles
    """

    def __init__(self, master, values: list = None, **kwargs):
        fg_color = kwargs.pop("fg_color", "transparent")
        super().__init__(master, fg_color=fg_color, **kwargs)

        self.placeholder = "ROLE"
        self.values = values or []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.role1 = DrakeComboBox(self, values=self.values, width=150)
        self.role1.set(self.placeholder)
        self.role1.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.role2 = DrakeComboBox(self, values=self.values, width=150)
        self.role2.set(self.placeholder)
        self.role2.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def get(self) -> str:
        r1 = self.role1.get().strip()
        r2 = self.role2.get().strip()
        if r1 == self.placeholder:
            r1 = ""
        if r2 == self.placeholder:
            r2 = ""
        if r1 and r2:
            return f"{r1}, {r2}"
        return r1 or r2 or ""

    def set(self, value: str) -> None:
        self.role1.set(self.placeholder)
        self.role2.set(self.placeholder)
        if not value:
            return
        parts = [p.strip().upper() for p in str(value).split(",") if p.strip()]
        if len(parts) >= 1:
            self.role1.set(parts[0])
        if len(parts) >= 2:
            self.role2.set(parts[1])

    def delete(self, start, end) -> None:
        """Vide les 2 combobox."""
        self.role1.set(self.placeholder)
        self.role2.set(self.placeholder)

    def insert(self, index, value: str) -> None:
        """Alias set()."""
        self.set(value)

    def configure(self, **kwargs):
        if "values" in kwargs:
            new_vals = kwargs.pop("values")
            self.values = new_vals
            self.role1.configure(values=new_vals)
            self.role2.configure(values=new_vals)
        super().configure(**kwargs)


class DrakeTitle1(ctk.CTkLabel):
    """Titre de niveau 1 stylisé pour les sections principales."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=DrakeConfig.FONT_TITLE,
            text_color=DrakeConfig.ACCENT_PRIMARY,
            **kwargs
        )

class DrakeTitle2(ctk.CTkLabel):
    """Titre de niveau 2 stylisé pour les sous-sections."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=("Orbitron", 14, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
            **kwargs
        )

class DrakeTitle3(ctk.CTkLabel):
    """Titre de niveau 3 stylisé pour les titres de configuration."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=("Orbitron", 12, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
            **kwargs
        )

class DrakeTitle4(ctk.CTkLabel):
    """Titre de niveau 4 stylisé pour les titres de catégorie."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=text.upper(),
            font=("Orbitron", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            **kwargs
        )

class DrakeClearButton(DrakeButton):
    """Bouton de réinitialisation stylisé pour les actions de reset."""

    def __init__(self, master, **kwargs) -> None:
        defaults = {
            "text": "RESET",
            "width": 60,
            "height": 30,
            "fg_color": "transparent",
            "border_width": 1,
            "border_color": DrakeConfig.ACCENT_ERROR,
            "text_color": DrakeConfig.ACCENT_ERROR,
            "hover_color": "#331111",
            "font": DrakeConfig.FONT_LOGS,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)