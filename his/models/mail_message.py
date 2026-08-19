from odoo import models, fields, api, _


class MailMessage(models.Model):
    _inherit = "mail.message"

    def init(self):
        self._cr.execute("""SELECT indexname FROM pg_indexes WHERE indexname = 'mail_message_model_res_id_idx'""")
        if not self._cr.fetchone():
            self._cr.execute("""CREATE INDEX mail_message_model_res_id_idx ON mail_message (model, res_id)""")
        self._cr.execute("""CREATE INDEX IF NOT EXISTS mail_message_model_res_id_id_idx ON mail_message (model, res_id, id)""")

        self._cr.execute(
            """CREATE INDEX IF NOT EXISTS mail_message_model_idx ON mail_message (model)"""
        )
        self._cr.execute(
            """CREATE INDEX IF NOT EXISTS mail_message_res_id_idx ON mail_message (res_id)"""
        )
