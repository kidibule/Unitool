"""Frame responsable du scanner de cibles et de l'édition des dossiers.

Fournit une interface de recherche, d'édition et d'export des cibles
stockées dans la base via le `controller`.
"""

import customtkinter as ctk
import webbrowser
import csv

from tkinter import filedialog
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal, DrakePopup
from utils import format_int_with_dots


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

        self.btn_export = DrakeButton(header, text="EXPORT DB", command=self.export, width=100)
        self.btn_export.pack(side="right", pady=5)

        self.title_label = ctk.CTkLabel(header, text="TACTICAL SCANNER", font=("Orbitron", 16, "bold"), text_color="#ff8c00")
        self.title_label.pack(side="left", expand=True, padx=(100, 0))

        self.search_entry = ctk.CTkEntry(self, placeholder_text="ENTREZ UN NOM OU UN TAG (SID)...", height=40, fg_color=DrakeConfig.BG_PANEL, border_color=DrakeConfig.ACCENT_PRIMARY, corner_radius=DrakeConfig.CORNER_RADIUS)
        self.search_entry.pack(pady=(0, 5), padx=50, fill="x")
        self.search_entry.bind("<KeyRelease>", self.run_scan)

        self.results = DrakeTerminal(self)
        self.results.pack(pady=10, padx=20, fill="both", expand=True)

        self.setup_tags()

    def setup_tags(self):
        self.results.tag_config("link", foreground=DrakeConfig.ACCENT_PRIMARY, underline=True)
        self.results.tag_config("link_org", foreground=DrakeConfig.TEXT_SECONDARY, underline=True)
        self.results.tag_config("link_rsi", foreground="#00aaff", underline=True)
        self.results.tag_config("AMI", foreground="#00FF00")
        self.results.tag_config("ENNEMI", foreground=DrakeConfig.ACCENT_ERROR)
        self.results.tag_config("NEUTRE", foreground=DrakeConfig.TEXT_MAIN)
        self.results.tag_config("open_contract", foreground=DrakeConfig.ACCENT_PRIMARY)
        self.results.tag_config("closed_contract", foreground="green")

        for k in ["link", "link_org", "link_rsi"]:
            self.results.tag_bind(k, "<Enter>", lambda e: self.results.configure(cursor="hand2"))
            self.results.tag_bind(k, "<Leave>", lambda e: self.results.configure(cursor="arrow"))

    def open_rsi(self, pseudo):
        webbrowser.open(f"https://robertsspaceindustries.com/citizens/{pseudo}")

    def open_org(self, sid):
        if sid and sid != "N/A":
            # Nettoyage au cas où (espaces ou crochets)
            clean_sid = str(sid).strip().replace("[", "").replace("]", "")
            webbrowser.open(f"https://robertsspaceindustries.com/orgs/{clean_sid}")

    def edit_target_window(self, pseudo):
        """Fenêtre d'édition — HANDLE et CREATION en lecture seule."""
        toplevel = ctk.CTkToplevel(self)
        toplevel.title(f"MODIFICATION DOSSIER : {pseudo}")
        toplevel.geometry("700x700")
        toplevel.configure(fg_color=DrakeConfig.BG_MAIN)
        toplevel.transient(self)
        toplevel.grab_set()

        row = self.controller.scanner.get_target_full(pseudo)
        if not row:
            return
        d = row[0]

        ctk.CTkLabel(toplevel, text=f"ÉDITION DES DONNÉES IFF : {pseudo}", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(pady=12)

        frame = ctk.CTkScrollableFrame(toplevel, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        meta = ctk.CTkFrame(frame, fg_color="transparent")
        meta.pack(fill="x", pady=6)
        ctk.CTkLabel(meta, text="HANDLE", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        handle_entry = ctk.CTkEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        handle_entry.insert(0, str(pseudo).upper())
        handle_entry.configure(state="disabled")
        handle_entry.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkLabel(meta, text="CREATION", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=120).pack(side="left", padx=6)
        creation_val = d[13] if len(d) > 13 else (d[6] if len(d) > 6 else "")
        created_entry = ctk.CTkEntry(meta, fg_color=DrakeConfig.BG_TERMINAL)
        created_entry.insert(0, creation_val)
        created_entry.configure(state="disabled")
        created_entry.pack(side="left", fill="x", expand=True, padx=6)

        def field(parent, label, value):
            f = ctk.CTkFrame(parent, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=label.upper(), font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
            e = ctk.CTkEntry(f, fg_color=DrakeConfig.BG_TERMINAL, border_width=1, border_color=DrakeConfig.BORDER_COLOR, corner_radius=0)
            e.insert(0, str(value) if value not in [None, "None"] else "")
            e.pack(side="right", fill="x", expand=True, padx=8, pady=6)
            return e

        e_org = field(frame, "Organization", d[1] if len(d) > 1 else "")
        e_sid = field(frame, "SID", d[11] if len(d) > 11 else "")
        e_rank = field(frame, "Orga Rank", d[12] if len(d) > 12 else "")
        e_ship = field(frame, "Ship", d[2] if len(d) > 2 else "")
        e_threat = field(frame, "Threat", d[3] if len(d) > 3 else "")

        align_f = ctk.CTkFrame(frame, fg_color=DrakeConfig.BG_PANEL)
        align_f.pack(fill="x", pady=4)
        ctk.CTkLabel(align_f, text="ALIGNEMENT", font=("Segoe UI", 10, "bold"), text_color=DrakeConfig.TEXT_SECONDARY, width=150).pack(side="left", padx=8)
        e_align = ctk.CTkOptionMenu(align_f, values=["NEUTRE", "AMI", "ENNEMI", "PIRATE"], fg_color=DrakeConfig.BG_MAIN, button_color=DrakeConfig.ACCENT_PRIMARY, text_color="black")
        e_align.set(d[8] if len(d) > 8 and d[8] else "NEUTRE")
        e_align.pack(side="right", fill="x", expand=True, padx=8)

        e_pvp = field(frame, "PVP Level", d[9] if len(d) > 9 else "")
        e_activity = field(frame, "Activity", d[10] if len(d) > 10 else "")
        e_lang = field(frame, "Language", d[14] if len(d) > 14 else "")

        ctk.CTkLabel(frame, text="NOTES DE RENSEIGNEMENT", font=DrakeConfig.FONT_UI, text_color=DrakeConfig.ACCENT_PRIMARY).pack(anchor="w", pady=(10, 2), padx=8)
        e_notes = ctk.CTkTextbox(frame, height=120, fg_color=DrakeConfig.BG_TERMINAL, border_color=DrakeConfig.BORDER_COLOR, border_width=1)
        e_notes.insert("0.0", d[4] if len(d) > 4 and d[4] else "")
        e_notes.pack(fill="x", padx=8, pady=(0, 8))

        def save_all():
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
                    "notes": e_notes.get("0.0", "end").strip(),
                }
                
                # Exécution
                self.controller.scanner.update_target(pseudo, **data)
                
                # IMPORTANT : On rafraîchit d'abord
                self.run_scan(None)
                
                # On ferme la fenêtre AVANT de lancer le popup 
                # (cela évite les conflits de focus/grab qui font planter l'app)
                toplevel.grab_release()
                toplevel.destroy()
                
                # Le popup de succès s'affiche sur la fenêtre principale
                DrakePopup.info("DRAKE SYSTEMS", f"Dossier de {pseudo} synchronisé.")

            except Exception as e:
                # On affiche l'erreur sans fermer pour pouvoir copier le message
                print(f"DEBUG SAVE ERROR: {e}")
                DrakePopup.error("ERREUR SQL", f"Détails : {e}", parent=toplevel)

        # 2. On place le bouton DIRECTEMENT sur le toplevel, tout en bas
        btn_save = DrakeButton(toplevel, text="SAVE CHANGES", command=save_all, height=40)
        btn_save.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Petit bouton pour annuler juste en dessous (optionnel mais propre)
        btn_cancel = ctk.CTkButton(
            toplevel, 
            text="CANCEL", 
            fg_color="transparent", 
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            command=toplevel.destroy
        )
        btn_cancel.pack(fill="x", padx=20, pady=(0, 15))

    def run_scan(self, event):
        q = self.search_entry.get().strip().upper()
        self.results.delete("0.0", "end")

        if len(q) > 1:
            targets = self.controller.scanner.search_targets_as_models(q)

            if not targets:
                return

            for t in targets:
                # Tags pour les liens cliquables
                tag_p, tag_o, tag_r = f"tp_{t.pseudo}", f"to_{t.pseudo}", f"tr_{t.pseudo}"

                # Ligne principale : Pseudo et Orga
                self.results.insert("end", " ■ ", t.alignment)
                self.results.insert("end", f"{t.pseudo}", ("link", tag_p))

                # Affiche l'organisation si présente et pertinente, sinon indique [NONE] sans lien
                org_val = (t.org or "")
                org_norm = str(org_val).strip().upper().replace("[", "").replace("]", "")
                is_valid_org = bool(org_norm) and not (
                    org_norm.startswith("NONE") or org_norm == "INCONNU" or org_norm == "UNKNOWN"
                )

                if is_valid_org:
                    self.results.insert("end", " ")
                    self.results.insert("end", "[")
                    self.results.insert("end", f"{org_val}")
                    self.results.insert("end", "/")
                    self.results.insert("end", f"{t.sid or 'N/A'}", ("link_org", tag_o))
                    self.results.insert("end", "]")
                else:
                    # Aucun lien si pas d'orga publique
                    self.results.insert("end", " [NONE]")

                self.results.insert("end", " [")
                self.results.insert("end", "RSI", ("link_rsi", tag_r))
                self.results.insert("end", "]\n")
                
                # --- BLOC INFOS (DÉTAILS) ---
                self.results.insert("end", f"   VAISSEAU: {t.ship or 'INC'} | MENACE: {t.threat or '0'} | W/L: {t.wins}/{t.losses}\n")
                self.results.insert("end", f"   PVP: {t.pvp_lvl or 'N/A'} | ACTIVITÉ: {t.activity or 'N/A'} | LANG: {t.language or '??'}\n")

               # --- BLOC CONTRATS ---
                try:
                    target_contracts = self.controller.contract.get_contracts_for_target(t.pseudo)
                    client_contracts = self.controller.contract.get_contracts_for_client(t.pseudo)

                    if target_contracts or client_contracts:
                        t_open = sum(1 for c in target_contracts if c[4] != "CLOSED")
                        c_open = sum(1 for c in client_contracts if c[4] != "CLOSED")
                        
                        self.results.insert("end", f"   CONTRATS: CIBLE(O:{t_open}) | CLIENT(O:{c_open})\n")

                        # --- SECTION : JOUEUR EST LA CIBLE ---
                        if target_contracts:
                            self.results.insert("end", "    -> En tant que CIBLE:\n")
                            for c in target_contracts:
                                status, reward, ctype, client = c[4], format_int_with_dots(c[3]), c[7], c[2]
                                icon = "✔" if status == "CLOSED" else "○"
                                tag = "closed_contract" if status == "CLOSED" else "open_contract"
                                self.results.insert("end", f"       {icon} # {status} | {ctype} | Client: {client} | {reward} aUEC\n", (tag,))

                        # --- SECTION : JOUEUR EST LE COMMANDITAIRE (CLIENT) ---
                        if client_contracts:
                            self.results.insert("end", "    -> En tant que CLIENT:\n")
                            for c in client_contracts:
                                # Index : 1 = target_c, 3 = reward, 4 = status, 7 = ctype
                                target_c, reward, status, ctype = c[1], format_int_with_dots(c[3]), c[4], c[7]
                                icon = "✔" if status == "CLOSED" else "○"
                                tag = "closed_contract" if status == "CLOSED" else "open_contract"
                                self.results.insert("end", f"       {icon} # {status} | {ctype} | Cible: {target_c} | {reward} aUEC\n", (tag,))
                
                except Exception as e:
                    print(f"Erreur affichage contrats scan: {e}")

                self.results.insert("end", f"{'-'*60}\n")

                # --- BINDINGS (SÉPARÉS !) ---
                # On bind les tags créés plus haut pour les rendre cliquables
                self.results.tag_bind(tag_p, "<Button-1>", lambda e, p=t.pseudo: self.edit_target_window(p))

                # On bind le SID pour ouvrir la page RSI de l'Orga
                if is_valid_org:
                    # On passe t.sid ici, car c'est lui qui sert d'identifiant dans l'URL RSI
                    self.results.tag_bind(tag_o, "<Button-1>", lambda e, s=t.sid: self.open_org(s))

                # On bind le bouton RSI pour ouvrir le profil du citoyen
                self.results.tag_bind(tag_r, "<Button-1>", lambda e, p=t.pseudo: self.open_rsi(p))

    def export(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filename:
            try:
                rows = self.controller.scanner.export_targets_csv()
                with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(["PSEUDO", "ORGA", "SHIP", "ALIGNMENT", "NOTES"])
                    writer.writerows(rows)
                DrakePopup.info("DRAKE SYSTEMS", "EXPORTATION TERMINÉE", parent=self)
                try:
                    if hasattr(self.controller, "log"):
                        self.controller.log(f"Exported DB to {filename}", source="SCANNER")
                except Exception:
                    pass
            except Exception as e:
                DrakePopup.error("ERREUR", f"ÉCHEC DE L'EXPORT : {e}", parent=self)

