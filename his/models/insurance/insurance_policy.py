from odoo import models, fields, api, exceptions


class InsurancePolicy(models.Model):
    _name = "his.insurance_policy"
    _description = "Payer Policy Records"
    _rec_name = "policy_number"

    full_name = fields.Char(string="Full Name", required=True)
    passport_number = fields.Char(string="Passport Number")
    phone_number = fields.Char(string="Phone Number")
    pinfl = fields.Char(string="PINFL")
    contract_id = fields.Many2one("his.insurance_contract")
    patient_id = fields.Many2one("his.patient")
    policy_number = fields.Char(string="Policy Number", required=True)
    policy_amount = fields.Float(string="Policy Amount", required=True)
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date")
    is_active = fields.Boolean(string="Is Active", default=True)

    # type = fields.Selection(
    #     [("direct_access", "Direct Access"), ("temporary_certificate", "Temporary Certificate"),
    #      ("default", "Default")], string="Type"
    # )
    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if name:
            new_domain = [
                args[1],
                ("policy_number", "ilike", name + "%"),
                ("to_date", ">=", fields.Date.today()),
            ]
            return self._search(new_domain, limit=limit)
        elif args and self.search(args):
            return self._search(args, limit=limit)
        return self._search(args, limit=limit)

    #
    def action_delete(self):
        self.is_active = False

    def action_restore(self):
        self.is_active = True
