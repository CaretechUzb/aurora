from odoo import models, fields, api, exceptions


class FavouriteProducts(models.Model):
    _name = "his.favourite_products"
    _description = "Favourite Products Records"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True)
    priority_color = fields.Char(
        related="product_id.priority_color", string="Priority Color", readonly=True
    )
    type = fields.Selection(
        [("all", "All"), ("doctor", "Doctor"), ("department", "Department")],
        string="Type",
        default="all",
        required=True,
    )
    doctor_id = fields.Many2one("hr.employee", string="Doctor")
    department_id = fields.Many2one("hr.department", string="Department")

    @api.onchange("type")
    def onchange_type(self):
        if self.type == "department":
            self.doctor_id = False
        elif self.type == "doctor":
            self.department_id = False
