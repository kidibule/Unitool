"""ScannerController — gere la recherche et edition de cibles."""

from models import Target


class ScannerController:
    """Controleur pour le scanner de cibles."""

    def __init__(self, app_controller):
        self.app = app_controller

    def search_targets(self, query: str) -> list:
        """Cherche des cibles par pseudo, org ou SID."""
        if len(query) <= 1:
            return []

        sql = """
        SELECT pseudo, org, ship, alignment, pvp_lvl, activity, sid, enlisted_date, language
        FROM targets
        WHERE pseudo LIKE ? OR org LIKE ? OR sid LIKE ?
        """
        return self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))

    def search_targets_as_models(self, query: str) -> list:
        """Cherche des cibles et retourne des objets Target."""
        if len(query) <= 1:
            return []

        sql = "SELECT * FROM targets WHERE pseudo LIKE ? OR org LIKE ? OR sid LIKE ?"
        rows = self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [Target.from_db_row(row) for row in rows]

    def get_target_full(self, pseudo: str) -> list:
        """Recupere toutes les colonnes d'une cible."""
        sql = (
            "SELECT pseudo, org, ship, threat, notes, date, wins, losses, alignment, "
            "pvp_lvl, activity, sid, org_rank, enlisted_date, language, affiliates "
            "FROM targets WHERE pseudo=?"
        )
        return self.app.query(sql, (pseudo.upper(),))

    def update_target(
        self,
        pseudo: str,
        org: str = None,
        ship: str = None,
        alignment: str = None,
        notes: str = None,
        sid: str = None,
        pvp_lvl: str = None,
        activity: str = None,
        language: str = None,
        **kwargs,
    ) -> None:
        """Met a jour les infos d'une cible avec validation simple des numeriques."""
        fields = {
            "org": org,
            "ship": ship,
            "alignment": alignment,
            "notes": notes,
            "sid": sid,
            "pvp_lvl": pvp_lvl,
            "activity": activity,
            "language": language,
        }
        fields.update(kwargs)

        numeric_fields = {"wins", "losses"}
        updates = []
        params = []

        for key, value in fields.items():
            if value is None:
                continue

            if key in numeric_fields:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = 0

            updates.append(f"{key}=?")
            params.append(value)

        if updates:
            params.append(pseudo.upper())
            sql = f"UPDATE targets SET {', '.join(updates)} WHERE pseudo=?"
            self.app.commit(sql, tuple(params))

    def add_target_note(self, pseudo: str, note_text: str) -> None:
        """Ajoute une note au journal de la cible, cree la cible si absente."""
        handle = str(pseudo or "").strip().upper()
        note = str(note_text or "").strip()
        if not handle or not note:
            return

        exists = self.app.query("SELECT pseudo FROM targets WHERE pseudo=?", (handle,))
        if not exists:
            self.app.commit(
                "INSERT INTO targets (pseudo, date, alignment) VALUES (?, strftime('%d/%m/%Y','now'), 'NEUTRE')",
                (handle,),
            )

        # Migration douce: si une ancienne note existe dans targets.notes, on l'importe une seule fois.
        legacy = self.app.query(
            "SELECT notes, date FROM targets WHERE pseudo=?",
            (handle,),
        )
        if legacy:
            legacy_note = str(legacy[0][0] or "").strip()
            legacy_date = str(legacy[0][1] or "").strip() or "N/A"
            if legacy_note:
                already = self.app.query(
                    "SELECT 1 FROM target_notes WHERE target_pseudo=? AND note_text=? LIMIT 1",
                    (handle, legacy_note),
                )
                if not already:
                    created = f"{legacy_date} 00:00" if "/" in legacy_date else legacy_date
                    self.app.db.add_target_note(handle, legacy_note, created)

        self.app.db.add_target_note(handle, note)

    def get_target_notes(self, pseudo: str, limit: int = 50) -> list:
        """Retourne les notes d'une cible (id, note_text, created_at)."""
        return self.app.db.get_target_notes(pseudo, limit=limit)

    def update_target_note(self, pseudo: str, note_id: int, note_text: str) -> None:
        """Modifie une entree du journal de la cible."""
        self.app.db.update_target_note(pseudo, note_id, note_text)

    def delete_target_note(self, pseudo: str, note_id: int) -> None:
        """Supprime une entree du journal de la cible."""
        self.app.db.delete_target_note(pseudo, note_id)

    def export_targets_csv(self) -> list:
        """Recupere tous les targets pour export."""
        rows = self.app.query("SELECT * FROM targets")
        try:
            if hasattr(self.app, "log"):
                self.app.log(f"Exporting {len(rows)} targets to CSV", source="SCANNER")
        except Exception:
            pass
        return rows
