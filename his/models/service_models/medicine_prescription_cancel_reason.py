from odoo import exceptions, models, fields, api, _


class MedicinePrescriptionCancelReason(models.Model):
    _name = "his.medicine_prescription_cancel_reason"
    _description = "Medicine Prescription Cancel Reason"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description")
