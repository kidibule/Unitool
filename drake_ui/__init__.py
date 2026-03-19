"""Petite bibliothèque UI personnalisée "Drake".

Ce package expose des classes utilitaires (boutons, terminal, config)
et permet une configuration globale minimale de CustomTkinter.
"""

from .engine import (
	DrakeConfig,
	DrakeButton,
	DrakeTerminal,
	DrakeEntry,
	DrakeEntryLight,
	DrakeComboBox,
	DrakeComboBoxLight,
)

__version__ = "1.0.0"
__author__ = "UNITOOL System"

# Configuration d'apparence par défaut pour l'ensemble du package
import customtkinter as ctk

ctk.set_appearance_mode("Dark")

__all__ = [
	"DrakeConfig",
	"DrakeButton",
	"DrakeTerminal",
	"DrakeEntry",
	"DrakeEntryLight",
	"DrakeComboBox",
	"DrakeComboBoxLight",
]
