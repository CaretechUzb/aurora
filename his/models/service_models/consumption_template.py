from odoo import models, fields, api, exceptions


class ConsumptionTemplate(models.Model):
    _name = "his.consumption_template"
    _description = "Consumption Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    lines = fields.One2many(
        "his.consumption_template_line", "template_id", string="Lines", tracking=True
    )
