from odoo import fields, models


class DoctorAppointmentType(models.Model):
    _name = "his.doctor.appointment.type"
    _description = "Doctor Appointment Type"

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Char(string="Code", required=True)  # online, offline, etc.

