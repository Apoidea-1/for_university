import os
import odoo
from odoo import http
from odoo.http import request

class NetworkPilotApp(http.Controller):
    @http.route(['/app', '/app/<path:path>'], type='http', auth='user', website=True)
    def serve_app(self, **kwargs):
        """
        Serves the React application.
        The auth='user' ensures that only logged-in Odoo users can access the dashboard.
        """
        # We read the index.html from our static directory and return it.
        # This allows React Router to handle all paths under /app.
        addon_path = odoo.modules.get_module_path('networkPilotNew')
        index_file = os.path.join(addon_path, 'static', 'app', 'index.html')
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return request.make_response(content, headers=[('Content-Type', 'text/html')])
        except FileNotFoundError:
            return request.make_response(
                "<h1>React App Not Built</h1><p>Please build the React app and place it in the static/app directory.</p>",
                headers=[('Content-Type', 'text/html')],
                status=404
            )
