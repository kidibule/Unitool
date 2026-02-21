"""Controller pour la gestion des vaisseaux (ships)."""

from datetime import datetime
from models.ship import Ship


class ShipController:
    """Contrôleur simple pour CRUD sur la table `ships`.

    Expose des méthodes:
    - save_ship
    - load_ship
    - import_ships_csv
    - export_ships_csv
    """

    def __init__(self, app_controller):
        self.app = app_controller

    def save_ship(
        self,
        name: str,
        brand: str = "",
        role: str = "",
        career: str = "",
        size: str = "",
        crew_size: int = 0,
        scm_speed: str = "",
        scm_boost_forward: str = "",
        scm_boost_backward: str = "",
        nav_max_speed: str = "",
        pitch: str = "",
        yaw: str = "",
        roll: str = "",
        boosted_pitch: str = "",
        boosted_yaw: str = "",
        boosted_roll: str = "",
        power_consumption: str = "",
        cm_decoy_noise: str = "",
        hp: int = 0,
        cargo: str = "",
        dimensions: str = "",
        mass: str = "",
        hydrogen_capacity: str = "",
        qt_fuel_capacity: str = "",
        expedition_fee: str = "",
        claim_time: str = "",
        expedite_time: str = "",
    ) -> None:
        """Insère ou met à jour un ship par `name` unique."""
        sql = """
        INSERT INTO ships (name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, scm_boost_backward,
            nav_max_speed, pitch, yaw, roll, boosted_pitch, boosted_yaw, boosted_roll, power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass,
            hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            brand=excluded.brand,
            role=excluded.role,
            career=excluded.career,
            size=excluded.size,
            crew_size=excluded.crew_size,
            scm_speed=excluded.scm_speed,
            scm_boost_forward=excluded.scm_boost_forward,
            scm_boost_backward=excluded.scm_boost_backward,
            nav_max_speed=excluded.nav_max_speed,
            pitch=excluded.pitch,
            yaw=excluded.yaw,
            roll=excluded.roll,
            boosted_pitch=excluded.boosted_pitch,
            boosted_yaw=excluded.boosted_yaw,
            boosted_roll=excluded.boosted_roll,
            power_consumption=excluded.power_consumption,
            cm_decoy_noise=excluded.cm_decoy_noise,
            hp=excluded.hp,
            cargo=excluded.cargo,
            dimensions=excluded.dimensions,
            mass=excluded.mass,
            hydrogen_capacity=excluded.hydrogen_capacity,
            qt_fuel_capacity=excluded.qt_fuel_capacity,
            expedition_fee=excluded.expedition_fee,
            claim_time=excluded.claim_time,
            expedite_time=excluded.expedite_time
        """
        params = (
            name.upper(),
            brand.upper(),
            role.upper(),
            career.upper(),
            size,
            int(crew_size) if crew_size else 0,
            scm_speed,
            scm_boost_forward,
            scm_boost_backward,
            nav_max_speed,
            pitch,
            yaw,
            roll,
            boosted_pitch,
            boosted_yaw,
            boosted_roll,
            power_consumption,
            cm_decoy_noise,
            int(hp) if hp else 0,
            cargo,
            dimensions,
            mass,
            hydrogen_capacity,
            qt_fuel_capacity,
            expedition_fee,
            claim_time,
            expedite_time,
        )
        self.app.commit(sql, params)
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Saved ship: {name}", source="SHIP")
        except Exception:
            pass

    def load_ship(self, name: str) -> list:
        """Retourne les rows correspondant au nom (uppercased)."""
        return self.app.query("SELECT * FROM ships WHERE name=?", (name.upper(),))

    def load_ship_as_model(self, name: str) -> Ship:
        rows = self.app.query("SELECT * FROM ships WHERE name=?", (name.upper(),))
        if rows:
            # Utilise la méthode de classe que tu as définie
            return Ship.from_db_row(rows[0])
        return None

    def import_ships_csv(self, rows: list) -> None:
        """Import simple depuis une liste de dicts (ex CSV.DictReader)."""
        count = 0
        for r in rows:
            sql = "INSERT OR REPLACE INTO ships (name, brand, role, career, size, crew_size, scm_speed, scm_boost_forward, scm_boost_backward, nav_max_speed, pitch, yaw, roll, boosted_pitch, boosted_yaw, boosted_roll, power_consumption, cm_decoy_noise, hp, cargo, dimensions, mass, hydrogen_capacity, qt_fuel_capacity, expedition_fee, claim_time, expedite_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            params = (
                r.get("name", "").upper(),
                r.get("brand", ""),
                r.get("role", ""),
                r.get("career", ""),
                r.get("size", ""),
                r.get("crew_size", 0),
                r.get("scm_speed", ""),
                r.get("scm_boost_forward", ""),
                r.get("scm_boost_backward", ""),
                r.get("nav_max_speed", ""),
                r.get("pitch", ""),
                r.get("yaw", ""),
                r.get("roll", ""),
                r.get("boosted_pitch", ""),
                r.get("boosted_yaw", ""),
                r.get("boosted_roll", ""),
                r.get("power_consumption", ""),
                r.get("cm_decoy_noise", ""),
                r.get("hp", 0),
                r.get("cargo", ""),
                r.get("dimensions", ""),
                r.get("mass", ""),
                r.get("hydrogen_capacity", ""),
                r.get("qt_fuel_capacity", ""),
                r.get("expedition_fee", ""),
                r.get("claim_time", ""),
                r.get("expedite_time", ""),
            )
            self.app.commit(sql, params)
            count += 1
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Imported {count} ships from CSV", source="SHIP")
        except Exception:
            pass

    def export_ships_csv(self) -> list:
        return self.app.query("SELECT * FROM ships")

    def clear_all_fields(self):
        pass
