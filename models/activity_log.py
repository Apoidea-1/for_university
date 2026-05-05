from odoo import models, fields

class ActivityLog(models.Model):
    _name = 'networkpilot.activity_log'
    _description = 'Activity Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade', index=True)
    entity_type = fields.Char(string='Entity Type', required=True, index=True)
    entity_id = fields.Integer(string='Entity ID', required=True, index=True)
    action = fields.Char(string='Action', required=True)
    payload_json = fields.Text(string='Payload (JSON)', default='{}', required=True)
