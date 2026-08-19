from odoo import fields, models, tools, api, _

from odoo.tools import html2plaintext


class ModelName(models.Model):
    _inherit = "res.company"

    oked = fields.Char(string="OKED", help=_("Bank OKED"))
    director_id = fields.Many2one("hr.employee", string=_("Director"))
    medical_director = fields.Many2one("hr.employee", string=_("Medical Director"))

    @api.model
    def _tz_get(self):
        import pytz
        return [(x, x) for x in pytz.all_timezones]

    timezone = fields.Selection(
        _tz_get, string="Timezone",
        default="Asia/Tashkent",
        help="Branch working timezone"
    )

    company_full_name = fields.Char("Full name")
    company_short_name = fields.Char("Short name")
    company_legal_name = fields.Char("Legal name")

    latitude = fields.Float("Latitude", digits=(10, 6))
    longitude = fields.Float("Longitude", digits=(10, 6))
    # map_is = fields.Selection([('google', 'Google Maps'),
    #                            ('yandex', 'Yandex Maps')], string='On which map')
    main_company_account_id = fields.Many2one(
        "res.partner.bank",
        string="Main Accounts",
        compute="_compute_main_accounts",
        store=True,
    )

    # Due From/Due To Account fields
    due_from_account_id = fields.Many2one("account.account", "Due From")
    due_to_account_id = fields.Many2one("account.account", "Due To")
    due_fromto_payment_journal_id = fields.Many2one(
        "account.journal", string="Due From/Due To Journal"
    )

    start_time = fields.Float(
        string="Start Time",
        digits=(2, 2),
        help="Start time in hours (0.00 - 23.59)",
        group_operator=False,
    )
    end_time = fields.Float(
        string="End Time",
        digits=(2, 2),
        help="End time in hours (0.00 - 23.59)",
        group_operator=False,
    )

    working_days = fields.Many2many("his.weekdays", string="working_days")
    x_bank_data = fields.Char(string="Bank data")

    @api.depends("partner_id.bank_ids.is_main")
    def _compute_main_accounts(self):
        for company in self:
            main_account = self.env["res.partner.bank"].search(
                [
                    # ('company_id', '=', company.id),
                    ("is_main", "=", True)
                ]
            )
            company.main_company_account_id = main_account
