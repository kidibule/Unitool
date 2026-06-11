"""Repository Ships — opérations sur le catalogue de composants et les loadouts."""


class ShipRepository:
    """Opérations DB liées aux composants de vaisseau et aux loadouts directs (legacy)."""

    def __init__(self, db):
        """
        Args:
            db: instance DBConnection (conn + cursor + query/commit)
        """
        self._db = db

    def add_component_type(self, name: str, category: str) -> None:
        """Crée un type de composant s'il n'existe pas encore."""
        self._db.commit(
            "INSERT OR IGNORE INTO component_types (name, category) VALUES (?, ?)",
            (name.upper(), category.upper()),
        )

    def add_component(
        self,
        name: str,
        brand: str,
        type_name: str,
        category: str,
        size: int,
        grade: str,
        stats: str = "{}",
    ) -> None:
        """Insère ou remplace un composant dans le catalogue."""
    def add_component(
        self,
        name: str,
        brand: str,
        type_name: str,
        category: str,
        size: int,
        grade: str,
        stats: str = "{}",
    ) -> None:
        """Insère ou remplace un composant dans le catalogue."""
        sql = """
            INSERT OR REPLACE INTO components
                (name, brand, type_name, category, size, grade)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self._db.commit(sql, (
            name.upper(),
            brand.upper(),
            type_name.upper(),
            category.upper(),
            size,
            grade.upper(),
        ))

    def equip_component(
        self, ship_name: str, component_name: str, qty: int = 1
    ) -> None:
        """Monte un composant sur un vaisseau (slot LEGACY générique)."""
        sql = """
            INSERT OR REPLACE INTO ship_loadout
                (ship_name, profile_name, category, subtype_name, slot_number, component_name, quantity)
            VALUES (?, 'DEFAULT', 'LEGACY', 'GENERIC', 0, ?, ?)
        """
        self._db.commit(sql, (ship_name.upper(), component_name.upper(), qty))

    def get_ship_components(self, ship_name: str) -> list:
        """Retourne tous les composants équipés sur un vaisseau."""
        sql = """
            SELECT c.*, ct.category
            FROM components c
            JOIN ship_loadout sl ON c.name = sl.component_name
            JOIN component_types ct ON c.type_name = ct.name
            WHERE sl.ship_name = ?
        """
        return self._db.query(sql, (ship_name.upper(),))
