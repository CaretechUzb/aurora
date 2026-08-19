from odoo import models, fields, api, exceptions, _
from ...utils import convert_string_to_list
from odoo.exceptions import UserError, ValidationError
import base64
import csv
from io import StringIO
import io
import xlsxwriter
from datetime import datetime, timedelta


class PayerCompany(models.Model):
    _name = "his.payer_company"
    _inherit = ["mail.thread"]
    _inherits = {"res.partner": "partner_id"}
    _description = "Payer Company Records"
    _allow_sudo_commands = False

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        auto_join=True,
        index=True,
        string="Company ",
        help="Partner-related data of the Payer Company",
    )
    name = fields.Char(related="partner_id.name", inherited=True, readonly=False)
    start_date = fields.Date(string="Start Date ")
    end_date = fields.Date(string="Expired Date")
    # contract_number = fields.Char(string='Contract Number')
    # federate_number = fields.Char(string='Federate Number')

    description = fields.Text(string="Description")
    cooperation_type = fields.Selection(
        [
            ("дмс", "ДМС"),
            ("b2b", "B2B"),
            ("state_payer", "State fund"),
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

    contract_ids = fields.One2many(
        "his.payer_contract", "payer_company_id", string="Contracts"
    )
    global_discount = fields.Float(string="Global Discount")
    selected_payer_contracts = fields.Char()
    selected_changed_field_many = fields.Char()
    export_contract_ids = fields.Char("contract_export_ids")
    export_policy_ids = fields.Char("policy_export_ids")
    export_file = fields.Binary(string="Export File", readonly=True)
    selected_payer_template_ids = fields.Char()
    template_ids = fields.Many2many("his.payer_template")
    policy_ids = fields.One2many(
        "his.payer_policy", "payer_company_id", string="Policies"
    )
    payer_invoice_ids = fields.Many2many(
        "account.move", compute="_compute_policy_invoice_ids"
    )
    is_limit_validation_enabled = fields.Boolean(string="Limit Validation", default=True)
    can_autogenerate_policy = fields.Boolean(string="Can autogenerate policy")
    tg_bot_token = fields.Char(string="Telegram Bot Token")
    web_link = fields.Char(string="Web Link")
    auto_send_resalt = fields.Boolean(string="Auto Send Result", default=False)

    @api.onchange("can_autogenerate_policy")
    def _onchange_can_autogenerate_policy(self):
        if self.can_autogenerate_policy:
            self.is_limit_validation_enabled = False

    @api.depends("partner_id")
    def _compute_policy_invoice_ids(self):
        for rec in self:
            rec.payer_invoice_ids = self.env["account.move"].search(
                [
                    ("partner_id", "=", rec.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                ]
            )

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

    @api.onchange("selected_payer_contracts")
    def _onchange_selected_payer_contracts(self):
        if self.selected_payer_contracts:
            services_ids_str = (
                self.selected_payer_contracts.replace("[", "")
                .replace("]", "")
                .replace(" ", "")
                .split(",")
            )
            services_ids = [int(service_id) for service_id in services_ids_str]
            selected_payer_contract_ids = self.env["his.payer_contract"].search(
                [("id", "in", services_ids)]
            )
            self.contract_ids = [
                (4, contract.id) for contract in selected_payer_contract_ids
            ]

    def action_download_template(self):
        pass

    def action_import_contract(self):
        pass

    def action_export_contract(self):
        pass

    def action_export(self):
        self.ensure_one()
        export_field = self.env.context.get("export_field")

        # Faqat belgilangan child yozuvlarini eksport qilish
        if export_field == "contract":
            export_ids = convert_string_to_list(self.export_contract_ids)
            exports = self.contract_ids.filtered(lambda c: c.id in export_ids)
        elif export_field == "policy":
            export_ids = convert_string_to_list(self.export_policy_ids)
            exports = self.policy_ids.filtered(lambda c: c.id in export_ids)

        if not export_field:
            raise UserError(_("Export field is not specified."))

        if not exports:
            raise UserError(_("Export field not found."))

        # XLSX faylini yaratish
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet(f"{export_field}")

        # Sarlavhalar
        headers = []
        if export_field == "contract":
            headers = ["Name", "Date"]  # his.payer_contract uchun
        elif export_field == "policy":
            headers = [
                "Full Name",
                "Passport Serial",
                "Phone Number",
                "PINFL",
                "Birth Date",
                "Gender",
                "Contract ID",
                "Company ID",
                "Patient ID",
                "Policy Number",
                "Policy Amount",
                "From Date",
                "To Date",
                "Is Active",
            ]  # his.payer_policy uchun

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Ma'lumotlarni yozish
        for row, contract in enumerate(exports, start=1):
            if export_field == "contract":
                worksheet.write(row, 0, contract.name)
                worksheet.write(
                    row, 1, contract.date.strftime("%d/%m/%Y") if contract.date else ""
                )
            elif export_field == "policy":
                worksheet.write(row, 0, contract.full_name)
                worksheet.write(row, 1, contract.passport_serial)
                worksheet.write(row, 2, contract.phone_number)
                worksheet.write(row, 3, contract.pinfl)
                worksheet.write(
                    row,
                    4,
                    (
                        contract.birth_date.strftime("%d/%m/%Y")
                        if contract.birth_date
                        else ""
                    ),
                )
                worksheet.write(row, 5, contract.gender)
                worksheet.write(
                    row, 6, contract.contract_id.name if contract.contract_id else ""
                )
                worksheet.write(
                    row, 7, contract.company_id.name if contract.company_id else ""
                )
                worksheet.write(
                    row, 8, contract.patient_id.name if contract.patient_id else ""
                )
                worksheet.write(row, 9, contract.policy_number)
                worksheet.write(row, 10, contract.policy_amount)
                worksheet.write(
                    row,
                    11,
                    (
                        contract.from_date.strftime("%d/%m/%Y")
                        if contract.from_date
                        else ""
                    ),
                )
                worksheet.write(
                    row,
                    12,
                    contract.to_date.strftime("%d/%m/%Y") if contract.to_date else "",
                )
                worksheet.write(row, 13, contract.is_active)

        workbook.close()
        xlsx_data = output.getvalue()
        output.close()

        # Encode qilish
        xlsx_encoded = base64.b64encode(xlsx_data).decode("utf-8")

        # Faylni attachment sifatida yaratish
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"{export_field}_export_{self.name}.xlsx",
                "type": "binary",
                "datas": xlsx_encoded,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "res_model": "his.payer_company",
                "res_id": self.id,
            }
        )

        # Faylni brauzerga yuklab berish URL manzilini yaratish
        download_url = f"/web/content/{attachment.id}?download=true"

        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "new",
        }

    def action_import(self):
        self.ensure_one()

        import_field = self.env.context.get("import_field")
        if not import_field:
            raise UserError(_("Import field is not specified."))

        return {
            "type": "ir.actions.act_window",
            "name": "Import",
            "res_model": "his.payer_contract_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_import_field": import_field,
                "default_payer_company": self.id,
            },
        }

    @api.model
    def clean_old_attachments(self):

        attachments = self.env["ir.attachment"].search(
            [
                ("create_date", "<", fields.Datetime.now()),
                ("res_model", "=", "his.payer_company"),
            ]
        )
        attachments.unlink()

    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="his_payer_company_api_users_rel",
        column1="payer_id",
        column2="user_id",
        string="Users",
        domain="[('share', '=', True)]",
        help=(
            "Portal users (share=True) attached to this payer. Used by "
            "API integrations and ir.rule scoping to authorise access on "
            "behalf of this payer."
        ),
    )

    def write(self, vals):
        # Snapshot ``user_ids`` membership *before* the write so the
        # post-write hook can diff added/removed users (the ORM cache
        # returns the new value after super().write()). This single
        # snapshot is reused by subclasses through
        # ``_on_payer_user_ids_changed`` — they must not take their own.
        before = (
            {rec.id: set(rec.user_ids.ids) for rec in self}
            if "user_ids" in vals
            else {}
        )
        result = super().write(vals)
        if "user_ids" in vals:
            self._on_payer_user_ids_changed(before)
        return result

    def _on_payer_user_ids_changed(self, before):
        """Hook fired after a write that changed ``user_ids``.

        ``before`` maps record id -> set of previously-attached user ids.
        Core stamps newly-attached users' ``external_partner_id`` with the
        payer's own partner so HIS-level integrations (LIS external orders,
        billing, ...) know which payer the user represents. Subclasses
        override to add their own membership-change side effects and call
        ``super()`` to keep this stamp.
        """
        for rec in self:
            added = set(rec.user_ids.ids) - before.get(rec.id, set())
            if not added or not rec.partner_id:
                continue
            # added_users is already a sudo recordset; stamp the ones
            # that still point elsewhere in a single batch write to
            # avoid a per-user UPDATE.
            added_users = self.env["res.users"].sudo().browse(list(added))
            to_stamp = added_users.filtered(
                lambda u: u.external_partner_id != rec.partner_id
            )
            if to_stamp:
                to_stamp.write({"external_partner_id": rec.partner_id.id})

    @api.constrains("user_ids")
    def _check_user_single_payer(self):
        # DEV-107: a portal user belongs to at most one payer company —
        # cross-payer membership would let one payer's cabinet/API user
        # read another payer's ir.rule-scoped data. Fail closed: read
        # everything with active_test=False so an archived user/payer can
        # never slip a duplicate past the guard. sudo() on the cross-payer
        # search is required — an ir.rule that hides the conflicting payer
        # would otherwise make the check pass and open the hole.
        recs = self.with_context(active_test=False)
        users = recs.mapped("user_ids")
        if not users:
            return
        others = (
            self.env["his.payer_company"].sudo()
            .with_context(active_test=False)
            .search([("id", "not in", self.ids), ("user_ids", "in", users.ids)])
        )
        taken = set(others.mapped("user_ids").ids)
        for rec in recs:
            clash = rec.user_ids.filtered(
                lambda u: u.id in taken or u in (recs - rec).user_ids
            )
            if clash:
                raise ValidationError(
                    _(
                        "User(s) %s already belong to another payer company; "
                        "a user can be attached to only one payer."
                    )
                    % ", ".join(clash.mapped("display_name"))
                )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if not args:
            args = []

        if "filter_coverer_type" in self.env.context:
            args.append(
                ("cooperation_type", "=", self.env.context.get("filter_coverer_type"))
            )

        return super(PayerCompany, self).name_search(name, args, operator, limit)
