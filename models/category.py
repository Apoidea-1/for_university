from odoo import models, fields

class Category(models.Model):
    _name = 'networkpilot.category'
    _description = 'Contact Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    color = fields.Char(string='Color', default='#0f766e', required=True)
    
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, ondelete='cascade')
    contact_ids = fields.One2many('networkpilot.contact', 'category_id', string='Contacts')

    _sql_constraints = [
        ('user_name_uniq', 'unique(user_id, name)', 'Category name must be unique per user!')
    ]
