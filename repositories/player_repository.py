"""Repository Targets — opérations sur les joueurs pistés et leurs notes."""

import time


class PlayerRepository:
    """Toutes les opérations DB liées aux targets et à leurs notes."""

    def __init__(self, db):
        """
        Args:
            db: instance DBConnection (conn + cursor + query/commit)
        """
        self._db = db

    # ------------------------------------------------------------------
    # Intel (résumé rapide d'un joueur)
    # ------------------------------------------------------------------

    def upsert_intel(self, data: dict) -> None:
        """Insère ou met à jour les infos récupérées par le scanner."""
        sql = """
            INSERT INTO players
                (pseudo, org, sid, affiliates, org_rank, enlisted_date, language, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pseudo) DO UPDATE SET
                org=excluded.org,
                sid=excluded.sid,
                affiliates=excluded.affiliates,
                org_rank=excluded.org_rank,
                enlisted_date=excluded.enlisted_date,
                language=excluded.language,
                date=excluded.date
        """
        handle = str(data.get("Handle", "")).strip().upper()
        params = (
            handle,
            data["OrgaNom"],
            data["SID"],
            data.get("Affiliates", "NONE"),
            data["Rang"],
            data["Date"],
            data["Language"],
            time.strftime("%d/%m/%Y"),
        )
        self._db.commit(sql, params)

    def get_by_handle(self, handle: str) -> dict | None:
        """Retourne un résumé de joueur pour la prévisualisation."""
        handle = str(handle or "").strip()
        if not handle:
            return None
        sql = """
            SELECT org, sid, org_rank, enlisted_date, language
            FROM players
            WHERE UPPER(pseudo) = UPPER(?)
        """
        rows = self._db.query(sql, (handle,))
        if rows:
            row = rows[0]
            return {
                "OrgaNom": row[0],
                "SID": row[1],
                "Rang": row[2],
                "Date": row[3],
                "Language": row[4],
            }
        return None

    # ------------------------------------------------------------------
    # Notes de target
    # ------------------------------------------------------------------

    def add_note(self, pseudo: str, note_text: str, created_at: str | None = None) -> None:
        """Ajoute une note horodatée au journal d'une target."""
        handle = str(pseudo or "").strip().upper()
        note = str(note_text or "").strip()
        if not handle or not note:
            return

        created = created_at or time.strftime("%d/%m/%Y %H:%M")
        self._db.commit(
            "INSERT INTO player_notes (player_pseudo, note_text, created_at) VALUES (?, ?, ?)",
            (handle, note, created),
        )
        # Compatibilité : conserve la dernière note dans la table players.
        self._db.commit(
            "UPDATE players SET notes=?, date=? WHERE pseudo=?",
            (note, time.strftime("%d/%m/%Y"), handle),
        )

    def get_notes(self, pseudo: str, limit: int = 50) -> list:
        """Retourne les notes d'une target, de la plus récente à la plus ancienne."""
        handle = str(pseudo or "").strip().upper()
        if not handle:
            return []

        sql = (
            "SELECT id, note_text, created_at FROM player_notes "
            "WHERE player_pseudo=? ORDER BY id DESC"
        )
        params: tuple = (handle,)
        if limit and int(limit) > 0:
            sql += " LIMIT ?"
            params = (handle, int(limit))

        return self._db.query(sql, params)

    def update_note(self, pseudo: str, note_id: int, note_text: str) -> None:
        """Modifie une note existante d'une target."""
        handle = str(pseudo or "").strip().upper()
        note = str(note_text or "").strip()
        if not handle or not note:
            return
        self._db.commit(
            "UPDATE player_notes SET note_text=? WHERE id=? AND player_pseudo=?",
            (note, int(note_id), handle),
        )

    def delete_note(self, pseudo: str, note_id: int) -> None:
        """Supprime une note du journal d'une target."""
        handle = str(pseudo or "").strip().upper()
        if not handle:
            return
        self._db.commit(
            "DELETE FROM player_notes WHERE id=? AND player_pseudo=?",
            (int(note_id), handle),
        )

    # ------------------------------------------------------------------
    # Vaisseaux de joueur (player_ships)
    # ------------------------------------------------------------------

    def add_player_ship(self, pseudo: str, ship: str) -> None:
        """Associe un vaisseau à un joueur."""
        if ship and ship.strip():
            self._db.commit(
                "INSERT OR IGNORE INTO player_ships (pseudo, ship) VALUES (?, ?)",
                (pseudo, ship.upper()),
            )

    def get_player_ships(self, pseudo: str) -> list[str]:
        """Retourne tous les vaisseaux associés à un joueur."""
        rows = self._db.query(
            "SELECT ship FROM player_ships WHERE pseudo = ? ORDER BY ship",
            (pseudo,),
        )
        return [row[0] for row in rows]

    def delete_player_ship(self, pseudo: str, ship: str) -> None:
        """Supprime un vaisseau d'un joueur."""
        self._db.commit(
            "DELETE FROM player_ships WHERE pseudo = ? AND ship = ?",
            (pseudo, ship),
        )

    def delete_all_player_ships(self, pseudo: str) -> None:
        """Supprime tous les vaisseaux d'un joueur."""
        self._db.commit(
            "DELETE FROM player_ships WHERE pseudo = ?",
            (pseudo,),
        )
