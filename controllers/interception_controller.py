import numpy as np

class InterceptionController:
    def __init__(self, master):
        self.master = master 

    def get_location_names(self):
        rows = self.master.query("SELECT name FROM locations ORDER BY name ASC")
        return [row[0] for row in rows]

    def get_coords_from_db(self, name):
        res = self.master.query("SELECT x, y, z FROM locations WHERE name = ?", (name,))
        if res:
            return np.array(res[0])
        return None

    def upsert_location(self, name, x, y, z, loc_type="POI"):
        location_name = (name or "").strip().upper()
        if not location_name:
            raise ValueError("Location name is required.")

        try:
            fx = float(x)
            fy = float(y)
            fz = float(z)
        except (TypeError, ValueError):
            raise ValueError("Coordinates must be numeric.")

        self.master.commit(
            """
            INSERT INTO locations (name, x, y, z, type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                x = excluded.x,
                y = excluded.y,
                z = excluded.z,
                type = excluded.type
            """,
            (location_name, fx, fy, fz, (loc_type or "POI").strip().upper()),
        )

        return location_name

    def delete_location(self, name):
        location_name = (name or "").strip().upper()
        if not location_name or location_name == "NO DATA":
            raise ValueError("Location name is required.")

        self.master.commit(
            "DELETE FROM locations WHERE name = ?",
            (location_name,),
        )

        return location_name

    def calculate_snare_distance(self, source_names, dest_name, radius=20000):
        sources_coords = [self.get_coords_from_db(n) for n in source_names if self.get_coords_from_db(n) is not None]
        end_coords = self.get_coords_from_db(dest_name)

        if not sources_coords or end_coords is None:
            return None

        # Calcul de l'axe moyen
        directions = []
        for s in sources_coords:
            dir_vec = end_coords - s
            norm = np.linalg.norm(dir_vec)
            if norm > 0:
                directions.append(dir_vec / norm)
        
        avg_dir = np.mean(directions, axis=0)
        avg_dir /= np.linalg.norm(avg_dir)

        # Recherche de la distance maximale valide
        best_dist = 0
        for dist in range(0, 250000, 500): 
            current_p = end_coords - (avg_dir * dist)
            valid = True
            for s in sources_coords:
                line_vec = end_coords - s
                t = np.dot(current_p - s, line_vec) / np.dot(line_vec, line_vec)
                t = max(0, min(1, t))
                closest = s + t * line_vec
                
                if np.linalg.norm(current_p - closest) > radius:
                    valid = False
                    break
            
            if valid:
                best_dist = dist
            else:
                break 
                
        return best_dist # Retourne maintenant une distance en km