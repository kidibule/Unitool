import customtkinter as ctk
from views.main_view import MainView
from controllers import AppController
from drake_ui.engine import DrakeConfig, DrakeButton, DrakeTerminal

"""Point d'entrée de l'interface UNITOOL.

Ce module initialise la fenêtre principale, crée le contrôleur applicatif
et monte la vue principale qui orchestre les différents panneaux.
"""

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Paramètres de fenêtre globaux
        self.title("UNITOOL - STAR CITIZEN INTEL")
        self.geometry("1400x800")
        self.state("zoomed")
        self.attributes("-topmost", False)

        # Instancie le contrôleur applicatif (gestion DB + sub-controllers)
        self.controller = AppController(reset_db_on_start=False)

        # Configuration de la fenêtre principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Passe le controller (AppController) à la vue principale
        self.view = MainView(parent=self, controller=self.controller)
        self.view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    # Thème global CustomTkinter
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Démarrage de l'application
    app = App()
    app.mainloop()