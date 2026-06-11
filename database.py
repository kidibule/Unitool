from db_connection import DBConnection
from db_migrations import run_migrations
from repositories.player_repository import PlayerRepository
from repositories.org_repository import OrgRepository
from repositories.location_repository import LocationRepository
from repositories.ship_repository import ShipRepository



class Database(DBConnection):
    def __init__(self, db_name="unitool_data.db", reset_on_start: bool = False):
        # La connexion SQLite est gérée par DBConnection
        super().__init__(db_name, reset_on_start)

        # Applique toutes les migrations manquantes
        self.setup()

        # Repositories — un par domaine fonctionnel
        self.players = PlayerRepository(self)
        self.orgs = OrgRepository(self)
        self.locations = LocationRepository(self)
        self.ships = ShipRepository(self)

    def setup(self):
        """Point d'entrée des migrations — délègue à db_migrations.run_migrations."""
        run_migrations(self.conn, self.conn.cursor())


