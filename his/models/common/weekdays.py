from odoo import models, fields, api


class Weekdays(models.Model):
    _name = "his.weekdays"
    _description = "Weekdays Records"

    number = fields.Integer(string="Number")
    name = fields.Char(string="Name", required=True, translate=True)
