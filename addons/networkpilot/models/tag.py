from odoo import models, fields

class Tag(models.Model):
    _name = 'networkpilot.tag'
    _description = 'Contact Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, ondelete='cascade')

    _sql_constraints = [
        ('user_name_uniq', 'unique(user_id, name)', 'Tag name must be unique per user!')
    ]
