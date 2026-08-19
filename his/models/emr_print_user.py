from odoo import models, fields, api, exceptions

class EMRPrintUser(models.Model):
    _name = "his.emr_print_user"
    _description = "EMR print user"

    user_id = fields.Many2one('res.users', 'User')