# drake_ui/__init__.py

from .engine import DrakeConfig, DrakeButton, DrakeTerminal

__version__ = "1.0.0"
__author__ = "UNITOOL System"

# On peut aussi pré-configurer CustomTkinter ici
import customtkinter as ctk
ctk.set_appearance_mode("dark")