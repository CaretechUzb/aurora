from odoo import models, fields, api, exceptions
from ...utils import convert_string_to_list


class InsuranceContract(models.Model):
    _name = "his.insurance_contract"
    _description = "Insurance Contract"

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    insurance_policy_ids = fields.One2many("his.insurance_policy", "contract_id")
    insurance_service_id = fields.Many2many("product.product")
