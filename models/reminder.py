from odoo import models, fields

class Reminder(models.Model):
    _name = 'networkpilot.reminder'
    _description = 'Reminder'
    _rec_name = 'title'
    _order = 'due_date, id desc'

    contact_id = fields.Many2one('networkpilot.contact', string='Contact', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True, ondelete='cascade', index=True)
    
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    
    due_date = fields.Datetime(string='Due Date', required=True, index=True)
    
    status = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed')
    ], string='Status', default='active', required=True, index=True)
    
    reminder_type = fields.Selection([
        ('follow_up', 'Follow Up'),
        ('congratulation', 'Congratulation'),
        ('reconnect', 'Reconnect'),
        ('custom', 'Custom')
    ], string='Reminder Type', default='follow_up', required=True)

    push_notified = fields.Boolean(string='Push Notification Sent', default=False, index=True)
