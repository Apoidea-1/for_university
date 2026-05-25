from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContactRelationship(models.Model):
    _name = "networkpilot.contact_relationship"
    _description = "Relationship Between Contacts"
    _order = "strength desc, last_active_at desc, id desc"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        required=True,
        ondelete="cascade",
        index=True,
    )
    source_contact_id = fields.Many2one(
        "networkpilot.contact",
        string="Source Contact",
        required=True,
        ondelete="cascade",
        index=True,
    )
    target_contact_id = fields.Many2one(
        "networkpilot.contact",
        string="Target Contact",
        required=True,
        ondelete="cascade",
        index=True,
    )
    pair_key = fields.Char(string="Pair Key", required=True, copy=False, readonly=True, index=True)
    relationship_type = fields.Selection(
        [
            ("professional", "Professional"),
            ("mentor", "Mentor"),
            ("peer", "Peer"),
            ("friend", "Friend"),
            ("client", "Client"),
            ("community", "Community"),
            ("broker", "Broker"),
            ("other", "Other"),
        ],
        string="Relationship Type",
        default="professional",
        required=True,
        index=True,
    )
    strength = fields.Float(string="Strength", default=1.0, required=True)
    shared_context = fields.Char(string="Shared Context")
    notes = fields.Text(string="Notes")
    last_active_at = fields.Datetime(string="Last Active At", default=fields.Datetime.now, index=True)
    message_count = fields.Integer(string="Message Count", default=0, required=True)
    interaction_count = fields.Integer(string="Interaction Count", default=0, required=True)
    is_bridge = fields.Boolean(string="Bridge Contact Pair", default=False)

    _sql_constraints = [
        ("user_pair_uniq", "unique(user_id, pair_key)", "A relationship for this contact pair already exists."),
    ]

    @api.model
    def build_pair_key(self, source_contact_id, target_contact_id):
        first, second = sorted([int(source_contact_id), int(target_contact_id)])
        return f"{first}:{second}"

    @api.constrains("source_contact_id", "target_contact_id")
    def _check_distinct_contacts(self):
        for record in self:
            if record.source_contact_id and record.source_contact_id == record.target_contact_id:
                raise ValidationError("A relationship requires two different contacts.")

    @api.constrains("user_id", "source_contact_id", "target_contact_id")
    def _check_contact_ownership(self):
        for record in self:
            contacts = record.source_contact_id | record.target_contact_id
            if contacts and any(contact.user_id != record.user_id for contact in contacts):
                raise ValidationError("You can only relate contacts that belong to the same user.")

    @api.constrains("strength")
    def _check_strength(self):
        for record in self:
            if record.strength <= 0:
                raise ValidationError("Relationship strength must be positive.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            source_contact_id = vals.get("source_contact_id")
            target_contact_id = vals.get("target_contact_id")
            if source_contact_id and target_contact_id:
                vals["pair_key"] = self.build_pair_key(source_contact_id, target_contact_id)
            vals.setdefault("user_id", self.env.user.id)
        return super().create(vals_list)

    def write(self, vals):
        if "source_contact_id" in vals or "target_contact_id" in vals:
            for record in self:
                source_contact_id = vals.get("source_contact_id", record.source_contact_id.id)
                target_contact_id = vals.get("target_contact_id", record.target_contact_id.id)
                vals["pair_key"] = self.build_pair_key(source_contact_id, target_contact_id)
                break
        return super().write(vals)

    def _sync_message_stats(self, pair_keys):
        if not pair_keys:
            return
        Message = self.env["networkpilot.contact_message"]
        for relationship in self.search(
            [
                ("pair_key", "in", list(set(pair_keys))),
            ]
        ):
            messages = Message.search(
                [
                    ("user_id", "=", relationship.user_id.id),
                    ("pair_key", "=", relationship.pair_key),
                ],
                order="sent_at desc, id desc",
            )
            relationship.write(
                {
                    "message_count": len(messages),
                    "last_active_at": messages[:1].sent_at if messages else relationship.last_active_at,
                }
            )
