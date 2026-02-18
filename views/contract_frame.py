"""Frame pour la gestion des contrats / bounty board."""

import customtkinter as ctk
from datetime import datetime
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal


class ContractFrame(ctk.CTkFrame):
    """Gestionnaire de contrats (ajout, fermeture, historique).

    Le `controller` doit exposer `db` avec `cursor` et `conn`.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- TITRE ---
        DrakeConfig.create_title(self, "BOUNTY BOARD")

        # --- FORMULAIRE D'AJOUT ---
        f_add = ctk.CTkFrame(
            self,
            fg_color=DrakeConfig.BG_PANEL,
            border_width=DrakeConfig.BORDER_WIDTH,
            border_color=DrakeConfig.BORDER_COLOR,
            corner_radius=0,
        )
        f_add.pack(pady=5, padx=20, fill="x")

        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "corner_radius": 0,
            "height": 30,
        }

        self.target_in = ctk.CTkEntry(
            f_add, placeholder_text="TARGET ID", width=150, **entry_kwargs
        )
        self.target_in.pack(side="left", padx=10, pady=15)

        self.client_in = ctk.CTkEntry(
            f_add, placeholder_text="CLIENT ID", width=150, **entry_kwargs
        )
        self.client_in.pack(side="left", padx=10, pady=15)

        self.reward_in = ctk.CTkEntry(
            f_add, placeholder_text="REWARD aUEC", width=120, **entry_kwargs
        )
        self.reward_in.pack(side="left", padx=10, pady=15)

        # Menu Type
        self.type_var = ctk.StringVar(value="TYPE")  # Valeur par défaut
        self.type_menu = ctk.CTkOptionMenu(
            f_add,
            variable=self.type_var,
            width=100,
            fg_color=DrakeConfig.BG_MAIN,
            button_color=DrakeConfig.BORDER_COLOR,
            button_hover_color=DrakeConfig.ACCENT_HOVER,
            text_color=DrakeConfig.TEXT_MAIN,
            dropdown_fg_color=DrakeConfig.BG_PANEL,
            dropdown_text_color=DrakeConfig.TEXT_MAIN,
            font=DrakeConfig.FONT_LOGS,
            corner_radius=0,
            values=[],  # Sera rempli par update_type_menu sans le mot "TYPE"
            command=self.apply_type,
        )
        self.type_menu.pack(side="left", padx=5)

        # Menu Priorité
        self.prio_var = ctk.StringVar(value="MEDIUM")
        self.prio_menu = ctk.CTkOptionMenu(
            f_add,
            variable=self.prio_var,
            width=100,
            fg_color=DrakeConfig.BG_MAIN,
            button_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_MAIN,
            corner_radius=0,
            values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        )
        self.prio_menu.pack(side="left", padx=5)

        # Bouton Accepter (Drake Style)
        DrakeButton(
            f_add, text="ACCEPT CONTRACT", width=150, command=self.add_contract
        ).pack(side="left", padx=15)

        # Gestion des Types (Petit bouton discret)
        ctk.CTkButton(
            self,
            text="EDIT TYPES",
            command=self.open_type_manager,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
            text_color=DrakeConfig.TEXT_SECONDARY,
            hover_color=DrakeConfig.BG_PANEL,
            width=80,
            height=20,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="ne", padx=20)

        # --- SECTION MISSIONS ACTIVES ---
        self.active_scroll = ctk.CTkScrollableFrame(
            self,
            label_text="ACTIVE MISSIONS / URGENT TASKS",
            label_font=DrakeConfig.FONT_UI,
            label_fg_color=DrakeConfig.BG_PANEL,
            label_text_color=DrakeConfig.ACCENT_PRIMARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.active_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        # --- STATS & HISTORIQUE ---
        self.stats_label = ctk.CTkLabel(
            self,
            text="TOTAL COLLECTED : 0 aUEC",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )
        self.stats_label.pack(pady=(10, 0))

        self.history_scroll = ctk.CTkScrollableFrame(
            self,
            label_text="TRANSACTION LOGS / COMPLETED",
            label_font=DrakeConfig.FONT_UI,
            label_fg_color=DrakeConfig.BG_PANEL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
            fg_color=DrakeConfig.BG_TERMINAL,
            corner_radius=0,
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        )
        self.history_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        self.refresh()
        self.update_type_menu()

    def add_contract(self):
        target = self.target_in.get().strip().upper()
        if target:
            reward = self.reward_in.get().strip()
            if not reward and self.type_var.get() != "TYPE":
                row = self.controller.db.query(
                    "SELECT reward FROM contract_types WHERE name=?",
                    (self.type_var.get(),),
                )
                if row:
                    reward = row[0][0]

            c_type = self.type_var.get()
            if c_type == "TYPE":
                c_type = None

            self.controller.db.cursor.execute(
                "INSERT INTO contracts (target, client, reward, date, status, priority, contract_type) VALUES (?,?,?,?,'OPEN',?,?)",
                (
                    target,
                    self.client_in.get().upper(),
                    reward,
                    datetime.now().strftime("%d/%m %H:%M"),
                    self.prio_var.get(),
                    c_type,
                ),
            )
            self.controller.db.conn.commit()
            self.refresh()
            self.target_in.delete(0, "end")
            self.client_in.delete(0, "end")
            self.reward_in.delete(0, "end")

    def refresh(self):
        for w in self.active_scroll.winfo_children():
            w.destroy()
        for w in self.history_scroll.winfo_children():
            w.destroy()

        total_gains = 0

        # 1. Missions OPEN
        self.controller.db.cursor.execute(
            "SELECT * FROM contracts WHERE status='OPEN' ORDER BY id DESC"
        )
        for row in self.controller.db.cursor.fetchall():
            f = ctk.CTkFrame(
                self.active_scroll, fg_color=DrakeConfig.BG_PANEL, corner_radius=0
            )
            f.pack(pady=2, fill="x", padx=5)

            prio = row[6] if len(row) > 6 else "MEDIUM"
            colors = {
                "LOW": "#aaaaaa",
                "MEDIUM": DrakeConfig.ACCENT_PRIMARY,
                "HIGH": "#ff6600",
                "CRITICAL": DrakeConfig.ACCENT_ERROR,
            }
            p_color = colors.get(prio, DrakeConfig.TEXT_MAIN)

            ctk.CTkLabel(
                f,
                text=f"[{prio[:3]}] {row[5] if row[5] else 'TASK'}",
                font=DrakeConfig.FONT_LOGS,
                text_color=p_color,
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                f,
                text=f"🎯 {row[1]} | {row[3]} aUEC",
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_MAIN,
            ).pack(side="left", padx=5)

            DrakeButton(
                f,
                text="CLOSE",
                width=60,
                height=24,
                command=lambda cid=row[0], tgt=row[1]: self.complete_contract(cid, tgt),
            ).pack(side="right", padx=10)

        # 2. Historique CLOSED
        self.controller.db.cursor.execute(
            "SELECT * FROM contracts WHERE status='CLOSED' ORDER BY id DESC"
        )
        for row in self.controller.db.cursor.fetchall():
            f = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            f.pack(pady=1, fill="x", padx=5)

            try:
                total_gains += int(str(row[3]).replace(" ", "").replace(",", ""))
            except:
                pass

            c_type = row[7] if len(row) > 7 and row[7] else "MISC"
            txt = f">> {row[5]} | COMPLETED: {row[1]} | RECEIVED: {row[3]} aUEC"
            ctk.CTkLabel(
                f,
                text=txt,
                font=DrakeConfig.FONT_LOGS,
                text_color=DrakeConfig.TEXT_SECONDARY,
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                f,
                text="[DEL]",
                fg_color="transparent",
                text_color="#444",
                hover_color=DrakeConfig.ACCENT_ERROR,
                width=20,
                height=18,
                command=lambda cid=row[0]: self.delete_history(cid),
            ).pack(side="right", padx=5)

        self.stats_label.configure(
            text=f"TOTAL COLLECTED : {total_gains:,} aUEC".replace(",", " ")
        )

    def complete_contract(self, cid, target):
        self.controller.db.cursor.execute(
            "UPDATE contracts SET status='CLOSED' WHERE id=?", (cid,)
        )
        # On met à jour les stats de la cible
        self.controller.db.cursor.execute(
            "UPDATE targets SET wins = wins + 1 WHERE pseudo=?", (target,)
        )
        if self.controller.db.cursor.rowcount == 0:
            self.controller.db.cursor.execute(
                "INSERT INTO targets (pseudo, wins, date, alignment) VALUES (?,?,?,'ENNEMI')",
                (target, 1, datetime.now().strftime("%d/%m/%y")),
            )
        self.controller.db.conn.commit()
        self.refresh()
        if hasattr(self.controller, "view") and hasattr(
            self.controller.view, "refresh_intel"
        ):
            self.controller.view.refresh_intel()

    def delete_history(self, cid):
        self.controller.db.cursor.execute("DELETE FROM contracts WHERE id=?", (cid,))
        self.controller.db.conn.commit()
        self.refresh()

    def update_type_menu(self):
        try:
            types = self.controller.db.query("SELECT name FROM contract_types")
            # On ne met QUE les noms des types, pas le mot "TYPE"
            values = [t[0] for t in types]
            self.type_menu.configure(values=values)
            self.type_var.set("TYPE")  # Mais on garde "TYPE" à l'affichage initial
        except:
            pass

    def apply_type(self, choice):
        if choice == "TYPE":
            return
        row = self.controller.db.query(
            "SELECT reward FROM contract_types WHERE name=?", (choice,)
        )
        if row:
            self.reward_in.delete(0, "end")
            self.reward_in.insert(0, row[0][0])

    def open_type_manager(self):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title("TYPE MANAGER")
        toplevel.geometry("450x400")
        toplevel.configure(fg_color=DrakeConfig.BG_MAIN)
        toplevel.transient(self)
        toplevel.grab_set()

        ctk.CTkLabel(
            toplevel,
            text="REGISTER NEW CONTRACT TYPE",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.ACCENT_PRIMARY,
        ).pack(pady=10)

        f_in = ctk.CTkFrame(toplevel, fg_color="transparent")
        f_in.pack(pady=5)

        n_entry = ctk.CTkEntry(
            f_in, placeholder_text="CODE (ex: VHRT)", fg_color=DrakeConfig.BG_TERMINAL
        )
        n_entry.pack(side="left", padx=5)
        r_entry = ctk.CTkEntry(
            f_in, placeholder_text="REWARD", width=100, fg_color=DrakeConfig.BG_TERMINAL
        )
        r_entry.pack(side="left", padx=5)

        def add():
            n, r = n_entry.get().strip().upper(), r_entry.get().strip()
            if n and r:
                try:
                    self.controller.db.commit(
                        "INSERT INTO contract_types VALUES (?,?)", (n, r)
                    )
                    refresh_list()
                    self.update_type_menu()
                    n_entry.delete(0, "end")
                    r_entry.delete(0, "end")
                except:
                    pass

        DrakeButton(f_in, text="+", width=40, command=add).pack(side="left", padx=5)

        scroll = ctk.CTkScrollableFrame(
            toplevel,
            label_text="REGISTERED TYPES",
            fg_color=DrakeConfig.BG_TERMINAL,
            label_text_color=DrakeConfig.TEXT_SECONDARY,
        )
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def delete(name):
            self.controller.db.commit(
                "DELETE FROM contract_types WHERE name=?", (name,)
            )
            refresh_list()
            self.update_type_menu()

        def refresh_list():
            for w in scroll.winfo_children():
                w.destroy()
            for row in self.controller.db.query("SELECT * FROM contract_types"):
                f = ctk.CTkFrame(scroll, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    f, text=f"{row[0]} >> {row[1]} aUEC", font=DrakeConfig.FONT_LOGS
                ).pack(side="left", padx=10)
                ctk.CTkButton(
                    f,
                    text="REMOVE",
                    width=60,
                    fg_color="transparent",
                    text_color=DrakeConfig.ACCENT_ERROR,
                    hover_color="#330000",
                    command=lambda n=row[0]: delete(n),
                ).pack(side="right", padx=5)

        refresh_list()
