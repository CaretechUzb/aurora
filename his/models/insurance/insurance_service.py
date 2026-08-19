from odoo import models, fields, api, _


class InsuranceService(models.Model):
    _name = "his.insurance_service"
    _description = "Payers Service Records"

    contract_id = fields.Many2one("his.insurance_contract")
    service_id = fields.Many2one("product.product", string="Service")
    product_type = fields.Many2one(
        "his.category_base",
        string="Product Type",
        related="service_id.product_type",
        store=True,
    )
    categ_id = fields.Many2one(
        "product.category", string="Category", related="service_id.categ_id", store=True
    )
    list_price = fields.Float(
        string="List Price", related="service_id.list_price", store=True
    )
    discount = fields.Float(string="Discount")
    approval_date = fields.Date(string="Approval Date")
    is_cancel = fields.Boolean(string="Is Cancel")
    insurance_company_id = fields.Many2one(
        "his.insurance_company", string="Payers Company"
    )
