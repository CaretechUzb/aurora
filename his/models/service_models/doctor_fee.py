import json
from odoo import exceptions, fields, models, api, _
from odoo.addons.his.utils.selections import categ_selection
from datetime import timedelta, datetime


class DoctorFeePriceLine(models.Model):
    _name = "his.doctor_fee.price.line"
    _description = "Doctor Fee Price Line"
    _order = "start_date desc, create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    doctor_fee_id = fields.Many2one(
        "his.doctor_fee",
        string="Doctor Fee",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    start_date = fields.Date(string="Start Date", required=True, tracking=True)
    first_visit_price = fields.Float(
        string="First Visit Price", required=True, tracking=True
    )
    revisit_price = fields.Float(string="Revisit Price", required=True, tracking=True)
    follow_up_price = fields.Float(
        string="Follow Up Price", required=False, tracking=True
    )
    active = fields.Boolean(default=True, required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        store=True,
        compute="_compute_company_id",
    )
    service_id = fields.Many2one(
        "product.product",
        string="Service",
        related="doctor_fee_id.service_id",
        store=True,
    )
    sync_with_doctor_fee = fields.Boolean(
        related="doctor_fee_id.service_id.sync_with_doctor_fee",
        string="Synced with base price",
    )
    product_type_id = fields.Many2one(
        "his.category_base",
        string="Product Type",
        related="doctor_fee_id.service_id.product_type",
        store=True,
    )
    doctor_id = fields.Many2one(
        "hr.employee",
        string="Doctor",
        related="doctor_fee_id.doctor_id",
        store=True,
    )

    @api.depends("doctor_fee_id")
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = rec.doctor_fee_id.company_id

    @api.constrains("start_date")
    def _check_date(self):
        for rec in self:
            if rec.start_date:
                today = fields.Date.today()
                if rec.start_date < today:
                    raise exceptions.ValidationError(
                        _("You cannot add or modify prices for past dates!")
                    )


class DoctorFee(models.Model):
    _name = "his.doctor_fee"
    _description = "Doctor Fee"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    branch_conf_id = fields.Many2one(
        "his.product.branch.conf", string="Branch Configuration"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="branch_conf_id.company_id",
        store=True,
        readonly=False,
        tracking=True,
    )

    doctor_id = fields.Many2one(
        "hr.employee",
        string="Doctor",
        domain=[("job_id.can_earn_share", "=", True)],
        required=True,
        check_company=True,
        tracking=True,
    )
    work_expreience = fields.Integer(
        string="Work Experience", related="doctor_id.work_experience"
    )

    filial_names = fields.Char(
        compute="_compute_filial_names",
        readonly=True,
    )

    job_id = fields.Many2one(
        "hr.job",
        string="Job Position",
        related="doctor_id.job_id",
    )

    doctor_schedule_type = fields.Selection(
        [
            ("default", "Default"),
            ("in_queue", "In Queue"),
        ],
        string="Doctor Schedule Type",
        compute="_compute_doctor_schedule_type",
    )
    doctor_information_tooltip = fields.Char(
        string="Doctor Info",
        compute="_compute_doctor_information_tooltip",
    )
    product_type = fields.Many2one("his.category_base", string="Product Type ")
    product_type_selection = fields.Selection(
        related="service_id.product_type.category_selection"
    )
    categ_id = fields.Many2one("product.category", string="Category ")
    service_id = fields.Many2one(
        "product.product", string="Service", required=True, tracking=True
    )
    first_visit_price = fields.Float(
        string="First Visit Price", compute="_compute_prices", store=True
    )
    revisit_price = fields.Float(
        string="Revisit Price", compute="_compute_prices", store=True
    )
    follow_up_price = fields.Float(
        string="Follow Up Price",
        compute="_compute_prices",
        store=True,
        help="Price for follow-up visits, if applicable",
    )
    first_visit_duration = fields.Float(
        string="First Visit Duration (in days)",
    )
    revisit_duration = fields.Float(
        string="Revisit Duration (in days)",
    )
    related_revisit = fields.Selection(
        [
            ("last_of_the_first_visit", "Last of the first visit"),
            ("last_visit", "Last visit"),
        ],
        string="Related Revisit",
        default="last_of_the_first_visit",
        help="Define how the revisit is related to the first visit",
    )
    follow_up_duration = fields.Float(
        string="Follow Up Duration (in days)",
        help="Duration for follow-up visits, if applicable (in days)",
    )
    performance_percentage = fields.Float(string="Performance Percentage")
    per_dividend_refer = fields.Float(string="Performance Dividend Refer")
    is_authority = fields.Boolean(string="Is Authority")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    service_duration = fields.Integer(
        string="Service Duration(in minutes)", tracking=True
    )
    revisit_service_duration = fields.Integer(
        string="Revisit Service Duration (in minutes)", tracking=True
    )
    follow_up_service_duration = fields.Integer(
        string="Follow Up Service Duration (in minutes)", tracking=True
    )
    room = fields.Many2one(
        "his.room", string="Room", required=True, tracking=True, check_company=True
    )
    share_type = fields.Selection(
        [
            ("percent", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("formula", "Formula"),
        ],
        string="Share Type",
        default="percent",
        tracking=True,
    )
    share_value = fields.Float(string="Share Value", tracking=True)
    formula = fields.Char(string="Formula", help="Python formula to calculate share amount. Available variables: price_subtotal, discount_total, price_total, quantity, price_tax, price, actual_price, doctor_price", tracking=True)
    # recommendation_bonus_type = fields.Selection(
    #     [
    #         ("percent", "Percentage"),
    #         ("fixed", "Fixed Amount"),
    #     ],
    #     string="Recomendation Bonus Type",
    #     default="percent",
    # )
    # recommendation_bonus_value = fields.Float(string="Recomendation Bonus Value")
    calculation_type = fields.Selection(
        [
            ("actual_price", _("Actual Price")),
            ("dicounted_price", _("Subtotal price (discounted)")),
            ("dicounted_total_price", _("Total Price (discounted)")),
            ("doctor_price", _("Doctor Price")),
        ],
        string="Calculation Type",
        default="dicounted_price",
        tracking=True,
        help="""
        - Actual Price: The doctor's share is calculated based on the actual price (before discount, after tax) of the service.
        - Subtotal Price (discounted): The doctor's share is calculated based on the subtotal price (after discount, before tax) of the service.
        - Total Price (discounted): The doctor's share is calculated based on the total price (after discount, after tax) of the service.
        - Doctor Price: The doctor's share is calculated based on order_detail.doctor_price (the negotiated per-unit price).
        """
    )
    age = fields.Selection(
        [("all", "All"), ("child", "Child"), ("adult", "Adult")],
        "Age",
        default="all",
        required=True,
    )
    can_online_appointment = fields.Boolean(string="Can Online Appointment")
    require_prepayment = fields.Boolean(
        string="Require Prepayment",
        tracking=True,
        help="Service cannot be completed until paid; aggregators must "
        "collect payment before booking.",
    )

    price_line_ids = fields.One2many(
        "his.doctor_fee.price.line", "doctor_fee_id", string="Scheduled Prices"
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)
    mobile_phone = fields.Char("Mobile Phone", related="doctor_id.mobile_phone")
    service_tooltip = fields.Char(
        string="Service Tooltip",
        compute="_compute_service_tooltip",
    )

    @api.depends("service_id")
    def _compute_service_tooltip(self):
        for rec in self:
            if rec.service_id:
                text = (
                    rec.service_id.service_requirements
                    if rec.service_id.service_requirements
                    else ""
                )
                rec.service_tooltip = json.dumps(
                    {
                        "title": "Service Information",
                        "html": f"{text}",
                    }
                )
            else:
                rec.service_tooltip = ""

    def parse_time(self, time_float):
        hours = int(time_float)
        minutes = int(round((time_float - hours) * 100))
        return "%02d:%02d" % (hours, minutes)

    @api.depends("company_id", "doctor_id")
    def _compute_doctor_information_tooltip(self):
        for record in self:
            today = fields.Date.today()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

            doctor_schedule_ids = self.env["his.doctor_schedule"].search(
                [
                    ("doctor_id", "=", record.doctor_id.id),
                    ("date", ">=", today),
                    ("date", "<=", end_date),
                    ("company_id", "=", record.company_id.id),
                ]
            )
            if not doctor_schedule_ids:
                record.doctor_information_tooltip = json.dumps(
                    {"title": "Working Period", "html": "No working period found"}
                )
                continue

            working_periods = self.env["his.doctor_working_periods"].search(
                [
                    ("doctor_schedule_id", "in", doctor_schedule_ids.ids),
                    ("start_time", "!=", False),
                    ("end_time", "!=", False),
                ]
            )

            if not working_periods:
                record.doctor_information_tooltip = json.dumps(
                    {"title": "Working Period", "html": "No working period found"}
                )
                continue
            academic_rank = (
                record.doctor_id.academic_rank + "<br/><br/>"
                if record.doctor_id.academic_rank
                else ""
            )
            work_experience = (
                str(record.doctor_id.work_experience) + "<br/><br/>"
                if record.doctor_id.work_experience
                else ""
            )
            doctor_mobile_phone = (
                _("Phone number") + f" - {record.doctor_id.mobile_phone}<br/><br/>"
                if record.doctor_id.mobile_phone
                else ""
            )
            doctor_resume = ""
            counter = 1
            for resume in record.doctor_id.resume_line_ids:
                if counter == 1:
                    doctor_resume += (
                        _("Resume")
                        + "<br/>"
                        + f"<b>1.{resume.name}</b>:<br/> {resume.description + '<br/>' if resume.description else ''}{resume.date_start} - {resume.date_end if resume.date_end else _('Current')}<br/><br/>"
                    )
                doctor_resume += f"<b>{counter}.{resume.name}</b>:<br/> {resume.description + '<br/>' if resume.description else ''}{resume.date_start} - {resume.date_end if resume.date_end else _('Current')}<br/><br/>"
                counter += 1
            doctor_information_tooltip = {
                "title": "Working Period",
                "html": f"{academic_rank}{work_experience}{doctor_mobile_phone}{doctor_resume}<table class='table table-bordered table-sm'><thead><tr><th>Date</th><th>Start Time</th><th>End Time</th></tr></thead><tbody>",
            }

            for period in working_periods:
                start_time = self.parse_time(period.start_time)
                end_time = self.parse_time(period.end_time)
                doctor_schedule_date = str(period.doctor_schedule_id.date)
                doctor_information_tooltip[
                    "html"
                ] += f"<tr><td>{doctor_schedule_date}</td><td>{start_time}</td><td>{end_time}</td></tr>"

            doctor_information_tooltip["html"] += "</tbody></table>"
            record.doctor_information_tooltip = json.dumps(doctor_information_tooltip)

    def _compute_doctor_schedule_type(self):
        for rec in self:
            if rec.service_id.exists() and rec.service_id.is_schedulable:
                rec.doctor_schedule_type = rec.service_id.schedule_type
            else:
                rec.doctor_schedule_type = False

    @api.onchange("share_value")
    def onchange_share_value(self):
        Param = self.env['ir.config_parameter'].sudo()
        allow_greater = Param.get_param(
            'his.allow_doctor_fee_greater_than_service'
        )

        if allow_greater == 'True':
            return

        if self.share_type == "percent" and self.share_value > 100:
            raise exceptions.ValidationError(_("Percentage should be less than 100"))
        elif (
            self.share_type == "fixed" and self.service_id.lst_price < self.share_value
        ):
            raise exceptions.ValidationError(_("Fixed amount should be less than the service price"))

    @api.constrains("start_date", "end_date")
    def _check_date(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise exceptions.ValidationError(
                    _("End Date should be greater than Start Date")
                )

    @api.constrains("price_line_ids")
    def _check_price_lines(self):
        for rec in self:
            active_price_lines = rec.price_line_ids.filtered(lambda l: l.active)
            if not active_price_lines:
                raise exceptions.ValidationError(
                    _("You must set at least one active price line for the doctor fee!")
                )

    @api.constrains("service_id", "company_id", "doctor_id", "active")
    def _check_doctor_service_unique(self):
        for record in self:
            if record.active:
                domain = [
                    ("id", "!=", record.id),
                    ("service_id", "=", record.service_id.id),
                    ("company_id", "=", record.company_id.id),
                    ("doctor_id", "=", record.doctor_id.id),
                    ("active", "=", True),
                ]
                if self.search_count(domain) > 0:
                    raise exceptions.ValidationError(
                        _("Doctor Fee must be unique for Doctor and Service!")
                    )

    def name_get(self):
        result = []
        for record in self:
            # name = f"{record.doctor_id.name} - {record.service_id.name}" # old
            name = f"{record.doctor_id.name} - {record.first_visit_price} / {record.revisit_price}"
            result.append((record.id, name))
        return result

    def action_create_doctor_fee(self):
        view_id = self.env.ref("his.view_bulk_doctor_fee_wizard_form").id
        return {
            "name": "Product Prices",
            "type": "ir.actions.act_window",
            "res_model": "his.bulk_doctor_fee_wizard",
            "views": [[view_id, "form"]],
            "view_mode": "form",
            "target": "current",
            "context": {"bin_size": False},
        }

    def load(self, fields, data):
        if "branch_conf_id" not in fields:
            fields.append("branch_conf_id/.id")
            for row in data:
                company_index = fields.index("company_id")
                service_index = fields.index("service_id")
                company_name = row[company_index]
                service_name = row[service_index]
                companys = self.env["res.company"].name_search(
                    company_name, operator="="
                )
                if not companys:
                    raise exceptions.ValidationError(
                        _("Company %s not found") % company_name
                    )
                if len(companys) > 1:
                    raise exceptions.ValidationError(
                        _("Multiple companies found for %s") % company_name
                    )
                services = self.env["product.product"].name_search(
                    service_name, operator="="
                )
                if not services:
                    raise exceptions.ValidationError(
                        _("Service %s not found") % service_name
                    )
                if len(services) > 1:
                    raise exceptions.ValidationError(
                        _("Multiple services found for %s") % service_name
                    )
                company_id = companys[0][0]
                service_id = services[0][0]
                branch_conf_id = (
                    self.env["his.product.branch.conf"]
                    .sudo()
                    .search(
                        [
                            ("company_id", "=", company_id),
                            ("service_id", "=", service_id),
                        ],
                        limit=1,
                    )
                )
                if not branch_conf_id:
                    branch_conf_id = self.env["his.product.branch.conf"].create(
                        {"company_id": company_id, "service_id": service_id}
                    )
                row.append(str(branch_conf_id.id))
        return super(DoctorFee, self).load(fields, data)

    def get_doctor_ids(self, id):
        product_type = self.env["his.category_base"].browse(id)
        doctors = self.env["his.doctor_fee"].search(
            [("service_id.product_type", "=", product_type.id)]
        )
        if doctors.exists():
            doctor_ids = doctors.mapped("doctor_id.id")
            return doctor_ids
        return []

    def get_doctor_tags(self, id):
        product_type = self.env["his.category_base"].browse(id)
        doctor_categories = self.env["his.doctor_fee"].search(
            [("service_id.product_type", "=", product_type.id)]
        )
        if doctor_categories.exists():
            doctor_category_ids = doctor_categories.mapped("doctor_id.category_ids")
            doctors_list = []
            for doctor_category in doctor_category_ids:
                doctors_list.append(
                    {"id": doctor_category.id, "name": doctor_category.name}
                )
            return doctors_list
        return []

    @api.model_create_multi
    def create(self, vals_list):
        # Validate each record before creation
        for vals in vals_list:
            if not vals.get("price_line_ids"):
                raise exceptions.ValidationError(
                    _("You must set at least one price line when creating a doctor fee!")
                )
        records = super().create(vals_list)
        for res in records:
            if (
                res.doctor_id.exists()
                and res.service_id.exists()
                and res.service_id.categ_id.exists()
            ):
                res.doctor_id.write({"specialization_ids": [(4, res.service_id.categ_id.id)]})
            if (
                res.doctor_id.exists()
                and res.service_id.exists()
                and res.service_id.product_type.exists()
            ):
                res.product_type = res.service_id.product_type.id
                res.categ_id = res.service_id.categ_id.id
        return records

    def write(self, vals):
        if "doctor_id" in vals:
            for rec in self:
                if (
                    rec.doctor_id.exists()
                    and rec.service_id.exists()
                    and rec.service_id.categ_id.exists()
                ):
                    rec.doctor_id.write(
                        {"specialization_ids": [(4, rec.service_id.categ_id.id)]}
                    )
        return super().write(vals)

    def unlink(self):
        # `doctor_fee_id` on the wizard is contributed by his_service_multi_selected
        # (ondelete="cascade"). Guard on its presence so core his can unlink a fee
        # even when that module isn't installed (else the search raises Invalid field).
        DoctorFeeWizard = self.env["his.doctor_fee_wizard"].sudo()
        if "doctor_fee_id" in DoctorFeeWizard._fields:
            wizard_lines = DoctorFeeWizard.search([("doctor_fee_id", "in", self.ids)])
            if wizard_lines:
                wizard_lines.unlink()

        for rec in self:
            if (
                rec.doctor_id.exists()
                and rec.service_id.exists()
                and rec.service_id.categ_id.exists()
            ):
                rec.doctor_id.write(
                    {"specialization_ids": [(3, rec.service_id.categ_id.id)]}
                )
        return super(DoctorFee, self).unlink()

    def get_from_doctor_id(self, id):
        if not id:
            return "Doctor id not found"

        doctor_fees = self.env["his.doctor_fee"].search([("doctor_id", "=", id)])
        if not doctor_fees:
            return "Doctor fees not found for the given doctor ID"

        result = []
        for doctor_fee in doctor_fees:
            categ_id = (
                [doctor_fee.categ_id.id, doctor_fee.categ_id.name]
                if doctor_fee.categ_id
                else None
            )
            result.append(
                {
                    "display_name": doctor_fee.doctor_id.display_name,
                    "id": doctor_fee.id,
                    "categ_id": categ_id,
                }
            )

        return result


    def _get_price_for_date(self, visit_date, type_visit):
        """
        Get the price for a specific date and visit type.
        This method filters price_line_ids based on the given date.
        """
        self.ensure_one()

        if not visit_date:
            visit_date = fields.Date.context_today(self)

        # Filter price lines that are active and have start_date <= visit_date
        eligible_lines = self.price_line_ids.filtered(
            lambda l: l.active and l.start_date and l.start_date <= visit_date
        )

        current_price = False
        if eligible_lines:
            # Get the most recent price line based on start_date and create_date
            current_price = max(
                eligible_lines, key=lambda l: (l.start_date, l.create_date)
            )

        if current_price:
            if type_visit == "1":
                return current_price.first_visit_price
            elif type_visit == "2":
                return current_price.revisit_price
            elif type_visit == "follow_up":
                return current_price.follow_up_price

        # If no price found for the date, raise an error
        raise exceptions.UserError(
            _("No active price found for doctor fee on date %s") % visit_date
        )

    def get_price_from_type_visit(self, type_visit, date=None):
        """
        Get price based on visit type and date.
        Depending on the system setting 'doctor_fee_price_date':
        - 'now': Use current date (computed prices from _compute_prices)
        - 'visit_date': Use provided date parameter

        Args:
            type_visit: Type of visit ('1', '2', 'follow_up')
            date: Date to use for price calculation (optional)
        """
        self.ensure_one()

        # Get the setting value
        Param = self.env['ir.config_parameter'].sudo()
        price_date_setting = Param.get_param(
            'his.doctor_fee_price_date', default='now'
        )

        # If setting is 'visit_date', use provided date
        if price_date_setting == 'visit_date' and date:
            return self._get_price_for_date(date, type_visit)

        # Default behavior: use current prices (based on today's date)
        if type_visit == "1":
            return self.first_visit_price
        elif type_visit == "2":
            return self.revisit_price
        elif type_visit == "follow_up":
            return self.follow_up_price
        else:
            raise exceptions.UserError(_("Invalid visit type provided: %s") % type_visit)

    def get_price(self, patient_visit_id):
        if isinstance(patient_visit_id, int):
            patient_visit_id = self.env["his.patient_visit"].browse(patient_visit_id)
        return self.get_price_from_type_visit(
            patient_visit_id.type_visit, patient_visit_id.date
        )

    def get_service_duration(self, type_visit=None):
        """Resolve the booking slot duration (in minutes) for a visit type.

        Revisit ('2') uses ``revisit_service_duration`` and follow-up visits
        use ``follow_up_service_duration`` when configured (> 0); otherwise they
        fall back to the regular ``service_duration``. A value of 0 means
        "not configured" and is ignored, so existing fees keep their behaviour.

        Single source of truth for slot length across every booking flow.
        """
        self.ensure_one()
        if type_visit == "2" and self.revisit_service_duration:
            return self.revisit_service_duration
        if type_visit == "follow_up" and self.follow_up_service_duration:
            return self.follow_up_service_duration
        return self.service_duration

    _BASE_PRICE_FIELDS = ("first_visit_price", "revisit_price", "follow_up_price")

    def _apply_service_base_price(self, price):
        """Overwrite each fee's visit prices with the service base price.

        Triggered when the linked service's base price (``lst_price``) changes.
        Doctor fee prices are computed from ``price_line_ids``, so we update
        today's active price line in place when one exists, otherwise create a
        new line dated today so the price history is preserved.

        A visit price that was 0 on the previous line is kept at 0 (e.g. a fee
        with no revisit/follow-up price): only non-zero prices follow the base.
        """
        today = fields.Date.context_today(self)
        PriceLine = self.env["his.doctor_fee.price.line"]
        for fee in self:
            line = fee.price_line_ids.filtered(
                lambda l: l.active and l.start_date == today
            ).sorted("id", reverse=True)[:1]
            # Old values come from today's line (updated in place) or, when none
            # exists, from the most recent active line carried forward.
            source = line or fee.price_line_ids.filtered(
                lambda l: l.active and l.start_date and l.start_date <= today
            ).sorted(lambda l: (l.start_date, l.id), reverse=True)[:1]
            price_vals = {
                f: 0.0 if (source and not source[f]) else price
                for f in self._BASE_PRICE_FIELDS
            }
            if line:
                line.write(price_vals)
            else:
                PriceLine.create(dict(price_vals, doctor_fee_id=fee.id, start_date=today))

    @api.depends(
        "price_line_ids",
        "price_line_ids.start_date",
        "price_line_ids.first_visit_price",
        "price_line_ids.revisit_price",
    )
    def _compute_prices(self):
        today_in_user_tz = fields.Date.context_today(self)

        for rec in self:
            eligible_lines = rec.price_line_ids.filtered(
                lambda l: l.start_date
                and l.start_date <= today_in_user_tz
                and l.create_date
            )

            current_price = False
            if eligible_lines:
                current_price = max(
                    eligible_lines, key=lambda l: (l.start_date, l.create_date)
                )

            if current_price:
                rec.first_visit_price = current_price.first_visit_price
                rec.revisit_price = current_price.revisit_price
                rec.follow_up_price = current_price.follow_up_price
            else:
                if len(rec.price_line_ids) > 0:
                    latest_price_line = sorted(
                        rec.price_line_ids,
                        key=lambda l: (
                            l.start_date or datetime.min.date(),
                            l.create_date or datetime.min,
                        ),
                        reverse=True,
                    )[0]
                    self.env["mail.message"].create(
                        {
                            "model": "his.doctor_fee",
                            "res_id": rec.id,
                            "message_type": "notification",
                            "body": f"Today in user TZ: {today_in_user_tz}, No active price found for doctor fee. Latest price line start date: {latest_price_line.start_date}, ID: {latest_price_line.id}",
                        }
                    )

                    admin_users = self.env.ref("base.group_system").users
                    self.env["mail.message"].create(
                        {
                            "message_type": "notification",
                            "body": f"Doctor Fee Warning: No active price found for {rec.doctor_id.name} - {rec.service_id.name}",
                            "subject": "Doctor Fee Price Warning",
                            "partner_ids": [
                                (6, 0, admin_users.mapped("partner_id").ids)
                            ],
                            "model": rec._name,
                            "res_id": rec.id,
                        }
                    )

                # Bu holatga tushmaslik kerak, chunki _check_price_lines constraint bor
                rec.first_visit_price = 0.0
                rec.revisit_price = 0.0
                rec.follow_up_price = 0.0

    @api.depends("doctor_id")
    def _compute_filial_names(self):
        for rec in self:
            rec.filial_names = ", ".join(rec.doctor_id.filial_ids.mapped("name"))
