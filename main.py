"""Point d'entrée de l'application UNITOOL.

Ce module initialise la fenêtre principale `App` basée sur
CustomTkinter et instancie la vue principale `MainView`.
"""

from typing import Optional

import customtkinter as ctk

from views.main_view import MainView
from database import Database


class App(ctk.CTk):
    """Application principale.

    Hérite de `ctk.CTk` pour construire la fenêtre principale de l'application.
    """

    def __init__(self) -> None:
        super().__init__()

        # Titre et taille de la fenêtre
        self.title("UNITOOL - STAR CITIZEN INTEL")
        self.geometry("1400x800")

        # Initialisation de la base de données (objet accessible par le controller)
        self.db: Optional[Database] = Database()

        # Configuration du grid pour que la vue principale prenne tout l'espace
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Création et placement de la vue principale
        self.view = MainView(parent=self, controller=self)
        self.view.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    # Apparence et thème par défaut
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Lancement de l'application
    app = App()
    app.mainloop()
