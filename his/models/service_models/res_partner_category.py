from odoo import models, api, _
from odoo.exceptions import UserError


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    def unlink(self):
        aggregator_category = self.env.ref(
            "his.referral_source_category_aggregator_id", False
        )

        if aggregator_category and aggregator_category in self:
            raise UserError(
                _(
                    "The Aggregator category cannot be deleted. It is a required category for the system."
                )
            )

        return super(PartnerCategory, self).unlink()
