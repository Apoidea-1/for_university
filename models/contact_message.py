from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContactMessage(models.Model):
    _name = "networkpilot.contact_message"
    _description = "Message Between Contacts"
    _order = "sent_at desc, id desc"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        required=True,
        ondelete="cascade",
        index=True,
    )
    sender_contact_id = fields.Many2one(
        "networkpilot.contact",
        string="Sender",
        required=True,
        ondelete="cascade",
        index=True,
    )
    recipient_contact_id = fields.Many2one(
        "networkpilot.contact",
        string="Recipient",
        required=True,
        ondelete="cascade",
        index=True,
    )
    pair_key = fields.Char(string="Pair Key", required=True, copy=False, readonly=True, index=True)
    body = fields.Text(string="Message", required=True)
    message_type = fields.Selection(
        [
            ("chat", "Chat"),
            ("note", "Note"),
            ("follow_up", "Follow Up"),
            ("meeting", "Meeting"),
        ],
        string="Message Type",
        default="chat",
        required=True,
        index=True,
    )
    sent_at = fields.Datetime(string="Sent At", default=fields.Datetime.now, required=True, index=True)
    metadata_json = fields.Text(string="Metadata (JSON)", default="{}", required=True)
    is_ai_draft = fields.Boolean(string="Created From AI Draft", default=False)

    @api.model
    def build_pair_key(self, sender_contact_id, recipient_contact_id):
        first, second = sorted([int(sender_contact_id), int(recipient_contact_id)])
        return f"{first}:{second}"

    @api.constrains("sender_contact_id", "recipient_contact_id")
    def _check_distinct_contacts(self):
        for record in self:
            if record.sender_contact_id and record.sender_contact_id == record.recipient_contact_id:
                raise ValidationError("A message requires two different contacts.")

    @api.constrains("user_id", "sender_contact_id", "recipient_contact_id")
    def _check_contact_ownership(self):
        for record in self:
            contacts = record.sender_contact_id | record.recipient_contact_id
            if contacts and any(contact.user_id != record.user_id for contact in contacts):
                raise ValidationError("You can only create messages for your own contacts.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sender_contact_id = vals.get("sender_contact_id")
            recipient_contact_id = vals.get("recipient_contact_id")
            if sender_contact_id and recipient_contact_id:
                vals["pair_key"] = self.build_pair_key(sender_contact_id, recipient_contact_id)
            vals.setdefault("user_id", self.env.user.id)
            vals.setdefault("metadata_json", "{}")
        records = super().create(vals_list)
        records._sync_relationship_activity()
        return records

    def unlink(self):
        pair_keys = self.mapped("pair_key")
        result = super().unlink()
        self.env["networkpilot.contact_relationship"]._sync_message_stats(pair_keys)
        return result

    def _sync_relationship_activity(self):
        relationships = self.env["networkpilot.contact_relationship"]
        for record in self:
            relationship = relationships.search(
                [
                    ("user_id", "=", record.user_id.id),
                    ("pair_key", "=", record.pair_key),
                ],
                limit=1,
            )
            if not relationship:
                relationship = relationships.create(
                    {
                        "user_id": record.user_id.id,
                        "source_contact_id": record.sender_contact_id.id,
                        "target_contact_id": record.recipient_contact_id.id,
                        "relationship_type": "other",
                        "strength": 1.0,
                        "shared_context": False,
                        "notes": False,
                        "last_active_at": record.sent_at,
                    }
                )
            relationship._sync_message_stats([record.pair_key])
