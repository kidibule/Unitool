import customtkinter as ctk
from views.main_view import MainView
from controllers import AppController
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UNITOOL - STAR CITIZEN INTEL")
        self.geometry("1400x800")

        # Instancie le contrôleur applicatif (gestion DB + sub-controllers)
        self.controller = AppController(reset_db_on_start=False)

        # Configuration de la fenêtre principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Passe le controller (AppController) à la vue principale
        self.view = MainView(parent=self, controller=self.controller)
        self.view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()