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
    
    def write(self, vals):
        completed_reminders = self.filtered(lambda r: r.status != 'completed')
        res = super().write(vals)
        if vals.get('status') == 'completed':
            for reminder in completed_reminders:
                if reminder.contact_id:
                    self.env['networkpilot.interaction'].create({
                        'contact_id': reminder.contact_id.id,
                        'interaction_type': 'other',
                        'title': f'Выполнено: {reminder.title}',
                        'description': reminder.description,
                        'interaction_date': fields.Datetime.now(),
                    })
        return res
    
    reminder_type = fields.Selection([
        ('follow_up', 'Follow Up'),
        ('congratulation', 'Congratulation'),
        ('reconnect', 'Reconnect'),
        ('custom', 'Custom')
    ], string='Reminder Type', default='follow_up', required=True)

    push_notified = fields.Boolean(string='Push Notification Sent', default=False, index=True)
