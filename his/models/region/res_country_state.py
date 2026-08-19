from odoo import api, fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    name = fields.Char(
        string="State Name",
        required=True,
        help="Administrative divisions of a country. E.g. Fed. State, Departement, Canton",
        translate=True,
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result
