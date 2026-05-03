from odoo import models, fields

class Integration(models.Model):
    _name = 'networkpilot.integration'
    _description = 'Integration'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, ondelete='cascade')
    
    provider = fields.Selection([
        ('google_calendar', 'Google Calendar'),
        ('linkedin', 'LinkedIn'),
        ('telegram', 'Telegram')
    ], string='Provider', required=True)
    
    status = fields.Selection([
        ('connected', 'Connected'),
        ('not_connected', 'Not Connected'),
        ('coming_soon', 'Coming Soon')
    ], string='Status', default='not_connected', required=True)
    
    metadata_json = fields.Text(string='Metadata (JSON)', default='{}', required=True)

    _sql_constraints = [
        ('user_provider_uniq', 'unique(user_id, provider)', 'User can have only one integration per provider!')
    ]
