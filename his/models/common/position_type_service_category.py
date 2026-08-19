from odoo import models, fields


class PositionTypeServiceCategory(models.Model):
    _name = "his.position_type_service_category"
    _description = "Position Type Service Category"

    position_type = fields.Selection(
        [
            ("doctor", "Doctor"),
            ("nurse", "Nurse"),
            ("other", "Other"),
        ],
        string="Position Type",
    )

    service_category = fields.Many2many(
        "product.category",
        string="Excluded Services Category",
        domain=[("is_his", "=", True)],
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.position_type}"))
        return result
