import customtkinter as ctk
from views.main_view import MainView
from database import Database

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UNITOOL - STAR CITIZEN INTEL")
        self.geometry("1400x800")
        
        # Initialisation BDD
        self.db = Database()
        
        # Configuration de la fenêtre principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.view = MainView(parent=self, controller=self)
        self.view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()