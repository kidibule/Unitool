"""Frame responsable du scanner de cibles et de l'édition des dossiers.

Ce module fournit une interface de recherche, d'édition et d'export
des cibles stockées dans la base de données via le `controller`.
"""

import customtkinter as ctk
import webbrowser
import csv

from tkinter import filedialog, messagebox
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal

# Paramètres d'entrée réutilisables pour les widgets (utilisés dans plusieurs méthodes)
entry_kwargs = {
    "font": DrakeConfig.FONT_LOGS,
    "fg_color": DrakeConfig.BG_TERMINAL,
    "border_color": DrakeConfig.BORDER_COLOR,
    "corner_radius": 0,
    "height": 35,
}


class ScannerFrame(ctk.CTkFrame):
    """Interface de recherche et d'édition des cibles.

    Le `controller` attendu doit exposer `db` avec méthodes `query`, `cursor`,
    et `conn` pour les opérations SQL.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- HEADER (Conteneur pour Titre + Export) ---
        # On réduit le pady à (5, 0) pour coller le header en haut
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)

        # 1. On place d'abord le bouton Export à droite
        self.btn_export = DrakeButton(
            header, text="EXPORT DB", command=self.export, width=100
        )
        self.btn_export.pack(side="right", pady=5)

        # 2. On place le titre DANS le header pour qu'il soit sur la même zone
        # On utilise side="left" ou on le laisse au centre avec expand=True
        self.title_label = ctk.CTkLabel(
            header,
            text="TACTICAL SCANNER",
            font=("Orbitron", 16, "bold"),
            text_color="#ff8c00",
        )
        # L'expand=True permet de centrer le texte malgré le bouton à droite
        self.title_label.pack(side="left", expand=True, padx=(100, 0))

        # --- BARRE DE RECHERCHE ---
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="ENTREZ UN NOM OU UN TAG (SID)...",
            height=40,
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            corner_radius=DrakeConfig.CORNER_RADIUS,
        )
        # On réduit le pady ici aussi pour remonter la barre de recherche
        self.search_entry.pack(pady=(0, 5), padx=50, fill="x")
        self.search_entry.bind("<KeyRelease>", self.run_scan)

        # --- TERMINAL DE RÉSULTATS ---
        self.results = DrakeTerminal(self)
        self.results.pack(pady=10, padx=20, fill="both", expand=True)

        self.setup_tags()

    def setup_tags(self):
        """Configuration des styles de texte dans le terminal"""
        self.results.tag_config(
            "link", foreground=DrakeConfig.ACCENT_PRIMARY, underline=True
        )
        self.results.tag_config(
            "link_org", foreground=DrakeConfig.TEXT_SECONDARY, underline=True
        )
        self.results.tag_config("link_rsi", foreground="#00aaff", underline=True)
        self.results.tag_config("AMI", foreground="#00FF00")
        self.results.tag_config("ENNEMI", foreground=DrakeConfig.ACCENT_ERROR)
        self.results.tag_config("NEUTRE", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("open_contract", foreground=DrakeConfig.ACCENT_PRIMARY)
        self.results.tag_config("closed_contract", foreground="green")

        for k in ["link", "link_org", "link_rsi"]:
            self.results.tag_bind(
                k, "<Enter>", lambda e: self.results.configure(cursor="hand2")
            )
            self.results.tag_bind(
                k, "<Leave>", lambda e: self.results.configure(cursor="arrow")
            )

    def open_rsi(self, pseudo):
        webbrowser.open(f"https://robertsspaceindustries.com/citizens/{pseudo}")

    def open_org(self, org):
        if org and org != "Inconnu":
            webbrowser.open(f"https://robertsspaceindustries.com/orgs/{org}")

    def edit_target_window(self, pseudo):
        """Fenêtre d'édition complète - Style Drake Intel"""
        toplevel = ctk.CTkToplevel(self)
        toplevel.title(f"MODIFICATION DOSSIER : {pseudo}")
        toplevel.geometry("550x800")  # Légèrement plus grand pour les nouveaux champs
        toplevel.configure(fg_color=DrakeConfig.BG_MAIN)
        toplevel.transient(self)
        toplevel.grab_set()

        # On récupère TOUTES les colonnes pour être sûr
        row = self.controller.scanner.get_target_full(pseudo)
        if not row:
            return
        d = row[0]

        # Note : Si ta base de données change d'ordre,
        # il faudra adapter les index d[x] ci-dessous.

        ctk.CTkLabel(
            toplevel,
            text=f"ÉDITION DES DONNÉES IFF : {pseudo}",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=15)

        scroll_frame = ctk.CTkScrollableFrame(toplevel, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        def create_field(parent, label, default_val):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(
                f,
                text=label.upper(),
                font=("Segoe UI", 10, "bold"),
                text_color=DrakeConfig.TEXT_SECONDARY,
                width=150,
            ).pack(side="left", padx=10)
            entry = ctk.CTkEntry(
                f,
                fg_color=DrakeConfig.BG_TERMINAL,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
                corner_radius=0,
            )
            entry.insert(
                0, str(default_val) if default_val not in [None, "None", "N/A"] else ""
            )
            entry.pack(side="right", fill="x", expand=True, padx=10, pady=5)
            return entry

        # --- GÉNÉRATION DES CHAMPS (Basé sur ton run_scan) ---
        e_org = create_field(scroll_frame, "Organisation", d[1])
        e_sid = create_field(scroll_frame, "SID Tag", d[11] if len(d) > 11 else "")
        e_ship = create_field(scroll_frame, "Vaisseau", d[2])
        e_pvp = create_field(scroll_frame, "Niveau PvP", d[5])  # Colonne pvp_lvl
        e_activity = create_field(scroll_frame, "Activité", d[6])  # Colonne activity
        e_lang = create_field(scroll_frame, "Langue", d[8])  # Colonne language

        # Alignement (Menu déroulant)
        align_frame = ctk.CTkFrame(
            scroll_frame, fg_color=DrakeConfig.BG_PANEL, corner_radius=0
        )
        align_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            align_frame,
            text="ALIGNEMENT",
            font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            width=150,
        ).pack(side="left", padx=10)
        e_align = ctk.CTkOptionMenu(
            align_frame,
            values=["NEUTRE", "AMI", "ENNEMI", "PIRATE"],
            fg_color=DrakeConfig.BG_MAIN,
            button_color=DrakeConfig.ACCENT_PRIMARY,
            button_hover_color=DrakeConfig.ACCENT_HOVER,
            text_color="black",
        )
        current_align = (
            d[3] if d[3] in ["NEUTRE", "AMI", "ENNEMI", "PIRATE"] else "NEUTRE"
        )
        e_align.set(current_align)
        e_align.pack(side="right", fill="x", expand=True, padx=10)

        # Notes
        ctk.CTkLabel(
            scroll_frame,
            text="NOTES DE RENSEIGNEMENT",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(15, 5))
        e_notes = ctk.CTkTextbox(
            scroll_frame,
            height=120,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        # On suppose que les notes sont en colonne 4 (d[4])
        e_notes.insert("0.0", d[4] if d[4] else "")
        e_notes.pack(fill="x", padx=10)

        def save():
            # Préparation de la requête SQL de mise à jour complète
            # /!\ ATTENTION : Vérifie bien que les noms de colonnes correspondent à ta DB
            sql = """
                UPDATE targets 
                SET org=?, sid=?, ship=?, alignment=?, pvp_lvl=?, activity=?, language=?, notes=? 
                WHERE pseudo=?
            """
            params = (
                e_org.get(),
                e_sid.get(),
                e_ship.get(),
                e_align.get(),
                e_pvp.get(),
                e_activity.get(),
                e_lang.get(),
                e_notes.get("0.0", "end").strip(),
                pseudo,
            )

            try:
                self.controller.db.cursor.execute(sql, params)
                self.controller.db.conn.commit()
                messagebox.showinfo("DRAKE INTEL", f"Dossier de {pseudo} mis à jour.")
                toplevel.destroy()
                self.run_scan(None)  # Rafraîchit l'affichage du scanner
            except Exception as e:
                messagebox.showerror("ERREUR SQL", f"Impossible de sauvegarder : {e}")

        # Bouton de validation Drake
        DrakeButton(toplevel, text="MISE À JOUR DU DOSSIER", command=save).pack(pady=20)

        def create_labeled_entry(parent, label, default_val):
            container = ctk.CTkFrame(parent, fg_color="transparent")
            container.pack(fill="x", pady=5)
            ctk.CTkLabel(
                container,
                text=label,
                font=DrakeConfig.FONT_UI,
                text_color=DrakeConfig.ACCENT_PRIMARY,
            ).pack(anchor="w")
            e = ctk.CTkEntry(container, **entry_kwargs)
            e.insert(
                0, str(default_val) if default_val not in [None, "None", "N/A"] else ""
            )
            e.pack(fill="x", pady=2)
            return e

        # --- CHAMPS ---
        # Basé sur ton CREATE TABLE : 1:org, 2:ship, 3:threat, 11:sid, 12:org_rank, 14:language
        e_org = create_labeled_entry(scroll_frame, "ORGANIZATION", d[1])
        e_sid = create_labeled_entry(scroll_frame, "SID TAG", d[11])
        e_rank = create_labeled_entry(scroll_frame, "ORGA RANK", d[12])
        e_ship = create_labeled_entry(scroll_frame, "CURRENT SHIP", d[2])
        e_lang = create_labeled_entry(scroll_frame, "LANGUAGE", d[14])

        # Alignement (Style SegmentedButton comme ton encodage)
        ctk.CTkLabel(
            scroll_frame,
            text="ALIGNEMENT IFF",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=(10, 0))
        e_align = ctk.CTkSegmentedButton(
            scroll_frame,
            values=["AMI", "NEUTRE", "ENNEMI", "PIRATE"],
            selected_color=DrakeConfig.ACCENT_PRIMARY,
            text_color="black",
            corner_radius=0,
        )
        e_align.pack(fill="x", pady=5)
        e_align.set(d[8] if d[8] else "NEUTRE")

        # Notes
        ctk.CTkLabel(
            scroll_frame,
            text="INTEL NOTES",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(anchor="w", pady=(10, 0))
        e_notes = ctk.CTkTextbox(scroll_frame, height=120, **entry_kwargs)
        e_notes.insert("0.0", d[4] if d[4] else "")
        e_notes.pack(fill="x", pady=5)

        def save_changes():
            sql = """UPDATE targets SET 
                     org=?, ship=?, notes=?, alignment=?, sid=?, org_rank=?, language=?
                     WHERE pseudo=?"""
            params = (
                e_org.get().upper(),
                e_ship.get().upper(),
                e_notes.get("0.0", "end").strip(),
                e_align.get(),
                e_sid.get().upper(),
                e_rank.get().upper(),
                e_lang.get().upper(),
                pseudo,
            )

            self.controller.db.cursor.execute(sql, params)
            self.controller.db.conn.commit()
            messagebox.showinfo("DRAKE SYSTEMS", "ARCHIVE UPDATED")
            toplevel.destroy()
            if hasattr(self, "run_scan"):
                self.run_scan(None)

        # Bouton Action
        DrakeButton(
            toplevel, text="UPDATE INTEL CORE", command=save_changes, height=50
        ).pack(pady=20, padx=50, fill="x")

        def create_field(parent, label, default_val):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(
                f,
                text=label.upper(),
                font=("Segoe UI", 10, "bold"),
                text_color=DrakeConfig.TEXT_SECONDARY,
                width=150,
            ).pack(side="left", padx=10)
            entry = ctk.CTkEntry(
                f,
                fg_color=DrakeConfig.BG_TERMINAL,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
                corner_radius=0,
            )
            entry.insert(
                0, str(default_val) if default_val not in [None, "None", "N/A"] else ""
            )
            entry.pack(side="right", fill="x", expand=True, padx=10, pady=5)
            return entry

        # --- MAPPAGE DES CHAMPS SELON TA DB ---
        e_org = create_field(scroll_frame, "Organisation", d[1])
        e_ship = create_field(scroll_frame, "Vaisseau", d[2])
        e_threat = create_field(scroll_frame, "Menace", d[3])
        e_pvp = create_field(scroll_frame, "Niveau PvP", d[9])
        e_activity = create_field(scroll_frame, "Activité", d[10])
        e_sid = create_field(scroll_frame, "SID Tag", d[11])
        e_rank = create_field(scroll_frame, "Rang Orga", d[12])
        e_lang = create_field(scroll_frame, "Langue", d[14])

        # Alignement (Index 8 dans ta DB)
        align_frame = ctk.CTkFrame(
            scroll_frame, fg_color=DrakeConfig.BG_PANEL, corner_radius=0
        )
        align_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            align_frame,
            text="ALIGNEMENT",
            font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            width=150,
        ).pack(side="left", padx=10)
        e_align = ctk.CTkOptionMenu(
            align_frame,
            values=["NEUTRE", "AMI", "ENNEMI", "PIRATE"],
            fg_color=DrakeConfig.BG_MAIN,
            button_color=DrakeConfig.ACCENT_PRIMARY,
            text_color="black",
        )
        e_align.set(d[8])
        e_align.pack(side="right", fill="x", expand=True, padx=10)

        # Notes (Index 4 dans ta DB)
        ctk.CTkLabel(
            scroll_frame,
            text="NOTES DE RENSEIGNEMENT",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(15, 5))
        e_notes = ctk.CTkTextbox(
            scroll_frame,
            height=100,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        e_notes.insert("0.0", d[4] if d[4] else "")
        e_notes.pack(fill="x", padx=10)

        def save():
            # Mise à jour de TOUTES les colonnes modifiables
            sql = """
                UPDATE targets 
                SET org=?, ship=?, threat=?, notes=?, alignment=?, 
                    pvp_lvl=?, activity=?, sid=?, org_rank=?, language=? 
                WHERE pseudo=?
            """
            params = (
                e_org.get(),
                e_ship.get(),
                e_threat.get(),
                e_notes.get("0.0", "end").strip(),
                e_align.get(),
                e_pvp.get(),
                e_activity.get(),
                e_sid.get(),
                e_rank.get(),
                e_lang.get(),
                pseudo,
            )

            try:
                self.controller.db.cursor.execute(sql, params)
                self.controller.db.conn.commit()
                messagebox.showinfo("DRAKE SYSTEMS", f"Dossier de {pseudo} mis à jour.")
                toplevel.destroy()
                self.run_scan(None)
            except Exception as e:
                messagebox.showerror("ERREUR", f"Erreur lors de la sauvegarde : {e}")

        DrakeButton(toplevel, text="APPLIQUER LES MODIFICATIONS", command=save).pack(
            pady=20
        )

        def create_field(parent, label, row_idx, default_val):
            # Panel individuel pour chaque champ
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=2)

            ctk.CTkLabel(
                f,
                text=label.upper(),
                font=("Segoe UI", 10, "bold"),
                text_color=DrakeConfig.TEXT_SECONDARY,
                width=150,
            ).pack(side="left", padx=10)

            entry = ctk.CTkEntry(
                f,
                fg_color=DrakeConfig.BG_TERMINAL,
                border_width=1,
                border_color=DrakeConfig.BORDER_COLOR,
                corner_radius=0,
            )
            entry.insert(0, str(default_val) if default_val else "")
            entry.pack(side="right", fill="x", expand=True, padx=10, pady=5)
            return entry

        # Champs de saisie
        e_org = create_field(scroll_frame, "Organisation", 1, d[1])
        e_sid = create_field(scroll_frame, "SID Tag", 2, d[11])
        e_ship = create_field(scroll_frame, "Vaisseau", 3, d[2])

        # Alignement (OptionMenu stylisé)
        align_frame = ctk.CTkFrame(
            scroll_frame, fg_color=DrakeConfig.BG_PANEL, corner_radius=0
        )
        align_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            align_frame,
            text="ALIGNEMENT",
            font=("Segoe UI", 10, "bold"),
            text_color=DrakeConfig.TEXT_SECONDARY,
            width=150,
        ).pack(side="left", padx=10)
        e_align = ctk.CTkOptionMenu(
            align_frame,
            values=["NEUTRE", "AMI", "ENNEMI", "PIRATE"],
            fg_color=DrakeConfig.BG_MAIN,
            button_color=DrakeConfig.ACCENT_PRIMARY,
            button_hover_color=DrakeConfig.ACCENT_HOVER,
            text_color="black",
        )
        e_align.set(d[8])
        e_align.pack(side="right", fill="x", expand=True, padx=10)

        # Notes
        ctk.CTkLabel(
            scroll_frame,
            text="NOTES DE RENSEIGNEMENT",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=(15, 5))
        e_notes = ctk.CTkTextbox(
            scroll_frame,
            height=120,
            fg_color=DrakeConfig.BG_TERMINAL,
            border_color=DrakeConfig.BORDER_COLOR,
            border_width=1,
        )
        e_notes.insert("0.0", d[4] if d[4] else "")
        e_notes.pack(fill="x", padx=10)

        def save():
            sql = """UPDATE targets SET org=?, sid=?, ship=?, alignment=?, notes=? WHERE pseudo=?"""
            params = (
                e_org.get(),
                e_sid.get(),
                e_ship.get(),
                e_align.get(),
                e_notes.get("0.0", "end").strip(),
                pseudo,
            )
            self.controller.db.cursor.execute(sql, params)
            self.controller.db.conn.commit()
            toplevel.destroy()
            self.run_scan(None)

        # Bouton de validation Drake
        DrakeButton(toplevel, text="MISE À JOUR DU DOSSIER", command=save).pack(pady=20)

    def run_scan(self, event):
        q = self.search_entry.get().strip().upper()
        self.results.delete("0.0", "end")

        if len(q) > 1:
            # Utiliser le sub-controller scanner pour rechercher
            rows = self.controller.scanner.search_targets(q)

            for row in rows:
                pseudo, org, ship, align, pvp, activity, sid, enlist, lang = row
                tag_p, tag_o, tag_r = f"tp_{pseudo}", f"to_{pseudo}", f"tr_{pseudo}"

                # Affichage formaté style Console
                self.results.insert("end", " ■ ", align)
                self.results.insert("end", f"{pseudo}", ("link", tag_p))

                if org:
                    display_org = f"{org} ({sid})" if sid != "N/A" else org
                    self.results.insert("end", f" [{display_org}]", ("link_org", tag_o))

                self.results.insert("end", " ")
                self.results.insert("end", "[RSI]", ("link_rsi", tag_r))

                self.results.insert(
                    "end",
                    f"\n   VAISSEAU: {ship}\n   PVP: {pvp} | ACTIVITÉ: {activity}\n",
                )
                self.results.insert("end", f"{'-'*45}\n")

                # Bindings pour l'interactivité
                self.results.tag_bind(
                    tag_p, "<Button-1>", lambda e, p=pseudo: self.edit_target_window(p)
                )
                if org:
                    self.results.tag_bind(
                        tag_o, "<Button-1>", lambda e, o=org: self.open_org(o)
                    )
                self.results.tag_bind(
                    tag_r, "<Button-1>", lambda e, p=pseudo: self.open_rsi(p)
                )

    def export(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if filename:
            try:
                # Utiliser le sub-controller scanner pour exporter
                rows = self.controller.scanner.export_targets_csv()
                with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(["PSEUDO", "ORGA", "SHIP", "ALIGNMENT", "NOTES"])
                    writer.writerows(rows)
                messagebox.showinfo("DRAKE SYSTEMS", "EXPORTATION TERMINÉE")
            except Exception as e:
                messagebox.showerror("ERREUR", f"ÉCHEC DE L'EXPORT : {e}")
