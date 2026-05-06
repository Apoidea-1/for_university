from odoo import api, models, fields

class Interaction(models.Model):
    _name = 'networkpilot.interaction'
    _description = 'Interaction'
    _rec_name = 'title'
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

    def _sync_contact_last_interaction(self, contacts=None):
        contacts = contacts or self.mapped('contact_id')
        for contact in contacts:
            latest = self.search(
                [('contact_id', '=', contact.id)],
                order='interaction_date desc, id desc',
                limit=1,
            )
            contact.last_interaction_date = latest.interaction_date if latest else False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_contact_last_interaction()
        return records

    def write(self, vals):
        contacts = self.mapped('contact_id')
        result = super().write(vals)
        self._sync_contact_last_interaction(contacts | self.mapped('contact_id'))
        return result

    def unlink(self):
        contacts = self.mapped('contact_id')
        result = super().unlink()
        for contact in contacts:
            latest = self.search(
                [('contact_id', '=', contact.id)],
                order='interaction_date desc, id desc',
                limit=1,
            )
            contact.last_interaction_date = latest.interaction_date if latest else False
        return result
