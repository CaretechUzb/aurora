from odoo import models, fields, api, exceptions
from ...utils import convert_string_to_list
from odoo.exceptions import UserError
import base64
import csv
from io import StringIO
import io
import xlsxwriter


class InsurancePatient(models.Model):
    _name = "his.insurance_patient"
    _description = "Insurance patient"


class InsuranceCompany(models.Model):
    _name = "his.insurance_company"
    _inherit = "mail.thread"
    _inherits = {"res.partner": "partner_id"}
    _description = "Payers Company Records"
    _allow_sudo_commands = False

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        readonly=True,
        auto_join=True,
        index=True,
        string="Company ",
        help="Partner-related data of the Payers Company",
    )
    start_date = fields.Date(string="Expired Date ")
    end_date = fields.Date(string="Expired Date")
    contract_number = fields.Char(string="Contract Number")
    federate_number = fields.Char(string="Federate Number")

    description = fields.Text(string="Description")
    cooperation_type = fields.Selection(
        [
            ("дмс", "ДМС"),
            ("b2b", "B2B"),
            ("state_insurance", "Государственный фонд"),
        ],
        string="Cooperation Type",
    )
    # REQUISITES fields
    organization_name = fields.Char(string="Organization Name")
    inn = fields.Char(string="INN")
    checkpoint = fields.Char(string="Checkpoint")
    ogrn = fields.Char(string="OGRN")
    legal_address = fields.Char(string="Legal Address")
    actual_address = fields.Char(string="Actual Address")
    ceo = fields.Char(string="CEO")
    chief_accountant = fields.Char(string="Chief Accountant")
    bank_bic = fields.Char(string="Bank BIC")
    bank_name = fields.Char(string="Bank Name")
    correspondent_account = fields.Char(string="Correspondent Account")
    checking_account = fields.Char(string="Checking Account")

    contract_ids = fields.Many2many("his.insurance_contract", string="Contracts")
    global_discount = fields.Float(string="Global Discount")
    selected_insurance_contracts = fields.Char()
    selected_changed_field_many = fields.Char()
    export_selected_ids = fields.Char("export_selected_ids")
    export_file = fields.Binary(string="Export File", readonly=True)

    # company_id = fields.Many2one('res.branch', string='Company', required=True, default=lambda self: self.env.branch)

    # @api.onchange('global_discount')
    # def _onchange_global_discount(self):
    def action_multi_change_discount(self):
        self.ensure_one()
        if self.global_discount > 0:
            for service in self.service_ids:
                if ids := convert_string_to_list(self.selected_changed_field_many):
                    if service.ids[0] in ids:
                        service.discount = (
                            self.global_discount if self.global_discount <= 100 else 100
                        )

    @api.onchange("selected_insurance_contracts")
    def _onchange_selected_insurance_contracts(self):
        if self.selected_insurance_contracts:
            services_ids_str = (
                self.selected_insurance_contracts.replace("[", "")
                .replace("]", "")
                .replace(" ", "")
                .split(",")
            )
            services_ids = [int(service_id) for service_id in services_ids_str]
            selected_insurance_contract_ids = self.env["his.insurance_contract"].search(
                [("id", "in", services_ids)]
            )
            self.contract_ids = [
                (4, contract.id) for contract in selected_insurance_contract_ids
            ]

    def action_download_template(self):
        pass

    # def action_upload_patients(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'his.upload_insurance_patients',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }
