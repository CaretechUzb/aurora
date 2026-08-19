from odoo import models, fields, api, exceptions


class PayerTemplate(models.Model):
    _name = "his.payer_template"
    _description = "Payer Template"

    name = fields.Char(required=True)
    discount = fields.Float()
    products_ids = fields.Many2many("product.product")
    payer_company_id = fields.Many2one("his.payer_company")

    def action_add_services(self):
        print("action_add_services")

    # @api.onchange('selected_insurance_contracts')
    # def _onchange_selected_insurance_contracts(self):
    #     if self.selected_insurance_contracts:
    #         services_ids_str = self.selected_insurance_contracts.replace('[', '').replace(']',
    #                                                                                       '').replace(' ', '').split(
    #             ',')
    #         services_ids = [int(service_id) for service_id in services_ids_str]
    #         selected_insurance_contract_ids = self.env['his.insurance_contract'].search([('id', 'in', services_ids)])
    #         self.contract_ids = [(4, contract.id) for contract in selected_insurance_contract_ids]
