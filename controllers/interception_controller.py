"""Contrôleur d'interception quantique.

Gère la persistance des points de navigation et les calculs
de distance optimale pour le déploiement de snare.
"""

import numpy as np
from models.location import LocationSeedImporter

class InterceptionController:
    """Expose les opérations métier du module d'interception."""

    COORD_UNIT = "m"

    def __init__(self, master):
        # Référence vers le contrôleur principal (accès DB/query/commit)
        self.master = master
        try:
            self.seed_locations_if_empty()
        except Exception as e:
            self._log(f"Interception seed skipped: {e}")

    def _log(self, message):
        if hasattr(self.master, "log"):
            self.master.log(message, source="INTERCEPTION")

    @classmethod
    def units_to_km(cls, value):
        """Convertit une distance des unités DB vers kilomètres."""
        v = float(value)
        if cls.COORD_UNIT == "m":
            return v / 1000.0
        if cls.COORD_UNIT == "km":
            return v
        return v

    def seed_locations_if_empty(self, seed_file="data/locations.json"):
        """Initialise la table locations à partir d'un JSON si la DB est vide."""
        count_rows = self.master.query("SELECT COUNT(*) FROM locations")
        count = int(count_rows[0][0]) if count_rows else 0
        if count > 0:
            return False

        seed_data = LocationSeedImporter.load_seed_map(seed_file)
        for name, coords in seed_data.items():
            if not isinstance(coords, (list, tuple)) or len(coords) < 3:
                continue
            self.upsert_location(name, coords[0], coords[1], coords[2], loc_type="OTHER", parent_name=None)

        self._log(f"Interception locations seeded ({len(seed_data)} entries).")
        return True

    def get_location_names(self):
        """Retourne la liste triée des positions enregistrées."""
        rows = self.master.query("SELECT name FROM locations ORDER BY name ASC")
        return [row[0] for row in rows]

    def get_location_names_by_type(self, type_names):
        """Retourne les noms triés des positions filtrées par type."""
        normalized_types = [str(t).strip().upper() for t in (type_names or []) if str(t).strip()]
        if not normalized_types:
            return self.get_location_names()

        placeholders = ",".join(["?"] * len(normalized_types))
        rows = self.master.query(
            f"SELECT name FROM locations WHERE UPPER(COALESCE(type, 'POI')) IN ({placeholders}) ORDER BY name ASC",
            tuple(normalized_types),
        )
        return [row[0] for row in rows]

    def get_location_type(self, name):
        """Retourne le type normalisé d'un lieu, ou None s'il n'existe pas."""
        location_name = (name or "").strip().upper()
        if not location_name:
            return None

        row = self.master.query(
            "SELECT UPPER(COALESCE(type, 'POI')) FROM locations WHERE name = ?",
            (location_name,),
        )
        return row[0][0] if row else None

    def get_child_moons(self, planet_name):
        """Retourne les lunes enfants d'une planète."""
        parent = (planet_name or "").strip().upper()
        if not parent:
            return []

        rows = self.master.query(
            """
            SELECT name
            FROM locations
            WHERE parent_name = ?
              AND UPPER(COALESCE(type, 'POI')) = 'MOON'
            ORDER BY name ASC
            """,
            (parent,),
        )
        return [row[0] for row in rows]

    def get_coords_from_db(self, name):
        """Retourne les coordonnées d'une position sous forme de vecteur numpy."""
        res = self.master.query("SELECT x, y, z FROM locations WHERE name = ?", (name,))
        if res:
            return np.array(res[0])
        return None

    def upsert_location(self, name, x, y, z, loc_type="POI", parent_name=None):
        """Crée ou met à jour une position dans la base de données."""
        location_name = (name or "").strip().upper()
        if not location_name:
            raise ValueError("Location name is required.")

        normalized_type = (loc_type or "POI").strip().upper()
        normalized_parent = (parent_name or "").strip().upper()
        if normalized_parent in ("", "NONE", "NO PARENT"):
            normalized_parent = None

        if normalized_parent == location_name:
            raise ValueError("A location cannot be its own parent.")

        if normalized_parent is not None:
            parent_row = self.master.query(
                "SELECT UPPER(COALESCE(type, 'POI')) FROM locations WHERE name = ?",
                (normalized_parent,),
            )
            if not parent_row:
                raise ValueError("Selected parent location does not exist.")

            parent_type = parent_row[0][0]
            if normalized_type == "MOON" and parent_type != "PLANET":
                raise ValueError("A MOON must have a PLANET as parent.")

        if normalized_type == "MOON" and normalized_parent is None:
            raise ValueError("A MOON requires a parent PLANET.")

        try:
            fx = float(x)
            fy = float(y)
            fz = float(z)
        except (TypeError, ValueError):
            raise ValueError("Coordinates must be numeric.")

        self.master.commit(
            """
            INSERT INTO locations (name, x, y, z, type, parent_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x = excluded.x,
                y = excluded.y,
                z = excluded.z,
                type = excluded.type,
                parent_name = excluded.parent_name
            """,
            (location_name, fx, fy, fz, normalized_type, normalized_parent),
        )

        return location_name

    def delete_location(self, name):
        """Supprime une position existante par son nom."""
        location_name = (name or "").strip().upper()
        if not location_name or location_name == "NO DATA":
            raise ValueError("Location name is required.")

        child_rows = self.master.query(
            "SELECT name FROM locations WHERE parent_name = ? ORDER BY name ASC",
            (location_name,),
        )
        if child_rows:
            children = ", ".join([row[0] for row in child_rows])
            raise ValueError(f"Cannot delete parent location. Linked children: {children}")

        self.master.commit(
            "DELETE FROM locations WHERE name = ?",
            (location_name,),
        )

        return location_name

    def calculate_snare_solution(self, source_names, dest_name, radius=20000, max_dist=250000, step=500):
        """Calcule une solution complète de snare (distance + point + méta)."""
        result = {
            "ok": False,
            "distance_units": 0.0,
            "distance_km": 0.0,
            "point": None,
            "avg_dir": None,
            "radius_units": float(radius),
            "radius_km": self.units_to_km(radius),
            "max_dist_units": float(max_dist),
            "step_units": float(step),
            "limiting_source": None,
            "message": "",
        }

        try:
            radius = float(radius)
            max_dist = float(max_dist)
            step = float(step)
        except (TypeError, ValueError):
            result["message"] = "radius, step and max_dist must be numeric."
            return result

        if radius <= 0 or max_dist <= 0 or step <= 0:
            result["message"] = "radius, step and max_dist must be positive."
            return result

        normalized_sources = [str(n).strip().upper() for n in (source_names or []) if str(n).strip()]
        if not normalized_sources:
            result["message"] = "No source points provided."
            return result

        dest = (dest_name or "").strip().upper()
        if not dest:
            result["message"] = "Destination is required."
            return result

        names_to_fetch = set(normalized_sources + [dest])
        coords_cache = {name: self.get_coords_from_db(name) for name in names_to_fetch}

        end_coords = coords_cache.get(dest)
        if end_coords is None:
            result["message"] = f"Destination not found: {dest}."
            return result

        missing = [name for name in normalized_sources if coords_cache.get(name) is None]
        if missing:
            result["message"] = f"Source(s) not found: {', '.join(missing)}."
            return result

        sources_coords = [coords_cache[name] for name in normalized_sources]

        directions = []
        for source in sources_coords:
            dir_vec = end_coords - source
            norm = np.linalg.norm(dir_vec)
            if norm > 0:
                directions.append(dir_vec / norm)

        if not directions:
            result["message"] = "Cannot compute average direction: all sources overlap destination."
            return result

        avg_dir = np.mean(directions, axis=0)
        avg_norm = np.linalg.norm(avg_dir)
        if avg_norm == 0:
            result["message"] = "Average direction norm is zero."
            return result
        avg_dir = avg_dir / avg_norm

        result["avg_dir"] = [float(v) for v in avg_dir]

        max_iter = int(max_dist // step)
        best_dist = None
        best_point = None

        for idx in range(max_iter + 1):
            dist = idx * step
            current_p = end_coords - (avg_dir * dist)
            valid = True
            limiting_source = None

            for i, source in enumerate(sources_coords):
                source_name = normalized_sources[i]
                line_vec = end_coords - source
                denom = float(np.dot(line_vec, line_vec))

                if denom == 0:
                    point_dist = float(np.linalg.norm(current_p - source))
                else:
                    t = float(np.dot(current_p - source, line_vec) / denom)
                    t = max(0.0, min(1.0, t))
                    closest = source + t * line_vec
                    point_dist = float(np.linalg.norm(current_p - closest))

                if point_dist > radius:
                    valid = False
                    limiting_source = source_name
                    break

            if valid:
                best_dist = dist
                best_point = current_p
            else:
                result["limiting_source"] = limiting_source
                break

        if best_dist is None:
            result["message"] = "No valid snare point found (invalid at distance 0)."
            return result

        result["ok"] = True
        result["distance_units"] = float(best_dist)
        result["distance_km"] = self.units_to_km(best_dist)
        result["point"] = [float(v) for v in best_point]
        return result

    def calculate_snare_distance(self, source_names, dest_name, radius=20000, max_dist=250000, step=500):
        """Wrapper de compatibilité: retourne seulement la distance en km."""
        result = self.calculate_snare_solution(
            source_names,
            dest_name,
            radius=radius,
            max_dist=max_dist,
            step=step,
        )
        return result["distance_km"] if result.get("ok") else None