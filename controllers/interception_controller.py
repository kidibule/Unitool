"""Contrôleur d'interception quantique.

Gère la persistance des points de navigation et les calculs
de distance optimale pour le déploiement de snare.
"""

import numpy as np

class InterceptionController:
    """Expose les opérations métier du module d'interception."""

    def __init__(self, master):
        # Référence vers le contrôleur principal (accès DB/query/commit)
        self.master = master 

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

    def calculate_snare_distance(self, source_names, dest_name, radius=20000):
        """Calcule la distance maximale valide pour un déploiement de snare.

        Le calcul se base sur plusieurs sources et une destination afin de
        trouver le point le plus éloigné qui reste dans le rayon autorisé.
        """
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