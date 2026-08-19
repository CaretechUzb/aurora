from odoo import models, fields, api, exceptions, _


class MedicineClassification(models.Model):
    _name = "his.medicine_classification"
    _description = "Medicine Classification Records"
    _rec_name = "method"

    abbreviation = fields.Char(string="Abbreviation", translate=True)
    method = fields.Char(string="Method", translate=True)
    times = fields.Integer(string="Times")
