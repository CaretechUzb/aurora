from odoo import models


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    def validate_tier(self):
        """Override to conditionally require comment based on has_comment_validation"""
        self.ensure_one()
        sequences = self._get_sequences_to_approve(self.env.user)
        reviews = self.review_ids.filtered(
            lambda review: review.sequence in sequences or review.approve_sequence_bypass
        )

        # Check if any pending review requires comment on validation
        user_reviews = reviews.filtered(
            lambda r: r.status == "pending" and (self.env.user in r.reviewer_ids)
        )
        has_comment_validation = any(
            user_reviews.mapped("definition_id.has_comment_validation")
        )

        if has_comment_validation:
            return self._add_comment("validate", user_reviews)

        self._validate_tier(reviews)
        self._update_counter({"review_deleted": True})

    def reject_tier(self):
        """Override to conditionally require comment based on has_comment_reject"""
        self.ensure_one()
        sequences = self._get_sequences_to_approve(self.env.user)
        reviews = self.review_ids.filtered(
            lambda review: review.sequence in sequences
        )

        # Check if any pending review requires comment on rejection
        user_reviews = reviews.filtered(
            lambda r: r.status == "pending" and (self.env.user in r.reviewer_ids)
        )
        has_comment_reject = any(
            user_reviews.mapped("definition_id.has_comment_reject")
        )

        if has_comment_reject:
            return self._add_comment("reject", reviews)

        self._rejected_tier(reviews)
        self._update_counter({"review_deleted": True})
