from odoo import models, fields, api, exceptions
from ...utils import convert_string_to_list


class PayerContract(models.Model):
    _name = "his.payer_contract"
    _description = "Payer Contract"

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    policy_ids = fields.One2many("his.payer_policy", "contract_id")
    payer_company_id = fields.Many2one("his.payer_company")
    template_id = fields.Many2one("his.payer_template")
    template_discount = fields.Float(related="template_id.discount", string="Discount")
