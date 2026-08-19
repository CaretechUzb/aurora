from odoo import models, fields, api


class MessagePostMixin(models.AbstractModel):
    _name = "his.message_post_mixin"
    _description = "Message Post Mixin"

    _related_model_name = False
    _related_id_field = False

    # def get_related_id_field(self):
    #     return self[self._related_id_field]

    related_message_ids = fields.Many2many(
        "mail.message",
        string="Messages ",
        domain=lambda self: [("message_type", "!=", "user_notification")],
        auto_join=True,
        compute="_compute_message_ids",
        store=True,
    )

    #
    def _compute_message_ids(self):
        for rec in self:
            message_ids = self.env["mail.message"].search(
                [
                    ("model", "=", rec._related_model_name),
                    ("res_id", "=", rec[rec._related_id_field].id),
                ]
            )
            rec.message_ids = [(6, 0, message_ids.ids)]

    def message_post(self, **kwargs):
        message_dict = kwargs
        res = super(MessagePostMixin, self).message_post(**kwargs)
        message_vals = {
            "model": self._related_model_name,
            "res_id": self[self._related_id_field].id,
            "author_id": self.env.user.partner_id.id,
            "body": message_dict.get("body"),
            "attachment_ids": [(6, 0, message_dict.get("attachment_ids", []))],
            "partner_ids": [(6, 0, message_dict.get("partner_ids", []))],
            "message_type": message_dict.get("message_type", "comment"),
        }
        self.env["mail.message"].create(message_vals)

        return res
