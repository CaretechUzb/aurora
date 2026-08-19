from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    equipment_id = fields.Many2one("maintenance.equipment", string="Equipments")