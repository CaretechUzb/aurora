from odoo import exceptions, models, fields, api, _
from datetime import timedelta
from odoo.tools import format_duration
from datetime import datetime
import pytz
import dateutil


class MedicinePrescription(models.Model):
    _name = "his.medicine_prescription"
    _description = "Medicine Prescription"

    prescription_id = fields.Many2one(
        "his.prescription", string="Prescription", required=False
    )
    medicine_type = fields.Selection(
        [
            ("medicine", _("Medicine")),
            ("nutrition", _("Nutrition")),
        ],
        string="Medicine Type",
        default="medicine",
        required=True,
    )
    medicine_ids_domain = fields.Binary(
        string="Medicine IDs Domain",
        compute="_compute_medicine_ids_domain",
    )
    allow_dosage_selection = fields.Boolean(
        compute="_compute_allow_dosage_selection",
        default=lambda self: self._get_allow_dosage_selection_value(),
    )
    medicine_ids = fields.One2many(
        "his.medicine_prescription_dosage",
        "medicine_prescription_id",
        string="Medicine Dosages",
    )
    prescription_type = fields.Selection(
        [
            ("single", _("Single Medicine")),
            ("composite", _("Composite Medicine")),
        ],
        string="Prescription Type",
        compute="_compute_prescription_type",
        store=True,
    )
    doctor_id = fields.Many2one("hr.employee", string="Doctor")
    administration_method = fields.Selection(
        [
            ("oral", _("Перорально")),
            ("intramuscularly", _("Внутримышечно")),
            ("intravenously", _("Внутривенно")),
            ("buccal", _("Трансбуккально")),
            ("subcutaneously", _("Подкожно")),
            ("sublingual", _("Сублингвально")),
            ("inhalation", _("Ингаляция")),
            ("instillation", _("Инстилляция")),
            ("rectally", _("Ректально")),
            ("vaginally", _("Вагинально")),
            ("intraarterial", _("Внутриартериально")),
            ("nasally", _("Назально")),
            ("transdermally", _("Трансдермально")),
            ("intradermal", _("Внутрикожно")),
            ("epidurally", _("Эпидурально")),
            ("intrathecal", _("Интратекально")),
            ("intra-articular", _("Внутрисуставно")),
            ("intrapleural", _("Внутриплеврально")),
            ("intraosseous", _("Внутрикостно")),
        ],
        string="Administration Method",
    )
    sleep_regarding = fields.Selection(
        [
            ("regardless_of_sleep", "Regardless of Sleep"),
            ("before_sleep", "Before Sleep"),
            ("after_sleep", "After Sleep"),
            ("during_sleep", "During Sleep"),
        ],
        string="Sleep Regarding",
        default="regardless_of_sleep",
        required=True,
    )
    food_regarding = fields.Selection(
        [
            ("regardless_of_food", "Regardless of Food"),
            ("before_food", "Before Food"),
            ("after_food", "After Food"),
            ("during_food", "During Food"),
        ],
        default="regardless_of_food",
        string="Food Regarding",
        required=True,
    )
    start_date = fields.Date(
        string="Start Date", required=True, default=fields.Date.today
    )
    duration = fields.Integer(string="Duration", default=1)
    duration_unit = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
        string="Duration Unit",
        default="day",
    )
    expire_date = fields.Date(
        string="Expire Date",
        compute="_compute_expire_date",
        store=True,
        readonly=False,
    )
    state = fields.Selection(
        [
            ("active", _("Active")),
            ("canceled", _("Canceled")),
        ],
        string="State",
        default="active",
        required=True,
    )
    # continuous_duration = fields.Integer(string="Continuous Duration")
    # continuous_duration_unit = fields.Selection(
    #     [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
    #     string="Continuous Duration Unit",
    # )
    # break_duration = fields.Integer(string="Break Duration")
    # break_duration_unit = fields.Selection(
    #     [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
    #     string="Break Duration Unit",
    # )
    reception_per_day = fields.Integer(string="Reception Per Day")
    reception_times_ids = fields.One2many(
        "his.medicine_reception_time",
        "medicine_prescription_id",
        string="Reception Times",
        store=True,
    )
    infusion_rate = fields.Selection(
        [
            ("slow", _("Slow")),
            ("medium", _("Medium")),
            ("inkjet", _("Inkjet")),
            ("bolus", _("Bolus")),
            ("fast", _("Fast")),
            ("constant", _("Constant")),
        ],
        string="Infusion Rate",
    )
    infusion_speed = fields.Float(string="Infusion Speed")
    infusion_speed_unit = fields.Selection(
        [("ml/h", "ml/h"), ("ml/min", "ml/min")],
        string="Infusion Speed Unit",
    )
    is_urgently = fields.Boolean(string="Is Urgently")
    is_in_medical_organization = fields.Boolean(string="Is in Medical Organization")
    notes = fields.Text(string="Notes")

    medicine_names = fields.Char(
        string="Medicine Names", compute="_compute_medicine_names"
    )
    medicine_names_with_dosage = fields.Char(
        string="Medicine Names with Dosage",
        compute="_compute_medicine_names_with_dosage",
    )

    medicines_info = fields.Json(
        string="Medicines Info", compute="_compute_medicines_info"
    )
    drug_dosage_id = fields.Many2one("his.drug_dosage", string="Drug Dosage", compute="_compute_medicine_derived_fields")
    dosage_display = fields.Char(string="Dosage Infos", compute="_compute_medicine_derived_fields")
    product_nnm_id = fields.Many2one("product.nnm", string="Product NNM", compute="_compute_medicine_derived_fields")
    product_nnm_names =  fields.Char(string="Product NNM Names", compute="_compute_medicine_derived_fields")
    product_uom_id = fields.Many2one("uom.uom", string="Product UoM", compute="_compute_medicine_derived_fields")

    cancel_reason_id = fields.Many2one(
        "his.medicine_prescription_cancel_reason",
        string="Cancel Reason",
    )
    cancel_reason_notes = fields.Text(string="Cancel Reason Notes")
    schedules = fields.One2many(
        "his.medicine_prescription_schedule",
        "prescription_medicine",
        string="Schedules",
    )
    is_template = fields.Boolean(string="Is Template", default=False)
    template_name = fields.Char(string="Template Name")
    used_template_id = fields.Many2one(
        "his.medicine_prescription", string="Used Template"
    )
    schedule_ids = fields.One2many(
        "his.medicine_prescription_schedule",
        "prescription_medicine",
        string="Schedule IDs",
    )

    @api.depends("medicine_ids", "medicine_ids.medicine_id", "medicine_ids.medicine_id.uom_id")
    def _compute_medicine_derived_fields(self):
        for record in self:
            record.drug_dosage_id = False
            record.dosage_display = ""
            medicine = record.medicine_ids[:1]

            # dosage_display
            if medicine:
                if medicine.drug_dosage_id:
                    record.drug_dosage_id = medicine.drug_dosage_id
                    record.dosage_display = f"{medicine.drug_dosage_id.dosage} {medicine.dosage_unit_id.name}"
                else:
                    record.dosage_display = f"{medicine.dosage} {medicine.dosage_unit_id.name}"

            # product_nnm_id
            product_nnm = medicine.medicine_id.product_nnm_ids
            record.product_nnm_id = product_nnm[0] if product_nnm else False

            # product_nnm_names
            record.product_nnm_names = ", ".join(medicine.medicine_id.product_nnm_ids.mapped("name")) if medicine.medicine_id.product_nnm_ids else ""

            # product_uom_id
            product_uom = medicine.medicine_id.uom_id
            record.product_uom_id = product_uom if product_uom else False

    @api.depends("medicine_type", "medicine_ids")
    def _compute_medicine_ids_domain(self):
        for record in self:
            domain = [
                ("type", "=", "product"),
            ]
            if record.medicine_type == "medicine":
                domain += [
                    (
                        "product_type_selection",
                        "in",
                        ["drug"],
                    ),
                ]
            elif record.medicine_type == "nutrition":
                domain += [("product_type_selection", "in", ["nutrition"])]

            domain += [
                ("id", "not in", record.medicine_ids.mapped("medicine_id.id")),
            ]

            record.medicine_ids_domain = domain

    def _get_allow_dosage_selection_value(self):
        val = self.env["ir.config_parameter"].sudo().get_param(
            "his.allow_dosage_selection", "False"
        )
        return str(val).strip().lower() in {"1", "true", "yes", "on"}

    @api.depends_context("uid")
    def _compute_allow_dosage_selection(self):
        allow = self._get_allow_dosage_selection_value()
        for record in self:
            record.allow_dosage_selection = allow

    @api.depends("medicine_ids")
    def _compute_medicines_info(self):
        for record in self:
            record.medicines_info = [
                {
                    "medicine_id": medicine.medicine_id.id,
                    "medicine_name": medicine.medicine_id.name,
                    "dosage": medicine.dosage,
                    "dosage_unit_id": medicine.dosage_unit_id.name,
                }
                for medicine in record.medicine_ids
            ]

    def parse_time(time_str):
        parts = str(time_str).split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours + (minutes / 100)

    @api.onchange("reception_per_day")
    def _compute_reception_times_ids(self):
        for record in self:
            reception_times_ids = [(5, 0, 0)]
            start_day_time = record.env.context.get("start_day_time")
            initial_date = record.env.context.get("initial_date")

            if (
                start_day_time
                and initial_date
                and initial_date == record.start_date.strftime("%Y-%m-%d")
            ):
                parts = start_day_time[11:16].split(":")
                hours = int(parts[0])
                minutes = int(parts[1])
                float_time_format = hours + (minutes / 60)
                for i in range(record.reception_per_day):
                    reception_times_ids.append((0, 0, {"time": float_time_format}))
            else:
                reception_times_ids += [
                    (0, 0, {"time": False}) for i in range(record.reception_per_day)
                ]
            record.write({"reception_times_ids": reception_times_ids})

    @api.depends("medicine_ids")
    def _compute_prescription_type(self):
        for record in self:
            record.prescription_type = (
                "single" if len(record.medicine_ids) <= 1 else "composite"
            )

    @api.depends("medicine_ids")
    def _compute_medicine_names(self):
        for record in self:
            record.medicine_names = ", ".join(
                record.medicine_ids.mapped("medicine_id.name")
            )

    @api.depends("medicine_ids")
    def _compute_medicine_names_with_dosage(self):
        for record in self:
            record.medicine_names_with_dosage = ", ".join(
                [
                    f"{medicine.medicine_id.name} ({medicine.dosage} {medicine.dosage_unit_id.name})"
                    for medicine in record.medicine_ids
                ]
            )

    @api.depends("start_date", "duration", "duration_unit")
    def _compute_expire_date(self):
        for record in self:
            if record.start_date and record.duration:
                days = record._duration_in_days(record.duration, record.duration_unit)
                record.expire_date = record.start_date + timedelta(days=days)
            else:
                record.expire_date = record.start_date

    def _duration_in_days(self, duration, duration_unit):
        if duration_unit == "day":
            return duration
        elif duration_unit == "week":
            return duration * 7
        elif duration_unit == "month":
            return duration * 30
        elif duration_unit == "year":
            return duration * 365

    def action_create_schedule(self):
        timezone = pytz.timezone(self.env.user.tz)
        for record in self:
            if record.is_template:
                continue
            if record.schedules:
                continue
            if (
                self.env["his.medicine_prescription_schedule"].search_count(
                    [("prescription_medicine", "=", record.id)]
                )
                == 0
            ):
                duration_in_days = record._duration_in_days(
                    record.duration, record.duration_unit
                )

                if record.reception_times_ids:
                    dosage_info = record.medicine_ids[0]
                    for i in range(duration_in_days):
                        date = record.start_date + timedelta(days=i)
                        for reception_time in record.reception_times_ids:
                            if reception_time.time < 0:
                                raise exceptions.ValidationError(
                                    _("Reception Times must be greater than -1")
                                )
                            elif reception_time.time > 23:
                                raise exceptions.ValidationError(
                                    _("Reception Times must be less than 24")
                                )
                            utc = pytz.utc
                            time = dateutil.parser.parse(
                                f"{date} {format_duration(reception_time.time)}"
                            )
                            time = (
                                timezone.localize(time)
                                .astimezone(utc)
                                .replace(tzinfo=None)
                            )
                            self.env["his.medicine_prescription_schedule"].create(
                                {
                                    "prescription_medicine": record.id,
                                    "dosage": dosage_info.dosage,
                                    "time": time,
                                    # "infusion_speed_unit": dosage_info.dosage_unit_id.name,
                                }
                            )

    def name_get(self):
        result = []
        for record in self:
            if record.is_template:
                name = record.template_name
            else:
                name = record.medicine_names
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MedicinePrescription, self).create(vals_list)
        for record in res:
            record.action_create_schedule()
        return res

    def write(self, vals):
        res = super(MedicinePrescription, self).write(vals)
        for record in self:
            if record.id:
                if not record.schedule_ids:
                    record.action_create_schedule()
        return res

    def unlink(self):
        for record in self:
            self.env["his.medicine_prescription_schedule"].search(
                [("prescription_medicine", "=", record.id)]
            ).unlink()
        return super(MedicinePrescription, self).unlink()

    def cancel_medicine(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "his.medicine_prescription_cancel_form",
            "view_mode": "form",
            "target": "new",
            "views": [[False, "form"]],
            "context": {"default_medicine_prescription_id": self.id},
        }

    def open_edit_medicine_dialog(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Medicine Prescription"),
            "res_model": "his.medicine_prescription",
            "view_mode": "form",
            "target": "new",
            "views": [[self.env.ref("his.medicine_prescription_view_form").id, "form"]],
            "res_id": self.id,
        }

    def action_cancel(self):
        self.ensure_one()
        wizard_id = self.env.context.get("prescription_wizard_id")
        if wizard_id:
            wizard = self.env["his.prescription_wizard"].browse(wizard_id)
            if wizard.exists():
                return wizard.action_refresh()
        return {"type": "ir.actions.act_window_close"}

    def action_save(self):
        self.ensure_one()
        wizard_id = self.env.context.get("prescription_wizard_id")
        if wizard_id:
            wizard = self.env["his.prescription_wizard"].browse(wizard_id)
            if wizard.exists():
                return wizard.action_refresh()
        return {"type": "ir.actions.client", "tag": "soft_reload"}

    def action_save_as_template(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "his.medicine_prescription_save_as_template_wizard",
            "view_mode": "form",
            "target": "new",
            "views": [[False, "form"]],
            "context": {
                "default_medicine_prescription_id": self.id,
                "return_action": {
                    "type": "ir.actions.act_window",
                    "res_model": "his.medicine_prescription",
                    "view_ids": [[False, "form"]],
                    "view_mode": "form",
                    "res_id": self.id,
                    "target": "new",
                },
            },
        }

    def action_load_template(self):
        self.ensure_one()
        if self.used_template_id:
            if self.schedules:
                raise exceptions.ValidationError(
                    _("You can't load template for prescription with schedules")
                )
            self.write(
                {
                    "medicine_type": self.used_template_id.medicine_type,
                    "administration_method": self.used_template_id.administration_method,
                    "food_regarding": self.used_template_id.food_regarding,
                    "sleep_regarding": self.used_template_id.sleep_regarding,
                    "duration": self.used_template_id.duration,
                    "duration_unit": self.used_template_id.duration_unit,
                    "infusion_rate": self.used_template_id.infusion_rate,
                    "infusion_speed": self.used_template_id.infusion_speed,
                    "infusion_speed_unit": self.used_template_id.infusion_speed_unit,
                    "is_urgently": self.used_template_id.is_urgently,
                    "notes": self.used_template_id.notes,
                    "medicine_ids": [
                        (
                            0,
                            0,
                            {
                                "medicine_id": medicine.medicine_id.id,
                                "dosage": medicine.dosage,
                            },
                        )
                        for medicine in self.used_template_id.medicine_ids
                    ],
                    "reception_per_day": self.used_template_id.reception_per_day,
                    "reception_times_ids": [(5, 0, 0)]
                    + [
                        (0, 0, {"time": reception_time.time})
                        for reception_time in self.used_template_id.reception_times_ids
                    ],
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Medicine Prescription"),
            "res_model": "his.medicine_prescription",
            "view_mode": "form",
            "view_ids": [[False, "form"]],
            "res_id": self.id,
            "target": "new",
        }

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        args += [("template_name", operator, name)]
        return super().name_search(name, args, operator, limit)

    def action_open_readonly(self):
        form = self.env.ref("his.medicine_prescription_view_form_readonly")
        return {
            "type": "ir.actions.act_window",
            "name": _("Medicine Prescription"),
            "res_model": "his.medicine_prescription",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "views": [[form.id, "form"]],
            # 'flags': {'mode': 'readonly'},
        }
