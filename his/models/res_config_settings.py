import base64
import requests
import re
import pytz
from datetime import datetime
from html import escape
from odoo import api, fields, models
from telegraph import Telegraph
from odoo.exceptions import UserError

DEFAULT_REQUIRED_FIELDS = [
    'first_name',
    'last_name',
    'date',
    'phone_number',
    'gender',
]

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    reception_invoice_emr = fields.Many2one(
        "report.report",
        string="Reception Invoice EMR",
        domain="[('model_id.model', '=', 'sale.order')]",
    )
    cashier_report_emr = fields.Many2one(
        "report.report",
        string="Cashier Report EMR",
        domain="[('model_id.model', '=', 'his.cashier_session_wizard')]",
    )

    reception_invoice_with_coverer_emr = fields.Many2one(
        "report.report",
        string="Reception Invoice with Coverer EMR",
        domain="[('model_id.model', '=', 'sale.order')]",
    )
    cashier_cheque_emr = fields.Many2one(
        "report.report",
        string="Cashier cheque EMR",
        domain="[('model_id.model', '=', 'account.move')]",
    )

    receipt_with_debt_emr = fields.Many2one(
        "report.report",
        string="Receipt with debt",
        domain="[('model_id.model', '=', 'account.move')]",
    )
    registration_print_button = fields.Many2one(
        "report.report",
        string="Registration Print Button",
        domain="[('model_id.model', '=', 'his.order_print_wizard')]",
    )
    top_up_customer_emr = fields.Many2one(
        "report.report",
        string="Top Up Customer Deposit",
        domain="[('model_id.model', 'in', ['his.top_up_patient_balance_wizard', 'account.payment'])]",
    )
    return_customer_emr = fields.Many2one(
        "report.report",
        string="Return Customer Deposit",
        domain="[('model_id.model', 'in', ['his.top_up_patient_balance_wizard', 'account.payment'])]",
    )
    prescription_emr = fields.Many2one(
        "report.report",
        string="Prescription EMR",
        domain="[('model_id.model', '=', 'his.prescription')]",
    )
    prescription_print_template = fields.Many2one(
        "report.report",
        string="Prescription Print Template",
        domain="[('model_id.model', '=', 'his.prescription_print_wizard')]",
    )
    calculator_emr = fields.Many2one(
        "report.report",
        string="Calculator EMR",
        domain="[('model_id.model', '=', 'his.calculate_orders_wizard')]",
    )
    payment_history_print_emr = fields.Many2one(
        "report.report",
        string="Payment History Print EMR",
        domain="[('model_id.model', '=', 'his.payment_history_print_wizard')]",
    )
    require_patient_guardian = fields.Boolean(
        string="Require Patient Guardian",
        help="If checked, the patient guardian will be required when creating a new patient.",
        default=True,
    )
    is_pause_button_show = fields.Boolean(
        string="Pause Button Show",
        help="If checked, the in ambulatory visits form will show the pause button.",
        default=False,
    )

    restrict_product_selection_in_registration = fields.Boolean(
        string="Restrict Product Selection in Registration",
        help="Allow only services to be selected in the registration form.",
        default=False,
    )

    check_patient_name = fields.Boolean(
        string="Check Patient Name",
        help="If checked, patient names must contain only Latin or Cyrillic characters.",
        default=True,
    )

    is_doctor_dashboard_revenue_show = fields.Boolean(
        string="Show Revenue in Doctor Dashboard",
        default=True,
    )

    deposit_top_up_account_id = fields.Many2one(
        "account.analytic.account", string="Deposit Top Up Account"
    )
    deposit_return_account_id = fields.Many2one(
        "account.analytic.account", string="Deposit Return Account"
    )
    inkasso_account_id = fields.Many2one(
        "account.analytic.account", string="Inkasso Account"
    )

    # Due From/Due To Account fields - related to company
    due_from_account_id = fields.Many2one(
        "account.account",
        string="Due From",
        related="company_id.due_from_account_id",
        readonly=False,
    )
    due_to_account_id = fields.Many2one(
        "account.account",
        string="Due To",
        related="company_id.due_to_account_id",
        readonly=False,
    )
    due_fromto_payment_journal_id = fields.Many2one(
        "account.journal",
        string="Due From/Due To Journal",
        related="company_id.due_fromto_payment_journal_id",
        readonly=False,
    )

    # Share outstanding payments - company independent setting
    share_outstanding_payments = fields.Boolean(
        string="Share outstanding payments",
        help="Enable sharing of outstanding payments across companies",
        default=False,
    )

    only_manager_can_delete_amb = fields.Boolean(
        string="Only managers can delete ambulatory services",
        config_parameter="his.only_manager_can_delete_amb",
        default=False,
    )

    max_discount_for_referral = fields.Float(
        string="Max Allowed Discount for Referral Bonus (%)",
        digits=(2, 2),
        config_parameter="his.max_discount_for_referral",
    )
    identifying_similar_patients_trgm_limit = fields.Float(
        string="Duplicate patient trigram limit",
        config_parameter="his.identifying_similar_patients_trgm_limit",
        default=0.3,
        digits=(2, 2),
        help="pg_trgm similarity threshold (0.0–1.0, default 0.3) used when "
             "searching for duplicate patients by name. "
             "Lower values match more loosely — more candidate duplicates are "
             "surfaced, at the cost of more false positives. "
             "Higher values require closer name matches — fewer candidates and "
             "fewer false positives, but near-duplicates may be missed. "
             "Values outside 0.0–1.0 are ignored and the default 0.3 is used.",
    )
    identifying_similar_patients_min_matches_with_key = fields.Integer(
        string="Duplicate patient min matching name parts (with strong key)",
        config_parameter="his.identifying_similar_patients_min_matches_with_key",
        default=1,
        help="Minimum name positions that must match when a strong dedup key "
             "(birth date / phone / PINFL) is also present. Lower = looser name "
             "match, surfacing more spelling/transliteration variants. Default 1. "
             "Values below 1 are ignored and the default is used.",
    )
    identifying_similar_patients_min_matches_no_key = fields.Integer(
        string="Duplicate patient min matching name parts (no strong key)",
        config_parameter="his.identifying_similar_patients_min_matches_no_key",
        default=2,
        help="Minimum name positions that must match when no strong dedup key is "
             "present. Higher = stricter name match, fewer false positives — but "
             "note a high value silently collapses to 'all name parts must match', "
             "so a single typo can hide a real duplicate. Default 2. Values below 1 "
             "are ignored and the default is used.",
    )
    identifying_similar_patients_match_by_phone = fields.Boolean(
        string="Flag duplicate patients sharing a phone number",
        config_parameter="his.identifying_similar_patients_match_by_phone",
        default=False,
        help="If enabled, during patient registration a matching phone number "
             "(primary or secondary) also flags a potential duplicate, even when "
             "the name and birth date differ. Disabled by default. Note: patients "
             "who legitimately share a phone (e.g. family members) may be surfaced "
             "as duplicates.",
    )
    identifying_similar_patients_match_by_birth_date = fields.Boolean(
        string="Require exact birth date match for duplicate patients",
        config_parameter="his.identifying_similar_patients_match_by_birth_date",
        default=True,
        help="When enabled (default), a birth date entered during registration "
             "must match exactly for a patient to be flagged as a duplicate, and "
             "it also loosens the name match. Disable to surface same-name "
             "patients even when their birth dates differ or are missing — useful "
             "when DOB is often mistyped or unknown. Affects patient registration "
             "only.",
    )
    identifying_similar_patients_result_limit = fields.Integer(
        string="Duplicate patient name-only result cap",
        config_parameter="his.identifying_similar_patients_result_limit",
        default=100,
        help="Max candidate duplicate patients shown for a NAME-ONLY search "
             "(top-N by similarity), and the point at which the search wizard "
             "shows a 'narrow your search' note. Searches that include a birth "
             "date, PINFL, or phone number are never capped, so an exact-key "
             "match is never hidden. Default 100. Values below 1 are ignored.",
    )
    error_handle_bot_token = fields.Char(default=False)
    error_handle_group_id = fields.Char(config_parameter="his.error_handle_group_id",
        default=False)
    error_handle_group_topic_id = fields.Char(config_parameter="his.error_handle_group_topic_id",
        default=False)
    can_merge_multitab_pdf = fields.Boolean(
        string="Allow Merge Multi-tab PDF",
        config_parameter="his.can_merge_multitab_pdf",
        default=False,
        help="If enabled, multiple PDFs in multi-tab viewer will be merged into one."
    )
    include_unpaid_visits = fields.Boolean(
        string="Include Unpaid Visits",
        config_parameter="his.include_unpaid_visits",
        default=False,
        help="If enabled, unpaid visits will also be shown in the outpatient list (read-only)."
    )
    can_access_unpaid_visits = fields.Boolean(
        string="Allow Access to Unpaid Visits",
        config_parameter="his.can_access_unpaid_visits",
        default=False,
        help="If enabled, users can open unpaid visits from the outpatient list. Otherwise, unpaid visits will be hidden from the list."
    )
    share_and_bonus_price_source = fields.Selection(
        [
            ("sale_order_line", "Sale Order Line"),
            ("account_move_line", "Account Move Line"),
        ],
        string="Share and Bonus Price Source",
        config_parameter="his.share_and_bonus_price_source",
        default="sale_order_line",
        required=True,
        help="Select the source for price calculation in doctor share and bonus records."
    )
    order_wizard_switcher_status = fields.Selection(
        [
            ("service_to_doctor", "Service -> Doctor"),
            ("doctor_to_service", "Doctor -> Service"),
        ],
        default="service_to_doctor",
        string="Order Wizard Default Status for switcher.",
        config_parameter="his.order_wizard_switcher_status",
        required=True
    )

    subtract_covered_discount_from_share_and_bonus = fields.Boolean(
        string="Subtract Covered Discount from Share and Bonus",
        config_parameter="his.subtract_covered_discount_from_share_and_bonus",
        default=False,
        help="If enabled, covered discounts will be subtracted from doctor share and bonus calculations."
    )
    subtract_covered_discount_for_actual_price = fields.Boolean(
        string="Subtract Covered Discount from Share and Bonus for Actual Price Calculation",
        config_parameter="his.subtract_covered_discount_for_actual_price",
        default=False,
        help="If enabled, covered discounts will be subtracted from actual price calculations in doctor share and bonus. Discount recalculated based on partner's global discount."
    )
    require_diagnosis = fields.Boolean(
        string="Make diagnosis optional",
        config_parameter='his.require_diagnosis'
    )
    allow_doctor_fee_greater_than_service = fields.Boolean(
        string="Allow doctor fee price greater than service price",
        config_parameter='his.allow_doctor_fee_greater_than_service'
    )

    show_share_bonus_edit_button = fields.Boolean(
        string="Show Share and Bonus Edit Button",
        config_parameter="his.show_share_bonus_edit_button",
        default=False,
        help="If enabled, users will see an Edit button on share and bonus records to adjust the amount manually.",
    )
    allow_dosage_selection = fields.Boolean(
        string="Allow dosage selection on prescription",
        config_parameter="his.allow_dosage_selection",
        default=False,
    )

    allow_negative_transfer = fields.Boolean(
        string="Allow negative transfer",
        default=False,
        help="If enabled, cash transfers can be made even when the cash balance is insufficient."
    )

    block_cancel_invoice_when_service_done = fields.Boolean(
        string="Block cancel invoice when service is done",
        config_parameter="his.block_cancel_invoice_when_service_done",
        default=False,
        help="If enabled, invoices cannot be cancelled when any related service order line is already marked as done."
    )

    show_payment_method_line = fields.Boolean(
        string="Show Payment Method in Cash In/Out",
        default=False,
        help="If enabled, the Payment Method field will be shown in the Cash In/Out wizard.",
    )
    require_analytic_account_for_cash_in = fields.Boolean(
        string="Require Analytic Account for Cash In",
        config_parameter="his.require_analytic_account_for_cash_in",
        default=False,
        help="If enabled, the Analytic Account field becomes mandatory for Cash In transactions.",
    )
    require_analytic_account_for_cash_out = fields.Boolean(
        string="Require Analytic Account for Cash Out",
        config_parameter="his.require_analytic_account_for_cash_out",
        default=False,
        help="If enabled, the Analytic Account field becomes mandatory for Cash Out transactions.",
    )

    doctor_fee_price_date = fields.Selection(
        [
            ("now", "Current Date"),
            ("visit_date", "Visit Date"),
        ],
        string="Doctor Fee Price Date",
        config_parameter='his.doctor_fee_price_date',
        default="now",
        required=True,
        help="Select how to determine which price to use for doctor fees:\n"
             "- Current Date: Use prices based on today's date\n"
             "- Visit Date: Use prices based on the patient visit date"
    )

    patient_required_field_ids = fields.Many2many(
        'ir.model.fields',
        'res_config_patient_req_field_rel',
        'config_id', 'field_id',
        domain=[('model', '=', 'his.patient')],
        string='Required patient fields',
        help='These fields will be required on Patient form.',
    )
    disable_referral_fallback_to_main_visit = fields.Boolean(
        string="Disable referral fallback to main visit",
        config_parameter="his.disable_referral_fallback_to_main_visit",
        help="If enabled, when a sub-visit has no referral source, the system will NOT fall back to the main visit referral source."
    )

    show_products_in_doctor_done_services = fields.Boolean(
        string="Show products in Doctor Done Services",
        config_parameter="his.show_products_in_doctor_done_services",
        help="If enabled, Doctor Done Services will display regular products along with services."
    )

    allow_old_visit_ordering = fields.Boolean(
        string="Allow adding orders on past visits",
        config_parameter="his.allow_old_visit_ordering",
        default=False,
        help="If enabled, doctors (non-managers) can also add and delete service orders on visits from previous days."
    )

    duplicate_recom_check = fields.Selection(
        [
            ('none', 'No check'),
            ('block', 'Block'),
        ],
        string="Duplicate recommendation check",
        config_parameter="his.duplicate_recom_check",
        default="none",
        help="Controls what happens when a doctor recommends a service already recommended in the same day's visit.\n"
             "- No check: allow freely\n"
             "- Block: prevent adding the duplicate recommendation entirely",
    )

    title = fields.Char(string="Title", default="Aurora+", config_parameter='title')

    print_button_template_ids = fields.Many2many(
        "report.report",
        "res_config_print_button_template_rel",
        string="Print Button Templates",
        domain="[('model_id.model', '=', 'his.order_print_wizard')]",
        help="Reports used for the Print button "
         "(Registration, Admission, Patient Total View).",
    )

    his_content_lang_id = fields.Many2one(
        'res.lang',
        string="Default Content Language",
        domain="[('active', '=', True)]",
        help="Default language used when extracting content from translatable fields "
             "for reports, exports, or storing in non-translatable fields."
    )

    app_version = fields.Char(
        string="Application version",
        readonly=True,
        help="Latest release from CHANGELOG.MD. Refreshed on every container "
             "start by start-entrypoint.d/010_refresh_app_version.",
    )


    def _get_default_patient_required_fields(self):
        """his.patient modelidagi default majburiy fieldlar (ir.model.fields recordlari)."""
        return self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'his.patient'),
            ('name', 'in', DEFAULT_REQUIRED_FIELDS),
        ])


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].set_param(
            "his.reception_invoice_emr", self.reception_invoice_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.cashier_report_emr", self.cashier_report_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.cashier_cheque_emr", self.cashier_cheque_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.receipt_with_debt_emr", self.receipt_with_debt_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.registration_print_button", self.registration_print_button.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.payment_history_print_emr", self.payment_history_print_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.top_up_customer_emr", self.top_up_customer_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.return_customer_emr", self.return_customer_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.prescription_emr", self.prescription_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.prescription_print_template", self.prescription_print_template.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.calculator_emr", self.calculator_emr.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.reception_invoice_with_coverer_emr",
            self.reception_invoice_with_coverer_emr.id,
        )
        self.env["ir.config_parameter"].set_param(
            "his.require_patient_guardian", self.require_patient_guardian
        )
        self.env["ir.config_parameter"].set_param(
            "his.is_pause_button_show", self.is_pause_button_show
        )
        self.env["ir.config_parameter"].set_param(
            "his.show_payment_method_line", self.show_payment_method_line
        )

        self.env["ir.config_parameter"].set_param(
            "his.title", self.title
        )

        self.env["ir.config_parameter"].set_param(
            "his.restrict_product_selection_in_registration",
            self.restrict_product_selection_in_registration,
        )
        self.env["ir.config_parameter"].set_param(
            "his.check_patient_name", self.check_patient_name
        )
        self.env["ir.config_parameter"].set_param(
            "his.is_doctor_dashboard_revenue_show",
            self.is_doctor_dashboard_revenue_show,
        )

        self.env["ir.config_parameter"].set_param(
            "his.deposit_top_up_account_id", self.deposit_top_up_account_id.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.deposit_return_account_id", self.deposit_return_account_id.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.inkasso_account_id", self.inkasso_account_id.id
        )
        self.env["ir.config_parameter"].set_param(
            "his.share_outstanding_payments", self.share_outstanding_payments
        )
        self.env["ir.config_parameter"].set_param(
            "his.only_manager_can_delete_amb", self.only_manager_can_delete_amb
        )
        self.env["ir.config_parameter"].set_param(
            "his.max_discount_for_referral", self.max_discount_for_referral
        )
        if self.error_handle_bot_token != '****************':
            self.env["ir.config_parameter"].set_param(
                "his.error_handle_bot_token", self.error_handle_bot_token or False
            )

        self.env["ir.config_parameter"].set_param(
            "his.error_handle_group_id", self.error_handle_group_id
        )
        self.env["ir.config_parameter"].set_param(
            "his.error_handle_group_topic_id", self.error_handle_group_topic_id
        )
        self.env["ir.config_parameter"].set_param(
            "his.can_merge_multitab_pdf", self.can_merge_multitab_pdf
        )
        self.env["ir.config_parameter"].set_param(
            "his.include_unpaid_visits", self.include_unpaid_visits
        )
        self.env["ir.config_parameter"].set_param(
            "his.can_access_unpaid_visits", self.can_access_unpaid_visits
        )
        self.env["ir.config_parameter"].set_param(
            "his.require_diagnosis", self.require_diagnosis
        )
        self.env["ir.config_parameter"].set_param(
            "his.allow_doctor_fee_greater_than_service",
            self.allow_doctor_fee_greater_than_service
        )
        self.env["ir.config_parameter"].set_param(
            "his.allow_negative_transfer", self.allow_negative_transfer
        )
        self.env["ir.config_parameter"].set_param(
            "his.disable_referral_fallback_to_main_visit",
            self.disable_referral_fallback_to_main_visit
        )
        ICP = self.env['ir.config_parameter'].sudo()

        default_fields = self._get_default_patient_required_fields()

        ids = set(self.patient_required_field_ids.ids) | set(default_fields.ids)

        ICP.set_param(
            'his.patient_required_field_ids',
            ','.join(map(str, ids)) if ids else ''
        )
        ICP.set_param(
            'show_products_in_doctor_done_services', self.show_products_in_doctor_done_services
        )
        ICP.set_param(
            'his.print_button_template_ids',
            ','.join(map(str, self.print_button_template_ids.ids)) if self.print_button_template_ids else ''
        )
        ICP.set_param(
            'his.his_content_lang_id', self.his_content_lang_id.id
        )

        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        reception_invoice_emr = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.reception_invoice_emr")
        )
        cashier_report_emr = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.cashier_report_emr")
        )
        reception_invoice_with_coverer_emr = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.reception_invoice_with_coverer_emr")
        )
        cashier_cheque_emr = (
            self.env["ir.config_parameter"].sudo().get_param("his.cashier_cheque_emr")
        )
        receipt_with_debt_emr = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.receipt_with_debt_emr")
        )
        registration_print_button = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.registration_print_button")
        )
        payment_history_print_emr = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.payment_history_print_emr")
        )
        top_up_customer_emr = (
            self.env["ir.config_parameter"].sudo().get_param("his.top_up_customer_emr")
        )
        return_customer_emr = (
            self.env["ir.config_parameter"].sudo().get_param("his.return_customer_emr")
        )
        prescription_emr = (
            self.env["ir.config_parameter"].sudo().get_param("his.prescription_emr")
        )
        prescription_print_template = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.prescription_print_template")
        )
        calculator_emr = (
            self.env["ir.config_parameter"].sudo().get_param("his.calculator_emr")
        )
        require_patient_guardian = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.require_patient_guardian")
        )
        is_pause_button_show = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.is_pause_button_show")
        )
        show_payment_method_line = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.show_payment_method_line")
        )
        restrict_product_selection_in_registration = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.restrict_product_selection_in_registration")
        )
        check_patient_name = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.check_patient_name", "True")
        )
        is_doctor_dashboard_revenue_show = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.is_doctor_dashboard_revenue_show")
        )
        deposit_top_up_account_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.deposit_top_up_account_id")
        )
        deposit_return_account_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.deposit_return_account_id")
        )
        inkasso_account_id = (
            self.env["ir.config_parameter"].sudo().get_param("his.inkasso_account_id")
        )
        share_outstanding_payments = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.share_outstanding_payments")
        )
        only_manager_can_delete_amb = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.only_manager_can_delete_amb")
        )
        max_discount_for_referral = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.max_discount_for_referral")
        )
        error_handle_bot_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_bot_token")
        )
        error_handle_group_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_group_id")
        )
        error_handle_group_topic_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_group_topic_id")
        )
        can_merge_multitab_pdf = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.can_merge_multitab_pdf")
        )
        include_unpaid_visits = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.include_unpaid_visits")
        )
        can_access_unpaid_visits = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.can_access_unpaid_visits")
        )
        require_diagnosis = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.require_diagnosis")
        )
        allow_doctor_fee_greater_than_service = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.allow_doctor_fee_greater_than_service")
        )
        allow_negative_transfer = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.allow_negative_transfer")
        )

        disable_referral_fallback_to_main_visit = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.disable_referral_fallback_to_main_visit")
        )
        show_products_in_doctor_done_services = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.show_products_in_doctor_done_services")

        )
        ICP = self.env['ir.config_parameter'].sudo()

        ids_str = ICP.get_param('his.patient_required_field_ids', '')
        ids = {int(x) for x in ids_str.split(',') if x}

        default_fields = self._get_default_patient_required_fields()
        ids |= set(default_fields.ids)
        ICP = self.env['ir.config_parameter'].sudo()
        button_ids_str = ICP.get_param('his.print_button_template_ids', '') or ''
        button_ids = [int(x) for x in button_ids_str.split(',') if x]
        his_content_lang_id = ICP.get_param('his.his_content_lang_id', '')
        app_version = ICP.get_param('his.app_version', 'unknown')

        res.update(
            reception_invoice_emr=(
                int(reception_invoice_emr) if reception_invoice_emr else False
            ),
            cashier_report_emr=(
                int(cashier_report_emr) if cashier_report_emr else False
            ),
            reception_invoice_with_coverer_emr=(
                int(reception_invoice_with_coverer_emr)
                if reception_invoice_with_coverer_emr
                else False
            ),
            cashier_cheque_emr=(
                int(cashier_cheque_emr) if cashier_cheque_emr else False
            ),
            receipt_with_debt_emr=(
                int(receipt_with_debt_emr) if receipt_with_debt_emr else False
            ),
            registration_print_button=(
                int(registration_print_button) if registration_print_button else False
            ),
            payment_history_print_emr=(
                int(payment_history_print_emr) if payment_history_print_emr else False
            ),
            top_up_customer_emr=(
                int(top_up_customer_emr) if top_up_customer_emr else False
            ),
            return_customer_emr=(
                int(return_customer_emr) if return_customer_emr else False
            ),
            prescription_emr=(int(prescription_emr) if prescription_emr else False),
            prescription_print_template=(
                int(prescription_print_template) if prescription_print_template else False
            ),
            calculator_emr=(int(calculator_emr) if calculator_emr else False),
            require_patient_guardian=(
                True if require_patient_guardian == "True" else False
            ),
            is_pause_button_show=(
                True if is_pause_button_show == "True" else False
            ),
            show_payment_method_line=(
                True if show_payment_method_line == "True" else False
            ),
            restrict_product_selection_in_registration=(
                True if restrict_product_selection_in_registration == "True" else False
            ),
            check_patient_name=(
                True if check_patient_name == "True" else False
            ),
            is_doctor_dashboard_revenue_show=(
                True if is_doctor_dashboard_revenue_show == "True" else False
            ),
            deposit_top_up_account_id=(
                int(deposit_top_up_account_id) if deposit_top_up_account_id else False
            ),
            deposit_return_account_id=(
                int(deposit_return_account_id) if deposit_return_account_id else False
            ),
            inkasso_account_id=(
                int(inkasso_account_id) if inkasso_account_id else False
            ),
            share_outstanding_payments=(
                True if share_outstanding_payments == "True" else False
            ),
            only_manager_can_delete_amb=(
                True if only_manager_can_delete_amb == "True" else False
            ),
            max_discount_for_referral=(
                float(max_discount_for_referral) if max_discount_for_referral else 0.0
            ),
            error_handle_bot_token=(
                "****************" if error_handle_bot_token else ''
            ),
            error_handle_group_id=(
                str(error_handle_group_id) if error_handle_group_id else ''
            ),
            error_handle_group_topic_id=(
                str(error_handle_group_topic_id) if error_handle_group_topic_id else ''
            ),
            can_merge_multitab_pdf=(
                True if can_merge_multitab_pdf == "True" else False
            ),
            include_unpaid_visits=(
                True if include_unpaid_visits == "True" else False
            ),
            can_access_unpaid_visits=(
                True if can_access_unpaid_visits == "True" else False
            ),
            require_diagnosis=(
                True if require_diagnosis == "True" else False
            ),
            allow_doctor_fee_greater_than_service=(
                True if allow_doctor_fee_greater_than_service == "True" else False
            ),
            allow_negative_transfer=(
                True if allow_negative_transfer == "True" else False
            ),
            disable_referral_fallback_to_main_visit=(
                True if disable_referral_fallback_to_main_visit == "True" else False
            ),
            patient_required_field_ids=[(6, 0, list(ids))],
            show_products_in_doctor_done_services=(
                True if show_products_in_doctor_done_services == "True" else False
            ),
            print_button_template_ids=[(6, 0, button_ids)],
            his_content_lang_id=(
                int(his_content_lang_id) if his_content_lang_id else False
            ),
            app_version=app_version,
        )

        return res

    @api.model
    def get_default_content_lang_code(self):
        """
        Get the default content language code.

        Returns:
            str: Language code like 'en_US', 'uz_UZ', 'ru_RU'
        """
        ICP = self.env['ir.config_parameter'].sudo()
        default_lang_id = ICP.get_param('his.his_content_lang_id')

        if default_lang_id:
            language = self.env['res.lang'].browse(int(default_lang_id))
            if language.exists() and language.active:
                return language.code

        return self.env.user.lang or 'en_US'

    def sanitize_telegram_html(self, text):
        """
        Sanitize text to remove unsupported HTML tags and keep only Telegram-supported tags.
        """
        # List of Telegram-supported HTML tags (without angle brackets)
        supported_tags = [
            'b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del',
            'code', 'pre', 'a', 'tg-spoiler', 'tg-emoji'
        ]


        text = escape(text)  # Convert <, >, & to HTML entities
        for tag in supported_tags:
            text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
            text = text.replace(f"&lt;{tag} ", f"<{tag} ")  # Handle tags with attributes like <a href>

        # Remove any remaining HTML tags (e.g., <anonymous>)
        text = re.sub(r'<(?!\/?(' + '|'.join(supported_tags) + r')(\s|>))[^>]+>', '', text)

        return text

    def send_telegram_message(self, bot_token, chat_id, text, error_handle_group_topic_id=None):
        """
        Send a message to a Telegram chat using the provided bot token.
        """
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        sanitized_text = self.sanitize_telegram_html(text)

        payload = {
            "chat_id": int(chat_id),
            "text": sanitized_text,
            "parse_mode": "HTML"
        }
        if error_handle_group_topic_id:
            payload["message_thread_id"] = int(error_handle_group_topic_id)

        try:
            response = requests.post(url, json=payload)  # Use json= for proper encoding
            response_data = response.json()

            if not response_data.get('ok'):
                # Fallback: Try sending without parse_mode. Drop the key entirely;
                # Telegram rejects parse_mode=null with "unsupported parse_mode".
                payload["text"] = re.sub(r'<[^>]+>', '', sanitized_text)  # Strip all HTML tags
                payload.pop("parse_mode", None)
                response = requests.post(url, json=payload)
                response_data = response.json()

            return response_data

        except Exception as e:
            # Fallback message
            fallback_payload = {
                "chat_id": int(chat_id),
                "text": "Error sending message. Please contact support.",
            }
            try:
                response = requests.post(url, json=fallback_payload)
                response_data = response.json()
                return response_data
            except Exception as fallback_e:
                return {"ok": False, "description": str(fallback_e)}

    def send_telegram_photo(self, bot_token, chat_id, file_bytes, filename, caption=None,
                            error_handle_group_topic_id=None):
        """
        Send a photo (jpeg screenshot) to a Telegram chat. Photos keep the
        caption, unlike webp documents which Telegram renders as captionless stickers.
        """
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        data = {"chat_id": int(chat_id)}
        if caption:
            data["caption"] = self.sanitize_telegram_html(caption)
            data["parse_mode"] = "HTML"
        if error_handle_group_topic_id:
            data["message_thread_id"] = int(error_handle_group_topic_id)

        files = {"photo": (filename, file_bytes, "image/jpeg")}
        response = requests.post(url, data=data, files=files, timeout=15)
        return response.json()

    @api.model
    def send_error_report(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("send_error_report: payload must be a dict")

        # helpers
        def clean(val):
            if val is None:
                return ""
            if val is False:
                return "False"
            return str(val)

        def block(title, content):
            if not content:
                return ""
            return f"<b>{title}</b><br>{content}<br><br>"

        message = clean(payload.get("message"))
        traceback = clean(payload.get("traceback"))
        client = payload.get("client") or {}
        odoo = payload.get("odoo") or {}

        # required config
        params = self.env["ir.config_parameter"].sudo()
        bot_token = params.get_param("his.error_handle_bot_token")
        group_id = params.get_param("his.error_handle_group_id")
        topic_id = params.get_param("his.error_handle_group_topic_id")

        if not bot_token or not group_id:
            raise ValueError("Telegram bot token or group id is not configured")

        # time
        user_tz = self.env.user.tz or "UTC"
        current_time = datetime.now(pytz.timezone(user_tz)).strftime("%d-%m-%Y %H:%M:%S")

        # sanitize
        safe_message = self.sanitize_telegram_html(message)
        safe_traceback = self.sanitize_telegram_html(traceback)

        # blocks
        header = f"""
            <blockquote>
            👤 {clean(self.env.user.name)}<br>
            🕐 {current_time}<br>
            🏥 {clean(self.env.user.company_id.name)}<br>
            🌐 {clean(client.get("platform"))} | {clean(client.get("language"))}<br>
            📱 Mobile: {clean(client.get("mobile"))}
            </blockquote>
        """

        url_block = block(
            "URL",
            f"<code>{clean(client.get('url'))}</code>" if client.get("url") else ""
        )

        odoo_ctx = []
        if odoo.get("actionName"):
            odoo_ctx.append(f"Action: {clean(odoo.get('actionName'))} ({clean(odoo.get('actionId'))})")
        if odoo.get("resModel"):
            odoo_ctx.append(f"Model: {clean(odoo.get('resModel'))}")
        if odoo.get("viewType"):
            odoo_ctx.append(f"View: {clean(odoo.get('viewType'))}")
        if odoo.get("resId"):
            odoo_ctx.append(f"Res ID: {clean(odoo.get('resId'))}")
        if odoo.get("context"):
            odoo_ctx.append(f"Context: {clean(odoo.get('context'))}")

        odoo_block = block(
            "Odoo Context",
            f"<code>{'<br>'.join(odoo_ctx)}</code>" if odoo_ctx else ""
        )

        error_block = block(
            "Error",
            f"<code>{safe_message}</code>" if safe_message else ""
        )

        traceback_block = block(
            "Traceback",
            f"<pre>{safe_traceback}</pre>" if safe_traceback else ""
        )

        full_message = (
                header
                + url_block
                + odoo_block
                + error_block
                + traceback_block
        )

        if not full_message.strip():
            raise ValueError("Empty error report")

        # Telegraph
        telegraph = Telegraph()
        telegraph.create_account(short_name="HIS")

        response = telegraph.create_page(
            title="Error Report from Aurora+",
            html_content=full_message
        )

        path = f"https://telegra.ph/{response['path']}"

        telegram_text = (
            "<b>Error Report from Aurora+</b>\n\n"
            f"👤 {self.env.user.name}\n"
            f"🕐 {current_time}\n"
            f"🏥 {self.env.user.company_id.name}\n\n"
            f"{path}"
        )

        # If a screenshot was captured, deliver it as a jpeg photo with the
        # report as caption. Any decode/send failure falls back to a text message.
        screenshot = payload.get("screenshot")
        if not isinstance(screenshot, dict):
            screenshot = {}
        screenshot_data = screenshot.get("data")
        if screenshot_data:
            try:
                file_bytes = base64.b64decode(screenshot_data)
            except Exception:
                file_bytes = None
            if file_bytes and len(file_bytes) <= 10 * 1024 * 1024:
                filename = screenshot.get("filename") or "error.jpg"
                try:
                    result = self.send_telegram_photo(
                        bot_token,
                        group_id,
                        file_bytes,
                        filename,
                        telegram_text,
                        topic_id,
                    )
                    if result.get("ok"):
                        return result
                except Exception:
                    pass

        return self.send_telegram_message(
            bot_token,
            group_id,
            telegram_text,
            topic_id,
        )


    def get_error_handle_group_data(self):
        """
        Get error handle group data from Telegram, including group name and topic name, in a nice format.
        """
        error_handle_bot_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_bot_token")
        )

        url = f"https://api.telegram.org/bot{error_handle_bot_token}/getUpdates"
        params = {"timeout": 100}
        response = requests.get(url, params=params)
        updates = response.json()

        group_data = ""
        for result in updates.get("result", []):
            message = result.get("message")
            if message:
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                chat_title = chat.get("title", "Unknown Group Name")
                thread_id = message.get("message_thread_id")
                text = message.get("text", "")

                group_data += "=" * 40 + "\n"
                group_data += f"Group Name : {chat_title}\n"
                group_data += f"Group ID   : {chat_id}\n"
                if thread_id:
                    group_data += f"Thread ID  : {thread_id}\n"
                group_data += f"Message    : {text}\n"
                group_data += "=" * 40 + "\n"

        raise UserError(group_data)

    def send_error_to_telegram_group(self):
        error_handle_bot_token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_bot_token")
        )
        error_handle_group_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_group_id")
        )
        error_handle_group_topic_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("his.error_handle_group_topic_id")
        )

        max_length = 4096
        title = "Error Report from Aurora+"
        message = "Test message for error handling Aurora+. This message is intentionally long to test the chunking functionality of the Telegram bot integration. "

        user_tz = self.env.user.tz or 'UTC'
        current_time = datetime.now(pytz.timezone(user_tz)).strftime("%d-%m-%Y %H:%M:%S")
        full_message = f"<blockquote>👤 {self.env.user.name}<br>🕐 {current_time}<br>🏥 {self.env.user.company_id.name}</blockquote><br><code>{self.sanitize_telegram_html(message)}</code>"
        telegraph = Telegraph()
        telegraph.create_account(short_name='HIS')
        # if need new token
        # new_account = telegraph.create_account(short_name='HIS')
        # print(response['access_token'])  # token
        response = telegraph.create_page(
            title=f"{self.sanitize_telegram_html(title)}",
            html_content=full_message
        )
        path = f"https://telegra.ph/{response['path']}"
        chunk = f'<b>{self.sanitize_telegram_html(title)}</b>\n\n👤 {self.env.user.name}\n🕐 {current_time}\n🏥 {self.env.user.company_id.name}\n\n{path}'

        telegram_response = self.send_telegram_message(error_handle_bot_token, error_handle_group_id, chunk, error_handle_group_topic_id)
