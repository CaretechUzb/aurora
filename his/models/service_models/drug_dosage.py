import re

from odoo import api, fields, models


class DrugDosage(models.Model):
    _name = "his.drug_dosage"
    _description = "Drug Dosage"

    product_id = fields.Many2one(
        "product.product", string="Product", required=True, ondelete="cascade"
    )
    dosage = fields.Char(string="Dosage", required=True)
    dosage_amount = fields.Float(string="Dosage Amount", required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.dosage))
        return result

    @api.onchange("dosage")
    def _onchange_dosage(self):
        if self.dosage:
            value = self.dosage.strip().replace(",", ".")
            match = re.match(r"([\d.]+)", value)
            if match:
                try:
                    self.dosage_amount = float(match.group(1))
                except ValueError:
                    pass
