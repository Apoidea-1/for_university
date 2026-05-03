from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    contact_ids = fields.One2many('networkpilot.contact', 'user_id', string='Contacts')
    reminder_ids = fields.One2many('networkpilot.reminder', 'user_id', string='Reminders')
    category_ids = fields.One2many('networkpilot.category', 'user_id', string='Categories')
    tag_ids = fields.One2many('networkpilot.tag', 'user_id', string='Tags')
    integration_ids = fields.One2many('networkpilot.integration', 'user_id', string='Integrations')
    activity_log_ids = fields.One2many('networkpilot.activity_log', 'user_id', string='Activity Logs')
