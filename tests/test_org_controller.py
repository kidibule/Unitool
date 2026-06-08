"""Tests unitaires pour controllers/org_controller.py."""

from unittest.mock import MagicMock, patch

from controllers.org_controller import OrgController


def make_controller_with_events(rows):
    app = MagicMock()
    app.db.orgs.get_events.return_value = rows
    app.get_setting.return_value = ""
    return OrgController(app)


class TestPublishEventToDiscord:
    def test_retourne_erreur_si_event_introuvable(self):
        ctrl = make_controller_with_events([])

        ok, msg = ctrl.publish_event_to_discord(999)

        assert ok is False
        assert "introuvable" in msg.lower()

    def test_publie_evenement_sur_webhook(self):
        ctrl = make_controller_with_events(
            [(1, "2026-06-08", "21:30", "Briefing", "Point tactique", "Discord", "ALPHA")]
        )

        fake_response = MagicMock()
        fake_response.status = 204
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = fake_response
        fake_cm.__exit__.return_value = False

        with patch("controllers.org_controller.request.urlopen", return_value=fake_cm) as mock_urlopen:
            ok, msg = ctrl.publish_event_to_discord(1)

        assert ok is True
        assert "discord" in msg.lower()
        assert mock_urlopen.called


class TestWebhookSettings:
    def test_get_webhook_depuis_settings(self):
        ctrl = make_controller_with_events([])
        ctrl.app.get_setting.return_value = "https://discord.com/api/webhooks/custom"

        value = ctrl.get_discord_webhook_url()

        assert value == "https://discord.com/api/webhooks/custom"

    def test_set_webhook_enregistre_setting(self):
        ctrl = make_controller_with_events([])

        ctrl.set_discord_webhook_url("https://discord.com/api/webhooks/new")

        ctrl.app.set_setting.assert_called_once_with(
            "discord_events_webhook_url",
            "https://discord.com/api/webhooks/new",
        )
