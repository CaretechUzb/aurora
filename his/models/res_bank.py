from odoo import fields, models, api, _, exceptions


class ResBank(models.Model):
    _inherit = "res.bank"

    mfo = fields.Char(string="MFO", help=_("Bank MFO"))


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    is_main = fields.Boolean(string="Is_main", default=False)

    @api.onchange("is_main")
    def _onchange_is_main(self):
        for record in self:
            if record.is_main:
                search_count = self.search_count(
                    [("company_id", "=", record.company_id.id), ("is_main", "=", True)]
                )
                if search_count > 0:
                    raise exceptions.ValidationError(
                        _("Main must be one in one branch")
                    )
