"""Quantum interception controller.

Handles location persistence and optimal snare distance calculations.
"""

import numpy as np
import json
from models.location import LocationSeedImporter

class InterceptionController:
    """Exposes business operations for the interception module."""

    COORD_UNIT = "m"

    def __init__(self, master):
        # Reference to main app controller (DB query/commit access)
        self.master = master
        self._ensure_interception_routes_table()
        try:
            self.seed_locations_if_empty()
        except Exception as e:
            self._log(f"Interception seed skipped: {e}")

    def _ensure_interception_routes_table(self):
        self.master.commit(
            """
            CREATE TABLE IF NOT EXISTS interception_routes (
                name TEXT PRIMARY KEY,
                destination_name TEXT NOT NULL,
                sources_json TEXT NOT NULL,
                radius REAL NOT NULL DEFAULT 20000,
                step REAL NOT NULL DEFAULT 500,
                max_dist REAL NOT NULL DEFAULT 250000,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def _log(self, message):
        if hasattr(self.master, "log"):
            self.master.log(message, source="INTERCEPTION")

    @classmethod
    def units_to_km(cls, value):
        """Converts a DB-unit distance to kilometers."""
        v = float(value)
        if cls.COORD_UNIT == "m":
            return v / 1000.0
        if cls.COORD_UNIT == "km":
            return v
        return v

    def seed_locations_if_empty(self, seed_file="data/locations.json"):
        """Seeds locations from JSON when the table is empty."""
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
        """Returns sorted saved location names."""
        rows = self.master.query("SELECT name FROM locations ORDER BY name ASC")
        return [row[0] for row in rows]

    def get_location(self, name):
        """Returns full data dict for a location, or None if not found."""
        location_name = (name or "").strip().upper()
        if not location_name or location_name == "NO DATA":
            return None
        rows = self.master.query(
            "SELECT name, x, y, z, type, parent_name FROM locations WHERE name = ?",
            (location_name,),
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "name": row[0],
            "x": row[1],
            "y": row[2],
            "z": row[3],
            "type": (row[4] or "POI").upper(),
            "parent_name": row[5] or "NONE",
        }

    def get_road_names(self):
        """Returns sorted saved interception road names."""
        rows = self.master.query(
            "SELECT name FROM interception_routes ORDER BY UPPER(name) ASC"
        )
        return [row[0] for row in rows]

    def save_road(self, road_name, source_names, dest_name, radius, step, max_dist):
        """Creates or updates a reusable interception road."""
        name = (road_name or "").strip()
        if not name:
            raise ValueError("Road name is required.")

        normalized_sources = [str(n).strip().upper() for n in (source_names or []) if str(n).strip()]
        if not normalized_sources:
            raise ValueError("At least one source point is required.")

        destination = (dest_name or "").strip().upper()
        if not destination:
            raise ValueError("Destination is required.")

        try:
            radius = float(radius)
            step = float(step)
            max_dist = float(max_dist)
        except (TypeError, ValueError):
            raise ValueError("radius, step and max_dist must be numeric.")

        if radius <= 0 or step <= 0 or max_dist <= 0:
            raise ValueError("radius, step and max_dist must be positive.")

        self.master.commit(
            """
            INSERT INTO interception_routes (name, destination_name, sources_json, radius, step, max_dist, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                destination_name = excluded.destination_name,
                sources_json = excluded.sources_json,
                radius = excluded.radius,
                step = excluded.step,
                max_dist = excluded.max_dist,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                name,
                destination,
                json.dumps(normalized_sources),
                radius,
                step,
                max_dist,
            ),
        )
        return name

    def get_road(self, road_name):
        """Returns a full road payload or None if missing."""
        name = (road_name or "").strip()
        if not name:
            return None

        rows = self.master.query(
            """
            SELECT name, destination_name, sources_json, radius, step, max_dist
            FROM interception_routes
            WHERE name = ?
            """,
            (name,),
        )
        if not rows:
            return None

        row = rows[0]
        try:
            sources = json.loads(row[2]) if row[2] else []
        except json.JSONDecodeError:
            sources = []

        if not isinstance(sources, list):
            sources = []

        return {
            "name": row[0],
            "destination_name": row[1],
            "source_names": [str(x).strip().upper() for x in sources if str(x).strip()],
            "radius": float(row[3]),
            "step": float(row[4]),
            "max_dist": float(row[5]),
        }

    def delete_road(self, road_name):
        """Deletes a saved interception road."""
        name = (road_name or "").strip()
        if not name:
            raise ValueError("Road name is required.")

        self.master.commit(
            "DELETE FROM interception_routes WHERE name = ?",
            (name,),
        )
        return name

    # Backward-compatible wrappers (legacy route naming)
    def get_route_names(self):
        return self.get_road_names()

    def save_route(self, route_name, source_names, dest_name, radius, step, max_dist):
        return self.save_road(route_name, source_names, dest_name, radius, step, max_dist)

    def get_route(self, route_name):
        return self.get_road(route_name)

    def delete_route(self, route_name):
        return self.delete_road(route_name)

    def get_location_names_by_type(self, type_names):
        """Returns sorted location names filtered by type."""
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
        """Returns normalized location type, or None if missing."""
        location_name = (name or "").strip().upper()
        if not location_name:
            return None

        row = self.master.query(
            "SELECT UPPER(COALESCE(type, 'POI')) FROM locations WHERE name = ?",
            (location_name,),
        )
        return row[0][0] if row else None

    def get_child_moons(self, planet_name):
        """Returns child moons for a planet."""
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
        """Returns location coordinates as a numpy vector."""
        res = self.master.query("SELECT x, y, z FROM locations WHERE name = ?", (name,))
        if res:
            return np.array(res[0])
        return None

    def upsert_location(self, name, x, y, z, loc_type="POI", parent_name=None):
        """Creates or updates a location in SQLite."""
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
        """Deletes an existing location by name."""
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

    def validate_sources_for_destination(self, source_names, dest_name):
        """Validates if source selection can produce a snare cone for a destination."""
        normalized_sources = [str(n).strip().upper() for n in (source_names or []) if str(n).strip()]
        destination = (dest_name or "").strip().upper()

        if not normalized_sources:
            return {
                "ok": False,
                "message": "No source points provided.",
                "invalid_sources": [],
            }

        if not destination:
            return {
                "ok": False,
                "message": "Destination is required.",
                "invalid_sources": [],
            }

        end_coords = self.get_coords_from_db(destination)
        if end_coords is None:
            return {
                "ok": False,
                "message": f"Destination not found: {destination}.",
                "invalid_sources": [],
            }

        invalid_sources = []
        directions = []
        for source_name in normalized_sources:
            source_coords = self.get_coords_from_db(source_name)
            if source_coords is None:
                invalid_sources.append(source_name)
                continue

            dir_vec = end_coords - source_coords
            norm = float(np.linalg.norm(dir_vec))
            if norm == 0.0:
                # A source exactly on destination cannot define a usable interception cone.
                invalid_sources.append(source_name)
                continue

            directions.append(dir_vec / norm)

        if invalid_sources:
            return {
                "ok": False,
                "message": f"Invalid source(s) for destination {destination}: {', '.join(invalid_sources)}.",
                "invalid_sources": invalid_sources,
            }

        if not directions:
            return {
                "ok": False,
                "message": "No valid source direction available.",
                "invalid_sources": normalized_sources,
            }

        avg_dir = np.mean(directions, axis=0)
        avg_norm = float(np.linalg.norm(avg_dir))
        if avg_norm <= 1e-9:
            return {
                "ok": False,
                "message": "No interception cone possible with these sources (average direction is null).",
                "invalid_sources": [],
            }

        return {
            "ok": True,
            "message": "",
            "invalid_sources": [],
        }

    def get_radius_from_db(self, name):
        """Returns the radius (m) of a location, or 0 if unknown."""
        res = self.master.query("SELECT radius FROM locations WHERE name = ?", (name,))
        if res and res[0][0] is not None:
            return float(res[0][0])
        return 0.0

    def get_physics_grid_from_db(self, name):
        """Returns the physics grid radius (m) of a location.

        C'est le rayon réel de la zone de départ des vaisseaux utilisé par SnarePlan
        comme altitude dans la formule triangle quand aucun point C externe n'est disponible.
        Tombe en fallback sur le rayon physique, puis sur 0.
        """
        res = self.master.query(
            "SELECT physics_grid, radius FROM locations WHERE name = ?", (name,)
        )
        if res:
            pg = res[0][0]
            if pg is not None and float(pg) > 0:
                return float(pg)
            r = res[0][1]
            if r is not None and float(r) > 0:
                return float(r)
        return 0.0

    def calculate_snare_solution(self, source_names, dest_name, radius=20000, max_dist=250000, step=500):
        """Calculates a snare solution using the SnarePlan triangle formula.

        Formula (per source):
            snare_dist = (snare_range × route_length) / (2 × source_radius)
        capped at max_dist (QED max range).

        For multiple sources the most constraining (smallest) result is used.
        """
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
            "source_details": [],   # [{name, route_length, origin_diameter, snare_dist}]
            "message": "",
        }

        try:
            snare_range = float(radius)
            max_dist = float(max_dist)
        except (TypeError, ValueError):
            result["message"] = "radius and max_dist must be numeric."
            return result

        if snare_range <= 0 or max_dist <= 0:
            result["message"] = "radius and max_dist must be positive."
            return result

        normalized_sources = [str(n).strip().upper() for n in (source_names or []) if str(n).strip()]
        if not normalized_sources:
            result["message"] = "No source points provided."
            return result

        dest = (dest_name or "").strip().upper()
        if not dest:
            result["message"] = "Destination is required."
            return result

        precheck = self.validate_sources_for_destination(normalized_sources, dest)
        if not precheck.get("ok"):
            result["message"] = precheck.get("message") or "Invalid source/destination selection."
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

        # ── Calcul triangle SnarePlan par source ──────────────────────
        # Formule : snare_dist = snare_range × altitude_base_from_A / altitude
        # où A=destination, B=source, C=autre source explicitement sélectionnée
        directions = []
        source_details = []
        best_dist = max_dist          # on cherche le minimum contraint
        limiting_source = None

        for source_name in normalized_sources:
            src_coords = coords_cache[source_name]
            route_vec = end_coords - src_coords
            route_length = float(np.linalg.norm(route_vec))

            if route_length == 0.0:
                result["message"] = f"Source {source_name} is at the same position as the destination."
                return result

            route_hat = route_vec / route_length
            directions.append(route_hat)

            src_radius = self.get_radius_from_db(source_name)
            origin_diameter = 2.0 * src_radius
            physics_grid = self.get_physics_grid_from_db(source_name)

            # Candidat C virtuel : bord de la physics grid perpendiculaire à la route
            if physics_grid > 0:
                snare_dist = (snare_range * route_length) / physics_grid
                best_c_name = "physics_grid"
                best_origin_range = physics_grid
            elif origin_diameter > 0:
                snare_dist = (snare_range * route_length) / origin_diameter
                best_c_name = "diameter"
                best_origin_range = origin_diameter
            else:
                snare_dist = route_length / 2.0
                best_c_name = "mid_route"
                best_origin_range = 0.0
            snare_dist = min(snare_dist, route_length)
            best_snare = snare_dist

            # Candidats C : uniquement les autres sources explicitement sélectionnées
            for other in normalized_sources:
                if other != source_name:
                    c_coords = coords_cache.get(other)
                    if c_coords is None:
                        continue
                    bc_vec = c_coords - src_coords
                    proj = float(np.dot(bc_vec, route_hat))
                    perp_vec = bc_vec - proj * route_hat
                    altitude = float(np.linalg.norm(perp_vec))
                    if altitude < 1.0:
                        continue
                    altitude_base_from_a = route_length - proj
                    if altitude_base_from_a <= 0:
                        continue
                    candidate = (snare_range * altitude_base_from_a) / altitude
                    candidate = min(candidate, route_length)
                    if candidate < best_snare:
                        best_snare = candidate
                        best_c_name = other
                        best_origin_range = float(np.linalg.norm(bc_vec))

            source_details.append({
                "name": source_name,
                "route_length": route_length,
                "origin_diameter": origin_diameter,
                "origin_range": best_origin_range,
                "limiting_c": best_c_name,
                "snare_dist": best_snare,
            })
            snare_dist = best_snare

            if snare_dist < best_dist:
                best_dist = snare_dist
                limiting_source = source_name

        # ── Direction moyenne (pour affichage du point) ────────────────
        avg_dir = np.mean(directions, axis=0)
        avg_norm = float(np.linalg.norm(avg_dir))
        if avg_norm == 0:
            result["message"] = "Average direction norm is zero."
            return result
        avg_dir = avg_dir / avg_norm

        best_point = end_coords - (avg_dir * best_dist)

        # ── Zone d'interception : fenêtre ± snare_range autour du point ──
        limiting_detail = next(
            (d for d in source_details if d["name"] == limiting_source), None
        )
        limiting_route = limiting_detail["route_length"] if limiting_detail else float(best_dist)
        zone_start = max(0.0, best_dist - snare_range)
        zone_end   = min(limiting_route, best_dist + snare_range)

        result["ok"] = True
        result["distance_units"] = float(best_dist)
        result["distance_km"] = self.units_to_km(best_dist)
        result["zone_start_units"] = float(zone_start)
        result["zone_end_units"]   = float(zone_end)
        result["point"] = [float(v) for v in best_point]
        result["avg_dir"] = [float(v) for v in avg_dir]
        result["limiting_source"] = limiting_source
        result["source_details"] = source_details
        return result

    def calculate_snare_distance(self, source_names, dest_name, radius=20000, max_dist=250000, step=500):
        """Compatibility wrapper: returns only distance in km."""
        result = self.calculate_snare_solution(
            source_names,
            dest_name,
            radius=radius,
            max_dist=max_dist,
            step=step,
        )
        return result["distance_km"] if result.get("ok") else None