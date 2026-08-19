from odoo import models, fields, api, _


class Diagnosis(models.Model):
    _name = "his.diagnosis"
    _description = "Diagnosis Records"
    _rec_name = "name"

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", translate=True)
    category_id = fields.Many2one("his.diagnosis_category", string="Category")
    complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", store=True
    )

    @api.depends("name", "code")
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = "%s (%s)" % (rec.name, rec.code)
