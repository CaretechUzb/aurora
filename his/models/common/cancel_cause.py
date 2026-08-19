from odoo import exceptions, fields, models, api, _


class CancelCause(models.Model):
    _name = "his.cancel_cause"
    _description = "Cancel Cause for Order Detail"
    _rec_name = "title"

    title = fields.Char(string="Title", required=True)
