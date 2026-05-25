import json
from datetime import date, datetime, time, timedelta, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse

from odoo import fields, http
from odoo.http import request


class NetworkPilotAPI(http.Controller):
    PROVIDERS = ('google_calendar', 'linkedin', 'telegram')

    def _json_response(self, data=None, status=200):
        body = '' if status == 204 else json.dumps(data, default=str, ensure_ascii=False)
        return request.make_response(
            body,
            headers=[('Content-Type', 'application/json')],
            status=status,
        )

    def _json_payload(self):
        try:
            return json.loads(request.httprequest.data or b'{}')
        except Exception:
            return None

    def _bad_json(self):
        return self._json_response({'detail': 'Invalid JSON'}, status=400)

    def _current_user_id(self):
        return request.env.user.id

    def _parse_datetime(self, value):
        if not value:
            return False
        if isinstance(value, datetime):
            dt = value
        else:
            raw = str(value).strip()
            if raw.endswith('Z'):
                raw = raw[:-1] + '+00:00'
            try:
                dt = datetime.fromisoformat(raw)
            except ValueError:
                return False
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return fields.Datetime.to_string(dt)

    def _safe_int(self, value):
        if value in (None, '', False):
            return False
        try:
            return int(value)
        except (TypeError, ValueError):
            return False

    def _clean_text(self, value):
        if value in (None, ''):
            return False
        return str(value).strip()

    def _is_same_origin(self):
        host_url = request.httprequest.host_url.rstrip('/')
        allowed = {host_url}
        origin = (request.httprequest.headers.get('Origin') or '').rstrip('/')
        referer = request.httprequest.headers.get('Referer') or ''
        if origin:
            return origin in allowed
        if referer:
            parsed = urlparse(referer)
            referer_origin = f'{parsed.scheme}://{parsed.netloc}'.rstrip('/')
            return referer_origin in allowed
        return False

    def _forbid_cross_origin(self):
        if not self._is_same_origin():
            return self._json_response({'detail': 'Cross-origin request denied'}, status=403)
        return None

    def _get_networkpilot_group(self):
        return request.env['res.groups'].sudo().search([
            ('name', '=', 'User'),
            ('category_id.name', '=', 'Networkpilot'),
        ], limit=1)

    def _ensure_user_group(self, user):
        group = self._get_networkpilot_group()
        if group and group.id not in user.groups_id.ids:
            user.sudo().write({'groups_id': [(4, group.id)]})

    def _authenticate(self, db, email, password):
        credentials = {'login': email, 'password': password, 'type': 'password'}
        try:
            return request.session.authenticate(db, credentials)
        except TypeError:
            return request.session.authenticate(db, email, password)

    def _category_payload(self, category):
        return {
            'id': category.id,
            'user_id': category.user_id.id or None,
            'name': category.name,
            'color': category.color,
            'created_at': category.create_date,
        }

    def _tag_payload(self, tag):
        return {
            'id': tag.id,
            'user_id': tag.user_id.id or None,
            'name': tag.name,
            'created_at': tag.create_date,
        }

    def _contact_payload(self, contact):
        category = contact.category_id
        return {
            'id': contact.id,
            'user_id': contact.user_id.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name or None,
            'company': contact.company or None,
            'role': contact.role or None,
            'source_where_met': contact.source_where_met or None,
            'email': contact.email or None,
            'phone': contact.phone or None,
            'telegram': contact.telegram or None,
            'linkedin': contact.linkedin or None,
            'other_social': contact.other_social or None,
            'category_id': category.id or None,
            'importance_level': contact.importance_level,
            'last_interaction_date': contact.last_interaction_date or None,
            'notes': contact.notes or None,
            'created_at': contact.create_date,
            'updated_at': contact.write_date,
            'category': self._category_payload(category) if category else None,
            'tags': [self._tag_payload(tag) for tag in contact.tag_ids],
        }

    def _interaction_payload(self, interaction):
        return {
            'id': interaction.id,
            'contact_id': interaction.contact_id.id,
            'type': interaction.interaction_type,
            'title': interaction.title,
            'description': interaction.description or None,
            'interaction_date': interaction.interaction_date,
            'created_at': interaction.create_date,
        }

    def _reminder_payload(self, reminder):
        contact = reminder.contact_id
        return {
            'id': reminder.id,
            'contact_id': contact.id or None,
            'user_id': reminder.user_id.id,
            'title': reminder.title,
            'description': reminder.description or None,
            'due_date': reminder.due_date,
            'status': reminder.status,
            'reminder_type': reminder.reminder_type,
            'created_at': reminder.create_date,
            'updated_at': reminder.write_date,
            'contact': {
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name or None,
                'company': contact.company or None,
            } if contact else None,
        }

    def _integration_payload(self, integration):
        try:
            metadata = json.loads(integration.metadata_json or '{}')
        except Exception:
            metadata = {}
        return {
            'id': integration.id,
            'user_id': integration.user_id.id,
            'provider': integration.provider,
            'status': integration.status,
            'metadata_json': metadata,
            'created_at': integration.create_date,
        }

    def _contact_domain(self):
        return [('user_id', '=', self._current_user_id())]

    def _get_contact(self, contact_id):
        return request.env['networkpilot.contact'].sudo().search(
            self._contact_domain() + [('id', '=', self._safe_int(contact_id))],
            limit=1,
        )

    def _sync_tags(self, names):
        Tag = request.env['networkpilot.tag'].sudo()
        tags = Tag.browse()
        for name in names or []:
            clean = self._clean_text(name)
            if not clean:
                continue
            tag = Tag.search([
                ('user_id', '=', self._current_user_id()),
                ('name', '=ilike', clean),
            ], limit=1)
            if not tag:
                tag = Tag.create({'user_id': self._current_user_id(), 'name': clean})
            tags |= tag
        return [(6, 0, tags.ids)]

    def _contact_vals(self, data, partial=False):
        vals = {}
        text_fields = [
            'first_name', 'last_name', 'company', 'role', 'source_where_met',
            'email', 'phone', 'telegram', 'linkedin', 'other_social', 'notes',
        ]
        for field_name in text_fields:
            if field_name in data:
                vals[field_name] = self._clean_text(data.get(field_name))

        if not partial:
            vals.setdefault('first_name', self._clean_text(data.get('first_name')))
            vals['user_id'] = self._current_user_id()

        if 'category_id' in data:
            category_id = self._safe_int(data.get('category_id'))
            if category_id:
                category = request.env['networkpilot.category'].sudo().search([
                    ('id', '=', category_id),
                    ('user_id', '=', self._current_user_id()),
                ], limit=1)
                vals['category_id'] = category.id if category else False
            else:
                vals['category_id'] = False

        if 'importance_level' in data:
            vals['importance_level'] = data.get('importance_level') or 'medium'
        elif not partial:
            vals['importance_level'] = 'medium'

        if 'last_interaction_date' in data:
            vals['last_interaction_date'] = self._parse_datetime(data.get('last_interaction_date'))

        if 'tag_names' in data:
            vals['tag_ids'] = self._sync_tags(data.get('tag_names') or [])

        return vals

    def _ensure_integrations(self):
        Integration = request.env['networkpilot.integration'].sudo()
        existing = Integration.search([('user_id', '=', self._current_user_id())])
        existing_providers = set(existing.mapped('provider'))
        for provider in self.PROVIDERS:
            if provider not in existing_providers:
                Integration.create({
                    'user_id': self._current_user_id(),
                    'provider': provider,
                    'status': 'not_connected' if provider == 'google_calendar' else 'coming_soon',
                    'metadata_json': '{}',
                })

    def _score_contact_match(self, contact, search_term):
        if not search_term:
            return 0
        needle = search_term.lower()
        fields_to_rank = [
            contact.full_name or '',
            contact.first_name or '',
            contact.last_name or '',
            contact.company or '',
            contact.role or '',
            contact.email or '',
            contact.phone or '',
            contact.telegram or '',
            contact.linkedin or '',
            contact.notes or '',
            ' '.join(contact.tag_ids.mapped('name')),
        ]
        score = 0
        for raw_value in fields_to_rank:
            value = raw_value.lower().strip()
            if not value:
                continue
            if value == needle:
                score = max(score, 240)
            elif value.startswith(needle):
                score = max(score, 180)
            elif f' {needle}' in f' {value}':
                score = max(score, 135)
            elif needle in value:
                score = max(score, 100)
            ratio = SequenceMatcher(None, needle, value[: max(len(needle) * 2, len(value))]).ratio()
            if ratio >= 0.7:
                score = max(score, int(ratio * 90))
        if contact.importance_level == 'strategic':
            score += 12
        elif contact.importance_level == 'high':
            score += 8
        if contact.last_interaction_date:
            days_since = (date.today() - contact.last_interaction_date.date()).days
            score += max(0, 14 - min(days_since, 14))
        return score

    @http.route('/api/v1/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()

        email = self._clean_text(data.get('email'))
        password = data.get('password', '')
        if not email or not password:
            return self._json_response({'detail': 'email and password are required'}, status=400)

        try:
            self._authenticate(request.db, email, password)
        except Exception:
            return self._json_response({'detail': 'Invalid email or password'}, status=401)

        uid = request.session.uid
        if not uid:
            return self._json_response({'detail': 'Invalid email or password'}, status=401)

        user = request.env['res.users'].sudo().browse(uid)
        self._ensure_user_group(user)
        return self._json_response({
            'access_token': 'session',
            'token_type': 'session',
            'user': {
                'id': user.id,
                'full_name': user.name,
                'email': user.login,
                'created_at': user.create_date,
                'updated_at': user.write_date,
            },
        })

    @http.route('/api/v1/auth/register', type='http', auth='public', methods=['POST'], csrf=False)
    def register(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()

        full_name = self._clean_text(data.get('full_name'))
        email = self._clean_text(data.get('email'))
        password = data.get('password', '')
        if not full_name or not email or not password:
            return self._json_response({'detail': 'full_name, email and password are required'}, status=400)

        Users = request.env['res.users'].sudo()
        if Users.search([('login', '=', email)], limit=1):
            return self._json_response({'detail': 'User with this email already exists'}, status=409)

        company = request.env['res.company'].sudo().search([], limit=1)
        base_group = request.env.ref('base.group_user')
        group_ids = [base_group.id]
        network_group = self._get_networkpilot_group()
        if network_group:
            group_ids.append(network_group.id)

        try:
            new_user = Users.create({
                'name': full_name,
                'login': email,
                'password': password,
                'company_id': company.id,
                'company_ids': [(6, 0, company.ids)],
                'groups_id': [(6, 0, group_ids)],
            })
        except Exception as exc:
            return self._json_response({'detail': str(exc)}, status=500)

        request.env.cr.commit()
        try:
            self._authenticate(request.db, email, password)
        except Exception as exc:
            return self._json_response({'detail': str(exc)}, status=401)

        return self._json_response({
            'access_token': 'session',
            'token_type': 'session',
            'user': {
                'id': new_user.id,
                'full_name': new_user.name,
                'email': new_user.login,
                'created_at': new_user.create_date,
                'updated_at': new_user.write_date,
            },
        }, status=201)

    @http.route('/api/v1/auth/logout', type='http', auth='user', methods=['POST'], csrf=False)
    def logout(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        try:
            request.session.logout(keep_db=True)
        except TypeError:
            request.session.logout()
        return self._json_response(status=204)

    @http.route('/api/v1/auth/me', type='http', auth='user', methods=['GET'], csrf=False)
    def get_me(self, **kwargs):
        user = request.env.user
        return self._json_response({
            'id': user.id,
            'full_name': user.name,
            'email': user.login,
            'created_at': user.create_date,
            'updated_at': user.write_date,
        })

    @http.route('/api/v1/analytics/overview', type='http', auth='user', methods=['GET'], csrf=False)
    def get_analytics_overview(self, **kwargs):
        Contact = request.env['networkpilot.contact'].sudo()
        Interaction = request.env['networkpilot.interaction'].sudo()
        Reminder = request.env['networkpilot.reminder'].sudo()

        now = fields.Datetime.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        stale_before = now - timedelta(days=21)
        contact_domain = self._contact_domain()
        interaction_domain = [('contact_id.user_id', '=', self._current_user_id())]
        reminder_domain = [('user_id', '=', self._current_user_id())]

        today = fields.Date.context_today(request.env.user)
        timeline = []
        for offset in range(13, -1, -1):
            day = today - timedelta(days=offset)
            start = datetime.combine(day, time.min)
            end = datetime.combine(day, time.max)
            timeline.append({
                'date': day.isoformat(),
                'contacts_added': Contact.search_count(contact_domain + [
                    ('create_date', '>=', fields.Datetime.to_string(start)),
                    ('create_date', '<=', fields.Datetime.to_string(end)),
                ]),
                'interactions_logged': Interaction.search_count(interaction_domain + [
                    ('interaction_date', '>=', fields.Datetime.to_string(start)),
                    ('interaction_date', '<=', fields.Datetime.to_string(end)),
                ]),
            })

        stale_count = Contact.search_count(contact_domain + [
            '|',
            ('last_interaction_date', '=', False),
            ('last_interaction_date', '<', stale_before),
        ])

        return self._json_response({
            'new_contacts_7d': Contact.search_count(contact_domain + [('create_date', '>=', seven_days_ago)]),
            'new_contacts_30d': Contact.search_count(contact_domain + [('create_date', '>=', thirty_days_ago)]),
            'interactions_7d': Interaction.search_count(interaction_domain + [('interaction_date', '>=', seven_days_ago)]),
            'interactions_30d': Interaction.search_count(interaction_domain + [('interaction_date', '>=', thirty_days_ago)]),
            'active_reminders': Reminder.search_count(reminder_domain + [('status', '=', 'active'), ('due_date', '>=', now)]),
            'overdue_reminders': Reminder.search_count(reminder_domain + [('status', '=', 'active'), ('due_date', '<', now)]),
            'stale_contacts_count': stale_count,
            'activity_timeline': timeline,
        })

    @http.route('/api/v1/analytics/categories', type='http', auth='user', methods=['GET'], csrf=False)
    def get_analytics_categories(self, **kwargs):
        Contact = request.env['networkpilot.contact'].sudo()
        categories = request.env['networkpilot.category'].sudo().search([
            ('user_id', '=', self._current_user_id()),
        ], order='name')
        result = []
        for category in categories:
            count = Contact.search_count(self._contact_domain() + [('category_id', '=', category.id)])
            if count:
                result.append({
                    'category_name': category.name,
                    'count': count,
                    'color': category.color or '#CBD5E1',
                })
        return self._json_response(result)

    @http.route('/api/v1/analytics/stale-contacts', type='http', auth='user', methods=['GET'], csrf=False)
    def get_stale_contacts(self, **kwargs):
        days = request.httprequest.args.get('days', default=21, type=int)
        threshold = fields.Datetime.now() - timedelta(days=days)
        contacts = request.env['networkpilot.contact'].sudo().search(
            self._contact_domain() + [
                '|',
                ('last_interaction_date', '=', False),
                ('last_interaction_date', '<', threshold),
            ],
            order='last_interaction_date asc, create_date asc',
            limit=20,
        )
        today = date.today()
        result = []
        for contact in contacts:
            days_since = None
            if contact.last_interaction_date:
                days_since = (today - contact.last_interaction_date.date()).days
            result.append({
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name or None,
                'company': contact.company or None,
                'last_interaction_date': contact.last_interaction_date or None,
                'days_since_last_interaction': days_since,
            })
        return self._json_response(result)

    @http.route('/api/v1/categories', type='http', auth='user', methods=['GET'], csrf=False)
    def get_categories(self, **kwargs):
        categories = request.env['networkpilot.category'].sudo().search([
            ('user_id', '=', self._current_user_id()),
        ], order='name')
        return self._json_response([self._category_payload(category) for category in categories])

    @http.route('/api/v1/categories', type='http', auth='user', methods=['POST'], csrf=False)
    def create_category(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        name = self._clean_text(data.get('name'))
        if not name:
            return self._json_response({'detail': 'name is required'}, status=400)
        category = request.env['networkpilot.category'].sudo().create({
            'user_id': self._current_user_id(),
            'name': name,
            'color': self._clean_text(data.get('color')) or '#0f766e',
        })
        return self._json_response(self._category_payload(category), status=201)

    @http.route('/api/v1/tags', type='http', auth='user', methods=['GET'], csrf=False)
    def get_tags(self, **kwargs):
        tags = request.env['networkpilot.tag'].sudo().search([
            ('user_id', '=', self._current_user_id()),
        ], order='name')
        return self._json_response([self._tag_payload(tag) for tag in tags])

    @http.route('/api/v1/tags', type='http', auth='user', methods=['POST'], csrf=False)
    def create_tag(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        name = self._clean_text(data.get('name'))
        if not name:
            return self._json_response({'detail': 'name is required'}, status=400)
        tag = request.env['networkpilot.tag'].sudo().create({
            'user_id': self._current_user_id(),
            'name': name,
        })
        return self._json_response(self._tag_payload(tag), status=201)

    @http.route('/api/v1/contacts', type='http', auth='user', methods=['GET'], csrf=False)
    def list_contacts(self, **kwargs):
        args = request.httprequest.args
        domain = self._contact_domain()
        search = self._clean_text(args.get('search'))
        if search:
            domain += [
                '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('first_name', 'ilike', search),
                ('last_name', 'ilike', search),
                ('company', 'ilike', search),
                ('role', 'ilike', search),
                ('email', 'ilike', search),
                ('phone', 'ilike', search),
                ('telegram', 'ilike', search),
                ('linkedin', 'ilike', search),
                ('notes', 'ilike', search),
                ('tag_ids.name', 'ilike', search),
            ]

        category_id = self._safe_int(args.get('category_id'))
        if category_id:
            domain.append(('category_id', '=', category_id))

        importance = self._clean_text(args.get('importance_level'))
        if importance:
            domain.append(('importance_level', '=', importance))

        sort_by = args.get('sort_by') or 'last_interaction_date'
        sort_order = 'asc' if args.get('sort_order') == 'asc' else 'desc'
        order_map = {
            'name': 'full_name asc',
            'created_at': f'create_date {sort_order}',
            'last_interaction_date': 'last_interaction_date desc, create_date desc',
        }
        order = order_map.get(sort_by, 'last_interaction_date desc, create_date desc')
        page = max(args.get('page', default=1, type=int), 1)
        per_page = min(max(args.get('per_page', default=100, type=int), 1), 200)
        offset = (page - 1) * per_page

        Contact = request.env['networkpilot.contact'].sudo()
        if search:
            candidate_limit = min(max(per_page * 5, 150), 600)
            candidates = Contact.search(domain, order='write_date desc, create_date desc', limit=candidate_limit)
            ranked_contacts = sorted(
                candidates,
                key=lambda contact: (
                    -self._score_contact_match(contact, search),
                    contact.full_name or '',
                    -(contact.id or 0),
                ),
            )
            total = len(ranked_contacts)
            contacts = ranked_contacts[offset : offset + per_page]
        else:
            total = Contact.search_count(domain)
            contacts = Contact.search(domain, order=order, limit=per_page, offset=offset)
        return self._json_response({
            'total': total,
            'items': [self._contact_payload(contact) for contact in contacts],
        })

    @http.route('/api/v1/contacts', type='http', auth='user', methods=['POST'], csrf=False)
    def create_contact(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        vals = self._contact_vals(data)
        if not vals.get('first_name'):
            return self._json_response({'detail': 'first_name is required'}, status=400)
        contact = request.env['networkpilot.contact'].sudo().create(vals)
        return self._json_response(self._contact_payload(contact), status=201)

    @http.route('/api/v1/contacts/quick-add', type='http', auth='user', methods=['POST'], csrf=False)
    def quick_add_contact(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        vals = self._contact_vals(data)
        if not vals.get('first_name'):
            return self._json_response({'detail': 'first_name is required'}, status=400)
        contact = request.env['networkpilot.contact'].sudo().create(vals)
        if contact.source_where_met:
            request.env['networkpilot.interaction'].sudo().create({
                'contact_id': contact.id,
                'interaction_type': 'meeting',
                'title': 'Первое знакомство',
                'description': f'Где познакомились: {contact.source_where_met}',
                'interaction_date': fields.Datetime.now(),
            })
        return self._json_response(self._contact_payload(contact), status=201)

    @http.route('/api/v1/contacts/<int:contact_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_contact(self, contact_id, **kwargs):
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({'detail': 'Contact not found'}, status=404)
        return self._json_response(self._contact_payload(contact))

    @http.route('/api/v1/contacts/<int:contact_id>', type='http', auth='user', methods=['PATCH'], csrf=False)
    def update_contact(self, contact_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({'detail': 'Contact not found'}, status=404)
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        vals = self._contact_vals(data, partial=True)
        if vals:
            contact.write(vals)
        return self._json_response(self._contact_payload(contact))

    @http.route('/api/v1/contacts/<int:contact_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_contact(self, contact_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({'detail': 'Contact not found'}, status=404)
        contact.unlink()
        return self._json_response(status=204)

    @http.route('/api/v1/contacts/<int:contact_id>/interactions', type='http', auth='user', methods=['GET'], csrf=False)
    def list_interactions(self, contact_id, **kwargs):
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({'detail': 'Contact not found'}, status=404)
        interactions = request.env['networkpilot.interaction'].sudo().search([
            ('contact_id', '=', contact.id),
        ], order='interaction_date desc, id desc')
        return self._json_response([self._interaction_payload(item) for item in interactions])

    @http.route('/api/v1/contacts/<int:contact_id>/interactions', type='http', auth='user', methods=['POST'], csrf=False)
    def create_interaction(self, contact_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({'detail': 'Contact not found'}, status=404)
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        title = self._clean_text(data.get('title'))
        if not title:
            return self._json_response({'detail': 'title is required'}, status=400)
        interaction = request.env['networkpilot.interaction'].sudo().create({
            'contact_id': contact.id,
            'interaction_type': data.get('type') or data.get('interaction_type') or 'other',
            'title': title,
            'description': self._clean_text(data.get('description')),
            'interaction_date': self._parse_datetime(data.get('interaction_date')) or fields.Datetime.now(),
        })
        return self._json_response(self._interaction_payload(interaction), status=201)

    @http.route('/api/v1/interactions/<int:interaction_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_interaction(self, interaction_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        interaction = request.env['networkpilot.interaction'].sudo().search([
            ('id', '=', interaction_id),
            ('contact_id.user_id', '=', self._current_user_id()),
        ], limit=1)
        if not interaction:
            return self._json_response({'detail': 'Interaction not found'}, status=404)
        interaction.unlink()
        return self._json_response(status=204)

    @http.route('/api/v1/reminders', type='http', auth='user', methods=['GET'], csrf=False)
    def get_reminders(self, **kwargs):
        args = request.httprequest.args
        now = fields.Datetime.now()
        domain = [('user_id', '=', self._current_user_id())]
        status = args.get('status')
        if status == 'overdue':
            domain += [('status', '=', 'active'), ('due_date', '<', now)]
        elif status:
            domain.append(('status', '=', status))
            if status == 'active':
                domain.append(('due_date', '>=', now))
        limit = args.get('limit', type=int)
        reminders = request.env['networkpilot.reminder'].sudo().search(domain, limit=limit, order='due_date asc')
        return self._json_response([self._reminder_payload(reminder) for reminder in reminders])

    @http.route('/api/v1/reminders', type='http', auth='user', methods=['POST'], csrf=False)
    def create_reminder(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        title = self._clean_text(data.get('title'))
        due_date = self._parse_datetime(data.get('due_date'))
        if not title or not due_date:
            return self._json_response({'detail': 'title and due_date are required'}, status=400)
        contact_id = self._safe_int(data.get('contact_id'))
        if contact_id and not self._get_contact(contact_id):
            return self._json_response({'detail': 'Contact not found'}, status=404)
        reminder = request.env['networkpilot.reminder'].sudo().create({
            'user_id': self._current_user_id(),
            'contact_id': contact_id or False,
            'title': title,
            'description': self._clean_text(data.get('description')),
            'due_date': due_date,
            'status': data.get('status') or 'active',
            'reminder_type': data.get('reminder_type') or 'follow_up',
        })
        return self._json_response(self._reminder_payload(reminder), status=201)

    @http.route('/api/v1/reminders/<int:reminder_id>', type='http', auth='user', methods=['PATCH'], csrf=False)
    def update_reminder(self, reminder_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        reminder = request.env['networkpilot.reminder'].sudo().search([
            ('id', '=', reminder_id),
            ('user_id', '=', self._current_user_id()),
        ], limit=1)
        if not reminder:
            return self._json_response({'detail': 'Reminder not found'}, status=404)
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        vals = {}
        for field_name in ('title', 'description', 'status', 'reminder_type'):
            if field_name in data:
                vals[field_name] = self._clean_text(data.get(field_name))
        if 'due_date' in data:
            vals['due_date'] = self._parse_datetime(data.get('due_date'))
        if 'contact_id' in data:
            contact_id = self._safe_int(data.get('contact_id'))
            if contact_id and not self._get_contact(contact_id):
                return self._json_response({'detail': 'Contact not found'}, status=404)
            vals['contact_id'] = contact_id or False
        if vals:
            reminder.write(vals)
        return self._json_response(self._reminder_payload(reminder))

    @http.route('/api/v1/reminders/<int:reminder_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_reminder(self, reminder_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        reminder = request.env['networkpilot.reminder'].sudo().search([
            ('id', '=', reminder_id),
            ('user_id', '=', self._current_user_id()),
        ], limit=1)
        if not reminder:
            return self._json_response({'detail': 'Reminder not found'}, status=404)
        reminder.unlink()
        return self._json_response(status=204)

    @http.route('/api/v1/ai/suggest-contact-metadata', type='http', auth='user', methods=['POST'], csrf=False)
    def suggest_contact_metadata(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        source = ' '.join(filter(None, [
            self._clean_text(data.get('company')),
            self._clean_text(data.get('role')),
            self._clean_text(data.get('source_where_met')),
            self._clean_text(data.get('notes')),
        ])).lower()
        if any(word in source for word in ('hr', 'карьер', 'рекрутер', 'стажиров')):
            category = 'Карьера'
            tags = ['карьера', 'hr']
        elif any(word in source for word in ('университет', 'учеб', 'студент')):
            category = 'Учеба'
            tags = ['учеба', 'университет']
        else:
            category = 'Профессиональные контакты'
            tags = ['нетворкинг', 'контакт']
        notes = self._clean_text(data.get('notes')) or 'Контакт добавлен без подробных заметок.'
        return self._json_response({
            'category': category,
            'tags': tags,
            'note_summary': notes[:240],
            'next_action': 'Запланировать короткий follow-up и зафиксировать договоренности.',
        })

    @http.route('/api/v1/ai/suggest-next-action', type='http', auth='user', methods=['POST'], csrf=False)
    def suggest_next_action(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        return self._json_response({
            'next_action': 'Написать follow-up, напомнить контекст знакомства и предложить следующий конкретный шаг.',
            'rationale': 'Подсказка построена по заметкам и последнему взаимодействию.',
        })

    @http.route('/api/v1/integrations', type='http', auth='user', methods=['GET'], csrf=False)
    def get_integrations(self, **kwargs):
        self._ensure_integrations()
        integrations = request.env['networkpilot.integration'].sudo().search([
            ('user_id', '=', self._current_user_id()),
        ], order='provider')
        return self._json_response([self._integration_payload(integration) for integration in integrations])

    @http.route('/api/v1/integrations/<string:provider>/connect-mock', type='http', auth='user', methods=['POST'], csrf=False)
    def connect_mock_integration(self, provider, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        if provider not in self.PROVIDERS:
            return self._json_response({'detail': 'Unknown provider'}, status=404)
        self._ensure_integrations()
        integration = request.env['networkpilot.integration'].sudo().search([
            ('user_id', '=', self._current_user_id()),
            ('provider', '=', provider),
        ], limit=1)
        integration.write({
            'status': 'connected',
            'metadata_json': json.dumps({'connected_at': fields.Datetime.to_string(fields.Datetime.now())}),
        })
        return self._json_response({
            'provider': provider,
            'status': integration.status,
            'message': 'Integration connected in mock mode',
        })
