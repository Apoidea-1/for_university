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

    @http.route('/api/v1/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            return self._json_response({'detail': 'Invalid JSON'}, status=400)

        email = data.get('email', '')
        password = data.get('password', '')

        # Try to authenticate via Odoo
        db = request.db
        uid = request.session.authenticate(db, email, password)

        if not uid:
            return self._json_response({'detail': 'Invalid email or password'}, status=401)

        user = request.env['res.users'].sudo().browse(uid)
        return self._json_response({
            "access_token": request.session.sid,
            "token_type": "session",
            "user": {
                "id": user.id,
                "full_name": user.name,
                "email": user.login,
                "created_at": str(user.create_date),
                "updated_at": str(user.write_date),
            }
        })

    @http.route('/api/v1/auth/register', type='http', auth='none', methods=['POST'], csrf=False)
    def register(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            return self._json_response({'detail': 'Invalid JSON'}, status=400)

        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not full_name or not email or not password:
            return self._json_response({'detail': 'full_name, email and password are required'}, status=400)

        # Check if user already exists
        existing = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing:
            return self._json_response({'detail': 'User with this email already exists'}, status=409)

        # Create user
        try:
            new_user = request.env['res.users'].sudo().create({
                'name': full_name,
                'login': email,
                'password': password,
                'groups_id': [(6, 0, [request.env.ref('base.group_user').id])],
            })
        except Exception as e:
            return self._json_response({'detail': str(e)}, status=500)

        # Authenticate immediately after registration
        db = request.db
        uid = request.session.authenticate(db, email, password)

        return self._json_response({
            "access_token": request.session.sid,
            "token_type": "session",
            "user": {
                "id": new_user.id,
                "full_name": new_user.name,
                "email": new_user.login,
                "created_at": str(new_user.create_date),
                "updated_at": str(new_user.write_date),
            }
        }, status=201)

    @http.route('/api/v1/auth/me', type='http', auth='user', methods=['GET'], csrf=False)
    def get_me(self, **kwargs):
        user = request.env.user
        return self._json_response({
            "id": user.id,
            "full_name": user.name,
            "email": user.login,
            "created_at": str(user.create_date),
            "updated_at": str(user.write_date),
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
            "new_contacts_7d": contacts_7_days,
            "new_contacts_30d": Contact.search_count([('create_date', '>=', thirty_days_ago)]),
            "interactions_7d": Interaction.search_count([('date', '>=', seven_days_ago)]),
            "interactions_30d": interactions_30_days,
            "active_reminders": active_reminders,
            "overdue_reminders": overdue_reminders,
            "stale_contacts_count": 0,
            "activity_timeline": [],
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
                    "category_name": cat.name,
                    "count": count,
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
