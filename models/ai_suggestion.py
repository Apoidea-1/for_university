from odoo import models, fields

class AISuggestion(models.Model):
    _name = 'networkpilot.ai_suggestion'
    _description = 'AI Suggestion'
    _order = 'create_date desc'

    contact_id = fields.Many2one('networkpilot.contact', string='Contact', required=True, ondelete='cascade', index=True)
    
    suggestion_type = fields.Selection([
        ('metadata', 'Metadata'),
        ('next_action', 'Next Action')
    ], string='Suggestion Type', required=True)
    
    content = fields.Text(string='Content', required=True)
