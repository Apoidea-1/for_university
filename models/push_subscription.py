from odoo import models, fields


class PushSubscription(models.Model):
    _name = 'networkpilot.push_subscription'
    _description = 'Web Push Subscription'
    _order = 'id desc'

    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        ondelete='cascade', index=True,
    )
    endpoint = fields.Char(string='Endpoint', required=True)
    p256dh   = fields.Char(string='P256DH Key', required=True)
    auth     = fields.Char(string='Auth Key', required=True)

    _sql_constraints = [
        ('endpoint_unique', 'unique(endpoint)', 'Endpoint must be unique'),
    ]

    # ── VAPID keys (generated once, hardcoded for this project) ──────────
    _VAPID_PRIVATE_PEM = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgm9hnIl0qSuXgFQ2s\n"
        "mCrkVkbI89oR9UuLxWAxQt00xPChRANCAASzXHvgZm7QHUhdDM2ef9FPCVARcq7B\n"
        "NJ4JIBsDc5mTZfNvFAHaZ1AdoEafnsTDuTJkciuqZtJaDwycTrXcb0nJ\n"
        "-----END PRIVATE KEY-----\n"
    )
    _VAPID_PUBLIC_KEY = (
        "BLNce-BmbtAdSF0MzZ5_0U8JUBFyrsE0ngkgGwNzmZNl828UAdpnUB2gRp-exMO5"
        "MmRyK6pm0loPDJxOtdxvSck"
    )
    _VAPID_CLAIMS = {"sub": "mailto:admin@networkpilot.local"}

    def _send_push(self, endpoint, p256dh, auth, payload: dict):
        """Send a single Web Push message. Returns True on success."""
        import json
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            return False
        try:
            webpush(
                subscription_info={
                    "endpoint": endpoint,
                    "keys": {"p256dh": p256dh, "auth": auth},
                },
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=self._VAPID_PRIVATE_PEM,
                vapid_claims=self._VAPID_CLAIMS,
            )
            return True
        except Exception:
            return False

    def cron_send_push_reminders(self):
        """Called every 5 minutes by ir.cron. Sends push for due reminders."""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        window_end = now + timedelta(minutes=6)   # look 6 min ahead
        window_start = now - timedelta(minutes=1) # avoid very old ones

        Reminder = self.env['networkpilot.reminder'].sudo()
        reminders = Reminder.search([
            ('status', '=', 'active'),
            ('due_date', '>=', fields.Datetime.to_string(window_start)),
            ('due_date', '<=', fields.Datetime.to_string(window_end)),
            ('push_notified', '=', False),
        ])

        for reminder in reminders:
            subs = self.sudo().search([('user_id', '=', reminder.user_id.id)])
            sent = False
            for sub in subs:
                contact_name = (
                    reminder.contact_id.full_name if reminder.contact_id else None
                )
                payload = {
                    "title": reminder.title,
                    "body": (
                        f"Контакт: {contact_name}" if contact_name
                        else reminder.description or "Напоминание NetWorkPilot"
                    ),
                    "tag": f"reminder-{reminder.id}",
                    "url": "/app/reminders",
                }
                ok = self._send_push(sub.endpoint, sub.p256dh, sub.auth, payload)
                if ok:
                    sent = True
                else:
                    # Remove invalid subscription
                    sub.unlink()
            if sent:
                reminder.write({'push_notified': True})
