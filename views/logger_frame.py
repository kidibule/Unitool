import customtkinter as ctk
import csv
from datetime import datetime
from tkinter import filedialog, messagebox

# Importation des ressources graphiques
from drake_ui.engine import DrakeConfig, DrakeButton

class LoggerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # --- TITRE ---
        DrakeConfig.create_title(self, "INTEL ARCHIVE SYSTEM")
        # Configuration des entrées style "Drake Console"
        entry_kwargs = {
            "font": DrakeConfig.FONT_LOGS, 
            "fg_color": DrakeConfig.BG_TERMINAL, 
            "border_color": DrakeConfig.BORDER_COLOR, 
            "corner_radius": 0, 
            "height": 35
        }
        
        # --- CHAMPS DE SAISIE ---
        self.p_in = ctk.CTkEntry(self, placeholder_text="TARGET PSEUDO", **entry_kwargs)
        self.p_in.pack(pady=5, padx=100, fill="x")
        self.p_in.bind("<Return>", self.load_target)

        self.o_in = ctk.CTkEntry(self, placeholder_text="ORGANIZATION", **entry_kwargs)
        self.o_in.pack(pady=5, padx=100, fill="x")
        
        # Segmented Button (Alignement IFF)
        self.a_btn = ctk.CTkSegmentedButton(
            self, values=["AMI", "NEUTRE", "ENNEMI"], 
            font=DrakeConfig.FONT_UI,
            selected_color=DrakeConfig.ACCENT_PRIMARY, 
            selected_hover_color=DrakeConfig.ACCENT_HOVER, 
            unselected_color=DrakeConfig.BG_PANEL, 
            unselected_hover_color="#222",
            text_color="black", # Texte noir sur fond orange une fois sélectionné
            corner_radius=0
        )
        self.a_btn.pack(pady=15)
        self.a_btn.set("NEUTRE")
        
        self.s_in = ctk.CTkEntry(self, placeholder_text="CURRENT SHIP", **entry_kwargs)
        self.s_in.pack(pady=5, padx=100, fill="x")
        
        # --- NOUVEAUX CHAMPS (PVP & ACTIVITY) ---
        f_extra = ctk.CTkFrame(self, fg_color="transparent")
        f_extra.pack(pady=5, padx=100, fill="x")
        
        # Combo Boxes stylisées
        combo_style = {
            "font": DrakeConfig.FONT_UI,
            "fg_color": DrakeConfig.BG_TERMINAL,
            "border_color": DrakeConfig.BORDER_COLOR,
            "button_color": DrakeConfig.ACCENT_PRIMARY,
            "button_hover_color": DrakeConfig.ACCENT_HOVER,
            "dropdown_fg_color": DrakeConfig.BG_PANEL,
            "dropdown_text_color": DrakeConfig.TEXT_MAIN,
            "dropdown_hover_color": DrakeConfig.ACCENT_HOVER,
            "corner_radius": 0
        }

        self.pvp_in = ctk.CTkComboBox(f_extra, values=["NOOB", "ROOKIE", "VETERAN", "ACE"], height=35, **combo_style)
        self.pvp_in.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.pvp_in.set("ROOKIE")
        
        self.act_in = ctk.CTkComboBox(f_extra, values=["PIRATE", "BOUNTY HUNTER", "MINEUR", "TRADER", "EXPLORATEUR"], height=35, **combo_style)
        self.act_in.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.act_in.set("PIRATE")

        # Zone de Notes (Style Terminal)
        self.n_in = ctk.CTkTextbox(self, height=100, 
                                   font=DrakeConfig.FONT_LOGS, 
                                   fg_color=DrakeConfig.BG_TERMINAL, 
                                   border_width=1, 
                                   border_color=DrakeConfig.BORDER_COLOR, 
                                   corner_radius=0)
        self.n_in.pack(pady=10, padx=100, fill="x")
        
        # --- BOUTONS D'ACTION ---
        # Utilisation des DrakeButton pour la cohérence
        self.btn_save = DrakeButton(self, text="SYNCHRONIZE DATABASE", command=self.save, height=45)
        self.btn_save.pack(pady=15, padx=100, fill="x")

        self.btn_import = ctk.CTkButton(self, text="IMPORT EXTERNAL CSV", 
                                       command=self.import_csv, 
                                       fg_color="transparent", 
                                       border_width=1, 
                                       border_color=DrakeConfig.BORDER_COLOR, 
                                       text_color=DrakeConfig.TEXT_SECONDARY,
                                       hover_color=DrakeConfig.BG_PANEL,
                                       font=DrakeConfig.FONT_UI,
                                       corner_radius=0,
                                       height=35)
        self.btn_import.pack(pady=5)

    def save(self):
        p = self.p_in.get().strip().upper()
        if p:
            self.controller.db.commit(
                "INSERT OR REPLACE INTO targets (pseudo, org, alignment, ship, notes, date, pvp_lvl, activity) VALUES (?,?,?,?,?,?,?,?)",
                (p, self.o_in.get().upper(), self.a_btn.get(), self.s_in.get().upper(), 
                 self.n_in.get("0.0", "end").strip(), datetime.now().strftime("%d/%m/%y"),
                 self.pvp_in.get().upper(), self.act_in.get().upper())
            )
            messagebox.showinfo("DRAKE SYSTEMS", f"Target {p} synchronized successfully.")

    def load_target(self, event=None):
        pseudo = self.p_in.get().strip().upper()
        if not pseudo: return
        
        rows = self.controller.db.query("SELECT org, ship, alignment, notes, pvp_lvl, activity FROM targets WHERE pseudo = ?", (pseudo,))
        if rows:
            row = rows[0]
            self.o_in.delete(0, "end"); self.o_in.insert(0, row[0])
            self.s_in.delete(0, "end"); self.s_in.insert(0, row[1])
            self.a_btn.set(row[2])
            self.n_in.delete("0.0", "end"); self.n_in.insert("0.0", row[3])
            
            if len(row) > 4:
                if row[4]: self.pvp_in.set(row[4])
                if row[5]: self.act_in.set(row[5])
            
            self.o_in.focus()

    def import_csv(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if not path: return
                
            with open(path, 'r', encoding='utf-8-sig') as f:
                first_line = f.readline()
                delimiter = first_line.split('=')[1].strip() if "sep=" in first_line else ';'
                if "sep=" not in first_line: f.seek(0)
                    
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, None)
                
                count = 0
                for row in reader:
                    if len(row) >= 9:
                        self.controller.db.commit(
                            "INSERT OR REPLACE INTO targets (pseudo, org, ship, threat, notes, date, wins, losses, alignment) VALUES (?,?,?,?,?,?,?,?,?)",
                            row[:9]
                        )
                        count += 1
                
                messagebox.showinfo("DRAKE SYSTEMS", f"Import complete: {count} entries added.")
                if hasattr(self.controller, 'view') and hasattr(self.controller.view, 'refresh_intel'):
                    self.controller.view.refresh_intel()
                    
        except Exception as e:
            messagebox.showerror("SYSTEM ERROR", f"Import failed: {e}")