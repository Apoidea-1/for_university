from odoo import models, fields, api

class Contact(models.Model):
    _name = 'networkpilot.contact'
    _description = 'Contact'
    _rec_name = 'full_name'
    _order = 'last_interaction_date desc, id desc'

    # Note: Odoo standard models like res.partner could be used, but since we are migrating
    # an existing DB schema strictly, we'll create a custom model first to keep it 1:1.

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, ondelete='cascade', index=True)
    
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name')
    
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)

    company = fields.Char(string='Company')
    role = fields.Char(string='Role')
    source_where_met = fields.Char(string='Source Where Met')
    
    email = fields.Char(string='Email', index=True)
    phone = fields.Char(string='Phone')
    telegram = fields.Char(string='Telegram')
    linkedin = fields.Char(string='LinkedIn')
    other_social = fields.Char(string='Other Social')

    category_id = fields.Many2one('networkpilot.category', string='Category', ondelete='set null')
    
    tag_ids = fields.Many2many('networkpilot.tag', string='Tags')
    
    importance_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('strategic', 'Strategic')
    ], string='Importance Level', default='medium', required=True)

    last_interaction_date = fields.Datetime(string='Last Interaction Date', index=True)
    notes = fields.Text(string='Notes')

    interaction_ids = fields.One2many('networkpilot.interaction', 'contact_id', string='Interactions')
    reminder_ids = fields.One2many('networkpilot.reminder', 'contact_id', string='Reminders')
    ai_suggestion_ids = fields.One2many('networkpilot.ai_suggestion', 'contact_id', string='AI Suggestions')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        from datetime import timedelta
        now = fields.Datetime.now()
        for record in records:
            if record.importance_level in ['high', 'strategic']:
                self.env['networkpilot.reminder'].create({
                    'user_id': record.user_id.id,
                    'contact_id': record.id,
                    'title': f'Связаться с {record.full_name} (Новый важный контакт)',
                    'description': 'AI ассистент рекомендует организовать ознакомительную встречу или звонок для укрепления связи.',
                    'due_date': now + timedelta(days=2),
                    'status': 'active',
                    'reminder_type': 'follow_up'
                })
        return records

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            parts = [record.first_name, record.last_name]
            record.full_name = ' '.join(p for p in parts if p)

    def action_suggest_metadata(self):
        for record in self:
            # Mock AI logic: generate fake metadata suggestion
            mock_content = f"Suggested tags for {record.full_name}: AI, Tech, Networking\nSuggested Category: Professional"
            self.env['networkpilot.ai_suggestion'].create({
                'contact_id': record.id,
                'suggestion_type': 'metadata',
                'content': mock_content,
            })
            
            # Log activity
            self.env['networkpilot.activity_log'].create({
                'user_id': self.env.user.id,
                'entity_type': 'networkpilot.contact',
                'entity_id': record.id,
                'action': 'ai_metadata_generated',
                'payload_json': '{"status": "success", "mock": true}'
            })

    def action_suggest_next_action(self):
        for record in self:
            # Mock AI logic: generate fake next action
            mock_content = f"Next Action for {record.full_name}: Schedule a catch-up call next week to discuss recent projects."
            self.env['networkpilot.ai_suggestion'].create({
                'contact_id': record.id,
                'suggestion_type': 'next_action',
                'content': mock_content,
            })
            
            # Log activity
            self.env['networkpilot.activity_log'].create({
                'user_id': self.env.user.id,
                'entity_type': 'networkpilot.contact',
                'entity_id': record.id,
                'action': 'ai_next_action_generated',
                'payload_json': '{"status": "success", "mock": true}'
            })

    def calculate_current_value(self):
        self.ensure_one()
        TAG_WEIGHTS = {
            "mentor": 20.0,
            "recruiter": 15.0,
            "peer": 5.0,
            "bridge_contact": 25.0
        }
        base_weight = 1.0
        for tag in self.tag_ids:
            base_weight += TAG_WEIGHTS.get(tag.name.lower(), 0.0)

        INTERACTION_WEIGHTS = {
            "meeting": 5.0,
            "call": 4.0,
            "project": 5.0,
            "message": 2.0,
            "other": 1.0
        }
        total_value = base_weight
        now = fields.Datetime.now()
        decay_lambda = 0.05
        import math
        for interaction in self.interaction_ids:
            if not interaction.interaction_date:
                continue
            days_passed = max(0, (now - interaction.interaction_date).days)
            weight = INTERACTION_WEIGHTS.get(interaction.interaction_type, 1.0)
            decayed_weight = weight * math.exp(-decay_lambda * days_passed)
            total_value += decayed_weight
        return round(total_value, 2)

    @api.model
    def _cron_evaluate_contacts(self):
        dormant_threshold = 10.0
        contacts = self.search([('importance_level', 'in', ['high', 'strategic'])])
        now = fields.Datetime.now()
        from datetime import timedelta
        for contact in contacts:
            current_value = contact.calculate_current_value()
            if current_value < dormant_threshold:
                existing = self.env['networkpilot.reminder'].search([
                    ('contact_id', '=', contact.id),
                    ('status', '!=', 'completed'),
                    ('reminder_type', '=', 'reconnect')
                ], limit=1)
                if not existing:
                    self.env['networkpilot.reminder'].create({
                        'user_id': contact.user_id.id,
                        'contact_id': contact.id,
                        'title': f'Связаться с {contact.full_name} (Затухающий контакт)',
                        'description': f'Показатель связи с этим контактом упал до {current_value}. Необходимо организовать встречу или созвониться.',
                        'due_date': now + timedelta(days=2),
                        'status': 'active',
                        'reminder_type': 'reconnect'
                    })
