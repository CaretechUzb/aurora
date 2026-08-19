from odoo import models, fields, tools, _


class DailyRevenue(models.Model):
    _name = "his.daily_revenue_report"
    _description = "Daily Revenue Report"
    _auto = False
    _log_access = True

    date = fields.Date(string="Date")
    card_amount = fields.Float(string="Card Amount")
    cash_amount = fields.Float(string="Cash Amount")
    total_amount = fields.Float(string="Total Amount")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    create_uid = fields.Many2one("res.users", string="Created by")
    write_uid = fields.Many2one("res.users", string="Last Updated by")
    create_date = fields.Datetime(string="Created on")
    write_date = fields.Datetime(string="Last Updated on")

    def _query(self):
        return """
            SELECT
                ROW_NUMBER() OVER () AS id,
                DATE(payment_date) AS date,
                SUM(CASE WHEN provider = 'card' THEN amount ELSE 0 END) AS card_amount,
                SUM(CASE WHEN provider = 'cash' THEN amount ELSE 0 END) AS cash_amount,
                SUM(amount) AS total_amount,
                company_id,
                1 as create_uid,
                1 as write_uid,
                NOW() as create_date,
                NOW() as write_date
            FROM 
                his_payment_transaction
            GROUP BY
                Date, company_id;
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("Daily Revenue Search"),
            "res_model": "his.daily_revenue_search",
            "context": context,
            "views": [[self.env.ref("his.daily_revenue_search_view").id, "form"]],
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_daily_revenue"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["context"] = {
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
            "use_custom_search": "1",
            "filter_is_active": False,
        }
        action["target"] = "main"
        return action
