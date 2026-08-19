from odoo import exceptions, fields, models, api, _


class Booking(models.Model):
    _name = "his.doctor_booking"
    _description = "Service Booking for Patient Records"

    service_id = fields.Many2one("product.product", string="Service", required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    doctor_id = fields.Many2one(
        "hr.employee",
        string="Doctor",
        domain="[('department_id', '=', department_id)]",
        required=True,
    )
    start_time = fields.Float(
        string="Start Time",
        digits=(2, 2),
        help="Start time in hours (0.00 - 23.99)",
        required=True,
    )
    end_time = fields.Float(
        string="End Time",
        digits=(2, 2),
        help="End time in hours (0.00 - 23.99)",
        required=True,
    )
    date = fields.Date(string="Date", default=fields.Date.today())
