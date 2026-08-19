from odoo import models, fields


class GTINProducts(models.Model):
    _name = "his.gtin_products"
    _description = "GTIN Products Records"
    _rec_name = "name"

    name = fields.Char(string="GTIN", required=True)
    package_code = fields.Char("MXIK Package Code")
    class_code = fields.Char("MXIK Class Code")
