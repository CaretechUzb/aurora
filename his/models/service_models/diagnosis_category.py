from odoo import exceptions, fields, models, api, _


class DiagnosisCategory(models.Model):
    _name = "his.diagnosis_category"
    _description = "Diagnosis Category Records"
    _rec_name = "name"

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    parent_id = fields.Many2one("his.diagnosis_category", string="Parent Category")

    # complete_name = fields.Char(
    #     'Complete Name', compute='_compute_complete_name', recursive=True,
    #     store=True)
    #
    # @api.depends('name', 'parent_id.complete_name')
    # def _compute_complete_name(self):
    #     for category in self:
    #         if category.parent_id:
    #             category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
    #         else:
    #             category.complete_name = category.name
