from odoo import models, fields

class Interaction(models.Model):
    _name = 'networkpilot.interaction'
    _description = 'Interaction'
    _order = 'interaction_date desc, id desc'

    contact_id = fields.Many2one('networkpilot.contact', string='Contact', required=True, ondelete='cascade')
    
    interaction_type = fields.Selection([
        ('meeting', 'Meeting'),
        ('message', 'Message'),
        ('call', 'Call'),
        ('project', 'Project'),
        ('other', 'Other')
    ], string='Type', required=True)
    
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    
    interaction_date = fields.Datetime(string='Interaction Date', default=fields.Datetime.now, required=True, index=True)
