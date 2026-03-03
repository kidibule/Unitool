"""Frame pour la gestion des contrats / bounty board."""

import customtkinter as ctk
import tkinter as tk
from drake_ui.engine import DrakeComboBox, DrakeConfig, DrakeButton
from utils import format_int_with_dots

class ContractFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        

        # --- Variables de gestion du popup ---
        self._suggestion_popup = None
        self._suggestion_owner = None
        self.winfo_toplevel().bind("<Configure>", self._update_popup_pos, add="+")
        # --- TITRE ---
        DrakeConfig.create_title(self, "BOUNTY BOARD")

        # --- FORMULAIRE D'AJOUT ---
        f_add = ctk.CTkFrame(self, fg_color=DrakeConfig.BG_PANEL, corner_radius=0, 
                             border_width=1, border_color=DrakeConfig.BORDER_COLOR)
        f_add.pack(pady=5, padx=20, fill="x")

        # Configuration des colonnes pour qu'elles se partagent l'espace
        # Les colonnes 0, 1 et 2 prendront plus de place si besoin (weight=1)
        f_add.grid_columnconfigure((0, 1, 2), weight=1) 
        f_add.grid_columnconfigure((3, 4, 5), weight=0) # Les menus et bouton gardent leur taille

        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "text_color": DrakeConfig.TEXT_MAIN,
            "corner_radius": 0,
            "border_width": 1
        }   
        
        # On utilise .grid() au lieu de .pack()
        self.target_in = ctk.CTkEntry(f_add, placeholder_text="TARGET ID", **entry_kwargs)
        self.target_in.grid(row=0, column=0, padx=5, pady=15, sticky="ew")
        self.target_in.bind("<KeyRelease>", lambda e: self._on_key_release(e, self.target_in))
        self.target_in.bind("<FocusOut>", self._on_focus_out)

        self.client_in = ctk.CTkEntry(f_add, placeholder_text="CLIENT ID", **entry_kwargs)
        self.client_in.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        self.client_in.bind("<KeyRelease>", lambda e: self._on_key_release(e, self.client_in))
        self.client_in.bind("<FocusOut>", self._on_focus_out)
        
        self.reward_in = ctk.CTkEntry(f_add, placeholder_text="REWARD", **entry_kwargs)
        self.reward_in.grid(row=0, column=2, padx=5, pady=15, sticky="ew")

        self.type_var = ctk.StringVar(value="TYPE")
        self.type_menu = DrakeComboBox(
            f_add, 
            variable=self.type_var, 
            width=110,
            values=[],
            command=self.apply_type,
        )
        self.type_menu.grid(row=0, column=3, padx=5, pady=15)

        self.prio_var = ctk.StringVar(value="PRORITY")
        self.prio_menu = DrakeComboBox(
            f_add, 
            variable=self.prio_var, 
            width=100,
            values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        )
        self.prio_menu.grid(row=0, column=4, padx=5, pady=15)

        # Le bouton "ACCEPT" est maintenant bien ancré à droite
        DrakeButton(f_add, text="ACCEPT", width=140, command=self.add_contract).grid(row=0, column=5, padx=10, pady=15)
        
          # Gestion des Types (Petit bouton discret)
        ctk.CTkButton(
            self,
            text="EDIT TYPES",
            command=self.open_type_manager, # On pointe vers la nouvelle méthode
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            width=80,
            height=20,
            font=("Segoe UI", 9, "bold"),
            corner_radius=0 # Pour garder le look industriel angulaire
        ).pack(anchor="ne", padx=20, pady=(0, 5))

        # --- SECTIONS DE LISTES ---
        self.active_scroll = ctk.CTkScrollableFrame(
            self, label_text="ACTIVE MISSIONS / URGENT TASKS",
            label_font=DrakeConfig.FONT_UI, label_fg_color=DrakeConfig.BG_PANEL,
            label_text_color=DrakeConfig.ACCENT_PRIMARY, fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0, border_width=1, border_color=DrakeConfig.BORDER_COLOR
        )
        self.active_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        self.stats_label = ctk.CTkLabel(self, text="TOTAL COLLECTED : 0 aUEC", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY)
        self.stats_label.pack(pady=(10, 0))

        self.history_scroll = ctk.CTkScrollableFrame(
            self, label_text="TRANSACTION LOGS / COMPLETED",
            label_font=DrakeConfig.FONT_UI, label_fg_color=DrakeConfig.BG_PANEL,
            label_text_color=DrakeConfig.TEXT_SECONDARY, fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0, border_width=1, border_color=DrakeConfig.BORDER_COLOR
        )
        self.history_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        # --- INITIALISATION ---
        self.refresh()
        self.update_type_menu()
        self.winfo_toplevel().bind("<Configure>", self._update_popup_pos, add="+")

    def refresh(self):
        """Rafraîchit l'UI via le sub-controller 'contract'."""
        for scroll in [self.active_scroll, self.history_scroll]:
            for w in scroll.winfo_children(): w.destroy()

        # Accès via self.controller.contract
        for c in self.controller.contract.get_active_contracts_as_models():
            self._draw_active_row(c)

        for c in self.controller.contract.get_closed_contracts_as_models():
            self._draw_history_row(c)
            
        total = self.controller.contract.get_total_gains()
        self.stats_label.configure(text=f"TOTAL COLLECTED : {format_int_with_dots(total)} aUEC")

    def _draw_active_row(self, c):
        f = ctk.CTkFrame(self.active_scroll, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
        f.pack(pady=2, fill="x", padx=5)

        colors = {"LOW": "#aaaaaa", "MEDIUM": DrakeConfig.ACCENT_PRIMARY, "HIGH": "#ff6600", "CRITICAL": DrakeConfig.ACCENT_ERROR}
        p_color = colors.get(c.priority, DrakeConfig.TEXT_MAIN)

        ctk.CTkLabel(f, text=f"[{c.priority[:3]}] {c.contract_type or 'TASK'}", 
                     font=DrakeConfig.FONT_LOGS, text_color=p_color).pack(side="left", padx=10)
        
        ctk.CTkLabel(f, text=f"🎯 {c.target} | {format_int_with_dots(c.reward)} aUEC", 
                     font=DrakeConfig.FONT_LOGS).pack(side="left", padx=5)

        DrakeButton(f, text="CLOSE", width=60, height=24, 
                    command=lambda: self.complete_contract(c.id, c.target)).pack(side="right", padx=10)

    def _draw_history_row(self, c):
        f = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
        f.pack(pady=1, fill="x", padx=5)
        txt = f">> {c.priority} | COMPLETED: {c.target} | RECEIVED: {format_int_with_dots(c.reward)} aUEC"
        ctk.CTkLabel(f, text=txt, font=DrakeConfig.FONT_LOGS, text_color=DrakeConfig.TEXT_SECONDARY).pack(side="left", padx=10)
        ctk.CTkButton(f, text="[DEL]", fg_color="transparent", text_color="#444", hover_color=DrakeConfig.ACCENT_ERROR,
                      width=20, height=18, command=lambda: self.delete_history(c.id)).pack(side="right", padx=5)

    def add_contract(self):
        if hasattr(self.type_menu, "close_dropdown"):
            self.type_menu.close_dropdown()

        target = self.target_in.get().strip()
        if not target: return
        
        self.controller.contract.add_contract(
            target=target,
            client=self.client_in.get().strip(),
            reward=self.reward_in.get().strip(),
            priority=self.prio_var.get(),
            contract_type=None if self.type_var.get() == "TYPE" else self.type_var.get()
        )
        self.refresh()
        for e in [self.target_in, self.client_in, self.reward_in]: e.delete(0, "end")

    def complete_contract(self, cid, target):
        self.controller.contract.complete_contract(cid, target)
        self.refresh()
        if hasattr(self.controller, "view") and hasattr(self.controller.view, "refresh_intel"):
            self.controller.view.refresh_intel()

    def delete_history(self, cid):
        self.controller.contract.delete_contract(cid)
        self.refresh()

    def update_type_menu(self):
        types = self.controller.contract.get_contract_types()
        # On s'assure que c'est une liste plate : ["BOUNTY", "MINING", ...]
        clean_values = [str(t[0]) for t in types]
        self.type_menu.configure(values=clean_values)
        
    def apply_type(self, choice):
        if choice == "TYPE": return
        reward = self.controller.contract.get_contract_reward_for_type(choice)
        if reward:
            self.reward_in.delete(0, "end")
            self.reward_in.insert(0, format_int_with_dots(reward))

    def _on_key_release(self, event, entry_widget):
        val = entry_widget.get().strip()
        if not val or event.keysym in ("Down", "Up", "Return", "Escape"):
            self._close_popup()
            return
        suggestions = self.controller.contract.get_suggestions(val)
        if suggestions: self._show_popup(entry_widget, suggestions)
        else: self._close_popup()

    def _show_popup(self, entry_widget, items):
        self._close_popup()

        # CRUCIAL : Force Windows à calculer la position réelle du widget
        self.update_idletasks()

        self._suggestion_popup = tk.Toplevel(self)
        self._suggestion_popup.wm_overrideredirect(True)
        self._suggestion_popup.attributes("-topmost", True)

        # Calcul de position
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        w = entry_widget.winfo_width()
        
        lb = tk.Listbox(
            self._suggestion_popup, 
            bg=DrakeConfig.BG_PANEL, 
            fg=DrakeConfig.TEXT_MAIN,
            font=(DrakeConfig.FONT_LOGS[0], 10),
            selectbackground=DrakeConfig.ACCENT_PRIMARY,
            selectforeground=DrakeConfig.BG_MAIN,
            highlightthickness=1,
            highlightbackground=DrakeConfig.BORDER_COLOR,
            bd=0,
            activestyle="none"
        )
        for item in items:
            lb.insert(tk.END, item)
        lb.pack(fill="both", expand=True)

        # On définit la taille et la position
        self._suggestion_popup.geometry(f"{w}x{len(items)*22}+{x}+{y}")
        
        lb.bind("<ButtonRelease-1>", lambda e: self._select_item(entry_widget, lb))
        self._suggestion_owner = entry_widget

    def _select_item(self, entry_widget, listbox):
        selection = listbox.curselection()
        if selection:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, listbox.get(selection[0]))
        self._close_popup()

    def _on_focus_out(self, event):
        self.after(200, self._close_popup)
    
    def _update_popup_pos(self, event=None):
        """Recalcule la position du popup si la fenêtre principale bouge."""
        if self._suggestion_popup and self._suggestion_owner:
            # On récupère les nouvelles coordonnées du champ (owner)
            x = self._suggestion_owner.winfo_rootx()
            y = self._suggestion_owner.winfo_rooty() + self._suggestion_owner.winfo_height()
            w = self._suggestion_owner.winfo_width()
            
            # On applique la nouvelle géométrie
            self._suggestion_popup.geometry(f"{w}x{self._suggestion_popup.winfo_height()}+{x}+{y}")

    def _close_popup(self):
        if self._suggestion_popup:
            self._suggestion_popup.destroy()
            self._suggestion_popup = None
            self._suggestion_owner = None

    def open_type_manager(self):
        """Ouvre la fenêtre de configuration des types de contrats."""
        toplevel = ctk.CTkToplevel(self)
        toplevel.title("DRAKE - TYPE CONFIGURATION")
        toplevel.geometry("500x450")
        toplevel.configure(fg_color=DrakeConfig.BG_MAIN)
        toplevel.attributes("-topmost", True)
        
        # Titre interne à la popup
        ctk.CTkLabel(toplevel, text="CONTRACT TYPES DATABASE", 
                     font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=10)

        # --- Formulaire d'ajout ---
        f_in = ctk.CTkFrame(toplevel, fg_color=DrakeConfig.BG_PANEL, corner_radius=0, 
                           border_width=1, border_color=DrakeConfig.BORDER_COLOR)
        f_in.pack(fill="x", padx=20, pady=10)

        n_entry = ctk.CTkEntry(f_in, placeholder_text="TYPE NAME", font=DrakeConfig.FONT_LOGS, 
                               fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
        n_entry.pack(side="left", padx=10, pady=15, expand=True, fill="x")
        
        r_entry = ctk.CTkEntry(f_in, placeholder_text="REWARD (aUEC)", font=DrakeConfig.FONT_LOGS,
                               fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
        r_entry.pack(side="left", padx=5, pady=15)

        def add():
            n, r = n_entry.get().strip().upper(), r_entry.get().strip()
            if n and r:
                try:
                    # Conversion en int pour être sûr de la donnée
                    reward_val = int(r.replace(".", "").replace(" ", ""))
                    saved = self.controller.contract.add_contract_type(n, str(reward_val))
                    if saved:
                        refresh_list()
                        self.update_type_menu()
                        n_entry.delete(0, "end")
                        r_entry.delete(0, "end")
                except ValueError:
                    if hasattr(self.controller, "log"):
                        self.controller.log("CONFIG ERROR: INVALID REWARD NUMBER", source="ERROR")

        DrakeButton(f_in, text="+", width=40, command=add).pack(side="left", padx=10)

        # --- Liste Scrollable ---
        scroll = ctk.CTkScrollableFrame(
            toplevel, label_text="REGISTERED MISSION PROFILES",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            corner_radius=0, border_width=1, border_color=DrakeConfig.BORDER_COLOR
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        btn_abort = DrakeButton(toplevel, text="SAVE", border_width=1,
                                   command=toplevel.destroy)
        btn_abort.pack(side="bottom", fill="x", padx=20, pady=(0,20))

        def delete(name):
            self.controller.contract.delete_contract_type(name)
            refresh_list()
            self.update_type_menu()

        def refresh_list():
            for w in scroll.winfo_children(): w.destroy()
            rows = self.controller.contract.get_contract_types()
            for row in rows:
                f = ctk.CTkFrame(scroll, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
                f.pack(fill="x", pady=2, padx=5)
                
                ctk.CTkLabel(f, text=f"{row[0]}", font=DrakeConfig.FONT_LOGS, width=150, anchor="w").pack(side="left", padx=10)
                ctk.CTkLabel(f, text=f"{format_int_with_dots(row[1])} aUEC", font=DrakeConfig.FONT_LOGS, text_color=DrakeConfig.TEXT_SECONDARY).pack(side="left", padx=5)
                
                ctk.CTkButton(f, text="[ DELETE ]", width=70, height=20, 
                              fg_color="transparent", text_color=DrakeConfig.ACCENT_ERROR,
                              hover_color="#330000", font=("Segoe UI", 8, "bold"),
                              command=lambda n=row[0]: delete(n)).pack(side="right", padx=5)

        refresh_list()