import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class MedicinePrescriptionSchedule(models.Model):
    _name = "his.medicine_prescription_schedule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "time"
    _description = "Medicine Prescription Schedule"
    _rec_name = "prescription_medicine"

    prescription_medicine = fields.Many2one(
        "his.medicine_prescription",
        string="Prescription Medicine",
    )
    prescription = fields.Many2one(
        "his.prescription",
        string="Prescription",
        related="prescription_medicine.prescription_id",
        store=True,
    )
    medicine_ids = fields.One2many(
        "his.medicine_prescription_dosage",
        "medicine_prescription_id",
        string="Medicine Dosages",
        related="prescription_medicine.medicine_ids",
    )
    medicines_info = fields.Json(
        string="Medicines Info", related="prescription_medicine.medicines_info"
    )
    medicine_type = fields.Selection(
        related="prescription_medicine.medicine_type", store=True
    )

    dosage = fields.Float(string="Dosage")
    # infusion_speed_unit = fields.Selection(
    #     [("ml/h", "ml/h"), ("ml/min", "ml/min")],
    #     string="Infusion Speed Unit",
    # )

    time = fields.Datetime(string="Time")
    state = fields.Selection(
        [("pending", "Pending"), ("done", "Done"), ("canceled", _("Canceled"))],
        default="pending",
        tracking=True,
    )
    done_by = fields.Many2one("hr.employee", string="Done by")
    done_time = fields.Datetime(string="Done time")
    cancel_reason = fields.Text(string="Cancel Reason")
    notes = fields.Text(string="Notes", related="prescription_medicine.notes")
    medicine_prescription_cancel = fields.Json(
        string="Medicine prescription cancel",
        compute="_computed_medicine_prescription_cancel",
    )

    def action_done(self):
        for rec in self:
            # if rec.time + timedelta(minutes=60) > fields.Datetime.now():
            #     raise UserError(_("You can't mark this schedule as done"))
            rec.write(
                {
                    "state": "done",
                    "done_by": self.env.user.employee_id.id,
                    "done_time": fields.Datetime.now(),
                }
            )

    def action_show_cancel_form(self):
        form_id = self.env.ref("admission.schedule_cancel_form").id
        return {
            "type": "ir.actions.act_window",
            "name": _("Cancel Schedule"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "views": [(form_id, "form")],
            "target": "new",
        }

    def action_cancel(self):
        for rec in self:
            if not rec.cancel_reason:
                raise UserError(
                    _("Please provide a reason for canceling this schedule")
                )
            rec.write({"state": "canceled"})

    @api.depends("prescription_medicine")
    def _computed_medicine_prescription_cancel(self):
        for rec in self:
            medicine_prescription_cancel = self.env[
                "his.medicine_prescription_cancel_form"
            ].search(
                [("medicine_prescription_id", "=", rec.prescription_medicine.id)],
                limit=1,
            )

            if not medicine_prescription_cancel.exists():
                rec.medicine_prescription_cancel = False
            else:
                rec.medicine_prescription_cancel = {
                    "description": medicine_prescription_cancel.description,
                    "cancel_reason": [
                        medicine_prescription_cancel.cancel_reason_id.id,
                        medicine_prescription_cancel.cancel_reason_id.name,
                    ],
                }
