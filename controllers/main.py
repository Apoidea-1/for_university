import os
from odoo import http
from odoo.http import request

class NetworkPilotApp(http.Controller):
    @http.route(['/'], type='http', auth='public', sitemap=False)
    def root_redirect(self, **kwargs):
        return request.redirect('/app/')

    @http.route(
        [
            '/dashboard',
            '/login',
            '/register',
            '/contacts',
            '/contacts/<path:path>',
            '/reminders',
            '/analytics',
            '/integrations',
            '/network',
            '/messages',
        ],
        type='http',
        auth='public',
        sitemap=False,
    )
    def legacy_spa_redirect(self, path=None, **kwargs):
        request_path = request.httprequest.path or '/'
        return request.redirect(f'/app{request_path}')

    @http.route(['/app', '/app/', '/app/<path:path>'], type='http', auth='public', sitemap=False)
    def serve_app(self, **kwargs):
        """
        Serves the React application.
        The React application owns the auth flow itself and uses the Odoo
        session cookie through /api/v1/auth/* endpoints.
        """
        addon_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        index_file = os.path.join(addon_path, 'static', 'app', 'index.html')
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return request.make_response(
                content,
                headers=[
                    ('Content-Type', 'text/html'),
                    ('Cache-Control', 'no-store'),
                    ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                    ('X-Frame-Options', 'DENY'),
                    ('X-Content-Type-Options', 'nosniff'),
                ],
            )
        except FileNotFoundError:
            return request.make_response(
                "<h1>React App Not Built</h1><p>Please build the React app and place it in the static/app directory.</p>",
                headers=[('Content-Type', 'text/html')],
                status=404
            )
