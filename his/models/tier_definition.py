from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    has_comment_validation = fields.Boolean(
        string="Comment on Validation",
        help="If checked, comment will be required when validating this tier",
    )
    has_comment_reject = fields.Boolean(
        string="Comment on Reject",
        help="If checked, comment will be required when rejecting this tier",
    )

    @api.constrains("has_comment", "has_comment_validation", "has_comment_reject")
    def _check_comment_fields(self):
        for record in self:
            if record.has_comment and not (
                record.has_comment_validation or record.has_comment_reject
            ):
                raise ValidationError(
                    "When 'Comment' is enabled, at least one of "
                    "'Comment on Validation' or 'Comment on Reject' must be checked."
                )

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append("account.payment")
        return res
