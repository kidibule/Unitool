"""Frame Organisation — gestion dédiée des organisations.

Vue principale pour rechercher, consulter et éditer les organisations
enregistrées dans la base de données Unitool.
"""

import csv
import json
import webbrowser
from tkinter import filedialog

import customtkinter as ctk

from drake_ui.engine import (
    DrakeConfig,
    DrakeButton,
    DrakeComboBox,
    DrakeEntry,
    DrakePopup,
    DrakeTerminal,
    DrakeTitle1,
)


class OrgFrame(ctk.CTkFrame):
    """Vue dédiée à la gestion des organisations."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)
        DrakeTitle1(header, text="ORGANISATIONS").pack(side="left")

        # --- TOOLBAR ---
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 5))

        DrakeButton(
            toolbar,
            text="IMPORT CSV",
            width=150,
            command=self.import_orgs_csv,
        ).pack(side="left", padx=(0, 8))

        DrakeButton(
            toolbar,
            text="EXPORT CSV",
            width=150,
            command=self.export_orgs_csv,
        ).pack(side="left")

        # --- SEARCH BAR ---
        self.search_entry = DrakeEntry(
            self,
            placeholder_text="SEARCH AN ORG (NAME, SID OR TAG)...",
            height=40,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
        )
        self.search_entry.pack(pady=(0, 5), padx=20, fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # --- RESULTS TERMINAL ---
        self.results = DrakeTerminal(self)
        self.results.pack(pady=5, padx=20, fill="both", expand=True)

        self._setup_tags()

    # ------------------------------------------------------------------
    # Tag configuration
    # ------------------------------------------------------------------

    def _setup_tags(self):
        self.results.tag_config("ACCENT", foreground=DrakeConfig.ACCENT_PRIMARY)
        self.results.tag_config("link_org", foreground=DrakeConfig.TEXT_SECONDARY, underline=True)
        self.results.tag_config("NEUTRAL", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("ENEMY", foreground="#ff4444")
        self.results.tag_config("ALLY", foreground="#00FF00")
        self.results.tag_config("separator", foreground=DrakeConfig.BORDER_COLOR)
        self.results.tag_config("notes_label", foreground=DrakeConfig.ACCENT_PRIMARY, font=("Segoe UI", 10, "bold"))
        self.results.tag_config("notes_text", foreground=DrakeConfig.TEXT_MAIN, font=("Segoe UI", 10))
        self.results.tag_config("small_info", foreground=DrakeConfig.TEXT_SECONDARY, font=("Segoe UI", 9))
        self.results.tag_config("info_label", foreground="#00aaff", font=("Segoe UI", 10, "bold"))
        self.results.tag_config("warning_label", foreground="#ff4444", font=("Segoe UI", 10, "bold"))
        self.results.tag_config("bold", font=("Segoe UI", 10, "bold"))

        self.results.tag_bind(
            "link_org",
            "<Enter>",
            lambda e: self.results.configure(cursor="hand2"),
        )
        self.results.tag_bind(
            "link_org",
            "<Leave>",
            lambda e: self.results.configure(cursor="arrow"),
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _on_search(self, _event=None):
        q = self.search_entry.get().strip().upper()
        self.results.delete("0.0", "end")

        if len(q) < 2:
            return

        orgs = self.controller.org.search_orgs(q)
        orgs = [o for o in orgs if o[0] and len(str(o[0])) > 2]

        if not orgs:
            self.results.insert("end", "  NO MATCHING ORGANISATION FOUND.\n", "small_info")
            return

        for o in orgs:
            sid, name, tag, count, o_type, spec, alignment, updated_at = o
            tag_edit = f"edit_{sid}"
            tag_link = f"rsi_{sid}"
            tag_notes = f"notes_{sid}"

            org_model = self.controller.org.get_org_model(sid)

            # --- [IDENTITÉ] ---
            self.results.insert("end", " ■ ", alignment)
            self.results.insert("end", f"{name} ", (tag_edit, "NEUTRAL"))
            self.results.insert("end", "[")
            self.results.insert("end", f"{sid}", (tag_link, "link_org"))
            self.results.insert("end", "]\n")

            self.results.insert(
                "end",
                f"   TYPE: {o_type} | SPEC: {spec} | TAG: {tag or 'N/A'}\n",
            )
            self.results.insert(
                "end",
                f"   LAST UPDATE: {org_model.updated_at if org_model else 'UNKNOWN'}\n",
            )

            # --- [ROSTER] ---
            self.results.insert("end", "   " + "-" * 45 + "\n", "separator")

            if org_model and org_model.visible_members:
                try:
                    members = json.loads(org_model.visible_members)
                    if members:
                        self.results.insert(
                            "end",
                            f"   {'HANDLE':<25} | {'RANK':<20}\n",
                            "ACCENT",
                        )
                        self.results.insert("end", f"   {'-'*48}\n", "ACCENT")
                        for m in members[:15]:
                            h = str(m.get("h", "???")).upper()
                            r = str(m.get("r", "???")).upper()
                            self.results.insert(
                                "end", f"   {h:<25} | {r:<20}\n", "ACCENT"
                            )
                        self.results.insert("end", "   " + "-" * 45 + "\n", "separator")

                        r_val = 0
                        if org_model.redacted_members:
                            try:
                                if ":" in str(org_model.redacted_members):
                                    r_val = str(org_model.redacted_members).split(":")[-1].strip()
                                else:
                                    r_val = int(org_model.redacted_members)
                            except Exception:
                                r_val = "???"

                        summary = f"\n   TOTAL: {count:<4} | VISIBLE: {len(members):<4} | REDACTED: {r_val}\n"
                        self.results.insert("end", summary, "bold")
                except Exception as e:
                    self.results.insert("end", f"   [!] Roster error: {e}\n", "warning_label")

            # --- [DESCRIPTION] ---
            self.results.insert("end", "   " + "-" * 45 + "\n", "separator")
            if org_model and org_model.description and org_model.description.strip():
                desc = (
                    org_model.description[:200] + "..."
                    if len(org_model.description) > 200
                    else org_model.description
                )
                self.results.insert("end", "   DESCRIPTION / MANIFEST:\n", "notes_label")
                self.results.insert("end", f"   {desc}\n", "notes_text")
            else:
                self.results.insert("end", "   DESCRIPTION / MANIFEST: No data.\n", "small_info")

            # --- [DIPLOMATIE & NOTES] ---
            self.results.insert("end", "   " + "-" * 45 + "\n", "separator")
            if org_model:
                self.results.insert("end", "   ALLIES: ", "info_label")
                self.results.insert("end", f"{org_model.allies or 'NONE'}\n")

                self.results.insert("end", "   ENEMIES: ", "warning_label")
                self.results.insert("end", f"{org_model.enemies or 'NONE'}\n")

                notes = self.controller.org.get_org_notes(sid, limit=3)
                if notes:
                    self.results.insert("end", "\n   JOURNAL NOTES:\n", ("notes_label", tag_notes))
                    for note_id, note_text, created_at in notes:
                        compact = (
                            note_text[:120] + "..." if len(note_text) > 120 else note_text
                        )
                        self.results.insert(
                            "end",
                            f"   - #{note_id} {created_at}: {compact}\n",
                            ("notes_text", tag_notes),
                        )
                else:
                    self.results.insert(
                        "end", "\n   JOURNAL NOTES: No data.\n", ("small_info", tag_notes)
                    )

            self.results.insert("end", "   " + "-" * 45 + "\n", "separator")
            self.results.insert("end", f"{'='*60}\n\n")

            # --- BINDINGS ---
            self.results.tag_bind(
                tag_edit, "<Button-1>", lambda e, s=sid: self.edit_org_window(s)
            )
            self.results.tag_bind(
                tag_edit, "<Enter>", lambda e: self.results.configure(cursor="hand2")
            )
            self.results.tag_bind(
                tag_edit, "<Leave>", lambda e: self.results.configure(cursor="arrow")
            )
            self.results.tag_bind(
                tag_link, "<Button-1>", lambda e, s=sid: self._open_rsi(s)
            )
            self.results.tag_bind(
                tag_notes, "<Button-1>", lambda e, s=sid: self.open_org_notes_manager(s)
            )
            self.results.tag_bind(
                tag_notes, "<Enter>", lambda e: self.results.configure(cursor="hand2")
            )
            self.results.tag_bind(
                tag_notes, "<Leave>", lambda e: self.results.configure(cursor="arrow")
            )

    def refresh(self):
        """Rafraîchit les résultats selon la recherche courante."""
        self._on_search()

    # ------------------------------------------------------------------
    # RSI link
    # ------------------------------------------------------------------

    def _open_rsi(self, sid):
        if sid and sid != "N/A":
            clean_sid = str(sid).strip().replace("[", "").replace("]", "")
            webbrowser.open(f"https://robertsspaceindustries.com/orgs/{clean_sid}")
            self._log(f"Opening RSI org: {clean_sid}")

    # ------------------------------------------------------------------
    # CSV Import / Export
    # ------------------------------------------------------------------

    def import_orgs_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        main_win = self.winfo_toplevel()
        try:
            with open(filename, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
            self.controller.logger.import_organizations_csv(rows)
            self._on_search()
            DrakePopup.info("SYSTEMS", "ORGANIZATIONS IMPORT COMPLETED", parent=main_win)
            self._log(f"Organizations imported from {filename}")
        except Exception as e:
            self._log(f"Organizations import failed: {e}")
            DrakePopup.error("ERROR", f"IMPORT FAILED: {e}", parent=main_win)

    def export_orgs_csv(self):
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
            self._log(f"Organizations exported to {filename}")
        except Exception as e:
            self._log(f"Organizations export failed: {e}")
            DrakePopup.error("ERROR", f"EXPORT FAILED: {e}", parent=main_win)

    # ------------------------------------------------------------------
    # Edit org window
    # ------------------------------------------------------------------

    def edit_org_window(self, sid):
        """Fenêtre d'édition des données d'une organisation."""
        toplevel = DrakeConfig.create_modal_window(
            parent=self,
            title=f"EDIT CORPORATE FILE: {sid}",
            geometry="700x800",
            fg_color=DrakeConfig.BG_MAIN,
            resizable=True,
        )

        org = self.controller.org.get_org_model(sid)
        if not org:
            return

        ctk.CTkLabel(
            toplevel,
            text=f"EDIT CORPORATE DATA: {sid}",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=12)

        frame = ctk.CTkScrollableFrame(toplevel, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        # --- META (lecture seule) ---
        meta = ctk.CTkFrame(frame, fg_color="transparent")
        meta.pack(fill="x", pady=6)

        ctk.CTkLabel(
            meta, text="SID", font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY, width=120,
        ).pack(side="left", padx=6)
        sid_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        sid_entry.insert(0, str(sid).upper())
        sid_entry.configure(state="disabled")
        sid_entry.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkLabel(
            meta, text="LAST UPDATE", font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY, width=120,
        ).pack(side="left", padx=6)
        update_entry = DrakeEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        update_entry.insert(0, org.updated_at if org.updated_at else "UNKNOWN")
        update_entry.configure(state="disabled")
        update_entry.pack(side="left", fill="x", expand=True, padx=6)

        # --- Champs éditables ---
        def _field(parent, label, value):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(
                f, text=label.upper(), font=("Segoe UI", 10, "bold"),
                text_color=DrakeConfig.TEXT_SECONDARY, width=150,
            ).pack(side="left", padx=8)
            e = DrakeEntry(
                f, fg_color=DrakeConfig.BG_TERMINAL,
                border_width=1, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0,
            )
            e.insert(0, str(value) if value not in [None, "None", "NONE"] else "")
            e.pack(side="right", fill="x", expand=True, padx=8, pady=6)
            return e

        e_name = _field(frame, "Org Name", org.name)
        e_tag = _field(frame, "RSI Tag", org.tag)
        e_type = _field(frame, "Org Type", org.org_type)
        e_spec = _field(frame, "Specialization", org.specialization)
        e_count = _field(frame, "Members", org.member_count)

        # --- Alignement ---
        align_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        align_f.pack(fill="x", pady=4)
        ctk.CTkLabel(
            align_f, text="ALIGNMENT", font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY, width=150,
        ).pack(side="left", padx=8)
        e_align = DrakeComboBox(align_f, values=["NEUTRAL", "ALLY", "ENEMY"])
        e_align.set(org.alignment if hasattr(org, "alignment") and org.alignment else "NEUTRAL")
        e_align.pack(side="right", fill="x", expand=True, padx=8)

        e_allies = _field(frame, "Allies", org.allies)
        e_enemies = _field(frame, "Enemies", org.enemies)

        # --- Manifeste ---
        ctk.CTkLabel(
            frame, text="MANIFEST (LEGACY)", font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=(10, 2), padx=8)
        e_manifest = ctk.CTkTextbox(
            frame, height=90, fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR, border_width=1,
        )
        e_manifest.insert(
            "0.0",
            org.description if org.description and org.description != "NONE" else "",
        )
        e_manifest.pack(fill="x", padx=8, pady=(0, 8))

        # --- Journal notes intégré ---
        ctk.CTkLabel(
            frame, text="ORG INTEL JOURNAL", font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=(4, 2), padx=8)

        org_journal_list = ctk.CTkScrollableFrame(
            frame, height=200, fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR, border_width=1,
        )
        org_journal_list.pack(fill="x", padx=8, pady=(0, 8))

        def _refresh_journal():
            for child in org_journal_list.winfo_children():
                child.destroy()
            notes = self.controller.org.get_org_notes(sid, limit=100)
            if notes:
                for note_id, note_text, created_at in notes:
                    row_f = ctk.CTkFrame(org_journal_list, fg_color=DrakeConfig.BG_PANEL)
                    row_f.pack(fill="x", padx=4, pady=4)
                    top_f = ctk.CTkFrame(row_f, fg_color="transparent")
                    top_f.pack(fill="x", padx=6, pady=(6, 2))
                    ctk.CTkLabel(
                        top_f,
                        text=f"#{note_id} [{created_at}]",
                        font=("Segoe UI", 10, "bold"),
                        text_color=DrakeConfig.ACCENT_PRIMARY,
                    ).pack(side="left")
                    ctk.CTkLabel(
                        row_f, text=note_text, justify="left", anchor="w",
                        wraplength=560, text_color=DrakeConfig.TEXT_MAIN,
                        font=("Segoe UI", 10),
                    ).pack(fill="x", padx=8, pady=(0, 8))
            else:
                ctk.CTkLabel(
                    org_journal_list, text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")

        _refresh_journal()

        DrakeButton(
            frame,
            text="MANAGE ORG NOTES",
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=lambda: self.open_org_notes_manager(sid, parent=toplevel),
        ).pack(fill="x", padx=8, pady=(0, 12))

        # --- Save ---
        def _save():
            self.controller.org.update_org(
                sid,
                name=e_name.get().strip(),
                tag=e_tag.get().strip(),
                org_type=e_type.get().strip(),
                specialization=e_spec.get().strip(),
                member_count=e_count.get().strip(),
                alignment=e_align.get().strip(),
                allies=e_allies.get().strip(),
                enemies=e_enemies.get().strip(),
                description=e_manifest.get("0.0", "end").strip(),
            )
            self._log(f"Org {sid} saved.")
            self._on_search()
            toplevel.destroy()

        DrakeButton(toplevel, text="SAVE", command=_save).pack(
            side="bottom", fill="x", padx=20, pady=(0, 20)
        )

    # ------------------------------------------------------------------
    # Notes manager
    # ------------------------------------------------------------------

    def open_org_notes_manager(self, sid, parent=None):
        """Fenêtre dédiée pour gérer les notes Intel d'une organisation."""
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
            toplevel, fg_color=DrakeConfig.BG_PANEL, corner_radius=0,
            border_width=1, border_color=DrakeConfig.BORDER_COLOR,
        )
        add_frame.pack(fill="x", padx=20, pady=(0, 10))

        new_note_box = ctk.CTkTextbox(
            add_frame, height=100, fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR, border_width=1,
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

        editing_state = {"id": None}

        def _start_edit(note_id):
            editing_state["id"] = note_id
            _refresh()

        def _cancel_edit():
            editing_state["id"] = None
            _refresh()

        def _save_edit(note_id, edit_box):
            new_text = edit_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.org.update_org_note(sid, note_id, new_text)
            editing_state["id"] = None
            _refresh()
            self._on_search()

        def _delete_note(note_id):
            if not DrakePopup.yesno("CONFIRMATION", f"Delete org note #{note_id}?", parent=toplevel):
                return
            self.controller.org.delete_org_note(sid, note_id)
            _refresh()
            self._on_search()

        def _refresh():
            for child in journal_list.winfo_children():
                child.destroy()
            notes = self.controller.org.get_org_notes(sid, limit=100)
            if not notes:
                ctk.CTkLabel(
                    journal_list, text="No saved notes.",
                    text_color=DrakeConfig.TEXT_SECONDARY,
                ).pack(padx=8, pady=8, anchor="w")
                return

            for note_id, note_text, created_at in notes:
                is_editing = note_id == editing_state["id"]
                row_f = ctk.CTkFrame(
                    journal_list,
                    fg_color=DrakeConfig.BG_PANEL,
                    corner_radius=0,
                    border_width=1,
                    border_color=DrakeConfig.ACCENT_PRIMARY if is_editing else DrakeConfig.BORDER_COLOR,
                )
                row_f.pack(fill="x", padx=4, pady=4)

                top_f = ctk.CTkFrame(row_f, fg_color="transparent")
                top_f.pack(fill="x", padx=6, pady=(6, 2))

                ctk.CTkLabel(
                    top_f,
                    text=f"#{note_id} [{created_at}]",
                    font=("Segoe UI", 10, "bold"),
                    text_color=DrakeConfig.ACCENT_PRIMARY,
                ).pack(side="left")

                if is_editing:
                    edit_box = ctk.CTkTextbox(
                        row_f, height=80, fg_color=DrakeConfig.BG_TERMINAL,
                        border_color=DrakeConfig.BORDER_COLOR, border_width=1,
                    )
                    edit_box.insert("0.0", note_text)
                    edit_box.pack(fill="x", padx=8, pady=(4, 4))

                    btn_row = ctk.CTkFrame(row_f, fg_color="transparent")
                    btn_row.pack(fill="x", padx=8, pady=(0, 8))

                    DrakeButton(
                        btn_row, text="SAVE", width=80, height=26,
                        command=lambda nid=note_id, eb=edit_box: _save_edit(nid, eb),
                    ).pack(side="left", padx=(0, 6))

                    DrakeButton(
                        btn_row, text="CANCEL", width=80, height=26,
                        fg_color="transparent", border_width=1,
                        border_color=DrakeConfig.BORDER_COLOR,
                        command=_cancel_edit,
                    ).pack(side="left")
                else:
                    DrakeButton(
                        top_f, text="EDIT", width=90, height=26,
                        command=lambda nid=note_id: _start_edit(nid),
                    ).pack(side="right", padx=(4, 0))
                    DrakeButton(
                        top_f, text="DELETE", width=90, height=26,
                        fg_color="#8b2c2c", hover_color="#a63a3a",
                        command=lambda nid=note_id: _delete_note(nid),
                    ).pack(side="right", padx=(4, 0))
                    ctk.CTkLabel(
                        row_f, text=note_text, justify="left", anchor="w",
                        wraplength=520, text_color=DrakeConfig.TEXT_MAIN,
                        font=("Segoe UI", 10),
                    ).pack(fill="x", padx=8, pady=(0, 8))

        def _add_note():
            new_text = new_note_box.get("0.0", "end").strip()
            if not new_text:
                DrakePopup.error("ERROR", "Note cannot be empty.", parent=toplevel)
                return
            self.controller.org.add_org_note(sid, new_text)
            new_note_box.delete("0.0", "end")
            _refresh()
            self._on_search()

        DrakeButton(add_frame, text="ADD NOTE", command=_add_note, height=34).pack(
            fill="x", padx=10, pady=(0, 10)
        )
        DrakeButton(
            toplevel, text="CLOSE", border_width=1, command=toplevel.destroy,
        ).pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        _refresh()

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        try:
            if hasattr(self.controller, "log"):
                self.controller.log(message, source="ORGS")
        except Exception:
            pass
