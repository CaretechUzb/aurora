from odoo import models, fields, tools, _


class MedicineStatistics(models.Model):
    _name = "his.medical_statistics_report"
    _description = "Medicine statistics"
    _auto = False
    _log_access = True

    prescription_date = fields.Date(string="Prescription Date")
    medicine_prescription_name = fields.Many2one(
        "product.template", string="Medicine Prescription Name"
    )
    unit = fields.Char(string="Unit")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    amount = fields.Float(string="Amount")
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
                ROW_NUMBER() OVER () as id,
                hod.write_date as prescription_date,
                pt.id as medicine_prescription_name,
                hod.unit_quantity as unit,
                hod.quantity as quantity,
                pt.list_price as unit_price,
                pt.list_price * hod.quantity as amount, -- formulani tekshirish kerak
                hod.company_id as company_id,
                hod.create_uid as create_uid,
                hod.write_uid as write_uid,
                hod.create_date as create_date,
                hod.create_date as write_date
            FROM
                his_order_detail hod
                LEFT JOIN product_product pp ON hod.service_id = pp.id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            GROUP BY
                hod.id, pt.id, hod.company_id
                """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE view %s as %s """ % (self._table, self._query()))

    def custom_search_filter(self, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": _("Medicine statistics Search"),
            "res_model": "his.medicine_statistics_search",
            "context": context,
            "views": [[self.env.ref("his.medicine_statistics_search_view").id, "form"]],
            "target": "new",
        }

    def custom_search_reset(self, context=None):
        action_id = "his.action_medical_statistics_report"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_id)
        action["context"] = {
            "open_filters_callback": "custom_search_filter",
            "reset_filters_callback": "custom_search_reset",
            "use_custom_search": "1",
            "filter_is_active": False,
        }
        action["target"] = "main"
        return action
