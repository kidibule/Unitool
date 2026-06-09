"""OrgController — gère la logique métier des organisations."""

import json
from datetime import date
from urllib import error, request

from models import OrgEvent, Organization

class OrgController:
    """Contrôleur pour la gestion des organisations."""

    DISCORD_EVENTS_WEBHOOK_URL = (
        "https://discord.com/api/webhooks/1513509945738399875/"
        "cn4cdbtCQgWv1g2L0bmbkoa-zwvOFfXLON113hJ9vOrATRVc1bTRKyCZLBI7J3fG39Nv"
    )

    def __init__(self, app_controller):
        """Initialise avec l'instance AppController pour l'accès DB."""
        self.app = app_controller

    def get_discord_webhook_url(self) -> str:
        """Retourne le webhook Discord configuré en settings (ou fallback)."""
        try:
            value = self.app.get_setting("discord_events_webhook_url", "")
        except Exception:
            value = ""
        return str(value or self.DISCORD_EVENTS_WEBHOOK_URL).strip()

    def set_discord_webhook_url(self, webhook_url: str) -> None:
        """Enregistre le webhook Discord de publication d'événements."""
        self.app.set_setting("discord_events_webhook_url", str(webhook_url or "").strip())

    def search_orgs(self, query: str) -> list:
        """Recherche rapide pour affichage en liste/vue."""
        if len(query) < 2:
            return []
        
        # AJOUT : On récupère alignment et updated_at directement dans la recherche
        sql = """
        SELECT sid, name, tag, member_count, org_type, specialization, alignment, updated_at
        FROM organizations 
        WHERE sid LIKE ? OR name LIKE ? OR tag LIKE ?
        """
        return self.app.query(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))

    # ------------------------------------------------------------------
    # Agenda organisation (org_events)
    # ------------------------------------------------------------------

    def get_event_dates_for_month(self, year: int, month: int) -> set[str]:
        """Retourne les dates contenant des événements pour un mois donné."""
        try:
            return self.app.db.orgs.get_event_dates_for_month(year, month)
        except Exception:
            return set()

    def get_events(self) -> list[OrgEvent]:
        """Retourne tous les événements triés en objets métier OrgEvent."""
        try:
            rows = self.app.db.orgs.get_events()
            return [OrgEvent.from_db_row(row) for row in rows]
        except Exception:
            return []

    def add_event(
        self,
        date_str: str,
        time_str: str,
        title: str,
        description: str = "",
        location: str = "",
        participants: str = "",
    ) -> None:
        """Ajoute un événement d'organisation."""
        self.app.db.orgs.add_event(date_str, time_str, title, description, location, participants)

    def update_event(
        self,
        event_id: int,
        title: str,
        time_str: str,
        description: str = "",
        location: str = "",
        participants: str = "",
    ) -> None:
        """Met à jour un événement d'organisation."""
        self.app.db.orgs.update_event(event_id, title, time_str, description, location, participants)

    def delete_event(self, event_id: int) -> None:
        """Supprime un événement d'organisation."""
        self.app.db.orgs.delete_event(event_id)

    def publish_event_to_discord(self, event_id: int, webhook_url: str | None = None) -> tuple[bool, str]:
        """Publie un événement sur Discord via webhook.

        Returns:
            tuple[bool, str]: (succès, message utilisateur)
        """
        rows = self.app.db.orgs.get_events()
        events = [OrgEvent.from_db_row(row) for row in rows]
        target = next((evt for evt in events if evt.id == int(event_id)), None)
        if target is None:
            return False, "Event not found."

        hook = str(webhook_url or self.get_discord_webhook_url()).strip()
        if not hook:
            return False, "Discord webhook is not configured."

        try:
            d = date.fromisoformat(str(target.date or ""))
            date_label = d.strftime("%d/%m/%Y")
        except Exception:
            date_label = str(target.date or "")

        desc = str(target.description or "").strip()
        if len(desc) > 500:
            desc = f"{desc[:497]}..."

        lines = [
            "@everyone",
            f"📅 **{target.title or 'EVENT'}**",
            f"**Date:** {date_label}",
            f"**Time:** {target.time or '--:--'}",
        ]
        if target.location:
            lines.append(f"**Location:** {target.location}")
        if target.participants:
            lines.append(f"**Participants:** {target.participants}")
        if desc:
            lines.append(f"**Details:** {desc}")

        payload = {
            "content": "\n".join(lines),
            "allowed_mentions": {"parse": ["everyone"]},
        }

        req = request.Request(
            hook,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Unitool-OrgWebhook/1.0",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as resp:
                if int(getattr(resp, "status", resp.getcode())) >= 400:
                    return False, "Discord rejected the publish request."
        except error.HTTPError as ex:
            raw = ""
            try:
                raw = ex.read().decode("utf-8", errors="replace").strip()
            except Exception:
                raw = ""

            if raw:
                try:
                    parsed = json.loads(raw)
                    message = str(parsed.get("message", "")).strip()
                    code = parsed.get("code")
                    if message and code is not None:
                        return False, f"Discord HTTP error {ex.code}: {message} (code {code})."
                    if message:
                        return False, f"Discord HTTP error {ex.code}: {message}."
                except Exception:
                    return False, f"Discord HTTP error {ex.code}: {raw}"

            return False, f"Discord HTTP error {ex.code}."
        except error.URLError as ex:
            return False, f"Discord network error: {ex.reason}"
        except Exception as ex:
            return False, f"Publish failed: {ex}"

        return True, "Event published to Discord."

    def get_visible_members(self, sid: str) -> list:
        """Retourne les membres visibles d'une org sous forme de liste de dicts."""
        try:
            return self.app.db.orgs.get_visible_members(sid)
        except Exception:
            return []

    def get_org_model(self, sid: str) -> Organization:
        """Récupère une organisation et retourne un objet Organization."""
        sql = "SELECT * FROM organizations WHERE sid = ?"
        row = self.app.query(sql, (sid.upper(),))
        if row:
            # Utilise la méthode from_db_row du modèle pour mapper proprement
            return Organization.from_db_row(row[0])
        return None

    # Colonnes autorisées pour éviter toute injection SQL via noms de colonnes dynamiques
    _ALLOWED_ORG_COLUMNS = frozenset({
        "name", "tag", "description", "member_count", "visible_members",
        "redacted_members", "ranks", "org_type", "specialization",
        "allies", "enemies", "neutrals", "updated_at", "alignment",
    })

    def update_org(self, sid: str, **kwargs) -> None:
        """Met à jour les informations d'une organisation avec protection des types."""
        
        # Champs numériques à valider
        numeric_fields = ['member_count']
        
        cleaned_kwargs = {}
        for key, value in kwargs.items():
            if key not in self._ALLOWED_ORG_COLUMNS:
                continue
            if key in numeric_fields:
                try:
                    cleaned_kwargs[key] = int(value)
                except (ValueError, TypeError):
                    cleaned_kwargs[key] = 0
            # On s'assure que alignment est en majuscule si présent
            elif key == "alignment" and value:
                cleaned_kwargs[key] = value.upper()
            elif value is not None:
                cleaned_kwargs[key] = value

        if cleaned_kwargs:
            updates = [f"{key}=?" for key in cleaned_kwargs.keys()]
            params = list(cleaned_kwargs.values())
            params.append(sid.upper()) # Clause WHERE

            sql = f"UPDATE organizations SET {', '.join(updates)} WHERE sid=?"
            self.app.commit(sql, tuple(params))
            try:
                if hasattr(self.app, "notify_stats_changed"):
                    self.app.notify_stats_changed()
            except Exception:
                pass
            
            if hasattr(self.app, "log"):
                self.app.log(f"Org {sid} updated (Fields: {list(cleaned_kwargs.keys())})", source="ORG_CTRL")

    def get_diplomatic_report(self, sid: str) -> dict:
        """Génère un dictionnaire des relations pour la vue."""
        org = self.get_org_model(sid)
        if not org:
            return {}

        return {
            "alignment": org.alignment,
            "allies": org.allies.split(",") if org.allies and org.allies != "NONE" else [],
            "enemies": org.enemies.split(",") if org.enemies and org.enemies != "NONE" else [],
            "neutrals": org.neutrals.split(",") if org.neutrals and org.neutrals != "NONE" else []
        }
    
    def save_scanned_org(self, sid, name, **kwargs):
        """Méthode 'tout-en-un' pour le Scrapbot."""
        sid = sid.upper()
        if self.get_org_model(sid):
            self.update_org(sid, **kwargs)
        else:
            # Logique d'insertion si l'org n'existe pas
            cols = ["sid", "name"] + list(kwargs.keys())
            placeholders = ", ".join(["?"] * len(cols))
            vals = [sid, name] + list(kwargs.values())
            
            sql = f"INSERT INTO organizations ({', '.join(cols)}) VALUES ({placeholders})"
            self.app.commit(sql, tuple(vals))
            try:
                if hasattr(self.app, "notify_stats_changed"):
                    self.app.notify_stats_changed()
            except Exception:
                pass

    def add_org_note(self, sid: str, note_text: str) -> None:
        """Ajoute une note au journal d'une organisation."""
        org_sid = str(sid or "").strip().upper()
        note = str(note_text or "").strip()
        if not org_sid or not note:
            return

        org = self.get_org_model(org_sid)
        if org is None:
            self.app.commit(
                "INSERT INTO organizations (sid, name, updated_at) VALUES (?, ?, strftime('%d/%m/%Y','now'))",
                (org_sid, org_sid),
            )
            try:
                if hasattr(self.app, "notify_stats_changed"):
                    self.app.notify_stats_changed()
            except Exception:
                pass

        # Migration douce de l'ancienne description en premiere entree du journal.
        org = self.get_org_model(org_sid)
        if org and org.description and str(org.description).strip():
            legacy_note = str(org.description).strip()
            already = self.app.query(
                "SELECT 1 FROM org_notes WHERE org_sid=? AND note_text=? LIMIT 1",
                (org_sid, legacy_note),
            )
            if not already:
                legacy_date = str(org.updated_at or "").strip() or "N/A"
                created = f"{legacy_date} 00:00" if "/" in legacy_date else legacy_date
                self.app.db.orgs.add_note(org_sid, legacy_note, created)

        self.app.db.orgs.add_note(org_sid, note)

    def get_org_notes(self, sid: str, limit: int = 50) -> list:
        """Retourne les notes d'organisation (id, note_text, created_at)."""
        return self.app.db.orgs.get_notes(sid, limit=limit)

    def update_org_note(self, sid: str, note_id: int, note_text: str) -> None:
        """Modifie une entree du journal d'organisation."""
        self.app.db.orgs.update_note(sid, note_id, note_text)

    def delete_org_note(self, sid: str, note_id: int) -> None:
        """Supprime une entree du journal d'organisation."""
        self.app.db.orgs.delete_note(sid, note_id)