"""Repository Organisations — opérations sur les orgs et leurs notes."""

import time


class OrgRepository:
    """Toutes les opérations DB liées aux organisations et à leurs notes."""

    def __init__(self, db):
        """
        Args:
            db: instance DBConnection (conn + cursor + query/commit)
        """
        self._db = db

    # ------------------------------------------------------------------
    # Notes d'organisation
    # ------------------------------------------------------------------

    def add_note(self, sid: str, note_text: str, created_at: str | None = None) -> None:
        """Ajoute une note horodatée au journal d'une organisation."""
        org_sid = str(sid or "").strip().upper()
        note = str(note_text or "").strip()
        if not org_sid or not note:
            return

        created = created_at or time.strftime("%d/%m/%Y %H:%M")
        self._db.commit(
            "INSERT INTO org_notes (org_sid, note_text, created_at) VALUES (?, ?, ?)",
            (org_sid, note, created),
        )
        # Compatibilité legacy : description conserve la dernière note.
        self._db.commit(
            "UPDATE organizations SET description=?, updated_at=? WHERE sid=?",
            (note, time.strftime("%d/%m/%Y"), org_sid),
        )

    def get_notes(self, sid: str, limit: int = 50) -> list:
        """Retourne les notes d'une organisation, de la plus récente à la plus ancienne."""
        org_sid = str(sid or "").strip().upper()
        if not org_sid:
            return []

        sql = (
            "SELECT id, note_text, created_at FROM org_notes "
            "WHERE org_sid=? ORDER BY id DESC"
        )
        params: tuple = (org_sid,)
        if limit and int(limit) > 0:
            sql += " LIMIT ?"
            params = (org_sid, int(limit))

        return self._db.query(sql, params)

    def update_note(self, sid: str, note_id: int, note_text: str) -> None:
        """Modifie une note existante d'une organisation."""
        org_sid = str(sid or "").strip().upper()
        note = str(note_text or "").strip()
        if not org_sid or not note:
            return
        self._db.commit(
            "UPDATE org_notes SET note_text=? WHERE id=? AND org_sid=?",
            (note, int(note_id), org_sid),
        )

    def delete_note(self, sid: str, note_id: int) -> None:
        """Supprime une note du journal d'une organisation."""
        org_sid = str(sid or "").strip().upper()
        if not org_sid:
            return
        self._db.commit(
            "DELETE FROM org_notes WHERE id=? AND org_sid=?",
            (int(note_id), org_sid),
        )
