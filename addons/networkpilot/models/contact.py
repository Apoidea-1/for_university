from odoo import models, fields, api

class Contact(models.Model):
    _name = 'networkpilot.contact'
    _description = 'Contact'
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
