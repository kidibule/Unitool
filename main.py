"""Point d'entrée de l'application UNITOOL.

Ce module initialise la fenêtre principale `App` basée sur
CustomTkinter et instancie la vue principale `MainView`.
"""

import customtkinter as ctk

from controllers import AppController
from views.main_view import MainView


class App(ctk.CTk):
    """Application principale — fenêtre root Tkinter.

    Hérite de `ctk.CTk` pour construire la fenêtre principale.
    Contient le contrôleur métier et délègue l'affichage à MainView.
    """

    def __init__(self) -> None:
        super().__init__()

        # Titre et taille de la fenêtre
        self.title("UNITOOL - STAR CITIZEN INTEL")
        self.geometry("1400x800")

        # Initialisation du contrôleur métier (gère la DB et la logique)
        self.controller = AppController()

        # Configuration du grid pour que la vue principale prenne tout l'espace
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Création et placement de la vue principale
        self.view = MainView(parent=self, controller=self.controller)
        self.view.grid(row=0, column=0, sticky="nsew")

        # Log application start
        try:
            if hasattr(self.controller, "log"):
                self.controller.log("Application started", source="APP")
        except Exception:
            pass

        # Ensure we log on close as well
        try:
            def _on_close():
                try:
                    if hasattr(self.controller, "log"):
                        self.controller.log("Application exiting", source="APP")
                except Exception:
                    pass
                self.destroy()

            self.protocol("WM_DELETE_WINDOW", _on_close)
        except Exception:
            pass


if __name__ == "__main__":
    # Apparence et thème par défaut
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Lancement de l'application
    app = App()
    app.mainloop()
