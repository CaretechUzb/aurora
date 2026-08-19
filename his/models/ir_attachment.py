from odoo import models, fields, api, _


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def action_open_attachment(self):
        self.ensure_one()
        if self.mimetype == "application/pdf":
            view_id = self.env.ref("his.ir_attachment_show_pdf_form").id
            return {
                "name": self.res_name,
                "type": "ir.actions.act_window",
                "res_model": "ir.attachment",
                "views": [[view_id, "form"]],
                "res_id": self.id,
                "target": "new",
                "context": {"bin_size": False},
            }

        else:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{self.id}?download=true",
                "target": "new",
            }

    @api.model
    def check(self, mode, values=None):
        if self._context.get("access_sudo", False):
            return True
        return super().check(mode, values)

    def validate_access(self, access_token):
        record = super().validate_access(access_token)
        if not record.env.su:
            self.check('read')
        return record
