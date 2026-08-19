from odoo import fields, models, api, _
import json
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = "hr.employee"

    info_description = fields.Html(string="Info", translate=True, sanitize=False)
    information_tooltip = fields.Char(
        string="Info ", compute="_compute_info_description", store=True
    )
    is_virtual = fields.Boolean(string="Virtual")
    department_ids = fields.One2many(
        "hr.employee_department", "employee_id", string="Departments"
    )
    doctor_ids = fields.Many2many(
        "hr.employee",
        "virtual_doctor_rel",
        "virtual_doctor_id",
        "doctor_id",
        string="Doctors",
    )
    filial_ids = fields.Many2many(
        "res.company",
        relation="user_company_rel",
        string="Companies",
        related="user_id.company_ids",
    )

    signature = fields.Binary(string="Signature")
    fingerprint = fields.Binary(string="Fingerprint")
    specialization_ids = fields.Many2many(
        comodel_name="product.category",
        string="Specialization",
        relation="hr_employee_product_category_rel",
        column1="hr_employee_id",
        column2="product_category_id",
        domain=[("is_his", "=", True)],
        tracking=True,
    )
    service_price_list = fields.Html(
        compute="_compute_service_price_list", translate=True
    )
    price_list = fields.One2many("his.doctor_fee", "doctor_id")

    short_desc = fields.Text(translate=True)
    academic_rank = fields.Char(translate=True)
    work_experience = fields.Integer(
        readonly=True, compute="_compute_work_experience", store=True
    )
    can_online_appointment = fields.Boolean()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company_id",
        search="_search_company_id",
        store=True,
        readonly=True,
        required=False,
    )
    working_perion_html = fields.Html(
        "Working Periods", compute="_compute_working_period_html"
    )
    can_create_share_bonus = fields.Boolean('Create share bonus', default=True)

    doctor_appointment_type_ids = fields.Many2many(
        "his.doctor.appointment.type", string="Appointment Types"
    )
    doctor_target_group = fields.Selection(
        [
            ("adult", "Adult"),
            ("child", "Child"),
            ("all", "All"),
        ],
        string="Patient Target Group",
    )
    doctor_language_ids = fields.Many2many("res.lang", string="Spoken Languages")
    pinfl = fields.Char(string="PINFL", size=14, tracking=True)

    _sql_constraints = [
        ('pinfl_unique', 'UNIQUE(pinfl)', 'PINFL must be unique per employee.'),
    ]

    def parse_time(self, time_float):
        hours = int(time_float)
        minutes = int(round((time_float - hours) * 100))
        return "%02d:%02d" % (hours, minutes)

    @api.depends_context("company")
    def _compute_working_period_html(self):
        for record in self:
            today = fields.Date.today()
            start_date = today
            end_date = start_date + timedelta(days=7)

            doctor_schedule_ids = (
                self.env["his.doctor_schedule"]
                .sudo()
                .search(
                    [
                        ("doctor_id", "=", record.id),
                        ("date", ">=", today),
                        ("date", "<=", end_date),
                        # ("company_id", "=", record.company_id.id),
                    ]
                )
            )
            if not doctor_schedule_ids:
                record.working_perion_html = "No working period found"
                continue

            working_periods = (
                self.env["his.doctor_working_periods"]
                .sudo()
                .search(
                    [
                        ("doctor_schedule_id", "in", doctor_schedule_ids.ids),
                        ("start_time", "!=", False),
                        ("end_time", "!=", False),
                    ],
                    order="id asc",
                )
            )

            if not working_periods:
                record.working_perion_html = "No working period found"
                continue
            html = "<table class='table table-bordered'><thead><tr><th>Date</th><th>Start Time</th><th>End Time</th></tr></thead><tbody>"
            for period in working_periods:
                start_time = self.parse_time(period.start_time)
                end_time = self.parse_time(period.end_time)
                schedule_date = period.doctor_schedule_id.date.strftime("%A")
                html += f"<tr><td>{schedule_date}</td><td>{start_time}</td><td>{end_time}</td></tr>"
            html += "</tbody></table>"
            record.working_perion_html = html

    def get_doctors_list(self, domain):
        doctors = self.search(domain)
        result = []
        for doctor in doctors:
            result.append(
                {
                    "name": doctor.name,
                    "id": doctor.id,
                    "filial": [
                        {"id": filial.id, "name": filial.name}
                        for filial in doctor.filial_ids
                    ],
                }
            )

        return result

    @api.model_create_multi
    def create(self, vals):
        for rec in vals:
            if rec.get("company_id"):
                rec["company_id"] = False
        return super(Employee, self).create(vals)

    def write(self, vals):
        if vals.get("company_id"):
            vals["company_id"] = False
        return super(Employee, self).write(vals)

    @api.model
    def _search_company_id(self, operator, value):
        return [("department_ids.company_id", operator, value)]

    @api.depends("department_ids")
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = False

    user_id = fields.Many2one(
        "res.users",
        "User",
        tracking=True,
        related="resource_id.user_id",
        store=True,
        readonly=False,
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            self.company_id = False

    @api.depends("info_description")
    def _compute_info_description(self):
        for record in self:
            button_struct = {
                "title": record.name,
                "html": record.info_description,
            }
            record.information_tooltip = json.dumps(button_struct)

    @api.depends("price_list")
    def _compute_service_price_list(self):
        for record in self:
            doctor_fee = self.env["his.doctor_fee"].search(
                [
                    ("doctor_id", "=", record.id),
                ]
            )

            html_price_list_by_service = "<table style='width: 100%; border: 1px solid #d5d5d5;padding: 5px; border-collapse: collapse;'>\
                <tr style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'><th style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'>Service</th>\
                <th style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'>Service Requirements</th>\
                <th style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'>First Visit Price</th>\
                    <th style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'>Revisit Price</th><th style='border: 1px solid #d5d5d5;padding: 5px;font-weight:bold;'>Company</th></tr>"
            for i in doctor_fee:
                first_visit_price = f"{int(i.first_visit_price):,}"
                revisit_price = f"{int(i.revisit_price):,}"
                service_requirements = i.service_id.service_requirements if i.service_id.service_requirements else ''
                html_price_list_by_service += f"<tr style='border: 1px solid #d5d5d5;padding: 5px;'><td style='border: 1px solid #d5d5d5;padding: 5px;'>{i.service_id.name}</td>\
                    <td style='border: 1px solid #d5d5d5;padding: 5px;'>{service_requirements}</td>\
                    <td style='border: 1px solid #d5d5d5;padding: 5px;'>{first_visit_price}</td><td style='border: 1px solid #d5d5d5;padding: 5px;'>{revisit_price}</td>\
                        <td style='border: 1px solid #d5d5d5;padding: 5px;'>{i.company_id.name}</td></tr>"

            html_price_list_by_service += "</table>"
            record.service_price_list = html_price_list_by_service

    # d=self.env['hr.employee'].search([('id','=',8)])
    # d._compute_service_price_list()
    # d.service_price_list

    def get_doctor_schedule(self, user_id, start_time=None, end_time=None):
        user = self.env["res.users"].browse(user_id)
        if not user or not user.employee_id:
            raise ValidationError(_("User or employee not found."))
        return self.get_doctors_schedule_list(user.employee_id.id, start_time, end_time)

    def get_doctors_schedule_list(
        self, employee_id=None, start_time=None, end_time=None
    ):
        # Return an empty dictionary if no employee_id is provided
        if not employee_id:
            return {}

        # Search for the specific employee by employee_id
        employees = self.env["hr.employee"].search([("id", "=", employee_id)])

        doctors_schedule_dict = {}

        for employee in employees:
            # Search for the doctor's schedule for the current employee in the given date range
            doctor_schedules = self.env["his.doctor_schedule"].search(
                [
                    ("doctor_id", "=", employee.id),
                    ("date", ">=", start_time),
                    ("date", "<=", end_time),
                    ("company_id", "in", self.env.companies.ids),
                ]
            )

            # Raise validation error if no schedule is found for the doctor in the given date range
            if not doctor_schedules:
                return {"error": "doctor_schedules_not_found"}

            # Loop through all doctor schedules found
            for doctor_schedule in doctor_schedules:
                # Search for the working periods for the doctor on this specific schedule
                doctor_working_periods = self.env["his.doctor_working_periods"].search(
                    [("doctor_schedule_id", "=", doctor_schedule.id)]
                )

                # Prepare the working periods for the current schedule if they exist
                working_periods = []
                if doctor_working_periods:
                    working_periods = doctor_working_periods.mapped(lambda wp: {
                        'start_time': wp.start_time,
                        'end_time': wp.end_time,
                        'name': wp.label,
                        'type': wp.schedule_type,
                        'company_name': wp.company_id.name,
                        'company_id': wp.company_id.id,
                    })

                # Convert schedule date to string to avoid JSON serialization issues
                schedule_date_str = doctor_schedule.date.strftime("%Y-%m-%d")

                # Use the schedule date (string) as the key, and add the working periods
                if schedule_date_str not in doctors_schedule_dict:
                    doctors_schedule_dict[schedule_date_str] = working_periods
                else:
                    # If there are multiple periods on the same day, append them to the existing list
                    doctors_schedule_dict[schedule_date_str].extend(working_periods)

        return doctors_schedule_dict

    @api.depends("resume_line_ids")
    def _compute_work_experience(self):
        type_id = self.env.ref("hr_skills.resume_type_experience").id
        total_experience = 0.0

        for record in self:
            for resume in record.resume_line_ids:
                if resume.line_type_id.id == type_id and resume.date_start:
                    try:
                        start_date = fields.Date.from_string(resume.date_start)
                        end_date = (
                            fields.Date.from_string(resume.date_end)
                            if resume.date_end
                            else fields.Date.today()
                        )

                        if start_date > end_date:
                            continue
                        delta = relativedelta(end_date, start_date)
                        years = delta.years + delta.months / 12.0 + delta.days / 365.25

                        total_experience += years
                    except Exception as e:
                        continue
            record.work_experience = round(total_experience, 1)

    # @api.model
    # def create(self, vals):
    #     employee = super(Employee, self).create(vals)
    #     if 'work_contact_id' in vals and vals['work_contact_id']:
    #         employee._compute_referral_sources()
    #     return employee
    # def write(self, vals):
    #     result = super(Employee, self).write(vals)
    #     if 'work_contact_id' in vals:
    #         self._compute_referral_sources()
    #     return result

    # def _compute_referral_sources(self):
    #     for employee in self:
    #         # print(employee.work_contact_id)
    #         if employee.work_contact_id:
    #             for partner in employee.work_contact_id:
    #                 # print(partner)
    #                 # print(partner.referral_source_by_service_ids)
    #                 if not partner.referral_source_by_service_ids and not partner.referral_source_by_product_type_ids:
    #                     referral_service_records = self.env['his.referral_source_by_service'].sudo().search([('partner_id', '=', False)])
    #                     # print(referral_service_records)
    #                     for record in referral_service_records:
    #                         # print(record)
    #                         record.copy({'partner_id': employee.work_contact_id.id})

    #                     referral_product_type_records = self.env['his.referral_source_by_product_type'].sudo().search([('partner_id', '=', False)])
    #                     # print(referral_product_type_records)
    #                     for record in referral_product_type_records:
    #                         # print(record)
    #                         record.copy({'partner_id': employee.work_contact_id.id})

    def init(self):
        """
        This has to be called in every overriding module
        """
        res = super().init()
        import os

        sql_path = os.path.join(
            os.path.dirname(__file__), "hr_employee_company_id_null_trigger.sql"
        )
        sql_path = os.path.abspath(sql_path)
        with open(sql_path, "r") as f:
            sql = f.read()
        try:
            self.env.cr.execute(sql)
        except Exception as e:
            import logging

            _logger = logging.getLogger(__name__)
            _logger.warning(f"Error executing SQL trigger creation: {e}")
        return res

    def _get_all_managers(self):
        """
        Get recursively all managers of the employee
        """
        manager_ids = set()
        for employee in self:
            current_employee = employee
            while current_employee and current_employee.parent_id:
                manager_ids.add(current_employee.parent_id.id)
                current_employee = current_employee.parent_id
        return self.browse(manager_ids)
