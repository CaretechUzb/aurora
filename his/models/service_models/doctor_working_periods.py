from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta


class DoctorScheduleVisitType(models.Model):
    _name = "his.doctor_schedule_visit_type"
    _description = "Doctor Schedule Visit Type"

    visit_type = fields.Selection(
        [("1", "1П"), ("follow_up", _("Follow-up")), ("2", "2П")],
        string="Schedule Type",
        required=True,
        help="Type of vistis for the doctor schedule",
    )

    def unlink(self):
        if self.env.context.get("force_delete", False):
            return super(DoctorScheduleVisitType, self).unlink()
        raise exceptions.UserError(_("You cannot delete this record."))

    def name_get(self):
        result = []
        for record in self:
            selection_dict = dict(
                self.env[record._name]
                .with_context(lang=self.env.user.lang)
                .fields_get(["visit_type"])["visit_type"]["selection"]
            )
            name = selection_dict.get(record.visit_type, record.visit_type)
            result.append((record.id, name))
        return result


class DoctorWorkingPeriods(models.Model):
    _name = "his.doctor_working_periods"
    _description = "Working Periods Records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    doctor_schedule_id = fields.Many2one(
        "his.doctor_schedule", required=True, check_company=True, tracking=True
    )
    start_time = fields.Float(
        string="Start Time",
        digits=(2, 2),
        help="Start time in hours (0.00 - 23.99)",
        required=True,
        tracking=True,
    )
    end_time = fields.Float(
        string="End Time",
        digits=(2, 2),
        help="End time in hours (0.00 - 23.99)",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    doctor_id = fields.Many2one(
        "hr.employee",
        string="Doctor",
        related="doctor_schedule_id.doctor_id",
        store=True,
    )

    start_datetime = fields.Datetime(
        string="Start Time ", compute="_compute_datetimes", store=True
    )
    end_datetime = fields.Datetime(
        string="End Time ", compute="_compute_datetimes", store=True
    )
    label = fields.Char(
        string="Label",
    )
    name = fields.Text(
        string="Working Periods Summary",
        compute="_compute_name",
        store=True,
    )
    schedule_type = fields.Selection(
        [("default", _("Default")), ("in_queue", _("In Queue"))],
        string="Schedule Type",
        help="Type of schedule for the doctor",
        tracking=True,
    )
    is_services_restricted = fields.Boolean(
        string="Restrict Services",
        default=False,
        help="If checked, restricts the services available during this working period",
        tracking=True,
    )
    allowed_services_ids = fields.Many2many(
        "product.product",
        string="Allowed Services",
        help="Services allowed during this working period",
        tracking=True,
        domain=[("type", "=", "service"), ("is_schedulable", "=", True)],
    )
    visit_type = fields.Many2many(
        "his.doctor_schedule_visit_type",
        string="Visiti Types",
        help="Types of visits for the doctor schedule",
        tracking=True,
    )

    @api.depends("doctor_schedule_id.date", "start_time", "end_time")
    def _compute_datetimes(self):
        for record in self:
            if record.doctor_schedule_id.date:
                start_hours = int(record.start_time)
                start_minutes = int((record.start_time % 1) * 60)

                end_hours = int(record.end_time)
                end_minutes = int((record.end_time % 1) * 60)

                start_datetime = datetime.combine(
                    record.doctor_schedule_id.date, datetime.min.time()
                ) + timedelta(hours=start_hours, minutes=start_minutes)
                end_datetime = datetime.combine(
                    record.doctor_schedule_id.date, datetime.min.time()
                ) + timedelta(hours=end_hours, minutes=end_minutes)

                record.start_datetime = start_datetime
                record.end_datetime = end_datetime

    @api.depends("doctor_schedule_id", "start_time", "end_time", "company_id")
    def _compute_name(self):
        for record in self:
            name = ""
            start_time = f"{record.start_time:.2f}".replace(".", ":")
            end_time = f"{record.end_time:.2f}".replace(".", ":")
            if record.label:
                name += record.label
            name += f' <div style="color: #325599;">🕓 {start_time} - {end_time}, 🏥 {record.company_id.name}<br /></div>'
            record.name = name

    @api.constrains("start_time", "end_time")
    def _onchange_check_overlapping_periods(self):
        for record in self:
            if record.start_time is not None and record.end_time is not None:
                if record.start_time >= record.end_time:
                    raise exceptions.ValidationError(
                        _("Start time cannot be greater than or equal to end time.")
                    )

                if not record.doctor_schedule_id or not record.doctor_schedule_id.date:
                    continue

                # Hamma company_id uchun tekshirilsin
                domain = [
                    ("doctor_schedule_id.doctor_id", "=", record.doctor_schedule_id.doctor_id.id),
                    ("doctor_schedule_id.date", "=", record.doctor_schedule_id.date),
                ]

                # ID mavjud bo'lsa, o'zini tekshiruvdan chiqaramiz
                if isinstance(record.id, int):
                    domain.append(("id", "!=", record.id))

                periods = record.sudo().with_company(False).search(domain)

                temp_id = str(record.id).split("_")
                if len(temp_id) > 1 and temp_id[1].isdigit():
                    temp_id = int(temp_id[1])
                else:
                    temp_id = record.id

                format_time = lambda x: f"{x:.2f}".replace(".", ":")

                for period in periods:
                    if (
                        period.id != temp_id
                        and period.start_time < record.end_time
                        and period.end_time > record.start_time
                    ):
                        raise exceptions.ValidationError(
                            _(
                                "The specified time period overlaps with an existing period from {} to {} "
                                "on {} in company '{}'. Current period: {} to {}"
                            ).format(
                                format_time(period.start_time),
                                format_time(period.end_time),
                                record.doctor_schedule_id.date,
                                period.company_id.name or _("Unknown"),
                                format_time(record.start_time),
                                format_time(record.end_time),
                            )
                        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            new_start_time = vals.get("start_time")
            new_end_time = vals.get("end_time")
            if (
                new_start_time is not None
                and new_end_time is not None
                and new_start_time >= new_end_time
            ):
                raise exceptions.ValidationError(
                    _("Start time cannot be greater than or equal to end time.")
                )

        return super(DoctorWorkingPeriods, self).create(vals_list)

    def write(self, vals):
        return super(DoctorWorkingPeriods, self).write(vals)
