"""Frame responsable du scanner de cibles et de l'édition des dossiers.

Fournit une interface de recherche, d'édition et d'export des cibles
stockées dans la base via le `controller`.
"""

import customtkinter as ctk
import webbrowser
import csv
import json
from tkinter import filedialog
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal, DrakePopup, DrakeComboBox, DrakeEntry, DrakeTitle1
from views.ship_frame import ShipFrame


def format_int_with_dots(value) -> str:
    """Format integer-like value with '.' thousands separator."""
    if value is None:
        return ""
    s = str(value).strip()
    if s in ("", "None"):
        return ""
    cleaned = s.replace(" ", "").replace(".", "").replace(",", "")
    try:
        n = int(cleaned)
    except Exception:
        return s
    return f"{n:,}".replace(",", ".")


# Paramètres d'entrée réutilisables pour les widgets
entry_kwargs = {
    "font": DrakeConfig.FONT_LOGS,
    "fg_color": DrakeConfig.BG_TERMINAL,
    "border_color": DrakeConfig.BORDER_COLOR,
    "corner_radius": 0,
    "height": 35,
}


class ScannerFrame(ctk.CTkFrame):
    """Interface de recherche et d'édition des cibles."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)

        self.title_label = DrakeTitle1(header, text="DATABASE")
        self.title_label.pack(side="left", expand=True, padx=(0, 0))

        self.tabview = DrakeConfig.create_tabview(self)

        self.tab_players = self.tabview.add("PLAYERS")
        self.tab_orgs = self.tabview.add("ORGANIZATIONS")
        self.tab_ships = self.tabview.add("SHIPS")

        self.setup_players_tab()
        self.setup_orgs_tab()
        self.setup_ships_tab()
        self.setup_tags()

    def setup_ships_tab(self):
        """Ajoute le catalogue Ships dans DATABASE (sans LOADOUT/CONFIG)."""
        self.ship_catalog = ShipFrame(self.tab_ships, self.controller, mode="catalog_only")
        self.ship_catalog.pack(fill="both", expand=True)

    def refresh(self):
        """Rafraîchit les sous-vues actives de DATABASE."""
        try:
            if hasattr(self, "ship_catalog"):
                self.ship_catalog.refresh()
        except Exception:
            pass

    def _on_page_leave(self):
        """Propague le cycle de sortie aux sous-vues embarquées."""
        try:
            if hasattr(self, "ship_catalog") and hasattr(self.ship_catalog, "_on_page_leave"):
                self.ship_catalog._on_page_leave()
        except Exception:
            pass

    def _close_ship_popup(self):
        """Expose la fermeture des popups Ship pour la vue principale."""
        try:
            if hasattr(self, "ship_catalog") and hasattr(self.ship_catalog, "_close_ship_popup"):
                self.ship_catalog._close_ship_popup()
        except Exception:
            pass

    def _log(self, message: str, source: str = "SCANNER") -> None:
        """Forward un message vers le terminal principal si l'API de log existe."""
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(message, source=source)
        except Exception:
            pass

    def setup_players_tab(self):
        """Configure l'onglet de recherche de joueurs."""
        self.search_entry = DrakeEntry(
            self.tab_players, placeholder_text="ENTER A HANDLE OR SID...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.search_entry.pack(pady=(10, 5), padx=20, fill="x")
        self.search_entry.bind("<KeyRelease>", self.run_scan)

        toolbar = ctk.CTkFrame(self.tab_players, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        DrakeButton(
            toolbar,
            text="IMPORT CSV",
            width=150,
            command=self.import_players_csv,
        ).pack(side="left", padx=5)

        DrakeButton(
            toolbar,
            text="EXPORT CSV",
            width=150,
            command=self.export_players_csv,
        ).pack(side="left", padx=5)

        self.results = DrakeTerminal(self.tab_players)
        self.results.pack(pady=5, padx=10, fill="both", expand=True)

   
    def setup_orgs_tab(self):
        """Configure l'onglet de recherche d'organisations."""
        self.org_search_entry = DrakeEntry(
            self.tab_orgs, placeholder_text="SEARCH AN ORG (NAME OR SID)...", 
            height=40, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.ACCENT_PRIMARY
        )
        self.org_search_entry.pack(pady=(10, 5), padx=20, fill="x")
        self.org_search_entry.bind("<KeyRelease>", self.run_org_scan)

        toolbar = ctk.CTkFrame(self.tab_orgs, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        DrakeButton(
            toolbar,
            text="IMPORT CSV",
            width=150,
            command=self.import_orgs_csv,
        ).pack(side="left", padx=5)

        DrakeButton(
            toolbar,
            text="EXPORT CSV",
            width=150,
            command=self.export_orgs_csv,
        ).pack(side="left", padx=5)

        self.org_results = DrakeTerminal(self.tab_orgs)
        self.org_results.pack(pady=5, padx=10, fill="both", expand=True)

    def run_org_scan(self, event):
        """Moteur de recherche Orga - Format Dossier de Renseignement."""
        import json
        q = self.org_search_entry.get().strip().upper()
        
        self.org_results.delete("0.0", "end")

        if len(q) > 1:
            orgs = self.controller.org.search_orgs(q) 
            # On filtre les résultats vides ou trop courts
            orgs = [o for o in orgs if o[0] and len(str(o[0])) > 2]

            for o in orgs:
                # On adapte la déballage pour correspondre au retour du controller
                sid, name, tag, count, o_type, spec, alignment, updated_at = o
                tag_name_click = f"edit_name_{sid}"
                tag_link = f"link_org_{sid}"
                tag_notes = f"notes_org_{sid}"
                
                # Récupération du modèle complet pour les champs étendus
                org_model = self.controller.org.get_org_model(sid)

                # --- [BLOC 1 : IDENTITÉ & TYPE] ---
                self.org_results.insert("end", " ■ ", alignment) 
                
                self.org_results.insert("end", f"{name} ", (tag_name_click, "NEUTRAL"))
                self.org_results.insert("end", "[")
                self.org_results.insert("end", f"{sid}", (tag_link, "link_org"))
                self.org_results.insert("end", "]")
                
                # Ligne de spécialisation
                self.org_results.insert("end", f"\n   TYPE: {o_type} | SPEC: {spec} | TAG: {tag or 'N/A'}\n")
                self.org_results.insert("end", f"   LAST UPDATE: {org_model.updated_at if org_model else 'UNKNOWN'}\n")

                # --- [BLOC 2 : ROSTER & EFFECTIFS] ---
                self.org_results.insert("end", "   " + "-"*45 + "\n", "separator")
                
                if org_model and org_model.visible_members:
                    try:
                        members = json.loads(org_model.visible_members)
                        if members:
                            # En-tête du tableau de membres
                            self.org_results.insert("end", f"   {'HANDLE':<25} | {'RANK':<20}\n", "ACCENT")
                            self.org_results.insert("end", f"   {'-'*48}\n", "ACCENT")
                            
                            # On affiche tous les membres
                            for m in members:
                                h = str(m.get('h', '???')).upper()
                                r = str(m.get('r', '???')).upper()
                                self.org_results.insert("end", f"   {h:<25} | {r:<20}\n", "ACCENT")

                            self.org_results.insert("end", "   " + "-"*45 + "\n", "separator")
                            
                            r_val = 0
                            if org_model.redacted_members:
                                try:
                                    if ":" in str(org_model.redacted_members):
                                        r_val = str(org_model.redacted_members).split(":")[-1].strip()
                                    else:
                                        r_val = int(org_model.redacted_members)
                                except: r_val = "???"
                                
                            # Résumé des effectifs
                            summary = f"\n   TOTAL: {count:<4} | VISIBLE: {len(members):<4} | REDACTED: {r_val}\n"
                            self.org_results.insert("end", summary, "bold")
                    except Exception as e:
                        self.org_results.insert("end", f"   [!] Roster error: {e}\n", "warning")

                # --- [BLOC 3 : DESCRIPTION / MANIFEST] ---
                self.org_results.insert("end", "   " + "-"*45 + "\n", "separator")
                if org_model and org_model.description and org_model.description.strip():
                    desc = org_model.description[:200] + "..." if len(org_model.description) > 200 else org_model.description
                    self.org_results.insert("end", "   DESCRIPTION / MANIFEST:\n", "notes_label")
                    self.org_results.insert("end", f"   {desc}\n", "notes_text")
                else:
                    self.org_results.insert("end", "   DESCRIPTION / MANIFEST: No data.\n", "small_info")
                
                # --- [BLOC 4 : DIPLOMATIE & NOTES] ---
                self.org_results.insert("end", "   " + "-"*45 + "\n", "separator")
                
                if org_model:
                    # Diplomatie
                    self.org_results.insert("end", "   ALLIES: ", "info_label")
                    self.org_results.insert("end", f"{org_model.allies or 'NONE'}\n")
                    
                    self.org_results.insert("end", "   ENEMIES: ", "warning_label")
                    self.org_results.insert("end", f"{org_model.enemies or 'NONE'}\n")

                    # Journal notes (3 dernieres) + fallback legacy description
                    notes = self.controller.org.get_org_notes(sid, limit=3)
                    if notes:
                        self.org_results.insert("end", "\n   JOURNAL NOTES :\n", ("notes_label", tag_notes))
                        for note_id, note_text, created_at in notes:
                            compact = note_text[:120] + "..." if len(note_text) > 120 else note_text
                            self.org_results.insert("end", f"   - #{note_id} {created_at}: {compact}\n", ("notes_text", tag_notes))
                    else:
                        self.org_results.insert("end", "\n   JOURNAL NOTES: No data.\n", ("small_info", tag_notes))
                
                self.org_results.insert("end", "   " + "-"*45 + "\n", "separator")

                # --- SÉPARATEUR FINAL ENTRE LES ORGAS ---
                self.org_results.insert("end", f"{'='*60}\n\n")

                # --- BINDINGS ---
                self.org_results.tag_bind(tag_name_click, "<Button-1>", lambda e, s=sid: self.edit_org_window(s))   
                self.org_results.tag_bind(tag_link, "<Button-1>", lambda e, s=sid: self.open_org(s))
                self.org_results.tag_bind(tag_notes, "<Button-1>", lambda e, s=sid: self.open_org_notes_manager(s))
                self.org_results.tag_bind(tag_notes, "<Enter>", lambda e: self.org_results.configure(cursor="hand2"))
                self.org_results.tag_bind(tag_notes, "<Leave>", lambda e: self.org_results.configure(cursor="arrow"))

    def setup_tags(self):
        self.results.tag_config("link", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("link_org", foreground=DrakeConfig.TEXT_SECONDARY, underline=True)
        self.results.tag_config("link_rsi", foreground="#00aaff", underline=True)
        self.results.tag_config("ship_name_white", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("ALLY", foreground="#00FF00")
        self.results.tag_config("ENEMY", foreground=DrakeConfig.ACCENT_ERROR)
        self.results.tag_config("NEUTRAL", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("open_contract", foreground=DrakeConfig.ACCENT_PRIMARY)
        self.results.tag_config("closed_contract", foreground="green")

        self.org_results.tag_config("ACCENT", foreground="#ff8c00")
        self.org_results.tag_config("link_org", foreground=DrakeConfig.TEXT_SECONDARY, underline=True)
        self.org_results.tag_config("NEUTRAL", foreground="white")
        self.org_results.tag_config("ENEMY", foreground="#ff4444")
        self.org_results.tag_config("ALLY", foreground="#00FF00")

        for k in ["link", "link_org", "link_rsi"]:
            self.results.tag_bind(k, "<Enter>", lambda e: self.results.configure(cursor="hand2"))
            self.results.tag_bind(k, "<Leave>", lambda e: self.results.configure(cursor="arrow"))

    def open_rsi(self, pseudo):
        self._log(f"Opening RSI profile: {pseudo}")
        webbrowser.open(f"https://robertsspaceindustries.com/citizens/{pseudo}")

    def open_org(self, sid):
        if sid and sid != "N/A":
            # Nettoyage au cas où (espaces ou crochets)
            clean_sid = str(sid).strip().replace("[", "").replace("]", "")
            self._log(f"Opening RSI organization: {clean_sid}")
            webbrowser.open(f"https://robertsspaceindustries.com/orgs/{clean_sid}")

    def open_player_notes_manager(self, pseudo, parent=None):
        """Fenetre dediee pour gerer les notes Intel d'une cible."""
        owner = parent if parent is not None else self
        toplevel = DrakeConfig.create_modal_window(
            parent=owner,
            title=f"DRAKE - PLAYER INTEL: {pseudo}",
            geometry="620x560",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )

        ctk.CTkLabel(
            toplevel,
            text=f"INTEL JOURNAL: {pseudo}",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=10)

        add_frame = ctk.CTkFrame(
            toplevel,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        new_note_box = ctk.CTkTextbox(
            add_frame,
            height=100,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        new_note_box.pack(fill="x", padx=10, pady=(10, 8))

        journal_list = ctk.CTkScrollableFrame(
            toplevel,
            label_text="REGISTERED INTEL NOTES",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        journal_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        editing = {"id": None}

        def start_player_note_edit(note_id: int) -> None:
            editing["id"] = note_id
            refresh_note_journal()

        def cancel_player_note_edit() -> None:
            editing["id"] = None
            refresh_note_journal()

        def save_player_note_inline(note_id: int, edit_box) -> None:
            new_text = edit_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.scanner.update_player_note(pseudo, note_id, new_text)
            editing["id"] = None
            refresh_note_journal()
            self.run_scan(None)

        def delete_player_note(note_id: int) -> None:
            confirm = DrakePopup.yesno("CONFIRMATION", f"Delete note #{note_id}?", parent=toplevel)
            if not confirm:
                return
            self.controller.scanner.delete_player_note(pseudo, note_id)
            refresh_note_journal()
            self.run_scan(None)

        def refresh_note_journal() -> None:
            for child in journal_list.winfo_children():
                child.destroy()

            notes = self.controller.scanner.get_player_notes(pseudo, limit=100)
            if notes:
                for note_id, note_text, created_at in notes:
                    is_editing = note_id == editing["id"]
                    row = ctk.CTkFrame(
                        journal_list,
                        fg_color=DrakeConfig.BG_PANEL,
                        corner_radius=0,
                        border_width=1,
                        border_color=DrakeConfig.ACCENT_PRIMARY if is_editing else DrakeConfig.BORDER_COLOR,
                    )
                    row.pack(fill="x", padx=4, pady=4)

                    top = ctk.CTkFrame(row, fg_color="transparent")
                    top.pack(fill="x", padx=6, pady=(6, 2))

                    ctk.CTkLabel(
                        top,
                        text=f"#{note_id} [{created_at}]",
                        font=("Segoe UI", 10, "bold"),
                        text_color=DrakeConfig.ACCENT_PRIMARY,
                    ).pack(side="left")

                    if is_editing:
                        edit_box = ctk.CTkTextbox(
                            row,
                            height=80,
                            fg_color=DrakeConfig.BG_TERMINAL,
                            border_color=DrakeConfig.BORDER_COLOR,
                            border_width=1,
                        )
                        edit_box.insert("0.0", note_text)
                        edit_box.pack(fill="x", padx=8, pady=(4, 4))

                        btn_row = ctk.CTkFrame(row, fg_color="transparent")
                        btn_row.pack(fill="x", padx=8, pady=(0, 8))

                        DrakeButton(
                            btn_row,
                            text="SAVE",
                            width=80,
                            height=26,
                            command=lambda nid=note_id, eb=edit_box: save_player_note_inline(nid, eb),
                        ).pack(side="left", padx=(0, 6))

                        DrakeButton(
                            btn_row,
                            text="CANCEL",
                            width=80,
                            height=26,
                            fg_color="transparent",
                            border_width=1,
                            border_color=DrakeConfig.BORDER_COLOR,
                            command=cancel_player_note_edit,
                        ).pack(side="left")
                    else:
                        DrakeButton(
                            top,
                            text="EDIT",
                            width=90,
                            height=26,
                            command=lambda nid=note_id: start_player_note_edit(nid),
                        ).pack(side="right", padx=(4, 0))

                        DrakeButton(
                            top,
                            text="DELETE",
                            width=90,
                            height=26,
                            fg_color="#8b2c2c",
                            hover_color="#a63a3a",
                            command=lambda nid=note_id: delete_player_note(nid),
                        ).pack(side="right", padx=(4, 0))

                        ctk.CTkLabel(
                            row,
                            text=note_text,
                            justify="left",
                            anchor="w",
                            wraplength=520,
                            text_color=DrakeConfig.TEXT_MAIN,
                            font=("Segoe UI", 10),
                        ).pack(fill="x", padx=8, pady=(0, 8))
            else:
                ctk.CTkLabel(
                    journal_list,
                    text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")

        def add_note() -> None:
            new_text = new_note_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.scanner.add_player_note(pseudo, new_text)
            new_note_box.delete("0.0", "end")
            refresh_note_journal()
            self.run_scan(None)

        DrakeButton(add_frame, text="ADD NOTE", command=add_note, height=34).pack(fill="x", padx=10, pady=(0, 10))

        DrakeButton(
            toplevel,
            text="SAVE",
            border_width=1,
            command=toplevel.destroy,
        ).pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        refresh_note_journal()

    def open_org_notes_manager(self, sid, parent=None):
        """Fenetre dediee pour gerer les notes Intel d'une organisation."""
        owner = parent if parent is not None else self
        toplevel = DrakeConfig.create_modal_window(
            parent=owner,
            title=f"DRAKE - ORG INTEL: {sid}",
            geometry="620x560",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )

        ctk.CTkLabel(
            toplevel,
            text=f"ORG INTEL JOURNAL: {sid}",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=10)

        add_frame = ctk.CTkFrame(
            toplevel,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        new_note_box = ctk.CTkTextbox(
            add_frame,
            height=100,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        new_note_box.pack(fill="x", padx=10, pady=(10, 8))

        journal_list = ctk.CTkScrollableFrame(
            toplevel,
            label_text="REGISTERED ORG NOTES",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        journal_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        editing_org = {"id": None}

        def start_org_note_edit(note_id: int) -> None:
            editing_org["id"] = note_id
            refresh_org_journal()

        def cancel_org_note_edit() -> None:
            editing_org["id"] = None
            refresh_org_journal()

        def save_org_note_inline(note_id: int, edit_box) -> None:
            new_text = edit_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.org.update_org_note(sid, note_id, new_text)
            editing_org["id"] = None
            refresh_org_journal()
            self.run_org_scan(None)

        def delete_org_note(note_id: int) -> None:
            confirm = DrakePopup.yesno("CONFIRMATION", f"Delete org note #{note_id}?", parent=toplevel)
            if not confirm:
                return
            self.controller.org.delete_org_note(sid, note_id)
            refresh_org_journal()
            self.run_org_scan(None)

        def refresh_org_journal() -> None:
            for child in journal_list.winfo_children():
                child.destroy()

            notes = self.controller.org.get_org_notes(sid, limit=100)
            if notes:
                for note_id, note_text, created_at in notes:
                    is_editing = note_id == editing_org["id"]
                    row = ctk.CTkFrame(
                        journal_list,
                        fg_color=DrakeConfig.BG_PANEL,
                        corner_radius=0,
                        border_width=1,
                        border_color=DrakeConfig.ACCENT_PRIMARY if is_editing else DrakeConfig.BORDER_COLOR,
                    )
                    row.pack(fill="x", padx=4, pady=4)

                    top = ctk.CTkFrame(row, fg_color="transparent")
                    top.pack(fill="x", padx=6, pady=(6, 2))

                    ctk.CTkLabel(
                        top,
                        text=f"#{note_id} [{created_at}]",
                        font=("Segoe UI", 10, "bold"),
                        text_color=DrakeConfig.ACCENT_PRIMARY,
                    ).pack(side="left")

                    if is_editing:
                        edit_box = ctk.CTkTextbox(
                            row,
                            height=80,
                            fg_color=DrakeConfig.BG_TERMINAL,
                            border_color=DrakeConfig.BORDER_COLOR,
                            border_width=1,
                        )
                        edit_box.insert("0.0", note_text)
                        edit_box.pack(fill="x", padx=8, pady=(4, 4))

                        btn_row = ctk.CTkFrame(row, fg_color="transparent")
                        btn_row.pack(fill="x", padx=8, pady=(0, 8))

                        DrakeButton(
                            btn_row,
                            text="SAVE",
                            width=80,
                            height=26,
                            command=lambda nid=note_id, eb=edit_box: save_org_note_inline(nid, eb),
                        ).pack(side="left", padx=(0, 6))

                        DrakeButton(
                            btn_row,
                            text="CANCEL",
                            width=80,
                            height=26,
                            fg_color="transparent",
                            border_width=1,
                            border_color=DrakeConfig.BORDER_COLOR,
                            command=cancel_org_note_edit,
                        ).pack(side="left")
                    else:
                        DrakeButton(
                            top,
                            text="EDIT",
                            width=90,
                            height=26,
                            command=lambda nid=note_id: start_org_note_edit(nid),
                        ).pack(side="right", padx=(4, 0))

                        DrakeButton(
                            top,
                            text="DELETE",
                            width=90,
                            height=26,
                            fg_color="#8b2c2c",
                            hover_color="#a63a3a",
                            command=lambda nid=note_id: delete_org_note(nid),
                        ).pack(side="right", padx=(4, 0))

                        ctk.CTkLabel(
                            row,
                            text=note_text,
                            justify="left",
                            anchor="w",
                            wraplength=520,
                            text_color=DrakeConfig.TEXT_MAIN,
                            font=("Segoe UI", 10),
                        ).pack(fill="x", padx=8, pady=(0, 8))
            else:
                ctk.CTkLabel(
                    journal_list,
                    text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")

        def add_note() -> None:
            new_text = new_note_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.org.add_org_note(sid, new_text)
            new_note_box.delete("0.0", "end")
            refresh_org_journal()
            self.run_org_scan(None)

        DrakeButton(add_frame, text="ADD NOTE", command=add_note, height=34).pack(fill="x", padx=10, pady=(0, 10))

        DrakeButton(
            toplevel,
            text="SAVE",
            border_width=1,
            command=toplevel.destroy,
        ).pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        refresh_org_journal()

    def edit_player_window(self, pseudo):
        """Fenêtre d'édition — HANDLE et CREATION en lecture seule."""
        toplevel = DrakeConfig.create_modal_window(
            parent=self,
            title=f"EDIT FILE: {pseudo}",
            geometry="700x700",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )

        row = self.controller.scanner.get_player_full(pseudo)
        if not row:
            return
        d = row[0]

        ctk.CTkLabel(toplevel, text=f"EDIT IFF DATA: {pseudo}", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=12)

        frame = ctk.CTkScrollableFrame(toplevel, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        meta = ctk.CTkFrame(frame, fg_color="transparent")
        meta.pack(fill="x", pady=6)
        ctk.CTkLabel(meta, text="HANDLE", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        handle_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        handle_entry.insert(0, str(pseudo).upper())
        handle_entry.configure(state="disabled")
        handle_entry.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkLabel(meta, text="CREATION", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        creation_val = d[13] if len(d) > 13 else (d[6] if len(d) > 6 else "")
        created_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        created_entry.insert(0, creation_val)
        created_entry.configure(state="disabled")
        created_entry.pack(side="left", fill="x", expand=True, padx=6)

        def field(parent, label, value):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=label.upper(), font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
            e = DrakeEntry(f, fg_color=DrakeConfig.BG_TERMINAL, border_width=1, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
            e.insert(0, str(value) if value not in [None, "None"] else "")
            e.pack(side="right", fill="x", expand=True, padx=8, pady=6)
            return e

        e_org = field(frame, "Organization", d[1] if len(d) > 1 else "")
        e_sid = field(frame, "SID", d[11] if len(d) > 11 else "")
        e_rank = field(frame, "Orga Rank", d[12] if len(d) > 12 else "")
        e_ship = field(frame, "Ship", d[2] if len(d) > 2 else "")

        threat_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        threat_f.pack(fill="x", pady=4)
        ctk.CTkLabel(threat_f, text="THREAT", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        e_threat = DrakeComboBox(threat_f, values=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        e_threat.set(str(d[3]).upper() if len(d) > 3 and d[3] else "THREAT LEVEL")
        e_threat.pack(side="right", fill="x", expand=True, padx=8)

        align_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        align_f.pack(fill="x", pady=4)
        ctk.CTkLabel(align_f, text="ALIGNMENT", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        e_align = DrakeComboBox(align_f, values=["NEUTRAL", "ALLY", "ENEMY"])
        e_align.set(d[8] if len(d) > 8 and d[8] else "ALIGNMENT")
        e_align.pack(side="right", fill="x", expand=True, padx=8)

        pvp_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        pvp_f.pack(fill="x", pady=4)
        ctk.CTkLabel(pvp_f, text="PVP LEVEL", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        e_pvp = DrakeComboBox(pvp_f, values=["NOOB", "APPRENTICE", "NORMAL", "VETERAN", "AS"])
        e_pvp.set(str(d[9]).upper() if len(d) > 9 and d[9] else "PVP LEVEL")
        e_pvp.pack(side="right", fill="x", expand=True, padx=8)

        activity_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        activity_f.pack(fill="x", pady=4)
        ctk.CTkLabel(activity_f, text="ACTIVITY", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        e_activity = DrakeComboBox(activity_f, values=["MINEUR", "PIRATE", "COMMERÇANT", "CHASSEUR", "MERCENAIRE", "EXPLORATEUR", "INDUSTRIEL", "MIXTE"])
        e_activity.set(str(d[10]).upper() if len(d) > 10 and d[10] else "ACTIVITY")
        e_activity.pack(side="right", fill="x", expand=True, padx=8)
        e_lang = field(frame, "Language", d[14] if len(d) > 14 else "")

        ctk.CTkLabel(frame, text="INTEL JOURNAL", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(10, 2), padx=8)
        journal_list = ctk.CTkScrollableFrame(
            frame,
            height=210,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        journal_list.pack(fill="x", padx=8, pady=(0, 8))

        def refresh_note_journal() -> None:
            for child in journal_list.winfo_children():
                child.destroy()

            notes = self.controller.scanner.get_player_notes(pseudo, limit=100)
            if notes:
                for note_id, note_text, created_at in notes:
                    row = ctk.CTkFrame(journal_list, fg_color=DrakeConfig.BG_PANEL)
                    row.pack(fill="x", padx=4, pady=4)

                    top = ctk.CTkFrame(row, fg_color="transparent")
                    top.pack(fill="x", padx=6, pady=(6, 2))

                    ctk.CTkLabel(
                        top,
                        text=f"#{note_id} [{created_at}]",
                        font=("Segoe UI", 10, "bold"),
                        text_color=DrakeConfig.ACCENT_PRIMARY,
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row,
                        text=note_text,
                        justify="left",
                        anchor="w",
                        wraplength=560,
                        text_color=DrakeConfig.TEXT_MAIN,
                        font=("Segoe UI", 10),
                    ).pack(fill="x", padx=8, pady=(0, 8))
            elif len(d) > 4 and d[4]:
                ctk.CTkLabel(
                    journal_list,
                    text=f"[{d[5] if len(d) > 5 else 'N/A'}]\n{d[4]}",
                    justify="left",
                    anchor="w",
                    wraplength=560,
                    text_color=DrakeConfig.TEXT_MAIN,
                ).pack(fill="x", padx=8, pady=8)
            else:
                ctk.CTkLabel(
                    journal_list,
                    text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")

        refresh_note_journal()

        DrakeButton(
            frame,
            text="MANAGE NOTES",
            command=lambda: self.open_target_notes_manager(pseudo, parent=toplevel),
            height=34,
        ).pack(fill="x", padx=8, pady=(0, 8))

        def save_all():
            main_win = self.winfo_toplevel()
            try:
                # Récupération des données
                data = {
                    "org": e_org.get().upper(),
                    "sid": e_sid.get().upper(),
                    "org_rank": e_rank.get().upper(),
                    "ship": e_ship.get().upper(),
                    "threat": e_threat.get(),
                    "alignment": e_align.get(),
                    "pvp_lvl": e_pvp.get(),
                    "activity": e_activity.get(),
                    "language": e_lang.get(),
                }
                
                # Exécution
                self.controller.scanner.update_player(pseudo, **data)
                
                # IMPORTANT : On rafraîchit d'abord
                self.run_scan(None)
                refresh_note_journal()
                
                # On ferme la fenêtre AVANT de lancer le popup 
                # (cela évite les conflits de focus/grab qui font planter l'app)
                toplevel.grab_release()
                
                # Le popup de succès s'affiche sur la fenêtre principale
                DrakePopup.info("SYSTEMS", f"File for {pseudo} synchronized.", parent=main_win)
                self._log(f"Target synchronized: {pseudo}")

            except Exception as e:
                # On affiche l'erreur sans fermer pour pouvoir copier le message
                self._log(f"Target sync failed {pseudo}: {e}", source="ERROR")
                DrakePopup.error("SQL ERROR", f"Details: {e}", parent=main_win)

        
        btn_cancel = DrakeButton(
            toplevel, 
            text="CANCEL", 
            fg_color="transparent", 
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR, 
            command=toplevel.destroy
        )
        btn_cancel.pack(side="bottom", fill="x", padx=20, pady=(0, 20)) # pady=(Top, Bottom)

        # 2. On place le bouton SAVE juste au-dessus
        btn_save = DrakeButton(
            toplevel, 
            text="SAVE CHANGES", 
            command=save_all, 
            height=40
        )
        btn_save.pack(side="bottom", fill="x", padx=20, pady=(10, 5))

    def run_scan(self, event):
        q = self.search_entry.get().strip().upper()
        self.results.delete("0.0", "end")

        if len(q) > 1:
            players = self.controller.scanner.search_players_as_models(q)

            if not players:
                return

            for t in players:
                # Tags pour les liens cliquables
                tag_p, tag_o, tag_r, tag_i = f"tp_{t.pseudo}", f"to_{t.pseudo}", f"tr_{t.pseudo}", f"ti_{t.pseudo}"

                # --- [BLOC 1 : ENTÊTE IDENTITÉ] ---
                self.results.insert("end", " ■ ", t.alignment)
                self.results.insert("end", f"{t.pseudo}", ("link", tag_p))

                org_val = (t.org or "")
                org_norm = str(org_val).strip().upper().replace("[", "").replace("]", "")
                is_valid_org = bool(org_norm) and not (
                    org_norm.startswith("NONE") or org_norm == "INCONNU" or org_norm == "UNKNOWN"
                )

                if is_valid_org:
                    self.results.insert("end", "[")
                    self.results.insert("end", f"{org_val}/{t.sid or 'N/A'}", ("link_org", tag_o))
                    self.results.insert("end", "]")
                else:
                    self.results.insert("end", " [NO ORG]")

                self.results.insert("end", " [")
                self.results.insert("end", "RSI", ("link_rsi", tag_r))
                self.results.insert("end", "]\n")
                
                # --- [BLOC 2 : INFOS TECHNIQUES] ---
                ratio = f"{t.pvp_ratio():.2f}"
                self.results.insert("end", "   SHIP: ")
                self.results.insert("end", f"{t.ship or 'INC'}", "ship_name_white")
                self.results.insert("end", f" | MENACE: {t.threat} | W/L: {t.wins}/{t.losses} ({ratio})\n")
                self.results.insert("end", f"   PVP: {t.pvp_lvl} | ACTIVITÉ: {t.activity} | LANG: {t.language}\n")

                # --- [BLOC 3 : NOTES / RENSEIGNEMENTS] ---
                self.results.insert("end", "   " + "-"*45 + "\n", "separator")
                notes = self.controller.scanner.get_player_notes(t.pseudo, limit=3)
                if notes:
                    self.results.insert("end", "   INTEL:\n", ("notes_label", tag_i))
                    for note_id, note_text, created_at in notes:
                        self.results.insert("end", f"   - #{note_id} {created_at}: {note_text}\n", ("notes_text", tag_i))
                elif t.notes and t.notes.strip():
                    self.results.insert("end", f"   INTEL ({t.date}):\n", ("notes_label", tag_i))
                    self.results.insert("end", f"   {t.notes}\n", ("notes_text", tag_i))
                else:
                    self.results.insert("end", "   INTEL: No data.\n", ("small_info", tag_i))
                self.results.insert("end", "   " + "-"*45 + "\n", "separator")

                # --- [BLOC 4 : CONTRATS (DÉTAILLÉ)] ---
                try:
                    target_contracts = self.controller.contract.get_contracts_for_target(t.pseudo)
                    client_contracts = self.controller.contract.get_contracts_for_client(t.pseudo)

                    if target_contracts or client_contracts:
                        t_open   = sum(1 for c in target_contracts if c[4] != "CLOSED")
                        t_closed = sum(1 for c in target_contracts if c[4] == "CLOSED")
                        c_open   = sum(1 for c in client_contracts if c[4] != "CLOSED")
                        c_closed = sum(1 for c in client_contracts if c[4] == "CLOSED")

                        self.results.insert("end", f"   CONTRACT HISTORY: TARGET(O:{t_open} C:{t_closed}) | CLIENT(O:{c_open} C:{c_closed})\n")

                        # Section : Joueur est la Cible
                        if target_contracts:
                            self.results.insert("end", "      -> As TARGET:\n")
                            for c in target_contracts:
                                status, reward, ctype, client = c[4], format_int_with_dots(c[3]), c[7], c[2]
                                icon = "✔" if status == "CLOSED" else "○"
                                tag = "closed_contract" if status == "CLOSED" else "open_contract"
                                self.results.insert("end", f"         {icon} # {status} | {ctype} | Client: {client} | {reward} aUEC\n", (tag,))

                        # Section : Joueur est le Client
                        if client_contracts:
                            self.results.insert("end", "      -> As CLIENT:\n")
                            for c in client_contracts:
                                target_c, reward, status, ctype = c[1], format_int_with_dots(c[3]), c[4], c[7]
                                icon = "✔" if status == "CLOSED" else "○"
                                tag = "closed_contract" if status == "CLOSED" else "open_contract"
                                self.results.insert("end", f"         {icon} # {status} | {ctype} | Target: {target_c} | {reward} aUEC\n", (tag,))
                    else:
                            self.results.insert("end", "   CONTRACTS: No history found.\n", "small_info")

                except Exception as e:
                    self._log(f"Contract display error for {t.pseudo}: {e}", source="ERROR")

                # Séparateur final de cible
                self.results.insert("end", f"{'='*60}\n")

                # --- BINDINGS ---
                self.results.tag_bind(tag_p, "<Button-1>", lambda e, p=t.pseudo: self.edit_player_window(p))
                if is_valid_org:
                    self.results.tag_bind(tag_o, "<Button-1>", lambda e, s=t.sid: self.open_org(s))
                self.results.tag_bind(tag_r, "<Button-1>", lambda e, p=t.pseudo: self.open_rsi(p))
                self.results.tag_bind(tag_i, "<Button-1>", lambda e, p=t.pseudo: self.open_player_notes_manager(p))
                self.results.tag_bind(tag_i, "<Enter>", lambda e: self.results.configure(cursor="hand2"))
                self.results.tag_bind(tag_i, "<Leave>", lambda e: self.results.configure(cursor="arrow"))

    def import_players_csv(self):
        """Import CSV strictement vers la table players."""
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return

        main_win = self.winfo_toplevel()
        try:
            with open(filename, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
            self.controller.logger.import_players_csv(rows)
            self.run_scan(None)
            DrakePopup.info("SYSTEMS", "PLAYERS IMPORT COMPLETED", parent=main_win)
            self._log(f"Players imported from {filename}", source="SCANNER")
        except Exception as e:
            self._log(f"Players import failed: {e}", source="ERROR")
            DrakePopup.error("ERROR", f"IMPORT FAILED: {e}", parent=main_win)

    def export_players_csv(self):
        """Export CSV strictement depuis la table players."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filename:
            return

        main_win = self.winfo_toplevel()
        try:
            rows = self.controller.scanner.export_players_csv()
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["pseudo", "org", "ship", "threat", "notes", "alignment"])
                for row in rows:
                    writer.writerow([row[0], row[1], row[2], row[3], row[4], row[8]])
            DrakePopup.info("SYSTEMS", "PLAYERS EXPORT COMPLETED", parent=main_win)
            self._log(f"Players exported to {filename}", source="SCANNER")
        except Exception as e:
            self._log(f"Players export failed: {e}", source="ERROR")
            DrakePopup.error("ERROR", f"EXPORT FAILED: {e}", parent=main_win)

    def import_orgs_csv(self):
        """Import CSV strictement vers la table organizations."""
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return

        main_win = self.winfo_toplevel()
        try:
            with open(filename, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
            self.controller.logger.import_organizations_csv(rows)
            self.run_org_scan(None)
            DrakePopup.info("SYSTEMS", "ORGANIZATIONS IMPORT COMPLETED", parent=main_win)
            self._log(f"Organizations imported from {filename}", source="SCANNER")
        except Exception as e:
            self._log(f"Organizations import failed: {e}", source="ERROR")
            DrakePopup.error("ERROR", f"IMPORT FAILED: {e}", parent=main_win)

    def export_orgs_csv(self):
        """Export CSV strictement depuis la table organizations."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filename:
            return

        main_win = self.winfo_toplevel()
        try:
            rows = self.controller.logger.export_organizations_csv()
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["sid", "name", "tag", "alignment"])
                writer.writerows(rows)
            DrakePopup.info("SYSTEMS", "ORGANIZATIONS EXPORT COMPLETED", parent=main_win)
            self._log(f"Organizations exported to {filename}", source="SCANNER")
        except Exception as e:
            self._log(f"Organizations export failed: {e}", source="ERROR")
            DrakePopup.error("ERROR", f"EXPORT FAILED: {e}", parent=main_win)

    def edit_org_window(self, sid):
        """Fenêtre d'édition Orga — Structure calquée sur le dossier Target."""
        toplevel = DrakeConfig.create_modal_window(
            parent=self,
            title=f"EDIT CORPORATE FILE: {sid}",
            geometry="700x800",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )

        # Récupération du modèle via le controller
        org = self.controller.org.get_org_model(sid)
        if not org:
            return

        # --- [HEADER] ---
        ctk.CTkLabel(toplevel, text=f"EDIT CORPORATE DATA: {sid}", 
                    font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=12)

        frame = ctk.CTkScrollableFrame(toplevel, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        # --- [SECTION 1 : META DATA - LECTURE SEULE] ---
        meta = ctk.CTkFrame(frame, fg_color="transparent")
        meta.pack(fill="x", pady=6)
        
        ctk.CTkLabel(meta, text="SID", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        sid_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        sid_entry.insert(0, str(sid).upper())
        sid_entry.configure(state="disabled")
        sid_entry.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkLabel(meta, text="LAST UPDATE", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        update_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        update_entry.insert(0, org.updated_at if org.updated_at else "UNKNOWN")
        update_entry.configure(state="disabled")
        update_entry.pack(side="left", fill="x", expand=True, padx=6)

        # --- [SECTION 2 : CHAMPS ÉDITABLES] ---
        def field(parent, label, value):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=label.upper(), font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
            e = DrakeEntry(f, fg_color=DrakeConfig.BG_TERMINAL, border_width=1, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
            e.insert(0, str(value) if value not in [None, "None", "NONE"] else "")
            e.pack(side="right", fill="x", expand=True, padx=8, pady=6)
            return e

        e_name = field(frame, "Org Name", org.name)
        e_tag  = field(frame, "RSI Tag", org.tag)
        e_type = field(frame, "Org Type", org.org_type)
        e_spec = field(frame, "Specialization", org.specialization)
        e_count = field(frame, "Members", org.member_count)

        # --- [SECTION 3 : ALIGNEMENT & DIPLOMATIE] ---
        # On reprend exactement le même sélecteur d'alignement que pour les Targets
        align_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        align_f.pack(fill="x", pady=4)
        ctk.CTkLabel(align_f, text="ALIGNMENT", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        
        e_align = DrakeComboBox(align_f, values=["NEUTRAL", "ALLY", "ENEMY"])
        e_align.set(org.alignment if hasattr(org, 'alignment') and org.alignment else "ALIGNMENT")
        e_align.pack(side="right", fill="x", expand=True, padx=8)

        e_allies = field(frame, "Allies", org.allies)
        e_enemies = field(frame, "Enemies", org.enemies)

        # --- [SECTION 4 : MANIFESTE LEGACY + JOURNAL NOTES] ---
        ctk.CTkLabel(frame, text="MANIFEST (LEGACY)", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(10, 2), padx=8)
        e_manifest = ctk.CTkTextbox(frame, height=90, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR, border_width=1)
        e_manifest.insert("0.0", org.description if org.description and org.description != "NONE" else "")
        e_manifest.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(frame, text="ORG INTEL JOURNAL", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(4, 2), padx=8)
        org_journal_list = ctk.CTkScrollableFrame(
            frame,
            height=200,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        org_journal_list.pack(fill="x", padx=8, pady=(0, 8))

        def refresh_org_journal() -> None:
            for child in org_journal_list.winfo_children():
                child.destroy()

            notes = self.controller.org.get_org_notes(sid, limit=100)
            if notes:
                for note_id, note_text, created_at in notes:
                    row = ctk.CTkFrame(org_journal_list, fg_color=DrakeConfig.BG_PANEL)
                    row.pack(fill="x", padx=4, pady=4)

                    top = ctk.CTkFrame(row, fg_color="transparent")
                    top.pack(fill="x", padx=6, pady=(6, 2))

                    ctk.CTkLabel(
                        top,
                        text=f"#{note_id} [{created_at}]",
                        font=("Segoe UI", 10, "bold"),
                        text_color=DrakeConfig.ACCENT_PRIMARY,
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row,
                        text=note_text,
                        justify="left",
                        anchor="w",
                        wraplength=560,
                        text_color=DrakeConfig.TEXT_MAIN,
                        font=("Segoe UI", 10),
                    ).pack(fill="x", padx=8, pady=(0, 8))
            elif org.description and org.description.strip():
                ctk.CTkLabel(
                    org_journal_list,
                    text=f"[{org.updated_at or 'N/A'}]\n{org.description}",
                    justify="left",
                    anchor="w",
                    wraplength=560,
                    text_color=DrakeConfig.TEXT_MAIN,
                ).pack(fill="x", padx=8, pady=8)
            else:
                ctk.CTkLabel(
                    org_journal_list,
                    text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")

        refresh_org_journal()

        DrakeButton(
            frame,
            text="MANAGE ORG NOTES",
            command=lambda: self.open_org_notes_manager(sid, parent=toplevel),
            height=34,
        ).pack(fill="x", padx=8, pady=(0, 8))

        # --- [SECTION 5 : SAUVEGARDE] ---
        def save_changes():
            try:
                payload = {
                    "name": e_name.get().strip(),
                    "tag": e_tag.get().strip().upper(),
                    "org_type": e_type.get().strip().upper(),
                    "specialization": e_spec.get().strip().upper(),
                    "member_count": e_count.get().strip(),
                    "alignment": e_align.get(),
                    "allies": e_allies.get().strip().upper(),
                    "enemies": e_enemies.get().strip().upper(),
                    "description": e_manifest.get("0.0", "end").strip()
                }
                
                self.controller.org.update_org(sid, **payload)
                self.run_org_scan(None) # Auto refresh
                toplevel.destroy()
                DrakePopup.info("SYSTEMS", f"Corporate file {sid} updated.")
                self._log(f"Organization synchronized: {sid}", source="ORG")
                
            except Exception as ex:
                self._log(f"Organization update failed {sid}: {ex}", source="ERROR")
                DrakePopup.error("SYNC ERROR", f"Failed: {ex}")

        # Boutons de fin — meme structure et ordre que la fenetre d'edition target
        btn_cancel = DrakeButton(
            toplevel,
            text="CANCEL",
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=toplevel.destroy,
        )
        btn_cancel.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        btn_save = DrakeButton(
            toplevel,
            text="SAVE CHANGES",
            command=save_changes,
            height=40,
        )
        btn_save.pack(side="bottom", fill="x", padx=20, pady=(10, 5))