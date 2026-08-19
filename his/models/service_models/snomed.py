from odoo import _, fields, models


class Snomed(models.Model):
    _name = "his.snomed"
    _description = "SNOMED CT Codes"
    _order = "name"

    code = fields.Char(
        string="SNOMED CT Code",
        required=True,
        index=True,
        help="SNOMED CT concept ID (e.g. 387207008)",
    )
    name = fields.Char(
        string="Name",
        required=True,
        translate=True,
        help="SNOMED CT concept display name",
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", _("SNOMED CT code must be unique.")),
    ]

    def name_get(self):
        return [(rec.id, f"{rec.name} ({rec.code})") for rec in self]
