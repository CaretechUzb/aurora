from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class DoctorSchedule(models.Model):
    _name = "his.doctor_schedule"
    _description = "Doctor Schedule Records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    doctor_id = fields.Many2one(
        "hr.employee", string="Doctor", required=True, tracking=True
    )
    date = fields.Date(string="Date", required=True, tracking=True)
    working_periods = fields.One2many(
        "his.doctor_working_periods",
        "doctor_schedule_id",
        check_company=True,
        string="Working Periods",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )

    working_periods_display = fields.Char(
        string="Working Hours",
        compute="_compute_working_periods_display",
        store=True
    )

    @api.depends('working_periods', 'working_periods.start_time', 'working_periods.end_time')
    def _compute_working_periods_display(self):
        for record in self:
            # Only show periods with valid times
            valid_periods = record.working_periods.filtered(
                lambda p: p.start_time and p.end_time
            )

            if valid_periods:
                periods = []
                for period in valid_periods:
                    start_time = self._format_time(period.start_time)
                    end_time = self._format_time(period.end_time)
                    period_str = f"{start_time} - {end_time}"
                    periods.append(period_str)
                record.working_periods_display = ", ".join(periods)
            else:
                record.working_periods_display = "No records"

    def _format_time(self, time_float):
        """Convert float time to HH:MM format"""
        if not time_float:
            return "00:00"
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def name_get(self):
        result = []
        for record in self:
            name = _(f"{record.doctor_id.name} - {record.date} schedule")
            result.append((record.id, name))
        return result

    def action_bulk_delete_unused(self):
        """List-view "Delete" server action: bulk delete selected schedules.

        A schedule day is kept when its doctor has any active
        (non-cancelled, non-deleted) patient visit on that date; the rest
        are deleted together with their working periods. Kept days are
        reported back in a warning notification.
        """
        if not self.env.user.has_group("his.group_his_manager"):
            raise AccessError(
                _("Only managers can bulk delete doctor schedules.")
            )

        used_pairs = set()
        if self:
            # sudo: record rules must not hide a booked visit, otherwise a
            # used schedule could be deleted by a user who cannot see it
            visits = (
                self.env["his.patient_visit"]
                .sudo()
                .search_read(
                    [
                        ("doctor_id", "in", self.doctor_id.ids),
                        ("date", "in", list(set(self.mapped("date")))),
                        ("patient_status", "not in", ["cancelled", "deleted"]),
                    ],
                    ["doctor_id", "date"],
                )
            )
            used_pairs = {
                (visit["doctor_id"][0], visit["date"]) for visit in visits
            }

        protected = self.filtered(
            lambda schedule: (schedule.doctor_id.id, schedule.date) in used_pairs
        )
        to_delete = self - protected

        # sudo + explicit search: working periods carry a multi-company record
        # rule, so `to_delete.working_periods` hides periods in companies the
        # user has not enabled. Those would be left behind and trip the RESTRICT
        # FK when the schedule is unlinked. Delete children by parent id instead.
        self.env["his.doctor_working_periods"].sudo().search(
            [("doctor_schedule_id", "in", to_delete.ids)]
        ).unlink()
        to_delete.sudo().unlink()

        message = _(
            "%(deleted)s day(s) deleted, %(protected)s day(s) kept "
            "(have active visits).",
            deleted=len(to_delete),
            protected=len(protected),
        )
        if protected:
            shown = [
                f"{schedule.doctor_id.name} — {schedule.date.strftime('%d.%m.%Y')}"
                for schedule in protected[:10]
            ]
            if len(protected) > 10:
                shown.append("…")
            message += " " + _("Not deleted (in use): %s", ", ".join(shown))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Schedule Delete Results"),
                "message": message,
                "type": "warning" if protected else "success",
                "sticky": bool(protected),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def init(self):
        super(DoctorSchedule, self).init()
        self._cr.execute(
            """CREATE INDEX IF NOT EXISTS idx_his_doctor_schedule_doctor_date ON his_doctor_schedule(doctor_id, date);"""
        )

