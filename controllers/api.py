import json
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request

class NetworkPilotAPI(http.Controller):
    
    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str),
            headers=[('Content-Type', 'application/json')],
            status=status
        )

    @http.route('/api/v1/auth/me', type='http', auth='user', methods=['GET'], csrf=False)
    def get_me(self, **kwargs):
        user = request.env.user
        return self._json_response({
            "id": user.id,
            "email": user.login,
            "name": user.name,
            "is_active": user.active,
        })

    @http.route('/api/v1/analytics/overview', type='http', auth='user', methods=['GET'], csrf=False)
    def get_analytics_overview(self, **kwargs):
        Contact = request.env['networkpilot.contact']
        Interaction = request.env['networkpilot.interaction']
        Reminder = request.env['networkpilot.reminder']
        
        now = fields.Datetime.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        contacts_7_days = Contact.search_count([('create_date', '>=', seven_days_ago)])
        interactions_30_days = Interaction.search_count([('date', '>=', thirty_days_ago)])
        active_reminders = Reminder.search_count([('status', '=', 'pending')])
        overdue_reminders = Reminder.search_count([
            ('status', '=', 'pending'),
            ('due_date', '<', now)
        ])
        
        return self._json_response({
            "contacts_7_days": contacts_7_days,
            "interactions_30_days": interactions_30_days,
            "active_reminders": active_reminders,
            "overdue_reminders": overdue_reminders
        })

    @http.route('/api/v1/analytics/categories', type='http', auth='user', methods=['GET'], csrf=False)
    def get_analytics_categories(self, **kwargs):
        Contact = request.env['networkpilot.contact']
        categories = request.env['networkpilot.category'].search([])
        result = []
        for cat in categories:
            count = Contact.search_count([('category_id', '=', cat.id)])
            if count > 0:
                result.append({
                    "name": cat.name,
                    "value": count,
                    "color": cat.color or "#CBD5E1"
                })
        return self._json_response(result)

    @http.route('/api/v1/categories', type='http', auth='user', methods=['GET'], csrf=False)
    def get_categories(self, **kwargs):
        categories = request.env['networkpilot.category'].search([])
        return self._json_response([{"id": c.id, "name": c.name, "color": c.color} for c in categories])

    @http.route('/api/v1/contacts/quick-add', type='http', auth='user', methods=['POST'], csrf=False)
    def quick_add_contact(self, **kwargs):
        data = json.loads(request.httprequest.data)
        Contact = request.env['networkpilot.contact']
        new_contact = Contact.create({
            'name': data.get('name'),
            'category_id': data.get('category_id'),
            'notes': data.get('notes'),
        })
        
        where_met = data.get('where_met')
        if where_met:
            request.env['networkpilot.interaction'].create({
                'contact_id': new_contact.id,
                'interaction_type': 'meeting',
                'date': fields.Datetime.now(),
                'summary': f"Met at: {where_met}",
                'notes': data.get('notes')
            })
            
        return self._json_response({
            "id": new_contact.id,
            "name": new_contact.name,
            "category_id": new_contact.category_id.id
        })

    @http.route('/api/v1/reminders', type='http', auth='user', methods=['GET'], csrf=False)
    def get_reminders(self, **kwargs):
        # We handle query params like status=pending&limit=3
        domain = []
        status = request.httprequest.args.get('status')
        if status:
            domain.append(('status', '=', status))
            
        limit = request.httprequest.args.get('limit', type=int)
        
        reminders = request.env['networkpilot.reminder'].search(domain, limit=limit, order='due_date asc')
        result = []
        for r in reminders:
            result.append({
                "id": r.id,
                "title": r.title,
                "due_date": r.due_date,
                "status": r.status,
                "contact_id": r.contact_id.id,
                "contact_name": r.contact_id.name
            })
        return self._json_response(result)
