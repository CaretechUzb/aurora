from datetime import timedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import float_compare


class PayerPolicyLimit(models.Model):
    _name = "his.payer_policy_limit"
    _inherit = "mail.thread"
    _description = "Payer Policy Limit Records"
    _rec_name = "amount"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    amount = fields.Float(string="Amount", required=True, tracking=True)
    policy_id = fields.Many2one(
        "his.payer_policy", string="Policy", required=True, tracking=True
    )
    date = fields.Date(
        string="Expire Date", required=True, tracking=True, default=fields.Date.today
    )

    _sql_constraints = [
        (
            "unique_policy_company_date",
            "unique(company_id, policy_id, date)",
            "Policy limit must be unique per branch and policy",
        )
    ]

    def action_open_in_current(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def write(self, vals):
        if "amount" in vals:
            patient_visit = self.env["his.patient_visit"].search(
                [
                    ("payer_policy", "=", self.policy_id.id),
                    ("date", "=", self.date),
                    ("visiting_type", "=", "main"),
                ],
                limit=1,
            )
            if patient_visit and patient_visit.payer_policy_limit != vals["amount"]:
                patient_visit.with_context(skip_payer_policy_update=True).write(
                    {"payer_policy_limit": vals["amount"]}
                )
        return super().write(vals)

    def _get_total_used_amount(self, exclude_order_id=None):
        self.ensure_one()
        domain = [
            ("payer_policy_limit_id", "=", self.id),
            ("state", "in", ["sale", "done"]),
            ("qty_invoiced", ">", 0),
        ]
        if exclude_order_id:
            domain.append(("order_id", "!=", exclude_order_id))

        result = (
            self.env["sale.order.line"]
            .sudo()
            .read_group(
                domain + [("coverage_amount", "=", 0)],
                ["price_total:sum"],
                ["payer_policy_limit_id"],
            )
        )
        total_used_amount1 = result[0]["price_total"] if result else 0.0

        result = (
            self.env["sale.order.line"]
            .sudo()
            .read_group(
                domain + [("coverage_amount", ">", 0)],
                ["coverage_amount:sum"],
                ["payer_policy_limit_id"],
            )
        )
        total_used_amount2 = result[0]["coverage_amount"] if result else 0.0

        return total_used_amount1 + total_used_amount2

    @api.model
    def get_or_create_policy_limit(self, policy_id, company_id, amount, date=None):
        """
        Get existing policy limit or create new one if not exists.
        This method ensures no duplicate limits are created.
        """
        if not date:
            date = fields.Date.today()
            
        # Search for existing limit with same policy, company, and date
        existing_limit = self.search([
            ('policy_id', '=', policy_id),
            ('company_id', '=', company_id),
            ('date', '=', date)
        ], limit=1)
        
        if existing_limit:
            if amount and existing_limit.amount != amount:
                existing_limit.write({'amount': amount})
            return existing_limit
        else:
            return self.create({
                'policy_id': policy_id,
                'company_id': company_id,
                'amount': amount,
                'date': date
            })
