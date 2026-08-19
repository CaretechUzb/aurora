from odoo import models, fields, api, _
from odoo import exceptions
from odoo.tools.misc import format_duration


class MedicineReceptionTime(models.Model):
    _name = "his.medicine_reception_time"
    _description = "Medicine Reception Time"

    medicine_prescription_id = fields.Many2one(
        "his.medicine_prescription", string="Medicine Prescription"
    )
    time = fields.Float(string="Time")
    formatted_time = fields.Char(
        string="Formatted Time", compute="_compute_formatted_time"
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, str(record.time)))
        return result

    @api.depends("time")
    def _compute_formatted_time(self):
        for record in self:
            record.formatted_time = format_duration(record.time)

    def parse_to_float(self, str_time):
        parts = str_time.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours + (minutes / 60)

    @api.onchange("time")
    def _onchange_time(self):
        if self.time:
            if self.time < 0:
                raise exceptions.ValidationError(_("Time must be greater than 0"))
            elif self.time > 23.59:
                raise exceptions.ValidationError(_("Time must be less than 24"))

            start_day_time = self.env.context.get("start_day_time")
            end_day_time = self.env.context.get("end_day_time")
            initial_date = self.env.context.get("initial_date")
            if (
                start_day_time
                and end_day_time
                and initial_date
                and self.medicine_prescription_id
                and self.medicine_prescription_id.start_date.strftime("%Y-%m-%d")
                == initial_date
            ):
                float_start_time = self.parse_to_float(start_day_time[11:16])
                float_end_time = self.parse_to_float(end_day_time[11:16])
                if float_end_time < float_start_time:
                    valid_time_range = (self.time >= float_start_time) or (
                        self.time < float_end_time
                    )
                else:
                    valid_time_range = float_start_time <= self.time < float_end_time

                if not valid_time_range:
                    raise exceptions.ValidationError(
                        _(
                            "Time must be between {} and {}".format(
                                start_day_time[11:16], end_day_time[11:16]
                            )
                        )
                    )
