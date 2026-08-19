from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MedicinePrescriptionDosage(models.Model):
    _name = "his.medicine_prescription_dosage"
    _description = "Medicine Prescription Dosage"

    medicine_prescription_id = fields.Many2one(
        "his.medicine_prescription", string="Medicine Prescription", required=True, ondelete="cascade"
    )
    medicine_id = fields.Many2one("product.product", string="Medicine", required=True)
    drug_dosage_id = fields.Many2one("his.drug_dosage", string="Drug Dosage")
    allow_dosage_selection = fields.Boolean(
        compute="_compute_allow_dosage_selection",
    )

    dosage = fields.Float(string="Dosage", required=True)
    dosage_unit_id = fields.Many2one(
        "uom.uom", string="Dosage Unit", store=True, compute="_compute_dosage_unit"
    )

    @api.depends_context("uid")
    def _compute_allow_dosage_selection(self):
        val = self.env["ir.config_parameter"].sudo().get_param(
            "his.allow_dosage_selection", False
        )
        allow = bool(val) and str(val) != "False"
        for record in self:
            record.allow_dosage_selection = allow

    @api.onchange("drug_dosage_id")
    def _onchange_drug_dosage_id(self):
        if self.drug_dosage_id:
            self.dosage = self.drug_dosage_id.dosage_amount
        else:
            self.dosage = 0.0

    @api.onchange("medicine_id")
    def _onchange_medicine_id(self):
        # Reset dosage catalog selection when medicine changes to avoid stale/incompatible value.
        self.drug_dosage_id = False

    @api.constrains("dosage")
    def _validate_dosage(self):
        for record in self:
            if record.dosage <= 0:
                raise ValidationError(_("Dosage must be greater than 0."))

    @api.depends("medicine_id")
    def _compute_dosage_unit(self):
        for record in self:
            if record.medicine_id.calculation_type in ["pack", "one_time"]:
                record.dosage_unit_id = record.medicine_id.amt_unit.id
            else:
                record.dosage_unit_id = record.medicine_id.uom_id.id
