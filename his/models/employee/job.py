from odoo import fields, models, api


class HRJob(models.Model):
    _inherit = "hr.job"

    can_earn_share = fields.Boolean(string="Can earn share", tracking=True)