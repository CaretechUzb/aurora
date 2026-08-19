from odoo import fields, models


class MessageLog(models.Model):
    _name = "his.message_log"
    _inherit = "mail.thread"
    _description = "Message Log Records"
    _rec_name = "phone_number"

    phone_number = fields.Char(string="Phone Number", required=True)
    message = fields.Text(string="Message", required=True)
    is_send = fields.Boolean(string="Is Send", default=False)
    ip = fields.Char("IP address of the client", size=255)
    res_data = fields.Json("Response data from playmobile")
