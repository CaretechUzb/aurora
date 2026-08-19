from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.exceptions import UserError


class Prescription(models.Model):
    _name = "his.prescription"
    _description = "Prescription"

    name = fields.Char(string="Name")
    patient_visit_id = fields.Many2one("his.patient_visit", string="Patient Visit")
    patient_id = fields.Many2one(
        "his.patient",
        string="Patient",
        related="patient_visit_id.patient_id",
        store=True,
    )
    doctor_id = fields.Many2one(
        "hr.employee",
        string="Doctor",
    )
    medicine_ids = fields.One2many(
        "his.medicine_prescription",
        "prescription_id",
        string="Medicine Dosages",
    )
    prescription_with_markup = fields.Html(
        string="Prescription with Markup", compute="_compute_prescription_with_markup"
    )
    is_template = fields.Boolean(string="Is Template", default=False)
    template_name = fields.Char(string="Template Name")
    medicine_schedules = fields.One2many(
        "his.medicine_prescription_schedule",
        "prescription",
        string="Medicine Schedules",
    )

    def name_get(self):
        result = []
        for record in self:
            name = _("Prescription") + " - " + record.patient_id.full_name
            result.append((record.id, name))
        return result

    @api.depends("medicine_ids")
    def _compute_prescription_with_markup(self):
        for record in self:
            prescription_with_markup = "<ol style='font-size: 16px;'>"
            for medicine in record.medicine_ids:

                medicine_name = f"<b>{medicine.medicine_names_with_dosage}</b>"
                prescription_with_markup += f"<li>{medicine_name}"
                if medicine.administration_method:
                    prescription_with_markup += f" ({medicine.administration_method}),"
                if medicine.sleep_regarding:
                    txt = dict(medicine._fields["sleep_regarding"].selection).get(
                        medicine.sleep_regarding
                    )
                    prescription_with_markup += f" {str(_(txt))},"
                if medicine.food_regarding:
                    txt = dict(medicine._fields["food_regarding"].selection).get(
                        medicine.food_regarding
                    )
                    prescription_with_markup += f" {str(_(txt))},"
                if medicine.start_date:
                    prescription_with_markup += f" {str(_('start from'))} {format_date(self.env, medicine.start_date)},"
                if medicine.duration:
                    prescription_with_markup += (
                        f" {medicine.duration} {str(_(medicine.duration_unit))}"
                    )
                if medicine.reception_per_day:
                    prescription_with_markup += (
                        f" {medicine.reception_per_day} {str(_('times per day'))}"
                    )
                if medicine.reception_times_ids:
                    prescription_with_markup += f" {','.join(medicine.reception_times_ids.mapped('formatted_time'))},"
                if medicine.infusion_rate:
                    prescription_with_markup += f" {medicine.infusion_rate} ml,"
                if medicine.infusion_speed:
                    prescription_with_markup += (
                        f" {medicine.infusion_speed} {medicine.infusion_speed_unit},"
                    )
                if medicine.is_urgently:
                    prescription_with_markup += f" {str(_('Urgently'))},"
                if medicine.notes:
                    prescription_with_markup += f" {medicine.notes}"
                prescription_with_markup += "</li>"
            prescription_with_markup += "</ol>"
            record.prescription_with_markup = prescription_with_markup

    def action_print(self):
        self.ensure_one()
        template_id = (
            self.env["ir.config_parameter"].sudo().get_param("his.prescription_emr")
        )
        if not template_id:
            raise UserError(_("Please set EMR template in settings"))
        return {
            "type": "ir.actions.client",
            "tag": "print_emr",
            "params": {"report_id": int(template_id), "record_id": self.id},
        }

    def action_open_readonly_wizard(self):
        self.ensure_one()
        wizard = self.env["his.prescription_wizard"].create(
            {
                "prescription_id": self.id,
                "medicine_prescription_ids": [(6, 0, self.medicine_ids.ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Prescription"),
            "res_model": "his.prescription_wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
            "views": [
                [
                    self.env.ref(
                        "his.prescription_wizard_readonly_view_form"
                    ).id,
                    "form",
                ]
            ],
        }

    def action_add_medicine_prescription(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "his.medicine_prescription",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_prescription_id": self.id,
            },
        }
