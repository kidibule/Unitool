"""Repository Locations — opérations sur les points d'intérêt et lieux de navigation."""


class LocationRepository:
    """Toutes les opérations DB liées aux locations (POI, planètes, stations…)."""

    def __init__(self, db):
        """
        Args:
            db: instance DBConnection (conn + cursor + query/commit)
        """
        self._db = db

    def get_all_names(self) -> list[str]:
        """Retourne tous les noms de lieux, triés alphabétiquement."""
        rows = self._db.query("SELECT name FROM locations ORDER BY name ASC")
        return [row[0] for row in rows]

    def upsert(
        self,
        name: str,
        x: float,
        y: float,
        z: float,
        loc_type: str = "POI",
        parent_name: str | None = None,
    ) -> None:
        """Insère ou met à jour un lieu (clé = nom)."""
        sql = """
            INSERT INTO locations (name, x, y, z, type, parent_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x=excluded.x,
                y=excluded.y,
                z=excluded.z,
                type=excluded.type,
                parent_name=excluded.parent_name
        """
        self._db.commit(sql, (name.upper(), x, y, z, loc_type, parent_name))
