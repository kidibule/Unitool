"""Repository Organisations — opérations sur les orgs et leurs notes."""

import json
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
    # Agenda org (org_events)
    # ------------------------------------------------------------------

    def get_event_dates_for_month(self, year: int, month: int) -> set[str]:
        """Retourne les dates (YYYY-MM-DD) ayant au moins un événement sur un mois."""
        month_str = f"{int(year):04d}-{int(month):02d}"
        rows = self._db.query(
            "SELECT DISTINCT date FROM org_events WHERE date LIKE ?",
            (f"{month_str}%",),
        )
        return {str(r[0]) for r in rows if r and r[0]}

    def get_events(self) -> list:
        """Retourne tous les événements triés par date/heure/id."""
        return self._db.query(
            "SELECT id, date, time, title, description, location, participants "
            "FROM org_events ORDER BY date, time, id",
            (),
        )

    def add_event(
        self,
        date_str: str,
        time_str: str,
        title: str,
        description: str,
        location: str,
        participants: str,
    ) -> None:
        """Ajoute un événement à l'agenda org."""
        self._db.commit(
            "INSERT INTO org_events (date, time, title, description, location, participants) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(date_str or "").strip(),
                str(time_str or "").strip(),
                str(title or "").strip(),
                str(description or "").strip(),
                str(location or "").strip(),
                str(participants or "").strip(),
            ),
        )

    def update_event(
        self,
        event_id: int,
        title: str,
        time_str: str,
        description: str,
        location: str,
        participants: str,
    ) -> None:
        """Met à jour un événement existant."""
        self._db.commit(
            "UPDATE org_events "
            "SET title=?, time=?, description=?, location=?, participants=? WHERE id=?",
            (
                str(title or "").strip(),
                str(time_str or "").strip(),
                str(description or "").strip(),
                str(location or "").strip(),
                str(participants or "").strip(),
                int(event_id),
            ),
        )

    def delete_event(self, event_id: int) -> None:
        """Supprime un événement par son identifiant."""
        self._db.commit("DELETE FROM org_events WHERE id=?", (int(event_id),))

    # ------------------------------------------------------------------
    # Membres visibles (organizations.visible_members)
    # ------------------------------------------------------------------

    def get_visible_members(self, sid: str) -> list:
        """Retourne la liste des membres visibles d'une organisation."""
        org_sid = str(sid or "").strip().upper()
        if not org_sid:
            return []

        rows = self._db.query(
            "SELECT visible_members FROM organizations WHERE sid = ?",
            (org_sid,),
        )
        if not rows:
            return []

        try:
            return json.loads(rows[0][0] or "[]")
        except Exception:
            return []

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
