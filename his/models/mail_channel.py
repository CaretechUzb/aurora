from odoo import _, api, fields, models, tools, Command


class Channel(models.Model):
    _inherit = "mail.channel"

    patient_id = fields.Many2one("his.patient", string="Patient")
    is_his_channel = fields.Boolean(
        string="Is HIS Channel",
        default=False,
    )

    _sql_constraints = [
        (
            "patient_id_unique",
            "unique(patient_id)",
            "Patient can have only one channel",
        )
    ]
