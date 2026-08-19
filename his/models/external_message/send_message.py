from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from ...utils.sms_providers import send_via_play_mobile


class SendMessage(models.Model):
    _name = "his.send_message"
    _inherit = "mail.thread"
    _description = "Send Message Records"

    patient_id = fields.Many2one("his.patient", string="Patient")
    message = fields.Text(string="Message", required=True)
    type = fields.Selection(
        [
            ("sms", "SMS"),
            ("telegram", "Telegram Message"),
        ],
        string="Type",
        default="sms",
        required=True,
    )

    def action_send_message(self):
        if self.type == "sms":
            if not self.patient_id.phone_number:
                raise ValidationError(_("Patient has no phone number"))
            send_via_play_mobile(self.env, self.message, self.patient_id.phone_number)
        else:
            raise ValidationError(_("Not implemented yet"))
        return {
            # "tag": "display_notification",
            # "params": {
            #     "title": "Success",
            #     "message": "SMS has been sent successfully",
            #     "sticky": False,
            # },
            "type": "ir.actions.act_window_close",
        }
