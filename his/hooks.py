from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Rename subject of Welcome to Aurora+ mail"""
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        record = env.ref("mail.module_install_notification")
        record.write({"subject": "Welcome to Aurora+"})
    except:
        pass
