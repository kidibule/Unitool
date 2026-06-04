"""Frame Organisation — gestion dédiée des organisations.

Vue principale pour rechercher, consulter et éditer les organisations
enregistrées dans la base de données Unitool.
"""

import csv
import json
import calendar
import webbrowser
from datetime import date, datetime
from tkinter import filedialog

import customtkinter as ctk

from drake_ui.engine import (
    DrakeConfig,
    DrakeButton,
    DrakeComboBox,
    DrakeEntry,
    DrakePopup,
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
        DrakeTitle1(header, text="ORGANISATIONS").pack(anchor="center", expand=True)

        # --- TABVIEW PRINCIPAL ---
        self.tabview = DrakeConfig.create_tabview(self)

        self.tab_agenda = self.tabview.add("AGENDA")
        self.tab_membres = self.tabview.add("MEMBRES")
        self.tab_flotte = self.tabview.add("FLOTTE")

        self._setup_agenda_tab()
        self._setup_membres_tab()
        self._setup_flotte_tab()

    # ------------------------------------------------------------------
    # Onglet AGENDA
    # ------------------------------------------------------------------

    def _setup_agenda_tab(self):
        """Onglet Agenda — calendrier mensuel + gestion des événements."""
        today = date.today()
        self._cal_year  = today.year
        self._cal_month = today.month
        self._cal_selected = today

        # Layout principal : gauche = calendrier, droite = événements
        agenda_main = ctk.CTkFrame(self.tab_agenda, fg_color="transparent")
        agenda_main.pack(fill="both", expand=True, padx=10, pady=8)
        agenda_main.grid_columnconfigure(0, weight=0, minsize=320)
        agenda_main.grid_columnconfigure(1, weight=1)
        agenda_main.grid_rowconfigure(0, weight=1)

        # ── Panneau gauche : calendrier ──
        self._cal_panel = ctk.CTkFrame(
            agenda_main,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._cal_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # ── Panneau droit : événements ──
        self._evt_panel = ctk.CTkFrame(
            agenda_main,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_panel.grid(row=0, column=1, sticky="nsew")

        self._render_calendar()
        self._render_events()

    # ── Calendrier ─────────────────────────────────────────────────────

    def _render_calendar(self):
        """Reconstruit la grille du calendrier pour le mois courant."""
        for w in self._cal_panel.winfo_children():
            w.destroy()

        today = date.today()
        DAYS_FR = ["LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"]
        MONTHS_FR = [
            "", "JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN",
            "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE",
        ]

        # ── Navigation mois ──
        nav = ctk.CTkFrame(self._cal_panel, fg_color="transparent")
        nav.pack(fill="x", padx=10, pady=(10, 6))

        DrakeButton(
            nav, text="◀", width=36, height=30,
            fg_color="transparent",
            border_width=1, border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_MAIN,
            hover_color=DrakeConfig.BG_MAIN,
            command=self._cal_prev_month,
        ).pack(side="left")

        ctk.CTkLabel(
            nav,
            text=f"{MONTHS_FR[self._cal_month]}  {self._cal_year}",
            font=("Orbitron", 12, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(side="left", expand=True)

        DrakeButton(
            nav, text="▶", width=36, height=30,
            fg_color="transparent",
            border_width=1, border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_MAIN,
            hover_color=DrakeConfig.BG_MAIN,
            command=self._cal_next_month,
        ).pack(side="right")

        # ── Grille jours ──
        grid = ctk.CTkFrame(self._cal_panel, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=(0, 10))
        for col in range(7):
            grid.grid_columnconfigure(col, weight=1)

        # En-têtes de colonnes
        for col, day_name in enumerate(DAYS_FR):
            color = "#ff5555" if col >= 5 else DrakeConfig.TEXT_SECONDARY
            ctk.CTkLabel(
                grid,
                text=day_name,
                font=("Consolas", 9, "bold"),
                text_color=color,
                width=38,
                height=22,
            ).grid(row=0, column=col, padx=2, pady=(2, 4))

        # Récupère les jours qui ont des événements ce mois
        month_str = f"{self._cal_year}-{self._cal_month:02d}"
        try:
            evt_rows = self.controller.query(
                "SELECT DISTINCT date FROM org_events WHERE date LIKE ?",
                (f"{month_str}%",),
            )
            days_with_events = {r[0] for r in evt_rows}
        except Exception:
            days_with_events = set()

        # Remplissage des jours
        cal_matrix = calendar.monthcalendar(self._cal_year, self._cal_month)
        for row_i, week in enumerate(cal_matrix, start=1):
            for col_i, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(grid, text="", width=38, height=34).grid(
                        row=row_i, column=col_i, padx=2, pady=2
                    )
                    continue

                day_date = date(self._cal_year, self._cal_month, day_num)
                date_str  = day_date.strftime("%Y-%m-%d")
                is_today  = day_date == today
                is_sel    = day_date == self._cal_selected
                has_evt   = date_str in days_with_events

                if is_sel:
                    bg     = DrakeConfig.ACCENT_PRIMARY
                    fg     = DrakeConfig.BG_MAIN
                    border = DrakeConfig.ACCENT_PRIMARY
                elif is_today:
                    bg     = "transparent"
                    fg     = "#00cc55"
                    border = "#00cc55"
                else:
                    bg     = "transparent"
                    fg     = DrakeConfig.TEXT_MAIN
                    border = DrakeConfig.BORDER_COLOR

                # Bordure orange si le jour a des événements (sauf sélectionné ou aujourd'hui)
                if has_evt and not is_sel and not is_today:
                    border = "#ff8800"

                btn = ctk.CTkButton(
                    grid,
                    text=str(day_num),
                    width=38,
                    height=34,
                    font=("Consolas", 10, "bold" if is_today or is_sel else "normal"),
                    fg_color=bg,
                    text_color=fg,
                    hover_color=DrakeConfig.ACCENT_HOVER,
                    border_width=2 if has_evt and not is_sel else 1,
                    border_color=border,
                    corner_radius=2,
                    command=lambda d=day_date: self._cal_select_day(d),
                )
                btn.grid(row=row_i, column=col_i, padx=2, pady=2)

    def _cal_prev_month(self):
        if self._cal_month == 1:
            self._cal_month = 12
            self._cal_year -= 1
        else:
            self._cal_month -= 1
        self._render_calendar()

    def _cal_next_month(self):
        if self._cal_month == 12:
            self._cal_month = 1
            self._cal_year += 1
        else:
            self._cal_month += 1
        self._render_calendar()

    def _cal_select_day(self, day: date):
        self._cal_selected = day
        self._render_calendar()
        self._render_events()

    # ── Événements ─────────────────────────────────────────────────────

    def _render_events(self):
        """Reconstruit le panneau — tous les événements + formulaire pour le jour sélectionné."""
        for w in self._evt_panel.winfo_children():
            w.destroy()

        MONTHS_FR = [
            "", "JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN",
            "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE",
        ]
        d = self._cal_selected
        date_str   = d.strftime("%Y-%m-%d")
        date_label = f"{d.day:02d}  {MONTHS_FR[d.month]}  {d.year}"

        # ── Titre ──
        ctk.CTkLabel(
            self._evt_panel,
            text="TOUS LES ÉVÉNEMENTS",
            font=("Orbitron", 11, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkFrame(
            self._evt_panel, height=1,
            fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0,
        ).pack(fill="x", padx=12, pady=(0, 6))

        # ── Liste scrollable : TOUS les événements ──
        self._evt_list_frame = ctk.CTkScrollableFrame(
            self._evt_panel,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self._reload_event_list()

        # ── Séparateur formulaire ──
        ctk.CTkFrame(
            self._evt_panel, height=1,
            fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0,
        ).pack(fill="x", padx=12, pady=(0, 0))

        # ── Formulaire ajout pour le jour sélectionné ──
        add_frame = ctk.CTkFrame(
            self._evt_panel,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        add_frame.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            add_frame,
            text=f"AJOUTER POUR LE  {date_label}",
            font=("Consolas", 9, "bold"),
            text_color="#ff8800",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Ligne titre + heure
        row_th = ctk.CTkFrame(add_frame, fg_color="transparent")
        row_th.pack(fill="x", padx=10, pady=(0, 4))

        self._evt_title_entry = DrakeEntry(
            row_th,
            placeholder_text="Titre de l'événement...",
            height=34,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_title_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # Champs Heure et Minute séparés
        self._evt_hour_entry = DrakeEntry(
            row_th,
            placeholder_text="HH",
            width=46,
            height=34,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_hour_entry.pack(side="left", padx=(0, 2))
        vcmd_h = self._evt_hour_entry.register(lambda v: len(v) <= 2 and v.isdigit() or v == "")
        self._evt_hour_entry.configure(validate="key", validatecommand=(vcmd_h, "%P"))

        ctk.CTkLabel(
            row_th, text=":",
            font=("Segoe UI", 14, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            width=8,
        ).pack(side="left")

        self._evt_min_entry = DrakeEntry(
            row_th,
            placeholder_text="MM",
            width=46,
            height=34,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_min_entry.pack(side="left", padx=(2, 0))
        vcmd_m = self._evt_min_entry.register(lambda v: len(v) <= 2 and v.isdigit() or v == "")
        self._evt_min_entry.configure(validate="key", validatecommand=(vcmd_m, "%P"))

        self._evt_desc_entry = DrakeEntry(
            add_frame,
            placeholder_text="Description (optionnel)...",
            height=30,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self._evt_desc_entry.pack(fill="x", padx=10, pady=(0, 6))

        DrakeButton(
            add_frame,
            text="+ AJOUTER",
            height=32,
            command=lambda ds=date_str: self._add_event(ds),
        ).pack(fill="x", padx=10, pady=(0, 8))

        self._evt_title_entry.bind("<Return>", lambda e, ds=date_str: self._add_event(ds))

    def _reload_event_list(self):
        """Vide et recharge la liste de TOUS les événements triés par date/heure."""
        for w in self._evt_list_frame.winfo_children():
            w.destroy()

        MONTHS_FR = [
            "", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
            "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
        ]

        try:
            rows = self.controller.query(
                "SELECT id, date, time, title, description FROM org_events ORDER BY date, time, id",
                (),
            )
        except Exception:
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._evt_list_frame,
                text="Aucun événement enregistré.",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=12, pady=16)
            return

        current_date_header = None
        for evt_id, evt_date, evt_time, title, desc in rows:
            # ── Séparateur de date ──
            if evt_date != current_date_header:
                current_date_header = evt_date
                try:
                    d = date.fromisoformat(evt_date)
                    date_label = f"── {d.day:02d}  {MONTHS_FR[d.month]}  {d.year} ──"
                except Exception:
                    date_label = f"── {evt_date} ──"

                ctk.CTkLabel(
                    self._evt_list_frame,
                    text=date_label,
                    font=("Consolas", 9, "bold"),
                    text_color="#ff8800",
                    anchor="w",
                ).pack(anchor="w", padx=8, pady=(10, 2))

            # ── Carte événement (style positions) ──
            row = ctk.CTkFrame(
                self._evt_list_frame,
                fg_color=DrakeConfig.BG_PANEL,
                corner_radius=0,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
            )
            row.pack(fill="x", padx=4, pady=2)

            # Boutons — EN PREMIER pour être visibles à droite
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=8, pady=4)

            ctk.CTkButton(
                btn_frame,
                text="EDIT",
                width=52,
                height=26,
                fg_color=DrakeConfig.ACCENT_PRIMARY,
                hover_color=DrakeConfig.ACCENT_HOVER,
                text_color=DrakeConfig.BG_MAIN,
                corner_radius=2,
                font=("Segoe UI", 10, "bold"),
                border_width=0,
                command=lambda eid=evt_id, et=evt_time, et2=title, ed=desc: self._edit_event_popup(eid, et, et2, ed),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                btn_frame,
                text="DELETE",
                width=60,
                height=26,
                fg_color="transparent",
                hover_color="#330000",
                text_color="#ff4444",
                border_width=1,
                border_color="#ff4444",
                corner_radius=2,
                font=("Segoe UI", 10, "bold"),
                command=lambda eid=evt_id: self._delete_event(eid),
            ).pack(side="left")

            # Badge heure à gauche
            time_label = evt_time if evt_time else "--:--"
            ctk.CTkLabel(
                row,
                text=time_label,
                font=("Orbitron", 9, "bold"),
                text_color="#ff8800",
                width=48,
                anchor="center",
            ).pack(side="left", padx=(8, 0), pady=4)

            # Séparateur vertical
            ctk.CTkFrame(row, width=1, fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0).pack(
                side="left", fill="y", padx=6, pady=3
            )

            # Infos textuelles
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=4)

            ctk.CTkLabel(
                info,
                text=title,
                font=("Segoe UI", 11, "bold"),
                text_color=DrakeConfig.TEXT_MAIN,
                anchor="w",
            ).pack(anchor="w")

            if desc:
                ctk.CTkLabel(
                    info,
                    text=desc,
                    font=DrakeConfig.FONT_LOGS,
                    text_color=DrakeConfig.TEXT_SECONDARY,
                    anchor="w",
                ).pack(anchor="w")

    def _add_event(self, date_str: str):
        title = self._evt_title_entry.get().strip()
        if not title:
            return
        desc = self._evt_desc_entry.get().strip()
        h = self._evt_hour_entry.get().strip()
        m = self._evt_min_entry.get().strip()
        time_val = f"{h.zfill(2)}:{m.zfill(2)}" if (h or m) else ""
        try:
            self.controller.commit(
                "INSERT INTO org_events (date, time, title, description) VALUES (?, ?, ?, ?)",
                (date_str, time_val, title, desc),
            )
        except Exception as e:
            self._log(f"Erreur ajout événement : {e}")
            return
        self._evt_title_entry.delete(0, "end")
        self._evt_hour_entry.delete(0, "end")
        self._evt_min_entry.delete(0, "end")
        self._evt_desc_entry.delete(0, "end")
        self._reload_event_list()
        self._render_calendar()

    def _delete_event(self, evt_id: int):
        try:
            self.controller.commit("DELETE FROM org_events WHERE id=?", (evt_id,))
        except Exception as e:
            self._log(f"Erreur suppression événement : {e}")
            return
        self._reload_event_list()
        self._render_calendar()

    def _edit_event_popup(self, evt_id: int, current_time: str, current_title: str, current_desc: str):
        """Petit popup d'édition inline pour un événement."""
        top = ctk.CTkToplevel(self)
        top.title("MODIFIER L'ÉVÉNEMENT")
        top.geometry("420x240")
        top.resizable(False, False)
        top.configure(fg_color=DrakeConfig.BG_MAIN)
        top.grab_set()
        top.focus_set()

        ctk.CTkLabel(
            top,
            text="MODIFIER L'ÉVÉNEMENT",
            font=("Orbitron", 11, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        # Titre + heure
        row_th = ctk.CTkFrame(top, fg_color="transparent")
        row_th.pack(fill="x", padx=16, pady=(0, 6))

        e_title = DrakeEntry(row_th, placeholder_text="Titre", height=34,
                             fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR)
        e_title.insert(0, current_title or "")
        e_title.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Heure et minutes séparés dans le popup d'édition
        t_parts = (current_time or "").split(":")
        t_h = t_parts[0] if len(t_parts) >= 2 else ""
        t_m = t_parts[1] if len(t_parts) >= 2 else ""

        e_hour = DrakeEntry(row_th, placeholder_text="HH", width=46, height=34,
                            fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR)
        e_hour.insert(0, t_h)
        e_hour.pack(side="left", padx=(0, 2))
        vcmd_h = e_hour.register(lambda v: len(v) <= 2 and v.isdigit() or v == "")
        e_hour.configure(validate="key", validatecommand=(vcmd_h, "%P"))

        ctk.CTkLabel(
            row_th, text=":",
            font=("Segoe UI", 14, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            width=8,
        ).pack(side="left")

        e_min = DrakeEntry(row_th, placeholder_text="MM", width=46, height=34,
                           fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR)
        e_min.insert(0, t_m)
        e_min.pack(side="left", padx=(2, 0))
        vcmd_m = e_min.register(lambda v: len(v) <= 2 and v.isdigit() or v == "")
        e_min.configure(validate="key", validatecommand=(vcmd_m, "%P"))

        # Description
        e_desc = DrakeEntry(top, placeholder_text="Description (optionnel)", height=32,
                            fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR)
        e_desc.insert(0, current_desc or "")
        e_desc.pack(fill="x", padx=16, pady=(0, 10))

        # Boutons
        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.pack(fill="x", padx=16)

        def _save():
            new_title = e_title.get().strip()
            if not new_title:
                return
            nh = e_hour.get().strip()
            nm = e_min.get().strip()
            new_time = f"{nh.zfill(2)}:{nm.zfill(2)}" if (nh or nm) else ""
            try:
                self.controller.commit(
                    "UPDATE org_events SET title=?, time=?, description=? WHERE id=?",
                    (new_title, new_time, e_desc.get().strip(), evt_id),
                )
            except Exception as ex:
                self._log(f"Erreur édition événement : {ex}")
                return
            top.destroy()
            self._reload_event_list()
            self._render_calendar()

        DrakeButton(btns, text="ENREGISTRER", height=32, command=_save).pack(side="left", fill="x", expand=True, padx=(0, 6))
        DrakeButton(
            btns, text="ANNULER", height=32,
            fg_color="transparent", border_width=1,
            border_color=DrakeConfig.BORDER_COLOR, text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            command=top.destroy,
        ).pack(side="left", fill="x", expand=True)

        e_title.bind("<Return>", lambda e: _save())

    # ------------------------------------------------------------------
    # Onglet MEMBRES
    # ------------------------------------------------------------------

    def _setup_membres_tab(self):
        """Onglet Membres — membres de l'organisation de l'utilisateur."""
        # ── Bandeau de configuration : sélection de son org ──
        config_bar = ctk.CTkFrame(
            self.tab_membres,
            fg_color=DrakeConfig.BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        config_bar.pack(fill="x", padx=10, pady=(8, 6))

        ctk.CTkLabel(
            config_bar,
            text="MON ORG (SID) :",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(side="left", padx=(12, 8))

        self.my_org_entry = DrakeEntry(
            config_bar,
            placeholder_text="EX: SCRP",
            width=120,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
        )
        # Pré-remplir avec le SID mémorisé
        saved_sid = self.controller.get_setting("my_org_sid", "")
        if saved_sid:
            self.my_org_entry.insert(0, saved_sid)
        self.my_org_entry.pack(side="left", padx=(0, 8))

        DrakeButton(
            config_bar,
            text="DÉFINIR",
            width=90,
            height=30,
            command=self._save_my_org,
        ).pack(side="left", padx=(0, 12))

        # Label d'info de l'org courante
        self.my_org_label = ctk.CTkLabel(
            config_bar,
            text="",
            font=("Consolas", 10),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )
        self.my_org_label.pack(side="left", padx=4)

        # Barre de recherche membre
        self.member_search_entry = DrakeEntry(
            self.tab_membres,
            placeholder_text="FILTRER PAR HANDLE OU GRADE...",
            height=36,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.member_search_entry.pack(pady=(0, 4), padx=10, fill="x")
        self.member_search_entry.bind("<KeyRelease>", lambda e: self._render_members())

        # Liste scrollable des membres
        self.member_list_scroll = ctk.CTkScrollableFrame(
            self.tab_membres,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.member_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self._render_members()

    def _save_my_org(self):
        """Enregistre le SID de l'org principale et rafraîchit la liste."""
        sid = self.my_org_entry.get().strip().upper()
        if not sid:
            return
        self.controller.set_setting("my_org_sid", sid)
        self._render_members()

    def _render_members(self):
        """Reconstruit la liste des membres de l'org principale."""
        import json

        for w in self.member_list_scroll.winfo_children():
            w.destroy()

        sid = self.controller.get_setting("my_org_sid", "")
        if not sid:
            ctk.CTkLabel(
                self.member_list_scroll,
                text="⚙  Configurez d'abord le SID de votre organisation ci-dessus.",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=24)
            return

        org = self.controller.org.get_org_model(sid)
        if not org:
            ctk.CTkLabel(
                self.member_list_scroll,
                text=f"Organisation « {sid} » introuvable dans la base.",
                font=DrakeConfig.FONT_LOGS,
                text_color="#ff4444",
            ).pack(anchor="w", padx=16, pady=24)
            return

        # Mise à jour du label d'info
        self.my_org_label.configure(
            text=f"— {org.name or sid}  [{org.member_count or 0} membres]"
        )

        # Chargement des membres visibles
        try:
            members = json.loads(org.visible_members or "[]")
        except Exception:
            members = []

        # Filtre par la barre de recherche
        q = self.member_search_entry.get().strip().upper()
        if q:
            members = [
                m for m in members
                if q in str(m.get("h", "")).upper() or q in str(m.get("r", "")).upper()
            ]

        if not members:
            ctk.CTkLabel(
                self.member_list_scroll,
                text="Aucun membre visible enregistré pour cette organisation.",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=24)
            return

        # En-tête de colonne
        header = ctk.CTkFrame(
            self.member_list_scroll,
            fg_color="transparent",
            corner_radius=0,
        )
        header.pack(fill="x", padx=6, pady=(6, 2))
        ctk.CTkLabel(
            header,
            text="HANDLE",
            font=("Orbitron", 10, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
            width=220,
            anchor="w",
        ).pack(side="left", padx=8)
        ctk.CTkLabel(
            header,
            text="GRADE / RANG",
            font=("Orbitron", 10, "bold"),
            text_color=DrakeConfig.ACCENT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Séparateur
        ctk.CTkFrame(
            self.member_list_scroll, height=1,
            fg_color=DrakeConfig.BORDER_COLOR, corner_radius=0,
        ).pack(fill="x", padx=6, pady=(0, 4))

        # Cartes membres
        for m in members:
            handle = str(m.get("h", "???")).upper()
            rank   = str(m.get("r", "—"))

            card = ctk.CTkFrame(
                self.member_list_scroll,
                fg_color=DrakeConfig.BG_PANEL,
                corner_radius=0,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
            )
            card.pack(fill="x", padx=6, pady=2)

            ctk.CTkLabel(
                card,
                text=handle,
                font=("Segoe UI", 12, "bold"),
                text_color=DrakeConfig.TEXT_MAIN,
                width=220,
                anchor="w",
            ).pack(side="left", padx=12, pady=7)

            ctk.CTkLabel(
                card,
                text=rank,
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
                anchor="w",
            ).pack(side="left", pady=7)

            DrakeButton(
                card,
                text="PROFIL",
                width=65,
                height=26,
                fg_color="transparent",
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
                text_color=DrakeConfig.TEXT_SECONDARY,
                hover_color=DrakeConfig.BG_MAIN,
                command=lambda h=handle: self._open_rsi_player(h),
            ).pack(side="right", padx=8, pady=6)

    # ------------------------------------------------------------------
    # Onglet FLOTTE
    # ------------------------------------------------------------------

    def _setup_flotte_tab(self):
        """Onglet Flotte — gestion de la flotte de l'organisation."""
        ctk.CTkLabel(
            self.tab_flotte,
            text="FLOTTE",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self.tab_flotte,
            text="[ MODULE EN COURS DE DÉVELOPPEMENT ]",
            font=("Consolas", 11),
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(pady=6)

    # ------------------------------------------------------------------
    def refresh(self):
        """Rafraîchit la liste des membres."""
        self._render_members()

    # ------------------------------------------------------------------
    # RSI links
    # ------------------------------------------------------------------

    def _open_rsi(self, sid):
        if sid and sid != "N/A":
            clean_sid = str(sid).strip().replace("[", "").replace("]", "")
            webbrowser.open(f"https://robertsspaceindustries.com/orgs/{clean_sid}")
            self._log(f"Opening RSI org: {clean_sid}")

    def _open_rsi_player(self, handle):
        if handle:
            webbrowser.open(f"https://robertsspaceindustries.com/citizens/{handle}")
            self._log(f"Opening RSI profile: {handle}")

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
            self._render_members()
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
