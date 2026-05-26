{
    'name': 'Networkpilot',
    'version': '1.0',
    'category': 'CRM',
    'summary': 'Personal CRM with Professional Context',
    'description': """
Networkpilot - A Personal CRM
=============================
Manage contacts, interactions, reminders, and AI suggestions.
    """,
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/category_tag_views.xml',
        'views/interaction_views.xml',
        'views/reminder_views.xml',
        'views/contact_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
