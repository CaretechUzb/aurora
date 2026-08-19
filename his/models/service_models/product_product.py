import base64
import json

from ...utils.selections import categ_selection
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"
    _order = "sequence, name"

    # product_type = fields.Many2one("his.category_base", string="Product Type ")
    # short_name = fields.Char(string='Short Name', unique=True)
    product_type_selection = fields.Selection(
        string="Category Base Selection ",
        related="product_type.category_selection",
        store=True,
    )
    medical_classification_type = fields.Selection(
        [
            ("normal", "Normal"),
            ("psychotropic", "Psychotropic"),
            ("narcotic", "Narcotic"),
            ("antimicrobial", "Antimicrobial"),
            ("limited_antimicrobial", "Limited Antimicrobial"),
            ("tpn", "Limited Antimicrobial"),
            ("contrast_medium", "Contrast Medium"),
            ("raw_materials_medicine", "Raw Materials Medicine"),
            ("anticancer_medicine", "Anticancer Medium"),
            ("sap", "Sap"),
        ],
        "Medical Classification type",
    )
    categ_is_his = fields.Boolean(
        string="Is HIS", related="categ_id.is_his", store=True
    )
    tx_meds = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Tx Meds",
    )
    doctor_branch_price_conf = fields.One2many(
        "his.product.branch.conf", "service_id", string="Doctor Branch Price Conf"
    )
    drug_dosage_ids = fields.One2many(
        "his.drug_dosage", "product_id", string="Drug Dosages"
    )

    age = fields.Selection(
        [("all", "All"), ("child", "Child"), ("adult", "Adult")],
        "Age",
        default="all",
        required=True,
    )
    rx_out_host = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Rx Out Hosp",
    )
    instruction = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Instruction Option",
    )
    set_test = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        "Set Test Option",
    )
    from_date = fields.Date()
    to_date = fields.Date()

    calculation_type = fields.Selection(
        [
            ("pack", "Pack"),
            ("one_time", "One Time"),
        ],
        string="Calculation Type",
        tracking=True,
    )
    room_id = fields.Many2one("his.room", string="Room", tracking=True)
    quantity_in_pack = fields.Float(string="Quantity in Pack", tracking=True)
    pack_type_id = fields.Many2one("his.unit_pack_type", string="Pack Type")
    basic_type_id = fields.Many2one("his.unit_pack_type", string="Basic Type")
    basic_price = fields.Integer(
        string="Basic Price", help="Price for one unit", tracking=True
    )
    no_resident_price = fields.Float(
        string="No Resident Price(in %)",
        help="No resident price percentage for one unit",
        tracking=True,
    )

    @api.constrains("no_resident_price")
    def _validate_no_resident_price(self):
        for record in self:
            if record.no_resident_price < 0:
                raise exceptions.ValidationError(_("No resident price percentage should be greater than 0"))
            elif record.no_resident_price > 100:
                raise exceptions.ValidationError(_("No resident price percentage should be less than 100"))

    is_rx_possible = fields.Selection(
        [("yes", "Yes"), ("no", "No")], "Is Rx Possible", tracking=True
    )
    calc_ext_use_drug = fields.Selection(
        [("yes", "Yes"), ("no", "No")], "Calculation Ext Use Drug", tracking=True
    )
    price_type = fields.Selection(
        [
            ("single", "Single"),
            ("group", "Group"),
        ],
        "Price Type",
        tracking=True,
    )
    category_service_type = fields.Char(string="Service Type")
    # categ_id = fields.Many2one("product.category", string="Category", tracking=True)
    medical_classification_id = fields.Many2one(
        "his.medicine_classification", string="Med Classification"
    )
    med_direction_core = fields.Char(
        string="Med Direction Core",
        related="medical_classification_id.abbreviation",
        store=True,
    )
    product_properties = fields.Properties(
        "Properties", definition="product_type.product_definition"
    )

    basic_dosage = fields.Char(string="Basic Dosage")
    default_no = fields.Char(string="Default No")
    daily_max_amt = fields.Integer(string="Daily Max Amt")
    content = fields.Integer(string="Content")
    amt_unit = fields.Many2one("uom.uom", "Dosage Unit")

    priority_color = fields.Char(string="Priority Color")
    base_service_duration = fields.Integer(
        string="Base Service Duration(in minutes)", required=True, default=30
    )
    second_visit_duration = fields.Integer(
        string="Second Visit Duration(in days)", required=True, default=1
    )
    follow_up_duration = fields.Integer(
        string="Follow Up Duration(in days)", required=True, default=1
    )
    base_share_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Share Type",
        default="percent",
        required=True,
        tracking=True,
    )
    base_share_value = fields.Float(
        string="Share Value", required=True, default=0, tracking=True
    )
    # base_recommendation_bonus_type = fields.Selection([
    #     ('percent', 'Percentage'),
    #     ('fixed', 'Fixed Amount'),
    # ],
    #     string='Recommendation Bonus Type',
    #     default='percent')
    # base_recommendation_bonus_value = fields.Float(string='Recommendation Bonus Value')
    service_requirements = fields.Html(string="Service Requirements", translate=True, sanitize=False)
    information_tooltip = fields.Char(
        string="Info ", compute="_compute_prerequirements_info", store=False
    )
    doctor_prices_range = fields.Char(
        string="Doctor Prices Range", compute="_compute_doctor_prices_range"
    )
    is_schedulable = fields.Boolean(
        "Is Schdedulable", tracking=True
    )

    schedule_type = fields.Selection(
        [
            ("default", "Default"),
            ("in_queue", "In Queue"),
        ],
        default="default",
        tracking=True,
        company_dependent=True,
    )
    default_department_id = fields.Many2one(
        "hr.department", string="Default Department"
    )
    has_virtual_doctor_id = fields.Boolean(
        string="Has Virtual Doctor",
        compute="_compute_has_virtual_doctor_id",
        store=True,
    )
    product_code = fields.Char(string="Product Code")
    doctors_first_visit_prices = fields.Char(
        compute="_compute_doctors_visit_prices",
        help="First visit prices of doctor (min - max range)",
    )
    doctors_re_visit_prices = fields.Char(
        compute="_compute_doctors_visit_prices",
        help="Re visit prices of doctor (min - max range)",
    )
    tooltip_info_html = fields.Html(
        string="Info", compute="_compute_tooltip_info_html", translate=True
    )
    GTIN = fields.Char(string="gtin", tracking=True)
    gtin_id = fields.Many2one("his.gtin_products", string="GTIN", tracking=True)
    snomed_id = fields.Many2one(
        "his.snomed",
        string="SNOMED CT Code",
        tracking=True,
        help="SNOMED CT code for this product/medicine (used in DHP FHIR sync)",
    )
    product_nnm_ids = fields.Many2many("product.nnm", "product_nnm_product_product_rel")
    product_nnm_str = fields.Char(
        string="Product NNM",
        compute="_compute_product_nnm_str",
    )
    is_cito = fields.Boolean(tracking=True)
    can_online_appointment = fields.Boolean(
        string="Can Online Appointment", tracking=True
    )
    can_receive_call_back = fields.Boolean(tracking=True)
    sorting_to_website = fields.Integer("Ordering")
    sorting_in_category = fields.Integer("Ordering In Category")

    package_code = fields.Char("MXIK Package Code")
    class_code = fields.Char("MXIK Class Code")

    available_in_registration = fields.Boolean(
        string="Available in Registration",
        tracking=True,
        default=True,
    )
    subtract_from_share_bonus = fields.Boolean(
        string="Subtract from share bonus",
        help="When enabled, the price of pack components will be subtracted from doctor share and referral bonus calculations",
        tracking=True,
    )
    subtract_from_referral_bonus = fields.Boolean(
        string="Subtract from referral bonus",
        help="When enabled, the price of pack components will be subtracted from doctor share and referral bonus calculations",
        tracking=True,
    )
    sync_with_doctor_fee = fields.Boolean(
        string="Sync with doctor fee",
        default=False,
        tracking=True,
        help="Tick this before changing the base service price to also update "
        "the prices of every doctor fee for this service. It is a one-shot "
        "switch: once the price is saved the sync runs and this box is "
        "automatically unticked again.",
    )

    def write(self, vals):
        res = super().write(vals)
        if "is_schedulable" in vals and not vals["is_schedulable"]:
            for record in self:
                if self.env["his.doctor_fee"].sudo().search([("service_id", "=", record.id)]):
                    raise ValidationError(
                        _("This product has doctor fees associated with it. Please make is_schedulable True or remove the doctor fees before making it unschedulable.")
                    )
        # When the service base price changes, propagate it to the prices of
        # every doctor fee for this service. Skipped during pricelist sync,
        # which writes lst_price (and the doctor fees) itself.
        if {"lst_price", "list_price"} & set(vals) and not self.env.context.get(
            "pricelist_sync_bypass"
        ):
            to_sync = self.filtered("sync_with_doctor_fee")
            if to_sync:
                # One query for every synced service, then split per product in
                # memory (avoids an N+1 search when several are written at once).
                fees = self.env["his.doctor_fee"].sudo().search(
                    [("service_id", "in", to_sync.ids)]
                )
                for product in to_sync:
                    product_fees = fees.filtered(lambda f: f.service_id.id == product.id)
                    if product_fees:
                        product_fees._apply_service_base_price(product.lst_price)
        return res

    def action_archive(self):
        res = super().action_archive()
        for product in self:
            doctor_fees = self.env['his.doctor_fee'].search([
                ('service_id', '=', product.id)
            ])
            if doctor_fees:
                doctor_fees.write({'active': False})
        return res

    @api.constrains("quantity_in_pack")
    def _validate_quantity_in_pack(self):
        for record in self:
            if (
                record.calculation_type in ["pack", "one_time"]
                and record.quantity_in_pack <= 0
            ):
                raise exceptions.ValidationError(_("Quantity in pack should be greater than 0"))

    @api.constrains("amt_unit")
    def _validate_calculation_type(self):
        for record in self:
            if record.calculation_type in ["pack", "one_time"] and not record.amt_unit:
                raise exceptions.ValidationError(_("Dosage unit is required for pack and calculation type"))

    @api.depends("service_requirements", "doctor_branch_price_conf.service_doctors")
    def _compute_tooltip_info_html(self):
        for record in self:
            if type(record.id) != int:
                id = int(str(record.id).split("_")[1])
            else:
                id = record.id
            doctor_fees = self.env["his.doctor_fee"]
            doctors = doctor_fees.search(
                [
                    ("company_id", "=", self.env.user.company_id.id),
                    ("service_id", "=", id),
                ]
            )

            if len(doctors.ids) > 0:
                doctor_info = "<ul>"
                for doctor in doctors:
                    first_visit_price = f"{doctor.first_visit_price:,.2f}"
                    revisit_price = f"{doctor.revisit_price:,.2f}"
                    doctor_info += f"<li style='font-size: 12px'>{doctor.doctor_id.name}: {first_visit_price}/{revisit_price}</li>"
                doctor_info += "</ul>"

                button_struct = {
                    "html": f"{record.service_requirements if record.service_requirements else ''}{doctor_info}",
                }

                record.tooltip_info_html = button_struct["html"]
            elif record.service_requirements:
                button_struct = {
                    "html": record.service_requirements,
                }
                record.tooltip_info_html = button_struct["html"]
            else:
                record.tooltip_info_html = False

    def custom_format(self, n):
        s = "{:,.2f}".format(n).replace(",", " ")
        return s

    @api.depends("doctor_branch_price_conf.service_doctors")
    def _compute_doctors_visit_prices(self):
        for record in self:
            first_visit_price = record.doctor_branch_price_conf.service_doctors.mapped(
                "first_visit_price"
            )
            re_visit_price = record.doctor_branch_price_conf.service_doctors.mapped(
                "revisit_price"
            )

            if first_visit_price:
                min_price = min(first_visit_price)
                max_price = max(first_visit_price)
                min_price_formatted = self.custom_format(min_price)
                max_price_formatted = self.custom_format(max_price)
                record.doctors_first_visit_prices = (
                    f"{min_price_formatted} - {max_price_formatted}"
                    if min_price != max_price
                    else min_price_formatted
                )
            else:
                record.doctors_first_visit_prices = self.custom_format(
                    record.list_price
                )

            if re_visit_price:
                min_price = min(re_visit_price)
                max_price = max(re_visit_price)
                min_price_formatted = self.custom_format(min_price)
                max_price_formatted = self.custom_format(max_price)
                record.doctors_re_visit_prices = (
                    f"{min_price_formatted} - {max_price_formatted}"
                    if min_price != max_price
                    else min_price_formatted
                )
            else:
                record.doctors_re_visit_prices = self.custom_format(record.list_price)

    @api.depends("doctor_branch_price_conf.service_doctors")
    def _compute_has_virtual_doctor_id(self):
        for record in self:
            virtual_doctor_id = self.env["his.doctor_fee"].search(
                [
                    ("service_id", "=", record.id),
                    ("doctor_id.is_virtual", "=", True),
                ]
            )
            if len(virtual_doctor_id) > 0:
                record.has_virtual_doctor_id = True
            else:
                record.has_virtual_doctor_id = False

    @api.depends("product_nnm_ids")
    def _compute_product_nnm_str(self):
        for record in self:
            record.product_nnm_str = ", ".join(record.product_nnm_ids.mapped("name"))

    def _compute_doctor_prices_range(self):
        for record in self:
            doctor_prices = record.doctor_branch_price_conf.service_doctors.mapped(
                "first_visit_price"
            )
            if doctor_prices:
                record.doctor_prices_range = (
                    f"{min(doctor_prices)} - {max(doctor_prices)}"
                    if min(doctor_prices) != max(doctor_prices)
                    else min(doctor_prices)
                )
            else:
                record.doctor_prices_range = record.list_price

    def get_doctors_and_prices(self):
        price_list = []
        counter = 0
        for doctor in self.doctor_branch_price_conf.service_doctors:
            counter += 1
            doctor_name = doctor.doctor_id.name or "Unknown"
            first_visit_price = doctor.first_visit_price or 0.0
            revisit_price = doctor.revisit_price or 0.0
            price_list.append(
                f"{counter}. {doctor_name} - {first_visit_price} - {revisit_price}<br>"
            )
        return price_list

    @api.depends("service_requirements", "doctor_branch_price_conf.service_doctors")
    def _compute_prerequirements_info(self):
        for record in self:
            if type(record.id) != int:
                id = int(str(record.id).split("_")[1])
            else:
                id = record.id
            doctor_fees = self.env["his.doctor_fee"]
            doctors = doctor_fees.search(
                [
                    ("company_id", "=", self.env.user.company_id.id),
                    ("service_id", "=", id),
                ]
            )
            if len(doctors.ids) > 0:
                doctor_info = "<ul>"
                for doctor in doctors:
                    first_visit_price = f"{doctor.first_visit_price:,.2f}"
                    revisit_price = f"{doctor.revisit_price:,.2f}"
                    doctor_info += f"<li>{doctor.doctor_id.name}: {first_visit_price}/{revisit_price}</li>"
                doctor_info += "</ul>"

                button_struct = {
                    "title": record.name,
                    "html": f"{record.service_requirements if record.service_requirements else ''}{doctor_info}",
                }

                record.information_tooltip = json.dumps(button_struct)
            elif record.service_requirements:
                button_struct = {
                    "title": record.name,
                    "html": record.service_requirements,
                }
                record.information_tooltip = json.dumps(button_struct)
            else:
                record.information_tooltip = False
            print(record.information_tooltip, "tttttttttt")

    def action_configure_branches(self):
        return {
            "name": self.name + _(" Branch Configuration"),
            "type": "ir.actions.act_window",
            "res_model": "his.product.branch.conf",
            "view_mode": "tree,form",
            "domain": [("service_id", "=", self.id)],
            "target": "current",
        }

    # @api.depends('categ_id')
    # def setup_base_category_in_depend(self):
    #     for record in self:
    #         if len(record.categ_id) == 1:
    #             record.product_type_selection = record.categ_id.product_type.category_selection

    # @api.onchange('base_recommendation_bonus_value')
    # def base_recommendation_bonus_value_validate(self):
    #     self.ensure_one()
    #     if self.base_recommendation_bonus_type == 'percent' and self.base_recommendation_bonus_value > 100:
    #         self.base_recommendation_bonus_value = 100

    # @api.onchange('is_cito')
    # def onchange_is_cito(self):
    #     if self.is_cito:
    #         if self.name:
    #             self.name = f"(CITO) {self.name}"
    #         else:
    #             self.name = "(CITO)"
    #     elif not self.is_cito and self.name and "(CITO)" in self.name:
    #         if self.name == '(CITO)':
    #             self.name = self.name.replace("(CITO)", "")
    #         else:
    #             self.name = self.name.replace("(CITO) ", "")
    @api.onchange("base_share_type")
    def base_share_type_validate(self):
        self.ensure_one()
        self.base_share_value = 0

    @api.onchange("base_share_value")
    def base_share_value_validate(self):
        self.ensure_one()
        if self.base_share_type == "percent" and self.base_share_value > 100:
            raise UserError(
                _("Share value cannot be greater than 100% for percentage type.")
            )

    @api.onchange("product_type")
    def onchange_base_category_id(self):
        self.ensure_one()
        if len(self.product_type) == 1 and len(self.categ_id) == 0:
            self.base_share_type = self.product_type.share_type
            self.base_share_value = self.product_type.share_value
            # self.base_recommendation_bonus_type = self.product_type.recommendation_bonus_type
            # self.base_recommendation_bonus_value = self.product_type.recommendation_bonus_value
            self.is_schedulable = self.product_type.is_schedulable
            self.schedule_type = self.product_type.schedule_type

    @api.onchange("categ_id")
    def setup_base_category(self):
        self.ensure_one()
        if len(self.categ_id) == 1:
            self.base_share_type = self.categ_id.share_type
            self.base_share_value = self.categ_id.share_value
            # self.base_recommendation_bonus_type = self.categ_id.recommendation_bonus_type
            # self.base_recommendation_bonus_value = self.categ_id.recommendation_bonus_value
            self.is_schedulable = self.categ_id.is_schedulable
            self.schedule_type = self.categ_id.schedule_type
        elif len(self.product_type) == 1 and len(self.categ_id) == 0:
            self.base_share_type = self.product_type.share_type
            self.base_share_value = self.product_type.share_value
            # self.base_recommendation_bonus_type = self.product_type.recommendation_bonus_type
            # self.base_recommendation_bonus_value = self.product_type.recommendation_bonus_value
            self.is_schedulable = self.product_type.is_schedulable
            self.schedule_type = self.product_type.schedule_type

    @api.onchange("is_schedulable")
    def onchange_is_schedulable(self):
        if not self.is_schedulable:
            self.can_online_appointment = False

    @api.onchange("base_service_duration")
    def base_service_duration_validate(self):
        self.ensure_one()
        if self.base_service_duration < 0:
            raise UserError(_("Base service duration cannot be negative"))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("Prescription Management Search"),
            "res_model": "his.pres_management_search",
            "views": [[self.env.ref("his.pres_management_search_view").id, "form"]],
            "context": context,
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_product_proxy_product"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["id"] = False
        action["xml_id"] = False
        action["context"] = {
            "search_default_filter_child": 1,
            "use_custom_search": "1",
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
        }
        action["target"] = "main"
        return action

    def action_export_pdf(self):
        IrConfig = self.env["ir.config_parameter"].sudo()
        page_list = []

        rendered_html = self.env["ir.ui.view"]._render_template(
            "his.report_prescription_management",
            values={
                "docs": self,  # The context needs to match what the template expects
                "base_url": IrConfig.get_param("report.url"),
            },
        )
        page_list.append(rendered_html)

        report = self.env.ref("his.action_prescription_management_report_form")
        pdf_content = self.env["ir.actions.report"]._run_wkhtmltopdf(
            page_list, report_ref=report
        )

        encoded_pdf = base64.b64encode(pdf_content).decode("utf-8")
        pdf_preview = (
            self.env["his.prescription_management_pdf_preview"]
            .with_context()
            .create({"pdf_file": encoded_pdf})
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Prescription Management Report"),
            "res_model": "his.prescription_management_pdf_preview",
            "res_id": pdf_preview.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "bin_size": False,
                "create": False,
                "edit": False,
            },
        }

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         # name = f"{record.name} - {record.list_price}"
    #         # first_visit_price = record.doctor_branch_price_conf.service_doctors.mapped('first_visit_price')
    #         # if first_visit_price:
    #         #     min_price = str(min(first_visit_price))
    #         #     max_price = str(max(first_visit_price))
    #         #     name = f"{record.name} - {min_price} - {max_price}" if min_price != max_price else f"{record.name} - {min_price}"
    #         result.append((record.id, record.name))
    #     return result
