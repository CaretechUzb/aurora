from odoo import models, fields, api, exceptions


class ConsumptionTemplateLine(models.Model):
    _name = "his.consumption_template_line"
    _description = "Consumption Template Line"
    _rec_name = "product_id"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    quantity = fields.Float(string="Quantity", compute="_compute_qty", store=True)
    is_free = fields.Boolean(string="Is Free")
    template_id = fields.Many2one(
        "his.consumption_template",
        string="Consumption Template",
        required=True,
        ondelete="cascade",
    )
    uom_id = fields.Many2one(
        "uom.uom", string="Unit of Measure", related="product_id.uom_id", readonly=True
    )
    product_name = fields.Char(
        related="product_id.name", string="Product Name", readonly=True
    )
    product_code = fields.Char(
        related="product_id.default_code", string="Product Code", readonly=True
    )
    unit_quantity = fields.Float(string="Unit Quantity")
    product_uom_id = fields.Many2one(
        "uom.uom", string="Product UoM", compute="_compute_product_uom_id", store=True
    )

    @api.depends("unit_quantity")
    def _compute_qty(self):
        for rec in self:
            if not rec.product_id.calculation_type:
                rec.quantity = rec.unit_quantity
            elif rec.product_id.calculation_type == "one_time":
                rec.quantity = rec.unit_quantity
            else:
                if rec.product_id.quantity_in_pack > 0:
                    rec.quantity = rec.unit_quantity / rec.product_id.quantity_in_pack
                else:
                    rec.quantity = rec.unit_quantity

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for record in self:
            if record.product_uom_id:
                continue
            if record.product_id.calculation_type:
                if record.product_id.calculation_type == "one_time":
                    record.product_uom_id = record.product_id.uom_id.id
                else:
                    record.product_uom_id = record.product_id.amt_unit.id
            else:
                record.product_uom_id = record.product_id.uom_id.id
