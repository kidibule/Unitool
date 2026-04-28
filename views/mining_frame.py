"""Frame dédiée au minage — référence des signatures radar des rochers.

Affiche le tableau de signatures et délègue toute la logique métier
au MiningController via self.controller.mining.
"""

import customtkinter as ctk
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeEntry, DrakeTitle1
from controllers.mining_controller import RARITY_COLORS, RARITY_LABELS, SPECIAL_CATEGORIES


def _fmt(value: int) -> str:
    """Formate un entier avec séparateur de milliers (espace)."""
    return f"{value:,}".replace(",", " ")


# ──────────────────────────────────────────────────────────────────────────────
# FRAME PRINCIPALE
# ──────────────────────────────────────────────────────────────────────────────

class MiningFrame(ctk.CTkFrame):
    """Interface de référence pour le minage — signatures radar des rochers."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # En-tête
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(5, 10), fill="x", padx=20)
        DrakeTitle1(header, text="MINING").pack(side="left")

        # TabView
        self.tabview = DrakeConfig.create_tabview(self)
        self.tab_sigs   = self.tabview.add("SIGNATURES RADAR")
        self.tab_special = self.tabview.add("ROC / FPS / SALVAGE")

        self._build_signatures_tab()
        self._build_special_tab()

    # ── Tab 1 : SIGNATURES RADAR ────────────────────────────────────────────

    def _build_signatures_tab(self):
        tab = self.tab_sigs

        # ── Barre de recherche ──────────────────────────────────────────────
        search_frame = ctk.CTkFrame(tab, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
        search_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            search_frame,
            text="IDENTIFIER UNE SIGNATURE :",
            font=DrakeConfig.FONT_UI,
            text_color=DrakeConfig.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 8), pady=10)

        self.search_var = ctk.StringVar()
        self.search_entry = DrakeEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="ex: 7 200",
            width=160,
        )
        self.search_entry.pack(side="left", padx=(0, 8), pady=10)
        self.search_entry.bind("<Return>", lambda _e: self._do_search())

        DrakeButton(
            search_frame,
            text="IDENTIFIER",
            command=self._do_search,
            width=120,
            corner_radius=0,
            height=35,
        ).pack(side="left", padx=(0, 8), pady=10)

        DrakeButton(
            search_frame,
            text="✕",
            command=self._clear_search,
            width=40,
            corner_radius=0,
            height=35,
            fg_color="transparent",
            border_width=1,
            border_color=DrakeConfig.BORDER_COLOR,
        ).pack(side="left", pady=10)

        # ── Toolbar import / export ─────────────────────────────────────────
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=5)

        btn_center = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_center.pack(anchor="center")

        DrakeButton(btn_center, text="IMPORT CSV", width=150,
                    command=self._import_csv).pack(side="left", padx=5)

        DrakeButton(btn_center, text="EXPORT CSV", width=150,
                    command=self.controller.mining.export_signatures_to_csv).pack(side="left", padx=5)

        # Zone de résultats de recherche
        self.result_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=15, pady=(0, 5))
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="",
            font=("Courier New", 12),
            text_color=DrakeConfig.TEXT_MAIN,
            justify="left",
            anchor="w",
        )
        self.result_label.pack(fill="x", padx=5)

        # ── Table de référence ──────────────────────────────────────────────
        # En-têtes colonnes
        header_frame = ctk.CTkFrame(tab, fg_color=DrakeConfig.BG_PANEL, corner_radius=0)
        header_frame.pack(fill="x", padx=15, pady=(5, 0))

        col_widths = [160, 130, 80, 80, 80, 80, 80, 80]
        headers    = ["MINÉRAL", "RARETÉ", "×1", "×2", "×3", "×4", "×5", "×6"]
        for c, (h, w) in enumerate(zip(headers, col_widths)):
            ctk.CTkLabel(
                header_frame,
                text=h,
                font=("Segoe UI", 11, "bold"),
                text_color=DrakeConfig.ACCENT_PRIMARY,
                width=w,
                anchor="center",
            ).grid(row=0, column=c, padx=2, pady=6, sticky="ew")

        # Corps scrollable
        self.table_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color="transparent",
            corner_radius=0,
        )
        self.table_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._highlighted_cells: list = []  # (widget, original_fg_color)
        self._all_rows: list = []              # (row_widgets, mineral_entry, bg)
        self._build_table_rows(col_widths)

    def _build_table_rows(self, col_widths: list):
        """Construit toutes les lignes du tableau de signatures."""
        scroll = self.table_scroll
        row_idx = 0
        current_rarity = None

        for mineral in self.controller.mining.get_signatures():
            rarity  = mineral["rarity"]
            color   = RARITY_COLORS[rarity]
            sigs    = mineral["sigs"]

            # Séparateur de groupe de rareté
            if rarity != current_rarity:
                current_rarity = rarity
                sep = ctk.CTkFrame(scroll, fg_color=color, height=2, corner_radius=0)
                sep.grid(row=row_idx, column=0, columnspan=8, sticky="ew",
                         padx=0, pady=(8, 2))
                row_idx += 1

                lbl = ctk.CTkLabel(
                    scroll,
                    text=f"── {RARITY_LABELS[rarity]} ──",
                    font=("Segoe UI", 10, "bold"),
                    text_color=color,
                    anchor="w",
                )
                lbl.grid(row=row_idx, column=0, columnspan=8, sticky="w",
                         padx=6, pady=(0, 4))
                row_idx += 1

            # Ligne minéral
            bg = DrakeConfig.BG_PANEL if row_idx % 2 == 0 else DrakeConfig.BG_MAIN
            row_widgets = []

            name_lbl = ctk.CTkLabel(
                scroll,
                text=mineral["name"],
                font=("Segoe UI", 12, "bold"),
                text_color=color,
                width=col_widths[0],
                anchor="w",
                fg_color=bg,
            )
            name_lbl.grid(row=row_idx, column=0, padx=2, pady=1, sticky="ew")
            row_widgets.append(name_lbl)

            rarity_lbl = ctk.CTkLabel(
                scroll,
                text=RARITY_LABELS[rarity],
                font=("Segoe UI", 10),
                text_color=color,
                width=col_widths[1],
                anchor="center",
                fg_color=bg,
            )
            rarity_lbl.grid(row=row_idx, column=1, padx=2, pady=1, sticky="ew")
            row_widgets.append(rarity_lbl)

            for col_i in range(6):
                if col_i < len(sigs):
                    sig_text = _fmt(sigs[col_i])
                    sig_color = DrakeConfig.TEXT_MAIN
                else:
                    sig_text  = "—"
                    sig_color = DrakeConfig.TEXT_SECONDARY

                sig_lbl = ctk.CTkLabel(
                    scroll,
                    text=sig_text,
                    font=("Courier New", 11),
                    text_color=sig_color,
                    width=col_widths[2 + col_i],
                    anchor="center",
                    fg_color=bg,
                )
                sig_lbl.grid(row=row_idx, column=2 + col_i, padx=2, pady=1, sticky="ew")
                row_widgets.append(sig_lbl)

            self._all_rows.append((row_widgets, mineral, bg))
            row_idx += 1

    # ── Tab 2 : ROC / FPS / SALVAGE ─────────────────────────────────────────

    def _build_special_tab(self):
        tab = self.tab_special

        ctk.CTkLabel(
            tab,
            text=(
                "Ces catégories ont une signature par palier fixe,\n"
                "indépendante du minéral exact."
            ),
            font=("Segoe UI", 11),
            text_color=DrakeConfig.TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(12, 8))

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        for cat in self.controller.mining.get_special_categories():
            color = cat["color"]
            sigs  = cat["sigs"]

            # Titre catégorie
            sep = ctk.CTkFrame(scroll, fg_color=color, height=2, corner_radius=0)
            sep.pack(fill="x", pady=(10, 2))

            ctk.CTkLabel(
                scroll,
                text=cat["name"].upper(),
                font=("Segoe UI", 13, "bold"),
                text_color=color,
                anchor="w",
            ).pack(anchor="w", padx=6, pady=(0, 6))

            # Grille des valeurs
            grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            grid_frame.pack(fill="x", padx=6, pady=(0, 8))

            for i, sig in enumerate(sigs):
                cell = ctk.CTkFrame(
                    grid_frame,
                    fg_color=DrakeConfig.BG_PANEL,
                    corner_radius=4,
                    border_width=1,
                    border_color=color,
                )
                cell.grid(row=0, column=i, padx=4, pady=2)

                ctk.CTkLabel(
                    cell,
                    text=f"×{i + 1}",
                    font=("Segoe UI", 9),
                    text_color=color,
                ).pack(padx=10, pady=(4, 0))

                ctk.CTkLabel(
                    cell,
                    text=_fmt(sig),
                    font=("Courier New", 12, "bold"),
                    text_color=DrakeConfig.TEXT_MAIN,
                ).pack(padx=10, pady=(0, 4))

    # ── Logique de recherche ─────────────────────────────────────────────────

    def _do_search(self):
        raw = self.search_var.get().strip()
        if not raw:
            self._clear_search()
            return

        results = self.controller.mining.search_signature(raw)
        self._clear_highlights()

        if not results:
            self.result_label.configure(
                text=f"  Aucune signature trouvée pour « {raw} »",
                text_color=DrakeConfig.ACCENT_ERROR,
            )
            return

        lines = []
        # Ensemble (nom, count) des correspondances exactes
        matched = {(r["name"], r["count"]) for r in results}

        for r in results:
            rarity_str = (
                f"  [{RARITY_LABELS[r['rarity']]}]" if r["rarity"] else ""
            )
            lines.append(
                f"  ✓  {r['name']}{rarity_str}  —  ×{r['count']} rocher(s)  →  sig. {_fmt(r['sig'])}"
            )

        self.result_label.configure(
            text="\n".join(lines),
            text_color=DrakeConfig.ACCENT_PRIMARY,
        )

        # Surligner uniquement la cellule exacte (minéral + colonne du nombre de rochers)
        # row_widgets : [0]=nom, [1]=rareté, [2]=×1, [3]=×2, ..., [7]=×6
        for row_widgets, mineral, _bg in self._all_rows:
            for r in results:
                if mineral["name"] == r["name"]:
                    cell_index = 1 + r["count"]  # 0=nom,1=rareté,2=×1,3=×2…
                    if cell_index < len(row_widgets):
                        widget = row_widgets[cell_index]
                        try:
                            original_color = widget.cget("fg_color")
                            widget.configure(
                                fg_color="#3a2a00",
                                text_color=DrakeConfig.ACCENT_PRIMARY,
                            )
                            self._highlighted_cells.append((widget, original_color, r["color"]))
                        except Exception:
                            pass

        # Naviguer vers l'onglet signatures si on vient d'un autre onglet
        try:
            self.tabview.set("SIGNATURES RADAR")
        except Exception:
            pass

    def _clear_search(self):
        self.search_var.set("")
        self.result_label.configure(text="")
        self._clear_highlights()

    def _clear_highlights(self):
        for widget, original_color, original_text_color in self._highlighted_cells:
            try:
                widget.configure(fg_color=original_color, text_color=original_text_color)
            except Exception:
                pass
        self._highlighted_cells.clear()

    def _import_csv(self):
        """Délègue l'import CSV au controller puis reconstruit le tableau."""
        new_sigs = self.controller.mining.import_signatures_from_csv()
        if new_sigs is not None:
            self._rebuild_table()

    def _rebuild_table(self):
        """Vide et reconstruit le tableau de signatures (après import)."""
        self._clear_highlights()
        self._all_rows.clear()
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
        col_widths = [160, 130, 80, 80, 80, 80, 80, 80]
        self._build_table_rows(col_widths)

    def refresh(self):
        """Pas de données dynamiques — rien à rafraîchir."""
        pass
