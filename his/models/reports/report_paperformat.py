from odoo import models, fields, api, _


class report_paperformat(models.Model):
    _inherit = "report.paperformat"

    enable_forms = fields.Boolean("Enable Forms", default=False)
