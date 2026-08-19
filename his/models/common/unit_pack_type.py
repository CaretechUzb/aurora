from odoo import models, fields


class UnitPackType(models.Model):
    _name = "his.unit_pack_type"
    _description = "Unit Pack Type Records"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True, translate=True)
