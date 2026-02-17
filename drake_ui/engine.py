import customtkinter as ctk

# ==========================================
# 1. CONSTANTES DE LA CHARTE GRAPHIQUE (DRAKE CONFIG)
# ==========================================
class DrakeConfig:
    # Palette de Couleurs
    BG_MAIN = "#1a1a1a"
    BG_PANEL = "#2b2b2b"
    BG_TERMINAL = "#000000"
    
    ACCENT_PRIMARY = "#ff8c00"   # Dark Orange
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
    def create_title(parent, text, pady=(20, 10), with_line=False):
        label = ctk.CTkLabel(
            parent, 
            text=text.upper(), 
            font=DrakeConfig.FONT_TITLE, 
            text_color=DrakeConfig.ACCENT_PRIMARY
        )
        label.pack(pady=pady)
        
        if with_line:
            line = ctk.CTkFrame(parent, height=2, fg_color=DrakeConfig.ACCENT_PRIMARY)
            line.pack(fill="x", padx=100, pady=(0, 20))
        
        return label

# ==========================================
# 2. COMPOSANTS PRÉ-STYLISEZ (BIBLIOTHÈQUE)
# ==========================================

class DrakeButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": DrakeConfig.ACCENT_PRIMARY,
            "hover_color": DrakeConfig.ACCENT_HOVER,
            "text_color": "#000000",
            "font": DrakeConfig.FONT_UI,
            "corner_radius": DrakeConfig.CORNER_RADIUS,
            "height": 35
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

class DrakeTerminal(ctk.CTkTextbox):
    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": DrakeConfig.BG_TERMINAL,
            "text_color": DrakeConfig.ACCENT_PRIMARY,
            "border_color": DrakeConfig.ACCENT_PRIMARY,
            "border_width": DrakeConfig.BORDER_WIDTH,
            "font": DrakeConfig.FONT_LOGS,
            "corner_radius": DrakeConfig.CORNER_RADIUS
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)
    
    def log(self, message):
        """Ajoute un préfixe automatique style Star Citizen"""
        self.insert("end", f"> {message.upper()}...\n")
        self.see("end")

# ==========================================
# 3. INTERFACE UTILISATEUR (APPLICATION)
# ==========================================

class DrakeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURATION FENÊTRE ---
        self.title("DRAKE SYSTEMS - OPERATIONAL UNIT")
        self.geometry("700x550")
        self.configure(fg_color=DrakeConfig.BG_MAIN)
        ctk.set_appearance_mode("dark")

        # --- HEADER ---
        self.lbl_status = ctk.CTkLabel(
            self, 
            text="UPLINK STATUS: CONNECTED", 
            text_color=DrakeConfig.ACCENT_PRIMARY,
            font=("Segoe UI", 14, "bold")
        )
        self.lbl_status.pack(pady=(20, 10))

        # --- MAIN CONTAINER ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=DrakeConfig.PADDING, pady=DrakeConfig.PADDING)

        # --- INPUT SECTION (FRAME) ---
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(0, 10))

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="ENTER TARGET PARAMETERS",
            fg_color=DrakeConfig.BG_PANEL,
            border_color=DrakeConfig.ACCENT_PRIMARY,
            text_color=DrakeConfig.TEXT_MAIN,
            height=40
        )
        self.entry.pack(fill="x")

        # --- TERMINAL SECTION ---
        self.terminal = DrakeTerminal(self.main_frame, height=250)
        self.terminal.pack(fill="both", expand=True, pady=10)

        # --- ACTION BUTTONS (BOTTOM) ---
        self.btn_execute = DrakeButton(
            self.main_frame, 
            text="INITIALIZE HANDSHAKE", 
            command=self.run_process
        )
        self.btn_execute.pack(fill="x", side="bottom", pady=(10, 0))
        

    def run_process(self):
        """Logique de traitement"""
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